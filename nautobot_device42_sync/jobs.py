# pylint: disable=too-few-public-methods
"""Jobs for Device42 integration with SSoT plugin."""

from requests import HTTPError
from django.urls import reverse
from django.templatetags.static import static
from nautobot.extras.jobs import Job, BooleanVar
from nautobot_ssot.jobs.base import DataSource, DataMapping
from diffsync import DiffSyncFlags
from nautobot_device42_sync.diffsync.from_d42.device42 import Device42Adapter
from nautobot_device42_sync.diffsync.from_d42.nautobot import NautobotAdapter
from nautobot_device42_sync.constant import PLUGIN_CFG


class Device42DataSource(DataSource, Job):
    """Device42 SSoT Data Source."""

    debug = BooleanVar(description="Enable for more verbose debug logging")

    class Meta:
        """Meta data for Device42."""

        name = "Device42"
        data_source = "Device42"
        data_source_icon = static("nautobot_device42_sync/d42_logo.png")
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
            DataMapping("building", None, "Sites", reverse("dcim:site_list")),
            DataMapping("room", None, "Rack-Groups", reverse("dcim:rackgroup_list")),
            DataMapping("vendor", None, "Manufacturers", reverse("dcim:manufacturer_list")),
            DataMapping("hardware", None, "Device Types", reverse("dcim:devicetype_list")),
            DataMapping("device", None, "Devices", reverse("dcim:device_list")),
        )

    def sync_data(self):
        """Device42 Sync."""
        self.log_info(message="Connecting to Device42...")
        d42_adapter = Device42Adapter(job=self, sync=self.sync)
        self.log_info(message="Loading data from Device42...")
        d42_adapter.load()
        self.log_info(message="Connecting to Nautobot...")
        nb_adapter = NautobotAdapter(job=self, sync=self.sync)
        self.log_info(message="Loading data from Nautobot...")
        nb_adapter.load()
        self.log_info(message="Performing diff of data between Device42 and Nautobot.")
        diff = nb_adapter.diff_from(d42_adapter, flags=DiffSyncFlags.CONTINUE_ON_FAILURE)
        self.sync.diff = diff.dict()
        self.sync.save()
        self.log_info(message=diff.summary())
        if not self.kwargs["dry_run"]:
            self.log_info(message="Performing data synchronization from Device42.")
            try:
                nb_adapter.sync_from(d42_adapter, flags=DiffSyncFlags.CONTINUE_ON_FAILURE)
            except HTTPError as err:
                self.log_failure(message="Sync failed.")
                raise err
            self.log_success(message="Sync complete.")


jobs = [Device42DataSource]
