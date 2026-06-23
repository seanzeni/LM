from __future__ import annotations

"""
Purpose:
    Load and search fixed-width mainframe location data.

Used By:
    ValidationService
    ResyncReport
    LocationReport

Responsibilities:
    - Read fixed-width mainframe location output.
    - Parse one location record per line.
    - Build fast lookups by element/type.
    - Build fast lookups by environment.
    - Provide simple location/version lookup helpers.

Notes:
    This service does not decide whether something is an issue.
    It only answers location/version questions.
"""

from collections import defaultdict
from pathlib import Path

from app.core.models import MainframeLocationRecord


class MainframeLocationService:
    FIELD_WIDTHS: list[tuple[str, int]] = [
        ("element", 8),
        ("type", 8),
        ("subsystem", 8),
        ("system", 4),
        ("env", 5),
        ("date_generated", 10),
        ("time_generated", 11),
        ("version", 5),
        ("user", 8),
        ("ccid", 7),
        ("comments", 40),
    ]

    ENV_LEVELS: dict[str, int] = {
        "MAIN1": 1,
        "DEVL1": 1,
        "QUAL1": 2,
        "PROD1": 3,
        "FIXP1": 4,
    }

    VERSION_COMPARE_ENVS: set[str] = {
        "MAIN1",
        "DEVL1",
        "QUAL1",
        "PROD1",
    }

    FIX_ENV: str = "FIXP1"

    def __init__(
        self,
    ) -> None:
        self.records: list[MainframeLocationRecord] = []

        self.by_element_type: dict[
            tuple[str, str],
            list[MainframeLocationRecord],
        ] = defaultdict(list)

        self.by_element: dict[
            str,
            list[MainframeLocationRecord],
        ] = defaultdict(list)

        self.by_env: dict[
            str,
            list[MainframeLocationRecord],
        ] = defaultdict(list)

    def load_file(
        self,
        file_path: str | Path,
    ) -> MainframeLocationService:
        path = Path(file_path)

        self.records.clear()
        self.by_element_type.clear()
        self.by_element.clear()
        self.by_env.clear()

        with path.open(
            "r",
            encoding="cp1252",
            errors="replace",
        ) as file:
            for line_number, line in enumerate(
                file,
                start=1,
            ):
                if not line.strip():
                    continue

                record = self._parse_line(
                    line=line.rstrip("\n"),
                    line_number=line_number,
                )

                self.records.append(record)
                self.by_element_type[record.key].append(record)
                self.by_element[record.element_key].append(record)
                self.by_env[record.env.upper()].append(record)

        return self

    def _parse_line(
        self,
        line: str,
        line_number: int,
    ) -> MainframeLocationRecord:
        values: dict[str, str] = {}
        position = 0

        for field_name, width in self.FIELD_WIDTHS:
            values[field_name] = line[position : position + width].strip()

            position += width + 1

        major_version, level = self._parse_version(
            value=values.get(
                "version",
                "",
            ),
            line_number=line_number,
        )

        return MainframeLocationRecord(
            element=values.get("element", ""),
            type=values.get("type", ""),
            subsystem=values.get("subsystem", ""),
            system=values.get("system", ""),
            env=values.get("env", ""),
            date_generated=values.get("date_generated", ""),
            time_generated=values.get("time_generated", ""),
            version=values.get("version", ""),
            major_version=major_version,
            level=level,
            user=values.get("user", ""),
            ccid=values.get("ccid", ""),
            comments=values.get("comments", ""),
        )

    def _parse_version(
        self,
        value: str,
        line_number: int,
    ) -> tuple[int, int]:
        clean_value = str(value).strip()

        if "." not in clean_value:
            raise ValueError(f"Invalid version on line {line_number}: {clean_value!r}")

        major, level = clean_value.split(
            ".",
            maxsplit=1,
        )

        if not major.isdigit() or not level.isdigit():
            raise ValueError(f"Invalid version on line {line_number}: {clean_value!r}")

        return int(major), int(level)

    def find(
        self,
        element: str,
        type_: str,
    ) -> list[MainframeLocationRecord]:
        return self.by_element_type.get(
            (
                str(element).upper(),
                str(type_).upper(),
            ),
            [],
        )

    def find_by_element(
        self,
        element: str,
    ) -> list[MainframeLocationRecord]:
        return self.by_element.get(
            str(element).upper(),
            [],
        )

    def exists(
        self,
        element: str,
        type_: str,
    ) -> bool:
        return (
            len(
                self.find(
                    element=element,
                    type_=type_,
                )
            )
            > 0
        )

    def exists_in_env(
        self,
        element: str,
        type_: str,
        env: str,
    ) -> bool:
        wanted_env = str(env).strip().upper()

        return any(
            record.env.upper() == wanted_env
            for record in self.find(
                element=element,
                type_=type_,
            )
        )

    def exists_in_fixp1(
        self,
        element: str,
        type_: str,
    ) -> bool:
        return self.exists_in_env(
            element=element,
            type_=type_,
            env=self.FIX_ENV,
        )

    def get_records_in_env(
        self,
        env: str,
    ) -> list[MainframeLocationRecord]:
        return self.by_env.get(
            str(env).upper(),
            [],
        )

    def get_fixp1_records(
        self,
        element: str,
        type_: str,
    ) -> list[MainframeLocationRecord]:
        return [
            record
            for record in self.find(
                element=element,
                type_=type_,
            )
            if record.env.upper() == self.FIX_ENV
        ]

    def get_resync_details(
        self,
        element: str,
        type_: str,
    ) -> list[dict[str, str]]:
        """
        Future Resync Report helper.

        FIXP1 is excluded from version comparison because
        FIXP1 resets version numbers.
        """

        records = [
            record
            for record in self.find(
                element=element,
                type_=type_,
            )
            if record.env.upper() in self.VERSION_COMPARE_ENVS
        ]

        details: list[dict[str, str]] = []

        for lower in records:
            lower_level = self.ENV_LEVELS.get(
                lower.env.upper(),
                0,
            )

            for higher in records:
                higher_level = self.ENV_LEVELS.get(
                    higher.env.upper(),
                    0,
                )

                if higher_level <= lower_level:
                    continue

                if higher.version_number > lower.version_number:
                    details.append(
                        {
                            "lower_env": lower.env,
                            "lower_version": lower.version,
                            "higher_env": higher.env,
                            "higher_version": higher.version,
                        }
                    )

        return details

    def has_resync_issue(
        self,
        element: str,
        type_: str,
    ) -> bool:
        return (
            len(
                self.get_resync_details(
                    element=element,
                    type_=type_,
                )
            )
            > 0
        )
