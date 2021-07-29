"""DiffSync adapter class for Nautobot as source-of-truth."""

from diffsync import DiffSync
from nautobot.dcim.models import Site
from nautobot.dcim.models.racks import RackGroup
from nautobot_device42_sync.diffsync.from_d42 import models


class NautobotAdapter(DiffSync):
    """Nautobot adapter for DiffSync."""

    building = models.Building
    room = models.Room
    vendor = models.Vendor
    hardware = models.Hardware
    device = models.Device

    top_level = [
        "building",
    ]

    def __init__(self, *args, job=None, sync=None, **kwargs):
        """Initialize the Device42 DiffSync adapter."""
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync

    def load_sites(self):
        """Add Nautobot Site objects as DiffSync Building models."""
        for site in Site.objects.all():
            try:
                self.add(
                    self.building(
                        name=site.name,
                        address=site.physical_address,
                        latitude=site.latitude,
                        longitude=site.longitude,
                        contact_name=site.contact_name,
                        contact_phone=site.contact_phone,
                    )
                )
            except AttributeError:
                continue

    def load_rackgroups(self):
        """Add Nautobot RackGroup objects as DiffSync Room models."""
        for rg in RackGroup.objects.all():
            _building_name = Site.objects.get(name=rg.site).name
            try:
                self.add(self.room(name=rg.name, building=_building_name, notes=rg.description))
            except AttributeError:
                continue

    def load_interface(self, interface_record, device_model):
        """Import a single Nautobot Interface object as a DiffSync Interface model."""
        interface = self.interface(
            diffsync=self,
            name=interface_record.name,
            device_name=device_model.name,
            description=interface_record.description,
            pk=interface_record.pk,
        )
        self.add(interface)
        device_model.add_child(interface)

    def load(self):
        """Load data from Nautobot."""
        # Import all Nautobot Site records as Buildings
        self.load_sites()
        self.load_rackgroups()
