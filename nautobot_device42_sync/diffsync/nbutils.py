"""Utility functions for Nautobot ORM."""
from nautobot.dcim.models import DeviceType, DeviceRole, Site, Manufacturer
from nautobot.extras.models.statuses import Status
from nautobot_device42_sync.constant import DEFAULTS


def verify_site(site_name: str) -> Site:
    """Verifies whether Site in plugin config is created. If not, creates site.

    Args:
        site_name (str): Name of the site.
    """
    try:
        site_obj = Site.objects.get(name=site_name)
    except Site.DoesNotExist:
        site_obj = Site(
            name=site_name, slug=site_name.lower(), status=Status.objects.get(name=DEFAULTS.get("site_status"))
        )
        site_obj.validated_save()
    return site_obj


def verify_manufacturer(manufacturer: str) -> Manufacturer:
    """Verifies whether specified Manufacturer exists in Nautobot. If not, creates it.

    Args:
        manufacturer (str): Name of manufacturer to verify.

    Returns:
        Manufacturer: Created Manufacturer object.
    """
    try:
        new_manuf = Manufacturer.objects.get(name=manufacturer)
    except Manufacturer.DoesNotExist:
        new_manuf = Manufacturer(name=manufacturer, slug=manufacturer.replace(" ", "_").to_lower())
        new_manuf.validated_save()
    return new_manuf


def verify_device_type(device_type: str) -> DeviceType:
    """Verifies whether DeviceType object already exists in Nautobot. If not, creates it.

    Args:
        device_type (str): The DeviceType to verify.

    Returns:
        DeviceType: Created DeviceType object.
    """
    try:
        device_type_obj = DeviceType.objects.get(model=device_type)
    except DeviceType.DoesNotExist:
        mf = verify_manufacturer()
        device_type_obj = DeviceType(manufacturer=mf, model=device_type, slug=device_type.lower())
        device_type_obj.validated_save()
    return device_type_obj


def verify_device_role(role_name: str, role_color: str = DEFAULTS.get("role_color")) -> DeviceRole:
    """Verifies DeviceRole object exists in Nautobot. If not, creates it.

    Args:
        role_name (str): Name of role to verify.
        role_color (str): Color of role to verify.

    Returns:
        DeviceRole: Created DeviceRole object.
    """
    try:
        role_obj = DeviceRole.objects.get(name=role_name)
    except DeviceRole.DoesNotExist:
        role_obj = DeviceRole(name=role_name, slug=role_name.lower(), color=role_color)
        role_obj.validated_save()
    return role_obj
