from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate ProdInventory SQL data for consolidated inventory.",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config JSON. Defaults to config.json.",
    )
    email_group = parser.add_mutually_exclusive_group()
    email_group.add_argument(
        "--draftemails",
        "--emails",
        action="store_true",
        dest="draftemails",
        help="Generate email draft templates for reportable issues.",
    )
    email_group.add_argument(
        "--sendemails",
        action="store_true",
        help="Send project issue emails through configured SMTP.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(Path(args.config))
    result = run_pipeline(
        config,
        write_email_drafts=args.draftemails,
        send_emails=args.sendemails,
    )

    print(f"Validated rows: {result.total_rows}")
    print(f"Good rows: {result.good_rows}")
    print(f"Issues: {result.issue_count}")
    print(f"Warnings: {result.warning_count}")
    print(f"Output folder: {result.output_dir}")
    return 1 if result.error_count else 0
