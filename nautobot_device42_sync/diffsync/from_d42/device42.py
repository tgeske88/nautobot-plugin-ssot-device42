"""DiffSync adapter for Device42."""

from django.utils.functional import classproperty
from diffsync import DiffSync

from nautobot_device42_sync.diffsync.from_d42 import models
from nautobot_device42_sync.diffsync.d42utils import Device42API
from nautobot_device42_sync.constant import PLUGIN_CFG
from nautobot_device42_sync.constant import DEFAULTS
from decimal import Decimal


class Device42Adapter(DiffSync):
    """DiffSync adapter using requests to communicate to Device42 server."""

    building = models.Building
    room = models.Room
    vendor = models.Vendor
    hardware = models.Hardware
    device = models.Device
    top_level = ["building"]

    def __init__(self, *args, job=None, sync=None, **kwargs):
        """Initialize Device42Adapter.

        Args:
            job (object, optional): Nautobot job. Defaults to None.
            sync (object, optional): Nautobot DiffSync. Defaults to None.
        """
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self._device42_hardware_dict = {}
        self._device42 = Device42API(
            base_url=PLUGIN_CFG["device42_host"],
            username=PLUGIN_CFG["device42_username"],
            password=PLUGIN_CFG["device42_password"],
            verify=PLUGIN_CFG["verify_ssl"],
        )

    @classproperty
    def _device42_hardwares(self):
        if not self._device42_hardware_dict:
            device42_hardware_list = self._device42.api_call(path="api/2.0/hardwares/")["models"]
            for hardware in device42_hardware_list["models"]:
                self._device42_hardware_dict[hardware["hardware_id"]] = hardware
        return self._device42_hardware_dict

    def load_buildings(self):
        """Load Device42 buildings."""
        for record in self._device42.api_call(path="api/1.0/buildings")["buildings"]:
            building = self.building(
                name=record["name"],
                address=record["address"] if record.get("address") else "",
                latitude=round(Decimal(record["latitude"] if record["latitude"] else 0.0), 6),
                longitude=round(Decimal(record["longitude"] if record["longitude"] else 0.0), 6),
                contact_name=record["contact_name"] if record.get("contact_name") else "",
                contact_phone=record["contact_phone"] if record.get("contact_phone") else "",
                rooms=record["rooms"] if record.get("rooms") else [],
            )
            self.add(building)

    def load_rooms(self):
        """Load Device42 rooms."""
        for record in self._device42.api_call(path="api/1.0/rooms")["rooms"]:
            room = self.room(
                name=record["name"],
                building=record["building"] if record.get("building") else DEFAULTS.get("site"),
                notes=record["notes"] if record.get("notes") else "",
            )
            self.add(room)
            _site = self.get(models.Building, record.get("building"))
            _site.add_child(child=room)

    def load_devices(self):
        """Load Device42 devices."""
        for device_record in self._device42.api_call(path="api/2.0/devices/")["Devices"]:
            device = self.device(
                device_name=device_record["name"],
                hardware=self._device42_hardwares[device_record["hardware_id"]]["name"]
                if device_record.get("hardware_id")
                else None,
                serial=device_record["serial_no"],
            )
            self.add(device)

    def load(self):
        """Load data from Device42."""
        self.load_buildings()
        self.load_rooms()
        # self.load_devices()
