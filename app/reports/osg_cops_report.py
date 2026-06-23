from __future__ import annotations

"""
Purpose:
    Generate OSG/COPS Report CSV.

Used By:
    Reports dialog

Responsibilities:
    - Report selected visible elements beginning with O or X.
    - Deduplicate element/type combinations for PROD movement.
    - Keep export/report output alphabetically sorted by element.

Notes:
    This report is based only on selected items.
"""

from pathlib import Path

from app.core.models import Element
from app.reports.report_utils import export_csv


class OsgCopsReport:
    FILE_NAME = "OSG_COPS_Report.csv"

    def generate(
        self,
        elements: list[Element],
        output_folder: Path,
        mode: str,
        include_empty: bool = False,
    ) -> Path:
        report_path = output_folder / self.FILE_NAME

        rows: list[list[str]] = []
        seen: set[tuple[str, str]] = set()

        selected_elements = [
            element
            for element in elements
            if element.visible
            and element.selected
            and self._is_osg_cops_element(element)
        ]

        for element in sorted(
            selected_elements,
            key=lambda item: (
                item.element.upper(),
                item.type.upper(),
            ),
        ):
            if mode.upper() == "PROD":
                if element.key in seen:
                    continue

                seen.add(element.key)

            rows.append(
                [
                    element.release,
                    element.project,
                    element.element,
                    element.type,
                    element.source_row.get("Submitter", ""),
                    element.source_row.get("Application", ""),
                    element.source_row.get("Package", ""),
                    element.source_row.get("Area", ""),
                    element.source_row.get("Service", ""),
                ]
            )

        if not rows and include_empty:
            rows.append(
                [
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "No selected OSG/COPS elements found.",
                ]
            )

        export_csv(
            output_path=report_path,
            headers=[
                "Release",
                "Project",
                "Element",
                "Type",
                "Submitter",
                "Application",
                "Package",
                "Area",
                "Service",
            ],
            rows=rows,
        )

        return report_path

    def _is_osg_cops_element(
        self,
        element: Element,
    ) -> bool:
        return element.element.upper().startswith(
            ("O", "X")
        ) or element.type.upper().startswith(("O", "X"))
