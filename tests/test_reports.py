from __future__ import annotations
from pathlib import Path
import csv
from app.core.models import ArchiveStatus, Element, InventoryIssue, ReleaseEffort, ScheduleStatus
from app.reports.effort_summary_report import EffortSummaryReport
from app.reports.issues_report import IssuesReport
from app.reports.osg_cops_report import OsgCopsReport
from app.reports.release_estimate_report import ReleaseEstimateReport
from app.reports.release_inventory_report import ReleaseInventoryReport
from app.services.stats_service import StatsService

def make_stats_service() -> StatsService:
    return StatsService(workload_settings={"default_thread_count":1,"type_categories":{"JCL":["JCL"],"NON_COMPILE":["PROC"],"COBOL":["OCOB"],"APS":["OAPS"],"X_ELEMENTS":["XML"],"LINKDECK":["LINK"]},"types_per_hour_per_thread":{"PROD":{"JCL":30,"NON_COMPILE":20,"COBOL":10,"APS":5,"X_ELEMENTS":10,"LINKDECK":10}}})

def make_element(name='OPGM001', type_='OCOB', project='ABC', selected=True, visible=True, archive_status=ArchiveStatus.OK, schedule_status=ScheduleStatus.OK) -> Element:
    e=Element(release='REL1', project=project, element=name, type=type_, selected=selected, visible=visible, archive_status=archive_status, schedule_status=schedule_status, source_row={"Submitter":"USER1","Application":"APP","Package":"PKG","Area":"AREA","Service":"SVC"})
    if archive_status != ArchiveStatus.OK or schedule_status != ScheduleStatus.OK: e.reasons.append('Test reason')
    return e

def read_csv(path: Path) -> list[dict[str,str]]:
    with path.open('r', encoding='utf-8', newline='') as f: return list(csv.DictReader(f))

def test_issues_report_excludes_hidden(tmp_path: Path) -> None:
    output=IssuesReport().generate([make_element(archive_status=ArchiveStatus.POTENTIAL_MISSING_ARCHIVE), make_element(name='OPGM002', visible=False, archive_status=ArchiveStatus.POTENTIAL_MISSING_ARCHIVE)], tmp_path, False)
    rows=read_csv(output)
    assert len(rows)==1 and rows[0]['Element']=='OPGM001'

def test_effort_summary_report_generates_rows(tmp_path: Path) -> None:
    output=EffortSummaryReport(make_stats_service()).generate([make_element(project='ABC', type_='OCOB'), make_element(project='ABC', type_='OAPS')], tmp_path, 'PROD', 1)
    rows=read_csv(output)
    assert len(rows)==1 and rows[0]['Project']=='ABC' and rows[0]['Selected Elements']=='2'

def test_release_estimate_report_generates_total(tmp_path: Path) -> None:
    output=ReleaseEstimateReport(make_stats_service()).generate([make_element(project='ABC', type_='OCOB')], {'ABC':'2026-06-22'}, tmp_path, 'PROD', 1)
    assert read_csv(output)[-1]['Move Date'] == 'TOTAL'

def test_release_inventory_report_missing_inventory(tmp_path: Path) -> None:
    output=ReleaseInventoryReport().generate('REL1','PROD',1,[],[InventoryIssue(release='REL1', effort_id='ABC', issue_type=ScheduleStatus.SQL_EXPECTED_INVENTORY_MISSING, reason='Missing inventory')],[ReleaseEffort(effort_id='ABC')],tmp_path)
    assert read_csv(output)[0]['Inventory Status'] == 'Missing Inventory'

def test_osg_cops_report_filters_selected_visible_o_or_x(tmp_path: Path) -> None:
    output=OsgCopsReport().generate([make_element(name='OPGM001', type_='OCOB'), make_element(name='APGM001', type_='JCL'), make_element(name='XPGM001', type_='XCOB', visible=False)], tmp_path, 'PROD')
    rows=read_csv(output)
    assert len(rows)==1 and rows[0]['Element']=='OPGM001'
