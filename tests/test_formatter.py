from __future__ import annotations
from app.core.formatter import build_record


def base_row() -> dict[str, str]:
    return {
        "Element": "PGM001",
        "Type": "OCOB",
        "Project": "ABCD999",
        "DSN ID": "DSN12345",
        "Release": "REL1",
        "Subsys": "SUB1",
        "System": "SYSTEM99",
        "Act Rgn": "DV01",
        "Application": "APP TEST",
    }


def test_build_record_uses_dsn_id_first_four_at_position_18() -> None:
    print(build_record(base_row(), "PROD"))
    assert build_record(base_row(), "PROD")[18:22] == "DSN1"


def test_build_record_sets_prod_env() -> None:
    assert build_record(base_row(), "PROD")[60:65] == "PROD1"


def test_build_record_sets_qual_env_from_dv_region() -> None:
    assert build_record(base_row(), "QUAL")[60:65] == "DEVL1"
