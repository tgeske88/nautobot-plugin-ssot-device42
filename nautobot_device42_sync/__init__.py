"""Plugin declaration for nautobot_device42_sync."""

__version__ = "0.8.3"

from nautobot.extras.plugins import PluginConfig


class NautobotDevice42SyncConfig(PluginConfig):
    """Plugin configuration for the nautobot_device42_sync plugin."""

    name = "nautobot_device42_sync"
    verbose_name = "Nautobot Device42 Sync"
    version = __version__
    author = "Justin Drew"
    description = "Nautobot plugin for syncing to Device42."
    base_url = "nautobot-device42-sync"
    required_settings = []
    min_version = "1.0.0"
    max_version = "1.9999"
    default_settings = {}
    caching_config = {}


config = NautobotDevice42SyncConfig  # pylint:disable=invalid-name
