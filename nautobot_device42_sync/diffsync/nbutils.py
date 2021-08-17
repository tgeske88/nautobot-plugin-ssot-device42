"""Utility functions for Nautobot ORM."""
from django.utils.text import slugify
from nautobot.dcim.models import DeviceRole
from nautobot.dcim.models.devices import Manufacturer, Platform
from nautobot.virtualization.models import ClusterType
from nautobot_device42_sync.constant import DEFAULTS


def verify_device_role(role_name: str, role_color: str = DEFAULTS.get("role_color")) -> DeviceRole:
    """Verifies DeviceRole object exists in Nautobot. If not, creates it.

    Args:
        role_name (str): Name of role to verify.
        role_color (str): Color of role to verify. Must be hex code format.

    Returns:
        DeviceRole: Created DeviceRole object.
    """
    try:
        role_obj = DeviceRole.objects.get(name=role_name)
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


def verify_cluster_type(cluster_type: str) -> ClusterType:
    """Verifies ClusterType object exists in Nautobot. If not, creates it.

    Args:
        cluster_type (str): Name for cluster type to be validated/created.

    Returns:
        ClusterType: Created ClusterType object.
    """
    try:
        clustertype_obj = ClusterType.objects.get(name=cluster_type)
    except ClusterType.DoesNotExist:
        clustertype_obj = ClusterType(
            name=cluster_type,
            slug=slugify(cluster_type),
        )
        clustertype_obj.validated_save()
    return clustertype_obj
