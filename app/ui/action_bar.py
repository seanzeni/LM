from __future__ import annotations

"""
Purpose:
    Bottom action button bar.

Used By:
    MainWindow

Responsibilities:
    - Provide primary application actions.
    - Keep bottom button layout consistent.
"""

from typing import Callable

import customtkinter as ctk


class ActionBar(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        on_generate: Callable[[], None],
        on_select_all: Callable[[], None],
        on_clear_all: Callable[[], None],
        on_refresh: Callable[[], None],
        on_reports: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        super().__init__(
            parent,
            corner_radius=10,
        )

        inner = ctk.CTkFrame(
            self,
            fg_color="transparent",
        )
        inner.pack(
            anchor="center",
            pady=8,
        )

        buttons = [
            ("Generate", on_generate),
            ("Select All", on_select_all),
            ("Clear All", on_clear_all),
            ("Refresh", on_refresh),
            ("Reports", on_reports),
            ("Exit", on_exit),
        ]

        for text, command in buttons:
            ctk.CTkButton(
                inner,
                text=text,
                command=command,
                width=115,
            ).pack(
                side="left",
                padx=6,
            )
