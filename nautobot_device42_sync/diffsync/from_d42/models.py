"""DiffSyncModel subclasses for Nautobot-to-Device42 data sync."""

from django.utils.text import slugify
from diffsync import DiffSyncModel
from typing import Optional, List
from nautobot.core.settings_funcs import is_truthy
from nautobot.extras.models import Status as NautobotStatus
from nautobot.dcim.models import Site as NautobotSite
from nautobot.dcim.models.racks import RackGroup as NautobotRackGroup
from nautobot.dcim.models.racks import Rack as NautobotRack
from nautobot.dcim.models import Manufacturer as NautobotManufacturer
from nautobot.dcim.models import DeviceType as NautobotDeviceType
from nautobot.dcim.models import Device as NautobotDevice
from nautobot.dcim.models import Interface as NautobotInterface
from nautobot.virtualization.models import Cluster as NautobotCluster
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
        """Delete Site object from Nautobot.

        Because Site has a direct relationship with many other objects it can't be deleted before anything else.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"Site {self.name} will be deleted.")
        super().delete()
        site = NautobotSite.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["site"].append(site)  # pylint: disable=protected-access
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
        """Delete RackGroup object from Nautobot.

        Because RackGroup has a direct relationship to Rack objects it can't be deleted before any Racks.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"RackGroup {self.name} will be deleted.")
        super().delete()
        rackgroup = NautobotRackGroup.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["rackgroup"].append(rackgroup)  # pylint: disable=protected-access
        return self


class Rack(DiffSyncModel):
    """Device42 Rack model."""

    _modelname = "rack"
    _identifiers = ("name", "building", "room")
    _shortname = ("name",)
    _attributes = ("height", "numbering_start_from_bottom")
    _children = {}
    name: str
    building: str
    room: str
    height: int
    numbering_start_from_bottom: str

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
        """Delete Rack object from Nautobot.

        Because Rack has a direct relationship with Devices it can't be deleted before they are.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"Rack {self.name} will be deleted.")
        super().delete()
        rack = NautobotRack.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["rack"].append(rack)  # pylint: disable=protected-access
        return self


class Vendor(DiffSyncModel):
    """Device42 Vendor model."""

    _modelname = "vendor"
    _identifiers = ("name",)
    _shortname = ("name",)
    _attributes = ()
    _children = {}
    name: str

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Manufacturer object in Nautobot."""
        diffsync.job.log_debug(message=f"Creating Manufacturer {ids['name']}")
        try:
            NautobotManufacturer.objects.get(slug=slugify(ids["name"]))
        except NautobotManufacturer.DoesNotExist:
            new_manu = NautobotManufacturer(
                name=ids["name"],
                slug=slugify(ids["name"]),
            )
            new_manu.validated_save()
            return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Manufactuer object in Nautobot."""
        return super().update(attrs)

    def delete(self):
        """Delete Manufacturer object from Nautobot.

        Because Manufacturer has a direct relationship with DeviceTypes and other objects it can't be deleted before them.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"Manufacturer {self.name} will be deleted.")
        super().delete()
        _manu = NautobotManufacturer.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["manufacturer"].append(_manu)  # pylint: disable=protected-access
        return self


class Hardware(DiffSyncModel):
    """Device42 Hardware model."""

    _modelname = "hardware"
    _identifiers = ("name",)
    _shortname = ("name",)
    _attributes = (
        "manufacturer",
        "size",
        "depth",
        "part_number",
    )
    _children = {}
    name: str
    manufacturer: str
    size: float
    depth: Optional[str]
    part_number: Optional[str]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create DeviceType object in Nautobot."""
        diffsync.job.log_debug(message=f"Creating DeviceType {ids['name']}")
        try:
            NautobotDeviceType.objects.get(slug=slugify(ids["name"]))
        except NautobotDeviceType.DoesNotExist:
            new_dt = NautobotDeviceType(
                model=ids["name"],
                slug=slugify(ids["name"]),
                manufacturer=NautobotManufacturer.objects.get(slug=slugify(attrs["manufacturer"])),
                part_number=attrs["part_number"] if attrs.get("part_number") else "",
                u_height=int(attrs["size"]) if attrs.get("size") else 1,
                is_full_depth=True if attrs.get("depth") == "Full Depth" else False,
            )
            new_dt.validated_save()
            return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update DeviceType object in Nautobot."""
        return super().update(attrs)

    def delete(self):
        """Delete DeviceType object from Nautobot.

        Because DeviceType has a direct relationship with Devices it can't be deleted before all Devices are.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"DeviceType {self.name} will be deleted.")
        super().delete()
        _dt = NautobotDeviceType.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["device_type"].append(_dt)  # pylint: disable=protected-access
        return self


class Cluster(DiffSyncModel):
    """Device42 Cluster model."""

    _modelname = "cluster"
    _identifiers = ("name",)
    _shortname = ("name",)
    _attributes = ("ctype", "building")
    _children = {"device": "devices"}
    name: str
    ctype: str
    building: Optional[str]
    devices: List["Device"] = list()

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Cluster object in Nautobot."""
        # diffsync.job.log_debug(message=f"Creating cluster {ids['name']}.")
        ctype = nbutils.verify_cluster_type("network")
        new_cluster = NautobotCluster(
            name=ids["name"],
            type=ctype,
            site=NautobotSite.objects.get(name=attrs["building"]) if attrs.get("building") else None,
        )
        new_cluster.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Cluster object in Nautobot."""
        return super().update(attrs)

    def delete(self):
        """Delete Cluster object from Nautobot.

        Because Cluster has a direct relationship with Devices it can't be deleted before they are.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"Cluster {self.name} will be deleted.")
        super().delete()
        _cluster = NautobotCluster.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["cluster"].append(_cluster)  # pylint: disable=protected-access
        return self


class Device(DiffSyncModel):
    """Device42 Device model."""

    _modelname = "device"
    _identifiers = ("name",)
    _shortname = ("name",)
    _attributes = (
        "dtype",
        "building",
        "room",
        "rack",
        "rack_position",
        "rack_orientation",
        "hardware",
        "os",
        "in_service",
        "ip_addresses",
        "serial_no",
        "tags",
        "cluster_host",
    )
    _children = {"port": "interfaces"}
    name: str
    dtype: str
    building: Optional[str]
    room: Optional[str]
    rack: Optional[str]
    rack_position: Optional[float]
    rack_orientation: Optional[str]
    hardware: Optional[str]
    os: Optional[str]
    in_service: Optional[bool]
    ip_addresses: Optional[List[str]] = list()
    interfaces: Optional[List["Port"]] = list()
    serial_no: Optional[str]
    tags: Optional[List[str]] = list()
    cluster_host: Optional[str]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Device object in Nautobot."""
        diffsync.job.log_debug(message=f"Creating device {ids['name']}.")
        if attrs["in_service"]:
            _status = NautobotStatus.objects.get(name="Active")
        else:
            _status = NautobotStatus.objects.get(name="Offline")
        if attrs.get("building"):
            try:
                _dt = NautobotDeviceType.objects.get(model=attrs["hardware"])
                new_device = NautobotDevice(
                    name=ids["name"],
                    status=_status,
                    site=NautobotSite.objects.get(name=attrs["building"]),
                    rack=NautobotRack.objects.get(
                        name=attrs["rack"], site__name=attrs["building"], group__name=attrs["room"]
                    ),
                    position=int(attrs["rack_position"]) if attrs["rack_position"] else None,
                    face=attrs["rack_orientation"] if attrs["rack_orientation"] else "front",
                    device_type=_dt,
                    device_role=nbutils.verify_device_role(role_name=DEFAULTS.get("device_role")),
                    serial=attrs["serial_no"] if attrs.get("serial_no") else "",
                )
                if attrs.get("os"):
                    new_device.platform = nbutils.verify_platform(
                        platform_name=attrs["os"],
                        manu=NautobotDeviceType.objects.get(model=attrs["hardware"]).manufacturer,
                        napalm_driver=attrs["os"],
                    )
                if attrs.get("cluster_host"):
                    new_device.cluster = NautobotCluster.objects.get(name=attrs["cluster_host"])
                new_device.validated_save()
                return super().create(diffsync=diffsync, ids=ids, attrs=attrs)
            except NautobotDeviceType.DoesNotExist:
                diffsync.job.log_debug(f"Unable to find matching DeviceType {attrs['hardware']} for {ids['name']}.")
        else:
            diffsync.job.log_debug(f"Device {ids['name']} is missing a Building and won't be created.")

    def update(self, attrs):
        """Update Device object in Nautobot."""
        return super().update(attrs)

    def delete(self):
        """Delete Device object from Nautobot.

        Because Device has a direct relationship with Ports and IP Addresses it can't be deleted before they are.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"Device {self.name} will be deleted.")
        super().delete()
        _dev = NautobotDevice.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["device"].append(_dev)  # pylint: disable=protected-access
        return self


class Port(DiffSyncModel):
    """Device42 Port model."""

    _modelname = "port"
    _identifiers = ("device", "name")
    _shortname = ("name",)
    _attributes = ("enabled", "mtu", "description", "mac_addr", "type")
    _children = {}
    name: str
    device: str
    enabled: Optional[bool]
    mtu: Optional[int]
    description: Optional[str]
    mac_addr: Optional[str]
    type: Optional[str]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Interface object in Nautobot."""
        # diffsync.job.log_debug("Creating Interface {ids['name']}.")
        try:
            if ids.get("device"):
                new_intf = NautobotInterface(
                    name=ids["name"],
                    device=NautobotDevice.objects.get(name=ids["device"]),
                    enabled=is_truthy(attrs["enabled"]),
                    mtu=attrs["mtu"] if attrs.get("mtu") else None,
                    description=attrs["description"],
                    type=attrs["type"],
                    mac_address=attrs["mac_addr"][:12] if attrs.get("mac_addr") else None,
                )
                new_intf.validated_save()
                return super().create(ids=ids, diffsync=diffsync, attrs=attrs)
        except NautobotDevice.DoesNotExist as err:
            print(f"{ids['name']} doesn't exist. {err}")

    def update(self, attrs):
        """Update Interface object in Nautobot."""
        return super().update(attrs)

    def delete(self):
        """Delete Interface object from Nautobot.

        Because Interface has a direct relationship with Cables and IP Addresses it can't be deleted before they are.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        print(f"Interface {self.name} for {self.device} will be deleted.")
        super().delete()
        _dev = NautobotInterface.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["port"].append(_dev)  # pylint: disable=protected-access
        return self


Building.update_forward_refs()
Room.update_forward_refs()
Rack.update_forward_refs()
Vendor.update_forward_refs()
Cluster.update_forward_refs()
Device.update_forward_refs()
