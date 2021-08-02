"""DiffSyncModel subclasses for Nautobot-to-Device42 data sync."""

from django.utils.text import slugify
from diffsync import DiffSyncModel
from typing import Optional, List
from nautobot.core.settings_funcs import is_truthy
from nautobot.extras.models import Status as NautobotStatus
from nautobot.dcim.models import Site as NautobotSite
from nautobot.dcim.models.racks import RackGroup as NautobotRackGroup
from nautobot.dcim.models.racks import Rack as NautobotRack
from nautobot.dcim.models import Device as NautobotDevice
import nautobot_device42_sync.diffsync.nbutils as nbutils
from nautobot_device42_sync.constant import DEFAULTS
from decimal import Decimal


class Building(DiffSyncModel):
    """Device42 Building model."""

    _modelname = "building"
    _identifiers = ("name",)
    _shortname = ("name",)
    _attributes = ("address", "latitude", "longitude", "contact_name", "contact_phone")
    _children = {"room": "rooms"}
    name: str
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    contact_name: Optional[str]
    contact_phone: Optional[str]
    rooms: List["Room"] = list()

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Site object in Nautobot."""
        def_site_status = NautobotStatus.objects.get(name=DEFAULTS.get("site_status"))
        new_site = NautobotSite(
            name=ids["name"],
            slug=slugify(ids["name"]),
            status=def_site_status,
            physical_address=attrs["address"] if attrs.get("address") else "",
            latitude=round(Decimal(attrs["latitude"] if attrs["latitude"] else 0.0), 6),
            longitude=round(Decimal(attrs["longitude"] if attrs["longitude"] else 0.0), 6),
            contact_name=attrs["contact_name"] if attrs.get("contact_name") else "",
            contact_phone=attrs["contact_phone"] if attrs.get("contact_phone") else "",
        )
        new_site.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Site object in Nautobot."""
        return super().update(attrs)

    def delete(self):
        """Delete Site object from Nautobot."""
        self.diffsync.job.log_warning(f"Site {self.name} will be deleted.")
        _site = NautobotSite.objects.get(name=self.name)
        _site.delete()
        super().delete()
        return self


class Room(DiffSyncModel):
    """Device42 Room model."""

    _modelname = "room"
    _identifiers = ("name", "building")
    _shortname = ("name",)
    _attributes = ("notes",)
    _children = {"rack": "racks"}
    name: str
    building: str
    notes: Optional[str]
    racks: List["Rack"] = list()

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create RackGroup object in Nautobot."""
        new_rg = NautobotRackGroup(
            name=ids["name"],
            slug=slugify(ids["name"]),
            site=NautobotSite.objects.get(name=ids["building"]),
            description=attrs["notes"] if attrs.get("notes") else "",
        )
        new_rg.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update RackGroup object in Nautobot."""
        return super().update(attrs)

    def delete(self):
        """Delete RackGroup object from Nautobot."""
        self.diffsync.job.log_warning(f"Room {self.name} will be deleted.")
        _rg = NautobotRackGroup.objects.get(name=self.name)
        _rg.delete()
        super().delete()
        return self


class Rack(DiffSyncModel):
    """Device42 Rack model."""

    _modelname = "rack"
    _identifiers = ("name", "building", "room")
    _shortname = ("name",)
    _attributes = ("height", "numbering_start_from_bottom")
    _children = {
        "device": "devices",
    }
    name: str
    building: str
    room: str
    height: int
    numbering_start_from_bottom: str
    devices: List["Device"] = list()

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Rack object in Nautobot."""
        _site = NautobotSite.objects.get(name=ids["building"])
        _rg = NautobotRackGroup.objects.get(name=ids["room"], site__name=ids["building"])
        new_rack = NautobotRack(
            name=ids["name"],
            site=_site,
            group=_rg,
            status=NautobotStatus.objects.get(name=DEFAULTS.get("rack_status")),
            u_height=attrs["height"] if attrs.get("height") else 1,
            desc_units=not (is_truthy(attrs["numbering_start_from_bottom"])),
        )
        new_rack.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Rack object in Nautobot."""
        return super().update(attrs)

    def delete(self):
        """Delete Rack object from Nautobot."""
        self.diffsync.job.log_warning(f"Rack {self.name} will be deleted.")
        _rack = NautobotRack.objects.get(name=self.name, site=NautobotSite.objects.get(name=self.building))
        _rack.delete()
        super().delete()
        return self


class Vendor(DiffSyncModel):
    """Device42 Vendor model."""

    _modelname = "vendor"
    _identifiers = ("name",)
    _shortname = ("name",)
    _attributes = (
        "contact_info",
        "escalation_1",
        "home_page",
    )
    _children = {
        "hardware": "models",
    }
    name: str
    vendor_id: int
    contact_info: Optional[str]
    escalation_1: Optional[str]
    home_page: Optional[str]
    models: List["Hardware"] = list()


class Hardware(DiffSyncModel):
    """Device42 Hardware model."""

    _modelname = "hardware"
    _identifiers = (
        "name",
        "hardware_id",
    )
    _shortname = ("name",)
    _attributes = (
        "size",
        "type",
        "depth",
        "part_no",
        "manufacturer",
        "watts",
        "network_device",
        "blade_host",
    )
    _children = {
        "device": "devices",
    }
    name: str
    hardware_id: int
    size: float
    type: Optional[str]
    depth: str
    part_no: Optional[str]
    manufacturer: str
    watts: Optional[int]
    network_device: Optional[bool]
    blade_host: Optional[bool]
    devices: List["Device"] = list()


class Device(DiffSyncModel):
    """Device42 Device model."""

    _modelname = "device"
    _identifiers = (
        "name",
        "device_id",
    )
    _shortname = ("name",)
    _attributes = (
        "asset_no",
        "serial_no",
        "type",
    )
    _children = {}
    name: str
    device_id: int
    type: str
    site: str
    hardware: str
    primary_ip4: str
    asset_no: Optional[str]
    serial_no: Optional[str]
    tags: List[Optional[str]] = list()

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device object in Nautobot."""
        new_device = NautobotDevice(
            name=ids["name"],
            status=attrs["status"] if attrs.get("status") else DEFAULTS.get("status"),
            site=attrs["site"] if attrs.get("site") else nbutils.verify_site(DEFAULTS.get("site")),
            device_type=attrs["hardware"] if attrs.get("device_type") else DEFAULTS.get("device_type"),
            device_role=attrs["role"] if attrs.get("role") else DEFAULTS.get("role"),
            asset_tag=attrs["asset_no"],
            serial=attrs["serial_no"],
        )
        new_device.validated_save()
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def update(self, diffsync, attrs):
        """Update Device object in Nautobot."""
        return super().update(attrs, diffsync)

    def delete(self):
        """Delete Device object from Nautobot."""
        self.diffsync.job.log_warning(f"Device {self.name} will be deleted.")
        device = NautobotDevice.objects.get(name=self.name)
        device.delete()
        super().delete()
        return self


Building.update_forward_refs()
Room.update_forward_refs()
Rack.update_forward_refs()
