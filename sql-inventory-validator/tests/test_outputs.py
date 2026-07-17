from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

from inventory_validator.config import EmailSettings
from inventory_validator.models import ElementRecord, Severity, ValidationIssue
from inventory_validator.outputs import send_project_emails, write_outputs


def _element() -> ElementRecord:
    return ElementRecord(
        project_code="ABC1234",
        imp_date=date(2026, 7, 20),
        new_element=False,
        online=True,
        binds_required=False,
        trans_id="",
        element="ELM0001",
        type="BCOB",
        processor_group="",
        application="APP",
        application_area="AREA",
        other_area_impacts="",
        subsystem="SYS1",
        developer="DEV1",
        team_leader="Leader",
        ndvr_package_name="PKG",
        length="",
        test_coord=False,
        comments="",
        contact_number="",
        import_id="",
        import_date=None,
        major_functions="",
        minor_functions="",
        project_merge_region="Region Proper",
        misc_system="System Proper",
        misc_region="Region Proper",
        misc_lookup_source="region_prefix",
        misc_lookup_detail="Bundle.Sequence/TestEnvironment=1057/42",
        bundle_id="BUNDLE-1057",
        bundle_sequence=1057,
    )


class FakeSmtp:
    instances: list["FakeSmtp"] = []

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.started_tls = False
        self.login_args: tuple[str, str] | None = None
        self.messages = []
        FakeSmtp.instances.append(self)

    def __enter__(self) -> "FakeSmtp":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def starttls(self) -> None:
        self.started_tls = True

    def login(self, username: str, password: str) -> None:
        self.login_args = (username, password)

    def send_message(self, message: object) -> None:
        self.messages.append(message)


class OutputTests(unittest.TestCase):
    def test_issue_csv_excludes_info_and_good_output_keeps_note(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = write_outputs(
                output_root=Path(temp_dir),
                issues=[
                    ValidationIssue(
                        severity=Severity.INFO,
                        code="EFFORT_NOT_ASSIGNED",
                        message="Default placement will be used.",
                        project_code="ABC1234",
                        element="ELM0001",
                        type="BCOB",
                    ),
                    ValidationIssue(
                        severity=Severity.WARNING,
                        code="POTENTIAL_MISTYPE",
                        message="Review project code.",
                        project_code="ABC1234",
                        element="ELM0001",
                        type="BCOB",
                        project_imp_date=date(2026, 7, 20),
                        owner_id="DEV1",
                        owner_email="DEV1@domain.com",
                        cc_email="TL01@domain.com",
                        bundle_id="DEFAULT-JULY",
                        bundle_sequence=99,
                        bundle_prod_date=date(2026, 7, 31),
                        effort_team_lead="TL99",
                    ),
                    ValidationIssue(
                        severity=Severity.ERROR,
                        code="ELEMENT_IMP_DATE_MISMATCH",
                        message="Element implementation date must match the Project implementation date.",
                        project_code="ABC1234",
                        element="ELM0002",
                        type="BCOB",
                        project_imp_date=date(2026, 7, 20),
                        element_imp_date=date(2026, 7, 21),
                        owner_id="DEV2",
                        owner_email="DEV2@domain.com",
                        cc_email="TL01@domain.com",
                    ),
                ],
                good_elements=[_element()],
                write_csv=True,
                write_xlsx=False,
                write_email_drafts=True,
            )

            issues = pd.read_csv(run_dir / "validation_issues.csv")
            good_rows = pd.read_csv(run_dir / "consolidated_inventory_source.csv")
            draft = (run_dir / "email_drafts" / "ABC1234.txt").read_text(
                encoding="utf-8",
            )
            instructions = (
                run_dir / "email_drafts" / "issue_resolution_instructions.txt"
            ).read_text(
                encoding="utf-8",
            )

            self.assertEqual(set(issues["severity"]), {"ERROR", "WARNING"})
            self.assertIn("EFFORT_NOT_ASSIGNED", good_rows["Validation Notes"][0])
            self.assertEqual(good_rows["Merge Region"][0], "Region Proper")
            self.assertEqual(good_rows["System"][0], "System Proper")
            self.assertEqual(good_rows["Region"][0], "Region Proper")
            self.assertEqual(good_rows["Bundle Id"][0], "BUNDLE-1057")
            self.assertEqual(good_rows["Bundle Sequence"][0], 1057)
            self.assertEqual(good_rows["Misc Lookup Source"][0], "region_prefix")
            self.assertIn("TestEnvironment=1057/42", good_rows["Misc Lookup Detail"][0])
            self.assertIn("Subject: Inventory data issues need review - ABC1234", draft)
            self.assertIn("To: DEV1@domain.com, DEV2@domain.com", draft)
            self.assertIn("Cc: TL01@domain.com", draft)
            self.assertIn("RSET Data", draft)
            self.assertIn("Associated Bundle: DEFAULT-JULY", draft)
            self.assertIn("Bundle Prod Date: 2026-07-31", draft)
            self.assertIn("PID Data", draft)
            self.assertIn("Project Imp Date: 2026-07-20", draft)
            self.assertIn("Effort Team Lead(s): TL99", draft)
            self.assertIn("Owner: DEV1 <DEV1@domain.com>", draft)
            self.assertIn("Owner: DEV2 <DEV2@domain.com>", draft)
            self.assertIn("Owner=DEV1 <DEV1@domain.com>", draft)
            self.assertIn("TeamLead=TL01@domain.com", draft)
            self.assertIn("Element Imp Date=2026-07-21", draft)
            self.assertIn("Review the project draft for your Project Code.", instructions)

    def test_date_mismatch_email_does_not_show_assignment_context(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = write_outputs(
                output_root=Path(temp_dir),
                issues=[
                    ValidationIssue(
                        severity=Severity.ERROR,
                        code="ELEMENT_IMP_DATE_MISMATCH",
                        message="Element implementation date must match the Project implementation date.",
                        project_code="RD8560",
                        element="ELM0001",
                        type="BCOB",
                        project_imp_date=date(2026, 7, 12),
                        element_imp_date=date(2026, 7, 19),
                        owner_email="DEV1@domain.com",
                    ),
                ],
                good_elements=[],
                write_csv=True,
                write_xlsx=False,
                write_email_drafts=True,
            )

            draft = (run_dir / "email_drafts" / "RD8560.txt").read_text(
                encoding="utf-8",
            )

            self.assertIn("Project: RD8560", draft)
            self.assertIn("Associated Bundle: N/A", draft)
            self.assertIn("Bundle Prod Date: N/A", draft)
            self.assertIn("Project Imp Date: 2026-07-12", draft)
            self.assertIn("Element Imp Date=2026-07-19", draft)

    def test_date_mismatch_email_shows_existing_effort_bundle_context(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = write_outputs(
                output_root=Path(temp_dir),
                issues=[
                    ValidationIssue(
                        severity=Severity.ERROR,
                        code="ELEMENT_IMP_DATE_MISMATCH",
                        message="Element implementation date must match the Project implementation date.",
                        project_code="RD8560",
                        element="ELM0001",
                        type="BCOB",
                        project_imp_date=date(2026, 7, 12),
                        element_imp_date=date(2026, 7, 19),
                        owner_email="DEV1@domain.com",
                        bundle_id="BUNDLE-1057",
                        bundle_sequence=1057,
                        bundle_prod_date=date(2026, 6, 19),
                        effort_prod_date=date(2026, 6, 19),
                        effort_team_lead="RDTL",
                    ),
                ],
                good_elements=[],
                write_csv=True,
                write_xlsx=False,
                write_email_drafts=True,
            )

            draft = (run_dir / "email_drafts" / "RD8560.txt").read_text(
                encoding="utf-8",
            )

            self.assertIn("Associated Bundle: BUNDLE-1057", draft)
            self.assertIn("Bundle Sequence: 1057", draft)
            self.assertIn("Bundle Prod Date: 2026-06-19", draft)
            self.assertIn("Effort Team Lead(s): RDTL", draft)

    def test_good_csv_is_always_written(self) -> None:
        with TemporaryDirectory() as temp_dir:
            run_dir = write_outputs(
                output_root=Path(temp_dir),
                issues=[],
                good_elements=[_element()],
                write_csv=False,
                write_xlsx=False,
                write_email_drafts=False,
            )

            self.assertTrue((run_dir / "consolidated_inventory_source.csv").exists())
            self.assertFalse((run_dir / "validation_issues.csv").exists())

    def test_send_project_emails_uses_smtp_settings(self) -> None:
        FakeSmtp.instances.clear()

        sent_count = send_project_emails(
            [
                ValidationIssue(
                    severity=Severity.WARNING,
                    code="POTENTIAL_MISTYPE",
                    message="Review project code.",
                    project_code="ABC1234",
                    element="ELM0001",
                    type="BCOB",
                    owner_id="DEV1",
                    owner_email="DEV1@domain.com",
                    cc_email="TL01@domain.com",
                ),
            ],
            EmailSettings(
                domain="domain.com",
                from_address="inventory-validation@domain.com",
                smtp_host="smtp.domain.com",
                smtp_port=2525,
                smtp_username="smtp-user",
                smtp_password="smtp-pass",
                smtp_use_tls=True,
            ),
            smtp_factory=FakeSmtp,
        )

        self.assertEqual(sent_count, 1)
        smtp = FakeSmtp.instances[0]
        self.assertEqual(smtp.host, "smtp.domain.com")
        self.assertEqual(smtp.port, 2525)
        self.assertTrue(smtp.started_tls)
        self.assertEqual(smtp.login_args, ("smtp-user", "smtp-pass"))
        message = smtp.messages[0]
        self.assertEqual(message["From"], "inventory-validation@domain.com")
        self.assertEqual(message["To"], "DEV1@domain.com")
        self.assertEqual(message["Cc"], "TL01@domain.com")
        self.assertEqual(
            message["Subject"],
            "Inventory data issues need review - ABC1234",
        )
        self.assertIn("Resolution Instructions", message.get_content())


if __name__ == "__main__":
    unittest.main()
