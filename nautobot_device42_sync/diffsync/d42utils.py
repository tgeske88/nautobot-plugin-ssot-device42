"""Utility functions for Device42 API."""

import requests
import urllib3
from typing import List


def merge_offset_dicts(orig_dict: dict, offset_dict: dict) -> dict:
    """Method to merge two dicts and merge a list if found.

    Args:
        orig_dict (dict): Dict to have data merged from.
        offset_dict (dict): Dict to be merged into with offset data. Expects this to be like orig_dict but with offset data.

    Returns:
        dict: Dict with merged data from both dicts.
    """
    out = {}
    for key, value in offset_dict.items():
        if key in orig_dict and key in offset_dict:
            if isinstance(value, list):
                out[key] = orig_dict[key] + value
            else:
                out[key] = value
    return out


def get_intf_type(intf_record: dict) -> str:  # pylint: disable=inconsistent-return-statements
    """Method to determine an Interface type based on a few factors.

    Those factors include:
        - Port type
        - Port Speed Note: `port_speed` was used instead of `speedcapable` as `speedcapable` reported nothing.
        - Discovered type for port

    Anything explicitly not matched will go to `other`.
    """
    PHY_INTF_MAP = {  # pylint: disable=invalid-name
        "10 Mbps": "other",
        "50 Mbps": "other",
        "100 Mbps": "100base-tx",
        "1.0 Gbps": "1000base-t",
        "10 Gbps": "10gbase-t",
        "25 Gbps": "25gbase-x-sfp28",
        "40 Gbps": "40gbase-x-qsfpp",
        "50 Gbps": "50gbase-x-sfp28",
        "100 Gbps": "100gbase-x-qsfp28",
        "200 Gbps": "200gbase-x-qsfp56",
        "400 Gbps": "400gbase-x-qsfpdd",
        "10000": "other",
        "20000": "other",
        "1000000": "1000base-t",
        "10000000": "10gbase-t",
        "1000000000": "100gbase-x-qsfp28",
    }

    FC_INTF_MAP = {  # pylint: disable=invalid-name
        "1.0 Gbps": "1gfc-sfp",
        "2.0 Gbps": "2gfc-sfp",
        "4.0 Gbps": "4gfc-sfp",
        "4 Gbps": "4gfc-sfp",
        "8.0 Gbps": "8gfc-sfpp",
        "16.0 Gbps": "16gfc-sfpp",
        "32.0 Gbps": "32gfc-sfp28",
        "64.0 Gbps": "64gfc-qsfpp",
        "128.0 Gbps": "128gfc-sfp28",
    }

    # if switch is physical and name is from PHY_INTF_MAP dict
    if intf_record["port_type"] == "physical":
        if intf_record["port_speed"] in PHY_INTF_MAP and "ethernet" in intf_record["discovered_type"]:
            # print(f"Matched on intf mapping. {intf_record['port_speed']}")
            return PHY_INTF_MAP[intf_record["port_speed"]]
        if intf_record["discovered_type"] == "fibreChannel" and intf_record["port_speed"] in FC_INTF_MAP:
            # print(f"Matched on FibreChannel. {intf_record['port_name']} {intf_record['device_name']}")
            return FC_INTF_MAP[intf_record["port_speed"]]
        return "other"
    elif intf_record["port_type"] == "logical":
        if intf_record["discovered_type"] == "softwareLoopback" or intf_record["discovered_type"] == "propVirtual":
            # print(f"Virtual interface matched. {intf_record['port_name']} {intf_record['device_name']}.")
            return "virtual"
        if intf_record["discovered_type"] == "ieee8023adLag" or intf_record["discovered_type"] == "lacp":
            # print(f"PortChannel matched. {intf_record['port_name']} {intf_record['device_name']}")
            return "lag"
        return "other"


class Device42API:
    """Device42 API class."""

    def __init__(self, base_url: str, username: str, password: str, verify: bool = True):
        """Create Device42 API connection."""
        self.base_url = base_url
        self.verify = verify
        self.username = username
        self.password = password
        self.headers = {"Content-Type": "application/x-www-form-urlencoded"}

        if verify is False:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def validate_url(self, path):
        """Validate URL formatting is correct."""
        if not self.base_url.endswith("/") and not path.startswith("/"):
            full_path = f"{self.base_url}/{path}"
        else:
            full_path = f"{self.base_url}{path}"
        if not full_path.endswith("/"):
            return full_path
        return full_path

    def api_call(self, path: str, method: str = "GET", params: dict = None, payload: dict = None):
        """Method to send Request to Device42 of type `method`. Defaults to GET request.

        Args:
            path (str): API path to send request to.
            method (str, optional): API request method. Defaults to "GET".
            params (dict, optional): Additional parameters to send to API. Defaults to None.

        Raises:
            Exception: Error thrown if request errors.

        Returns:
            dict: JSON payload of API response.
        """
        url = self.validate_url(path)
        return_data = {}

        if params is None:
            params = {}

        params.update(
            {
                "_paging": "1",
                "_return_as_object": "1",
                "_max_results": "1000",
            }
        )

        resp = requests.request(
            method=method,
            headers=self.headers,
            auth=(self.username, self.password),
            url=url,
            params=params,
            verify=self.verify,
            data=payload,
        )
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"Error in communicating to Device42 API: {err}")
            return False

        return_data = resp.json()
        # print(f"Total count for {url}: {return_data.get('total_count')}")
        # Handle Device42 pagination
        counter = 0
        pagination = False
        if isinstance(return_data, dict) and return_data.get("total_count"):
            while (return_data.get("offset") + return_data.get("limit")) < return_data.get("total_count"):
                pagination = True
                # print("Handling paginated response from Device42.")
                new_offset = return_data["offset"] + return_data["limit"]
                params.update({"offset": new_offset})
                counter += 1
                response = requests.request(
                    method="GET",
                    headers=self.headers,
                    auth=(self.username, self.password),
                    url=url,
                    params=params,
                    verify=self.verify,
                )
                response.raise_for_status()
                return_data = merge_offset_dicts(return_data, response.json())
                # print(
                #     f"Number of devices: {len(return_data['Devices'])}.\noffset: {return_data.get('offset')}.\nlimit: {return_data.get('limit')}."
                # )

                # Handle possible infinite loop.
                if counter > 10000:
                    print("Too many pagination loops in Device42 request. Possible infinite loop.")
                    print(url)
                    break

            # print(f"Exiting API request loop after {counter} loops.")

        if pagination:
            return_data.pop("offset", None)

        return return_data

    def doql_query(self, query: str) -> dict:
        """Method to perform a DOQL query against Device42.

        Args:
            query (str): DOQL query to be sent to Device42.

        Returns:
            dict: Returned data from Device42 for DOQL query.
        """
        params = {
            "query": query,
            "output_type": "json",
        }
        url = "services/data/v1.0/query/"
        return self.api_call(path=url, params=params)

    def get_cluster_members(self) -> dict:
        """Method to get all member devices of a cluster from Device42.

        Returns:
            dict: Dictionary of all clusters with associated members.
        """
        query = "SELECT m.name as cluster, string_agg(d.name, '%3B ') as members FROM view_device_v1 m JOIN view_devices_in_cluster_v1 c ON c.parent_device_fk = m.device_pk JOIN view_device_v1 d ON d.device_pk = c.child_device_fk WHERE m.type like '%cluster%' GROUP BY m.name"
        _results = self.doql_query(query=query)

        return {
            _i["cluster"]: {"members": [x.strip() for x in _i["members"].split("%3B")], "is_network": "no"}
            for _i in _results
        }

    def get_physical_intfs(self) -> List[dict]:
        """Method to get all physical interfaces from Device42.

        This retrieves only the information we care about via DOQL in one giant json blob instead of multiple API calls.

        Returns:
            dict: Dict of interface information from DOQL query.
        """
        query = "SELECT m.port as port_name , m.description , m.up_admin, m.discovered_type, m.hwaddress, m.port_type, m.port_speed, m.mtu, m.tags, d.name as device_name FROM view_netport_v1 m JOIN view_device_v1 d on d.device_pk = m.device_fk WHERE m.port_type like '%physical%' GROUP BY m.port, m.description, m.up_admin, m.discovered_type, m.hwaddress, m.port_type, m.port_speed, m.mtu, m.tags, d.name"
        return self.doql_query(query=query)

    def get_logical_intfs(self) -> List[dict]:
        """Method to get all logical interfaces from Device42.

        This retrieves only the information we care about via DOQL in one giant json blob instead of multiple API calls.

        Returns:
            dict: Dict of interface information from DOQL query.
        """
        query = "SELECT m.port as port_name , m.description , m.up_admin, m.discovered_type, m.hwaddress, m.port_type, m.port_speed, m.mtu, m.tags, d.name as device_name FROM view_netport_v1 m JOIN view_device_v1 d on d.device_pk = m.device_fk WHERE m.port_type like '%logical%' GROUP BY m.port, m.description, m.up_admin, m.discovered_type, m.hwaddress, m.port_type, m.port_speed, m.mtu, m.tags, d.name"
        return self.doql_query(query=query)

    def get_subnets(self) -> List[dict]:
        """Method to get all subnets and associated data from Device42.

        Returns:
            dict: Dict of subnets from Device42.
        """
        query = "SELECT s.name, s.network, s.mask_bits, s.tags, v.name as vrf FROM view_subnet_v1 s JOIN view_vrfgroup_v1 v ON s.vrfgroup_fk = v.vrfgroup_pk"
        return self.doql_query(query=query)

    def get_ip_addrs(self) -> List[dict]:
        """Method to get all IP addresses and relevant data from Device42 via DOQL.

        Returns:
            List[dict]: List of dicts with info about each IP address.
        """
        query = "SELECT i.ip_address, i.available, i.label, i.tags, np.port AS port_name, s.network as subnet, s.mask_bits as netmask, v.name as vrf, d.name as device FROM view_ipaddress_v1 i LEFT JOIN view_subnet_v1 s ON s.subnet_pk = i.subnet_fk LEFT JOIN view_device_v1 d ON d.device_pk = i.device_fk LEFT JOIN view_netport_v1 np ON np.netport_pk = i.netport_fk LEFT JOIN view_vrfgroup_v1 v ON v.vrfgroup_pk = s.vrfgroup_fk WHERE s.mask_bits <> 0"
        return self.doql_query(query=query)
