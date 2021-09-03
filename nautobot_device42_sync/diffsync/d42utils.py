"""Utility functions for Device42 API."""

import re
import requests
import urllib3
from typing import List
from nautobot_device42_sync.constant import PHY_INTF_MAP, FC_INTF_MAP, INTF_NAME_MAP


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
    _port_name = re.search(r"^[a-zA-Z]+-?[a-zA-Z]+", intf_record["port_name"].strip())

    if _port_name:
        _port_name = _port_name.group()

    # if switch is physical and name is from PHY_INTF_MAP dict
    if intf_record["port_type"] == "physical":
        # Due to Device42 not reflecting the true speed capability of a port, just what it's running at, we must check if port is `up`.
        # If port is not showing as `up` then the `port_speed` field is inaccurate and we must resort to port name.
        if intf_record["up"]:
            if intf_record["port_speed"] in PHY_INTF_MAP and "ethernet" in intf_record["discovered_type"]:
                # print(f"Matched on intf mapping. {intf_record['port_speed']}")
                return PHY_INTF_MAP[intf_record["port_speed"]]
            if intf_record["discovered_type"] == "fibreChannel" and intf_record["port_speed"] in FC_INTF_MAP:
                # print(f"Matched on FibreChannel. {intf_record['port_name']} {intf_record['device_name']}")
                return FC_INTF_MAP[intf_record["port_speed"]]
            if intf_record["port_speed"] in PHY_INTF_MAP:
                # print(f"Matched on intf mapping. {intf_record['port_speed']}")
                return PHY_INTF_MAP[intf_record["port_speed"]]
            return "other"
        else:
            # Assumption is that `port_speed` is inaccurate and must use `port_name`.
            if _port_name in INTF_NAME_MAP and intf_record["port_speed"] == INTF_NAME_MAP[_port_name]["ex_speed"]:
                return INTF_NAME_MAP[_port_name]["itype"]
            if _port_name in INTF_NAME_MAP:
                return INTF_NAME_MAP[_port_name]["itype"]
            else:
                print(
                    f"Unable to determine port type based on port name ({_port_name}) or `port_speed` ({intf_record['port_speed']}) for {intf_record['device_name']} {intf_record['port_name']}."
                )
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
        query = "SELECT m.name as cluster, string_agg(d.name, '%3B ') as members, h.name as hardware, d.network_device, d.os_name as os, b.name as customer, d.tags FROM view_device_v1 m JOIN view_devices_in_cluster_v1 c ON c.parent_device_fk = m.device_pk JOIN view_device_v1 d ON d.device_pk = c.child_device_fk JOIN view_hardware_v1 h ON h.hardware_pk = d.hardware_fk JOIN view_customer_v1 b ON b.customer_pk = d.customer_fk WHERE m.type like '%cluster%' GROUP BY m.name, h.name, d.network_device, d.os_name, b.name, d.tags"
        _results = self.doql_query(query=query)

        return {
            _i["cluster"]: {
                "members": [x.strip() for x in _i["members"].split("%3B")],
                "is_network": _i["network_device"],
                "hardware": _i["hardware"],
                "os": _i["os"],
                "customer": _i["customer"],
                "tags": _i["tags"].split(",") if _i.get("tags") else [],
            }
            for _i in _results
        }

    def get_ports_with_vlans(self) -> List[dict]:
        """Method to get all Ports with attached VLANs from Device42.

        This retrieves only the information we care about via DOQL in one giant json blob instead of multiple API calls.

        Returns:
            List[dict]: Dict of interface information from DOQL query.
        """
        query = "SELECT array_agg( distinct concat (v.vlan_pk)) AS vlan_pks, n.port AS port_name, n.description, n.up, n.up_admin, n.discovered_type, n.hwaddress, n.port_type, n.port_speed, n.mtu, d.name AS device_name FROM view_vlan_v1 v LEFT JOIN view_vlan_on_netport_v1 vn ON vn.vlan_fk = v.vlan_pk LEFT JOIN view_netport_v1 n ON n.netport_pk = vn.netport_fk LEFT JOIN view_device_v1 d ON d.device_pk = n.device_fk WHERE n.port is not null OR n.hwaddress is not null GROUP BY n.port, n.description, n.up, n.up_admin, n.discovered_type, n.hwaddress, n.port_type, n.port_speed, n.mtu, d.name"
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

    def get_vlans_with_location(self) -> List[dict]:
        """Method to get all VLANs with Building and Customer info to attach to find Site.

        Returns:
            List[dict]: List of dicts of VLANs and location information.
        """
        query = "SELECT v.vlan_pk, v.number AS vid, v.description, vn.vlan_name, b.name as building, c.name as customer FROM view_vlan_v1 v LEFT JOIN view_vlan_on_netport_v1 vn ON vn.vlan_fk = v.vlan_pk LEFT JOIN view_netport_v1 n on n.netport_pk = vn.netport_fk LEFT JOIN view_device_v2 d on d.device_pk = n.device_fk LEFT JOIN view_building_v1 b ON b.building_pk = d.building_fk LEFT JOIN view_customer_v1 c ON c.customer_pk = d.customer_fk WHERE vn.vlan_name is not null and v.number <> 0 GROUP BY v.vlan_pk, v.number, v.description, vn.vlan_name, b.name, c.name"
        return self.doql_query(query=query)

    def get_vlan_info(self) -> dict:
        """Method to obtain the VLAN name and ID paired to primary key.

        Returns:
            dict: Mapping of VLAN primary key to VLAN name and ID.
        """
        query = "SELECT v.vlan_pk, v.name, v.number as vid FROM view_vlan_v1 v"
        doql_vlans = self.doql_query(query=query)
        return {str(x["vlan_pk"]): {"name": x["name"], "vid": x["vid"]} for x in doql_vlans}
