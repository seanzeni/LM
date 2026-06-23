from __future__ import annotations

"""
Purpose:
    SQL Server access layer for release/bundle/effort data.
    
Used By:
    MainWindow
    EffortService
    ValidationService

Responsibilities:
    - Connect to SQL Server using pyodbc.
    - Find the bundle sequence ID for a selected release.
    - Load efforts tied to that bundle sequence.
    - Look up what release SQl says an effort belongs to.

Notes:
    This file should not read Excel.
    This service should not validate inventory.
    This service should not build reports.
"""

import pyodbc

from app.core.models import ReleaseEffort


class DBService:
    def __init__(
        self,
        db_settings: dict,
    ) -> None:
        self.db_settings = db_settings
        self.conn_str: str = self._build_connection_string()

    def _build_connection_string(
        self,
    ) -> str:
        driver: str = str(
            self.db_settings.get("driver", "ODBC Driver 17 for SQL Server")
        )
        server: str = str(self.db_settings.get("server", ""))
        database: str = str(self.db_settings.get("database", ""))
        trusted: bool = bool(
            self.db_settings.get(
                "trusted_connection",
                True,
            )
        )

        parts: list[str] = [
            f"DRIVER={{{driver}}}",
            f"SERVER={server}",
            f"DATABASE={database}",
        ]

        if trusted:
            parts.append("Trusted_Connection=yes")
        else:
            parts.append(f"UID={self.db_settings.get('username', '')}")
            parts.append(f"PWD={self.db_settings.get('password', '')}")
        return ";".join(parts) + ";"

    def get_connection(self) -> pyodbc.Connection:
        return pyodbc.connect(self.conn_str)

    def get_bundle_sequence_id(
        self,
        release: str,
    ) -> str | None:
        """
        Find the bundle sequence ID for the selected release.

        The release value comes from the spreadsheet dropdown.
        """
        clean_release: str = str(release).strip()

        if not clean_release:
            return None

        query: str = """
        SELECT Sequence
        FROM Bundles
        WHERE LOWER(LTRIM(RTRIM(Id))) = LOWER(?)
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, clean_release)

            row = cursor.fetchone()

            if row is None:
                return None

            sequence: str = str(
                getattr(
                    row,
                    "Sequence",
                    "",
                )
            ).strip()

            return sequence or None

    def get_release_efforts(
        self,
        bundle_sequence_id: str,
    ) -> list[ReleaseEffort]:
        """
        Load only efforts connected to the one bundle sequence.
        """

        clean_sequence: str = str(bundle_sequence_id).strip()

        if not clean_sequence:
            return []

        query: str = """
        SELECT
            Id,
            BundleQualMoveDate,
            BundleProdMoveDate,
            BundleExitDate,
            NoInventory
        FROM Efforts
        WHERE CAST(BundleSequence AS VARCHAR(50)) = ?
        """

        efforts: list[ReleaseEffort] = []

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, clean_sequence)

            for row in cursor.fetchall():
                efforts.append(
                    ReleaseEffort(
                        effort_id=str(
                            getattr(
                                row,
                                "Id",
                                "",
                            ).strip()
                        ),
                        qual_date=getattr(row, "BundleQualMoveDate", None),
                        prod_date=getattr(row, "BundleProdMoveDate", None),
                        exit_date=getattr(row, "BundleExitDate", None),
                        no_inventory=bool(getattr(row, "NoInventory", False)),
                    ),
                )
        return efforts

    def get_efforts_for_release(
        self,
        release: str,
    ) -> list[ReleaseEffort]:
        """
        Convenience method:
            release -> bundle sequence -> release efforts
        """
        sequence: str | None = self.get_bundle_sequence_id(release)
        if sequence is None:
            return []

        return self.get_release_efforts(sequence)

    def find_release_for_effort(
        self,
        effort_id: str,
    ) -> str | None:
        """
        Find what release SQL says an effort belongs to.

        Used to identify:
            inventory effort connected to the wrong release
        """
        clean_effort_id: str = str(effort_id).strip()
        if not clean_effort_id:
            return None

        query: str = """
        SELECT TOP 1
            b.Id As ReleaseId
        FROM Efforts e
        INNER JOIN Bundles b
            ON CAST(e.BundleSequence AS VARCHAR(50)) = CAST(b.Sequence AS VARCHAR(50))
        WHERE LOWER(LTRIM(RTRIM(e.Id))) = LOWER(?)
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, clean_effort_id)

            row = cursor.fetchone()

            if row is None:
                return None

            release_id: str = str(getattr(row, "ReleaseId", "")).strip()

            return release_id or None

    def build_effort_release_lookup(
        self,
        effort_ids: set[str],
    ) -> dict[str, str]:
        """
        Build lookup only for effort IDs found in the loaded inventory.

        This avoids pulling unnecessary SQL data.
        """

        lookup: dict[str, str] = {}
        for effort_id in effort_ids:
            clean_effort_id: str = str(effort_id).strip()

            if not clean_effort_id:
                continue

            release: str | None = self.find_release_for_effort(clean_effort_id)

            if release:
                lookup[clean_effort_id] = release

        return lookup

    def connection(self):
        return pyodbc.connect(self._connection_string)

    def load_release_efforts(
        self,
        release: str,
    ) -> list[ReleaseEffort]:
        query = """
        SELECT
            EffortId,
            QualDate,
            ProdDate,
            ExistDate,
            NoInventory
        FROM ReleaseSchedule
        WHERE Release = ?
        """

        efforts: list[ReleaseEffort] = []

        with self.connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                query,
                release,
            )

            for row in cursor.fetchall():
                efforts.append(
                    ReleaseEffort(
                        effort_id=str(row.EffortId).strip(),
                        qual_date=row.QualDate,
                        prod_date=row.ProdDate,
                        exit_date=row.ExitDate,
                        no_inventory=bool(row.NoInventory),
                    )
                )
        return efforts

    def build_effort_lookup(
        self,
        efforts: list[ReleaseEffort],
    ) -> dict[str, ReleaseEffort]:
        return {effort.effort_id.upper(): efforts for effort in efforts}
