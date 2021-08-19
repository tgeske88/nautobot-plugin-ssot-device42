"""DiffSync adapter for Device42."""

from django.utils.functional import classproperty
from diffsync import DiffSync
from diffsync.exceptions import ObjectAlreadyExists, ObjectNotFound
from nautobot.core.settings_funcs import is_truthy
from nautobot_device42_sync.diffsync.from_d42 import models
from nautobot_device42_sync.diffsync.d42utils import Device42API
from nautobot_device42_sync.constant import PLUGIN_CFG
from decimal import Decimal
import re


class Device42Adapter(DiffSync):
    """DiffSync adapter using requests to communicate to Device42 server."""

    building = models.Building
    room = models.Room
    rack = models.Rack
    vendor = models.Vendor
    hardware = models.Hardware
    cluster = models.Cluster
    device = models.Device
    port = models.Port

    top_level = ["building", "vendor", "hardware", "cluster", "device"]

    def __init__(self, *args, job=None, sync=None, **kwargs):
        """Initialize Device42Adapter.

        Args:
            job (object, optional): Nautobot job. Defaults to None.
            sync (object, optional): Nautobot DiffSync. Defaults to None.
        """
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self._device42_hardware_dict = {}
        self._device42 = Device42API(
            base_url=PLUGIN_CFG["device42_host"],
            username=PLUGIN_CFG["device42_username"],
            password=PLUGIN_CFG["device42_password"],
            verify=PLUGIN_CFG["verify_ssl"],
        )
        self._device42_clusters = self._device42.get_cluster_members()

    @classproperty
    def _device42_hardwares(self):
        if not self._device42_hardware_dict:
            device42_hardware_list = self._device42.api_call(path="api/2.0/hardwares/")["models"]
            for hardware in device42_hardware_list["models"]:
                self._device42_hardware_dict[hardware["hardware_id"]] = hardware
        return self._device42_hardware_dict

    @classmethod
    def sanitize_string(self, san_str: str):
        """Sanitize string to ensure it doesn't have invisible characters."""
        return san_str.replace("\u200b", "")

    def get_cidrs(self, address_list: list) -> list:
        """Return list of CIDRs from list of dicts of IP Addresses from Device42.

        Args:
            address_list (list): List of dicts of IP addresses for a device in Device42.

        Returns:
            list: List of the CIDRs of the IP addresses for a device.
        """
        ip_list = []
        for _ip in address_list:
            _netmask = re.search(r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}\/(?P<mask>\d+)", _ip["subnet"])
            if _netmask:
                ip_list.append(f"{_ip['ip']}/{_netmask.group('mask')}")
        return ip_list

    def load_buildings(self):
        """Load Device42 buildings."""
        self.job.log_debug("Loading buildings from Device42.")
        for record in self._device42.api_call(path="api/1.0/buildings")["buildings"]:
            building = self.building(
                name=record["name"],
                address=record["address"] if record.get("address") else "",
                latitude=round(Decimal(record["latitude"] if record["latitude"] else 0.0), 6),
                longitude=round(Decimal(record["longitude"] if record["longitude"] else 0.0), 6),
                contact_name=record["contact_name"] if record.get("contact_name") else "",
                contact_phone=record["contact_phone"] if record.get("contact_phone") else "",
                rooms=record["rooms"] if record.get("rooms") else [],
            )
            try:
                self.add(building)
            except ObjectAlreadyExists as err:
                self.job.log_debug(f"{record['name']} is already loaded. {err}")

    def load_rooms(self):
        """Load Device42 rooms."""
        self.job.log_debug("Loading rooms from Device42.")
        for record in self._device42.api_call(path="api/1.0/rooms")["rooms"]:
            if record.get("building"):
                room = self.room(
                    name=record["name"],
                    building=record["building"],
                    notes=record["notes"] if record.get("notes") else "",
                )
                try:
                    self.add(room)
                    _site = self.get(self.building, record.get("building"))
                    _site.add_child(child=room)
                except ObjectAlreadyExists as err:
                    self.job.log_debug(f"{record['name']} is already loaded. {err}")
            else:
                self.job.log_debug(f"{record['name']} is missing Building and won't be imported.")

    def load_racks(self):
        """Load Device42 racks."""
        self.job.log_debug("Loading racks from Device42.")
        for record in self._device42.api_call(path="api/1.0/racks")["racks"]:
            if record.get("building") and record.get("room"):
                rack = self.rack(
                    name=record["name"],
                    building=record["building"],
                    room=record["room"],
                    height=record["size"] if record.get("size") else 1,
                    numbering_start_from_bottom=record["numbering_start_from_bottom"],
                )
                try:
                    self.add(rack)
                    _room = self.get(
                        self.room, {"name": record["room"], "building": record["building"], "room": record["room"]}
                    )
                    _room.add_child(child=rack)
                except ObjectAlreadyExists as err:
                    self.job.log_debug(f"Rack {record['name']} already exists. {err}")
            else:
                self.job.log_debug(f"{record['name']} is missing Building and Room and won't be imported.")

    def load_vendors(self):
        """Load Device42 vendors."""
        self.job.log_debug("Loading vendors from Device42.")
        for _vendor in self._device42.api_call(path="api/1.0/vendors")["vendors"]:
            vendor = self.vendor(name=_vendor["name"])
            self.add(vendor)

    def load_hardware_models(self):
        """Load Device42 hardware models."""
        self.job.log_debug("Loading hardware models from Device42.")
        for _model in self._device42.api_call(path="api/1.0/hardwares/")["models"]:
            if _model.get("manufacturer"):
                model = self.hardware(
                    name=_model["name"],
                    manufacturer=_model["manufacturer"] if _model.get("manufacturer") else "Unknown",
                    size=_model["size"] if _model.get("size") else 1,
                    depth=_model["depth"] if _model.get("depth") else "",
                    part_number=_model["part_no"],
                )
                try:
                    self.add(model)
                except ObjectAlreadyExists as err:
                    self.job.log_debug(f"Hardware model already exists. {err}")

    def get_cluster_host(self, device: str) -> str or bool:
        """Get name of cluster host if device is in a cluster.

        Args:
            device (str): Name of device to see if part of cluster.

        Returns:
            str or bool: Name of cluster device is part of or returns False.
        """
        for _cluster, _info in self._device42_clusters.items():
            if device in _info["members"]:
                return _cluster
        return False

    def load_cluster(self, cluster_name: dict) -> models.Cluster:
        """Load Device42 clusters into DiffSync model.

        Args:
            cluster_name (dict): Name of cluster to be added to DiffSync model.

        Returns:
            models.Cluster: Cluster model that has been created or found.
        """
        try:
            _cluster = self.get(self.cluster, cluster_name)
        except ObjectAlreadyExists as err:
            self.job.log_debug(f"Cluster {cluster_name} already has been added. {err}")
        except ObjectNotFound:
            self.job.log_debug(f"Cluster {cluster_name} being added.")
            _cluster = self.cluster(
                name=cluster_name,
                ctype="network",
            )
            self.add(_cluster)
        return _cluster

    def load_devices_and_clusters(self):
        """Load Device42 devices."""
        # Get all Devices from Device42
        self.job.log_debug("Retrieving devices from Device42.")
        _devices = self._device42.api_call(path="api/1.0/devices/all/?is_it_switch=yes")["Devices"]

        # Add all Clusters first
        self.job.log_debug("Loading clusters...")
        for _record in _devices:
            if _record.get("type") == "cluster":
                _cluster = self.load_cluster(_record["name"])
                _cluster.building = _record["building"] if _record.get("building") else ""
                if _record.get("name") in self._device42_clusters.keys():
                    self._device42_clusters[_record.get("name")]["is_network"] = _record.get("is_it_switch")
                else:
                    self.job.log_debug(
                        f"Cluster {_record['name']} has no cluster members. Please validate this is correct."
                    )

        # Then iterate through again and add Devices and if are part of a cluster, add to Cluster
        self.job.log_debug("Loading devices...")
        for _record in _devices:
            # self.job.log_debug(f"Record for {_record['name']}: {_record}.")
            if _record.get("type") != "cluster":
                _device = self.device(
                    name=_record["name"],
                    dtype=_record["type"],
                    building=_record["building"] if _record.get("building") else "",
                    room=_record["room"] if _record.get("room") else "",
                    rack=_record["rack"] if _record.get("rack") else "",
                    rack_position=int(_record["start_at"]) if _record.get("start_at") else None,
                    rack_orientation="front" if _record.get("orientation") == 1 else "rear",
                    hardware=self.sanitize_string(_record["hw_model"]) if _record.get("hw_model") else "",
                    os=_record.get("os"),
                    in_service=_record.get("in_service"),
                    ip_addresses=self.get_cidrs(_record["ip_addresses"]) if _record.get("ip_addresses") else [],
                    serial_no=_record["serial_no"],
                    tags=_record["tags"],
                )
                try:
                    cluster_host = self.get_cluster_host(_record["name"])
                    if cluster_host:
                        if is_truthy(self._device42_clusters[cluster_host]["is_network"]) is False:
                            self.job.log_warning(
                                f"{cluster_host} has network device members but isn't marked as network. This should be corrected in Device42."
                            )
                        _clus = self.load_cluster(cluster_host)
                        _device.cluster_host = cluster_host
                        self.job.log_debug(f"Device {_record['name']} being added.")
                        self.add(_device)
                        _clus.add_child(_device)
                    else:
                        self.add(_device)
                except ObjectAlreadyExists as err:
                    self.job.log_debug(f"Device already added. {err}")

    def load_ports(self):
        """Load Device42 ports."""
        self.job.log_debug("Retrieving ports from Device42.")
        phy_ports = self._device42.get_physical_intfs()
        logical_ports = self._device42.get_logical_intfs()
        _ports = phy_ports + logical_ports
        for _port in _ports:
            if _port.get("port_name"):
                try:
                    new_port = self.port(
                        name=_port["port_name"],
                        device=_port["device_name"],
                        enabled=is_truthy(_port["up_admin"]),
                        mtu=_port["mtu"],
                        description=_port["description"],
                        mac_addr=_port["hwaddress"],
                        type=self._device42.get_intf_type(intf_record=_port),
                    )
                    self.add(new_port)
                    _dev = self.get(self.device, _port["device_name"])
                    _dev.add_child(new_port)
                except ObjectAlreadyExists as err:
                    self.job.log_debug(f"Port already exists. {err}")
                except ObjectNotFound as err:
                    self.job.log_debug(f"Device {_port['device_name']} not found. {err}")

    def load(self):
        """Load data from Device42."""
        self.load_buildings()
        self.load_rooms()
        self.load_racks()
        self.load_vendors()
        self.load_hardware_models()
        self.load_devices_and_clusters()
        self.load_ports()
