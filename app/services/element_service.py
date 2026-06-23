from __future__ import annotations

"""
Purpose:
    Convert inventory rows into Element models.

Used By:
    ValidationService
    MainWindow
    Reports

Responsibilities:
    - Build Element objects.
    - Build common lookup dictionaries.
    - Build element/type indexes.

Notes:
    This service should not perform validation.
    This service should not query SQL.
"""

from collections import defaultdict

import pandas as pd

from app.core.models import Element


class ElementService:

    def build_elements(
        self,
        df: pd.DataFrame,
    ) -> list[Element]:

        elements: list[Element] = []

        for _, row in df.iterrows():

            project: str = str(
                row.get(
                    "Project",
                    "",
                )
            ).strip()

            element_name: str = str(
                row.get(
                    "Element",
                    "",
                )
            ).strip()

            type_name: str = str(
                row.get(
                    "Type",
                    "",
                )
            ).strip()

            elements.append(
                Element(
                    release=str(
                        row.get(
                            "Release",
                            "",
                        )
                    ).strip(),
                    project=project,
                    element=element_name,
                    type=type_name,
                    expected_subsystem=str(
                        row.get(
                            "Subsys",
                            "",
                        )
                    ).strip(),
                    expected_system=str(
                        row.get(
                            "System",
                            "",
                        )
                    ).strip(),
                    expected_region=str(
                        row.get(
                            "Act Rgn",
                            "",
                        )
                    ).strip(),
                    source_row=dict(row),
                )
            )

        return elements

    def build_element_lookup(
        self,
        elements: list[Element],
    ) -> dict[tuple[str, str], list[Element]]:

        lookup: dict[
            tuple[str, str],
            list[Element],
        ] = defaultdict(list)

        for element in elements:
            lookup[element.key].append(element)

        return dict(lookup)

    def build_name_lookup(
        self,
        elements: list[Element],
    ) -> dict[str, list[Element]]:

        lookup: dict[
            str,
            list[Element],
        ] = defaultdict(list)

        for element in elements:
            lookup[element.element.upper()].append(element)

        return dict(lookup)

    def build_project_lookup(
        self,
        elements: list[Element],
    ) -> dict[str, list[Element]]:

        lookup: dict[
            str,
            list[Element],
        ] = defaultdict(list)

        for element in elements:
            lookup[element.project_key].append(element)

        return dict(lookup)

    def build_release_lookup(
        self,
        elements: list[Element],
    ) -> dict[str, list[Element]]:

        lookup: dict[
            str,
            list[Element],
        ] = defaultdict(list)

        for element in elements:
            lookup[element.release.upper()].append(element)

        return dict(lookup)

    def build_element_type_set(
        self,
        elements: list[Element],
    ) -> set[tuple[str, str]]:

        return {element.key for element in elements}

    def build_element_name_type_lookup(
        self,
        elements: list[Element],
    ) -> dict[str, set[str]]:

        lookup: dict[
            str,
            set[str],
        ] = defaultdict(set)

        for element in elements:
            lookup[element.element.upper()].add(element.type.upper())

        return dict(lookup)
