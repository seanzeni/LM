from __future__ import annotations
import pandas as pd
from app.services.element_service import ElementService


def make_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Release": "REL1",
                "Project": "ABC",
                "Element": "PGM001",
                "Type": "OCOB",
                "Subsys": "SUB1",
                "System": "SYS1",
                "Act Rgn": "DV",
            },
            {
                "Release": "REL1",
                "Project": "ABC",
                "Element": "PGM001",
                "Type": "OAPS",
                "Subsys": "SUB1",
                "System": "SYS1",
                "Act Rgn": "DV",
            },
            {
                "Release": "REL1",
                "Project": "XYZ",
                "Element": "PGM002",
                "Type": "JCL",
                "Subsys": "SUB2",
                "System": "SYS2",
                "Act Rgn": "LO",
            },
        ]
    )


def test_build_elements() -> None:
    elements = ElementService().build_elements(make_dataframe())
    assert len(elements) == 3
    assert elements[0].release == "REL1"
    assert elements[0].project == "ABC"
    assert elements[0].element == "PGM001"
    assert elements[0].type == "OCOB"


def test_build_element_lookup() -> None:
    service = ElementService()
    elements = service.build_elements(make_dataframe())
    assert len(service.build_element_lookup(elements)[("PGM001", "OCOB")]) == 1


def test_build_project_lookup() -> None:
    service = ElementService()
    elements = service.build_elements(make_dataframe())
    assert len(service.build_project_lookup(elements)["ABC"]) == 2


def test_build_element_name_type_lookup() -> None:
    service = ElementService()
    elements = service.build_elements(make_dataframe())
    assert service.build_element_name_type_lookup(elements)["PGM001"] == {
        "OCOB",
        "OAPS",
    }
