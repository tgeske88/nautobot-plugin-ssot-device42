"""DiffSyncModel Asset subclasses for Nautobot Device42 data sync."""

from typing import Optional
from uuid import UUID

from diffsync import DiffSyncModel
from django.core.exceptions import ValidationError
from nautobot.dcim.models import Site, RackGroup, Rack, Device, DeviceType, FrontPort, RearPort
from nautobot.extras.models import Status
from nautobot_ssot_device42.constant import PLUGIN_CFG
from nautobot_ssot_device42.utils import nautobot


def find_site(diffsync, attrs):
    """Method to determine Site for Patch Panel based upon object attributes."""
    pp_site = False
    try:
        if attrs.get("building") is not None:
            pp_site = Site.objects.get(name=attrs["building"])
        elif attrs.get("room") is not None and attrs.get("rack") is not None:
            pp_site = Rack.objects.get(name=attrs["rack"], group__name=attrs["rack"]).site
        elif attrs.get("rack") is not None:
            pp_site = Rack.objects.get(name=attrs["rack"]).site
    except Site.DoesNotExist:
        if diffsync.job.debug:
            diffsync.job.log_warning(message=f"Unable to find Site {attrs.get('building')}.")
    except RackGroup.DoesNotExist:
        if diffsync.job.debug:
            diffsync.job.log_warning(
                message=f"Unable to find Site using Room {attrs.get('room')} & Rack {attrs.get('rack')}."
            )
    except Rack.DoesNotExist:
        if diffsync.job.debug:
            diffsync.job.log_warning(message=f"Unable to find Site using Rack {attrs.get('rack')}.")
    except Rack.MultipleObjectsReturned:
        if diffsync.job.debug:
            diffsync.job.log_warning(
                message=f"Unable to find Site using Rack {attrs.get('rack')} as more than one was found."
            )
    return pp_site


def find_rack(diffsync, ids, attrs):
    """Method to determine Site for Patch Panel based upon object attributes."""
    if attrs.get("room"):
        _room = attrs["room"]
    else:
        _room = ids["room"]
    if attrs.get("rack"):
        _rack = attrs["rack"]
    else:
        _rack = ids["rack"]
    pp_rack = False
    try:
        if _room is not None and _rack is not None:
            pp_rack = Rack.objects.get(name=_rack, group__name=_room)
        elif attrs.get("rack") is not None:
            pp_rack = Rack.objects.get(name=_rack)
    except RackGroup.DoesNotExist:
        if diffsync.job.debug:
            diffsync.job.log_warning(message=f"Unable to find Rack using Room {_room} & Rack {_rack}.")
    except Rack.DoesNotExist:
        if diffsync.job.debug:
            diffsync.job.log_warning(message=f"Unable to find Rack {_rack}.")
    except Rack.MultipleObjectsReturned:
        if diffsync.job.debug:
            diffsync.job.log_warning(message=f"Unable to find Rack {_rack} as more than one was found.")
    return pp_rack


class PatchPanel(DiffSyncModel):
    """Device42 Patch Panel model."""

    _modelname = "patchpanel"
    _identifiers = ("name",)
    _attributes = (
        "in_service",
        "vendor",
        "model",
        "size",
        "depth",
        "orientation",
        "position",
        "num_ports",
        "building",
        "room",
        "rack",
        "serial_no",
    )
    _children = {}

    name: str
    in_service: bool
    vendor: str
    model: str
    size: float
    depth: str
    orientation: str
    position: Optional[float]
    num_ports: int
    building: Optional[str]
    room: Optional[str]
    rack: Optional[str]
    serial_no: Optional[str]
    uuid: Optional[UUID]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Patch Panel Device in Nautobot."""
        if diffsync.job.debug:
            diffsync.job.log_debug(message=f"Creating patch panel {ids['name']}.")
        try:
            Device.objects.get(name=ids["name"])
        except Device.DoesNotExist:
            pp_site = find_site(diffsync=diffsync, attrs=attrs)
            pp_rack = find_rack(diffsync=diffsync, ids=ids, attrs=attrs)
            pp_role = nautobot.verify_device_role(role_name="patch panel")
            if attrs.get("in_service"):
                pp_status = Status.objects.get(name="Active")
            else:
                pp_status = Status.objects.get(name="Offline")
            if isinstance(pp_site, Site):
                patch_panel = Device(
                    name=ids["name"],
                    status=pp_status,
                    site=pp_site,
                    device_type=DeviceType.objects.get(model=attrs["model"]),
                    device_role=pp_role,
                    serial=attrs["serial_no"],
                )
                if pp_rack is not False and attrs.get("position") and attrs.get("orientation"):
                    patch_panel.rack = pp_rack
                    patch_panel.position = int(attrs["position"])
                    patch_panel.face = attrs["orientation"]
                try:
                    patch_panel.validated_save()
                    return super().create(ids=ids, diffsync=diffsync, attrs=attrs)
                except ValidationError as err:
                    if diffsync.job.debug:
                        diffsync.job.log_warning(message=f"Unable to create {ids['name']} patch panel. {err}")
            return None

    def update(self, attrs):
        """Update Patch Panel object in Nautobot."""
        ppanel = Device.objects.get(id=self.uuid)
        if attrs.get("in_service"):
            if attrs["in_service"] is True:
                ppanel.status = Status.objects.get(name="Active")
            else:
                ppanel.status = Status.objects.get(name="Offline")
        if attrs.get("vendor") and attrs.get("model"):
            ppanel.device_type = DeviceType.objects.get(model=attrs["model"])
            if attrs.get("size"):
                ppanel.device_type.u_height = int(attrs["size"])
            if attrs.get("depth"):
                ppanel.device_type.is_full_depth = bool(attrs["depth"] == "Full Depth")
        if attrs.get("orientation"):
            ppanel.face = attrs["orientation"]
        if attrs.get("position"):
            ppanel.position = attrs["position"]
        if attrs.get("building"):
            pp_site = find_site(diffsync=self.diffsync, attrs=attrs)
            if pp_site:
                ppanel.site = pp_site
        if attrs.get("room") or attrs.get("rack"):
            pp_rack = find_rack(diffsync=self.diffsync, ids={"room": self.room, "rack": self.rack}, attrs=attrs)
            if pp_rack:
                ppanel.rack = pp_rack
                ppanel.face = attrs["orientation"] if attrs.get("orientation") else self.orientation
        if attrs.get("serial_no"):
            ppanel.serial = attrs["serial_no"]
        try:
            ppanel.validated_save()
            return super().update(attrs)
        except ValidationError as err:
            if self.diffsync.job.debug:
                self.diffsync.job.log_warning(message=f"Unable to update {self.name} patch panel. {err}")
            return None

    def delete(self):
        """Delete Patch Panel Device object from Nautobot.

        Because a Patch Panel Device has a direct relationship with Ports it can't be deleted before they are.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.debug:
                self.diffsync.job.log_warning(message=f"Patch panel {self.name} will be deleted.")
            _pp = Device.objects.get(id=self.uuid)
            self.diffsync.objects_to_delete["patchpanel"].append(_pp)  # pylint: disable=protected-access
        return self


class PatchPanelRearPort(DiffSyncModel):
    """Device42 Patch Panel RearPort model."""

    _modelname = "patchpanelrearport"
    _identifiers = ("name", "patchpanel")
    _attributes = ("port_type",)
    _children = {}

    name: str
    patchpanel: str
    port_type: str
    uuid: Optional[UUID]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Patch Panel Port in Nautobot."""
        if diffsync.job.debug:
            diffsync.job.log_debug(message=f"Creating patch panel port {ids['name']} for {ids['patchpanel']}.")
        try:
            RearPort.objects.get(name=ids["name"], device__name=ids["patchpanel"])
        except RearPort.DoesNotExist:
            rear_port = RearPort(
                name=ids["name"],
                device=Device.objects.get(name=ids["patchpanel"]),
                type=attrs["port_type"],
                positions=ids["name"],
            )
            try:
                rear_port.validated_save()
                return super().create(ids=ids, diffsync=diffsync, attrs=attrs)
            except ValidationError as err:
                if diffsync.job.debug:
                    diffsync.job.log_debug(message=f"Unable to create patch panel {ids['name']}. {err}")
                return None

    def update(self, attrs):
        """Update RearPort object in Nautobot."""
        port = RearPort.objects.get(id=self.uuid)
        if attrs.get("type"):
            port.type = attrs["type"]
        try:
            port.validated_save()
            return super().update(attrs)
        except ValidationError as err:
            if self.diffsync.job.debug:
                self.diffsync.job.log_warning(message=f"Unable to update {self.name} RearPort. {err}")
            return None

    def delete(self):
        """Delete RearPort object from Nautobot."""
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.debug:
                self.diffsync.job.log_warning(message=f"RearPort {self.name} for {self.patchpanel} will be deleted.")
            port = RearPort.objects.get(id=self.uuid)
            port.delete()
        return self


class PatchPanelFrontPort(DiffSyncModel):
    """Device42 Patch Panel FrontPort model."""

    _modelname = "patchpanelfrontport"
    _identifiers = ("name", "patchpanel")
    _attributes = ("port_type",)
    _children = {}

    name: str
    patchpanel: str
    port_type: str
    uuid: Optional[UUID]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Patch Panel FrontPort in Nautobot."""
        if diffsync.job.debug:
            diffsync.job.log_debug(message=f"Creating patch panel front port {ids['name']} for {ids['patchpanel']}.")
        try:
            FrontPort.objects.get(name=ids["name"], device__name=ids["patchpanel"])
        except FrontPort.DoesNotExist:
            front_port = FrontPort(
                name=ids["name"],
                device=Device.objects.get(name=ids["patchpanel"]),
                type=attrs["port_type"],
                rear_port=RearPort.objects.get(name=ids["name"], device__name=ids["patchpanel"]),
                rear_port_position=ids["name"],
            )
            try:
                front_port.validated_save()
                return super().create(ids=ids, diffsync=diffsync, attrs=attrs)
            except ValidationError as err:
                if diffsync.job.debug:
                    diffsync.job.log_debug(message=f"Unable to create patch panel front port {ids['name']}. {err}")
                return None

    def update(self, attrs):
        """Update FrontPort object in Nautobot."""
        port = FrontPort.objects.get(id=self.uuid)
        if attrs.get("type"):
            port.type = attrs["type"]
        try:
            port.validated_save()
            return super().update(attrs)
        except ValidationError as err:
            if self.diffsync.job.debug:
                self.diffsync.job.log_warning(message=f"Unable to update {self.name} FrontPort. {err}")
            return None

    def delete(self):
        """Delete FrontPort object from Nautobot."""
        if PLUGIN_CFG.get("delete_on_sync"):
            super().delete()
            if self.diffsync.job.debug:
                self.diffsync.job.log_warning(message=f"FrontPort {self.name} for {self.patchpanel} will be deleted.")
            port = FrontPort.objects.get(id=self.uuid)
            port.delete()
        return self
