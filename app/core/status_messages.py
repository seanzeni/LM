from __future__ import annotations

"""
Purpose:
    Centralized validation and status reason messages.

Used By:
    ValidationService
    Reports
    UI

Notes:
    Do not hardcode user-facing validation messages in services or reports.
"""


class StatusMessages:
    OVERLAP = "Element/type overlaps with another project."
    DUPLICATE = "Element/type is duplicated within inventory."
    MISSING_NDVR = "Element/type was not found in the expected NDVR location."

    INVENTORY_NOT_IN_RELEASE = "Project is not connected to this release bundle."
    INVENTORY_WHEN_SQL_NO_INVENTORY = (
        "RSET says this project should not have inventory, but inventory rows exist."
    )
    SQL_EXPECTED_INVENTORY_MISSING = (
        "RSET expected inventory for this project, but no inventory rows were found."
    )
    EFFORT_RELEASE_MISMATCH = (
        "Inventory identified bundle does not match the RSET bundle for this project."
    )

    POTENTIAL_MISSING_ARCHIVE = (
        "Potential archive element may be missing for PROD movement."
    )
    POTENTIAL_MISSING_PROGRAM_MOVE = (
        "Potential program move may be missing for PROD movement."
    )

    EXISTS_IN_FIXP1 = "Element/type also exists in FIXP1."

    DO_NOT_MOVE = "Element is marked do not move."
    MARKED_ALREADY_THERE_BUT_MISSING = (
        "Element is marked already in target environment, but was not found there."
    )


class ReasonBuilder:
    @staticmethod
    def overlap(
        element: str,
        type_: str,
        project: str,
        other_projects: list[str],
    ) -> str:
        return (
            f"{StatusMessages.OVERLAP} "
            f"{element} {type_} in project {project} also appears in: "
            f"{', '.join(other_projects)}."
        )

    @staticmethod
    def duplicate(
        element: str,
        type_: str,
        project: str,
    ) -> str:
        return (
            f"{StatusMessages.DUPLICATE} "
            f"{element} {type_} appears more than once in project {project}."
        )

    @staticmethod
    def missing_ndvr(
        element: str,
        type_: str,
        expected_env: str,
    ) -> str:
        return (
            f"{StatusMessages.MISSING_NDVR} "
            f"Expected {element} {type_} to exist in {expected_env}."
        )

    @staticmethod
    def inventory_not_in_release(
        project: str,
        release: str,
    ) -> str:
        return (
            f"{StatusMessages.INVENTORY_NOT_IN_RELEASE} "
            f"Project {project} is present in inventory for release bundle [{release}], "
            f"but RSET does not list it on this release bundle."
        )

    @staticmethod
    def inventory_when_sql_no_inventory(
        project: str,
        release: str,
    ) -> str:
        return (
            f"{StatusMessages.INVENTORY_WHEN_SQL_NO_INVENTORY} "
            f"Project {project} has inventory rows for release bundle [{release}], "
            f"but RSET marks this project as not having an inventory."
        )

    @staticmethod
    def sql_expected_inventory_missing(
        project: str,
        release: str,
    ) -> str:
        return (
            f"{StatusMessages.SQL_EXPECTED_INVENTORY_MISSING} "
            f"Project {project} is on the RSET bundle release schedule for [{release}], "
            f"but no inventory rows were found."
        )

    @staticmethod
    def effort_release_mismatch(
        project: str,
        inventory_release: str,
        sql_release: str,
    ) -> str:
        return (
            f"{StatusMessages.EFFORT_RELEASE_MISMATCH} "
            f"Inventory says project {project} belongs to the release bundle [{inventory_release}], "
            f"but RSET states it belongs to this release [{sql_release}]."
        )

    @staticmethod
    def potential_missing_archive(
        element: str,
        moving_type: str,
        opposite_type: str,
        env: str,
    ) -> str:
        return (
            f"{StatusMessages.POTENTIAL_MISSING_ARCHIVE} "
            f"Moving {element} {moving_type}. "
            f"Found {element} {opposite_type} in {env}, "
            f"but {element} {opposite_type} is not present in the selected inventory."
        )

    @staticmethod
    def potential_missing_program_move(
        element: str,
        archive_type: str,
        program_type: str,
        env: str,
    ) -> str:
        return (
            f"{StatusMessages.POTENTIAL_MISSING_PROGRAM_MOVE} "
            f"Moving archive {element} {archive_type}. "
            f"Found opposite program type {element} {program_type} in {env}, "
            f"but {element} {program_type} is not present in the selected inventory."
        )

    @staticmethod
    def exists_in_fixp1(
        element: str,
        type_: str,
    ) -> str:
        return (
            f"{StatusMessages.EXISTS_IN_FIXP1} "
            f"{element} {type_} also exists in FIXP1. "
            f"Verify emergency fix path before PROD move."
        )

    @staticmethod
    def do_not_move(
        element: str,
        type_: str,
        marker_text: str,
    ) -> str:
        return (
            f"{StatusMessages.DO_NOT_MOVE} "
            f"{element} {type_} has marked '{marker_text}'."
        )

    @staticmethod
    def marked_already_there_but_missing(
        element: str,
        type_: str,
        target_env: str,
        marker_text: str,
    ) -> str:
        return (
            f"{StatusMessages.MARKED_ALREADY_THERE_BUT_MISSING} "
            f"{element} {type_} has marker '{marker_text}', "
            f"but it was not found in {target_env}."
        )
