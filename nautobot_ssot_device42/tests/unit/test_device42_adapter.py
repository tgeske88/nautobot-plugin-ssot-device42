"""Unit tests for the IPFabric DiffSync adapter class."""
import json
import uuid
from unittest.mock import MagicMock

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from nautobot.extras.models import Job, JobResult

from nautobot_ssot_device42.diffsync.from_d42.device42 import Device42Adapter
from nautobot_ssot_device42.jobs import Device42DataSource


def load_json(path):
    """Load a json file."""
    with open(path, encoding="utf-8") as file:
        return json.loads(file.read())


BUILDING_FIXTURE = load_json("./nautobot_ssot_device42/tests/fixtures/get_buildings_recv.json")


class Device42AdapterTestCase(TestCase):
    """Test the Device42Adapter class."""

    def test_data_loading(self):
        """Test the load() function."""

        # Create a mock client
        d42_client = MagicMock()
        d42_client.get_buildings.return_value = BUILDING_FIXTURE

        job = Device42DataSource()
        job.job_result = JobResult.objects.create(
            name=job.class_path, obj_type=ContentType.objects.get_for_model(Job), user=None, job_id=uuid.uuid4()
        )
        device42 = Device42Adapter(job=job, sync=None, client=d42_client)
        device42.load_buildings()
        self.assertEqual(
            {site["name"] for site in BUILDING_FIXTURE},
            {site.get_unique_id() for site in device42.get_all("building")},
        )
