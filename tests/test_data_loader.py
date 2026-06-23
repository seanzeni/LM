from __future__ import annotations
from pathlib import Path
import pandas as pd
import pytest
from app.services.data_loader import DataLoader
REQUIRED_COLUMNS=['Release','Project','Element','Type','Subsys','System','Act Rgn']

def test_data_loader_loads_excel_and_releases(tmp_path: Path) -> None:
    path=tmp_path/'inventory.xlsx'
    pd.DataFrame([{'Release':' REL1 ','Project':'ABC','Element':'PGM001','Type':'OCOB','Subsys':'SUB1','System':'SYS1','Act Rgn':'DV'},{'Release':'REL2','Project':'XYZ','Element':'PGM002','Type':'JCL','Subsys':'SUB2','System':'SYS2','Act Rgn':'LO'}]).to_excel(path,index=False)
    loader=DataLoader(path, REQUIRED_COLUMNS); loader.load()
    assert loader.get_releases() == ['REL1','REL2']
    assert len(loader.filter_release('REL1')) == 1

def test_missing_column_raises(tmp_path: Path) -> None:
    path=tmp_path/'inventory.xlsx'; pd.DataFrame([{'Release':'REL1'}]).to_excel(path,index=False)
    with pytest.raises(Exception): DataLoader(path, REQUIRED_COLUMNS).load()

def test_filter_release_projects(tmp_path: Path) -> None:
    path=tmp_path/'inventory.xlsx'
    pd.DataFrame([{'Release':'REL1','Project':'ABC','Element':'PGM001','Type':'OCOB','Subsys':'SUB1','System':'SYS1','Act Rgn':'DV'},{'Release':'REL1','Project':'XYZ','Element':'PGM002','Type':'JCL','Subsys':'SUB2','System':'SYS2','Act Rgn':'LO'}]).to_excel(path,index=False)
    loader=DataLoader(path, REQUIRED_COLUMNS); loader.load(); df=loader.filter_release_projects('REL1', {'ABC'})
    assert len(df)==1 and df.iloc[0]['Project']=='ABC'
