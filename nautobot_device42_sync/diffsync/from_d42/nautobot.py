"""DiffSync adapter class for Nautobot as source-of-truth."""

from diffsync import DiffSync
from nautobot.dcim.models import Site
from nautobot.dcim.models.devices import Manufacturer
from nautobot.dcim.models.racks import RackGroup, Rack
from nautobot_device42_sync.diffsync.from_d42 import models


class NautobotAdapter(DiffSync):
    """Nautobot adapter for DiffSync."""

    building = models.Building
    room = models.Room
    rack = models.Rack
    vendor = models.Vendor
    hardware = models.Hardware
    device = models.Device

    top_level = ["building", "vendor", "hardware", "device"]

    def __init__(self, *args, job=None, sync=None, **kwargs):
        """Initialize the Device42 DiffSync adapter."""
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync

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
        for rg in RackGroup.objects.all():
            try:
                room = self.room(name=rg.name, building=Site.objects.get(name=rg.site).name, notes=rg.description)
                self.add(room)
                _site = self.get(self.building, Site.objects.get(name=rg.site).name)
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

    def load_interface(self, interface_record, device_model):
        """Import a single Nautobot Interface object as a DiffSync Interface model."""
        interface = self.interface(
            diffsync=self,
            name=interface_record.name,
            device_name=device_model.name,
            description=interface_record.description,
            pk=interface_record.id,
        )
        self.add(interface)
        device_model.add_child(interface)

    def load(self):
        """Load data from Nautobot."""
        # Import all Nautobot Site records as Buildings
        self.load_sites()
        self.load_rackgroups()
        self.load_racks()
        self.load_manufacturers()
