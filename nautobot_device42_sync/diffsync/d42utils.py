"""Utility functions for Device42 API."""

import requests


class Device42API:
    """Device42 API class."""

    def __init__(self, base_url: str, username: str, password: str, verify: bool = True):
        """Create Device42 API connection."""
        self.base_url = base_url
        self.verify = verify
        self.username = username
        self.password = password
        self.headers = {"Content-Type": "application/x-www-form-urlencoded"}

    def validate_url(self, path):
        """Validate URL formatting is correct."""
        if not self.base_url.endswith("/") and not path.startswith("/"):
            full_path = f"{self.base_url}/{path}"
        else:
            full_path = f"{self.base_url}{path}"
        if not full_path.endswith("/"):
            return full_path + "/"
        return full_path

    def api_call(self, path: str, method: str = "GET", params: dict = None):
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
        try:
            if params:
                resp = requests.request(
                    method=method,
                    headers=self.headers,
                    auth=(self.username, self.password),
                    url=url,
                    params=params,
                    verify=self.verify,
                )
                resp.raise_for_status()
            else:
                resp = requests.request(
                    method=method,
                    headers=self.headers,
                    auth=(self.username, self.password),
                    url=url,
                    verify=self.verify,
                )
                resp.raise_for_status()
        except requests.HTTPError as err:
            raise Exception(f"Request error {url} [{resp.status_code}] {err}")
        return resp.json()

    def get_buildings(self) -> list:
        """Retrieve all buildings in Device42.

        Returns:
            list: List of buildings and associated information in Device42.
        """
        try:
            return self.api_call(path="api/1.0/buildings")["buildings"]
        except requests.HTTPError as err:
            raise Exception(f"Error retrieving buildings from Device42. {err}")
