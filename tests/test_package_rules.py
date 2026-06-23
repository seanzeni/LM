from __future__ import annotations
from app.core.package_rules import contains_any_marker, is_archive_package, is_do_not_move, is_marked_prod, is_marked_qual, normalize_marker_text

def test_normalize_marker_text_uppercases_and_strips() -> None:
    assert normalize_marker_text("  prod  ") == "PROD"

def test_is_archive_package_detects_arch() -> None:
    assert is_archive_package("archive aps") is True
    assert is_archive_package("normal move") is False

def test_contains_any_marker() -> None:
    assert contains_any_marker("already in prod", ["PROD"]) is True
    assert contains_any_marker("already in prod", ["QUAL"]) is False

def test_is_do_not_move() -> None:
    assert is_do_not_move("please DO NOT MOVE this", ["DO NOT MOVE"]) is True

def test_is_marked_prod() -> None:
    assert is_marked_prod("already prod", ["PROD"]) is True

def test_is_marked_qual() -> None:
    assert is_marked_qual("already qual", ["QUAL"]) is True
