"""DiffSync adapter class for Nautobot as source-of-truth."""

import dns.resolver
import ipaddress
import re
from django.contrib.contenttypes.models import ContentType
from django.db.models import ProtectedError
from diffsync import DiffSync
from diffsync.exceptions import ObjectAlreadyExists
from nautobot.core.settings_funcs import is_truthy
from nautobot.dcim.models import (
    Site,
    RackGroup,
    Rack,
    Manufacturer,
    DeviceType,
    Device,
    VirtualChassis,
    Interface,
    Cable,
)
from nautobot.ipam.models import VRF, Prefix, IPAddress, VLAN
from nautobot.extras.models import Status
from nautobot.extras.choices import LogLevelChoices
from nautobot_device42_sync.diffsync.from_d42.models import dcim
from nautobot_device42_sync.diffsync.from_d42.models import ipam
from nautobot_device42_sync.constant import USE_DNS
from nautobot_device42_sync.diffsync import nbutils


class NautobotAdapter(DiffSync):
    """Nautobot adapter for DiffSync."""

    _objects_to_delete = {
        "device": [],
        "site": [],
        "rack_group": [],
        "rack": [],
        "manufacturer": [],
        "device_type": [],
        "vrf": [],
        "cluster": [],
        "port": [],
        "subnet": [],
        "ipaddr": [],
        "vlan": [],
        "cable": [],
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
            "device",
            "site",
            "rack_group",
            "rack",
            "manufacturer",
            "vrf",
            "ipaddr",
            "cluster",
            "port",
            "vlan",
        ):
            for nautobot_object in self._objects_to_delete[grouping]:
                try:
                    nautobot_object.delete()
                except ProtectedError:
                    self.job.log(
                        f"Deletion failed protected object: {nautobot_object}", log_level=LogLevelChoices.LOG_FAILURE
                    )
            self._objects_to_delete[grouping] = []

        self.set_primary_from_dns()

    def set_primary_from_dns(self):
        """Method to resolve Device FQDNs A records into an IP and set primary IP for that Device to it if found.

        Checks if `use_dns` setting variable is `True`.
        """
        if is_truthy(USE_DNS):
            for _dev in Device.objects.all():
                _devname = _dev.name.strip()
                if not re.search(r"\s-\s\w+\s?\d+", _devname):
                    _devname = re.search(
                        r"[a-zA-Z0-9\.\/\?\:\-_=#]+\.[a-zA-Z]{2,6}[a-zA-Z0-9\.\&\\?\:@\-_=#]", _dev.name
                    )
                    if _devname:
                        _devname = _devname.group()
                    else:
                        continue
                    print(f"Attempting to resolve {_dev.name} _devname: {_devname}")
                    try:
                        answ = dns.resolver.resolve(_devname, "A")
                        _ans = answ[0].to_text()
                    except dns.resolver.NXDOMAIN as err:
                        print(err)
                        continue
                    except dns.resolver.NoAnswer as err:
                        print(f"No record found for {_devname} {err}")
                        continue
                    if _dev.primary_ip and _ans == _dev.primary_ip:
                        print(f"Primary IP for {_dev.name} already matches DNS. No need to change anything.")
                        continue
                    try:
                        print(
                            f"{_dev.name} missing primary IP / or it doesn't match DNS response. Updating primary IP to {_ans}."
                        )
                        _ip = IPAddress.objects.get(host=_ans)
                        if _ip:
                            nbutils.assign_primary(dev=_dev, ipaddr=_ip)
                    except IPAddress.DoesNotExist as err:
                        print(f"Unable to find IP Address {_ans}.")
                        _intf = nbutils.get_or_create_mgmt_intf(intf_name="Management", dev=_dev)
                        _intf.validated_save()
                        _pf = Prefix.objects.net_contains(f"{_ans}/32")
                        # the last Prefix is the most specific and is assumed the one the IP address resides in
                        _range = _pf[len(_pf) - 1]
                        if _range:
                            _ip = IPAddress(
                                address=f"{_ans}/{_range.prefix_length}",
                                vrf=_range.vrf,
                                status=Status.objects.get(name="Active"),
                                description="Management address via DNS",
                            )
                            _ip.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                            _ip.assigned_object_id = _intf.id
                            _ip.validated_save()
                        nbutils.assign_primary(_dev, _ip)
                else:
                    print(f"Skipping {_devname} due to invalid Device name.")

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
                    tags=nbutils.get_tag_strings(site.tags),
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
                    tags=nbutils.get_tag_strings(rack.tags),
                )
                self.add(new_rack)
                _room = self.get(self.room, {"name": rack.group, "building": _building_name})
                _room.add_child(child=new_rack)
            except ObjectAlreadyExists as err:
                print(err)

    def load_manufacturers(self):
        """Add Nautobot Manufacturer objects as DiffSync Vendor models."""
        for manu in Manufacturer.objects.all():
            new_manu = self.vendor(name=manu.name)
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
            )
            self.add(dtype)

    def load_virtual_chassis(self):
        """Add Nautobot Virtual Chassis objects as DiffSync."""
        # We import the master node as a VC
        for _vc in VirtualChassis.objects.all():
            new_vc = self.cluster(
                name=_vc.name,
                hardware=_vc.master.device_type.model,
                platform=_vc.master.platform.napalm_driver if _vc.master.platform else "",
                facility=_vc.master.site.facility,
                tags=nbutils.get_tag_strings(_vc.tags),
            )
            self.add(new_vc)

    def load_devices(self):
        """Add Nautobot Device objects as DiffSync Device models."""
        for dev in Device.objects.all():
            # self.job.log_debug(f"Loading Device: {dev.name}.")
            _dev = self.device(
                name=dev.name,
                dtype="physical",
                building=dev.site.name,
                room=dev.rack.group.name if dev.rack else None,
                rack=dev.rack.name if dev.rack else None,
                rack_position=dev.position,
                rack_orientation=dev.face,
                hardware=dev.device_type.model,
                os=dev.platform.napalm_driver if dev.platform else "",
                in_service=bool(dev.status == "Active"),
                serial_no=dev.serial if dev.serial else "",
                tags=nbutils.get_tag_strings(dev.tags),
            )
            self.add(_dev)

    def load_interfaces(self):
        """Add Nautobot Interface objects as DiffSync Port models."""
        for port in Interface.objects.all():
            # self.job.log_debug(f"Loading Interface: {port.name} for {port.device}.")
            if port.mac_address:
                _mac_addr = str(port.mac_address).strip(":").lower()
            else:
                _mac_addr = None
            _port = self.port(
                name=port.name,
                device=port.device.name,
                enabled=port.enabled,
                mtu=port.mtu,
                description=port.description,
                mac_addr=_mac_addr,
                type=port.type,
                tags=nbutils.get_tag_strings(port.tags),
                mode=port.mode,
            )
            if port.mode == "access" and port.untagged_vlan:
                _port.vlans = [
                    {
                        "vlan_name": port.untagged_vlan.name,
                        "vlan_id": str(port.untagged_vlan.vid),
                    }
                ]
            else:
                _vlans = []
                for _vlan in port.tagged_vlans.values():
                    _vlans.append(
                        {
                            "vlan_name": _vlan["name"],
                            "vlan_id": _vlan["vid"],
                        }
                    )
                _port.vlans = _vlans
            try:
                self.add(_port)
            except ObjectAlreadyExists as err:
                self.job.log_debug(f"Port already exists for {port.device_name}. {err}")
                continue

    def load_vrfs(self):
        """Add Nautobot VRF objects as DiffSync VRFGroup models."""
        # self.job.log_debug(f"Loading VRF: {self.name}.")
        for vrf in VRF.objects.all():
            _vrf = self.vrf(
                name=vrf.name,
                description=vrf.description,
                tags=nbutils.get_tag_strings(vrf.tags),
            )
            self.add(_vrf)

    def load_prefixes(self):
        """Add Nautobot Prefix objects as DiffSync Subnet models."""
        for _pf in Prefix.objects.all():
            # self.job.log_debug(f"Loading Prefix: {_pf.prefix}.")
            ip_net = ipaddress.ip_network(_pf.prefix)
            new_pf = self.subnet(
                network=str(ip_net.network_address),
                mask_bits=str(ip_net.prefixlen),
                description=_pf.description,
                vrf=_pf.vrf.name,
                tags=nbutils.get_tag_strings(_pf.tags),
            )
            self.add(new_pf)

    def load_ip_addresses(self):
        """Add Nautobot IPAddress objects as DiffSync IPAddress models."""
        for _ip in IPAddress.objects.all():
            # self.job.log_debug(f"Loading IPAddress: {_ip.address}.")
            new_ip = self.ipaddr(
                address=str(_ip.address),
                available=bool(_ip.status.name != "Active"),
                label=_ip.description,
                vrf=_ip.vrf.name if _ip.vrf else None,
                tags=nbutils.get_tag_strings(_ip.tags),
            )
            if _ip.assigned_object_id:
                _intf = Interface.objects.get(id=_ip.assigned_object_id)
                new_ip.interface = _intf.name
                new_ip.device = _intf.device.name
            self.add(new_ip)

    def load_vlans(self):
        """Add Nautobot VLAN objects as DiffSync VLAN models."""
        for vlan in VLAN.objects.all():
            self.job.log_debug(f"Loading VLAN: {vlan.name}.")
            try:
                _vlan = self.vlan(
                    name=vlan.name,
                    vlan_id=vlan.vid,
                    description=vlan.description,
                    building=vlan.site.name if vlan.site else "Unknown",
                )
                self.add(_vlan)
            except ObjectAlreadyExists as err:
                print(err)

    def load_cables(self):
        """Add Nautobot Cable objects as DiffSync Connection models."""
        for _cable in Cable.objects.all():
            src_port = Interface.objects.get(id=_cable.termination_a_id)
            dst_port = Interface.objects.get(id=_cable.termination_b_id)
            new_conn = self.conn(
                src_device=src_port.device.name,
                src_port=src_port.name,
                src_port_mac=str(src_port.mac_address).strip(":").lower(),
                dst_device=dst_port.device.name,
                dst_port=dst_port.name,
                dst_port_mac=str(dst_port.mac_address).strip(":").lower(),
            )
            self.add(new_conn)

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
