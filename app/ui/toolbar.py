from __future__ import annotations

"""
Purpose:
    Top toolbar for release, mode, threads, appearance, and search.

Used By:
    MainWindow

Responsibilities:
    - Let user choose release.
    - Let user choose PROD/QUAL mode.
    - Let user adjust thread count.
    - Let user change appearance mode.
    - Let user type element/type/project search text.

Notes:
    Search is display-only.
    Search should not affect exports, reports, or statistics.
"""

from typing import Callable

import customtkinter as ctk


class Toolbar(ctk.CTkFrame):
    def __init__(
        self,
        parent: ctk.CTk,
        releases: list[str],
        min_threads: int,
        max_threads: int,
        default_thread_count: int,
        appearance_values: tuple[str, ...],
        current_appearance: str,
        on_release_changed: Callable[[str], None],
        on_mode_changed: Callable[[str], None],
        on_thread_changed: Callable[[int], None],
        on_appearance_changed: Callable[[str], None],
        on_search_changed: Callable[[str], None],
    ) -> None:
        super().__init__(
            parent,
            corner_radius=10,
        )

        self.min_threads = min_threads
        self.max_threads = max_threads

        self.on_release_changed = on_release_changed
        self.on_mode_changed = on_mode_changed
        self.on_thread_changed = on_thread_changed
        self.on_appearance_changed = on_appearance_changed
        self.on_search_changed = on_search_changed

        self.release_var = ctk.StringVar(value=releases[0] if releases else "")
        self.mode_var = ctk.StringVar(value="PROD")
        self.thread_var = ctk.StringVar(value=str(default_thread_count))
        self.appearance_var = ctk.StringVar(value=current_appearance)
        self.search_var = ctk.StringVar(value="")

        self._build_ui(
            releases=releases,
            appearance_values=appearance_values,
        )

    def _build_ui(
        self,
        releases: list[str],
        appearance_values: tuple[str, ...],
    ) -> None:
        self.grid_columnconfigure(10, weight=1)

        ctk.CTkLabel(
            self,
            text="Release",
        ).grid(row=0, column=0, padx=(12, 4), pady=10)

        self.release_menu = ctk.CTkOptionMenu(
            self,
            values=releases or [""],
            variable=self.release_var,
            command=self._release_changed,
            width=160,
        )
        self.release_menu.grid(row=0, column=1, padx=(0, 12), pady=10)

        ctk.CTkLabel(
            self,
            text="Mode",
        ).grid(row=0, column=2, padx=(0, 4), pady=10)

        self.mode_menu = ctk.CTkOptionMenu(
            self,
            values=["PROD", "QUAL"],
            variable=self.mode_var,
            command=self._mode_changed,
            width=90,
        )
        self.mode_menu.grid(row=0, column=3, padx=(0, 12), pady=10)

        ctk.CTkLabel(
            self,
            text="Threads",
        ).grid(row=0, column=4, padx=(0, 4), pady=10)

        ctk.CTkButton(
            self,
            text="-",
            width=32,
            command=self.decrease_thread,
        ).grid(row=0, column=5, padx=(0, 2), pady=10)

        self.thread_entry = ctk.CTkEntry(
            self,
            textvariable=self.thread_var,
            width=48,
            justify="center",
        )
        self.thread_entry.grid(row=0, column=6, padx=2, pady=10)
        self.thread_entry.bind(
            "<Return>",
            lambda _event: self._thread_changed(),
        )
        self.thread_entry.bind(
            "<FocusOut>",
            lambda _event: self._thread_changed(),
        )

        ctk.CTkButton(
            self,
            text="+",
            width=32,
            command=self.increase_thread,
        ).grid(row=0, column=7, padx=(2, 12), pady=10)

        ctk.CTkLabel(
            self,
            text="Appearance",
        ).grid(row=0, column=8, padx=(0, 4), pady=10)

        self.appearance_menu = ctk.CTkOptionMenu(
            self,
            values=list(appearance_values),
            variable=self.appearance_var,
            command=self._appearance_changed,
            width=110,
        )
        self.appearance_menu.grid(row=0, column=9, padx=(0, 12), pady=10)

        ctk.CTkLabel(
            self,
            text="Search",
        ).grid(row=0, column=10, padx=(0, 4), pady=10, sticky="e")

        self.search_entry = ctk.CTkEntry(
            self,
            textvariable=self.search_var,
            placeholder_text="Element, Type, or Project",
            width=260,
        )
        self.search_entry.grid(row=0, column=11, padx=(0, 12), pady=10, sticky="e")

        self.search_var.trace_add(
            "write",
            lambda *_args: self.on_search_changed(self.search_var.get()),
        )

    def set_releases(
        self,
        releases: list[str],
    ) -> None:
        self.release_menu.configure(
            values=releases or [""],
        )

        if releases:
            self.release_var.set(
                releases[0],
            )
        else:
            self.release_var.set("")

    def get_release(
        self,
    ) -> str:
        return self.release_var.get().strip()

    def get_mode(
        self,
    ) -> str:
        return self.mode_var.get().strip().upper()

    def get_thread_count(
        self,
    ) -> int:
        try:
            thread_count = int(
                self.thread_var.get(),
            )
        except ValueError:
            thread_count = self.min_threads

        if thread_count < self.min_threads:
            thread_count = self.min_threads

        if thread_count > self.max_threads:
            thread_count = self.max_threads

        self.thread_var.set(
            str(thread_count),
        )

        return thread_count

    def decrease_thread(
        self,
    ) -> None:
        self.thread_var.set(
            str(self.get_thread_count() - 1),
        )
        self._thread_changed()

    def increase_thread(
        self,
    ) -> None:
        self.thread_var.set(
            str(self.get_thread_count() + 1),
        )
        self._thread_changed()

    def _release_changed(
        self,
        value: str,
    ) -> None:
        self.on_release_changed(
            value,
        )

    def _mode_changed(
        self,
        value: str,
    ) -> None:
        self.on_mode_changed(
            value,
        )

    def _thread_changed(
        self,
    ) -> None:
        self.on_thread_changed(
            self.get_thread_count(),
        )

    def _appearance_changed(
        self,
        value: str,
    ) -> None:
        self.on_appearance_changed(
            value,
        )
