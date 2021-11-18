"""Tests of Device42 utility methods."""

from nautobot.utilities.testing import TestCase
from parameterized import parameterized
from nautobot_ssot_device42.utils import device42


class TestUtilsDevice42(TestCase):
    """Test Device42 util methods."""

    def test_merge_offset_dicts(self):
        first_dict = {"total_count": 10, "limit": 2, "offset": 2, "Objects": ["a", "b"]}
        second_dict = {"total_count": 10, "limit": 2, "offset": 4, "Objects": ["c", "d"]}
        result_dict = {"total_count": 10, "limit": 2, "offset": 4, "Objects": ["a", "b", "c", "d"]}
        self.assertEqual(device42.merge_offset_dicts(orig_dict=first_dict, offset_dict=second_dict), result_dict)

    def test_get_intf_type_eth_intf(self):
        # test physical Ethernet interfaces
        eth_intf = {
            "port_name": "GigabitEthernet0/1",
            "port_type": "physical",
            "discovered_type": "ethernetCsmacd",
            "port_speed": "1.0 Gbps",
        }
        self.assertEqual(device42.get_intf_type(intf_record=eth_intf), "1000base-t")

    def test_get_intf_type_fc_intf(self):
        # test physical FiberChannel interfaces
        fc_intf = {
            "port_name": "FC0/1",
            "port_type": "physical",
            "discovered_type": "fibreChannel",
            "port_speed": "1.0 Gbps",
        }
        self.assertEqual(device42.get_intf_type(intf_record=fc_intf), "1gfc-sfp")

    def test_get_intf_type_unknown_phy_intf(self):
        # test physical interfaces that don't have a discovered_type of Ethernet or FiberChannel
        unknown_phy_intf_speed = {
            "port_name": "Ethernet0/1",
            "port_type": "physical",
            "discovered_type": "Unknown",
            "port_speed": "1.0 Gbps",
        }
        self.assertEqual(device42.get_intf_type(intf_record=unknown_phy_intf_speed), "1000base-t")

    def test_get_intf_type_gigabit_ethernet_intf(self):
        # test physical interface that's discovered as gigabitEthernet
        gigabit_ethernet_intf = {
            "port_name": "Vethernet100",
            "port_type": "physical",
            "discovered_type": "gigabitEthernet",
            "port_speed": "0",
        }
        self.assertEqual(device42.get_intf_type(intf_record=gigabit_ethernet_intf), "1000base-t")

    def test_get_intf_type_dot11_intf(self):
        # test physical interface discoverd as dot11a/b
        dot11_intf = {
            "port_name": "01:23:45:67:89:AB.0",
            "port_type": "physical",
            "discovered_type": "dot11b",
            "port_speed": None,
        }
        self.assertEqual(device42.get_intf_type(intf_record=dot11_intf), "ieee802.11a")

    def test_get_intf_type_ad_lag_intf(self):
        # test 802.3ad lag logical interface
        ad_lag_intf = {
            "port_name": "port-channel100",
            "port_type": "logical",
            "discovered_type": "ieee8023adLag",
            "port_speed": "100 Mbps",
        }
        self.assertEqual(device42.get_intf_type(intf_record=ad_lag_intf), "lag")

    def test_get_intf_type_lacp_intf(self):
        # test lacp logical interface
        lacp_intf = {
            "port_name": "Internal_Trunk",
            "port_type": "logical",
            "discovered_type": "lacp",
            "port_speed": "40 Gbps",
        }
        self.assertEqual(device42.get_intf_type(intf_record=lacp_intf), "lag")

    def test_get_intf_type_virtual_intf(self):
        # test "virtual" logical interface
        virtual_intf = {
            "port_name": "Vlan100",
            "port_type": "logical",
            "discovered_type": "propVirtual",
            "port_speed": "1.0 Gbps",
        }
        self.assertEqual(device42.get_intf_type(intf_record=virtual_intf), "virtual")

    def test_get_intf_type_port_channel_intf(self):
        # test Port-Channel logical interface
        port_channel_intf = {
            "port_name": "port-channel100",
            "port_type": "logical",
            "discovered_type": "propVirtual",
            "port_speed": "20 Gbps",
        }
        self.assertEqual(device42.get_intf_type(intf_record=port_channel_intf), "lag")

    netmiko_platforms = [
        ("asa", "asa", "cisco_asa"),
        ("ios", "ios", "cisco_ios"),
        ("iosxe", "iosxe", "cisco_ios"),
        ("nxos", "nxos", "cisco_nxos"),
        ("junos", "junos", "juniper_junos"),
    ]

    @parameterized.expand(netmiko_platforms, skip_on_empty=True)
    def test_get_netmiko_platform(self, name, sent, received):  # pylint: disable=unused-argument
        self.assertEqual(device42.get_netmiko_platform(sent), received)

    def test_find_device_role_from_tags(self):
        tags = [
            "core-router",
            "nautobot-core-router",
        ]
        self.assertEqual(device42.find_device_role_from_tags(tag_list=tags), "core-router")

    def test_get_facility(self):
        tags = ["core-router", "nautobot-core-router", "sitecode-DFW"]
        self.assertEqual(device42.get_facility(tags=tags), "DFW")
