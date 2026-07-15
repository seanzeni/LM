from __future__ import annotations

import unittest

from inventory_validator.cli import build_parser


class CliTests(unittest.TestCase):
    def test_email_drafts_are_opt_in(self) -> None:
        parser = build_parser()

        default_args = parser.parse_args([])
        draft_args = parser.parse_args(["--draftemails"])
        legacy_args = parser.parse_args(["--emails"])
        send_args = parser.parse_args(["--sendemails"])

        self.assertFalse(default_args.draftemails)
        self.assertFalse(default_args.sendemails)
        self.assertTrue(draft_args.draftemails)
        self.assertFalse(draft_args.sendemails)
        self.assertTrue(legacy_args.draftemails)
        self.assertTrue(send_args.sendemails)


if __name__ == "__main__":
    unittest.main()
