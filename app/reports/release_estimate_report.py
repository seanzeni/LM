from __future__ import annotations

"""
Purpose:
    Generate Release Estimate Report CSV.

Used By:
    Reports dialog

Responsibilities:
    - Summarize selected visible elements by release move date.
    - Count selected elements by workload category.
    - Calculate estimated time by date.
    - Add a total row.

Notes:
    This report should not change selection state.
"""

from collections import defaultdict
from pathlib import Path
from typing import Any

from app.core.models import Element
from app.reports.report_utils import export_csv


class ReleaseEstimateReport:
    FILE_NAME = "Release_Estimate_Report.csv"

    def __init__(
        self,
        stats_service: Any,
    ) -> None:
        self.stats_service = stats_service

    def generate(
        self,
        elements: list[Element],
        effort_dates: dict[str, str],
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

            if not element.selected:
                continue

            move_date = effort_dates.get(
                element.project,
                "Unknown",
            )

            grouped[move_date].append(element)

        rows: list[list[str]] = []

        total_selected = 0
        total_minutes = 0
        total_category_counts: dict[str, int] = {}

        for move_date in sorted(grouped.keys()):
            date_elements = grouped[move_date]

            if not date_elements and not include_empty:
                continue

            estimate = self.stats_service.build_estimate(
                elements=date_elements,
                mode=mode,
                thread_count=thread_count,
            )

            category_counts = estimate.get(
                "category_counts",
                {},
            )

            category_minutes = estimate.get(
                "category_minutes",
                {},
            )

            selected_count = int(
                estimate.get(
                    "selected_elements",
                    0,
                )
            )

            total_selected += selected_count
            total_minutes += int(
                estimate.get(
                    "total_minutes",
                    0,
                )
            )

            for category, count in category_counts.items():
                total_category_counts[category] = total_category_counts.get(
                    category,
                    0,
                ) + int(count)

            rows.append(
                [
                    move_date,
                    selected_count,
                    category_counts.get("JCL", 0),
                    category_counts.get("NON_COMPILE", 0),
                    category_counts.get("COBOL", 0),
                    category_counts.get("APS", 0),
                    category_counts.get("X_ELEMENTS", 0),
                    category_counts.get("LINKDECK", 0),
                    category_minutes.get("JCL", 0),
                    category_minutes.get("NON_COMPILE", 0),
                    category_minutes.get("COBOL", 0),
                    category_minutes.get("APS", 0),
                    category_minutes.get("X_ELEMENTS", 0),
                    category_minutes.get("LINKDECK", 0),
                    estimate.get("estimated_time", "00:00"),
                ]
            )

        if rows or include_empty:
            rows.append(
                [
                    "TOTAL",
                    total_selected,
                    total_category_counts.get("JCL", 0),
                    total_category_counts.get("NON_COMPILE", 0),
                    total_category_counts.get("COBOL", 0),
                    total_category_counts.get("APS", 0),
                    total_category_counts.get("X_ELEMENTS", 0),
                    total_category_counts.get("LINKDECK", 0),
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    self.stats_service.format_minutes(total_minutes),
                ]
            )

        export_csv(
            output_path=report_path,
            headers=[
                "Move Date",
                "Selected Elements",
                "JCL Count",
                "Non Compile Count",
                "COBOL Count",
                "APS Count",
                "X Elements Count",
                "Linkdeck Count",
                "JCL Minutes",
                "Non Compile Minutes",
                "COBOL Minutes",
                "APS Minutes",
                "X Elements Minutes",
                "Linkdeck Minutes",
                "Estimated Time",
            ],
            rows=rows,
        )

        return report_path
