from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .config import AppConfig
from .date_window import active_date_window
from .models import Severity
from .outputs import write_outputs
from .repository import InventoryRepository
from .validation import ValidationInput, validate_inventory


@dataclass(frozen=True, slots=True)
class PipelineResult:
    total_rows: int
    good_rows: int
    issue_count: int
    warning_count: int
    error_count: int
    output_dir: Path


def run_pipeline(
    config: AppConfig,
    write_email_drafts: bool | None = None,
    send_emails: bool = False,
) -> PipelineResult:
    repository = InventoryRepository(config)
    today = date.fromisoformat(config.validation.today) if config.validation.today else date.today()
    window = active_date_window(today)

    employees = repository.load_employees()
    projects = repository.load_projects()
    elements = repository.load_elements()
    efforts = repository.load_efforts()
    bundles = repository.load_bundles()
    regions = repository.load_regions()
    misc_environment_systems = repository.load_misc_environment_systems()

    validation = validate_inventory(
        ValidationInput(
            employees=employees,
            projects=projects,
            elements=elements,
            efforts=efforts,
            bundles=bundles,
            regions=regions,
            misc_regions=misc_environment_systems,
            date_window=window,
            misc_system_source_column=config.validation.misc_system_source_column,
        ),
        email_domain=config.email.domain,
    )

    output_dir = write_outputs(
        output_root=config.outputs.output_dir,
        issues=validation.issues,
        good_elements=validation.good_elements,
        write_csv=config.outputs.write_csv,
        write_xlsx=config.outputs.write_xlsx,
        write_email_drafts=(
            config.outputs.write_email_drafts
            if write_email_drafts is None
            else write_email_drafts
        ),
        send_emails=send_emails,
        email_settings=config.email,
    )

    error_count = sum(1 for issue in validation.issues if issue.severity == Severity.ERROR)
    warning_count = sum(1 for issue in validation.issues if issue.severity == Severity.WARNING)

    return PipelineResult(
        total_rows=len(elements),
        good_rows=len(validation.good_elements),
        issue_count=error_count + warning_count,
        warning_count=warning_count,
        error_count=error_count,
        output_dir=output_dir,
    )
