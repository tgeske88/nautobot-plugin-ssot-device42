"""Utility functions for Device42 API."""

import requests
import urllib3


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

    def merge_offset_dicts(self, orig_dict: dict, offset_dict: dict) -> dict:
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
        if isinstance(return_data, dict):
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
                return_data = self.merge_offset_dicts(return_data, response.json())
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
