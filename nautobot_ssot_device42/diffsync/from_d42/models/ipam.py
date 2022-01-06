"""DiffSyncModel IPAM subclasses for Nautobot Device42 data sync."""

import re
from typing import List, Optional
from uuid import UUID

from diffsync import DiffSyncModel
from diffsync.exceptions import ObjectAlreadyExists
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from nautobot.dcim.models import Device as NautobotDevice
from nautobot.dcim.models import Interface as NautobotInterface
from nautobot.dcim.models import Site as NautobotSite
from nautobot.extras.choices import CustomFieldTypeChoices
from nautobot.extras.models import CustomField
from nautobot.extras.models import Status as NautobotStatus
from nautobot.ipam.models import VLAN as NautobotVLAN
from nautobot.ipam.models import VRF as NautobotVRF
from nautobot.ipam.models import IPAddress as NautobotIPAddress
from nautobot.ipam.models import Prefix as NautobotPrefix
from nautobot_ssot_device42.utils import nautobot


class VRFGroup(DiffSyncModel):
    """Device42 VRFGroup model."""

    _modelname = "vrf"
    _identifiers = ("name",)
    _attributes = ("description", "tags", "custom_fields")
    _children = {}
    name: str
    description: Optional[str]
    tags: Optional[List[str]]
    custom_fields: Optional[List[dict]]
    uuid: Optional[UUID]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create VRF object in Nautobot."""
        _vrf = NautobotVRF(name=ids["name"], description=attrs["description"])
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
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
            for _tag in nautobot.get_tags(attrs["tags"]):
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
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        super().delete()
        vrf = NautobotVRF.objects.get(id=self.uuid)
        if self.diffsync.job.debug:
            self.diffsync.job.log_warning(message=f"VRF {self.name} will be deleted.")
        self.diffsync.objects_to_delete["vrf"].append(vrf)  # pylint: disable=protected-access
        return self


class Subnet(DiffSyncModel):
    """Device42 Subnet model."""

    _modelname = "subnet"
    _identifiers = (
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
    uuid: Optional[UUID]

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
            for _tag in nautobot.get_tags(attrs["tags"]):
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
        _pf = NautobotPrefix.objects.get(id=self.uuid)
        if attrs.get("description"):
            _pf.description = attrs["description"]
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
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
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        super().delete()
        subnet = NautobotPrefix.objects.get(id=self.uuid)
        if self.diffsync.job.debug:
            self.diffsync.job.log_debug(message=f"Subnet {self.network} will be deleted.")
        self.diffsync.objects_to_delete["subnet"].append(subnet)  # pylint: disable=protected-access
        return self


class IPAddress(DiffSyncModel):
    """Device42 IP Address model."""

    _modelname = "ipaddr"
    _identifiers = ("address", "vrf")
    _attributes = ("available", "label", "device", "interface", "primary", "tags", "custom_fields")
    _children = {}

    address: str
    available: bool
    label: Optional[str]
    device: Optional[str]
    interface: Optional[str]
    primary: Optional[bool]
    vrf: Optional[str]
    tags: Optional[List[str]]
    custom_fields: Optional[List[dict]]
    uuid: Optional[UUID]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create IP Address object in Nautobot."""
        if "/32" in ids["address"] and attrs.get("primary"):
            _pf = NautobotPrefix.objects.net_contains(ids["address"])
            # the last Prefix is the most specific and is assumed the one the IP address resides in
            if len(_pf) > 1:
                _range = _pf[len(_pf) - 1]
                _netmask = _range.prefix_length
            else:
                # for the edge case where the DNS answer doesn't reside in a pre-existing Prefix
                _netmask = "32"
            _address = re.sub(r"\/32", f"/{_netmask}", ids["address"])
        else:
            _address = ids["address"]
        _ip = NautobotIPAddress(
            address=_address,
            vrf=NautobotVRF.objects.get(name=ids["vrf"]) if ids.get("vrf") else None,
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
                if diffsync.job.debug:
                    diffsync.job.log_debug(
                        message=f"Unable to find Interface {attrs['interface']} for {attrs['device']}. {err}",
                    )
        if attrs.get("interface"):
            if re.search(r"[Ll]oopback", attrs["interface"]):
                _ip.role = "loopback"
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
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
        mgmt = r"^[mM]anagement|^[mM]gmt"

        if attrs.get("device"):
            try:
                _dev = NautobotDevice.objects.get(name=attrs["device"])
                # If the Interface is defined, see if it matches regex and the IP is marked primary
                if attrs.get("interface"):
                    if attrs.get("primary"):
                        _intf = NautobotInterface.objects.get(name=attrs["interface"], device__name=attrs["device"])
                        nautobot.set_primary_ip_and_mgmt(_ip, _dev, _intf)
                    elif re.search(mgmt, attrs["interface"].strip()) and attrs.get("primary"):
                        _intf = NautobotInterface.objects.get(name=attrs["interface"], device__name=attrs["device"])
                        nautobot.set_primary_ip_and_mgmt(_ip, _dev, _intf)
                # else check the label to see if it matches
                elif attrs.get("label"):
                    if re.search(mgmt, attrs["label"]):
                        _intf = nautobot.get_or_create_mgmt_intf(intf_name=attrs["label"], dev=_dev)
                        _ip.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                        _ip.assigned_object_id = _intf.id
                        _ip.validated_save()
                        nautobot.set_primary_ip_and_mgmt(_ip, _dev, _intf)
            except NautobotDevice.DoesNotExist:
                if diffsync.job.debug:
                    diffsync.job.log_debug(message=f"Unable to find Device {attrs['device']} for {_ip.address}.")
                pass
            except NautobotInterface.DoesNotExist:
                if diffsync.job.debug:
                    diffsync.job.log_debug(
                        message=f"Unable to find Interface {attrs['interface']} for device {attrs['device']} for {_ip.address}."
                    )
                pass
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update IPAddress object in Nautobot."""
        try:
            _ipaddr = NautobotIPAddress.objects.get(id=self.uuid)
        except NautobotIPAddress.DoesNotExist:
            if self.diffsync.job.debug:
                self.diffsync.job.log_debug(
                    message="IP Address passed to update but can't be found. This shouldn't happen. Why is this happening?!?!"
                )
            return
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
                intf = NautobotInterface.objects.get(device__name=_device, name=attrs["interface"])
                _ipaddr.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                _ipaddr.assigned_object_id = intf.id
            except NautobotInterface.DoesNotExist as err:
                if self.diffsync.job.debug:
                    self.diffsync.job.log_debug(
                        message=f"Unable to find Interface {attrs['interface']} for {attrs['device']}. {err}"
                    )
        elif attrs.get("device") and attrs["device"] == "":
            try:
                intf = NautobotInterface.objects.get(device=_ipaddr.assigned_object.device, name=self.interface)
                _ipaddr.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                _ipaddr.assigned_object_id = intf.id
                if hasattr(_ipaddr, "primary_ip4_for"):
                    _dev = NautobotDevice.objects.get(name=_ipaddr.primary_ip4_for)
                    _dev.primary_ip4 = None
                elif hasattr(_ipaddr, "primary_ip6_for"):
                    _dev = NautobotDevice.objects.get(name=_ipaddr.primary_ip6_for)
                    _dev.primary_ip6 = None
                _dev.validated_save()
            except NautobotInterface.DoesNotExist as err:
                if self.diffsync.job.debug:
                    self.diffsync.job.log_debug(
                        message=f"Unable to find Interface {attrs['interface']} for {str(_ipaddr.assigned_object.device)} {err}"
                    )
        elif attrs.get("interface") and attrs["interface"] == "":
            try:
                intf = NautobotInterface.objects.get(name=self.interface, device__name=attrs["device"])
                _ipaddr.assigned_object_type = ContentType.objects.get(app_label="dcim", model="interface")
                _ipaddr.assigned_object_id = intf.id
            except NautobotInterface.DoesNotExist as err:
                if self.diffsync.job.debug:
                    self.diffsync.job.log_debug(
                        message=f"Unable to find Interface {self.interface} for {attrs['device']}. {err}"
                    )
        if attrs.get("primary") and attrs["primary"] is not None:
            _device, _intf = False, False
            if attrs.get("device") and self.device != "":
                _device = NautobotDevice.objects.get(name=attrs["device"])
            elif self.device != "":
                _device = NautobotDevice.objects.get(name=self.device)
            if attrs.get("interface") and attrs["interface"] != "" and _device:
                _intf = NautobotInterface.objects.get(name=attrs["interface"], device=_device)
            elif attrs.get("label") and _device:
                _intf = NautobotInterface.objects.get(name=attrs["label"], device=_device)
            elif self.interface != "" and _device:
                _intf = NautobotInterface.objects.get(name=self.interface, device=_device)
            elif self.label != "" and _device:
                _intf = NautobotInterface.objects.get(name=self.label, device=_device)
            if _device and _intf:
                nautobot.set_primary_ip_and_mgmt(ipaddr=_ipaddr, dev=_device, intf=_intf)
        if attrs.get("tags"):
            for _tag in nautobot.get_tags(attrs["tags"]):
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
        _ipaddr.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete IPAddress object from Nautobot.

        Because IPAddress has a direct relationship with many other objects it can't be deleted before anything else.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        super().delete()
        ipaddr = NautobotIPAddress.objects.get(id=self.uuid)
        if self.diffsync.job.debug:
            self.diffsync.job.log_debug(message=f"IP Address {self.address} will be deleted. {self}")
        self.diffsync.objects_to_delete["ipaddr"].append(ipaddr)  # pylint: disable=protected-access
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
    uuid: Optional[UUID]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create VLAN object in Nautobot."""
        _site = None
        if ids["building"] != "Unknown":
            try:
                _site = NautobotSite.objects.get(name=ids["building"])
            except NautobotSite.DoesNotExist as err:
                if diffsync.job.debug:
                    diffsync.job.log_debug(message=f"Unable to find Site {ids['building']}. {err}")
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
            if diffsync.job.debug:
                diffsync.job.log_debug(message=f"{ids['name']} already exists. {err}")
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update VLAN object in Nautobot."""
        _vlan = NautobotVLAN.objects.get(id=self.uuid)
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
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        super().delete()
        vlan = NautobotVLAN.objects.get(id=self.uuid)
        if self.diffsync.job.debug:
            self.diffsync.job.log_debug(message=f"VLAN {self.name} {self.vlan_id} {self.building} will be deleted.")
        self.diffsync.objects_to_delete["vlan"].append(vlan)  # pylint: disable=protected-access
        return self
