from __future__ import annotations

"""
Purpose:
    Bottom data-source status bar.

Used By:
    MainWindow

Responsibilities:
    - Show Excel / SQL / NDVR load status.
    - Show last refresh time.
    - Support clickable source details.
    - Support hover text through simple detail dialogs.

Notes:
    Counts are intentionally not displayed on the bar to keep the UI clean.
"""

from dataclasses import dataclass
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk


@dataclass(slots=True)
class SourceStatus:
    name: str
    status: str = "not_loaded"
    detail: str = ""
    last_refresh: datetime | None = None


class StatusBar(ctk.CTkFrame):
    STATUS_COLORS = {
        "not_loaded": "#888888",
        "loading": "#4A90E2",
        "loaded": "#2E8B57",
        "partial": "#C98A00",
        "failed": "#C94B4B",
    }

    def __init__(
        self,
        parent: ctk.CTk,
        theme_manager,
    ) -> None:
        super().__init__(
            parent,
            corner_radius=0,
            fg_color=theme_manager.get_color(
                dark_key="status_bar_dark",
                light_key="status_bar_light",
                default_dark="#202020",
                default_light="#F7F7F7",
            ),
        )

        self.theme_manager = theme_manager

        self.sources: dict[str, SourceStatus] = {
            "Excel": SourceStatus(name="Excel"),
            "SQL": SourceStatus(name="SQL"),
            "NDVR": SourceStatus(name="NDVR"),
        }

        self.source_labels: dict[str, ctk.CTkLabel] = {}
        self.last_refresh_label: ctk.CTkLabel

        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
        self.grid_columnconfigure(3, weight=1)

        for column, source_name in enumerate(["Excel", "SQL", "NDVR"]):
            label = ctk.CTkLabel(
                self,
                text=f"● {source_name}",
                cursor="hand2",
            )
            label.grid(
                row=0,
                column=column,
                padx=(12, 4),
                pady=4,
                sticky="w",
            )
            label.bind(
                "<Button-1>",
                lambda _event, name=source_name: self.show_source_details(name),
            )

            self.source_labels[source_name] = label

        self.last_refresh_label = ctk.CTkLabel(
            self,
            text="Last Refresh: —",
        )
        self.last_refresh_label.grid(
            row=0,
            column=4,
            padx=12,
            pady=4,
            sticky="e",
        )

        self.refresh_display()

    def set_source_status(
        self,
        source_name: str,
        status: str,
        detail: str = "",
    ) -> None:
        source = self.sources.get(source_name)

        if source is None:
            return

        source.status = status
        source.detail = detail
        source.last_refresh = datetime.now()

        self.refresh_display()

    def set_last_refresh_now(
        self,
    ) -> None:
        self.last_refresh_label.configure(
            text=f"Last Refresh: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

    def refresh_display(
        self,
    ) -> None:
        latest_refresh: datetime | None = None

        for source_name, source in self.sources.items():
            label = self.source_labels.get(source_name)

            if label is None:
                continue

            color = self.STATUS_COLORS.get(
                source.status,
                self.STATUS_COLORS["not_loaded"],
            )

            label.configure(
                text=f"● {source_name}",
                text_color=color,
            )

            if source.last_refresh is not None:
                if latest_refresh is None or source.last_refresh > latest_refresh:
                    latest_refresh = source.last_refresh

        if latest_refresh is None:
            self.last_refresh_label.configure(text="Last Refresh: —")
        else:
            self.last_refresh_label.configure(
                text=f"Last Refresh: {latest_refresh.strftime('%Y-%m-%d %H:%M')}"
            )

    def show_source_details(
        self,
        source_name: str,
    ) -> None:
        source = self.sources.get(source_name)

        if source is None:
            return

        refreshed = (
            source.last_refresh.strftime("%Y-%m-%d %H:%M:%S")
            if source.last_refresh is not None
            else "Never"
        )

        detail = source.detail or "No details available."

        messagebox.showinfo(
            f"{source_name} Source",
            (
                f"Source: {source.name}\n"
                f"Status: {source.status.replace('_', ' ').title()}\n"
                f"Last Refresh: {refreshed}\n\n"
                f"{detail}"
            ),
        )
