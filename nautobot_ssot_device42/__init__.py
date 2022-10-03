"""Plugin declaration for nautobot_ssot_device42."""

__version__ = "1.3.11"

from nautobot.extras.plugins import PluginConfig


class NautobotDevice42SyncConfig(PluginConfig):
    """Plugin configuration for the nautobot_ssot_device42 plugin."""

    name = "nautobot_ssot_device42"
    verbose_name = "Nautobot Device42 Sync"
    version = __version__
    author = "Justin Drew"
    description = "Nautobot plugin for syncing to Device42."
    base_url = "nautobot-ssot-device42"
    required_settings = [
        "device42_host",
        "device42_username",
        "device42_password",
        "defaults",
    ]
    min_version = "1.3.0"
    max_version = "1.9999"
    default_settings = {}
    caching_config = {}


config = NautobotDevice42SyncConfig  # pylint:disable=invalid-name
