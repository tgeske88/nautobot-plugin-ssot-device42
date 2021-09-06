"""Storage of data that will not change throughout the life cycle of the application."""

from django.conf import settings

# Import config vars from nautobot_config.py
PLUGIN_CFG = settings.PLUGINS_CONFIG["nautobot_device42_sync"]

DEFAULTS = PLUGIN_CFG.get("defaults")

USE_DNS = PLUGIN_CFG.get("use_dns")

PHY_INTF_MAP = {  # pylint: disable=invalid-name
    "100 Mbps": "100base-tx",
    "1.0 Gbps": "1000base-t",
    "10 Gbps": "10gbase-t",
    "25 Gbps": "25gbase-x-sfp28",
    "40 Gbps": "40gbase-x-qsfpp",
    "50 Gbps": "50gbase-x-sfp28",
    "100 Gbps": "100gbase-x-qsfp28",
    "200 Gbps": "200gbase-x-qsfp56",
    "400 Gbps": "400gbase-x-qsfpdd",
    "1000000": "1000base-t",
    "10000000": "10gbase-t",
    "1000000000": "100gbase-x-qsfp28",
}

FC_INTF_MAP = {  # pylint: disable=invalid-name
    "1.0 Gbps": "1gfc-sfp",
    "2.0 Gbps": "2gfc-sfp",
    "4.0 Gbps": "4gfc-sfp",
    "4 Gbps": "4gfc-sfp",
    "8.0 Gbps": "8gfc-sfpp",
    "16.0 Gbps": "16gfc-sfpp",
    "32.0 Gbps": "32gfc-sfp28",
    "64.0 Gbps": "64gfc-qsfpp",
    "128.0 Gbps": "128gfc-sfp28",
}

INTF_NAME_MAP = {
    "Ethernet": {
        "itype": "1000base-t",
        "ex_speed": "1.0 Gbps",
    },
    "FastEthernet": {
        "itype": "100base-tx",
        "ex_speed": "100 Mbps",
    },
    "GigabitEthernet": {
        "itype": "1000base-t",
        "ex_speed": "1.0 Gbps",
    },
    "TenGigabitEthernet": {
        "itype": "10gbase-t",
        "ex_speed": "10 Gbps",
    },
    "TwentyFiveGigE": {
        "itype": "25gbase-x-sfp28",
        "ex_speed": "25 Gbps",
    },
    "FortyGigabitEthernet": {
        "itype": "40gbase-x-qsfpp",
        "ex_speed": "40 Gbps",
    },
    "HundredGigabitEthernet": {
        "itype": "100gbase-x-qsfp28",
        "ex_speed": "100 Gbps",
    },
}
