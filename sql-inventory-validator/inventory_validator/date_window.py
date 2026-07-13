from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class DateWindow:
    start: date

    def contains(self, value: date | None) -> bool:
        if value is None:
            return False
        return value >= self.start


def active_date_window(today: date) -> DateWindow:
    if today.day >= 15:
        return DateWindow(start=today.replace(day=1))

    if today.month == 1:
        return DateWindow(start=date(today.year - 1, 12, 1))

    return DateWindow(start=date(today.year, today.month - 1, 1))

