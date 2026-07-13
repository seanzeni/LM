from __future__ import annotations

from pathlib import Path
import unittest

from inventory_validator.config import AppConfig, ConnectionSettings, EmailSettings
from inventory_validator.config import OutputSettings, ValidationSettings
from inventory_validator.repository import InventoryRepository


class FakeSqlService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def fetch_all(
        self,
        table: str,
        columns: list[str],
        where_sql: str = "",
        params: tuple[object, ...] = (),
    ) -> list[dict[str, object]]:
        self.calls.append(
            {
                "table": table,
                "columns": columns,
                "where_sql": where_sql,
                "params": params,
            }
        )
        return []


def _config() -> AppConfig:
    connection = ConnectionSettings(
        driver="driver",
        server="server",
        database="database",
    )
    return AppConfig(
        prod_inventory=connection,
        rset=connection,
        email=EmailSettings(domain="domain.com"),
        outputs=OutputSettings(output_dir=Path("outputs")),
        validation=ValidationSettings(),
        tables={
            "efforts": "Efforts",
            "misc_environment_system": "MiscEnvironmentSystem",
        },
    )


class RepositoryTests(unittest.TestCase):
    def test_load_efforts_filters_to_null_bundle_exit_date(self) -> None:
        repository = InventoryRepository(_config())
        fake_rset = FakeSqlService()
        repository.rset = fake_rset

        efforts = repository.load_efforts()

        self.assertEqual(efforts, [])
        self.assertEqual(
            fake_rset.calls[0]["where_sql"],
            "[BundleExitDate] IS NULL",
        )

    def test_load_misc_environment_systems_uses_new_table(self) -> None:
        repository = InventoryRepository(_config())
        fake_rset = FakeSqlService()
        repository.rset = fake_rset

        rows = repository.load_misc_environment_systems()

        self.assertEqual(rows, [])
        self.assertEqual(
            fake_rset.calls[0]["table"],
            "MiscEnvironmentSystem",
        )


if __name__ == "__main__":
    unittest.main()
