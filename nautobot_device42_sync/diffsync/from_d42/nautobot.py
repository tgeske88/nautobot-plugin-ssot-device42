"""DiffSync adapter class for Nautobot as source-of-truth."""

import ipaddress
from django.db.models import ProtectedError
from diffsync import DiffSync
from nautobot.dcim.models import Site
from nautobot.dcim.models.device_components import Interface
from nautobot.dcim.models.devices import Manufacturer, DeviceType, Device
from nautobot.dcim.models.racks import RackGroup, Rack
from nautobot.ipam.models import VRF, Prefix
from nautobot.extras.choices import LogLevelChoices
from nautobot.virtualization.models import Cluster
from nautobot_device42_sync.diffsync.from_d42.models import dcim
from nautobot_device42_sync.diffsync.from_d42.models import ipam


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

    top_level = [
        "building",
        "vendor",
        "hardware",
        "cluster",
        "vrf",
        "subnet",
        "device",
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
            self.job.log_debug(f"Loading Device: {dev.name}.")
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
            self.job.log_debug(f"Loading Interface: {port.name} for {port.device}.")
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
        self.job.log_debug(f"Loading VRF: {self.name}.")
        for vrf in VRF.objects.all():
            _vrf = self.vrf(
                name=vrf.name,
                description=vrf.description,
            )
            self.add(_vrf)

    def load_prefixes(self):
        """Add Nautobot Prefix objects as DiffSync Subnet models."""
        for _pf in Prefix.objects.all():
            self.job.log_debug(f"Loading Prefix: {_pf.prefix}.")
            ip_net = ipaddress.ip_network(_pf.prefix)
            new_pf = self.subnet(
                network=str(ip_net.network_address),
                mask_bits=str(ip_net.prefixlen),
                description=_pf.description,
                vrf=_pf.vrf.name,
            )
            self.add(new_pf)

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
