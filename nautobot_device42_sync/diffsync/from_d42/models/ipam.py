"""DiffSyncModel IPAM subclasses for Nautobot Device42 data sync."""

from typing import Optional, List
from diffsync.diff import Diff
from django.utils.text import slugify
from diffsync import DiffSyncModel
from nautobot.core.settings_funcs import is_truthy
from nautobot.ipam.models import VRF as NautobotVRF
from nautobot.ipam.models import VLAN as NautobotVLAN
from nautobot.ipam.models import Prefix as NautobotPrefix
from nautobot.extras.models import Status as NautobotStatus


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
