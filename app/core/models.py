from __future__ import annotations

"""
Purpose:
    Shared application models and status enums.

Used By:
    Services
    Reports
    UI

Notes:
    Keep business rules out of this file.
    This file defines state, severity, colors, and model helpers only.
"""

from dataclasses import dataclass
from dataclasses import field
from strenum import StrEnum
from typing import Any


class Severity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ScheduleStatus(StrEnum):
    OK = "OK"
    INVENTORY_NOT_IN_RELEASE = "INVENTORY_NOT_IN_RELEASE"
    INVENTORY_WHEN_SQL_NO_INVENTORY = "INVENTORY_WHEN_SQL_NO_INVENTORY"
    SQL_EXPECTED_INVENTORY_MISSING = "SQL_EXPECTED_INVENTORY_MISSING"
    EFFORT_RELEASE_MISMATCH = "EFFORT_RELEASE_MISMATCH"

    @property
    def severity(self) -> Severity:
        return {
            ScheduleStatus.OK: Severity.INFO,
            ScheduleStatus.INVENTORY_NOT_IN_RELEASE: Severity.WARNING,
            ScheduleStatus.INVENTORY_WHEN_SQL_NO_INVENTORY: Severity.WARNING,
            ScheduleStatus.SQL_EXPECTED_INVENTORY_MISSING: Severity.ERROR,
            ScheduleStatus.EFFORT_RELEASE_MISMATCH: Severity.WARNING,
        }.get(self, Severity.INFO)

    @property
    def color(self) -> str:
        return {
            ScheduleStatus.OK: "",
            ScheduleStatus.INVENTORY_NOT_IN_RELEASE: "warning",
            ScheduleStatus.INVENTORY_WHEN_SQL_NO_INVENTORY: "warning",
            ScheduleStatus.SQL_EXPECTED_INVENTORY_MISSING: "error",
            ScheduleStatus.EFFORT_RELEASE_MISMATCH: "warning",
        }.get(self, "")


class LocationStatus(StrEnum):
    OK = "OK"
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"

    @property
    def severity(self) -> Severity:
        return {
            LocationStatus.OK: Severity.INFO,
            LocationStatus.FOUND: Severity.INFO,
            LocationStatus.NOT_FOUND: Severity.ERROR,
        }.get(self, Severity.INFO)

    @property
    def color(self) -> str:
        return {
            LocationStatus.OK: "",
            LocationStatus.FOUND: "",
            LocationStatus.NOT_FOUND: "error",
        }.get(self, "")


class InventoryStatus(StrEnum):
    OK = "OK"
    OVERLAP = "OVERLAP"
    DUPLICATE = "DUPLICATE"

    @property
    def severity(self) -> Severity:
        return {
            InventoryStatus.OK: Severity.INFO,
            InventoryStatus.OVERLAP: Severity.ERROR,
            InventoryStatus.DUPLICATE: Severity.ERROR,
        }.get(self, Severity.INFO)

    @property
    def color(self) -> str:
        return {
            InventoryStatus.OK: "",
            InventoryStatus.OVERLAP: "error",
            InventoryStatus.DUPLICATE: "error",
        }.get(self, "")


class ArchiveStatus(StrEnum):
    OK = "OK"
    ARCHIVE_IN_QUAL = "ARCHIVE_IN_QUAL"
    POTENTIAL_MISSING_ARCHIVE = "POTENTIAL_MISSING_ARCHIVE"
    POTENTIAL_MISSING_PROGRAM_MOVE = "POTENTIAL_MISSING_PROGRAM_MOVE"

    @property
    def severity(self) -> Severity:
        return {
            ArchiveStatus.OK: Severity.INFO,
            ArchiveStatus.ARCHIVE_IN_QUAL: Severity.INFO,
            ArchiveStatus.POTENTIAL_MISSING_ARCHIVE: Severity.ERROR,
            ArchiveStatus.POTENTIAL_MISSING_PROGRAM_MOVE: Severity.WARNING,
        }.get(self, Severity.INFO)

    @property
    def color(self) -> str:
        return {
            ArchiveStatus.OK: "",
            ArchiveStatus.ARCHIVE_IN_QUAL: "hidden",
            ArchiveStatus.POTENTIAL_MISSING_ARCHIVE: "error",
            ArchiveStatus.POTENTIAL_MISSING_PROGRAM_MOVE: "warning",
        }.get(self, "")


class MovementStatus(StrEnum):
    OK = "OK"
    DO_NOT_MOVE = "DO_NOT_MOVE"
    MARKED_ALREADY_THERE_BUT_MISSING = "MARKED_ALREADY_THERE_BUT_MISSING"

    @property
    def severity(self) -> Severity:
        return {
            MovementStatus.OK: Severity.INFO,
            MovementStatus.DO_NOT_MOVE: Severity.INFO,
            MovementStatus.MARKED_ALREADY_THERE_BUT_MISSING: Severity.WARNING,
        }.get(self, Severity.INFO)

    @property
    def color(self) -> str:
        return {
            MovementStatus.OK: "",
            MovementStatus.DO_NOT_MOVE: "hidden",
            MovementStatus.MARKED_ALREADY_THERE_BUT_MISSING: "warning",
        }.get(self, "")


class FixStatus(StrEnum):
    OK = "OK"
    EXISTS_IN_FIXP1 = "EXISTS_IN_FIXP1"

    @property
    def severity(self) -> Severity:
        return {
            FixStatus.OK: Severity.INFO,
            FixStatus.EXISTS_IN_FIXP1: Severity.WARNING,
        }.get(self, Severity.INFO)

    @property
    def color(self) -> str:
        return {
            FixStatus.OK: "",
            FileExistsError.__reduce_ex__: "warning",
        }.get(self, "")


class ResyncStatus(StrEnum):
    OK = "OK"
    HIGHER_VERSION_EXISTS = "HIGHER_VERSION_EXISTS"

    @property
    def severity(self) -> Severity:
        return {
            ResyncStatus.OK: Severity.INFO,
            ResyncStatus.HIGHER_VERSION_EXISTS: Severity.WARNING,
        }.get(self, Severity.INFO)

    @property
    def color(self) -> str:
        return {
            ResyncStatus.OK: "",
            ResyncStatus.HIGHER_VERSION_EXISTS: "warning",
        }.get(self, "")


@dataclass(slots=True)
class Element:
    release: str
    project: str
    element: str
    type: str

    expected_subsystem: str = ""
    expected_system: str = ""
    expected_region: str = ""

    selected: bool = True
    selectable: bool = True
    visible: bool = True

    schedule_status: ScheduleStatus = ScheduleStatus.OK
    location_status: LocationStatus = LocationStatus.OK
    inventory_status: InventoryStatus = InventoryStatus.OK
    archive_status: ArchiveStatus = ArchiveStatus.OK
    movement_status: MovementStatus = MovementStatus.OK
    fix_status: FixStatus = FixStatus.OK
    resync_status: ResyncStatus = ResyncStatus.OK

    reasons: list[str] = field(default_factory=list)
    source_row: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str]:
        return (self.element.strip().upper(), self.type.strip().upper())

    @property
    def project_key(self) -> str:
        return self.project.strip().upper()

    @property
    def active_statuses(self) -> list[str]:
        statuses = [
            self.schedule_status,
            self.location_status,
            self.inventory_status,
            self.archive_status,
            self.movement_status,
            self.fix_status,
            self.resync_status,
        ]

        return [
            str(status.value)
            for status in statuses
            if str(status.value) not in {"OK", "FOUND"}
        ]

    @property
    def severity(self) -> Severity:
        severities = [
            self.schedule_status.severity,
            self.location_status.severity,
            self.inventory_status.severity,
            self.archive_status.severity,
            self.movement_status.severity,
            self.movement_status.severity,
            self.fix_status.severity,
            self.resync_status.severity,
        ]

        if Severity.ERROR in severities:
            return Severity.ERROR

        if Severity.WARNING in severities:
            return Severity.WARNING

        return Severity.INFO

    @property
    def color(self) -> str:
        for status in [
            self.location_status,
            self.schedule_status,
            self.inventory_status,
            self.archive_status,
            self.movement_status,
            self.fix_status,
            self.resync_status,
        ]:
            if status.color:
                return status.color

        return ""

    @property
    def display_reason(self) -> str:
        return "; ".join(self.reasons)

    @property
    def display_sort_key(self) -> tuple[int, str, str]:
        priority = {
            Severity.ERROR: 0,
            Severity.WARNING: 1,
            Severity.INFO: 2,
        }.get(self.severity, 2)

        return (
            priority,
            self.element.upper(),
            self.type.upper(),
        )


@dataclass(slots=True)
class ReleaseEffort:
    effort_id: str
    qual_date: Any | None = None
    prod_date: Any | None = None
    exit_date: Any | None = None
    no_inventory: bool = False

    @property
    def withdrawn(self) -> bool:
        return self.exit_date is not None


@dataclass(slots=True)
class InventoryIssue:
    release: str
    effort_id: str
    issue_type: ScheduleStatus
    reason: str
    expected_release: str = ""
    inventory_release: str = ""


@dataclass(frozen=True, slots=True)
class MainframeLocationRecord:
    element: str
    type: str
    subsystem: str
    system: str
    env: str
    date_generated: str
    time_generated: str
    version: str
    major_version: int
    level: int
    user: str
    ccid: str
    comments: str

    @property
    def key(self) -> tuple[str, str]:
        return (
            self.element.upper(),
            self.type.upper(),
        )

    @property
    def element_key(self) -> str:
        return self.element.upper()

    @property
    def version_number(self) -> int:
        return (self.major_version * 100) + self.level
