from __future__ import annotations

"""
Purpose:
    Central registry for available reports.

Used By:
    ReportCenter
    MainWindow

Responsibilities:
    - Register all report generators.
    - Provide display names.
    - Create report instances.
    - Route report generation calls.
"""

from pathlib import Path

from app.reports.effort_summary_report import EffortSummaryReport
from app.reports.issues_report import IssuesReport
from app.reports.osg_cops_report import OsgCopsReport
from app.reports.release_estimate_report import ReleaseEstimateReport
from app.reports.release_inventory_report import ReleaseInventoryReport


class ReportRegistry:
    def __init__(
        self,
        stats_service,
    ) -> None:
        self._reports = {
            "Issues Report": lambda: IssuesReport(),
            "Effort Summary Report": lambda: EffortSummaryReport(stats_service),
            "Release Estimate Report": lambda: ReleaseEstimateReport(stats_service),
            "Release Inventory Report": lambda: ReleaseInventoryReport(),
            "OSG/COPS Report": lambda: OsgCopsReport(),
        }

    def get_names(
        self,
    ) -> list[str]:
        return sorted(self._reports.keys())

    def create(
        self,
        name: str,
    ):
        if name not in self._reports:
            raise KeyError(f"Unknown report: {name}")

        return self._reports[name]()

    def generate(
        self,
        name: str,
        output_format: str,
        state,
        output_folder: Path,
        include_empty: bool,
    ) -> Path | None:
        report = self.create(name)

        if output_format.lower() == "pdf":
            raise NotImplementedError(f"PDF output is not implemented yet for {name}.")

        if name == "Issues Report":
            return report.generate(
                elements=state.loaded_elements,
                output_folder=output_folder,
                include_empty=include_empty,
            )

        if name == "Effort Summary Report":
            return report.generate(
                elements=state.loaded_elements,
                output_folder=output_folder,
                mode=state.mode,
                thread_count=state.thread_count,
                include_empty=include_empty,
            )

        if name == "Release Estimate Report":
            return report.generate(
                elements=state.loaded_elements,
                effort_dates=state.effort_dates,
                output_folder=output_folder,
                mode=state.mode,
                thread_count=state.thread_count,
                include_empty=include_empty,
            )

        if name == "Release Inventory Report":
            return report.generate(
                release=state.release,
                mode=state.mode,
                thread_count=state.thread_count,
                elements=state.loaded_elements,
                inventory_issues=state.inventory_issues,
                release_efforts=state.release_efforts,
                output_folder=output_folder,
                include_empty=include_empty,
            )

        if name == "OSG/COPS Report":
            return report.generate(
                elements=state.loaded_elements,
                output_folder=output_folder,
                mode=state.mode,
                include_empty=include_empty,
            )

        raise KeyError(f"Unknown report: {name}")
