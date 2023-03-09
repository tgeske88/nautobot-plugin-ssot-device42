"""Plugin declaration for nautobot_ssot_device42."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
try:
    from importlib import metadata
except ImportError:
    # Python version < 3.8
    import importlib_metadata as metadata

__version__ = metadata.version(__name__)


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
    min_version = "1.5.1"
    max_version = "1.9999"
    default_settings = {}
    caching_config = {}


config = NautobotDevice42SyncConfig  # pylint:disable=invalid-name
