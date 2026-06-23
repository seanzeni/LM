from __future__ import annotations

"""
Purpose:
    Detect movement-related marker text from inventory rows.

Used By:
    ValidationService

Responsibilities:
    - Read configured marker columns from an Element source row.
    - Detect do-not-move markers.
    - Detect already-in-PROD markers.
    - Detect already-in-QUAL markers.

Notes:
    This service does not apply validation statuses.
    This service does not decide selected/selectable behavior.
"""

from app.core.models import Element
from app.core.package_rules import is_do_not_move
from app.core.package_rules import is_marked_prod
from app.core.package_rules import is_marked_qual


class StatusMarkerService:
    def __init__(
        self,
        status_markers: dict,
    ) -> None:
        self.marker_columns: list[str] = [
            str(column)
            for column in status_markers.get(
                "marker_columns",
                ["Package"],
            )
        ]

        self.do_not_move_markers: list[str] = [
            str(marker)
            for marker in status_markers.get(
                "do_not_move",
                [],
            )
        ]

        self.already_in_prod_markers: list[str] = [
            str(marker)
            for marker in status_markers.get(
                "already_in_prod",
                [],
            )
        ]

        self.already_in_qual_markers: list[str] = [
            str(marker)
            for marker in status_markers.get(
                "already_in_qual",
                [],
            )
        ]

    def get_marker_text(
        self,
        element: Element,
    ) -> str:
        values: list[str] = []

        for column in self.marker_columns:
            value = str(
                element.source_row.get(
                    column,
                    "",
                )
            ).strip()

            if value:
                values.append(value)

        return " ".join(values)

    def is_do_not_move(
        self,
        element: Element,
    ) -> bool:
        return is_do_not_move(
            value=self.get_marker_text(element),
            markers=self.do_not_move_markers,
        )

    def is_marked_prod(
        self,
        element: Element,
    ) -> bool:
        return is_marked_prod(
            value=self.get_marker_text(element),
            markers=self.already_in_prod_markers,
        )

    def is_marked_qual(
        self,
        element: Element,
    ) -> bool:
        return is_marked_qual(
            value=self.get_marker_text(element),
            markers=self.already_in_qual_markers,
        )

    def is_marked_for_target(
        self,
        element: Element,
        mode: str,
    ) -> bool:
        clean_mode = str(mode).strip().upper()

        if clean_mode == "PROD":
            return self.is_marked_prod(element)

        if clean_mode == "QUAL":
            return self.is_marked_qual(element)

        return False

    def get_target_marker_text(
        self,
        element: Element,
        mode: str,
    ) -> str:
        """
        Return the marker family text for reporting.

        This does not return the exact matching token.
        It returns PROD or QUAL based on the requested target.
        """

        clean_mode = str(mode).strip().upper()

        if clean_mode == "PROD" and self.is_marked_prod(element):
            return "PROD"

        if clean_mode == "QUAL" and self.is_marked_qual(element):
            return "QUAL"

        return ""
