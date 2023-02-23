"""Utility functions for Nautobot ORM."""
from typing import List, OrderedDict
from uuid import UUID

import random
from django.utils.text import slugify
from netutils.lib_mapper import ANSIBLE_LIB_MAPPER_REVERSE, NAPALM_LIB_MAPPER_REVERSE, PYATS_LIB_MAPPER
from taggit.managers import TaggableManager
from nautobot.circuits.models import CircuitType
from nautobot.dcim.models import Device, DeviceRole, Interface, Platform
from nautobot.extras.models import Tag, Relationship

try:
    from nautobot_device_lifecycle_mgmt.models import SoftwareLCM

    LIFECYCLE_MGMT = True
except ImportError:
    print("Device Lifecycle plugin isn't installed so will revert to CustomField for OS version.")
    LIFECYCLE_MGMT = False


def get_random_color() -> str:
    """Get random hex code color string.

    Returns:
        str: Hex code value for a color with hash stripped.
    """
    return f"{'%06x' % random.randint(0, 0xFFFFFF)}"  # pylint: disable=consider-using-f-string


def verify_device_role(diffsync, role_name: str, role_color: str = None) -> UUID:
    """Verifies DeviceRole object exists in Nautobot. If not, creates it.

    Args:
        diffsync (obj): DiffSync Job object.
        role_name (str): Name of role to verify.
        role_color (str): Color of role to verify. Must be hex code format.

    Returns:
        UUID: ID of found or created DeviceRole object.
    """
    if not role_color:
        role_color = get_random_color()
    try:
        role_obj = diffsync.devicerole_map[slugify(role_name)]
    except KeyError:
        role_obj = DeviceRole(name=role_name, slug=slugify(role_name), color=role_color)
        diffsync.objects_to_create["deviceroles"].append(role_obj)
        diffsync.devicerole_map[slugify(role_name)] = role_obj.id
        role_obj = role_obj.id
    return role_obj


def verify_platform(diffsync, platform_name: str, manu: UUID) -> UUID:
    """Verifies Platform object exists in Nautobot. If not, creates it.

    Args:
        diffsync (obj): DiffSync Job with maps.
        platform_name (str): Name of platform to verify.
        manu (UUID): The ID (primary key) of platform manufacturer.

    Returns:
        UUID: UUID for found or created DeviceRole object.
    """
    if platform_name == "f5":
        platform_name = "bigip"
    os_name = platform_name.replace("-", "")
    if PYATS_LIB_MAPPER.get(os_name):
        _slug = PYATS_LIB_MAPPER[os_name]
    else:
        _slug = slugify(platform_name)
    if NAPALM_LIB_MAPPER_REVERSE.get(_slug):
        napalm_driver = NAPALM_LIB_MAPPER_REVERSE[_slug]
    else:
        napalm_driver = platform_name
    try:
        platform_obj = diffsync.platform_map[_slug]
    except KeyError:
        platform_obj = Platform(
            name=ANSIBLE_LIB_MAPPER_REVERSE[_slug] if ANSIBLE_LIB_MAPPER_REVERSE.get(_slug) else platform_name,
            slug=_slug,
            manufacturer_id=manu,
            napalm_driver=napalm_driver[:50],
        )
        diffsync.objects_to_create["platforms"].append(platform_obj)
        diffsync.platform_map[slugify(platform_name)] = platform_obj.id
        platform_obj = platform_obj.id
    return platform_obj


def get_or_create_mgmt_intf(intf_name: str, dev: Device) -> Interface:
    """Creates a Management interface with specified name.

    This is expected to be used when assigning a management IP to a device that doesn't
    have a Management interface and we can't determine which one to assign the IP to.

    Args:
        intf_name (str): Name of Interface to be created.
        dev (Device): Device object for Interface to be assigned to.

    Returns:
        Interface: Management Interface object that was created.
    """
    # check if Interface already exists, returns it or creates it
    try:
        mgmt_intf = Interface.objects.get(name=intf_name.strip(), device__name=dev.name)
    except Interface.DoesNotExist:
        print(f"Mgmt Intf Not Found! Creating {intf_name} {dev.name}")
        mgmt_intf = Interface(
            name=intf_name.strip(),
            device=dev,
            type="other",
            enabled=True,
            mgmt_only=True,
        )
        mgmt_intf.validated_save()
    return mgmt_intf


def get_or_create_tag(tag_name: str) -> Tag:
    """Finds or creates a Tag that matches `tag_name`.

    Args:
        tag_name (str): Name of Tag to be created.

    Returns:
        Tag: Tag object that was found or created.
    """
    try:
        _tag = Tag.objects.get(slug=slugify(tag_name))
    except Tag.DoesNotExist:
        new_tag = Tag(
            name=tag_name,
            slug=slugify(tag_name),
            color=get_random_color(),
        )
        new_tag.validated_save()
        _tag = new_tag
    return _tag


def get_tags(tag_list: List[str]) -> List[Tag]:
    """Gets list of Tags from list of strings.

    This is the opposite of the `get_tag_strings` function.

    Args:
        tag_list (List[str]): List of Tags as strings to find.

    Returns:
        (List[Tag]): List of Tag object primary keys matching list of strings passed in.
    """
    return [get_or_create_tag(x) for x in tag_list if x != ""]


def get_tag_strings(list_tags: TaggableManager) -> List[str]:
    """Gets string values of all Tags in a list.

    This is the opposite of the `get_tags` function.

    Args:
        list_tags (TaggableManager): List of Tag objects to convert to strings.

    Returns:
        List[str]: List of string values matching the Tags passed in.
    """
    _strings = list(list_tags.names())
    if len(_strings) > 1:
        _strings.sort()
    return _strings


def get_custom_field_dicts(cfields: OrderedDict) -> List[dict]:
    """Creates list of CustomField dicts with CF key, value, and description.

    Args:
        cfields (OrderedDict): List of CustomFields with their value.

    Returns:
        cf_list (List[dict]): Return a list of CustomField dicts with key, value, and note (description).
    """
    cf_list = []
    for _cf, _cf_value in cfields.items():
        custom_field = {
            "key": _cf.label,
            "value": _cf_value,
            "notes": _cf.description if _cf.description != "" else None,
        }
        cf_list.append(custom_field)
    return sorted(cf_list, key=lambda d: d["key"])


def verify_circuit_type(circuit_type: str) -> CircuitType:
    """Method to find or create a CircuitType in Nautobot.

    Args:
        circuit_type (str): Name of CircuitType to be found or created.

    Returns:
        CircuitType: CircuitType object found or created.
    """
    try:
        _ct = CircuitType.objects.get(slug=slugify(circuit_type))
    except CircuitType.DoesNotExist:
        _ct = CircuitType(
            name=circuit_type,
            slug=slugify(circuit_type),
        )
        _ct.validated_save()
    return _ct


def get_software_version_from_lcm(relations: dict):
    """Method to obtain Software version for a Device from Relationship.

    Args:
        relations (dict): Results of a `get_relationships()` on a Device.

    Returns:
        str: String of SoftwareLCM version.
    """
    version = ""
    if LIFECYCLE_MGMT:
        _softwarelcm = Relationship.objects.get(name="Software on Device")
        for _, relationships in relations.items():
            for relationship, queryset in relationships.items():
                if relationship == _softwarelcm and len(queryset) > 0:
                    version = queryset[0].source.version
    return version


def get_version_from_custom_field(fields: OrderedDict):
    """Method to obtain a software version for a Device from its custom fields."""
    for field, value in fields.items():
        if field.label == "OS Version":
            return value
    return ""


def determine_vc_position(vc_map: dict, virtual_chassis: str, device_name: str) -> int:
    """Determine position of Member Device in Virtual Chassis based on name and other factors.

    Args:
        vc_map (dict): Dictionary of virtual chassis positions mapped to devices.
        virtual_chassis (str): Name of the virtual chassis that device is being added to.
        device_name (str): Name of member device to be added in virtual chassis.

    Returns:
        int: Position for member device in Virtual Chassis. Will always be position 2 or higher as 1 is master device.
    """
    return sorted(vc_map[virtual_chassis]["members"]).index(device_name) + 2


def get_dlc_version_map():
    """Method to create nested dictionary of Software versions mapped to their ID along with Platform.

    This should only be used if the Device Lifecycle plugin is found to be installed.

    Returns:
        dict: Nested dictionary of versions mapped to their ID and to their Platform.
    """
    version_map = {}
    for ver in SoftwareLCM.objects.only("id", "device_platform", "version"):
        if ver.device_platform.slug not in version_map:
            version_map[ver.device_platform.slug] = {}
        version_map[ver.device_platform.slug][ver.version] = ver.id
    return version_map


def get_cf_version_map():
    """Method to create nested dictionary of Software versions mapped to their ID along with Platform.

    This should only be used if the Device Lifecycle plugin is not found. It will instead use custom field "OS Version".

    Returns:
        dict: Nested dictionary of versions mapped to their ID and to their Platform.
    """
    version_map = {}
    for dev in Device.objects.only("id", "platform", "_custom_field_data"):
        if dev.platform.slug not in version_map:
            version_map[dev.platform.slug] = {}
        if "os-version" in dev.custom_field_data:
            version_map[dev.platform.slug][dev.custom_field_data["os-version"]] = dev.id
    return version_map
