"""DiffSyncModel DCIM subclasses for Nautobot Device42 data sync."""

import re
from typing import Optional, List
from decimal import Decimal
from django.utils.text import slugify
from diffsync import DiffSyncModel
from nautobot.core.settings_funcs import is_truthy
from nautobot.extras.models import Status as NautobotStatus
from nautobot.dcim.models import Site as NautobotSite
from nautobot.dcim.models.racks import RackGroup as NautobotRackGroup
from nautobot.dcim.models.racks import Rack as NautobotRack
from nautobot.dcim.models import Manufacturer as NautobotManufacturer
from nautobot.dcim.models import DeviceType as NautobotDeviceType
from nautobot.dcim.models import Device as NautobotDevice
from nautobot.dcim.models import VirtualChassis as NautobotVC
from nautobot.dcim.models import Interface as NautobotInterface
from nautobot.ipam.models import VLAN as NautobotVLAN
from nautobot_device42_sync.diffsync import nbutils
from nautobot_device42_sync.constant import DEFAULTS, PLUGIN_CFG


def find_device_role_from_tags(diffsync, tag_list: List[str]) -> str or bool:
    """Determine a Device role based upon a Tag matching the `role_prepend` setting.

    Args:
        tag_list (List[str]): List of Tags as strings to search.

    Returns:
        DEFAULTS["device_role"]: The Default device role defined in plugin settings.
    """
    if not PLUGIN_CFG.get("role_prepend"):
        print("You must have the `role_prepend` setting configured.")
        raise MissingConfigSetting(setting="role_prepend")
    _prepend = PLUGIN_CFG.get("role_prepend")
    for _tag in tag_list:
        if re.search(_prepend, _tag):
            return re.sub(_prepend, "", _tag)
    return DEFAULTS.get("device_role")


class MissingConfigSetting(Exception):
    """Exception raised for missing configuration settings.

    Attributes:
        message (str): Returned explanation of Error.
    """

    def __init__(self, setting):
        """Initialize Exception with Setting that is missing and message."""
        self.setting = setting
        self.message = f"Missing configuration setting - {setting}!"
        super().__init__(self.message)


class Building(DiffSyncModel):
    """Device42 Building model."""

    _modelname = "building"
    _identifiers = ("name",)
    _shortname = ("name",)
    _attributes = ("address", "latitude", "longitude", "contact_name", "contact_phone", "tags")
    _children = {"room": "rooms"}
    name: str
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    contact_name: Optional[str]
    contact_phone: Optional[str]
    rooms: List["Room"] = list()
    tags: Optional[List[str]]

    @classmethod
    def _get_facility(cls, diffsync, tags: List[str]):
        """Determine Site facility from a specified Tag."""
        if PLUGIN_CFG.get("facility_prepend"):
            for _tag in tags:
                if re.search(PLUGIN_CFG.get("facility_prepend"), _tag):
                    return re.sub(PLUGIN_CFG.get("facility_prepend"), "", _tag)
        else:
            diffsync.job.log_failure("The `facility_prepend` setting is missing or invalid.")
            raise MissingConfigSetting("facility_prepend")

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
        if attrs.get("tags"):
            for _tag in nbutils.get_tags(attrs["tags"]):
                new_site.tags.add(_tag)
            _facility = cls._get_facility(diffsync, tags=attrs["tags"])
            if _facility:
                new_site.facility = _facility.upper()
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
    _attributes = ("height", "numbering_start_from_bottom", "tags")
    _children = {}
    name: str
    building: str
    room: str
    height: int
    numbering_start_from_bottom: str
    tags: Optional[List[str]]

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
        if attrs.get("tags"):
            for _tag in nbutils.get_tags(attrs["tags"]):
                new_rack.tags.add(_tag)
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
        diffsync.job.log_debug(f"Creating Manufacturer {ids['name']}")
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
        diffsync.job.log_debug(f"Creating DeviceType {ids['name']}")
        try:
            NautobotDeviceType.objects.get(slug=slugify(ids["name"]))
        except NautobotDeviceType.DoesNotExist:
            new_dt = NautobotDeviceType(
                model=ids["name"],
                slug=slugify(ids["name"]),
                manufacturer=NautobotManufacturer.objects.get(slug=slugify(attrs["manufacturer"])),
                part_number=attrs["part_number"] if attrs.get("part_number") else "",
                u_height=int(attrs["size"]) if attrs.get("size") else 1,
                is_full_depth=bool(attrs.get("depth") == "Full Depth"),
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
    _attributes = ("hardware", "platform", "facility", "members", "tags")
    _children = {"port": "interfaces"}
    name: str
    hardware: str
    platform: str
    facility: str
    members: Optional[List[str]]
    interfaces: Optional[List["Port"]] = list()
    tags: Optional[List[str]]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Virtual Chassis object in Nautobot.

        As the master node of the VC needs to be a regular Device, we'll create that and then the VC.
        Member devices will be added to VC at Device creation.
        """
        diffsync.job.log_debug(f"Creating VC Master Device {ids['name']}.")
        try:
            new_master = NautobotDevice(
                name=ids["name"],
                device_type=NautobotDeviceType.objects.get(model=attrs["hardware"]),
                device_role=nbutils.verify_device_role(find_device_role_from_tags(diffsync, tag_list=attrs["tags"])),
                status=NautobotStatus.objects.get(name="Active"),
                site=NautobotSite.objects.get(facility=attrs["facility"]) if attrs.get("facility") else None,
            )
            new_master.validated_save()
            new_vc = NautobotVC(
                name=ids["name"],
                master=new_master,
            )
            if attrs.get("tags"):
                for _tag in nbutils.get_tags(attrs["tags"]):
                    new_vc.tags.add(_tag)
            new_vc.validated_save()
            new_master.virtual_chassis = new_vc
            new_master.vc_position = 1
            if attrs.get("tags"):
                for _tag in nbutils.get_tags(attrs["tags"]):
                    new_master.tags.add(_tag)
            new_master.validated_save()
        except NautobotDeviceType.DoesNotExist as err:
            print(f"Can't find DeviceType {attrs['hardware']} {err}")
        except NautobotSite.DoesNotExist as err:
            print(f"Can't find Site facility {attrs['facility']} {err}")
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Virtual Chassis object in Nautobot."""
        return super().update(attrs)

    def delete(self):
        """Delete Virtual Chassis object from Nautobot.

        Because Virtual Chassis has a direct relationship with Devices it can't be deleted before they are.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"Virtual Chassis {self.name} will be deleted.")
        super().delete()
        _cluster = NautobotVC.objects.get(**self.get_identifiers())
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
        "customer",
        "room",
        "rack",
        "rack_position",
        "rack_orientation",
        "hardware",
        "os",
        "in_service",
        "serial_no",
        "tags",
        "cluster_host",
    )
    _children = {"port": "interfaces"}
    name: str
    dtype: str
    building: Optional[str]
    customer: Optional[str]
    room: Optional[str]
    rack: Optional[str]
    rack_position: Optional[float]
    rack_orientation: Optional[str]
    hardware: Optional[str]
    os: Optional[str]
    in_service: Optional[bool]
    interfaces: Optional[List["Port"]] = list()
    serial_no: Optional[str]
    tags: Optional[List[str]]
    cluster_host: Optional[str]

    @classmethod
    def _get_site(cls, diffsync, ids, attrs):
        if PLUGIN_CFG.get("customer_is_facility") and attrs.get("customer"):
            try:
                _site = NautobotSite.objects.get(facility=attrs["customer"])
                return _site
            except NautobotSite.DoesNotExist as err:
                diffsync.job.log_debug("Unable to find Site by facility. Attempting by Building.")

        if attrs.get("building"):
            try:
                _site = NautobotSite.objects.get(name=attrs["building"])
                return _site
            except NautobotSite.DoesNotExist as err:
                diffsync.job.log_debug(f"Unable to find Site. {err}")
        else:
            diffsync.job.log_debug(f"Device {ids['name']} is missing Building or Customer.")
            return False

    @classmethod
    def create(cls, diffsync, ids, attrs):  # pylint: disable=inconsistent-return-statements
        """Create Device object in Nautobot."""
        if attrs["in_service"]:
            _status = NautobotStatus.objects.get(name="Active")
        else:
            _status = NautobotStatus.objects.get(name="Offline")
        if attrs.get("building") or attrs.get("customer"):
            diffsync.job.log_debug(f"Creating device {ids['name']}.")
            if attrs.get("tags") and len(attrs["tags"]) > 0:
                _role = nbutils.verify_device_role(find_device_role_from_tags(diffsync, tag_list=attrs["tags"]))
            else:
                _role = nbutils.verify_device_role(role_name=DEFAULTS.get("device_role"))
            try:
                _dt = NautobotDeviceType.objects.get(model=attrs["hardware"])
                _site = cls._get_site(diffsync, ids, attrs)
                if not _site:
                    diffsync.job.log_debug(f"Can't create {ids['name']} as unable to determine Site.")
                    return None
                new_device = NautobotDevice(
                    name=ids["name"][:64],
                    status=_status,
                    site=_site,
                    device_type=_dt,
                    device_role=_role,
                    serial=attrs["serial_no"] if attrs.get("serial_no") else "",
                )
                if attrs.get("rack"):
                    new_device.rack = NautobotRack.objects.get(
                        name=attrs["rack"], site=_site, group__name=attrs["room"]
                    )
                    new_device.position = int(attrs["rack_position"]) if attrs["rack_position"] else None
                    new_device.face = attrs["rack_orientation"] if attrs["rack_orientation"] else "front"
                if attrs.get("os"):
                    new_device.platform = nbutils.verify_platform(
                        platform_name=attrs["os"],
                        manu=NautobotDeviceType.objects.get(model=attrs["hardware"]).manufacturer,
                        napalm_driver=attrs["os"],
                    )
                if attrs.get("cluster_host"):
                    try:
                        new_device.virtual_chassis = NautobotVC.objects.get(name=attrs["cluster_host"])
                        position = len(NautobotDevice.objects.filter(virtual_chassis__name=attrs["cluster_host"]))
                        new_device.vc_position = position + 1
                    except NautobotVC.DoesNotExist as err:
                        print(err)
                if attrs.get("tags"):
                    for _tag in nbutils.get_tags(attrs["tags"]):
                        new_device.tags.add(_tag)
                new_device.validated_save()
                return super().create(diffsync=diffsync, ids=ids, attrs=attrs)
            except NautobotRack.DoesNotExist:
                diffsync.job.log_debug(f"Unable to find matching Rack {attrs.get('rack')} for {_site.name}")
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
    _attributes = ("enabled", "mtu", "description", "mac_addr", "type", "mode", "tags", "vlans")
    _children = {}
    name: str
    device: str
    enabled: Optional[bool]
    mtu: Optional[int]
    description: Optional[str]
    mac_addr: Optional[str]
    type: str
    tags: Optional[List[str]]
    mode: Optional[str]
    vlans: Optional[List[dict]]

    @classmethod
    def create(cls, diffsync, ids, attrs):  # pylint: disable=inconsistent-return-statements
        """Create Interface object in Nautobot."""
        diffsync.job.log_debug(f"Creating Interface {ids['name']} for {ids['device']}.")
        try:
            if ids.get("device"):
                _dev = NautobotDevice.objects.get(name=ids["device"])
                new_intf = NautobotInterface(
                    name=ids["name"],
                    device=_dev,
                    enabled=is_truthy(attrs["enabled"]),
                    mtu=attrs["mtu"] if attrs.get("mtu") in range(1, 65537) else None,
                    description=attrs["description"],
                    type=attrs["type"],
                    mac_address=attrs["mac_addr"][:12] if attrs.get("mac_addr") else None,
                    mode=attrs["mode"],
                )
                if attrs.get("tags"):
                    for _tag in nbutils.get_tags(attrs["tags"]):
                        new_intf.tags.add(_tag)
                try:
                    if attrs.get("vlans"):
                        if attrs["mode"] == "access" and len(attrs["vlans"]) == 1:
                            _vlan = attrs["vlans"][0]
                            vlan_found = NautobotVLAN.objects.filter(
                                name=_vlan["vlan_name"], vid=_vlan["vlan_id"], site=_dev.site
                            )
                            if vlan_found:
                                new_intf.untagged_vlan = vlan_found[0]
                        else:
                            tagged_vlans = []
                            for _vlan in attrs["vlans"]:
                                tagged_vlan = NautobotVLAN.objects.filter(
                                    name=_vlan["vlan_name"], vid=_vlan["vlan_id"], site=_dev.site
                                )
                                if not tagged_vlan:
                                    tagged_vlan = NautobotVLAN.objects.filter(
                                        name=_vlan["vlan_name"], vid=_vlan["vlan_id"]
                                    )
                                if tagged_vlan:
                                    tagged_vlans.append(tagged_vlan[0])
                            new_intf.tagged_vlans.set(tagged_vlans)
                except NautobotVLAN.DoesNotExist as err:
                    diffsync.job.log_debug(f"{err}: {_vlan['vlan_name']} {_vlan['vlan_id']} ")
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
        _dev = NautobotInterface.objects.get(
            name=self.get_identifiers()["name"], device__name=self.get_identifiers()["device"]
        )
        self.diffsync._objects_to_delete["port"].append(_dev)  # pylint: disable=protected-access
        return self


Building.update_forward_refs()
Room.update_forward_refs()
Rack.update_forward_refs()
Vendor.update_forward_refs()
Cluster.update_forward_refs()
Device.update_forward_refs()
