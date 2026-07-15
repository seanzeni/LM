from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ConnectionSettings:
    driver: str
    server: str
    database: str
    trusted_connection: bool = True
    username: str = ""
    password: str = ""


@dataclass(frozen=True, slots=True)
class EmailSettings:
    domain: str
    from_address: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True


@dataclass(frozen=True, slots=True)
class OutputSettings:
    output_dir: Path
    write_xlsx: bool = True
    write_csv: bool = True
    write_email_drafts: bool = False


@dataclass(frozen=True, slots=True)
class ValidationSettings:
    today: str | None = None
    misc_system_source_column: str = "Subsystem"


@dataclass(frozen=True, slots=True)
class AppConfig:
    prod_inventory: ConnectionSettings
    rset: ConnectionSettings
    email: EmailSettings
    outputs: OutputSettings
    validation: ValidationSettings
    tables: dict[str, str]


def _connection(raw: dict) -> ConnectionSettings:
    return ConnectionSettings(
        driver=str(raw.get("driver", "ODBC Driver 17 for SQL Server")),
        server=str(raw.get("server", "")),
        database=str(raw.get("database", "")),
        trusted_connection=bool(raw.get("trusted_connection", True)),
        username=str(raw.get("username", "")),
        password=str(raw.get("password", "")),
    )


def load_config(path: Path) -> AppConfig:
    with path.open("r", encoding="utf-8") as file:
        raw = json.load(file)

    connections = raw.get("connections", {})
    outputs = raw.get("outputs", {})
    validation = raw.get("validation", {})
    email = raw.get("email", {})

    return AppConfig(
        prod_inventory=_connection(connections.get("prod_inventory", {})),
        rset=_connection(connections.get("rset", {})),
        email=EmailSettings(
            domain=str(email.get("domain", "domain.com")).lstrip("@"),
            from_address=str(email.get("from_address", "")),
            smtp_host=str(email.get("smtp_host", "")),
            smtp_port=int(email.get("smtp_port", 587)),
            smtp_username=str(email.get("smtp_username", "")),
            smtp_password=str(email.get("smtp_password", "")),
            smtp_use_tls=bool(email.get("smtp_use_tls", True)),
        ),
        outputs=OutputSettings(
            output_dir=Path(outputs.get("output_dir", "outputs")),
            write_xlsx=bool(outputs.get("write_xlsx", True)),
            write_csv=bool(outputs.get("write_csv", True)),
            write_email_drafts=bool(outputs.get("write_email_drafts", False)),
        ),
        validation=ValidationSettings(
            today=validation.get("today"),
            misc_system_source_column=str(
                validation.get("misc_system_source_column", "Subsystem")
            ),
        ),
        tables={str(key): str(value) for key, value in raw.get("tables", {}).items()},
    )
