"""DiffSyncModel IPAM subclasses for Nautobot Device42 data sync."""

import re
from typing import Optional, List
from diffsync import DiffSyncModel
from diffsync.exceptions import ObjectAlreadyExists
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from nautobot.dcim.models import Device as NautobotDevice
from nautobot.dcim.models import Interface as NautobotInterface
from nautobot.dcim.models import Site as NautobotSite
from nautobot.extras.choices import CustomFieldTypeChoices
from nautobot.ipam.models import VRF as NautobotVRF
from nautobot.ipam.models import Prefix as NautobotPrefix
from nautobot.ipam.models import IPAddress as NautobotIPAddress
from nautobot.ipam.models import VLAN as NautobotVLAN
from nautobot.extras.models import Status as NautobotStatus
from nautobot.extras.models import CustomField
from nautobot_device42_sync.diffsync import nbutils
from nautobot_device42_sync.constant import PLUGIN_CFG


class VRFGroup(DiffSyncModel):
    """Device42 VRFGroup model."""

    _modelname = "vrf"
    _identifiers = ("name",)
    _shortname = ("name",)
    _attributes = ("description", "tags", "custom_fields")
    _children = {}
    name: str
    description: Optional[str]
    tags: Optional[List[str]]
    custom_fields: Optional[List[dict]]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create VRF object in Nautobot."""
        _vrf = NautobotVRF(name=ids["name"], description=attrs["description"])
        if attrs.get("tags"):
            for _tag in nbutils.get_tags(attrs["tags"]):
                _vrf.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotVRF).id)
                _vrf.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _vrf.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update VRF object in Nautobot."""
        _vrf = NautobotVRF.objects.get(name=self.name)
        if attrs.get("description"):
            _vrf.description = attrs["description"]
        if attrs.get("tags"):
            for _tag in nbutils.get_tags(attrs["tags"]):
                _vrf.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotVRF).id)
                _vrf.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _vrf.validated_save()
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
    _attributes = ("description", "tags", "custom_fields")
    _children = {}
    network: str
    mask_bits: int
    description: Optional[str]
    vrf: Optional[str]
    tags: Optional[List[str]]
    custom_fields: Optional[List[dict]]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Prefix object in Nautobot."""
        _pf = NautobotPrefix(
            prefix=f"{ids['network']}/{ids['mask_bits']}",
            vrf=NautobotVRF.objects.get(name=ids["vrf"]),
            description=attrs["description"],
            status=NautobotStatus.objects.get(name="Active"),
        )
        if attrs.get("tags"):
            for _tag in nbutils.get_tags(attrs["tags"]):
                _pf.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotPrefix).id)
                _pf.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _pf.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Prefix object in Nautobot."""
        _pf = NautobotPrefix.objects.get(prefix=f"{self.network}/{self.mask_bits}", vrf__name=self.vrf)
        if attrs.get("description"):
            _pf.description = attrs["description"]
        if attrs.get("tags"):
            for _tag in nbutils.get_tags(attrs["tags"]):
                _pf.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotPrefix).id)
                _pf.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _pf.validated_save()
        return super().update(attrs)

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
    _attributes = ("available", "label", "device", "interface", "vrf", "tags", "custom_fields")
    _children = {}

    address: str
    available: bool
    label: Optional[str]
    device: Optional[str]
    interface: Optional[str]
    vrf: Optional[str]
    tags: Optional[List[str]]
    custom_fields: Optional[List[dict]]

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
        if attrs.get("tags"):
            for _tag in nbutils.get_tags(attrs["tags"]):
                _ip.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotIPAddress).id)
                _ip.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
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
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update IPAddress object in Nautobot."""
        _ipaddr = NautobotIPAddress.objects.get(address=self.address)
        if attrs.get("available"):
            _ipaddr.status = (
                NautobotStatus.objects.get(name="Active")
                if not attrs["available"]
                else NautobotStatus.objects.get(name="Reserved")
            )
        if attrs.get("label"):
            _ipaddr.description = attrs["label"]
        if (attrs.get("device") and attrs["device"] != "") and (attrs.get("interface") and attrs["interface"] != ""):
            _device = attrs["device"]
            try:
                intf = NautobotInterface.objects.get(device__name=attrs["device"], name=attrs["interface"])
                _ipaddr.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                _ipaddr.assigned_object_id = intf.id
            except NautobotInterface.DoesNotExist as err:
                self.diffsync.job.log_debug(
                    f"Unable to find Interface {attrs['interface']} for {attrs['device']}. {err}"
                )
        elif (attrs.get("device") and attrs["device"] == "") or (attrs.get("interface") and attrs["interface"] == ""):
            if PLUGIN_CFG.get("verbose_debug"):
                self.diffsync.job.log_warning(f"Unassigning interface and Device for {self.address}.")
            _ipaddr.assigned_object_type = None
            _ipaddr.assigned_object_id = None
        else:
            _device = self.device
        if attrs.get("interface") and attrs["interface"] != "":
            try:
                _dev = NautobotInterface.objects.get(id=_ipaddr.assigned_object_id).device
                intf = NautobotInterface.objects.get(device=_dev, name=attrs["interface"])
                _ipaddr.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                _ipaddr.assigned_object_id = intf.id
            except NautobotInterface.DoesNotExist as err:
                self.diffsync.job.log_debug(f"Unable to find Interface {attrs['interface']} for {_device} {err}")
        if attrs.get("device"):
            try:
                _dev = NautobotDevice.objects.get(name=attrs["device"])
                intf = NautobotInterface.objects.get(name=self.interface, device=_dev)
                _ipaddr.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                _ipaddr.assigned_object_id = intf.id
                # check if the IP is assigned as primary to another device, and if so, unassign it
                if _ipaddr.family == 4 and hasattr(_ipaddr, "primary_ip4_for"):
                    if str(_ipaddr.primary_ip4_for) != attrs["device"]:
                        _dev.primary_ip4 = None
                        _dev.validated_save()
                if _ipaddr.family == 6 and hasattr(_ipaddr, "primary_ip6_for"):
                    if str(_ipaddr.primary_ip6_for) != attrs["device"]:
                        _dev.primary_ip6 = None
                        _dev.validated_save()
            except NautobotInterface.DoesNotExist as err:
                self.diffsync.job.log_debug(f"Unable to find Interface {self.interface} for {attrs['device']}. {err}")
        else:
            _dev = NautobotDevice.objects.get(name=self.device)
        if attrs.get("vrf"):
            _ipaddr.vrf = NautobotVRF.objects.get(name=attrs["vrf"])
        if attrs.get("tags"):
            for _tag in nbutils.get_tags(attrs["tags"]):
                _ipaddr.tags.add(_tag)
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotIPAddress).id)
                _ipaddr.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        if (getattr(_ipaddr, "primary_ip4_for") and _ipaddr.primary_ip4_for == _dev) or (
            getattr(_ipaddr, "primary_ip6_for") and _ipaddr.primary_ip6_for == _dev
        ):
            _ipaddr.validated_save()
            return super().update(attrs)

    def delete(self):
        """Delete IPAddress object from Nautobot."""
        print(f"IP Address {self.address} will be deleted.")
        ipaddr = NautobotIPAddress.objects.get(**self.get_identifiers())
        ipaddr.delete()
        super().delete()
        return self


class VLAN(DiffSyncModel):
    """Device42 VLAN model."""

    _modelname = "vlan"
    _identifiers = (
        "name",
        "vlan_id",
        "building",
    )
    _attributes = ("description", "custom_fields")
    _children = {}

    name: str
    vlan_id: int
    description: Optional[str]
    building: Optional[str]
    custom_fields: Optional[List[dict]]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create VLAN object in Nautobot."""
        _site = None
        if ids["building"] != "Unknown":
            try:
                _site = NautobotSite.objects.get(name=ids["building"])
            except NautobotSite.DoesNotExist as err:
                if PLUGIN_CFG.get("verbose_debug"):
                    diffsync.job.log_warning(f"Unable to find Site {ids['building']}. {err}")
        try:
            _vlan = NautobotVLAN.objects.get(name=ids["name"], vid=ids["vlan_id"], site=_site)
        except NautobotVLAN.DoesNotExist:
            _vlan = NautobotVLAN(
                name=ids["name"],
                vid=ids["vlan_id"],
                description=attrs["description"],
                status=NautobotStatus.objects.get(name="Active"),
            )
        if _site:
            _vlan.site = _site
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotVLAN).id)
                _vlan.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        try:
            _vlan.validated_save()
        except ObjectAlreadyExists as err:
            diffsync.job.log_debug(f"{ids['name']} already exists. {err}")
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update VLAN object in Nautobot."""
        try:
            if self.building != "Unknown":
                _vlan = NautobotVLAN.objects.get(name=self.name, vid=self.vlan_id, site__name=self.building)
            else:
                _vlan = NautobotVLAN.objects.get(name=self.name, vid=self.vlan_id, site=None)
        except NautobotVLAN.DoesNotExist as err:
            if PLUGIN_CFG.get("verbose_debug"):
                self.diffsync.job.log_warning(f"Unable to find Site {self.building}. {err}")
            return None
        except NautobotVLAN.MultipleObjectsReturned as err:
            if PLUGIN_CFG.get("verbose_debug"):
                self.diffsync.job.log_warning(
                    f"Unable to find VLAN {self.get_identifiers()} due to multiple objects found. {err}"
                )
            return None
        if attrs.get("description"):
            self.description = attrs["description"]
        if attrs.get("custom_fields"):
            for _cf in attrs["custom_fields"]:
                _cf_dict = {
                    "name": slugify(_cf["key"]),
                    "type": CustomFieldTypeChoices.TYPE_TEXT,
                    "label": _cf["key"],
                }
                field, _ = CustomField.objects.get_or_create(name=slugify(_cf_dict["name"]), defaults=_cf_dict)
                field.content_types.add(ContentType.objects.get_for_model(NautobotVLAN).id)
                _vlan.custom_field_data.update({_cf_dict["name"]: _cf["value"]})
        _vlan.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete VLAN object from Nautobot.

        Because VLAN has a direct relationship with many other objects it can't be deleted before anything else.
        The self.diffsync._objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(f"VLAN {self.name} {self.vlan_id} {self.building} will be deleted.")
        super().delete()
        try:
            vlan = NautobotVLAN.objects.get(vid=self.vlan_id, name=self.name, site__name=self.building)
        except NautobotVLAN.DoesNotExist:
            vlans = NautobotVLAN.objects.filter(vid=self.vlan_id, name=self.name)
            for _vlan in vlans:
                if not _vlan.site:
                    vlan = _vlan
                    break
        self.diffsync._objects_to_delete["vlan"].append(vlan)  # pylint: disable=protected-access
        return self
