"""DiffSyncModel IPAM subclasses for Nautobot Device42 data sync."""

from typing import Optional, List
from diffsync.diff import Diff
from django.utils.text import slugify
from diffsync import DiffSyncModel
from nautobot.core.settings_funcs import is_truthy
from nautobot.ipam.models import VRF as NautobotVRF
from nautobot.ipam.models import VLAN as NautobotVLAN


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

