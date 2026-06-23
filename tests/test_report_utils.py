from __future__ import annotations
from pathlib import Path
from app.core.models import ArchiveStatus, Element
from app.reports.report_utils import archive_existing_reports, get_date_folder, safe_release_name, sort_elements

def test_safe_release_name_replaces_unsafe_chars() -> None:
    assert safe_release_name('REL 2026/06') == 'REL_2026_06'

def test_get_date_folder_creates_folder(tmp_path: Path) -> None:
    folder=get_date_folder('REL1', tmp_path)
    assert folder.exists()
    assert folder.parent.name == 'REL1'

def test_archive_existing_reports_moves_files(tmp_path: Path) -> None:
    report=tmp_path/'report.csv'; report.write_text('data', encoding='utf-8')
    archive_existing_reports(tmp_path)
    assert not report.exists()
    assert (tmp_path/'History'/'report.csv').exists()

def test_sort_elements_excludes_hidden_and_orders_errors_first() -> None:
    error=Element(release='REL', project='ABC', element='ZZZ', type='OCOB', archive_status=ArchiveStatus.POTENTIAL_MISSING_ARCHIVE)
    info=Element(release='REL', project='ABC', element='AAA', type='OCOB')
    hidden=Element(release='REL', project='ABC', element='BBB', type='OCOB', visible=False)
    assert sort_elements([info, hidden, error]) == [error, info]
