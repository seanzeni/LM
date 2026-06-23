from __future__ import annotations

"""
Purpose:
    Display release efforts in a selectable tree.

Used By:
    MainWindow

Responsibilities:
    - Display efforts grouped by move date.
    - Separate Active and Withdrawn efforts.
    - Support multi-select efforts.
    - Notify MainWindow when effort selection changes.

Notes:
    This file should not query SQL.
    This file should not filter elements.
    This file should not calculate statistics.
"""

from collections import defaultdict
from typing import Callable

import customtkinter as ctk
from tkinter import ttk

from app.core.models import ReleaseEffort


class ReleaseTree(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        on_selection_changed: Callable[[set[str]], None],
    ) -> None:
        super().__init__(
            parent,
            corner_radius=8,
        )

        self.on_selection_changed = on_selection_changed
        self.effort_lookup: dict[str, str] = {}

        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Release Efforts",
            font=ctk.CTkFont(
                size=14,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=8,
            pady=(8, 4),
        )

        self.tree = ttk.Treeview(
            self,
            show="tree",
            selectmode="extended",
        )

        self.tree.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=8,
            pady=(0, 8),
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._selection_changed,
        )

    def load_efforts(
        self,
        release_efforts: list[ReleaseEffort],
        effort_dates: dict[str, str],
        inventory_effort_ids: set[str],
        inventory_not_in_sql_ids: set[str],
    ) -> None:
        self.tree.delete(
            *self.tree.get_children(),
        )
        self.effort_lookup.clear()

        grouped: dict[str, dict[str, list[ReleaseEffort]]] = defaultdict(
            lambda: {
                "Active": [],
                "Withdrawn": [],
            }
        )

        for effort in release_efforts:
            move_date = effort_dates.get(
                effort.effort_id,
                "Unknown",
            )

            bucket = "Withdrawn" if effort.withdrawn else "Active"

            grouped[move_date][bucket].append(effort)

        for move_date in sorted(grouped.keys()):
            date_node = self.tree.insert(
                "",
                "end",
                text=move_date,
                open=True,
            )

            active_node = self.tree.insert(
                date_node,
                "end",
                text="Active",
                open=True,
            )

            withdrawn_node = self.tree.insert(
                date_node,
                "end",
                text="Withdrawn",
                open=False,
            )

            for effort in sorted(
                grouped[move_date]["Active"],
                key=lambda item: item.effort_id.upper(),
            ):
                self._insert_effort(
                    parent=active_node,
                    effort=effort,
                    inventory_effort_ids=inventory_effort_ids,
                )

            for effort in sorted(
                grouped[move_date]["Withdrawn"],
                key=lambda item: item.effort_id.upper(),
            ):
                self._insert_effort(
                    parent=withdrawn_node,
                    effort=effort,
                    inventory_effort_ids=inventory_effort_ids,
                )

        if inventory_not_in_sql_ids:
            extra_node = self.tree.insert(
                "",
                "end",
                text="Inventory Not In SQL",
                open=True,
            )

            for effort_id in sorted(inventory_not_in_sql_ids):
                self._insert_extra_effort(
                    parent=extra_node,
                    effort_id=effort_id,
                    status_text="missing",
                )

    def _insert_effort(
        self,
        parent: str,
        effort: ReleaseEffort,
        inventory_effort_ids: set[str],
    ) -> None:
        effort_id = effort.effort_id.strip()

        if not effort_id:
            return

        item_id = f"effort::{effort_id}"
        self.effort_lookup[item_id] = effort_id

        effort_node = self.tree.insert(
            parent,
            "end",
            iid=item_id,
            text=effort_id,
            open=False,
        )

        if effort.no_inventory:
            self.tree.insert(
                effort_node,
                "end",
                text="NOINV",
            )
            return

        if effort_id not in inventory_effort_ids:
            self.tree.insert(
                effort_node,
                "end",
                text="missing",
            )

    def _insert_extra_effort(
        self,
        parent: str,
        effort_id: str,
        status_text: str,
    ) -> None:
        item_id = f"extra::{effort_id}"
        self.effort_lookup[item_id] = effort_id

        effort_node = self.tree.insert(
            parent,
            "end",
            iid=item_id,
            text=effort_id,
            open=False,
        )

        self.tree.insert(
            effort_node,
            "end",
            text=status_text,
        )

    def get_selected_efforts(
        self,
    ) -> set[str]:
        selected_efforts: set[str] = set()

        for item_id in self.tree.selection():
            effort_id = self.effort_lookup.get(
                item_id,
            )

            if effort_id:
                selected_efforts.add(
                    effort_id,
                )

        return selected_efforts

    def select_first_available(
        self,
    ) -> None:
        for item_id in self.effort_lookup:
            self.tree.selection_set(
                item_id,
            )
            self.on_selection_changed(
                self.get_selected_efforts(),
            )
            return

    def _selection_changed(
        self,
        _event,
    ) -> None:
        self.on_selection_changed(
            self.get_selected_efforts(),
        )
