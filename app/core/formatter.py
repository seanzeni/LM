from __future__ import annotations

"""
Purpose:
    Fixed-width mainframe export formatter to meet REXX program needs.

Used By:
    Exporter
    
Notes:
    Keep record layout changes isolated here.
    
Output:
    Record (Line in file, set to RECORD_SIZE length buffer)
    (COL-START, LENGTH) Data
    (0, 8) Element Name
    (9, 8) Element Type
    (18, 4) TeamLead ID
    (23, 20) Bundle ID
    (46, 4) Subsystem
    (51, 8) System
    (60, 5) Environment [MAIN1,DEVL1,QUAL1,PROD1]
    (66, 8) CCID/Effort/Project
    (75, 113) Application (from inventory)
    (113, 2) "NN" Added to end of comment line
    (115, 150) Filled with SPACES for now.
"""

import math
from typing import Any

RECORD_SIZE = 150  # Record length for output


def clean(
    value: Any,
) -> str:
    if value is None:
        return ""

    if isinstance(value, float) and math.isnan(value):
        return ""

    return str(value)


def fixed(
    value: Any,
    length: int,
) -> str:
    return clean(value).ljust(length)[:length]


def build_record(
    source_row: dict[str, Any],
    mode: str,
) -> str:
    buffer = [" "] * RECORD_SIZE

    def write(
        position: int,
        length: int,
        value: Any,
    ) -> None:
        value_text = fixed(value, length)

        for index in range(length):
            buffer[position + index] = value_text[index]

    write(0, 8, source_row.get("Element", ""))
    write(9, 8, source_row.get("Type", ""))

    # Grab team lead from first 4 characters in DSN ID field.
    team_lead = clean(source_row.get("DSN ID", ""))
    write(18, 4, team_lead[:4])

    write(23, 20, source_row.get("Release", ""))
    write(46, 4, source_row.get("Subsys", ""))

    # Inventory is built where their programs are in Unit/System.
    # Meaning their Systems will not be PRIVATE1/SHARED01. So when
    # going to prod, we need to update last character to 1.
    system_value = clean(source_row.get("System", ""))

    if mode.upper() == "PROD" and system_value.strip():
        system_value = system_value[:7] + "1"

    write(51, 8, system_value)

    # If they are working in LOE versus a development region we have to
    # update the environment to proper DEVL1 or MAIN1. Default to QUAL1
    # since it will come from there if going to PROD. (non-archive)
    env = "QUAL1"
    act_region = clean(source_row.get("Act Rgn", ""))

    if mode.upper() == "QUAL":
        if act_region.startswith("DV"):
            env = "DEVL1"
        elif act_region.startswith("LO"):
            env = "MAIN1"

    # For archive elements, they will be coming from PROD1.
    if mode.upper() == "PROD":
        env = "PROD1"

    write(60, 5, env)
    write(66, 8, source_row.get("Project", ""))

    application = clean(source_row.get("Application", ""))
    application = application.replace("~", ".")
    application = application.replace(" ", ".")

    write(75, 38, application)

    write(113, 2, "NN")

    return "".join(buffer)[:150]
