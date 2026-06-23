from __future__ import annotations

"""
Purpose:
    Export selected visible elements to fixed-width mainframe format.

Used By:
    MainWindow

Responsibilities:
    - Sort selected export rows alphabetically by element name.
    - Build fixed-width export records.
    - Write export file.

Notes:
    This file should not apply validation rules.
    Validation already happened before export.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.formatter import build_record
from app.core.models import Element


class Exporter:
    def __init__(
        self,
        settings: dict[str, Any],
        base_dir: str | Path,
    ) -> None:
        self.settings = settings
        self.base_dir = Path(base_dir)

    def sort_elements(
        self,
        elements: list[Element],
    ) -> list[Element]:
        return sorted(
            elements,
            key=lambda element: element.element.upper(),
        )

    def build_lines(
        self,
        elements: list[Element],
        mode: str,
    ) -> list[str]:
        selected_elements = [
            element for element in elements if element.visible and element.selected
        ]

        return [
            build_record(
                source_row=element.source_row,
                mode=mode,
            )
            for element in self.sort_elements(selected_elements)
        ]

    def build_default_output_path(
        self,
        release: str,
    ) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return self.base_dir / f"{release}_export_{timestamp}.txt"

    def export(
        self,
        elements: list[Element],
        mode: str,
        release: str,
        output_path: str | Path | None = None,
    ) -> Path:
        path = (
            Path(output_path)
            if output_path is not None
            else self.build_default_output_path(release)
        )

        lines = self.build_lines(
            elements=elements,
            mode=mode,
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:
            file.write("\n".join(lines))

        return path
