"""DiffSync adapter class for Nautobot as source-of-truth."""

import ipaddress
from diffsync import DiffSync
from diffsync.exceptions import ObjectAlreadyExists
from django.db.models import ProtectedError
from nautobot_ssot_device42.constant import PLUGIN_CFG
from nautobot_ssot_device42.diffsync.from_d42.models import circuits, dcim, ipam
from nautobot_ssot_device42.utils import nautobot
from netutils.lib_mapper import ANSIBLE_LIB_MAPPER

from nautobot.circuits.models import Circuit, CircuitTermination, Provider

from nautobot.dcim.models import (
    Cable,
    Device,
    DeviceType,
    Interface,
    Manufacturer,
    Rack,
    RackGroup,
    Site,
    VirtualChassis,
)
from nautobot.ipam.models import VLAN, VRF, IPAddress, Prefix

try:
    import nautobot_device_lifecycle_mgmt  # noqa: F401

    LIFECYCLE_MGMT = True
except ImportError:
    print("Device Lifecycle plugin isn't installed so will revert to CustomField for OS version.")
    LIFECYCLE_MGMT = False


class NautobotAdapter(DiffSync):
    """Nautobot adapter for DiffSync."""

    _objects_to_delete = {
        "device": [],
        "site": [],
        "rack": [],
        "manufacturer": [],
        "device_type": [],
        "ipaddr": [],
        "vrf": [],
        "cluster": [],
        "port": [],
        "subnet": [],
        "vlan": [],
        "provider": [],
        "circuit": [],
    }

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
    provider = circuits.Provider
    circuit = circuits.Circuit

    top_level = [
        "building",
        "vendor",
        "hardware",
        "vrf",
        "subnet",
        "vlan",
        "cluster",
        "device",
        "ipaddr",
        "provider",
        "circuit",
        "conn",
    ]

    def __init__(self, *args, job=None, sync=None, **kwargs):
        """Initialize the Device42 DiffSync adapter.

        Args:
            job (object, optional): Nautobot job. Defaults to None.
            sync (object, optional): Nautobot DiffSync. Defaults to None.
        """
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync

    def sync_complete(self, source: DiffSync, *args, **kwargs):
        """Clean up function for DiffSync sync.

        Once the sync is complete, this function runs deleting any objects
        from Nautobot that need to be deleted in a specific order.

        Args:
            source (DiffSync): DiffSync
        """
        for grouping in (
            "ipaddr",
            "subnet",
            "vrf",
            "vlan",
            "circuit",
            "provider",
            "cluster",
            "port",
            "device",
            "device_type",
            "manufacturer",
            "rack",
            "site",
        ):
            for nautobot_object in self._objects_to_delete[grouping]:
                try:
                    nautobot_object.delete()
                except ProtectedError:
                    self.job.log(f"Deletion failed protected object: {nautobot_object}")
            self._objects_to_delete[grouping] = []

        return super().sync_complete(source, *args, **kwargs)

    def load_sites(self):
        """Add Nautobot Site objects as DiffSync Building models."""
        for site in Site.objects.all():
            try:
                building = self.building(
                    name=site.name,
                    address=site.physical_address,
                    latitude=site.latitude,
                    longitude=site.longitude,
                    contact_name=site.contact_name,
                    contact_phone=site.contact_phone,
                    tags=nautobot.get_tag_strings(site.tags),
                    custom_fields=nautobot.get_custom_field_dicts(site.get_custom_fields()),
                )
                self.add(building)
            except AttributeError:
                continue

    def load_rackgroups(self):
        """Add Nautobot RackGroup objects as DiffSync Room models."""
        for _rg in RackGroup.objects.all():
            room = self.room(
                name=_rg.name,
                building=Site.objects.get(name=_rg.site).name,
                notes=_rg.description,
                custom_fields=nautobot.get_custom_field_dicts(_rg.get_custom_fields()),
            )
            self.add(room)
            _site = self.get(self.building, Site.objects.get(name=_rg.site).name)
            _site.add_child(child=room)

    def load_racks(self):
        """Add Nautobot Rack objects as DiffSync Rack models."""
        for rack in Rack.objects.all():
            try:
                _building_name = Site.objects.get(name=rack.site).name
                new_rack = self.rack(
                    name=rack.name,
                    building=_building_name,
                    room=RackGroup.objects.get(name=rack.group, site__name=_building_name).name,
                    height=rack.u_height,
                    numbering_start_from_bottom="no" if rack.desc_units else "yes",
                    tags=nautobot.get_tag_strings(rack.tags),
                    custom_fields=nautobot.get_custom_field_dicts(rack.get_custom_fields()),
                )
                self.add(new_rack)
                _room = self.get(self.room, {"name": rack.group, "building": _building_name})
                _room.add_child(child=new_rack)
            except ObjectAlreadyExists as err:
                if PLUGIN_CFG.get("verbose_debug"):
                    self.job.log_warning(err)

    def load_manufacturers(self):
        """Add Nautobot Manufacturer objects as DiffSync Vendor models."""
        for manu in Manufacturer.objects.all():
            new_manu = self.vendor(
                name=manu.name,
                custom_fields=nautobot.get_custom_field_dicts(manu.get_custom_fields()),
            )
            self.add(new_manu)

    def load_device_types(self):
        """Add Nautobot DeviceType objects as DiffSync Hardware models."""
        for _dt in DeviceType.objects.all():
            dtype = self.hardware(
                name=_dt.model,
                manufacturer=_dt.manufacturer.name,
                size=_dt.u_height,
                depth="Full Depth" if _dt.is_full_depth else "Half Depth",
                part_number=_dt.part_number,
                custom_fields=nautobot.get_custom_field_dicts(_dt.get_custom_fields()),
            )
            self.add(dtype)

    def load_virtual_chassis(self):
        """Add Nautobot Virtual Chassis objects as DiffSync."""
        # We import the master node as a VC
        for _vc in VirtualChassis.objects.all():
            _members = [x.name for x in _vc.members.all() if x.name != _vc.name]
            if len(_members) > 1:
                _members.sort()
            new_vc = self.cluster(
                name=_vc.name,
                members=_members,
                tags=nautobot.get_tag_strings(_vc.tags),
                custom_fields=nautobot.get_custom_field_dicts(_vc.get_custom_fields()),
            )
            self.add(new_vc)

    def load_devices(self):
        """Add Nautobot Device objects as DiffSync Device models."""
        for dev in Device.objects.all():
            if dev.platform and dev.platform.name in ANSIBLE_LIB_MAPPER:
                _platform = ANSIBLE_LIB_MAPPER[dev.platform.name]
            elif dev.platform:
                _platform = dev.platform.name
            else:
                _platform = ""
            if LIFECYCLE_MGMT:
                _version = nautobot.get_software_version_from_lcm(relations=dev.get_relationships())
            else:
                _version = nautobot.get_version_from_custom_field(fields=dev.get_custom_fields())
            _dev = self.device(
                name=dev.name,
                building=dev.site.slug,
                room=dev.rack.group.name if dev.rack else "",
                rack=dev.rack.name if dev.rack else "",
                rack_position=dev.position,
                rack_orientation=dev.face if dev.face else "rear",
                hardware=dev.device_type.model,
                os=_platform,
                os_version=_version,
                in_service=bool(str(dev.status) == "Active"),
                serial_no=dev.serial if dev.serial else "",
                tags=nautobot.get_tag_strings(dev.tags),
                master_device=False,
                custom_fields=nautobot.get_custom_field_dicts(dev.get_custom_fields()),
            )
            if dev.virtual_chassis:
                _dev.cluster_host = str(dev.virtual_chassis)
                if hasattr(dev, "vc_master_for"):
                    if str(dev.vc_master_for) == _dev.cluster_host:
                        _dev.master_device = True
            self.add(_dev)

    def load_interfaces(self):
        """Add Nautobot Interface objects as DiffSync Port models."""
        for port in Interface.objects.all():
            # self.job.log_debug(message=f"Loading Interface: {port.name} for {port.device}.")
            if port.mac_address:
                _mac_addr = str(port.mac_address).replace(":", "").lower()
            else:
                _mac_addr = ""
            _port = self.port(
                name=port.name,
                device=port.device.name,
                enabled=port.enabled,
                mtu=port.mtu,
                description=port.description,
                mac_addr=_mac_addr[:13],
                type=port.type,
                tags=nautobot.get_tag_strings(port.tags),
                mode=port.mode,
                custom_fields=nautobot.get_custom_field_dicts(port.get_custom_fields()),
            )
            if port.mode == "access" and port.untagged_vlan:
                _port.vlans = [
                    {
                        "vlan_name": port.untagged_vlan.name,
                        "vlan_id": str(port.untagged_vlan.vid),
                    }
                ]
            else:
                _tags = []
                for _vlan in port.tagged_vlans.values():
                    _tags.append(
                        {
                            "vlan_name": _vlan["name"],
                            "vlan_id": str(_vlan["vid"]),
                        }
                    )
                _vlans = sorted(_tags, key=lambda k: k["vlan_id"])
                _port.vlans = _vlans
            try:
                self.add(_port)
                _dev = self.get(self.device, port.device.name)
                _dev.add_child(_port)
            except ObjectAlreadyExists as err:
                if PLUGIN_CFG.get("verbose_debug"):
                    self.job.log_warning(message=f"Port already exists for {port.device_name}. {err}")
                continue

    def load_vrfs(self):
        """Add Nautobot VRF objects as DiffSync VRFGroup models."""
        # self.job.log_debug(message=f"Loading VRF: {self.name}.")
        for vrf in VRF.objects.all():
            _vrf = self.vrf(
                name=vrf.name,
                description=vrf.description,
                tags=nautobot.get_tag_strings(vrf.tags),
                custom_fields=nautobot.get_custom_field_dicts(vrf.get_custom_fields()),
            )
            self.add(_vrf)

    def load_prefixes(self):
        """Add Nautobot Prefix objects as DiffSync Subnet models."""
        for _pf in Prefix.objects.all():
            # self.job.log_debug(message=f"Loading Prefix: {_pf.prefix}.")
            ip_net = ipaddress.ip_network(_pf.prefix)
            new_pf = self.subnet(
                network=str(ip_net.network_address),
                mask_bits=str(ip_net.prefixlen),
                description=_pf.description,
                vrf=_pf.vrf.name,
                tags=nautobot.get_tag_strings(_pf.tags),
                custom_fields=nautobot.get_custom_field_dicts(_pf.get_custom_fields()),
            )
            self.add(new_pf)

    def load_ip_addresses(self):
        """Add Nautobot IPAddress objects as DiffSync IPAddress models."""
        for _ip in IPAddress.objects.all():
            # self.job.log_debug(message=f"Loading IPAddress: {_ip.address}.")
            new_ip = self.ipaddr(
                address=str(_ip.address),
                available=bool(_ip.status.name != "Active"),
                label=_ip.description,
                vrf=_ip.vrf.name if _ip.vrf else None,
                tags=nautobot.get_tag_strings(_ip.tags),
                interface="",
                device="",
                custom_fields=nautobot.get_custom_field_dicts(_ip.get_custom_fields()),
            )
            if _ip.assigned_object_id:
                _intf = Interface.objects.get(id=_ip.assigned_object_id)
                new_ip.interface = _intf.name
                new_ip.device = _intf.device.name
            if hasattr(_ip, "primary_ip4_for") or hasattr(_ip, "primary_ip6_for"):
                new_ip.primary = True
            else:
                new_ip.primary = False
            self.add(new_ip)

    def load_vlans(self):
        """Add Nautobot VLAN objects as DiffSync VLAN models."""
        for vlan in VLAN.objects.all():
            if PLUGIN_CFG.get("verbose_debug"):
                self.job.log_debug(message=f"Loading VLAN: {vlan.name}.")
            try:
                _vlan = self.vlan(
                    name=vlan.name,
                    vlan_id=vlan.vid,
                    description=vlan.description if vlan.description else "",
                    building=vlan.site.name if vlan.site else "Unknown",
                    custom_fields=nautobot.get_custom_field_dicts(vlan.get_custom_fields()),
                    tags=nautobot.get_tag_strings(vlan.tags),
                )
                self.add(_vlan)
            except ObjectAlreadyExists as err:
                if PLUGIN_CFG.get("verbose_debug"):
                    self.job.log_warning(err)

    def load_cables(self):
        """Add Nautobot Cable objects as DiffSync Connection models."""
        for _cable in Cable.objects.all():
            new_conn = self.conn(
                src_device="",
                src_port="",
                src_type="interface",
                dst_device="",
                dst_port="",
                dst_type="interface",
                tags=nautobot.get_tag_strings(_cable.tags),
            )
            new_conn = self.add_src_connection(
                cable_term_type=_cable.termination_a_type, cable_term_id=_cable.termination_a_id, connection=new_conn
            )
            new_conn = self.add_dst_connection(
                cable_term_type=_cable.termination_b_type, cable_term_id=_cable.termination_b_id, connection=new_conn
            )
            self.add(new_conn)
            # Now to ensure that diff matches, add a connection from reverse side.
            new_conn = self.add_src_connection(
                cable_term_type=_cable.termination_b_type, cable_term_id=_cable.termination_b_id, connection=new_conn
            )
            new_conn = self.add_dst_connection(
                cable_term_type=_cable.termination_a_type, cable_term_id=_cable.termination_a_id, connection=new_conn
            )
            self.add(new_conn)

    def add_src_connection(
        self, cable_term_type: Cable, cable_term_id: Cable, connection: dcim.Connection
    ) -> dcim.Connection:
        """Method to fill in source portion of a Connection object.

        Works in conjunction with the `load_cables` and `add_dst_connection` methods.

        Args:
            cable_term_type (Cable): The `termination_a_type` or `termination_b_type` attribute from a Cable object.
            cable_term_id (Cable): The `termination_a_id` or `termination_b_id` attribute from a Cable object.
            connection (dcim.Connection): Connection object being created. Expected to be empty with tags and types default `interface` type set for src side.

        Returns:
            dcim.Connection: Updated Connection object with source attributes populated.
        """
        if "interface" in str(cable_term_type):
            src_port = Interface.objects.get(id=cable_term_id)
            if src_port.mac_address:
                mac_addr = str(src_port.mac_address).replace(":", "").lower()
            else:
                mac_addr = None
            connection.src_port = src_port.name
            connection.src_device = src_port.device.name
            connection.src_port_mac = mac_addr
        elif "circuit" in str(cable_term_type):
            connection.src_type = "circuit"
            connection.src_port = CircuitTermination.objects.get(id=cable_term_id).circuit.cid
            connection.src_device = CircuitTermination.objects.get(id=cable_term_id).circuit.cid
        return connection

    def add_dst_connection(
        self, cable_term_type: Cable, cable_term_id: Cable, connection: dcim.Connection
    ) -> dcim.Connection:
        """Method to fill in destination portion of a Connection object.

        Works in conjunction with the `load_cables` and `add_src_connection` methods.

        Args:
            cable_term_type (Cable): The `termination_a_type` or `termination_b_type` attribute from a Cable object.
            cable_term_id (Cable): The `termination_a_id` or `termination_b_id` attribute from a Cable object.
            connection (dcim.Connection): Connection object being created. Expected to be empty with tags and types default `interface` type set for dst side.

        Returns:
            dcim.Connection: Updated Connection object with destination attributes populated.
        """
        if "interface" in str(cable_term_type):
            dst_port = Interface.objects.get(id=cable_term_id)
            if dst_port.mac_address:
                mac_addr = str(dst_port.mac_address).replace(":", "").lower()
            else:
                mac_addr = None
            connection.dst_port = dst_port.name
            connection.dst_device = dst_port.device.name
            connection.dst_port_mac = mac_addr
        elif "circuit" in str(cable_term_type):
            connection.dst_type = "circuit"
            connection.dst_port = CircuitTermination.objects.get(id=cable_term_id).circuit.cid
            connection.dst_device = CircuitTermination.objects.get(id=cable_term_id).circuit.cid
        return connection

    def load_providers(self):
        """Add Nautobot Provider objects as DiffSync Provider models."""
        for _prov in Provider.objects.all():
            new_prov = self.provider(
                name=_prov.name,
                notes=_prov.comments,
                vendor_url=_prov.portal_url,
                vendor_acct=_prov.account,
                vendor_contact1=_prov.noc_contact,
                vendor_contact2=_prov.admin_contact,
                tags=nautobot.get_tag_strings(_prov.tags),
            )
            self.add(new_prov)

    def load_circuits(self):
        """Add Nautobot Circuit objects as DiffSync Circuit models."""
        for _circuit in Circuit.objects.all():
            new_circuit = self.circuit(
                circuit_id=_circuit.cid,
                provider=_circuit.provider.name,
                notes=_circuit.comments,
                type=_circuit.type.name,
                status=_circuit.status.name,
                install_date=_circuit.install_date,
                bandwidth=_circuit.commit_rate,
                tags=nautobot.get_tag_strings(_circuit.tags),
            )
            if hasattr(_circuit.termination_a, "connected_endpoint") and hasattr(
                _circuit.termination_a.connected_endpoint, "name"
            ):
                new_circuit.origin_int = _circuit.termination_a.connected_endpoint.name
                new_circuit.origin_dev = _circuit.termination_a.connected_endpoint.device.name
            if hasattr(_circuit.termination_z, "connected_endpoint") and hasattr(
                _circuit.termination_z.connected_endpoint, "name"
            ):
                new_circuit.endpoint_int = _circuit.termination_z.connected_endpoint.name
                new_circuit.endpoint_dev = _circuit.termination_z.connected_endpoint.device.name
            self.add(new_circuit)

    def load(self):
        """Load data from Nautobot."""
        # Import all Nautobot Site records as Buildings
        self.load_sites()
        self.load_rackgroups()
        self.load_racks()
        self.load_manufacturers()
        self.load_device_types()
        self.load_vrfs()
        self.load_vlans()
        self.load_prefixes()
        self.load_virtual_chassis()
        self.load_devices()
        self.load_interfaces()
        self.load_ip_addresses()
        self.load_cables()
        self.load_providers()
        self.load_circuits()
