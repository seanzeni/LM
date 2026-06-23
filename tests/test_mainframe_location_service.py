from __future__ import annotations
from pathlib import Path
import pytest
from app.services.mainframe_location_service import MainframeLocationService

def make_line(element: str, type_: str, subsystem: str, system: str, env: str, version: str) -> str:
    fields=[(element,8),(type_,8),(subsystem,8),(system,4),(env,5),("2026/06/22",10),("12:00:00:00",11),(version,5),("USER01",8),("CCID01",7),("COMMENTS",40)]
    return " ".join(value.ljust(width)[:width] for value,width in fields)

def test_load_file_and_find(tmp_path: Path) -> None:
    path=tmp_path/"locations.txt"; path.write_text("\n".join([make_line("PGM001","OCOB","SUB1","SYS1","QUAL1","01.02"), make_line("PGM001","OCOB","SUB1","SYS1","PROD1","01.01")]), encoding="cp1252")
    service=MainframeLocationService().load_file(path)
    assert len(service.records)==2
    assert service.exists("PGM001","OCOB") is True
    assert service.exists_in_env("PGM001","OCOB","QUAL1") is True
    assert service.exists_in_env("PGM001","OCOB","FIXP1") is False

def test_exists_in_fixp1(tmp_path: Path) -> None:
    path=tmp_path/"locations.txt"; path.write_text(make_line("PGM001","OCOB","SUB1","SYS1","FIXP1","01.01"), encoding="cp1252")
    assert MainframeLocationService().load_file(path).exists_in_fixp1("PGM001","OCOB") is True

def test_resync_excludes_fixp1(tmp_path: Path) -> None:
    path=tmp_path/"locations.txt"; path.write_text("\n".join([make_line("PGM001","OCOB","SUB1","SYS1","QUAL1","01.01"), make_line("PGM001","OCOB","SUB1","SYS1","FIXP1","99.99")]), encoding="cp1252")
    assert MainframeLocationService().load_file(path).has_resync_issue("PGM001","OCOB") is False

def test_invalid_version_raises(tmp_path: Path) -> None:
    path=tmp_path/"locations.txt"; path.write_text(make_line("PGM001","OCOB","SUB1","SYS1","QUAL1","BAD"), encoding="cp1252")
    with pytest.raises(ValueError): MainframeLocationService().load_file(path)
