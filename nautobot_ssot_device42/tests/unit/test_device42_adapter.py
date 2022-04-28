"""Unit tests for the Device42 DiffSync adapter class."""
import json
import uuid
from unittest.mock import MagicMock, patch

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from nautobot.extras.models import Job, JobResult
from parameterized import parameterized
from nautobot_ssot_device42.diffsync.from_d42.device42 import Device42Adapter, get_circuit_status
from nautobot_ssot_device42.jobs import Device42DataSource


def load_json(path):
    """Load a json file."""
    with open(path, encoding="utf-8") as file:
        return json.loads(file.read())


BUILDING_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_buildings_recv.json")
ROOM_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_rooms_recv.json")
RACK_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_racks_recv.json")
VENDOR_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_vendors_recv.json")
HARDWARE_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_hardware_models_recv.json")


@patch("nautobot.extras.models.models.JOB_LOGS", None)
class Device42AdapterTestCase(TestCase):
    """Test the Device42Adapter class."""

    def setUp(self):
        """Method to initialize test case."""
        # Create a mock client
        self.d42_client = MagicMock()
        self.d42_client.get_buildings.return_value = BUILDING_FIXTURE
        self.d42_client.get_rooms.return_value = ROOM_FIXTURE
        self.d42_client.get_racks.return_value = RACK_FIXTURE
        self.d42_client.get_vendors.return_value = VENDOR_FIXTURE
        self.d42_client.get_hardware_models.return_value = HARDWARE_FIXTURE

        self.job = Device42DataSource()
        self.job.job_result = JobResult.objects.create(
            name=self.job.class_path, obj_type=ContentType.objects.get_for_model(Job), user=None, job_id=uuid.uuid4()
        )
        self.device42 = Device42Adapter(job=self.job, sync=None, client=self.d42_client)

    def test_data_loading(self):
        """Test the load() function."""

        self.device42.load_buildings()
        self.assertEqual(
            {site["name"] for site in BUILDING_FIXTURE},
            {site.get_unique_id() for site in self.device42.get_all("building")},
        )
        self.device42.load_rooms()
        self.assertEqual(
            {f"{room['name']}__{room['building']}" for room in ROOM_FIXTURE},
            {room.get_unique_id() for room in self.device42.get_all("room")},
        )
        self.device42.load_racks()
        self.assertEqual(
            {f"{rack['name']}__{rack['building']}__{rack['room']}" for rack in RACK_FIXTURE},
            {rack.get_unique_id() for rack in self.device42.get_all("rack")},
        )
        self.device42.load_vendors()
        self.assertEqual(
            {vendor["name"] for vendor in VENDOR_FIXTURE},
            {vendor.get_unique_id() for vendor in self.device42.get_all("vendor")},
        )
        self.device42.load_hardware_models()
        self.assertEqual(
            {model["name"] for model in HARDWARE_FIXTURE},
            {model.get_unique_id() for model in self.device42.get_all("hardware")},
        )

    statuses = [
        ("Production", "Production", "Active"),
        ("Provisioning", "Provisioning", "Provisioning"),
        ("Canceled", "Canceled", "Deprovisioning"),
        ("Decommissioned", "Decommissioned", "Decommissioned"),
        ("Ordered", "Ordered", "Offline"),
    ]

    @parameterized.expand(statuses, skip_on_empty=True)
    def test_get_circuit_status(self, name, sent, received):  # pylint: disable=unused-argument
        """Test get_circuit_status success."""
        self.assertEqual(get_circuit_status(sent), received)

    def test_filter_ports(self):
        """Method to test filter_ports success."""
        vlan_ports = load_json("./nautobot_ssot_device42/tests/fixtures/ports_with_vlans.json")
        no_vlan_ports = load_json("./nautobot_ssot_device42/tests/fixtures/ports_wo_vlans.json")
        merged_ports = load_json("./nautobot_ssot_device42/tests/fixtures/merged_ports.json")
        result = self.device42.filter_ports(vlan_ports, no_vlan_ports)
        self.assertEqual(merged_ports, result)
