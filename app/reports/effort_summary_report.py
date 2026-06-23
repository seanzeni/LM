from __future__ import annotations

"""
Purpose:
    Generate Effort Summary Report CSV.

Used By:
    Reports dialog

Responsibilities:
    - Group visible elements by effort/project.
    - Count selected elements.
    - Count errors, warnings, and info statuses.
    - Count selected elements by workload category.
    - Calculate estimated time per effort.
"""

from collections import defaultdict
from pathlib import Path
from typing import Any

from app.core.models import Element
from app.core.models import Severity
from app.reports.report_utils import export_csv


class EffortSummaryReport:
    FILE_NAME = "Effort_Summary_Report.csv"

    def __init__(
        self,
        stats_service: Any,
    ) -> None:
        self.stats_service = stats_service

    def generate(
        self,
        elements: list[Element],
        output_folder: Path,
        mode: str,
        thread_count: int,
        include_empty: bool = False,
    ) -> Path:
        report_path = output_folder / self.FILE_NAME

        grouped: dict[str, list[Element]] = defaultdict(list)

        for element in elements:
            if not element.visible:
                continue

            grouped[element.project].append(element)

        rows: list[list[str]] = []

        for project in sorted(grouped.keys()):
            project_elements = grouped[project]

            selected_elements = [
                element for element in project_elements if element.selected
            ]

            if not selected_elements and not include_empty:
                continue

            estimate = self.stats_service.build_estimate(
                elements=project_elements,
                mode=mode,
                thread_count=thread_count,
            )

            category_counts = estimate.get(
                "category_counts",
                {},
            )

            rows.append(
                [
                    project,
                    len(selected_elements),
                    self._count_severity(project_elements, Severity.ERROR),
                    self._count_severity(project_elements, Severity.WARNING),
                    self._count_severity(project_elements, Severity.INFO),
                    category_counts.get("JCL", 0),
                    category_counts.get("NON_COMPILE", 0),
                    category_counts.get("COBOL", 0),
                    category_counts.get("APS", 0),
                    category_counts.get("X_ELEMENTS", 0),
                    category_counts.get("LINKDECK", 0),
                    estimate.get("estimated_time", "00:00"),
                ]
            )

        export_csv(
            output_path=report_path,
            headers=[
                "Project",
                "Selected Elements",
                "Errors",
                "Warnings",
                "Info",
                "JCL Count",
                "Non Compile Count",
                "COBOL Count",
                "APS Count",
                "X Elements Count",
                "Linkdeck Count",
                "Estimated Time",
            ],
            rows=rows,
        )

        return report_path

    def _count_severity(
        self,
        elements: list[Element],
        severity: Severity,
    ) -> int:
        return sum(
            1
            for element in elements
            if element.visible and element.severity == severity
        )
