from __future__ import annotations

"""
Purpose:
    Manage application appearance and theme colors.

Used By:
    MainWindow
    Toolbar
    StatsPanel
    ReleaseTree
    ElementTable
    ReportDialog
    StatusBar

Responsibilities:
    - Apply Light/Dark/System appearance mode.
    - Store the active theme choice in UI settings.
    - Provide theme-aware colors.
    - Notify registered UI widgets when appearance changes.

Notes:
    UI widgets should request colors from ThemeManager instead of
    hardcoding theme-specific colors.
"""

import customtkinter as ctk


class ThemeManager:
    THEMES = (
        "System",
        "Light",
        "Dark",
    )

    def __init__(
        self,
        ui_settings: dict,
    ) -> None:
        self.ui_settings = ui_settings
        self._listeners: list = []

        self.current_theme = str(
            self.ui_settings.get(
                "appearance_mode",
                "System",
            )
        )

        self.apply_theme(
            self.current_theme,
        )

    def register(
        self,
        callback,
    ) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def apply_theme(
        self,
        theme: str,
    ) -> None:
        if theme not in self.THEMES:
            theme = "System"

        self.current_theme = theme
        self.ui_settings["appearance_mode"] = theme

        ctk.set_appearance_mode(theme)

        for listener in self._listeners:
            listener()

    def is_dark_mode(
        self,
    ) -> bool:
        return self.current_theme == "Dark"

    def get_color(
        self,
        dark_key: str,
        light_key: str,
        default_dark: str,
        default_light: str,
    ) -> str:
        if self.is_dark_mode():
            return str(
                self.ui_settings.get(
                    dark_key,
                    default_dark,
                )
            )

        return str(
            self.ui_settings.get(
                light_key,
                default_light,
            )
        )

    @property
    def accent_color(
        self,
    ) -> str:
        return str(
            self.ui_settings.get(
                "accent_color",
                "#3B8ED0",
            )
        )

    @property
    def success_color(
        self,
    ) -> str:
        return str(
            self.ui_settings.get(
                "success_color",
                "#2E8B57",
            )
        )

    @property
    def warning_color(
        self,
    ) -> str:
        return str(
            self.ui_settings.get(
                "warning_color",
                "#C98A00",
            )
        )

    @property
    def error_color(
        self,
    ) -> str:
        return str(
            self.ui_settings.get(
                "error_color",
                "#C94B4B",
            )
        )

    @property
    def card_color(
        self,
    ) -> str:
        return self.get_color(
            dark_key="card_color_dark",
            light_key="card_color_light",
            default_dark="#2B2B2B",
            default_light="#F2F2F2",
        )

    @property
    def tree_background(
        self,
    ) -> str:
        return self.get_color(
            dark_key="tree_background_dark",
            light_key="tree_background_light",
            default_dark="#1F1F1F",
            default_light="#FFFFFF",
        )

    @property
    def table_background(
        self,
    ) -> str:
        return self.get_color(
            dark_key="table_background_dark",
            light_key="table_background_light",
            default_dark="#1F1F1F",
            default_light="#FFFFFF",
        )
