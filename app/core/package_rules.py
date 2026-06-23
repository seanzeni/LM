from __future__ import annotations

"""
Purpose:
    Package classification helpers.
    
Used By:
    ValidationService
    
Notes:
    Used to cleanup markers so we can properly identify items to keep in
    the inventory and which ones to validate.
"""


def normalize_marker_text(
    value: object,
) -> str:
    return str(value or "").strip().upper()


def is_archive_package(
    package: object,
) -> bool:

    return "ARCH" in normalize_marker_text(package)


def contains_any_marker(
    value: object,
    markers: list[str],
) -> bool:
    text = normalize_marker_text(value)

    return any(normalize_marker_text(marker) in text for marker in markers)


def is_do_not_move(
    value: object,
    markers: list[str],
) -> bool:
    return contains_any_marker(
        value,
        markers,
    )


def is_marked_prod(
    value: object,
    markers: list[str],
) -> bool:
    return contains_any_marker(
        value,
        markers,
    )


def is_marked_qual(
    value: object,
    markers: list[str],
) -> bool:
    return contains_any_marker(
        value,
        markers,
    )
