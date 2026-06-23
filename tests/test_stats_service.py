from __future__ import annotations
from app.core.models import Element
from app.services.stats_service import StatsService

def make_service() -> StatsService:
    return StatsService(workload_settings={"default_thread_count":1,"type_categories":{"JCL":["JCL"],"NON_COMPILE":["PROC"],"COBOL":["OCOB","XCOB"],"APS":["OAPS","XAPS"],"X_ELEMENTS":["XML"],"LINKDECK":["LINK"]},"types_per_hour_per_thread":{"PROD":{"JCL":30,"NON_COMPILE":20,"COBOL":10,"APS":5,"X_ELEMENTS":10,"LINKDECK":10},"QUAL":{"JCL":30,"NON_COMPILE":20,"COBOL":10,"APS":5,"X_ELEMENTS":10,"LINKDECK":10}}})

def test_categorize_type_known() -> None:
    assert make_service().categorize_type("OCOB") == "COBOL"

def test_categorize_type_unknown_defaults_to_jcl() -> None:
    assert make_service().categorize_type("UNKNOWN") == "JCL"

def test_hidden_elements_do_not_count() -> None:
    counts = make_service().build_category_counts([Element("REL","ABC","PGM001","OCOB"), Element("REL","ABC","PGM002","OCOB", visible=False)])
    assert counts["COBOL"] == 1

def test_unselected_elements_do_not_count() -> None:
    counts = make_service().build_category_counts([Element("REL","ABC","PGM001","OCOB"), Element("REL","ABC","PGM002","OCOB", selected=False)])
    assert counts["COBOL"] == 1

def test_thread_count_reduces_minutes() -> None:
    service = make_service(); elements = [Element("REL","ABC",f"PGM{i:03}","OCOB") for i in range(10)]
    assert service.build_estimate(elements,"PROD",1)["total_minutes"] == 60
    assert service.build_estimate(elements,"PROD",2)["total_minutes"] == 30

def test_zero_rate_defaults_one_minute_per_element() -> None:
    service = StatsService(workload_settings={"default_thread_count":1,"type_categories":{"JCL":["JCL"]},"types_per_hour_per_thread":{"PROD":{"JCL":0}}})
    estimate = service.build_estimate([Element("REL","ABC","PGM001","JCL"), Element("REL","ABC","PGM002","JCL")], "PROD", 1)
    assert estimate["total_minutes"] == 2
    assert estimate["estimated_time"] == "00:02"
