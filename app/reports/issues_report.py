from __future__ import annotations

"""
Purpose:
    Generate Issues Report CSV.

Used By:
    Reports dialog

Responsibilities:
    - Export validation issues.
    - Export warnings.
    - Export informational statuses.
"""

from pathlib import Path

from app.core.models import Element
from app.reports.report_utils import export_csv
from app.reports.report_utils import sort_elements


class IssuesReport:
    FILE_NAME = "Issues_Report.csv"

    def generate(
        self,
        elements: list[Element],
        output_folder: Path,
        include_empty: bool = False,
    ) -> Path:
        report_path = output_folder / self.FILE_NAME

        rows: list[list[str]] = []

        for element in sort_elements(elements):
            if not element.visible:
                continue

            if not include_empty and not element.display_reason:
                continue

            rows.append(
                [
                    element.element,
                    element.type,
                    element.project,
                    element.release,
                    element.expected_system,
                    element.expected_region,
                    element.severity.value,
                    element.inventory_status.value,
                    element.schedule_status.value,
                    element.location_status.value,
                    element.archive_status.value,
                    element.fix_status.value,
                    element.movement_status.value,
                    element.display_reason,
                ]
            )

        export_csv(
            output_path=report_path,
            headers=[
                "Element",
                "Type",
                "Project",
                "Release",
                "Expected System",
                "Expected Region",
                "Severity",
                "Inventory Status",
                "Schedule Status",
                "Location Status",
                "Archive Status",
                "Fix Status",
                "Movement Status",
                "Reasons",
            ],
            rows=rows,
        )

        return report_path
