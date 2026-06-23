from __future__ import annotations
import json
from pathlib import Path
import pytest
from app.config.settings_loader import SettingsLoader


def make_settings() -> dict:
    return {
        "database": {
            "server": "localhost",
        },
        "files": {
            "default_input_file": "inventory.xlsx",
        },
        "required_columns": [
            "Release",
            "Project",
            "Element",
            "Type",
        ],
        "selection_rules": {},
        "status_markers": {},
        "type_archive_pairs": [],
        "reports": {},
        "ui": {
            "window_title": "Mainframe Export Tool",
            "window_width": 1600,
            "window_height": 900,
            "min_threads": 1,
            "max_threads": 20,
            "appearance_mode": "System",
            "color_theme": "blue",
        },
        "workload": {
            "default_thread_count": 4,
            "type_categories": {},
            "types_per_hour_per_thread": {},
        },
    }


def test_load_settings(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(make_settings()), encoding="utf-8")
    assert "database" in SettingsLoader(path).load()


def test_missing_settings_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        SettingsLoader(tmp_path / "missing.json").load()


def test_missing_required_section_raises(tmp_path: Path) -> None:
    settings = make_settings()
    settings.pop("database")
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(settings), encoding="utf-8")
    with pytest.raises(Exception):
        SettingsLoader(path).load()


def test_missing_nested_ui_key_raises(tmp_path: Path) -> None:
    settings = make_settings()
    settings["ui"].pop("window_width")

    path = tmp_path / "settings.json"
    path.write_text(json.dumps(settings), encoding="utf-8")

    with pytest.raises(Exception) as exc:
        SettingsLoader(path).load()

    assert "settings.ui" in str(exc.value)
    assert "window_width" in str(exc.value)


def test_missing_nested_workload_key_raises(tmp_path: Path) -> None:
    settings = make_settings()
    settings["workload"].pop("types_per_hour_per_thread")

    path = tmp_path / "settings.json"
    path.write_text(json.dumps(settings), encoding="utf-8")

    with pytest.raises(Exception) as exc:
        SettingsLoader(path).load()

    assert "settings.workload" in str(exc.value)
    assert "types_per_hour_per_thread" in str(exc.value)


def test_save_settings(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    settings = make_settings()

    SettingsLoader.save(path, settings)

    loaded = json.loads(path.read_text(encoding="utf-8"))

    assert (
        loaded["files"]["default_input_file"] == settings["files"]["default_input_file"]
    )
