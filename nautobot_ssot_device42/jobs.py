# pylint: disable=too-few-public-methods
"""Jobs for Device42 integration with SSoT plugin."""

from django.templatetags.static import static
from django.urls import reverse
from nautobot.extras.jobs import BooleanVar, Job
from nautobot_ssot.jobs.base import DataMapping, DataSource
from requests import HTTPError

from diffsync import DiffSyncFlags
from diffsync.exceptions import ObjectNotCreated
from nautobot_ssot_device42.constant import PLUGIN_CFG
from nautobot_ssot_device42.diffsync.from_d42.device42 import Device42Adapter
from nautobot_ssot_device42.diffsync.from_d42.nautobot import NautobotAdapter
from nautobot_ssot_device42.utils.device42 import Device42API

from .diff import CustomOrderingDiff


class Device42DataSource(DataSource, Job):
    """Device42 SSoT Data Source."""

    debug = BooleanVar(description="Enable for more verbose debug logging", default=False)

    class Meta:
        """Meta data for Device42."""

        name = "Device42"
        data_source = "Device42"
        data_source_icon = static("nautobot_ssot_device42/d42_logo.png")
        description = "Sync information from Device42 to Nautobot"

    @classmethod
    def config_information(cls):
        """Dictionary describing the configuration of this DataSource."""
        return {
            "Device42 Host": PLUGIN_CFG.get("device42_host"),
            "Username": PLUGIN_CFG.get("device42_username"),
            "Verify SSL": str(PLUGIN_CFG.get("verify_ssl")),
        }

    @classmethod
    def data_mappings(cls):
        """List describing the data mappings involved in this DataSource."""
        return (
            DataMapping(
                "Buildings", f"{PLUGIN_CFG['device42_host']}admin/rackraj/building/", "Sites", reverse("dcim:site_list")
            ),
            DataMapping(
                "Rooms",
                f"{PLUGIN_CFG['device42_host']}admin/rackraj/room/",
                "Rack Groups",
                reverse("dcim:rackgroup_list"),
            ),
            DataMapping(
                "Racks", f"{PLUGIN_CFG['device42_host']}admin/rackraj/rack/", "Racks", reverse("dcim:rack_list")
            ),
            DataMapping(
                "Vendors",
                f"{PLUGIN_CFG['device42_host']}admin/rackraj/organisation/",
                "Manufacturers",
                reverse("dcim:manufacturer_list"),
            ),
            DataMapping(
                "Hardware Models",
                f"{PLUGIN_CFG['device42_host']}admin/rackraj/hardware/",
                "Device Types",
                reverse("dcim:devicetype_list"),
            ),
            DataMapping(
                "Devices", f"{PLUGIN_CFG['device42_host']}admin/rackraj/device/", "Devices", reverse("dcim:device_list")
            ),
            DataMapping(
                "Ports",
                f"{PLUGIN_CFG['device42_host']}admin/rackraj/netport/",
                "Interfaces",
                reverse("dcim:interface_list"),
            ),
            DataMapping(
                "Cables", f"{PLUGIN_CFG['device42_host']}admin/rackraj/cable/", "Cables", reverse("dcim:cable_list")
            ),
            DataMapping(
                "VPC (VRF Groups)",
                f"{PLUGIN_CFG['device42_host']}admin/rackraj/vrfgroup/",
                "VRFs",
                reverse("ipam:vrf_list"),
            ),
            DataMapping(
                "Subnets", f"{PLUGIN_CFG['device42_host']}admin/rackraj/vlan/", "Prefixes", reverse("ipam:prefix_list")
            ),
            DataMapping(
                "IP Addresses",
                f"{PLUGIN_CFG['device42_host']}admin/rackraj/ip_address/",
                "IP Addresses",
                reverse("ipam:ipaddress_list"),
            ),
            DataMapping(
                "VLANs", f"{PLUGIN_CFG['device42_host']}admin/rackraj/switch_vlan/", "VLANs", reverse("ipam:vlan_list")
            ),
            DataMapping(
                "Vendors",
                f"{PLUGIN_CFG['device42_host']}admin/rackraj/organisation/",
                "Providers",
                reverse("circuits:provider_list"),
            ),
            DataMapping(
                "Telco Circuits",
                f"{PLUGIN_CFG['device42_host']}admin/rackraj/circuit/",
                "Circuits",
                reverse("circuits:circuit_list"),
            ),
        )

    def sync_data(self):
        """Device42 Sync."""
        if self.kwargs["debug"]:
            self.log_info(message="Connecting to Device42...")
        client = Device42API(
            base_url=PLUGIN_CFG["device42_host"],
            username=PLUGIN_CFG["device42_username"],
            password=PLUGIN_CFG["device42_password"],
            verify=PLUGIN_CFG["verify_ssl"],
        )
        d42_adapter = Device42Adapter(job=self, sync=self.sync, client=client)
        if self.kwargs["debug"]:
            self.log_info(message="Loading data from Device42...")
        d42_adapter.load()
        nb_adapter = NautobotAdapter(job=self, sync=self.sync)
        if self.kwargs["debug"]:
            self.log_info(message="Loading data from Nautobot...")
        nb_adapter.load()
        if self.kwargs["debug"]:
            self.log_info(message="Performing diff of data between Device42 and Nautobot.")
        diff = nb_adapter.diff_from(d42_adapter, flags=DiffSyncFlags.CONTINUE_ON_FAILURE, diff_class=CustomOrderingDiff)
        self.sync.diff = diff.dict()
        self.sync.save()
        if self.kwargs["debug"]:
            self.log_info(message=diff.summary())
        if not self.kwargs["dry_run"]:
            self.log_info(message="Performing data synchronization from Device42.")
            try:
                nb_adapter.sync_from(
                    d42_adapter, flags=DiffSyncFlags.CONTINUE_ON_FAILURE, diff_class=CustomOrderingDiff
                )
            except HTTPError as err:
                self.log_failure(message="Sync failed.")
                raise err
            except ObjectNotCreated as err:
                if self.kwargs["debug"]:
                    self.log_debug(message=f"Unable to create object. {err}")
            self.log_success(message="Sync complete.")


jobs = [Device42DataSource]
