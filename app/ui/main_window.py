from __future__ import annotations

"""
Purpose:
    Main application window and UI coordinator.

Used By:
    main.py

Responsibilities:
    - Build the main UI layout.
    - Wire toolbar, tree, table, stats, reports, and status bar.
    - Coordinate service calls.
    - Refresh UI after release/mode/thread/selection changes.

Notes:
    Keep business rules in ValidationService.
    Keep report content in report classes.
"""

from pathlib import Path
from tkinter import filedialog
from tkinter import messagebox
from tkinter import simpledialog

import customtkinter as ctk

from app.core.app_context import AppContext
from app.core.app_state import AppState
from app.services.mainframe_location_service import MainframeLocationService
from app.ui.action_bar import ActionBar
from app.ui.element_table import ElementTable
from app.ui.release_tree import ReleaseTree
from app.ui.report_center import ReportCenter
from app.ui.stats_panel import StatsPanel
from app.ui.status_bar import StatusBar
from app.ui.toolbar import Toolbar


class MainWindow(ctk.CTk):
    def __init__(
        self,
        context: AppContext,
    ) -> None:
        super().__init__()

        self.context = context
        self.state: AppState = context.state

        self.title(
            str(
                context.ui_settings.get(
                    "window_title",
                    "Mainframe Export Tool",
                )
            )
        )

        width = int(
            context.ui_settings.get(
                "window_width",
                1600,
            )
        )
        height = int(
            context.ui_settings.get(
                "window_height",
                950,
            )
        )

        self.geometry(f"{width}x{height}")
        self.minsize(1200, 750)

        self._build_ui()
        self._initialize_status_bar()
        self._load_initial_releases()

    def _build_ui(
        self,
    ) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.toolbar = Toolbar(
            parent=self,
            releases=[],
            min_threads=int(self.context.ui_settings.get("min_threads", 1)),
            max_threads=int(self.context.ui_settings.get("max_threads", 20)),
            default_thread_count=self.state.thread_count,
            appearance_values=self.context.theme_manager.THEMES,
            current_appearance=self.context.theme_manager.current_theme,
            on_release_changed=self.on_release_changed,
            on_mode_changed=self.on_mode_changed,
            on_thread_changed=self.on_thread_changed,
            on_appearance_changed=self.on_appearance_changed,
            on_search_changed=self.on_search_changed,
        )
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))

        self.stats_panel = StatsPanel(
            parent=self,
            theme_manager=self.context.theme_manager,
        )
        self.stats_panel.grid(row=1, column=0, sticky="ew", padx=12, pady=6)

        body = ctk.CTkFrame(self, corner_radius=10)
        body.grid(row=2, column=0, sticky="nsew", padx=12, pady=6)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        self.release_tree = ReleaseTree(
            parent=body,
            on_selection_changed=self.on_effort_selection_changed,
        )
        self.release_tree.grid(row=0, column=0, sticky="ns", padx=(8, 4), pady=8)

        self.element_table = ElementTable(
            parent=body,
            theme_manager=self.context.theme_manager,
            on_selection_changed=self.on_element_selection_changed,
        )
        self.element_table.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)

        self.action_bar = ActionBar(
            parent=self,
            on_generate=self.on_generate,
            on_select_all=self.on_select_all,
            on_clear_all=self.on_clear_all,
            on_refresh=self.on_refresh,
            on_reports=self.on_reports,
            on_exit=self.destroy,
        )
        self.action_bar.grid(row=3, column=0, sticky="ew", padx=12, pady=(6, 6))

        self.status_bar = StatusBar(
            parent=self,
            theme_manager=self.context.theme_manager,
        )
        self.status_bar.grid(row=4, column=0, sticky="ew")

        self.context.theme_manager.register(
            self.on_theme_updated,
        )

    def _initialize_status_bar(
        self,
    ) -> None:
        self.status_bar.set_source_status(
            source_name="Excel",
            status="not_loaded",
            detail="Excel file has not been loaded yet.",
        )
        self.status_bar.set_source_status(
            source_name="SQL",
            status="not_loaded",
            detail="SQL release data has not been loaded yet.",
        )
        self.status_bar.set_source_status(
            source_name="NDVR",
            status="not_loaded",
            detail="NDVR/mainframe location file has not been loaded yet.",
        )

    def _load_initial_releases(
        self,
    ) -> None:
        try:
            releases = self.context.data_loader.get_releases()
            self.toolbar.set_releases(releases)

            self.status_bar.set_source_status(
                source_name="Excel",
                status="loaded",
                detail=(
                    f"Excel loaded successfully.\n\n"
                    f"File:\n{self.state.current_xls_path}"
                ),
            )

            if releases and self.context.ui_settings.get(
                "auto_select_first_release", True
            ):
                self.on_release_changed(releases[0])

        except Exception as exc:
            self.status_bar.set_source_status(
                source_name="Excel",
                status="failed",
                detail=str(exc),
            )
            messagebox.showerror("Excel Load Error", str(exc))

    def on_release_changed(
        self,
        release: str,
    ) -> None:
        self.state.release = release
        self.state.mode = self.toolbar.get_mode()

        self.load_sql_for_release()
        self.load_release_tree()
        self.refresh_selected_elements()

    def on_mode_changed(
        self,
        mode: str,
    ) -> None:
        self.state.mode = mode
        self.load_release_tree()
        self.refresh_selected_elements()

    def on_thread_changed(
        self,
        thread_count: int,
    ) -> None:
        self.state.thread_count = thread_count
        self.refresh_statistics()

    def on_appearance_changed(
        self,
        appearance: str,
    ) -> None:
        self.context.theme_manager.apply_theme(
            appearance,
        )

    def on_theme_updated(
        self,
    ) -> None:
        self.stats_panel.update_theme()

    def on_search_changed(
        self,
        search_text: str,
    ) -> None:
        self.element_table.set_search_text(
            search_text,
        )

    def load_sql_for_release(
        self,
    ) -> None:
        if not self.state.release:
            return

        try:
            self.status_bar.set_source_status(
                source_name="SQL",
                status="loading",
                detail="Loading SQL release efforts...",
            )

            self.state.release_efforts = (
                self.context.db_service.get_efforts_for_release(
                    self.state.release,
                )
            )

            inventory_effort_ids = {
                element.project
                for element in self.context.element_service.build_elements(
                    self.context.data_loader.filter_release(self.state.release)
                )
                if element.project
            }

            self.state.inventory_effort_ids = inventory_effort_ids

            self.state.effort_release_lookup = (
                self.context.db_service.build_effort_release_lookup(
                    inventory_effort_ids,
                )
            )

            self.status_bar.set_source_status(
                source_name="SQL",
                status="loaded",
                detail=(
                    f"SQL loaded successfully.\n\n"
                    f"Release:\n{self.state.release}\n\n"
                    f"Efforts loaded:\n{len(self.state.release_efforts)}"
                ),
            )

        except Exception as exc:
            self.state.release_efforts = []
            self.state.effort_release_lookup = {}

            self.status_bar.set_source_status(
                source_name="SQL",
                status="failed",
                detail=str(exc),
            )

            messagebox.showerror("SQL Load Error", str(exc))

    def load_release_tree(
        self,
    ) -> None:
        self.state.effort_dates = self._build_effort_dates()

        sql_effort_ids = {
            effort.effort_id.strip()
            for effort in self.state.release_efforts
            if effort.effort_id.strip()
        }

        inventory_not_in_sql_ids = self.state.inventory_effort_ids - sql_effort_ids

        self.release_tree.load_efforts(
            release_efforts=self.state.release_efforts,
            effort_dates=self.state.effort_dates,
            inventory_effort_ids=self.state.inventory_effort_ids,
            inventory_not_in_sql_ids=inventory_not_in_sql_ids,
        )

        if self.context.ui_settings.get("auto_select_first_release", True):
            self.release_tree.select_first_available()

    def _build_effort_dates(
        self,
    ) -> dict[str, str]:
        dates: dict[str, str] = {}

        for effort in self.state.release_efforts:
            move_date = (
                effort.prod_date if self.state.mode == "PROD" else effort.qual_date
            )

            if move_date is None:
                dates[effort.effort_id] = "Unknown"
                continue

            if hasattr(move_date, "strftime"):
                dates[effort.effort_id] = move_date.strftime("%Y-%m-%d")
            else:
                dates[effort.effort_id] = str(move_date)[:10]

        return dates

    def on_effort_selection_changed(
        self,
        effort_ids: set[str],
    ) -> None:
        self.state.selected_effort_ids = effort_ids
        self.refresh_selected_elements()

    def refresh_selected_elements(
        self,
    ) -> None:
        if not self.state.release:
            return

        if not self.state.selected_effort_ids:
            self.state.loaded_elements = []
            self.state.inventory_issues = []
            self.element_table.load_elements([])
            self.refresh_statistics()
            return

        release_df = self.context.data_loader.filter_release_projects(
            release=self.state.release,
            projects=self.state.selected_effort_ids,
        )

        selected_elements = self.context.element_service.build_elements(
            release_df,
        )

        all_release_elements = self.context.element_service.build_elements(
            self.context.data_loader.filter_release(
                self.state.release,
            )
        )

        validated_elements, inventory_issues = (
            self.context.validation_service.validate_elements(
                elements=selected_elements,
                all_release_elements=all_release_elements,
                release_efforts=self.state.release_efforts,
                effort_release_lookup=self.state.effort_release_lookup,
                location_service=self.context.location_service,
                mode=self.state.mode,
                release=self.state.release,
            )
        )

        self.state.loaded_elements = validated_elements
        self.state.inventory_issues = inventory_issues

        self.element_table.load_elements(
            validated_elements,
        )

        self.refresh_statistics()

    def refresh_statistics(
        self,
    ) -> None:
        statistics = self.context.stats_service.build_statistics(
            elements=self.state.loaded_elements,
            inventory_issues=self.state.inventory_issues,
            selected_effort_count=len(self.state.selected_effort_ids),
            mode=self.state.mode,
            thread_count=self.state.thread_count,
        )

        self.stats_panel.update_statistics(
            statistics,
        )

    def on_element_selection_changed(
        self,
    ) -> None:
        self.refresh_statistics()

    def on_select_all(
        self,
    ) -> None:
        self.element_table.select_all()
        self.refresh_statistics()

    def on_clear_all(
        self,
    ) -> None:
        self.element_table.clear_all()
        self.refresh_statistics()

    def on_generate(
        self,
    ) -> None:
        try:
            output_path = self.context.exporter.export(
                elements=self.state.loaded_elements,
                mode=self.state.mode,
                release=self.state.release,
            )

            messagebox.showinfo(
                "Generate Complete",
                f"Export created:\n{output_path}",
            )

        except Exception as exc:
            messagebox.showerror(
                "Generate Error",
                str(exc),
            )

    def on_reports(
        self,
    ) -> None:
        ReportCenter(
            parent=self,
            report_registry=self.context.report_registry,
            app_state=self.state,
            base_output_folder=self.context.base_dir,
        )

    def on_refresh(
        self,
    ) -> None:
        choice = simpledialog.askstring(
            "Refresh",
            "Refresh SQL, Excel, NDVR, or Everything?",
            initialvalue="Everything",
        )

        if choice is None:
            return

        choice = choice.strip().upper()

        if choice not in {
            "SQL",
            "EXCEL",
            "NDVR",
            "EVERYTHING",
        }:
            messagebox.showwarning(
                "Invalid Refresh Option",
                "Enter SQL, Excel, NDVR, or Everything.",
            )
            return

        if choice in {"EXCEL", "EVERYTHING"}:
            self.refresh_excel()

        if choice in {"SQL", "EVERYTHING"}:
            self.load_sql_for_release()
            self.load_release_tree()

        if choice in {"NDVR", "EVERYTHING"}:
            self.refresh_ndvr()

        self.refresh_selected_elements()

    def refresh_excel(
        self,
    ) -> None:
        try:
            self.status_bar.set_source_status(
                source_name="Excel",
                status="loading",
                detail="Reloading Excel inventory...",
            )

            self.context.data_loader.reload()
            releases = self.context.data_loader.get_releases()
            self.toolbar.set_releases(releases)

            self.status_bar.set_source_status(
                source_name="Excel",
                status="loaded",
                detail=(
                    f"Excel refreshed successfully.\n\n"
                    f"File:\n{self.state.current_xls_path}"
                ),
            )

        except Exception as exc:
            self.status_bar.set_source_status(
                source_name="Excel",
                status="failed",
                detail=str(exc),
            )
            messagebox.showerror("Excel Refresh Error", str(exc))

    def refresh_ndvr(
        self,
    ) -> None:
        selected_file = filedialog.askopenfilename(
            title="Select NDVR/Mainframe Location File",
            filetypes=[
                ("Text Files", "*.txt *.dat *.csv"),
                ("All Files", "*.*"),
            ],
        )

        if not selected_file:
            return

        try:
            self.status_bar.set_source_status(
                source_name="NDVR",
                status="loading",
                detail="Loading NDVR/mainframe location file...",
            )

            service = self.context.load_location_file(selected_file)
            self.context.location_service = service

            self.status_bar.set_source_status(
                source_name="NDVR",
                status="loaded",
                detail=(
                    f"NDVR loaded successfully.\n\n"
                    f"File:\n{selected_file}\n\n"
                    f"Records loaded:\n{len(service.records)}"
                ),
            )

        except Exception as exc:
            self.context.location_service = None

            self.status_bar.set_source_status(
                source_name="NDVR",
                status="failed",
                detail=str(exc),
            )

            messagebox.showerror("NDVR Load Error", str(exc))
