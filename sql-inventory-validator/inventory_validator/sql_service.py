from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pyodbc

from .config import ConnectionSettings


def quote_name(name: str) -> str:
    parts = [part.strip() for part in name.split(".") if part.strip()]
    return ".".join(f"[{part.replace(']', ']]')}]" for part in parts)


class SqlService:
    def __init__(self, settings: ConnectionSettings) -> None:
        self.settings = settings
        self.connection_string = self._build_connection_string()

    def _build_connection_string(self) -> str:
        parts = [
            f"DRIVER={{{self.settings.driver}}}",
            f"SERVER={self.settings.server}",
            f"DATABASE={self.settings.database}",
        ]
        if self.settings.trusted_connection:
            parts.append("Trusted_Connection=yes")
        else:
            parts.append(f"UID={self.settings.username}")
            parts.append(f"PWD={self.settings.password}")
        return ";".join(parts) + ";"

    def fetch_all(
        self,
        table: str,
        columns: Iterable[str],
        where_sql: str = "",
        params: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        column_list = ", ".join(quote_name(column) for column in columns)
        query = f"SELECT {column_list} FROM {quote_name(table)}"
        if where_sql:
            query += f" WHERE {where_sql}"

        with pyodbc.connect(self.connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute(query, *params)
            names = [column[0] for column in cursor.description]
            return [dict(zip(names, row)) for row in cursor.fetchall()]

