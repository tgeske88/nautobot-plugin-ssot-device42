"""DiffSyncModel Circuit subclasses for Nautobot Device42 data sync."""

from typing import List, Optional
from uuid import UUID

from diffsync import DiffSyncModel
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from nautobot.circuits.models import Circuit as NautobotCircuit
from nautobot.circuits.models import CircuitTermination as NautobotCT
from nautobot.circuits.models import Provider as NautobotProvider
from nautobot.dcim.models import Cable as NautobotCable
from nautobot.dcim.models import Device as NautobotDevice
from nautobot.dcim.models import Interface as NautobotInterface
from nautobot.extras.models import Status as NautobotStatus
from nautobot_ssot_device42.constant import INTF_SPEED_MAP
from nautobot_ssot_device42.utils import nautobot


class Provider(DiffSyncModel):
    """Device42 Provider model."""

    _modelname = "provider"
    _identifiers = ("name",)
    _attributes = ("notes", "vendor_url", "vendor_acct", "vendor_contact1", "vendor_contact2")
    _children = {}

    name: str
    notes: Optional[str]
    vendor_url: Optional[str]
    vendor_acct: Optional[str]
    vendor_contact1: Optional[str]
    vendor_contact2: Optional[str]
    tags: Optional[List[str]]
    uuid: Optional[UUID]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Provider object in Nautobot."""
        try:
            _provider = NautobotProvider.objects.get(name=ids["name"])
        except NautobotProvider.DoesNotExist:
            _provider = NautobotProvider(
                name=ids["name"],
                slug=slugify(ids["name"]),
                account=attrs["vendor_acct"] if attrs.get("vendor_acct") else "",
                portal_url=attrs["vendor_url"] if attrs.get("vendor_url") else "",
                noc_contact=attrs["vendor_contact1"] if attrs.get("vendor_contact1") else "",
                admin_contact=attrs["vendor_contact2"] if attrs.get("vendor_contact2") else "",
                comments=attrs["notes"] if attrs.get("notes") else "",
            )
            if attrs.get("tags"):
                for _tag in nautobot.get_tags(attrs["tags"]):
                    _provider.tags.add(_tag)
            _provider.validated_save()
            return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Provider object in Nautobot."""
        _prov = NautobotProvider.objects.get(id=self.uuid)
        if attrs.get("notes"):
            _prov.comments = attrs["notes"]
        if attrs.get("vendor_url"):
            _prov.portal_url = attrs["vendor_url"]
        if attrs.get("vendor_acct"):
            _prov.account = attrs["vendor_acct"]
        if attrs.get("vendor_contact1"):
            _prov.noc_contact = attrs["vendor_contact1"]
        if attrs.get("vendor_contact2"):
            _prov.admin_contact = attrs["vendor_contact2"]
        _prov.validated_save()
        return super().update(attrs)

    def delete(self):
        """Delete Provider object from Nautobot.

        Because Provider has a direct relationship with Circuits it can't be deleted before them.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(message=f"Provider {self.name} will be deleted.")
        super().delete()
        provider = NautobotProvider.objects.get(id=self.uuid)
        self.diffsync.objects_to_delete["provider"].append(provider)  # pylint: disable=protected-access
        return self


class Circuit(DiffSyncModel):
    """Device42 TelcoCircuit model."""

    _modelname = "circuit"
    _identifiers = (
        "circuit_id",
        "provider",
    )
    _attributes = (
        "notes",
        "type",
        "status",
        "install_date",
        "origin_int",
        "origin_dev",
        "endpoint_int",
        "endpoint_dev",
        "bandwidth",
        "tags",
    )
    _children = {}
    circuit_id: str
    provider: str
    notes: Optional[str]
    type: str
    status: str
    install_date: Optional[str]
    origin_int: Optional[str]
    origin_dev: Optional[str]
    endpoint_int: Optional[str]
    endpoint_dev: Optional[str]
    bandwidth: Optional[int]
    tags: Optional[List[str]]
    uuid: Optional[UUID]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Circuit object in Nautobot."""
        try:
            NautobotCircuit.objects.get(cid=ids["circuit_id"])
        except NautobotCircuit.DoesNotExist:
            _circuit = NautobotCircuit(
                cid=ids["circuit_id"],
                provider=NautobotProvider.objects.get(name=ids["provider"]),
                type=nautobot.verify_circuit_type(attrs["type"]),
                status=NautobotStatus.objects.get(name=attrs["status"]),
                install_date=attrs["install_date"] if attrs.get("install_date") else None,
                commit_rate=attrs["bandwidth"] if attrs.get("bandwidth") else None,
                comments=attrs["notes"] if attrs.get("notes") else "",
            )
            if attrs.get("tags"):
                for _tag in nautobot.get_tags(attrs["tags"]):
                    _circuit.tags.add(_tag)
            _circuit.validated_save()
            if attrs.get("origin_int") and attrs.get("origin_dev"):
                cls.connect_circuit_to_device(
                    intf=attrs["origin_int"], dev=attrs["origin_dev"], term_side="A", circuit=_circuit
                )
            if attrs.get("endpoint_int") and attrs.get("endpoint_dev"):
                cls.connect_circuit_to_device(
                    intf=attrs["endpoint_int"], dev=attrs["endpoint_dev"], term_side="Z", circuit=_circuit
                )
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update Circuit object in Nautobot."""
        _circuit = NautobotCircuit.objects.get(id=self.uuid)
        if attrs.get("notes"):
            _circuit.comments = attrs["notes"]
        if attrs.get("type"):
            _circuit.type = nautobot.verify_circuit_type(attrs["type"])
        if attrs.get("status"):
            _circuit.status = NautobotStatus.objects.get(name=self.get_circuit_status(attrs["status"]))
        if attrs.get("install_date"):
            _circuit.install_date = attrs["install_date"]
        if attrs.get("bandwidth"):
            _circuit.commit_rate = attrs["bandwidth"]
        if attrs.get("origin_int") and attrs.get("origin_dev"):
            self.connect_circuit_to_device(
                intf=attrs["origin_int"], dev=attrs["origin_dev"], term_side="A", circuit=_circuit
            )
        if attrs.get("endpoint_int") and attrs.get("endpoint_dev"):
            self.connect_circuit_to_device(
                intf=attrs["endpoint_int"], dev=attrs["endpoint_dev"], term_side="Z", circuit=_circuit
            )
        _circuit.validated_save()
        return super().update(attrs)

    @staticmethod
    def connect_circuit_to_device(intf: str, dev: str, term_side: str, circuit: NautobotCircuit):
        """Method to handle Circuit Termination to a Device.

        Args:
            intf (str): Interface of Device to connect Circuit Termination.
            dev (str): Device with respective interface to connect Circuit to.
            term_side (str): Which side of the CircuitTermination this connection is on, A or Z.
            circuit (NautobotCircuit): The actual Circuit object that the CircuitTermination is connecting to.
        """
        try:
            _intf = NautobotInterface.objects.get(name=intf, device=NautobotDevice.objects.get(name=dev))
            try:
                _term = NautobotCT.objects.get(circuit=circuit, term_side=term_side)
            except NautobotCT.DoesNotExist:
                _term = NautobotCT(
                    circuit=circuit,
                    term_side=term_side,
                    site=_intf.device.site,
                    port_speed=INTF_SPEED_MAP[_intf.type],
                )
                _term.validated_save()
            if _intf and not _intf.cable and not _term.cable:
                new_cable = NautobotCable(
                    termination_a_type=ContentType.objects.get(app_label="dcim", model="interface"),
                    termination_a_id=_intf.id,
                    termination_b_type=ContentType.objects.get(app_label="circuits", model="circuittermination"),
                    termination_b_id=_term.id,
                    status=NautobotStatus.objects.get(name="Connected"),
                    color=nautobot.get_random_color(),
                )
                new_cable.validated_save()
        except NautobotDevice.DoesNotExist as err:
            print(f"Unable to find {dev} {err}")
        except NautobotInterface.DoesNotExist as err:
            print(f"Unable to find {intf} {dev} {err}")

    def delete(self):
        """Delete Provider object from Nautobot.

        Because Provider has a direct relationship with Circuits it can't be deleted before them.
        The self.diffsync.objects_to_delete dictionary stores all objects for deletion and removes them from Nautobot
        in the correct order. This is used in the Nautobot adapter sync_complete function.
        """
        self.diffsync.job.log_warning(message=f"Circuit {self.circuit_id} will be deleted.")
        super().delete()
        circuit = NautobotCircuit.objects.get(id=self.uuid)
        self.diffsync.objects_to_delete["circuit"].append(circuit)  # pylint: disable=protected-access
        return self
