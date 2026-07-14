from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import pandas as pd

from .models import ElementRecord, Severity, ValidationIssue


def write_outputs(
    output_root: Path,
    issues: list[ValidationIssue],
    good_elements: list[ElementRecord],
    write_csv: bool,
    write_xlsx: bool,
    write_email_drafts: bool,
) -> Path:
    run_dir = output_root / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    reportable_issues = [
        issue for issue in issues if issue.severity in {Severity.ERROR, Severity.WARNING}
    ]
    info_notes = _info_notes_by_element(issues)

    issues_df = pd.DataFrame([asdict(issue) for issue in reportable_issues])
    good_df = pd.DataFrame(
        [_element_row(element, info_notes) for element in good_elements],
    )
    email_df = pd.DataFrame(_email_rows(reportable_issues))
    missing_projects_summary_df = pd.DataFrame(
        _missing_projects_summary(reportable_issues),
    )
    missing_project_elements_df = pd.DataFrame(
        _issue_elements(reportable_issues, "ELEMENT_PROJECT_NOT_FOUND"),
    )
    imp_date_mismatch_summary_df = pd.DataFrame(
        _imp_date_mismatch_summary(reportable_issues),
    )
    imp_date_mismatch_elements_df = pd.DataFrame(
        _issue_elements(reportable_issues, "ELEMENT_IMP_DATE_MISMATCH"),
    )

    good_df.to_csv(run_dir / "consolidated_inventory_source.csv", index=False)

    if write_csv:
        issues_df.to_csv(run_dir / "validation_issues.csv", index=False)
        email_df.to_csv(run_dir / "email_recipients.csv", index=False)
        missing_projects_summary_df.to_csv(
            run_dir / "missing_projects_summary.csv",
            index=False,
        )
        missing_project_elements_df.to_csv(
            run_dir / "missing_project_elements.csv",
            index=False,
        )
        imp_date_mismatch_summary_df.to_csv(
            run_dir / "implementation_date_mismatch_summary.csv",
            index=False,
        )
        imp_date_mismatch_elements_df.to_csv(
            run_dir / "implementation_date_mismatch_elements.csv",
            index=False,
        )

    if write_xlsx:
        with pd.ExcelWriter(run_dir / "inventory_validation_outputs.xlsx") as writer:
            issues_df.to_excel(writer, sheet_name="Issues", index=False)
            missing_projects_summary_df.to_excel(
                writer,
                sheet_name="Missing Projects Summary",
                index=False,
            )
            missing_project_elements_df.to_excel(
                writer,
                sheet_name="Missing Project Elements",
                index=False,
            )
            imp_date_mismatch_summary_df.to_excel(
                writer,
                sheet_name="Imp Date Mismatch Summary",
                index=False,
            )
            imp_date_mismatch_elements_df.to_excel(
                writer,
                sheet_name="Imp Date Mismatch Rows",
                index=False,
            )
            good_df.to_excel(writer, sheet_name="Good Inventory Source", index=False)
            email_df.to_excel(writer, sheet_name="Email Recipients", index=False)

    if write_email_drafts:
        _write_email_drafts(run_dir / "email_drafts", reportable_issues)

    return run_dir


def _element_row(
    element: ElementRecord,
    info_notes: dict[tuple[str, str, str], str],
) -> dict[str, object]:
    return {
        "Project": element.project_code,
        "CCID": element.project_code.strip()[:6],
        "Merge Region": element.project_merge_region,
        "Element": element.element,
        "Type": element.type,
        "Subsys": element.subsystem,
        "System": element.misc_system or element.application,
        "Region": element.misc_region,
        "Misc Lookup Source": element.misc_lookup_source,
        "Misc Lookup Detail": element.misc_lookup_detail,
        "Application": element.application,
        "Area": element.application_area,
        "Package": element.ndvr_package_name,
        "Developer": element.developer,
        "Team Leader": element.team_leader,
        "Implementation Date": element.imp_date,
        "Comments": element.comments,
        "MajorFunctions": element.major_functions,
        "MinorFunctions": element.minor_functions,
        "Validation Notes": info_notes.get(
            _element_issue_key(element.project_code, element.element, element.type),
            "",
        ),
    }


def _email_rows(issues: list[ValidationIssue]) -> list[dict[str, object]]:
    rows = []
    for project_code, items in _issues_by_project(issues).items():
        rows.append(
            {
                "project_code": project_code,
                "to": ", ".join(_owner_emails(items)),
                "cc": ", ".join(_cc_emails(items)),
                "blocking_errors": sum(1 for item in items if item.severity == Severity.ERROR),
                "warnings": sum(1 for item in items if item.severity == Severity.WARNING),
                "issue_count": len(items),
                "developers": ", ".join(_owner_labels(items)),
                "team_leads": ", ".join(_team_lead_labels(items)),
            }
        )
    return rows


def _write_email_drafts(folder: Path, issues: list[ValidationIssue]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    _write_issue_resolution_instructions(folder)

    for project_code, items in _issues_by_project(issues).items():
        safe_name = _safe_filename(project_code or "NO_PROJECT")
        lines = [
            f"Subject: Inventory data issues need review - {project_code or 'Unknown Project'}",
            f"To: {', '.join(_owner_emails(items))}",
            f"Cc: {', '.join(_cc_emails(items))}",
            "",
            "The automated inventory validation found project issues that need review:",
            "",
        ]
        lines.extend(_project_context_lines(project_code, items))
        lines.append("PID Data")
        lines.append(f"Project Imp Date: {_unique_text(items, 'project_imp_date')}")
        lines.append(f"Developers: {', '.join(_owner_labels(items)) or 'N/A'}")
        lines.append(f"Team Leads: {', '.join(_team_lead_labels(items)) or 'N/A'}")
        lines.append("")
        lines.append("Issues")
        for item in items:
            lines.append(_issue_email_line(item))
        lines.append("")
        lines.append("Please correct the source data and rerun validation.")
        (folder / f"{safe_name}.txt").write_text("\n".join(lines), encoding="utf-8")


def _cc_emails(
    issues: list[ValidationIssue],
) -> list[str]:
    to_emails = {email.lower() for email in _owner_emails(issues)}
    return sorted(
        {
            issue.cc_email
            for issue in issues
            if issue.cc_email and issue.cc_email.lower() not in to_emails
        }
    )


def _owner_emails(issues: list[ValidationIssue]) -> list[str]:
    return sorted({issue.owner_email for issue in issues if issue.owner_email})


def _owner_labels(issues: list[ValidationIssue]) -> list[str]:
    return sorted(
        {
            _person_label(issue.owner_id, issue.owner_email)
            for issue in issues
            if issue.owner_id or issue.owner_email
        }
    )


def _team_lead_labels(issues: list[ValidationIssue]) -> list[str]:
    return sorted(
        {
            value
            for issue in issues
            for value in (
                _person_label("", issue.cc_email),
                issue.effort_team_lead.strip(),
            )
            if value
        }
    )


def _person_label(person_id: str, email: str) -> str:
    if person_id and email:
        return f"{person_id} <{email}>"
    return person_id or email


def _safe_filename(value: str) -> str:
    safe_chars = []
    for char in value.strip():
        safe_chars.append(char if char.isalnum() or char in {"-", "_"} else "_")
    return "".join(safe_chars) or "NO_PROJECT"


def _issues_by_project(
    issues: list[ValidationIssue],
) -> dict[str, list[ValidationIssue]]:
    grouped: dict[str, list[ValidationIssue]] = defaultdict(list)
    for issue in issues:
        grouped[issue.project_code].append(issue)
    return dict(sorted(grouped.items()))


def _project_context_lines(
    project_code: str,
    issues: list[ValidationIssue],
) -> list[str]:
    return [
        f"Project: {project_code}",
        "",
        "RSET Data",
        f"Associated Bundle: {_unique_text(issues, 'bundle_id')}",
        f"Bundle Sequence: {_unique_text(issues, 'bundle_sequence')}",
        f"Bundle Qual Date: {_unique_text(issues, 'bundle_qual_date')}",
        f"Bundle Prod Date: {_unique_text(issues, 'bundle_prod_date')}",
        f"Effort Team Lead(s): {_unique_text(issues, 'effort_team_lead')}",
        f"Effort Qual Date(s): {_unique_text(issues, 'effort_qual_date')}",
        f"Effort Prod Date(s): {_unique_text(issues, 'effort_prod_date')}",
        "",
    ]


def _issue_email_line(
    issue: ValidationIssue,
) -> str:
    parts = [
        f"- [{issue.severity}] {issue.code}:",
        f"Element={issue.element}",
        f"Type={issue.type}",
        f"Owner={_person_label(issue.owner_id, issue.owner_email) or 'N/A'}",
        f"TeamLead={_person_label('', issue.cc_email) or issue.effort_team_lead or 'N/A'}",
    ]
    if issue.code == "ELEMENT_IMP_DATE_MISMATCH":
        parts.append(f"Element Imp Date={_format_value(issue.element_imp_date)}")
    parts.append(issue.message)
    return " ".join(parts)


def _write_issue_resolution_instructions(folder: Path) -> None:
    lines = [
        "Inventory Validation Issue Resolution Instructions",
        "",
        "1. Review the project draft for your Project Code.",
        "2. Use the RSET Data section to confirm the Effort, Bundle, release dates, and RSET TeamLead.",
        "3. Use the PID Data section to confirm Project and Element values from ProdInventory.",
        "4. For missing projects, add or correct the Project row before rerunning validation.",
        "5. For implementation date mismatches, update the Element Imp Date or Project Imp Date so they match.",
        "6. For missing or invalid Developer/Team Leader values, correct the Element contact fields.",
        "7. For potential mistypes, review long Project Codes that are not found in RSET Efforts.",
        "8. After source data is corrected, rerun the validation pipeline and confirm the issue is gone.",
    ]
    (folder / "issue_resolution_instructions.txt").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def _unique_text(
    issues: list[ValidationIssue],
    field_name: str,
) -> str:
    values = sorted(
        {
            _format_value(getattr(issue, field_name))
            for issue in issues
            if _format_value(getattr(issue, field_name))
        }
    )
    return ", ".join(values) if values else "N/A"


def _format_value(
    value: object,
) -> str:
    if value is None:
        return ""
    return str(value)


def _missing_projects_summary(
    issues: list[ValidationIssue],
) -> list[dict[str, object]]:
    grouped: dict[str, list[ValidationIssue]] = defaultdict(list)
    for issue in issues:
        if issue.code == "ELEMENT_PROJECT_NOT_FOUND":
            grouped[issue.project_code].append(issue)

    return [
        {
            "issue_type": "MISSING_PROJECTS",
            "project_code": project_code,
            "element_count": len(items),
            "project_imp_date": "",
            "element_imp_dates": ", ".join(
                sorted({str(item.element_imp_date) for item in items if item.element_imp_date})
            ),
        }
        for project_code, items in sorted(grouped.items())
    ]


def _imp_date_mismatch_summary(
    issues: list[ValidationIssue],
) -> list[dict[str, object]]:
    grouped: dict[str, list[ValidationIssue]] = defaultdict(list)
    for issue in issues:
        if issue.code == "ELEMENT_IMP_DATE_MISMATCH":
            grouped[issue.project_code].append(issue)

    return [
        {
            "issue_type": "IMPLEMENTATION_DATE_MISMATCH",
            "project_code": project_code,
            "element_count": len(items),
            "project_imp_date": _first_date(items, "project"),
            "element_imp_dates": ", ".join(
                sorted({str(item.element_imp_date) for item in items if item.element_imp_date})
            ),
        }
        for project_code, items in sorted(grouped.items())
    ]


def _issue_elements(
    issues: list[ValidationIssue],
    code: str,
) -> list[dict[str, object]]:
    return [
        {
            "project_code": issue.project_code,
            "element": issue.element,
            "type": issue.type,
            "project_imp_date": issue.project_imp_date,
            "element_imp_date": issue.element_imp_date,
            "owner_id": issue.owner_id,
            "owner_email": issue.owner_email,
            "message": issue.message,
        }
        for issue in issues
        if issue.code == code
    ]


def _first_date(
    items: list[ValidationIssue],
    date_kind: str,
) -> object:
    for item in items:
        value = item.project_imp_date if date_kind == "project" else item.element_imp_date
        if value:
            return value
    return ""


def _info_notes_by_element(
    issues: list[ValidationIssue],
) -> dict[tuple[str, str, str], str]:
    grouped: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for issue in issues:
        if issue.severity != Severity.INFO:
            continue
        grouped[_element_issue_key(issue.project_code, issue.element, issue.type)].append(
            f"{issue.code}: {issue.message}",
        )

    return {
        issue_key: " | ".join(messages)
        for issue_key, messages in grouped.items()
    }


def _element_issue_key(
    project_code: str,
    element: str,
    type_value: str,
) -> tuple[str, str, str]:
    return (
        project_code.strip().upper(),
        element.strip().upper(),
        type_value.strip().upper(),
    )
