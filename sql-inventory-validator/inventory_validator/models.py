from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    INFO = "INFO"
    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True, slots=True)
class Employee:
    developer: str
    first_name: str
    last_name: str
    position: str
    email: str


@dataclass(frozen=True, slots=True)
class Project:
    project_code: str
    ccid: str
    project_name: str
    team_leader: str
    merge_region: str
    imp_date: date | None

    @property
    def merge_region_prefix(self) -> str:
        return self.merge_region.strip().upper()[:3]

    @property
    def derived_ccid(self) -> str:
        return self.project_code.strip()[:6]


@dataclass(frozen=True, slots=True)
class ElementRecord:
    project_code: str
    imp_date: date | None
    new_element: bool
    online: bool
    binds_required: bool
    trans_id: str
    element: str
    type: str
    processor_group: str
    application: str
    application_area: str
    other_area_impacts: str
    subsystem: str
    developer: str
    team_leader: str
    ndvr_package_name: str
    length: str
    test_coord: bool
    comments: str
    contact_number: str
    import_id: str
    import_date: datetime | None
    major_functions: str
    minor_functions: str
    project_merge_region: str = ""
    misc_system: str = ""
    misc_region: str = ""
    source_row: dict[str, Any] = field(default_factory=dict)

    @property
    def project_key(self) -> str:
        return self.project_code.strip().upper()


@dataclass(frozen=True, slots=True)
class Effort:
    id: str
    bundle_sequence: int | None
    team_lead: str
    bundle_merge_date: date | None
    bundle_qual_move_date: date | None
    bundle_prod_move_date: date | None
    bundle_exit_date: date | None


@dataclass(frozen=True, slots=True)
class Bundle:
    id: str
    sequence: int | None
    test_environment: int
    bundle_prod_imp_date: date | None


@dataclass(frozen=True, slots=True)
class Region:
    id: str
    test_environment: int

    @property
    def prefix(self) -> str:
        return self.id.strip().upper()[:3]


@dataclass(frozen=True, slots=True)
class MiscSystemRegion:
    system: str
    region: str

    @property
    def prefix(self) -> str:
        return self.region.strip().upper()[:3]


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    severity: Severity
    code: str
    message: str
    project_code: str = ""
    element: str = ""
    type: str = ""
    project_imp_date: date | None = None
    element_imp_date: date | None = None
    owner_id: str = ""
    owner_email: str = ""
    cc_email: str = ""
    bundle_id: str = ""
    bundle_sequence: int | None = None
    bundle_qual_date: date | None = None
    bundle_prod_date: date | None = None
    effort_qual_date: date | None = None
    effort_prod_date: date | None = None
