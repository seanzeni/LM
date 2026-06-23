from __future__ import annotations

"""
Purpose:
    Input validation helpers.

Used By:
    SettingsLoader
    DataLoader
    Toolbar

Notes:
    Business validation belongs in ValidationService.
"""


class ValidationError(Exception):
    pass


class ExcelValidationError(ValidationError):
    pass


class SettingsValidationError(ValidationError):
    pass


def validate_required_columns(
    actual_columns: list[str],
    required_columns: list[str],
) -> None:
    actual = {str(column).strip() for column in actual_columns}

    required = {str(column).strip() for column in required_columns}

    missing = sorted(required - actual)

    if missing:
        raise ExcelValidationError(
            "Missing required Excel columns: " + ", ".join(missing)
        )


def validate_required_settings(
    settings: dict[str, object],
    required_sections: set[str] | tuple[str, str],
    location: str = "settings",
) -> None:
    missing = [section for section in required_sections if section not in settings]

    if missing:
        raise SettingsValidationError(
            f"Missing required {location} key(s): " + ", ".join(sorted(missing))
        )


def validate_thread_count(
    thread_count: int,
    min_threads: int,
    max_threads: int,
) -> int:
    if thread_count < min_threads:
        return min_threads

    if thread_count > max_threads:
        return max_threads

    return thread_count


def validate_release(
    release: str,
) -> str:
    clean_release = str(release).strip()

    if not clean_release:
        raise ValidationError("Release cannot be blank.")

    return clean_release


def validate_effort_id(
    effort_id: str,
) -> str:
    clean_effort_id = str(effort_id).strip()

    if not clean_effort_id:
        raise ValidationError("Effort ID cannot be blank.")

    return clean_effort_id
