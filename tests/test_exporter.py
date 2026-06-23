from __future__ import annotations
from pathlib import Path
from app.core.models import Element
from app.services.exporter import Exporter

def make_element(name: str, selected: bool=True, visible: bool=True) -> Element:
    return Element(release="REL1", project="ABC", element=name, type="OCOB", selected=selected, visible=visible, source_row={"Element":name,"Type":"OCOB","Project":"ABC","DSN ID":"DSN1","Release":"REL1","Subsys":"SUB1","System":"SYSTEM99","Act Rgn":"DV","Application":"APP"})

def test_exporter_sorts_element_name_only() -> None:
    assert [e.element for e in Exporter({}, Path('.')).sort_elements([make_element('ZZZ'), make_element('AAA')])] == ['AAA','ZZZ']

def test_build_lines_excludes_hidden_and_unselected() -> None:
    lines=Exporter({}, Path('.')).build_lines([make_element('AAA'), make_element('BBB', selected=False), make_element('CCC', visible=False)], 'PROD')
    assert len(lines)==1
    assert lines[0][0:8].strip() == 'AAA'

def test_export_writes_file(tmp_path: Path) -> None:
    output_path=tmp_path/'out.txt'
    result=Exporter({}, tmp_path).export([make_element('AAA')], 'PROD', 'REL1', output_path)
    assert result == output_path
    assert output_path.exists()
    assert output_path.read_text(encoding='utf-8')
