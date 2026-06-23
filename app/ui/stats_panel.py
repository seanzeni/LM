from __future__ import annotations

"""
Purpose:
    Display dashboard statistic cards.

Used By:
    MainWindow

Responsibilities:
    - Show effort count.
    - Show available element count.
    - Show selected element count.
    - Show issue count.
    - Show estimated time.
    - Color only the card value, not the full card.

Notes:
    This panel should only display values given to it.
    It should not calculate statistics.
"""

from typing import Any

import customtkinter as ctk


class StatsPanel(ctk.CTkFrame):
    CARD_ORDER = [
        "efforts",
        "available_elements",
        "selected_elements",
        "issues",
        "estimated_time",
    ]

    CARD_LABELS = {
        "efforts": "Efforts",
        "available_elements": "Available Elements",
        "selected_elements": "Selected",
        "issues": "Issues",
        "estimated_time": "Estimate",
    }

    def __init__(
        self,
        parent: ctk.CTk,
        theme_manager,
    ) -> None:
        super().__init__(
            parent,
            corner_radius=10,
        )

        self.theme_manager = theme_manager
        self.value_labels: dict[str, ctk.CTkLabel] = {}

        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
        for column, key in enumerate(self.CARD_ORDER):
            self.grid_columnconfigure(
                column,
                weight=1,
            )

            card = ctk.CTkFrame(
                self,
                corner_radius=10,
                fg_color=self.theme_manager.card_color,
            )
            card.grid(
                row=0,
                column=column,
                sticky="ew",
                padx=6,
                pady=8,
            )

            ctk.CTkLabel(
                card,
                text=self.CARD_LABELS.get(
                    key,
                    key,
                ),
                font=ctk.CTkFont(
                    size=11,
                ),
            ).pack(
                pady=(8, 0),
            )

            value_label = ctk.CTkLabel(
                card,
                text="0",
                font=ctk.CTkFont(
                    size=20,
                    weight="bold",
                ),
            )
            value_label.pack(
                pady=(2, 8),
            )

            self.value_labels[key] = value_label

    def update_theme(
        self,
    ) -> None:
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                child.configure(
                    fg_color=self.theme_manager.card_color,
                )

    def update_statistics(
        self,
        statistics: dict[str, Any],
    ) -> None:
        self.value_labels["efforts"].configure(
            text=str(
                statistics.get(
                    "efforts",
                    0,
                )
            )
        )

        self.value_labels["available_elements"].configure(
            text=str(
                statistics.get(
                    "available_elements",
                    0,
                )
            )
        )

        self.value_labels["selected_elements"].configure(
            text=str(
                statistics.get(
                    "selected_elements",
                    0,
                )
            )
        )

        issue_count = int(
            statistics.get(
                "issues",
                0,
            )
        )

        self.value_labels["issues"].configure(
            text=str(issue_count),
            text_color=self._issue_color(
                issue_count,
            ),
        )

        self.value_labels["estimated_time"].configure(
            text=str(
                statistics.get(
                    "estimated_time",
                    "00:00",
                )
            ),
            text_color=self.theme_manager.accent_color,
        )

    def _issue_color(
        self,
        issue_count: int,
    ) -> str:
        if issue_count <= 0:
            return self.theme_manager.success_color

        if issue_count <= 10:
            return self.theme_manager.warning_color

        return self.theme_manager.error_color
