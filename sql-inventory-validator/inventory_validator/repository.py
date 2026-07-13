from __future__ import annotations

from .config import AppConfig
from .models import Bundle, Effort, Employee, ElementRecord, MiscSystemRegion
from .models import Project, Region
from .normalization import clean, parse_bool, parse_date, parse_datetime, parse_int
from .sql_service import SqlService


class InventoryRepository:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.prod = SqlService(config.prod_inventory)
        self.rset = SqlService(config.rset)

    def load_employees(self) -> list[Employee]:
        rows = self.prod.fetch_all(
            self.config.tables.get("employees", "Employees"),
            ["Developer", "First Name", "Last Name", "Position"],
        )
        domain = self.config.email.domain
        return [
            Employee(
                developer=clean(row.get("Developer")),
                first_name=clean(row.get("First Name")),
                last_name=clean(row.get("Last Name")),
                position=clean(row.get("Position")),
                email=f"{clean(row.get('Developer'))}@{domain}"
                if clean(row.get("Developer"))
                else "",
            )
            for row in rows
        ]

    def load_projects(self) -> list[Project]:
        rows = self.prod.fetch_all(
            self.config.tables.get("projects", "Projects"),
            [
                "Project Code",
                "CCID",
                "Project Name",
                "Team Leader",
                "Merge Region",
                "Imp Date",
            ],
        )
        return [
            Project(
                project_code=clean(row.get("Project Code")),
                ccid=clean(row.get("CCID")),
                project_name=clean(row.get("Project Name")),
                team_leader=clean(row.get("Team Leader")),
                merge_region=clean(row.get("Merge Region")),
                imp_date=parse_date(row.get("Imp Date")),
            )
            for row in rows
        ]

    def load_elements(self) -> list[ElementRecord]:
        rows = self.prod.fetch_all(
            self.config.tables.get("elements", "Elements"),
            [
                "Project Code",
                "Imp Date",
                "New Element",
                "Online",
                "Binds Required",
                "Trans ID",
                "Element",
                "Type",
                "Processor Group",
                "Application",
                "Application Area",
                "Other Area Impacts",
                "Subsystem",
                "Developer",
                "Team Leader",
                "NDVR Package Name",
                "Length",
                "Test Coord",
                "Comments",
                "Contact Number",
                "ImportID",
                "ImportDate",
                "MajorFunctions",
                "MinorFunctions",
            ],
        )
        return [
            ElementRecord(
                project_code=clean(row.get("Project Code")),
                imp_date=parse_date(row.get("Imp Date")),
                new_element=parse_bool(row.get("New Element")),
                online=parse_bool(row.get("Online")),
                binds_required=parse_bool(row.get("Binds Required")),
                trans_id=clean(row.get("Trans ID")),
                element=clean(row.get("Element")),
                type=clean(row.get("Type")),
                processor_group=clean(row.get("Processor Group")),
                application=clean(row.get("Application")),
                application_area=clean(row.get("Application Area")),
                other_area_impacts=clean(row.get("Other Area Impacts")),
                subsystem=clean(row.get("Subsystem")),
                developer=clean(row.get("Developer")),
                team_leader=clean(row.get("Team Leader")),
                ndvr_package_name=clean(row.get("NDVR Package Name")),
                length=clean(row.get("Length")),
                test_coord=parse_bool(row.get("Test Coord")),
                comments=clean(row.get("Comments")),
                contact_number=clean(row.get("Contact Number")),
                import_id=clean(row.get("ImportID")),
                import_date=parse_datetime(row.get("ImportDate")),
                major_functions=clean(row.get("MajorFunctions")),
                minor_functions=clean(row.get("MinorFunctions")),
                source_row=dict(row),
            )
            for row in rows
        ]

    def load_efforts(self) -> list[Effort]:
        rows = self.rset.fetch_all(
            self.config.tables.get("efforts", "Efforts"),
            [
                "Id",
                "BundleSequence",
                "TeamLead",
                "BundleMergeDate",
                "BundleQualMoveDate",
                "BundleProdMoveDate",
                "BundleExitDate",
            ],
        )
        return [
            Effort(
                id=clean(row.get("Id")),
                bundle_sequence=parse_int(row.get("BundleSequence")),
                team_lead=clean(row.get("TeamLead")),
                bundle_merge_date=parse_date(row.get("BundleMergeDate")),
                bundle_qual_move_date=parse_date(row.get("BundleQualMoveDate")),
                bundle_prod_move_date=parse_date(row.get("BundleProdMoveDate")),
                bundle_exit_date=parse_date(row.get("BundleExitDate")),
            )
            for row in rows
        ]

    def load_bundles(self) -> list[Bundle]:
        rows = self.rset.fetch_all(
            self.config.tables.get("bundles", "Bundles"),
            ["Id", "Sequence", "TestEnvironment", "BundleProdImpDate"],
        )
        return [
            Bundle(
                id=clean(row.get("Id")),
                sequence=parse_int(row.get("Sequence")),
                test_environment=parse_int(row.get("TestEnvironment")) or 0,
                bundle_prod_imp_date=parse_date(row.get("BundleProdImpDate")),
            )
            for row in rows
        ]

    def load_regions(self) -> list[Region]:
        rows = self.rset.fetch_all(
            self.config.tables.get("regions", "Regions"),
            ["Id", "TestEnvironment"],
        )
        return [
            Region(
                id=clean(row.get("Id")),
                test_environment=parse_int(row.get("TestEnvironment")) or 0,
            )
            for row in rows
        ]

    def load_misc_system_regions(self) -> list[MiscSystemRegion]:
        rows = self.rset.fetch_all(
            self.config.tables.get("misc_system_region", "MiscSystemRegion"),
            ["System", "Region"],
        )
        return [
            MiscSystemRegion(
                system=clean(row.get("System")),
                region=clean(row.get("Region")),
            )
            for row in rows
        ]

