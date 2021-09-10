"""DiffSync adapter for Device42."""

from decimal import Decimal
from django.utils.functional import classproperty
from diffsync import DiffSync
from diffsync.exceptions import ObjectAlreadyExists, ObjectNotFound
from nautobot.core.settings_funcs import is_truthy
from nautobot_device42_sync.diffsync.from_d42.models import dcim
from nautobot_device42_sync.diffsync.from_d42.models import ipam
from nautobot_device42_sync.diffsync.d42utils import Device42API, get_intf_type
from nautobot_device42_sync.constant import PLUGIN_CFG


def sanitize_string(san_str: str):
    """Sanitize string to ensure it doesn't have invisible characters."""
    return san_str.replace("\u200b", "")


class Device42Adapter(DiffSync):
    """DiffSync adapter using requests to communicate to Device42 server."""

    building = dcim.Building
    room = dcim.Room
    rack = dcim.Rack
    vendor = dcim.Vendor
    hardware = dcim.Hardware
    cluster = dcim.Cluster
    device = dcim.Device
    port = dcim.Port
    vrf = ipam.VRFGroup
    subnet = ipam.Subnet
    ipaddr = ipam.IPAddress
    vlan = ipam.VLAN
    conn = dcim.Connection

    top_level = [
        "building",
        "vendor",
        "hardware",
        "vrf",
        "subnet",
        "vlan",
        "cluster",
        "device",
        "conn",
        "ipaddr",
    ]

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

        # mapping of VLAN PK to VLAN name and ID
        self.vlan_map = self._device42.get_vlan_info()
        # mapping of Device PK to Device name
        self.device_map = self._device42.get_device_pks()
        # mapping of Port PK to Port name
        self.port_map = self._device42.get_port_pks()

    @classproperty
    def _device42_hardwares(self):
        if not self._device42_hardware_dict:
            device42_hardware_list = self._device42.api_call(path="api/2.0/hardwares/")["models"]
            for hardware in device42_hardware_list["models"]:
                self._device42_hardware_dict[hardware["hardware_id"]] = hardware
        return self._device42_hardware_dict

    def load_buildings(self):
        """Load Device42 buildings."""
        print("Loading buildings from Device42.")
        for record in self._device42.api_call(path="api/1.0/buildings")["buildings"]:
            _tags = record.get("tags")
            _tags.sort()
            building = self.building(
                name=record["name"],
                address=record["address"] if record.get("address") else "",
                latitude=round(Decimal(record["latitude"] if record["latitude"] else 0.0), 6),
                longitude=round(Decimal(record["longitude"] if record["longitude"] else 0.0), 6),
                contact_name=record["contact_name"] if record.get("contact_name") else "",
                contact_phone=record["contact_phone"] if record.get("contact_phone") else "",
                rooms=record["rooms"] if record.get("rooms") else [],
                tags=_tags,
            )
            try:
                self.add(building)
            except ObjectAlreadyExists as err:
                print(f"{record['name']} is already loaded. {err}")

    def load_rooms(self):
        """Load Device42 rooms."""
        print("Loading rooms from Device42.")
        for record in self._device42.api_call(path="api/1.0/rooms")["rooms"]:
            _tags = record["tags"] if record.get("tags") else []
            _tags.sort()
            if record.get("building"):
                room = self.room(
                    name=record["name"],
                    building=record["building"],
                    notes=record["notes"] if record.get("notes") else "",
                    tags=_tags,
                )
                try:
                    self.add(room)
                    _site = self.get(self.building, record.get("building"))
                    _site.add_child(child=room)
                except ObjectAlreadyExists as err:
                    print(f"{record['name']} is already loaded. {err}")
            else:
                # print(f"{record['name']} is missing Building and won't be imported.")
                continue

    def load_racks(self):
        """Load Device42 racks."""
        print("Loading racks from Device42.")
        for record in self._device42.api_call(path="api/1.0/racks")["racks"]:
            _tags = record["tags"] if record.get("tags") else []
            _tags.sort()
            if record.get("building") and record.get("room"):
                rack = self.rack(
                    name=record["name"],
                    building=record["building"],
                    room=record["room"],
                    height=record["size"] if record.get("size") else 1,
                    numbering_start_from_bottom=record["numbering_start_from_bottom"],
                    tags=_tags,
                )
                try:
                    self.add(rack)
                    _room = self.get(
                        self.room, {"name": record["room"], "building": record["building"], "room": record["room"]}
                    )
                    _room.add_child(child=rack)
                except ObjectAlreadyExists as err:
                    print(f"Rack {record['name']} already exists. {err}")
            else:
                # print(f"{record['name']} is missing Building and Room and won't be imported.")
                continue

    def load_vendors(self):
        """Load Device42 vendors."""
        print("Loading vendors from Device42.")
        for _vendor in self._device42.api_call(path="api/1.0/vendors")["vendors"]:
            vendor = self.vendor(name=_vendor["name"])
            self.add(vendor)

    def load_hardware_models(self):
        """Load Device42 hardware models."""
        print("Loading hardware models from Device42.")
        for _model in self._device42.api_call(path="api/1.0/hardwares/")["models"]:
            if _model.get("manufacturer"):
                model = self.hardware(
                    name=_model["name"],
                    manufacturer=_model["manufacturer"] if _model.get("manufacturer") else "Unknown",
                    size=_model["size"] if _model.get("size") else 1,
                    depth=_model["depth"] if _model.get("depth") else "Half Depth",
                    part_number=_model["part_no"],
                )
                try:
                    self.add(model)
                except ObjectAlreadyExists as err:
                    # print(f"Hardware model already exists. {err}")
                    continue

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

    def load_cluster(self, cluster_info: dict) -> dcim.Cluster:
        """Load Device42 clusters into DiffSync model.

        Args:
            cluster_info (dict): Information of cluster to be added to DiffSync model.

        Returns:
            models.Cluster: Cluster model that has been created or found.
        """
        try:
            _cluster = self.get(self.cluster, cluster_info)
        except ObjectAlreadyExists as err:
            print(f"Cluster {cluster_info['name']} already has been added. {err}")
        except ObjectNotFound:
            # print(f"Cluster {cluster_name} being added.")
            _clus = self._device42_clusters[cluster_info["name"]]
            _tags = cluster_info["tags"] if cluster_info.get("tags") else []
            _tags.sort()
            _cluster = self.cluster(
                name=cluster_info["name"],
                hardware=_clus["hardware"],
                platform=_clus["os"],
                facility=_clus["customer"],
                members=_clus["members"],
                tags=_tags,
            )
            self.add(_cluster)

    def load_devices_and_clusters(self):
        """Load Device42 devices."""
        # Get all Devices from Device42
        print("Retrieving devices from Device42.")
        _devices = self._device42.api_call(path="api/1.0/devices/all/?is_it_switch=yes")["Devices"]

        # Add all Clusters first
        print("Loading clusters...")
        for _record in _devices:
            if _record.get("type") == "cluster" and _record.get("name") in self._device42_clusters.keys():
                print(f"Attempting to load cluster {_record['name']}")
                self.load_cluster(_record)

        # Then iterate through again and add Devices and if are part of a cluster, add to Cluster
        print("Loading devices...")
        for _record in _devices:
            # print(f"Record for {_record['name']}: {_record}.")
            if _record.get("type") != "cluster":
                _tags = _record["tags"] if _record.get("tags") else []
                _tags.sort()
                _device = self.device(
                    name=_record["name"],
                    dtype=_record["type"],
                    building=_record["building"] if _record.get("building") else "",
                    customer=_record["customer"] if _record.get("customer") else "",
                    room=_record["room"] if _record.get("room") else "",
                    rack=_record["rack"] if _record.get("rack") else "",
                    rack_position=int(_record["start_at"]) if _record.get("start_at") else None,
                    rack_orientation="front" if _record.get("orientation") == 1 else "rear",
                    hardware=sanitize_string(_record["hw_model"]) if _record.get("hw_model") else "",
                    os=_record.get("os"),
                    in_service=_record.get("in_service"),
                    serial_no=_record["serial_no"],
                    tags=_tags,
                )
                try:
                    cluster_host = self.get_cluster_host(_record["name"])
                    if cluster_host:
                        if is_truthy(self._device42_clusters[cluster_host]["is_network"]) is False:
                            print(
                                f"{cluster_host} has network device members but isn't marked as network. This should be corrected in Device42."
                            )
                        _device.cluster_host = cluster_host
                        # print(f"Device {_record['name']} being added.")
                    self.add(_device)
                except ObjectAlreadyExists as err:
                    # print(f"Device already added. {err}")
                    continue

    def load_ports(self):
        """Load Device42 ports."""
        vlan_ports = self._device42.get_ports_with_vlans()
        no_vlan_ports = self._device42.get_logical_ports_wo_vlans()
        _ports = vlan_ports + no_vlan_ports
        for _port in _ports:
            if _port.get("port_name") and _port.get("device_name"):
                _tags = _port["tags"].split(",") if _port.get("tags") else []
                _tags.sort()
                try:
                    new_port = self.port(
                        name=_port["port_name"],
                        device=_port["device_name"],
                        enabled=is_truthy(_port["up_admin"]),
                        mtu=_port["mtu"],
                        description=_port["description"],
                        mac_addr=_port["hwaddress"],
                        type=get_intf_type(intf_record=_port),
                        tags=_tags,
                        mode="access",
                    )
                    if _port.get("vlan_pks"):
                        vlans = []
                        for _pk in _port["vlan_pks"]:
                            if self.vlan_map[_pk]["vid"] != 0:
                                _vlan = {
                                    "vlan_name": self.vlan_map[_pk]["name"],
                                    "vlan_id": self.vlan_map[_pk]["vid"],
                                }
                                vlans.append(_vlan)
                        new_port.vlans = vlans
                        if len(vlans) > 1:
                            new_port.mode = "tagged"
                    self.add(new_port)
                    try:
                        _dev = self.get(self.cluster, _port["device_name"])
                        _dev.add_child(new_port)
                    except ObjectNotFound:
                        _dev = self.get(self.device, _port["device_name"])
                        _dev.add_child(new_port)
                except ObjectAlreadyExists as err:
                    # print(f"Port already exists. {err}")
                    continue
                except ObjectNotFound as err:
                    # print(f"Device {_port['device_name']} not found. {err}")
                    continue

    def load_vrfgroups(self):
        """Load Device42 VRFGroups."""
        print("Retrieving VRF groups from Device42.")
        for _grp in self._device42.api_call(path="api/1.0/vrfgroup/")["vrfgroup"]:
            try:
                _tags = _grp["tags"] if _grp.get("tags") else []
                _tags.sort()
                new_vrf = self.vrf(
                    name=_grp["name"],
                    description=_grp["description"],
                    tags=_tags,
                )
                self.add(new_vrf)
            except ObjectAlreadyExists as err:
                # print(f"VRF Group {_grp['name']} already exists. {err}")
                continue

    def load_subnets(self):
        """Load Device42 Subnets."""
        print("Retrieving Subnets from Device42.")
        for _pf in self._device42.get_subnets():
            _tags = _pf["tags"].split(",") if _pf.get("tags") else []
            _tags.sort()
            # This handles Prefix with /32 netmask. These need to be added as an IPAddress.
            if _pf["mask_bits"] == 32 and ":" not in _pf["network"]:
                print(f"Network {_pf['network']} with 32 netmask found. Loading as IPAddress.")
                new_ip = self.ipaddr(
                    address=f"{_pf['network']}/{str(_pf['mask_bits'])}",
                    available=True,
                    label=_pf["name"],
                    vrf=_pf["vrf"],
                    tags=_tags,
                )
                self.add(new_ip)
            elif _pf["mask_bits"] != 0:
                try:
                    new_pf = self.subnet(
                        network=_pf["network"],
                        mask_bits=_pf["mask_bits"],
                        description=_pf["name"],
                        vrf=_pf["vrf"],
                        tags=_tags,
                    )
                    self.add(new_pf)
                except ObjectAlreadyExists as err:
                    # print(f"Subnet {_pf['network']} {_pf['mask_bits']} {_pf['vrf']} {err}")
                    continue
            else:
                # print(f"Unable to import Subnet with a 0 mask bits. {_pf['network']} {_pf['name']}.")
                continue

    def load_ip_addresses(self):
        """Load Device42 IP Addresses."""
        print("Retrieving IP Addresses from Device42.")
        for _ip in self._device42.get_ip_addrs():
            try:
                _tags = _ip["tags"].split(",") if _ip.get("tags") else []
                _tags.sort()
                new_ip = self.ipaddr(
                    address=f"{_ip['ip_address']}/{str(_ip['netmask'])}",
                    available=_ip["available"],
                    label=_ip["label"],
                    device=_ip["device"],
                    interface=_ip["port_name"],
                    vrf=_ip["vrf"],
                    tags=_tags,
                )
                self.add(new_ip)
            except ObjectAlreadyExists as err:
                # print(f"IP Address {_ip['ip_address']} {_ip['netmask']} already exists.{err}")
                continue

    def load_vlans(self):
        """Load Device42 VLANs."""
        _vlans = self._device42.get_vlans_with_location()
        for _info in _vlans:
            try:
                _vlan_name = _info["vlan_name"].strip()
                if _info.get("building"):
                    new_vlan = self.get(
                        self.vlan, {"name": _vlan_name, "vlan_id": _info["vid"], "building": _info["building"]}
                    )
                elif is_truthy(PLUGIN_CFG.get("customer_is_facility")) and _info.get("customer"):
                    new_vlan = self.get(
                        self.vlan, {"name": _vlan_name, "vlan_id": _info["vid"], "building": _info["customer"]}
                    )
                else:
                    new_vlan = self.get(self.vlan, {"name": _vlan_name, "vlan_id": _info["vid"], "building": "Unknown"})
            except ObjectAlreadyExists as err:
                print(f"VLAN {_vlan_name} already exists. {err}")
            except ObjectNotFound:
                new_vlan = self.vlan(
                    name=_vlan_name,
                    vlan_id=int(_info["vid"]),
                    description=_info["description"] if _info.get("description") else "",
                )
                if _info.get("building"):
                    new_vlan.building = _info["building"]
                elif is_truthy(PLUGIN_CFG.get("customer_is_facility")) and _info.get("customer"):
                    new_vlan.building = _info["customer"]
                else:
                    new_vlan.building = "Unknown"
                self.add(new_vlan)

    def load_connections(self):
        """Load Device42 connections."""
        _port_conns = self._device42.get_port_connections()
        for _conn in _port_conns:
            try:
                new_conn = self.conn(
                    src_device=self.device_map[_conn["src_device"]]["name"],
                    src_port=self.port_map[_conn["src_port"]]["port"],
                    src_port_mac=self.port_map[_conn["src_port"]]["hwaddress"],
                    dst_device=self.device_map[_conn["dst_device"]]["name"],
                    dst_port=self.port_map[_conn["dst_port"]]["port"],
                    dst_port_mac=self.port_map[_conn["dst_port"]]["hwaddress"],
                )
                self.add(new_conn)
            except ObjectAlreadyExists as err:
                print(err)

    def load(self):
        """Load data from Device42."""
        self.load_buildings()
        self.load_rooms()
        self.load_racks()
        self.load_vendors()
        self.load_hardware_models()
        self.load_vrfgroups()
        self.load_vlans()
        self.load_subnets()
        self.load_devices_and_clusters()
        self.load_ports()
        self.load_ip_addresses()
        self.load_connections()
