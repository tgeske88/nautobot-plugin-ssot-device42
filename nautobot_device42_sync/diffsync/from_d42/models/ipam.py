"""DiffSyncModel IPAM subclasses for Nautobot Device42 data sync."""

import re
from typing import Optional
from diffsync import DiffSyncModel
from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import Device as NautobotDevice
from nautobot.dcim.models import Interface as NautobotInterface
from nautobot.ipam.models import VRF as NautobotVRF
from nautobot.ipam.models import Prefix as NautobotPrefix
from nautobot.ipam.models import IPAddress as NautobotIPAddress
from nautobot.extras.models import Status as NautobotStatus
from nautobot_device42_sync.diffsync import nbutils


class VRFGroup(DiffSyncModel):
    """Device42 VRFGroup model."""

    _modelname = "vrf"
    _identifiers = ("name",)
    _shortname = ("name",)
    _attributes = ("description",)
    _children = {}
    name: str
    description: Optional[str]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create VRF object in Nautobot."""
        _vrf = NautobotVRF(name=ids["name"], description=attrs["description"])
        _vrf.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update VRF object in Nautobot."""
        return super().update(attrs)

    def delete(self):
        """Delete VRF object from Nautobot.

        Because VRF has a direct relationship with many other objects it can't be deleted before anything else.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"VRF {self.name} will be deleted.")
        super().delete()
        site = NautobotVRF.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["vrf"].append(site)  # pylint: disable=protected-access
        return self


class Subnet(DiffSyncModel):
    """Device42 Subnet model."""

    _modelname = "subnet"
    _identifiers = (
        "network",
        "mask_bits",
        "vrf",
    )
    _shortname = (
        "network",
        "mask_bits",
        "vrf",
    )
    _attributes = ("description",)
    _children = {}
    network: str
    mask_bits: int
    description: Optional[str]
    vrf: Optional[str]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Prefix object in Nautobot."""
        _pf = NautobotPrefix(
            prefix=f"{ids['network']}/{ids['mask_bits']}",
            vrf=NautobotVRF.objects.get(name=ids["vrf"]),
            description=attrs["description"],
            status=NautobotStatus.objects.get(name="Active"),
        )
        _pf.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self):
        """Delete Subnet object from Nautobot.

        Because Subnet has a direct relationship with many other objects it can't be deleted before anything else.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"Subnet {self.name} will be deleted.")
        super().delete()
        site = NautobotPrefix.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["subnet"].append(site)  # pylint: disable=protected-access
        return self


class IPAddress(DiffSyncModel):
    """Device42 IP Address model."""

    _modelname = "ipaddr"
    _identifiers = ("address",)
    _shortname = ("address",)
    _attributes = ("label", "device", "interface", "vrf")
    _children = {}

    address: str
    available: bool
    label: Optional[str]
    device: Optional[str]
    interface: Optional[str]
    vrf: Optional[str]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create IP Address object in Nautobot."""
        _ip = NautobotIPAddress(
            address=ids["address"],
            vrf=NautobotVRF.objects.get(name=attrs["vrf"]) if attrs.get("vrf") else None,
            status=NautobotStatus.objects.get(name="Active")
            if not attrs.get("available")
            else NautobotStatus.objects.get(name="Reserved"),
            description=attrs["label"] if attrs.get("label") else "",
        )
        if attrs.get("device") and attrs.get("interface"):
            try:
                intf = NautobotInterface.objects.get(device__name=attrs["device"], name=attrs["interface"])
                _ip.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                _ip.assigned_object_id = intf.id
            except NautobotInterface.DoesNotExist as err:
                diffsync.job.log_debug(f"Unable to find Interface {attrs['interface']} for {attrs['device']}. {err}")
        if attrs.get("interface"):
            if re.search(r"[Ll]oopback", attrs["interface"]):
                _ip.role = "loopback"
        _ip.validated_save()

        # Define regex match for Management interface (ex Management/Mgmt/mgmt/management)
        mgmt = r"[mM]anagement|[mM]gmt"

        if attrs.get("device"):
            try:
                _dev = NautobotDevice.objects.get(name=attrs["device"])
                # If the Interface is defined, see if it matches regex
                if attrs.get("interface"):
                    if re.search(mgmt, attrs["interface"].strip()):
                        _intf = NautobotInterface.objects.get(name=attrs["interface"], device__name=attrs["device"])
                        nbutils.set_primary_ip_and_mgmt(_ip, _dev, _intf)
                # else check the label to see if it matches
                elif attrs.get("label"):
                    if re.search(mgmt, attrs["label"]):
                        _intf = nbutils.get_or_create_mgmt_intf(intf_name=attrs["label"], dev=_dev)
                        _ip.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                        _ip.assigned_object_id = _intf.id
                        _ip.validated_save()
                        nbutils.set_primary_ip_and_mgmt(_ip, _dev, _intf)
            except NautobotDevice.DoesNotExist:
                pass
            except NautobotInterface.DoesNotExist:
                pass

    def delete(self):
        """Delete IPAddress object from Nautobot.

        Because IPAddress has a direct relationship with many other objects it can't be deleted before anything else.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"IP Address {self.address} will be deleted.")
        super().delete()
        site = NautobotIPAddress.objects.get(**self.get_identifiers())
        self.diffsync._objects_to_delete["ipaddr"].append(site)  # pylint: disable=protected-access
        return self
