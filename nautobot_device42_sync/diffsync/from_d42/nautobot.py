"""DiffSync adapter class for Nautobot as source-of-truth."""

import dns.resolver
import ipaddress
import re
from django.contrib.contenttypes.models import ContentType
from django.db.models import ProtectedError
from diffsync import DiffSync
from nautobot.core.settings_funcs import is_truthy
from nautobot.dcim.models import Site
from nautobot.dcim.models.device_components import Interface
from nautobot.dcim.models.devices import Manufacturer, DeviceType, Device
from nautobot.dcim.models.racks import RackGroup, Rack
from nautobot.extras.models import Status
from nautobot.ipam.models import VRF, Prefix, IPAddress
from nautobot.extras.choices import LogLevelChoices
from nautobot.virtualization.models import Cluster
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
        "ip_address": [],
        "cluster": [],
        "port": [],
        "subnet": [],
        "ipaddr": [],
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

    top_level = [
        "building",
        "vendor",
        "hardware",
        "cluster",
        "vrf",
        "subnet",
        "device",
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
            "ip_address",
            "cluster",
            "port",
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
                    print(f"Attempting to resolve {_devname}")
                    try:
                        answ = dns.resolver.resolve(_devname, "A")
                        _ans = answ[0].to_text()
                    except dns.resolver.NXDOMAIN as err:
                        print(err)
                        continue
                    except:
                        continue
                    if _dev.primary_ip:
                        if _ans == _dev.primary_ip:
                            print(f"Primary IP for {_dev.name} already matches DNS. No need to change anything.")
                            continue
                    try:
                        print(
                            f"{_dev.name} doesn't have primary IP assigned or it doesn't match DNS. Updating primary IP to {_ans}."
                        )
                        _ip = IPAddress.objects.get(host=_ans)
                        if _ip:
                            if _ip.assigned_object_id:
                                # Check if Interface assigned to IP matching DNS query matches Device that is being worked with.
                                if Interface.objects.get(id=_ip.assigned_object_id).device.id == _dev.id:
                                    if ":" in _ans:
                                        _dev.primary_ip6 = _ip
                                    else:
                                        _dev.primary_ip4 = _ip
                                    _dev.validated_save()
                    except IPAddress.DoesNotExist as err:
                        print(f"Unable to find IP Address {_ans}.")
                        _intf = nbutils.get_or_create_mgmt_intf(intf_name="Management", dev=_dev)
                        _intf.validated_save()
                        _pf = Prefix.objects.net_contains(f"{_ans}/32")
                        _range = _pf[len(_pf) - 1]
                        if _range:
                            _nip = IPAddress(
                                address=f"{_ans}/{_range.prefix_length}",
                                vrf=_range.vrf.name,
                                status=Status.objects.get(name="Active"),
                                description="Management address via DNS",
                            )
                            _nip.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                            _nip.assigned_object_id = _intf.id
                            _nip.validated_save()
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
                )
                self.add(building)
            except AttributeError:
                continue

    def load_rackgroups(self):
        """Add Nautobot RackGroup objects as DiffSync Room models."""
        for _rg in RackGroup.objects.all():
            try:
                room = self.room(
                    name=_rg.name,
                    building=Site.objects.get(name=_rg.site).name,
                    notes=_rg.description,
                )
                self.add(room)
                _site = self.get(self.building, Site.objects.get(name=_rg.site).name)
                _site.add_child(child=room)
            except AttributeError:
                continue

    def load_racks(self):
        """Add Nautobot Rack objects as DiffSync Rack models."""
        for rack in Rack.objects.all():
            _building_name = Site.objects.get(name=rack.site).name
            new_rack = self.rack(
                name=rack.name,
                building=_building_name,
                room=RackGroup.objects.get(name=rack.group, site__name=_building_name).name,
                height=rack.u_height,
                numbering_start_from_bottom="no" if rack.desc_units else "yes",
            )
            self.add(new_rack)
            _room = self.get(self.room, {"name": rack.group, "building": _building_name})
            _room.add_child(child=new_rack)

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

    def load_clusters(self):
        """Add Nautobot Cluster objects as DiffSync Cluster models."""
        for clus in Cluster.objects.all():
            _clus = self.cluster(
                name=clus.name,
                ctype="cluster",
                building=clus.site,
            )
            self.add(_clus)

    def load_devices(self):
        """Add Nautobot Device objects as DiffSync Device models."""
        for dev in Device.objects.all():
            # self.job.log_debug(f"Loading Device: {dev.name}.")
            _dev = self.device(
                name=dev.name,
                dtype="physical",
                building=dev.site.name,
                room=dev.rack.group.name,
                rack=dev.rack.name,
                rack_position=dev.position,
                rack_orientation=dev.face,
                hardware=dev.device_type.model,
                os=dev.platform.napalm_driver if dev.platform else "",
                in_service=bool(dev.status == "Active"),
                serial_no=dev.serial if dev.serial else "",
                # tags=dev.tags,
            )
            self.add(_dev)
            if dev.cluster:
                _clus = self.get(self.cluster, {"name": dev.cluster})
                _clus.add_child(_dev)

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
            )
            self.add(_port)
            _dev = self.get(self.device, port.device.name)
            _dev.add_child(_port)

    def load_vrfs(self):
        """Add Nautobot VRF objects as DiffSync VRFGroup models."""
        # self.job.log_debug(f"Loading VRF: {self.name}.")
        for vrf in VRF.objects.all():
            _vrf = self.vrf(
                name=vrf.name,
                description=vrf.description,
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
            )
            if _ip.assigned_object_id:
                _intf = Interface.objects.get(id=_ip.assigned_object_id)
                new_ip.interface = _intf.name
                new_ip.device = _intf.device.name
            self.add(new_ip)

    def load(self):
        """Load data from Nautobot."""
        # Import all Nautobot Site records as Buildings
        self.load_sites()
        self.load_rackgroups()
        self.load_racks()
        self.load_manufacturers()
        self.load_device_types()
        self.load_clusters()
        self.load_devices()
        self.load_interfaces()
        self.load_vrfs()
        self.load_prefixes()
        self.load_ip_addresses()
