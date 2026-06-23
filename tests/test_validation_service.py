from __future__ import annotations
from app.core.models import (
    ArchiveStatus,
    Element,
    FixStatus,
    InventoryStatus,
    LocationStatus,
    MovementStatus,
    ReleaseEffort,
    ScheduleStatus,
)
from app.services.status_marker_service import StatusMarkerService
from app.services.validation_service import ValidationService


class FakeLocationService:
    def __init__(self, env_records: set[tuple[str, str, str]]) -> None:
        self.env_records = {
            (e.upper(), t.upper(), v.upper()) for e, t, v in env_records
        }

    def exists_in_env(self, element: str, type_: str, env: str) -> bool:
        return (element.upper(), type_.upper(), env.upper()) in self.env_records

    def exists_in_fixp1(self, element: str, type_: str) -> bool:
        return self.exists_in_env(element, type_, "FIXP1")


def make_service() -> ValidationService:
    marker_service = StatusMarkerService(
        status_markers={
            "marker_columns": ["Package"],
            "do_not_move": ["DO NOT MOVE"],
            "already_in_prod": ["PROD"],
            "already_in_qual": ["QUAL"],
        }
    )
    return ValidationService(
        selection_rules={
            "overlap_selectable": False,
            "duplicate_selectable": False,
            "missing_ndvr_selectable": False,
            "inventory_not_in_release_selectable": True,
            "inventory_when_sql_no_inventory_selectable": True,
            "effort_release_mismatch_selectable": True,
            "potential_missing_archive_selectable": False,
            "potential_missing_program_move_selectable": True,
            "do_not_move_selectable": False,
            "marked_already_there_missing_selectable": True,
        },
        archive_pairs=[["OAPS", "OCOB"], ["XAPS", "XCOB"]],
        status_marker_service=marker_service,
    )


def make_element(
    element="PGM001", type_="OCOB", project="ABC", release="REL1", package=""
) -> Element:
    return Element(
        release=release,
        project=project,
        element=element,
        type=type_,
        source_row={"Package": package},
    )


def test_overlap_status() -> None:
    elements = [make_element(project="ABC"), make_element(project="XYZ")]
    make_service().apply_overlap_duplicate_status(elements)
    assert all(e.inventory_status == InventoryStatus.OVERLAP for e in elements)


def test_duplicate_status() -> None:
    elements = [make_element(project="ABC"), make_element(project="ABC")]
    make_service().apply_overlap_duplicate_status(elements)
    assert all(e.inventory_status == InventoryStatus.DUPLICATE for e in elements)


def test_inventory_not_in_release_status() -> None:
    element = make_element(project="NOTSQL")
    make_service().apply_schedule_status(
        [element], [ReleaseEffort(effort_id="ABC")], {}, "REL1"
    )
    assert element.schedule_status == ScheduleStatus.INVENTORY_NOT_IN_RELEASE


def test_no_inventory_with_inventory_status() -> None:
    element = make_element(project="ABC")
    make_service().apply_schedule_status(
        [element], [ReleaseEffort(effort_id="ABC", no_inventory=True)], {}, "REL1"
    )
    assert element.schedule_status == ScheduleStatus.INVENTORY_WHEN_SQL_NO_INVENTORY


def test_wrong_release_status() -> None:
    element = make_element(project="ABC", release="REL1")
    make_service().apply_schedule_status(
        [element], [ReleaseEffort(effort_id="ABC")], {"ABC": "REL2"}, "REL1"
    )
    assert element.schedule_status == ScheduleStatus.EFFORT_RELEASE_MISMATCH


def test_missing_location_status() -> None:
    element = make_element()
    make_service().apply_location_status([element], FakeLocationService(set()), "PROD")
    assert element.location_status == LocationStatus.NOT_FOUND


def test_found_location_status() -> None:
    element = make_element()
    make_service().apply_location_status(
        [element], FakeLocationService({("PGM001", "OCOB", "PROD1")}), "PROD"
    )
    assert element.location_status == LocationStatus.FOUND


def test_missing_archive_rule_opposite_type_exists_in_prod_and_missing_inventory() -> (
    None
):
    element = make_element(type_="OCOB")
    make_service().apply_archive_status(
        [element], FakeLocationService({("PGM001", "OAPS", "PROD1")}), "PROD"
    )
    assert element.archive_status == ArchiveStatus.POTENTIAL_MISSING_ARCHIVE


def test_missing_archive_rule_does_not_fire_when_opposite_type_in_inventory() -> None:
    elements = [make_element(type_="OCOB"), make_element(type_="OAPS")]
    make_service().apply_archive_status(
        elements, FakeLocationService({("PGM001", "OAPS", "PROD1")}), "PROD"
    )
    assert elements[0].archive_status == ArchiveStatus.OK


def test_missing_program_move_archive_side_in_inventory_program_side_in_qual_missing_inventory() -> (
    None
):
    element = make_element(type_="OAPS")
    make_service().apply_archive_status(
        [element], FakeLocationService({("PGM001", "OCOB", "QUAL1")}), "PROD"
    )
    assert element.archive_status == ArchiveStatus.POTENTIAL_MISSING_PROGRAM_MOVE


def test_missing_program_move_only_prod() -> None:
    element = make_element(type_="OAPS")
    make_service().apply_archive_status(
        [element], FakeLocationService({("PGM001", "OCOB", "QUAL1")}), "QUAL"
    )
    assert element.archive_status == ArchiveStatus.OK


def test_fixp1_warning_never_blocks_by_itself() -> None:
    element = make_element()
    service = make_service()
    service.apply_fixp1_status(
        [element], FakeLocationService({("PGM001", "OCOB", "FIXP1")}), "PROD"
    )
    service.apply_selection_rules([element])
    assert element.fix_status == FixStatus.EXISTS_IN_FIXP1
    assert element.selected is True and element.selectable is True


def test_do_not_move_marker_info_hidden_unselectable() -> None:
    element = make_element(package="DO NOT MOVE")
    service = make_service()
    service.apply_movement_status([element], FakeLocationService(set()), "PROD")
    service.apply_selection_rules([element])
    assert element.movement_status == MovementStatus.DO_NOT_MOVE
    assert element.selected is False and element.selectable is False


def test_confirmed_already_in_target_hidden() -> None:
    element = make_element(package="PROD")
    service = make_service()
    service.apply_movement_status(
        [element], FakeLocationService({("PGM001", "OCOB", "PROD1")}), "PROD"
    )
    service.apply_selection_rules([element])
    assert element.source_row["_confirmed_already_in_target"] is True
    assert (
        element.visible is False
        and element.selected is False
        and element.selectable is False
    )


def test_marked_already_there_but_missing_warning_selectable() -> None:
    element = make_element(package="PROD")
    service = make_service()
    service.apply_movement_status([element], FakeLocationService(set()), "PROD")
    service.apply_selection_rules([element])
    assert element.movement_status == MovementStatus.MARKED_ALREADY_THERE_BUT_MISSING
    assert element.selected is False and element.selectable is True


def test_build_inventory_issues_for_missing_expected_inventory() -> None:
    issues = make_service().build_inventory_issues(
        "REL1", [], [ReleaseEffort(effort_id="ABC", no_inventory=False)]
    )
    assert len(issues) == 1
    assert issues[0].issue_type == ScheduleStatus.SQL_EXPECTED_INVENTORY_MISSING
