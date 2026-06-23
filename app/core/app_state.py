from __future__ import annotations

"""
Purpose:
    Store the current runtime state of the application.

Used By:
    MainWindow
    UI panels
    ReportDialog
    Reports

Responsibilities:
    - Track selected release and mode
    - Track thread count.
    - Track loaded inventory elements.
    - Track selected effort IDs.
    - Track SQL release efforts.
    - Track inventory/SQL validation issues.

Notes:
    This file should not load files.
    This file should not query SQL.
    This file should not run validation.
    This file should not build reports.
    
    It is only a state container.
"""

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

from app.core.models import Element
from app.core.models import InventoryIssue
from app.core.models import ReleaseEffort


@dataclass(slots=True)
class AppState:
    release: str = ""
    mode: str = "PROD"
    thread_count: int = 1

    current_xls_path: Path | None = None
    current_ndvr_path: Path | None = None

    selected_effort_ids: set[str] = field(default_factory=set)
    inventory_effort_ids: set[str] = field(default_factory=set)

    release_efforts: list[ReleaseEffort] = field(default_factory=list)
    loaded_elements: list[Element] = field(default_factory=list)
    inventory_issues: list[InventoryIssue] = field(default_factory=list)

    all_release_elements: list[Element] = field(default_factory=list)
    effort_dates: dict[str, str] = field(default_factory=dict)
    effort_release_lookup: dict[str, str] = field(default_factory=dict)

    def reset_release_data(
        self,
    ) -> None:
        self.selected_effort_ids.clear()
        self.inventory_effort_ids.clear()
        self.release_efforts.clear()
        self.loaded_elements.clear()
        self.inventory_issues.clear()
        self.all_release_elements.clear()
        self.effort_dates.clear()
        self.effort_release_lookup.clear()

    def reset_elements(
        self,
    ) -> None:
        self.loaded_elements.clear()
        self.inventory_issues.clear()

    @property
    def selected_elements(
        self,
    ) -> list[Element]:
        return [element for element in self.loaded_elements if element.selected]

    @property
    def available_elements(
        self,
    ) -> list[Element]:
        return [element for element in self.loaded_elements if element.selectable]
