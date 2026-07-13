from __future__ import annotations

from datetime import date, datetime
from typing import Any


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def key(value: Any) -> str:
    return clean(value).upper()


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = clean(value).upper()
    return text in {"1", "TRUE", "T", "YES", "Y"}


def parse_int(value: Any) -> int | None:
    text = clean(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = clean(value)
    for fmt in ("%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def parse_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value

    text = clean(value)
    for fmt in (
        "%m/%d/%y %I:%M:%S %p",
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%y %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return None

