from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from datetime import date
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


@dataclass(frozen=True, slots=True)
class MiscRegionResolution:
    misc_region: MiscSystemRegion | None
    lookup_source: str
    lookup_detail: str


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
    misc_regions_by_system = _misc_regions_by_system(data.misc_regions)
    misc_regions_by_prefix = _misc_regions_by_prefix(data.misc_regions)

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
            element,
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
                    effort_team_lead=(
                        effort.team_lead
                        if include_effort_context and effort
                        else ""
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
                include_existing_effort_context=True,
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

            default_bundle = _default_bundle_for_project(
                project,
                data.bundles,
                target_date=element.imp_date,
            )
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
        actual_misc_region = _resolve_misc_region(
            element=element,
            bundle=bundle,
            region_prefixes_by_env=region_prefixes_by_env,
            misc_regions_by_prefix=misc_regions_by_prefix,
            misc_regions_by_system=misc_regions_by_system,
            misc_system_source_column=data.misc_system_source_column,
        ).misc_region
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
                _associated_bundle_for_project(
                    efforts_by_project.get(element.project_key),
                    projects_by_code.get(element.project_key),
                    element,
                    bundles_by_sequence,
                    data.bundles,
                ),
                region_prefixes_by_env,
                misc_regions_by_prefix,
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
    bundle: Bundle | None,
    region_prefixes_by_env: dict[int, set[str]],
    misc_regions_by_prefix: dict[str, list[MiscSystemRegion]],
    misc_regions_by_system: dict[str, MiscSystemRegion],
    misc_system_source_column: str,
) -> ElementRecord:
    team_lead_employee = tl_employees_by_last_name.get(key(element.team_leader))
    resolved_team_leader = element.team_leader
    if team_lead_employee and team_lead_employee.developer:
        resolved_team_leader = team_lead_employee.developer.strip()

    resolution = _resolve_misc_region(
        element=element,
        bundle=bundle,
        region_prefixes_by_env=region_prefixes_by_env,
        misc_regions_by_prefix=misc_regions_by_prefix,
        misc_regions_by_system=misc_regions_by_system,
        misc_system_source_column=misc_system_source_column,
    )
    misc_region = resolution.misc_region
    source_system = _element_system_value(element, misc_system_source_column)
    resolved_merge_region = (
        misc_region.region
        if misc_region
        else project.merge_region
        if project
        else ""
    )
    resolved_system = misc_region.system if misc_region else source_system
    resolved_region = misc_region.region if misc_region else ""
    lookup_source = resolution.lookup_source
    lookup_detail = resolution.lookup_detail

    if bundle and bundle.test_environment == 0 and project:
        default_region, default_system = _split_default_merge_region(project.merge_region)
        if default_region or default_system:
            resolved_merge_region = default_region
            resolved_region = default_region
            resolved_system = default_system
            lookup_source = "project_merge_region_split"
            lookup_detail = (
                f"Bundle.Sequence/TestEnvironment={bundle.sequence}/0; "
                f"Project Merge Region={project.merge_region}; "
                f"Region={default_region}; System={default_system}"
            )

    if "ARCHIVE" in element.ndvr_package_name.upper():
        resolved_system = "PRIVATE1"
        lookup_detail = (
            f"{lookup_detail}; Package contains ARCHIVE, System overridden to PRIVATE1"
            if lookup_detail
            else "Package contains ARCHIVE, System overridden to PRIVATE1"
        )

    return replace(
        element,
        team_leader=resolved_team_leader,
        project_merge_region=resolved_merge_region,
        misc_system=resolved_system,
        misc_region=resolved_region,
        misc_lookup_source=lookup_source,
        misc_lookup_detail=lookup_detail,
        bundle_id=bundle.id if bundle else "",
        bundle_sequence=bundle.sequence if bundle else None,
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


def _misc_regions_by_system(
    misc_regions: list[MiscSystemRegion],
) -> dict[str, MiscSystemRegion]:
    return {
        key(item.system): item
        for item in misc_regions
        if item.system
    }


def _misc_regions_by_prefix(
    misc_regions: list[MiscSystemRegion],
) -> dict[str, list[MiscSystemRegion]]:
    lookup: dict[str, list[MiscSystemRegion]] = {}
    for item in misc_regions:
        if not item.prefix:
            continue
        lookup.setdefault(item.prefix, []).append(item)

    for items in lookup.values():
        items.sort(key=lambda item: (item.region.upper(), item.system.upper()))

    return lookup


def _resolve_misc_region(
    element: ElementRecord,
    bundle: Bundle | None,
    region_prefixes_by_env: dict[int, set[str]],
    misc_regions_by_prefix: dict[str, list[MiscSystemRegion]],
    misc_regions_by_system: dict[str, MiscSystemRegion],
    misc_system_source_column: str,
) -> MiscRegionResolution:
    source_system = _element_system_value(element, misc_system_source_column)

    if bundle and bundle.test_environment != 0:
        prefixes = sorted(region_prefixes_by_env.get(bundle.test_environment, set()))
        candidates = [
            item
            for prefix in prefixes
            for item in misc_regions_by_prefix.get(prefix, [])
        ]
        if candidates:
            source_match = next(
                (item for item in candidates if key(item.system) == key(source_system)),
                None,
            )
            matched = source_match or candidates[0]
            return MiscRegionResolution(
                misc_region=matched,
                lookup_source="region_prefix",
                lookup_detail=(
                    f"Bundle.Sequence/TestEnvironment={bundle.sequence}/"
                    f"{bundle.test_environment}; Region prefixes={','.join(prefixes)}; "
                    f"matched Misc Region={matched.region}; matched System={matched.system}"
                ),
            )

        fallback = misc_regions_by_system.get(key(source_system))
        return MiscRegionResolution(
            misc_region=fallback,
            lookup_source="system_fallback",
            lookup_detail=(
                f"No MiscEnvironmentSystem rows matched Region prefixes "
                f"{','.join(prefixes) or 'NONE'} for TestEnvironment "
                f"{bundle.test_environment}; fallback System={source_system}"
            ),
        )

    fallback = misc_regions_by_system.get(key(source_system))
    if fallback:
        return MiscRegionResolution(
            misc_region=fallback,
            lookup_source="system_fallback",
            lookup_detail=(
                f"No nonzero bundle TestEnvironment available; fallback System={source_system}"
            ),
        )

    if bundle and bundle.test_environment == 0:
        selected = _first_misc_region(misc_regions_by_prefix)
        return MiscRegionResolution(
            misc_region=selected,
            lookup_source="test_environment_zero_default",
            lookup_detail=(
                f"Bundle.Sequence/TestEnvironment={bundle.sequence}/0; "
                "region validation is informational for default environments; "
                + (
                    f"selected Misc Region={selected.region}; matched System={selected.system}"
                    if selected
                    else "no MiscEnvironmentSystem row available"
                )
            ),
        )

    return MiscRegionResolution(
        misc_region=None,
        lookup_source="unresolved",
        lookup_detail=(
            f"No nonzero bundle TestEnvironment available; fallback System={source_system}"
        ),
    )


def _split_default_merge_region(merge_region: str) -> tuple[str, str]:
    region, separator, system = merge_region.partition("/")
    if not separator:
        return merge_region.strip().upper(), ""

    return region.strip().upper(), system.strip().upper()


def _first_misc_region(
    misc_regions_by_prefix: dict[str, list[MiscSystemRegion]],
) -> MiscSystemRegion | None:
    for prefix in sorted(misc_regions_by_prefix):
        items = misc_regions_by_prefix[prefix]
        if items:
            return items[0]
    return None


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
    target_date: date | None = None,
) -> Bundle | None:
    placement_date = target_date or (project.imp_date if project else None)
    if placement_date is None:
        return None

    default_bundles = [
        bundle
        for bundle in bundles
        if bundle.test_environment == 0 and bundle.bundle_prod_imp_date is not None
    ]
    if not default_bundles:
        return None

    exact_matches = [
        bundle for bundle in default_bundles if bundle.bundle_prod_imp_date == placement_date
    ]
    if exact_matches:
        return sorted(exact_matches, key=lambda item: item.bundle_prod_imp_date)[0]

    future_matches = [
        bundle for bundle in default_bundles if bundle.bundle_prod_imp_date >= placement_date
    ]
    if future_matches:
        return sorted(future_matches, key=lambda item: item.bundle_prod_imp_date)[0]

    return sorted(default_bundles, key=lambda item: item.bundle_prod_imp_date)[-1]


def _associated_bundle_for_project(
    effort: Effort | None,
    project: Project | None,
    element: ElementRecord,
    bundles_by_sequence: dict[int, Bundle],
    bundles: list[Bundle],
) -> Bundle | None:
    if effort and effort.bundle_sequence is not None:
        return bundles_by_sequence.get(effort.bundle_sequence)

    return _default_bundle_for_project(project, bundles, target_date=element.imp_date)
