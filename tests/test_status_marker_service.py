from __future__ import annotations
from app.core.models import Element
from app.services.status_marker_service import StatusMarkerService

def make_service() -> StatusMarkerService:
    return StatusMarkerService(status_markers={"marker_columns":["Package"],"do_not_move":["DO NOT MOVE"],"already_in_prod":["PROD"],"already_in_qual":["QUAL"]})

def make_element(package: str) -> Element:
    return Element(release="REL", project="ABC", element="PGM001", type="OCOB", source_row={"Package": package})

def test_get_marker_text_reads_configured_columns() -> None:
    assert make_service().get_marker_text(make_element("already PROD")) == "already PROD"

def test_is_do_not_move() -> None:
    assert make_service().is_do_not_move(make_element("DO NOT MOVE")) is True

def test_is_marked_prod() -> None:
    service = make_service()
    assert service.is_marked_prod(make_element("already PROD")) is True
    assert service.is_marked_for_target(make_element("already PROD"), "PROD") is True

def test_is_marked_qual() -> None:
    service = make_service()
    assert service.is_marked_qual(make_element("already QUAL")) is True
    assert service.is_marked_for_target(make_element("already QUAL"), "QUAL") is True

def test_get_target_marker_text() -> None:
    service = make_service()
    assert service.get_target_marker_text(make_element("already PROD"), "PROD") == "PROD"
    assert service.get_target_marker_text(make_element("already QUAL"), "QUAL") == "QUAL"
    assert service.get_target_marker_text(make_element("normal"), "PROD") == ""
