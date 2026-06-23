from __future__ import annotations

"""
Purpose:
    Load inventory spreadsheet data into memory.

Used By:
    MainWindow
    ElementService
    Reports

Responsibilities:
    - Read the Excel file.
    - Validate required columns.
    - Normalize column names.
    - Provide release/project filtering helpers.

Notes:
    This file should nto validate business rules.
    This file should not query SQL.
    This file should not calculate estimates.
"""

from pathlib import Path

import pandas as pd

from app.core.validators import validate_required_columns


class DataLoader:
    def __init__(
        self,
        file_path: str | Path,
        required_columns: list[str],
    ) -> None:
        self.file_path: Path = Path(file_path)
        self.required_columns: list[str] = required_columns
        self.df: pd.DataFrame | None = None

    def load(self) -> pd.DataFrame:
        df = pd.read_excel(self.file_path)
        df.columns = [str(column).strip() for column in df.columns]
        validate_required_columns(
            actual_columns=list(df.columns),
            required_columns=self.required_columns,
        )

        for column in df.columns:
            df[column] = df[column].apply(
                lambda value: value.strip() if isinstance(value, str) else value
            )

        self.df = df

        return df

    def reload(
        self,
    ) -> pd.DataFrame:
        return self.load()

    def _require_loaded(
        self,
    ) -> pd.DataFrame:
        if self.df is None:
            raise RuntimeError("Inventory file has not been loaded.")
        return self.df

    def get_releases(
        self,
    ) -> list[str]:
        df = self._require_loaded()
        return sorted(
            {str(value).strip() for value in df["Release"] if str(value).strip()}
        )

    def filter_release(
        self,
        release: str,
    ) -> pd.DataFrame:
        df = self._require_loaded()

        clean_release = str(release).strip()

        return df[df["Release"].astype(str).str.strip() == clean_release].copy()

    def filter_release_projects(
        self,
        release: str,
        projects: set[str],
    ) -> pd.DataFrame:
        df = self._require_loaded()
        clean_release = str(release).strip()

        clean_projects = {str(project).strip() for project in projects}

        return df[
            (df["Release"].astype(str).str.strip() == clean_release)
            & (df["Project"].astype(str).str.strip().isin(clean_projects))
        ].copy()

    def get_projects_for_release(
        self,
        release: str,
    ) -> set[str]:
        df = self.filter_release(release)

        return {str(value).strip() for value in df["Project"] if str(value).strip()}

    def get_inventory_release_lookup(
        self,
    ) -> dict[str, set[str]]:
        """
        Return:
            effort/project -> set of releases found in spreadsheet

        Used for wrong-release validation
        """
        df = self._require_loaded()

        lookup: dict[str, set[str]] = {}

        for _, row in df.iterrows():
            project = str(row.get("Project", "")).strip()
            release = str(row.get("Release", "")).strip()

            if not project or not release:
                continue

            lookup.setdefault(
                project,
                set(),
            ).add(release)

        return lookup
