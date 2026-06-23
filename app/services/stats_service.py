from __future__ import annotations

"""
Purpose:
    Calculate workload estimates and dashboard statistics.

Used By:
    MainWindow
    Reports
    StatsPanel

Responsibilities:
    - Categorize element types.
    - Calculate selected element counts.
    - Calculate estimated time using threads.
    - Build statistics for the dashboard.

Notes:
    This service does not validate inventory.
    This service does not export files.
    This service does not query SQL.
"""

from math import ceil
from typing import Any

from app.core.models import Element
from app.core.models import Severity


class StatsService:
    def __init__(
        self,
        workload_settings: dict,
    ) -> None:
        self.default_thread_count: int = int(
            workload_settings.get(
                "default_thread_count",
                1,
            )
        )

        self.type_categories: dict[str, list[str]] = dict(
            workload_settings.get(
                "type_categories",
                {},
            )
        )

        self.types_per_hour_per_thread: dict[str, dict[str, int | float]] = dict(
            workload_settings.get(
                "types_per_hour_per_thread",
                {},
            )
        )

    def categorize_type(
        self,
        type_name: str,
    ) -> str:
        clean_type = str(type_name or "").strip().upper()

        for category, values in self.type_categories.items():
            normalized_values = {str(value).strip().upper() for value in values}

            if clean_type in normalized_values:
                return category

        return "JCL"

    def get_rate_per_hour_per_thread(
        self,
        category: str,
        mode: str,
    ) -> float:
        mode_rates = self.types_per_hour_per_thread.get(
            str(mode).upper(),
            {},
        )

        rate = float(
            mode_rates.get(
                category,
                0,
            )
        )

        return rate

    def build_category_counts(
        self,
        elements: list[Element],
    ) -> dict[str, int]:
        counts: dict[str, int] = {category: 0 for category in self.type_categories}

        for element in elements:
            if not element.visible:
                continue
            if not element.selected:
                continue

            category = self.categorize_type(element.type)

            counts[category] = (
                counts.get(
                    category,
                    0,
                )
                + 1
            )

        return counts

    def build_category_minutes(
        self,
        category_counts: dict[str, int],
        mode: str,
        thread_count: int,
    ) -> dict[str, int]:
        minutes_by_category: dict[str, int] = {}

        clean_thread_count = max(
            int(thread_count),
            1,
        )

        for category, count in category_counts.items():
            if count <= 0:
                minutes_by_category[category] = 0
                continue

            rate = self.get_rate_per_hour_per_thread(
                category=category,
                mode=mode,
            )

            if rate <= 0:
                # Default rule:
                # if any element exists and no rate exists,
                # default to 1 minute per element.
                minutes = count
            else:
                minutes = ceil((count / rate) * 60)

            if minutes <= 0:
                minutes = 1

            minutes_by_category[category] = ceil(minutes / clean_thread_count)

        return minutes_by_category

    @staticmethod
    def format_minutes(
        total_minutes: int,
    ) -> str:
        hours = int(total_minutes) // 60
        minutes = int(total_minutes) % 60

        return f"{hours:02d}:{minutes:02d}"

    def build_estimate(
        self,
        elements: list[Element],
        mode: str,
        thread_count: int,
    ) -> dict[str, Any]:
        category_counts = self.build_category_counts(elements)

        category_minutes = self.build_category_minutes(
            category_counts=category_counts,
            mode=mode,
            thread_count=thread_count,
        )

        total_minutes = sum(category_minutes.values())

        selected_elements = sum(
            1 for element in elements if element.visible and element.selected
        )

        return {
            "selected_elements": selected_elements,
            "category_counts": category_counts,
            "category_minutes": category_minutes,
            "total_minutes": total_minutes,
            "estimated_time": self.format_minutes(total_minutes),
            "thread_count": max(
                int(thread_count),
                1,
            ),
        }

    def build_statistics(
        self,
        elements: list[Element],
        inventory_issues: list[Any],
        selected_effort_count: int,
        mode: str,
        thread_count: int,
    ) -> dict[str, Any]:
        estimate = self.build_estimate(
            elements=elements,
            mode=mode,
            thread_count=thread_count,
        )

        issue_count = sum(
            1
            for element in elements
            if element.visible
            and element.severity
            in {
                Severity.WARNING,
                Severity.ERROR,
            }
        ) + len(inventory_issues)

        return {
            "efforts": selected_effort_count,
            "available_elements": sum(1 for element in elements if element.visible),
            "selected_elements": estimate.get(
                "selected_elements",
                0,
            ),
            "issues": issue_count,
            "estimated_time": estimate.get(
                "estimated_time",
                "00:00",
            ),
            "thread_count": estimate.get(
                "thread_count",
                thread_count,
            ),
            "category_counts": estimate.get(
                "category_counts",
                {},
            ),
            "category_minutes": estimate.get(
                "category_minutes",
                {},
            ),
        }
