"""Tests of Nautobot utility methods."""
from uuid import UUID
from unittest.mock import MagicMock
from nautobot.utilities.testing import TransactionTestCase
from nautobot.dcim.models import Manufacturer
from nautobot_ssot_device42.utils.nautobot import verify_platform, determine_vc_position


class TestNautobotUtils(TransactionTestCase):
    """Test Nautobot utility methods."""

    databases = ("default", "job_logs")

    def test_verify_platform_ios(self):
        """Test the verify_platform method with IOS."""
        dsync = MagicMock()
        dsync.platform_map = {}
        dsync.objects_to_create = {"platforms": []}
        cisco_manu, _ = Manufacturer.objects.get_or_create(name="Cisco")
        platform = verify_platform(diffsync=dsync, platform_name="ios", manu=cisco_manu.id)
        self.assertEqual(type(platform), UUID)
        self.assertEqual(dsync.objects_to_create["platforms"][0].name, "cisco.ios.ios")
        self.assertEqual(dsync.objects_to_create["platforms"][0].slug, "cisco_ios")
        self.assertEqual(dsync.objects_to_create["platforms"][0].napalm_driver, "ios")

    def test_verify_platform_iosxe(self):
        """Test the verify_platform method with IOS-XE."""
        dsync = MagicMock()
        dsync.platform_map = {}
        dsync.objects_to_create = {"platforms": []}
        cisco_manu, _ = Manufacturer.objects.get_or_create(name="Cisco")
        platform = verify_platform(diffsync=dsync, platform_name="ios-xe", manu=cisco_manu.id)
        self.assertEqual(type(platform), UUID)
        self.assertEqual(dsync.objects_to_create["platforms"][0].name, "cisco.ios.ios")
        self.assertEqual(dsync.objects_to_create["platforms"][0].slug, "cisco_ios")
        self.assertEqual(dsync.objects_to_create["platforms"][0].napalm_driver, "ios")

    def test_verify_platform_iosxr(self):
        """Test the verify_platform method with IOS-XR."""
        dsync = MagicMock()
        dsync.platform_map = {}
        dsync.objects_to_create = {"platforms": []}
        cisco_manu, _ = Manufacturer.objects.get_or_create(name="Cisco")
        platform = verify_platform(diffsync=dsync, platform_name="ios-xr", manu=cisco_manu.id)
        self.assertEqual(type(platform), UUID)
        self.assertEqual(dsync.objects_to_create["platforms"][0].name, "cisco.iosxr.iosxr")
        self.assertEqual(dsync.objects_to_create["platforms"][0].slug, "cisco_xr")
        self.assertEqual(dsync.objects_to_create["platforms"][0].napalm_driver, "iosxr")

    def test_verify_platform_f5(self):
        """Test the verify_platform method with F5 BIG-IP."""
        dsync = MagicMock()
        dsync.platform_map = {}
        dsync.objects_to_create = {"platforms": []}
        f5_manu, _ = Manufacturer.objects.get_or_create(name="F5")
        platform = verify_platform(diffsync=dsync, platform_name="f5", manu=f5_manu.id)
        self.assertEqual(type(platform), UUID)
        self.assertEqual(dsync.objects_to_create["platforms"][0].name, "bigip")
        self.assertEqual(dsync.objects_to_create["platforms"][0].slug, "f5_tmsh")
        self.assertEqual(dsync.objects_to_create["platforms"][0].napalm_driver, "bigip")

    def test_determine_vc_position(self):
        vc_map = {
            "switch_vc_example": {
                "members": [
                    "switch_vc_example - Switch 1",
                    "switch_vc_example - Switch 2",
                ],
            },
            "node_vc_example": {
                "members": [
                    "node_vc_example - node0",
                    "node_vc_example - node1",
                    "node_vc_example - node2",
                ],
            },
            "firewall_pair_example": {
                "members": ["firewall - FTX123456AB", "firewall - FTX234567AB"],
            },
        }
        sw1_pos = determine_vc_position(
            vc_map=vc_map, virtual_chassis="switch_vc_example", device_name="switch_vc_example - Switch 1"
        )
        self.assertEqual(sw1_pos, 2)
        sw2_pos = determine_vc_position(
            vc_map=vc_map, virtual_chassis="switch_vc_example", device_name="switch_vc_example - Switch 2"
        )
        self.assertEqual(sw2_pos, 3)
        node3_pos = determine_vc_position(
            vc_map=vc_map, virtual_chassis="node_vc_example", device_name="node_vc_example - node2"
        )
        self.assertEqual(node3_pos, 4)
        fw_pos = determine_vc_position(
            vc_map=vc_map, virtual_chassis="firewall_pair_example", device_name="firewall - FTX123456AB"
        )
        self.assertEqual(fw_pos, 2)
