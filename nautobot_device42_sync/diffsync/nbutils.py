"""Utility functions for Nautobot ORM."""
from django.utils.text import slugify
from faker import Factory
from taggit.managers import TaggableManager
from typing import List
from nautobot.dcim.models import DeviceRole, Manufacturer, Platform, Device, Interface
from nautobot.extras.models import Tag
from nautobot.ipam.models import IPAddress


fake = Factory.create()


def get_random_color() -> str:
    """Get random hex code color string.

    Returns:
        str: Hex code value for a color with hash stripped.
    """
    return fake.hex_color().strip("#")


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


def verify_platform(platform_name: str, manu: str, napalm_driver: str = "") -> Platform:
    """Verifies Platform object exists in Nautobot. If not, creates it.

    Args:
        platform_name (str): Name of platform to verify.
        manu (str): Name of platform manufacturer.

    Returns:
        DeviceRole: Created DeviceRole object.
    """
    try:
        platform_obj = Platform.objects.get(name=platform_name)
    except Platform.DoesNotExist:
        platform_obj = Platform(
            name=platform_name,
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
    assign_primary(dev=dev, ipaddr=ipaddr)
    print(f"{ipaddr.address} set to primary on {dev.name}")
    dev.validated_save()
    intf.mgmt_only = True
    intf.validated_save()


def assign_primary(dev, ipaddr):
    """Method to assign IP address as primary to specified device.

    Args:
        dev (Device): Device object that the IPAddress is expected to already be assigned to.
        ipaddr (IPAddress): IPAddress object that is to be primary for `dev`.
    """
    if ipaddr.assigned_object_id:
        # Check if Interface assigned to IP matching DNS query matches Device that is being worked with.
        if Interface.objects.get(id=ipaddr.assigned_object_id).device.id == dev.id:
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
    return [x for x in list_tags.names()].sort()
