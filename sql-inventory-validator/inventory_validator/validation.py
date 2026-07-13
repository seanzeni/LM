from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from .date_window import DateWindow
from .models import Bundle, Effort, Employee, ElementRecord, MiscSystemRegion
from .models import Project, Region, Severity, ValidationIssue
from .normalization import key


@dataclass(frozen=True, slots=True)
class ValidationInput:
    employees: list[Employee]
    projects: list[Project]
    elements: list[ElementRecord]
    efforts: list[Effort]
    bundles: list[Bundle]
    regions: list[Region]
    misc_regions: list[MiscSystemRegion]
    date_window: DateWindow
    misc_system_source_column: str = "Subsystem"


@dataclass(frozen=True, slots=True)
class ValidationOutput:
    issues: list[ValidationIssue]
    good_elements: list[ElementRecord]


def _owner_email(
    developer: str,
    tl_employees_by_last_name: dict[str, Employee],
    efforts_by_project: dict[str, Effort],
    project_code: str,
    team_leader: str,
    domain: str,
) -> tuple[str, str]:
    clean_developer = developer.strip()
    if len(clean_developer) == 4:
        return clean_developer, f"{clean_developer}@{domain}"

    team_lead_employee = tl_employees_by_last_name.get(key(team_leader))
    if team_lead_employee and team_lead_employee.developer:
        return team_lead_employee.developer, team_lead_employee.email

    effort = efforts_by_project.get(key(project_code))
    if effort and effort.team_lead:
        return effort.team_lead, f"{effort.team_lead}@{domain}"

    return clean_developer, f"{clean_developer}@{domain}" if clean_developer else ""


def _team_leader_email(
    team_leader: str,
    tl_employees_by_last_name: dict[str, Employee],
    domain: str,
) -> str:
    team_lead_employee = tl_employees_by_last_name.get(key(team_leader))
    if not team_lead_employee or not team_lead_employee.developer:
        return ""

    developer_id = team_lead_employee.developer.strip()
    if not developer_id:
        return ""

    return f"{developer_id}@{domain}"


def validate_inventory(data: ValidationInput, email_domain: str) -> ValidationOutput:
    tl_employees_by_last_name = _tl_employees_by_last_name(data.employees)
    projects_by_code = {key(project.project_code): project for project in data.projects}
    efforts_by_project = {key(effort.id): effort for effort in data.efforts}
    bundles_by_sequence = {
        bundle.sequence: bundle for bundle in data.bundles if bundle.sequence is not None
    }
    region_prefixes_by_env = _region_prefixes_by_env(data.regions)
    misc_regions_by_system = {
        key(item.system): item for item in data.misc_regions if item.system
    }

    issues: list[ValidationIssue] = []
    bad_element_ids: set[int] = set()

    for project in data.projects:
        if not data.date_window.contains(project.imp_date):
            continue

        if not project.team_leader.strip():
            issues.append(
                ValidationIssue(
                    severity=Severity.WARNING,
                    code="PROJECT_TEAM_LEADER_MISSING",
                    message="Project Team Leader is empty.",
                    project_code=project.project_code,
                    project_imp_date=project.imp_date,
                )
            )

    for element in data.elements:
        project = projects_by_code.get(element.project_key)
        if project and not data.date_window.contains(project.imp_date):
            continue
        if not project and not data.date_window.contains(element.imp_date):
            continue

        owner_id, owner_email = _owner_email(
            element.developer,
            tl_employees_by_last_name,
            efforts_by_project,
            element.project_code,
            element.team_leader,
            email_domain,
        )
        team_leader_email = _team_leader_email(
            element.team_leader,
            tl_employees_by_last_name,
            email_domain,
        )
        effort = efforts_by_project.get(element.project_key)
        associated_bundle = _associated_bundle_for_project(
            effort,
            project,
            bundles_by_sequence,
            data.bundles,
        )

        def add_issue(
            severity: Severity,
            code: str,
            message: str,
            include_assignment_context: bool = True,
            include_existing_effort_context: bool = False,
        ) -> None:
            include_effort_context = (
                include_assignment_context
                or (include_existing_effort_context and effort is not None)
            )
            issues.append(
                ValidationIssue(
                    severity=severity,
                    code=code,
                    message=message,
                    project_code=element.project_code,
                    element=element.element,
                    type=element.type,
                    project_imp_date=project.imp_date if project else None,
                    element_imp_date=element.imp_date,
                    owner_id=owner_id,
                    owner_email=owner_email,
                    cc_email=team_leader_email,
                    bundle_id=(
                        associated_bundle.id
                        if include_effort_context and associated_bundle
                        else ""
                    ),
                    bundle_sequence=(
                        associated_bundle.sequence
                        if include_effort_context and associated_bundle
                        else None
                    ),
                    bundle_qual_date=(
                        effort.bundle_qual_move_date
                        if include_effort_context and effort
                        else None
                    ),
                    bundle_prod_date=(
                        effort.bundle_prod_move_date
                        if include_effort_context and effort
                        else associated_bundle.bundle_prod_imp_date
                        if include_assignment_context and associated_bundle
                        else None
                    ),
                    effort_qual_date=(
                        effort.bundle_qual_move_date
                        if include_effort_context and effort
                        else None
                    ),
                    effort_prod_date=(
                        effort.bundle_prod_move_date
                        if include_effort_context and effort
                        else None
                    ),
                )
            )
            if severity == Severity.ERROR or code in {
                "ELEMENT_DEVELOPER_MISSING",
                "ELEMENT_DEVELOPER_INVALID",
                "ELEMENT_TEAM_LEADER_MISSING",
            }:
                bad_element_ids.add(id(element))

        if project is None:
            add_issue(
                Severity.ERROR,
                "ELEMENT_PROJECT_NOT_FOUND",
                "Element Project Code does not have a corresponding Project.",
                include_assignment_context=False,
            )
            if len(element.project_code.strip()) > 8 and element.project_key not in efforts_by_project:
                add_issue(
                    Severity.WARNING,
                    "POTENTIAL_MISTYPE",
                    "Project Code is longer than eight characters and was not found in RSET Efforts.",
                    include_assignment_context=False,
                )
            continue
        elif element.imp_date != project.imp_date:
            add_issue(
                Severity.ERROR,
                "ELEMENT_IMP_DATE_MISMATCH",
                "Element implementation date must match the Project implementation date.",
                include_assignment_context=False,
                include_existing_effort_context=True,
            )
            continue

        if len(element.element.strip()) > 8:
            add_issue(
                Severity.ERROR,
                "ELEMENT_NAME_TOO_LONG",
                "Element must be eight characters or fewer.",
            )

        missing_required_contact = False
        if not element.developer.strip():
            add_issue(
                Severity.WARNING,
                "ELEMENT_DEVELOPER_MISSING",
                "Element Developer is empty.",
                include_assignment_context=False,
            )
            missing_required_contact = True
        elif len(element.developer.strip()) != 4:
            add_issue(
                Severity.WARNING,
                "ELEMENT_DEVELOPER_INVALID",
                "Element Developer must be a four-character ID.",
                include_assignment_context=False,
            )
            missing_required_contact = True

        if not element.team_leader.strip():
            add_issue(
                Severity.WARNING,
                "ELEMENT_TEAM_LEADER_MISSING",
                "Element Team Leader is empty.",
                include_assignment_context=False,
            )
            missing_required_contact = True

        if missing_required_contact:
            continue

        if effort is None:
            if len(element.project_code.strip()) > 8:
                add_issue(
                    Severity.WARNING,
                    "POTENTIAL_MISTYPE",
                    "Project Code is longer than eight characters and was not found in RSET Efforts.",
                )

            default_bundle = _default_bundle_for_project(project, data.bundles)
            add_issue(
                Severity.INFO,
                "EFFORT_NOT_ASSIGNED",
                "Project was not found in RSET Efforts yet; default bundle placement will be used."
                + (
                    f" Suggested bundle {default_bundle.id} with production date "
                    f"{default_bundle.bundle_prod_imp_date}."
                    if default_bundle
                    else " No future default bundle was found."
                ),
            )
            continue

        bundle = bundles_by_sequence.get(effort.bundle_sequence)
        if bundle is None:
            add_issue(
                Severity.WARNING,
                "BUNDLE_NOT_FOUND",
                "Effort references a BundleSequence that was not found in Bundles.",
            )
            continue

        if bundle.test_environment == 0:
            add_issue(
                Severity.INFO,
                "REGION_VALIDATION_SKIPPED",
                "Bundle TestEnvironment is zero, so region validation was skipped on purpose.",
            )
            continue

        expected_prefixes = region_prefixes_by_env.get(bundle.test_environment, set())
        actual_system = _element_system_value(element, data.misc_system_source_column)
        actual_misc_region = misc_regions_by_system.get(key(actual_system))
        actual_prefix = actual_misc_region.prefix if actual_misc_region else ""

        if expected_prefixes and actual_prefix and actual_prefix not in expected_prefixes:
            add_issue(
                Severity.ERROR,
                "REGION_MISMATCH",
                "Element system region does not match the Bundle TestEnvironment region.",
            )

    good_elements = []
    for element in data.elements:
        if id(element) in bad_element_ids:
            continue
        if not _is_in_scope(element, projects_by_code, data.date_window):
            continue

        good_elements.append(
            _with_output_enrichment(
                element,
                projects_by_code.get(element.project_key),
                tl_employees_by_last_name,
                misc_regions_by_system,
                data.misc_system_source_column,
            )
        )
    return ValidationOutput(issues=issues, good_elements=good_elements)


def _tl_employees_by_last_name(
    employees: list[Employee],
) -> dict[str, Employee]:
    return {
        key(employee.last_name): employee
        for employee in employees
        if employee.last_name and key(employee.position) == "TL"
    }


def _with_output_enrichment(
    element: ElementRecord,
    project: Project | None,
    tl_employees_by_last_name: dict[str, Employee],
    misc_regions_by_system: dict[str, MiscSystemRegion],
    misc_system_source_column: str,
) -> ElementRecord:
    team_lead_employee = tl_employees_by_last_name.get(key(element.team_leader))
    resolved_team_leader = element.team_leader
    if team_lead_employee and team_lead_employee.developer:
        resolved_team_leader = team_lead_employee.developer.strip()

    source_system = _element_system_value(element, misc_system_source_column)
    misc_region = misc_regions_by_system.get(key(source_system))

    return replace(
        element,
        team_leader=resolved_team_leader,
        project_merge_region=project.merge_region if project else "",
        misc_system=misc_region.system if misc_region else source_system,
        misc_region=misc_region.region if misc_region else "",
    )


def _is_in_scope(
    element: ElementRecord,
    projects_by_code: dict[str, Project],
    window: DateWindow,
) -> bool:
    project = projects_by_code.get(element.project_key)
    if project:
        return window.contains(project.imp_date)
    return window.contains(element.imp_date)


def _region_prefixes_by_env(regions: list[Region]) -> dict[int, set[str]]:
    lookup: dict[int, set[str]] = {}
    for region in regions:
        if not region.prefix:
            continue
        lookup.setdefault(region.test_environment, set()).add(region.prefix)
    return lookup


def _element_system_value(element: ElementRecord, source_column: str) -> str:
    normalized = key(source_column)
    if normalized == "APPLICATION":
        return element.application
    if normalized == "APPLICATION AREA":
        return element.application_area
    if normalized == "PROCESSOR GROUP":
        return element.processor_group
    return element.subsystem


def _default_bundle_for_project(
    project: Project | None,
    bundles: list[Bundle],
) -> Bundle | None:
    if project is None or project.imp_date is None:
        return None

    default_bundles = [
        bundle
        for bundle in bundles
        if bundle.test_environment == 0 and bundle.bundle_prod_imp_date is not None
    ]
    if not default_bundles:
        return None

    exact_matches = [
        bundle for bundle in default_bundles if bundle.bundle_prod_imp_date == project.imp_date
    ]
    if exact_matches:
        return sorted(exact_matches, key=lambda item: item.bundle_prod_imp_date)[0]

    future_matches = [
        bundle for bundle in default_bundles if bundle.bundle_prod_imp_date >= project.imp_date
    ]
    if future_matches:
        return sorted(future_matches, key=lambda item: item.bundle_prod_imp_date)[0]

    return sorted(default_bundles, key=lambda item: item.bundle_prod_imp_date)[-1]


def _associated_bundle_for_project(
    effort: Effort | None,
    project: Project | None,
    bundles_by_sequence: dict[int, Bundle],
    bundles: list[Bundle],
) -> Bundle | None:
    if effort and effort.bundle_sequence is not None:
        return bundles_by_sequence.get(effort.bundle_sequence)

    return _default_bundle_for_project(project, bundles)
