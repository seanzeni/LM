from __future__ import annotations

"""
Purpose:
    Load and validate settings.json

Used By:
    main.py

Responsibilities:
    - Confirm settings.json exists.
    - Read JSON settings.
    - Validate required top-level sections exist.
    
Notes:
    This file should not apply business rules.
    This file should not calculate workload.
    This file should not connect to SQL.
"""

import json
from pathlib import Path
from typing import Any

from app.core.validators import validate_required_settings


class SettingsLoader:
    REQUIRED_SECTIONS: set[str] = {
        "database",
        "files",
        "reports",
        "workload",
        "selection_rules",
        "required_columns",
        "ui",
        "type_archive_pairs",
        "status_markers",
    }

    REQUIRED_FILES = ("default_input_file", "default_ndvr_file")

    REQUIRED_UI = (
        "window_title",
        "window_width",
        "window_height",
        "min_threads",
        "max_threads",
        "appearance_mode",
        "color_theme",
    )

    REQUIRED_WORKLOAD = (
        "default_thread_count",
        "type_categories",
        "types_per_hour_per_thread",
    )

    def __init__(
        self,
        settings_path: str | Path,
    ) -> None:
        self.settings_path: Path = Path(settings_path)

    def load(
        self,
    ) -> dict[str, Any]:
        if not self.settings_path.exists():
            raise FileNotFoundError(f"Settings file not found: {self.settings_path}.")

        with self.settings_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            settings: dict[str, Any] = json.load(file)

        validate_required_settings(
            settings=settings, required_sections=self.REQUIRED_SECTIONS
        )
        validate_required_settings(
            settings=settings["files"],
            required_sections=self.REQUIRED_FILES,
            location="settings.files",
        )
        validate_required_settings(
            settings=settings["ui"],
            required_sections=self.REQUIRED_UI,
            location="settings.ui",
        )
        validate_required_settings(
            settings=settings["workload"],
            required_sections=self.REQUIRED_WORKLOAD,
            location="settings.workload",
        )

        return settings

    @staticmethod
    def save(
        settings_path: str | Path,
        settings: dict[str, Any],
    ) -> None:
        """
        Save settings.json using pretty formatting.
        """

        path = Path(settings_path)

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                settings,
                file,
                indent=4,
                sort_keys=False,
            )

    @staticmethod
    def update_value(
        settings_path: str | Path,
        settings: dict[str, Any],
        section: str,
        key: str,
        value: Any,
    ) -> None:
        """
        Update a single value and immediately save the file.
        """

        if section not in settings:
            settings[section] = {}

        settings[section][key] = value

        SettingsLoader.save(
            settings_path=settings_path,
            settings=settings,
        )
