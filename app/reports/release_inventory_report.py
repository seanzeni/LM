from __future__ import annotations

"""
Purpose:
    Generate Release Inventory Report CSV.

Used By:
    Reports dialog

Responsibilities:
    - Report effort/project-level inventory issues.
    - Summarize missing inventory.
    - Summarize unexpected inventory for NOINV efforts.
    - Summarize inventory projects not connected to the SQL release.
    - Summarize inventory projects potentially tied to another SQL release.

Notes:
    This is an effort-level report.
    Individual element issues belong in IssuesReport.
"""

from collections import defaultdict
from datetime import datetime
from pathlib import Path

from app.core.models import Element
from app.core.models import InventoryIssue
from app.core.models import ReleaseEffort
from app.core.models import ScheduleStatus
from app.reports.report_utils import export_csv


class ReleaseInventoryReport:
    FILE_NAME = "Release_Inventory_Report.csv"

    def generate(
        self,
        release: str,
        mode: str,
        thread_count: int,
        elements: list[Element],
        inventory_issues: list[InventoryIssue],
        release_efforts: list[ReleaseEffort],
        output_folder: Path,
        include_empty: bool = False,
    ) -> Path:
        report_path = output_folder / self.FILE_NAME
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        rows: list[list[str]] = []

        elements_by_project = self._group_visible_elements_by_project(elements)

        efforts_by_id = {
            effort.effort_id.strip(): effort
            for effort in release_efforts
            if effort.effort_id.strip()
        }

        # Missing inventory comes from InventoryIssue because there are no
        # element rows to represent it.
        for issue in inventory_issues:
            if issue.issue_type != ScheduleStatus.SQL_EXPECTED_INVENTORY_MISSING:
                continue

            rows.append(
                [
                    generated_at,
                    release,
                    mode,
                    thread_count,
                    issue.effort_id,
                    "Missing Inventory",
                    0,
                    issue.reason,
                    issue.expected_release,
                    issue.inventory_release,
                ]
            )

        for project in sorted(elements_by_project.keys()):
            project_elements = elements_by_project.get(
                project,
                [],
            )

            if not project_elements:
                continue

            first_element = project_elements[0]
            element_count = len(project_elements)
            effort = efforts_by_id.get(project)

            if effort is not None and effort.no_inventory:
                rows.append(
                    [
                        generated_at,
                        release,
                        mode,
                        thread_count,
                        project,
                        "Unexpected Inventory",
                        element_count,
                        "SQL marks this project as no inventory, but inventory rows were found.",
                        release,
                        first_element.release,
                    ]
                )
                continue

            if first_element.schedule_status == ScheduleStatus.INVENTORY_NOT_IN_RELEASE:
                rows.append(
                    [
                        generated_at,
                        release,
                        mode,
                        thread_count,
                        project,
                        "Inventory Not In Release",
                        element_count,
                        first_element.display_reason,
                        release,
                        first_element.release,
                    ]
                )
                continue

            if first_element.schedule_status == ScheduleStatus.EFFORT_RELEASE_MISMATCH:
                rows.append(
                    [
                        generated_at,
                        release,
                        mode,
                        thread_count,
                        project,
                        "Potential Wrong Release",
                        element_count,
                        first_element.display_reason,
                        release,
                        first_element.release,
                    ]
                )

        if not rows and include_empty:
            rows.append(
                [
                    generated_at,
                    release,
                    mode,
                    thread_count,
                    "",
                    "No Issues",
                    0,
                    "No release inventory issues found.",
                    release,
                    "",
                ]
            )

        export_csv(
            output_path=report_path,
            headers=[
                "Generated At",
                "Release",
                "Mode",
                "Thread Count",
                "Project",
                "Inventory Status",
                "Element Count",
                "Reason",
                "Expected Release",
                "Inventory Release",
            ],
            rows=rows,
        )

        return report_path

    def _group_visible_elements_by_project(
        self,
        elements: list[Element],
    ) -> dict[str, list[Element]]:
        grouped: dict[str, list[Element]] = defaultdict(list)

        for element in elements:
            if not element.visible:
                continue

            grouped[element.project].append(element)

        return dict(grouped)
