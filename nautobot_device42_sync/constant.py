"""Storage of data that will not change throughout the life cycle of the application."""

from django.conf import settings

# Import config vars from nautobot_config.py
PLUGIN_CFG = settings.PLUGINS_CONFIG["nautobot_device42_sync"]

DEFAULTS = PLUGIN_CFG.get("defaults")

USE_DNS = PLUGIN_CFG.get("use_dns")
