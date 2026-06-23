from __future__ import annotations

"""
Purpose:
    Shared report helper functions.

Used By:
    All report generators.

Responsibilities:
    - Report output folder creation.
    - Safe release folder naming.
    - History folder handling.
    - Common element sorting.
    - Common CSV helpers.

Notes:
    This file should not generate report content.
"""

import csv
import shutil
from datetime import datetime
from pathlib import Path

from app.core.models import Element


def safe_release_name(
    release: str,
) -> str:
    value = str(release).strip()

    invalid = '\\/:*?"<>| '

    for char in invalid:
        value = value.replace(
            char,
            "_",
        )

    return value


def get_release_folder(
    release: str,
    base_path: str | Path,
) -> Path:
    release_folder = Path(base_path) / safe_release_name(release)

    release_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    return release_folder


def get_date_folder(
    release: str,
    base_path: str | Path,
) -> Path:
    release_folder = get_release_folder(
        release=release,
        base_path=base_path,
    )

    date_folder = release_folder / datetime.now().strftime("%Y-%m-%d")

    date_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    return date_folder


def archive_existing_reports(
    target_folder: Path,
) -> None:
    history_folder = target_folder / "History"

    history_folder.mkdir(
        exist_ok=True,
    )

    for file_path in target_folder.iterdir():
        if not file_path.is_file():
            continue

        destination = history_folder / file_path.name

        try:
            shutil.move(
                str(file_path),
                str(destination),
            )
        except Exception:
            pass


def sort_elements(
    elements: list[Element],
) -> list[Element]:
    """
    Final report ordering rule.

    1. Errors
    2. Warnings
    3. Everything else

    Within each section:
        Element name alphabetical.
    """

    severity_rank = {
        "ERROR": 0,
        "WARNING": 1,
        "INFO": 2,
        "OK": 3,
    }

    return sorted(
        (element for element in elements if element.visible),
        key=lambda element: (
            severity_rank.get(
                getattr(
                    element.severity,
                    "value",
                    "OK",
                ),
                99,
            ),
            element.element.upper(),
        ),
    )


def export_csv(
    output_path: Path,
    headers: list[str],
    rows: list[list[str]],
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.writer(file)

        writer.writerow(headers)

        writer.writerows(rows)
