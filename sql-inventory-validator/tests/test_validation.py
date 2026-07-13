from __future__ import annotations

from datetime import date
import unittest

from inventory_validator.date_window import DateWindow
from inventory_validator.models import Bundle, Effort, Employee, ElementRecord
from inventory_validator.models import MiscSystemRegion, Project, Region, Severity
from inventory_validator.validation import ValidationInput, validate_inventory


def _element(**overrides: object) -> ElementRecord:
    values = {
        "project_code": "ABC1234",
        "imp_date": date(2026, 7, 20),
        "new_element": False,
        "online": True,
        "binds_required": False,
        "trans_id": "",
        "element": "ELM0001",
        "type": "BCOB",
        "processor_group": "",
        "application": "APP",
        "application_area": "AREA",
        "other_area_impacts": "",
        "subsystem": "SYS1",
        "developer": "DEV1",
        "team_leader": "Leader",
        "ndvr_package_name": "PKG",
        "length": "",
        "test_coord": False,
        "comments": "",
        "contact_number": "",
        "import_id": "",
        "import_date": None,
        "major_functions": "",
        "minor_functions": "",
    }
    values.update(overrides)
    return ElementRecord(**values)


def _input(elements: list[ElementRecord]) -> ValidationInput:
    return ValidationInput(
        employees=[
            Employee("DEV1", "Dev", "Person", "", "DEV1@domain.com"),
            Employee("TL01", "Team", "Leader", "TL", "TL01@domain.com"),
        ],
        projects=[
            Project("ABC1234", "ABC123", "Project", "TL01", "RGN-A", date(2026, 7, 20))
        ],
        elements=elements,
        efforts=[Effort("ABC1234", 10, "TL01", None, None, date(2026, 7, 20), None)],
        bundles=[Bundle("B1", 10, 2, date(2026, 7, 20))],
        regions=[Region("RGN1", 2)],
        misc_regions=[MiscSystemRegion("SYS1", "RGN2")],
        date_window=DateWindow(date(2026, 7, 1)),
    )


class ValidationTests(unittest.TestCase):
    def test_valid_element_is_good(self) -> None:
        result = validate_inventory(_input([_element()]), "domain.com")

        self.assertEqual(result.issues, [])
        self.assertEqual(len(result.good_elements), 1)
        self.assertEqual(result.good_elements[0].team_leader, "TL01")
        self.assertEqual(result.good_elements[0].project_merge_region, "RGN-A")
        self.assertEqual(result.good_elements[0].misc_system, "SYS1")
        self.assertEqual(result.good_elements[0].misc_region, "RGN2")

    def test_missing_project_blocks_good_output(self) -> None:
        result = validate_inventory(_input([_element(project_code="NOPE")]), "domain.com")

        self.assertTrue(any(issue.code == "ELEMENT_PROJECT_NOT_FOUND" for issue in result.issues))
        self.assertFalse(any(issue.code == "EFFORT_NOT_ASSIGNED" for issue in result.issues))
        self.assertEqual(result.good_elements, [])

    def test_long_missing_project_code_flags_potential_mistype(self) -> None:
        result = validate_inventory(
            _input([_element(project_code="TOO-LONG-PROJECT")]),
            "domain.com",
        )

        codes = {issue.code: issue.severity for issue in result.issues}
        self.assertEqual(codes["POTENTIAL_MISTYPE"], Severity.WARNING)
        self.assertFalse(any(issue.code == "EFFORT_NOT_ASSIGNED" for issue in result.issues))

    def test_effort_missing_is_info_only(self) -> None:
        data = _input([_element(project_code="ZZZ9999")])
        warning_data = ValidationInput(
            employees=data.employees,
            projects=[
                *data.projects,
                Project("ZZZ9999", "ZZZ999", "Unassigned", "TL01", "RGN-A", date(2026, 7, 20)),
            ],
            elements=data.elements,
            efforts=data.efforts,
            bundles=data.bundles,
            regions=data.regions,
            misc_regions=data.misc_regions,
            date_window=data.date_window,
        )

        result = validate_inventory(warning_data, "domain.com")

        codes = {issue.code: issue.severity for issue in result.issues}
        self.assertEqual(codes["EFFORT_NOT_ASSIGNED"], Severity.INFO)
        self.assertEqual(len(result.good_elements), 1)

    def test_existing_long_project_missing_effort_flags_potential_mistype(self) -> None:
        data = _input([_element(project_code="ABC1234567")])
        mistype_data = ValidationInput(
            employees=data.employees,
            projects=[
                *data.projects,
                Project("ABC1234567", "ABC123", "Long Project", "TL01", "RGN-A", date(2026, 7, 20)),
            ],
            elements=data.elements,
            efforts=data.efforts,
            bundles=data.bundles,
            regions=data.regions,
            misc_regions=data.misc_regions,
            date_window=data.date_window,
        )

        result = validate_inventory(mistype_data, "domain.com")

        codes = {issue.code: issue.severity for issue in result.issues}
        self.assertEqual(codes["POTENTIAL_MISTYPE"], Severity.WARNING)
        self.assertEqual(codes["EFFORT_NOT_ASSIGNED"], Severity.INFO)
        self.assertEqual(len(result.good_elements), 1)

    def test_region_validation_skipped_is_info(self) -> None:
        data = _input([_element()])
        skipped_data = ValidationInput(
            employees=data.employees,
            projects=data.projects,
            elements=data.elements,
            efforts=data.efforts,
            bundles=[Bundle("DEFAULT", 10, 0, date(2026, 7, 31))],
            regions=data.regions,
            misc_regions=data.misc_regions,
            date_window=data.date_window,
        )

        result = validate_inventory(skipped_data, "domain.com")

        codes = {issue.code: issue.severity for issue in result.issues}
        self.assertEqual(codes["REGION_VALIDATION_SKIPPED"], Severity.INFO)
        self.assertEqual(len(result.good_elements), 1)

    def test_empty_developer_and_team_leader_are_warnings(self) -> None:
        result = validate_inventory(
            _input([_element(developer="", team_leader="")]),
            "domain.com",
        )

        codes = {issue.code: issue.severity for issue in result.issues}
        self.assertEqual(codes["ELEMENT_DEVELOPER_MISSING"], Severity.WARNING)
        self.assertEqual(codes["ELEMENT_TEAM_LEADER_MISSING"], Severity.WARNING)
        self.assertFalse(any(issue.code == "REGION_MISMATCH" for issue in result.issues))
        self.assertEqual(result.good_elements, [])

    def test_unknown_four_character_developer_is_allowed(self) -> None:
        result = validate_inventory(
            _input([_element(developer="ZZ99")]),
            "domain.com",
        )

        self.assertFalse(any(issue.code.startswith("ELEMENT_DEVELOPER") for issue in result.issues))
        self.assertEqual(len(result.good_elements), 1)

    def test_non_four_character_developer_stops_validation(self) -> None:
        result = validate_inventory(
            _input([_element(developer="TOOLONG")]),
            "domain.com",
        )

        codes = {issue.code: issue.severity for issue in result.issues}
        self.assertEqual(codes["ELEMENT_DEVELOPER_INVALID"], Severity.WARNING)
        self.assertFalse(any(issue.code == "REGION_MISMATCH" for issue in result.issues))
        self.assertEqual(result.good_elements, [])

    def test_team_leader_last_name_resolves_owner_email_when_developer_invalid(self) -> None:
        result = validate_inventory(
            _input([_element(developer="BADID", team_leader="Leader")]),
            "domain.com",
        )

        invalid_issue = next(
            issue for issue in result.issues if issue.code == "ELEMENT_DEVELOPER_INVALID"
        )
        self.assertEqual(invalid_issue.owner_id, "TL01")
        self.assertEqual(invalid_issue.owner_email, "TL01@domain.com")
        self.assertEqual(invalid_issue.cc_email, "TL01@domain.com")

    def test_team_leader_email_is_cc_when_owner_is_developer(self) -> None:
        result = validate_inventory(
            _input([_element(element="TOOLONG01", developer="DEV1", team_leader="Leader")]),
            "domain.com",
        )

        element_issue = next(
            issue for issue in result.issues if issue.code == "ELEMENT_NAME_TOO_LONG"
        )
        self.assertEqual(element_issue.owner_email, "DEV1@domain.com")
        self.assertEqual(element_issue.cc_email, "TL01@domain.com")
        self.assertEqual(element_issue.bundle_id, "B1")
        self.assertEqual(element_issue.bundle_sequence, 10)
        self.assertEqual(element_issue.effort_prod_date, date(2026, 7, 20))

    def test_team_leader_resolution_uses_only_tl_position(self) -> None:
        data = _input([_element(team_leader="Person")])
        result = validate_inventory(data, "domain.com")

        self.assertEqual(result.good_elements[0].team_leader, "Person")

    def test_date_mismatch_stops_assignment_validation(self) -> None:
        result = validate_inventory(
            _input([_element(imp_date=date(2026, 7, 21))]),
            "domain.com",
        )

        self.assertTrue(any(issue.code == "ELEMENT_IMP_DATE_MISMATCH" for issue in result.issues))
        self.assertFalse(any(issue.code == "REGION_MISMATCH" for issue in result.issues))
        self.assertEqual(result.good_elements, [])

    def test_region_mismatch_is_error(self) -> None:
        data = _input([_element(subsystem="SYS1")])
        bad_data = ValidationInput(
            employees=data.employees,
            projects=data.projects,
            elements=data.elements,
            efforts=data.efforts,
            bundles=data.bundles,
            regions=[Region("ABC1", 2)],
            misc_regions=data.misc_regions,
            date_window=data.date_window,
        )

        result = validate_inventory(bad_data, "domain.com")

        self.assertTrue(any(issue.code == "REGION_MISMATCH" for issue in result.issues))
        self.assertEqual(result.good_elements, [])


if __name__ == "__main__":
    unittest.main()
