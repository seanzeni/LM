from __future__ import annotations

"""
Purpose:
    Build and hold application-wide services and settings.

Used By:
    main.py
    MainWindow

Notes:
    MainWindow should create UI widgets only.
    AppContext owns service creation.
"""

from pathlib import Path

from app.config.settings_loader import SettingsLoader
from app.core.app_state import AppState
from app.reports.report_registry import ReportRegistry
from app.services.data_loader import DataLoader
from app.services.db_service import DBService
from app.services.element_service import ElementService
from app.services.exporter import Exporter
from app.services.mainframe_location_service import MainframeLocationService
from app.services.stats_service import StatsService
from app.services.status_marker_service import StatusMarkerService
from app.services.validation_service import ValidationService
from app.ui.theme_manager import ThemeManager


class AppContext:
    def __init__(self, base_dir: str | Path, settings_path: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.settings_path = Path(settings_path)

        self.settings = SettingsLoader(
            self.settings_path,
        ).load()

        input_path = self.resolve_path(self.settings["files"]["default_input_file"])

        if not input_path.exists():
            selected_file = self.prompt_for_file(
                title="Select Inventory Spreadsheet",
                filetypes=[
                    ("Excel Files", "*.xlsx *.xls"),
                    ("All Files", "*.*"),
                ],
            )

            if selected_file is None:
                raise FileNotFoundError("No inventory spreadsheet was selected.")

            input_path = selected_file

            self.save_file_setting_if_needed(
                key="default_input_file",
                value=input_path,
            )

        if not default_input.exists():
            default_input = self.prompt_for_inventory_file()

        self.input_file = Path(default_input)

        self.state = AppState(
            current_xls_path=self.resolve_path(
                self.settings["files"]["default_input_file"]
            ),
            current_ndvr_path=self.resolve_path(
                self.settings["files"]["default_ndvr_file"]
            ),
        )

        self.ui_settings = self.settings["ui"]
        self.workload_settings = self.settings["workload"]
        self.selection_rules = self.settings["selection_rules"]
        self.archive_pairs = self.settings["type_archive_pairs"]
        self.status_markers = self.settings["status_markers"]
        self.db_settings = self.settings["database"]
        self.required_columns = self.settings["required_columns"]

        self.theme_manager = ThemeManager(
            ui_settings=self.ui_settings,
        )

        self.data_loader = DataLoader(
            file_path=self.input_file,
            required_columns=self.required_columns,
        )
        self.data_loader.load()

        self.db_service = DBService(
            db_settings=self.db_settings,
        )

        self.element_service = ElementService()

        self.status_marker_service = StatusMarkerService(
            status_markers=self.status_markers,
        )

        self.validation_service = ValidationService(
            selection_rules=self.selection_rules,
            archive_pairs=self.archive_pairs,
            status_marker_service=self.status_marker_service,
        )

        self.stats_service = StatsService(
            workload_settings=self.workload_settings,
        )

        self.exporter = Exporter(
            settings=self.settings,
            base_dir=self.base_dir,
        )

        self.report_registry = ReportRegistry(
            stats_service=self.stats_service,
        )

        self.location_service: MainframeLocationService | None = None

    def load_location_file(
        self,
        file_path: str | Path,
    ) -> MainframeLocationService:
        path = Path(file_path)

        service = MainframeLocationService()
        service.load_file(path)

        self.location_service = service
        self.state.current_ndvr_path = path

        self.save_file_setting_if_needed(
            key="default_ndvr_file",
            value=path,
        )

        return service

    def resolve_path(
        self,
        file_path: str | Path,
    ) -> Path:
        path = Path(file_path)

        if path.is_absolute():
            return path

        return self.base_dir / path

    def prompt_for_file(
        self,
        title: str,
        filetypes: list[tuple[str, str]],
    ) -> Path | None:
        from tkinter import filedialog

        selected = filedialog.askopenfilename(
            title=title,
            filetypes=filetypes,
        )

        if not selected:
            return None

        return Path(selected)

    def save_file_setting_if_needed(
        self,
        key: str,
        value: Path,
    ) -> None:
        if not self.settings.get("files", {}).get("remember_last_used_files", True):
            return

        current_value = str(
            self.settings["files"].get(
                key,
                "",
            )
        )

        new_value = str(value)

        if current_value == new_value:
            return

        self.settings["files"][key] = new_value

        SettingsLoader.save(
            settings_path=self.settings_path,
            settings=self.settings,
        )
