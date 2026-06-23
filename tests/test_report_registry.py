from __future__ import annotations
from pathlib import Path
import pytest
from app.core.app_state import AppState
from app.core.models import Element
from app.reports.report_registry import ReportRegistry
from app.services.stats_service import StatsService

def make_registry() -> ReportRegistry:
    stats=StatsService(workload_settings={"default_thread_count":1,"type_categories":{"JCL":["JCL"],"NON_COMPILE":["PROC"],"COBOL":["OCOB"],"APS":["OAPS"],"X_ELEMENTS":["XML"],"LINKDECK":["LINK"]},"types_per_hour_per_thread":{"PROD":{"JCL":30,"NON_COMPILE":20,"COBOL":10,"APS":5,"X_ELEMENTS":10,"LINKDECK":10}}})
    return ReportRegistry(stats_service=stats)

def test_get_names_contains_core_reports() -> None:
    names=make_registry().get_names()
    assert 'Issues Report' in names and 'Effort Summary Report' in names and 'Release Estimate Report' in names and 'Release Inventory Report' in names and 'OSG/COPS Report' in names

def test_unknown_report_raises_key_error() -> None:
    with pytest.raises(KeyError): make_registry().create('Missing Report')

def test_generate_issues_report_csv(tmp_path: Path) -> None:
    state=AppState(release='REL1', mode='PROD', thread_count=1); state.loaded_elements=[Element(release='REL1', project='ABC', element='PGM001', type='OCOB')]
    output=make_registry().generate('Issues Report','csv',state,tmp_path,True)
    assert output is not None and output.exists()

def test_generate_pdf_not_implemented() -> None:
    with pytest.raises(NotImplementedError): make_registry().generate('Issues Report','pdf',AppState(),Path('.'),True)
