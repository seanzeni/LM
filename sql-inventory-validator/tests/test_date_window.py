from __future__ import annotations

from datetime import date
import unittest

from inventory_validator.date_window import active_date_window


class DateWindowTests(unittest.TestCase):
    def test_before_15th_includes_previous_month(self) -> None:
        self.assertEqual(active_date_window(date(2026, 7, 13)).start, date(2026, 6, 1))

    def test_on_15th_starts_current_month(self) -> None:
        self.assertEqual(active_date_window(date(2026, 7, 15)).start, date(2026, 7, 1))

    def test_january_previous_month_crosses_year(self) -> None:
        self.assertEqual(active_date_window(date(2026, 1, 3)).start, date(2025, 12, 1))


if __name__ == "__main__":
    unittest.main()
