from __future__ import annotations

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

from inventory_validator.models import ElementRecord, Severity, ValidationIssue
from inventory_validator.outputs import write_outputs


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
        project_merge_region="RGN-A",
        misc_system="System Proper",
        misc_region="Region Proper",
    )


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
                        owner_email="DEV1@domain.com",
                        cc_email="TL01@domain.com",
                        bundle_id="DEFAULT-JULY",
                        bundle_sequence=99,
                        bundle_prod_date=date(2026, 7, 31),
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
                        owner_email="DEV1@domain.com",
                        cc_email="TL01@domain.com",
                        bundle_id="DEFAULT-JULY",
                        bundle_sequence=99,
                        bundle_prod_date=date(2026, 7, 31),
                    ),
                ],
                good_elements=[_element()],
                write_csv=True,
                write_xlsx=False,
                write_email_drafts=True,
            )

            issues = pd.read_csv(run_dir / "validation_issues.csv")
            good_rows = pd.read_csv(run_dir / "consolidated_inventory_source.csv")
            draft = (run_dir / "email_drafts" / "DEV1_at_domain_com.txt").read_text(
                encoding="utf-8",
            )

            self.assertEqual(set(issues["severity"]), {"ERROR", "WARNING"})
            self.assertIn("EFFORT_NOT_ASSIGNED", good_rows["Validation Notes"][0])
            self.assertEqual(good_rows["Merge Region"][0], "RGN-A")
            self.assertEqual(good_rows["System"][0], "System Proper")
            self.assertEqual(good_rows["Region"][0], "Region Proper")
            self.assertIn("Cc: TL01@domain.com", draft)
            self.assertIn("Associated Bundle: DEFAULT-JULY", draft)
            self.assertIn("Bundle Prod Date: 2026-07-31", draft)
            self.assertIn("Project Imp Date: 2026-07-20", draft)
            self.assertIn("Element Imp Date=2026-07-21", draft)


if __name__ == "__main__":
    unittest.main()
