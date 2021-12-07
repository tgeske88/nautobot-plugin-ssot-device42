"""Utility functions for Nautobot ORM."""
from typing import List, OrderedDict

import random
from django.utils.text import slugify
from netutils.lib_mapper import ANSIBLE_LIB_MAPPER_REVERSE, NAPALM_LIB_MAPPER_REVERSE
from taggit.managers import TaggableManager
from nautobot.circuits.models import CircuitType
from nautobot.dcim.models import Device, DeviceRole, Interface, Manufacturer, Platform
from nautobot.extras.models import Tag, Relationship
from nautobot.ipam.models import IPAddress

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


def verify_device_role(role_name: str, role_color: str = None) -> DeviceRole:
    """Verifies DeviceRole object exists in Nautobot. If not, creates it.

    Args:
        role_name (str): Name of role to verify.
        role_color (str): Color of role to verify. Must be hex code format.

    Returns:
        DeviceRole: Created DeviceRole object.
    """
    if not role_color:
        role_color = get_random_color()
    try:
        role_obj = DeviceRole.objects.get(slug=slugify(role_name))
    except DeviceRole.DoesNotExist:
        role_obj = DeviceRole(name=role_name, slug=slugify(role_name), color=role_color)
        role_obj.validated_save()
    return role_obj


def verify_platform(platform_name: str, manu: str) -> Platform:
    """Verifies Platform object exists in Nautobot. If not, creates it.

    Args:
        platform_name (str): Name of platform to verify.
        manu (str): Name of platform manufacturer.

    Returns:
        DeviceRole: Created DeviceRole object.
    """
    if ANSIBLE_LIB_MAPPER_REVERSE.get(platform_name):
        _name = ANSIBLE_LIB_MAPPER_REVERSE[platform_name]
    else:
        _name = platform_name
    if platform_name in NAPALM_LIB_MAPPER_REVERSE:
        napalm_driver = NAPALM_LIB_MAPPER_REVERSE[platform_name]
    else:
        if "cisco_" in platform_name:
            napalm_driver = platform_name.strip("cisco_")
        else:
            napalm_driver = platform_name
    try:
        platform_obj = Platform.objects.get(slug=slugify(platform_name))
    except Platform.DoesNotExist:
        platform_obj = Platform(
            name=_name,
            slug=slugify(platform_name),
            manufacturer=Manufacturer.objects.get(name=manu),
            napalm_driver=napalm_driver,
        )
        platform_obj.validated_save()
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


def set_primary_ip_and_mgmt(ipaddr: IPAddress, dev: Device, intf: Interface):
    """Method to set primary IP for a Device and mark Interface as management only.

    Args:
        diffsync (object): DiffSync job for logging.
        ids (dict): IPAddress object identifier attributes.
        attrs (dict): IPAddress object attributes.
        ipaddr (NautobotIPAddress): IPAddress object being created.
        dev (Device): Device to have primary IP set on.
        intf (Interface): Interface to set as management.
    """
    if ipaddr.assigned_object.device != dev:
        if ipaddr.family == 6:
            ipaddr.assigned_object.device.primary_ip6 = None
        else:
            ipaddr.assigned_object.device.primary_ip4 = None
        ipaddr.assigned_object.device.validated_save()
        ipaddr.assigned_object = intf
        ipaddr.validated_save()
    assign_primary(dev=dev, ipaddr=ipaddr)
    print(f"{ipaddr.address} set to primary on {dev.name}")
    dev.validated_save()
    intf.mgmt_only = True
    intf.validated_save()


def assign_primary(dev: Device, ipaddr: IPAddress):
    """Method to assign IP address as primary to specified device.

    Expects the assigned interface for the IP to belong to the passed Device.

    Args:
        dev (Device): Device object that the IPAddress is expected to already be assigned to.
        ipaddr (IPAddress): IPAddress object that is to be primary for `dev`.
    """
    # Check if Interface assigned to IP matching DNS query matches Device that is being worked with.
    if ipaddr.assigned_object.device == dev:
        if ipaddr.family == 6:
            dev.primary_ip6 = ipaddr
        else:
            dev.primary_ip4 = ipaddr
        dev.validated_save()


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
                if relationship == _softwarelcm:
                    if len(queryset) > 0:
                        version = SoftwareLCM.objects.get(id=queryset.get().source_id).version
    return version


def get_version_from_custom_field(fields: OrderedDict):
    """Method to obtain a software version for a Device from its custom fields."""
    for field, value in fields.items():
        if field.label == "OS Version":
            return value
    return ""
