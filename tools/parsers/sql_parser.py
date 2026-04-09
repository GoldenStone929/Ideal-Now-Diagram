"""SQL Parser

Parses SQL files into structured representations.
Extracts SELECT statements, CREATE TABLE, and CTEs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SQLBlock:
    block_type: str  # "select", "create_table", "cte", "insert", "other"
    name: str
    start_line: int
    end_line: int
    content: str
    columns: list[str] = field(default_factory=list)


def parse_sql(source: str) -> list[SQLBlock]:
    """Parse SQL source into a list of blocks."""
    blocks: list[SQLBlock] = []
    lines = source.split("\n")

    i = 0
    while i < len(lines):
        stripped = lines[i].strip().upper()

        if stripped.startswith("WITH "):
            end = _find_statement_end(lines, i)
            content = "\n".join(lines[i : end + 1])
            blocks.append(SQLBlock("cte", "", i, end, content))
            i = end + 1
        elif stripped.startswith("SELECT"):
            end = _find_statement_end(lines, i)
            content = "\n".join(lines[i : end + 1])
            blocks.append(SQLBlock("select", "", i, end, content))
            i = end + 1
        elif stripped.startswith("CREATE"):
            match = re.match(r"CREATE\s+TABLE\s+(\S+)", stripped)
            name = match.group(1) if match else ""
            end = _find_statement_end(lines, i)
            content = "\n".join(lines[i : end + 1])
            blocks.append(SQLBlock("create_table", name, i, end, content))
            i = end + 1
        else:
            i += 1

    return blocks


def _find_statement_end(lines: list[str], start: int) -> int:
    for j in range(start, len(lines)):
        if lines[j].rstrip().endswith(";"):
            return j
    return len(lines) - 1


def check_syntax(source: str) -> dict:
    """Basic SQL syntax check."""
    issues: list[str] = []

    selects = len(re.findall(r"\bSELECT\b", source, re.IGNORECASE))
    froms = len(re.findall(r"\bFROM\b", source, re.IGNORECASE))
    if selects > 0 and froms == 0:
        issues.append("SELECT without FROM clause detected")

    return {"passed": len(issues) == 0, "details": "; ".join(issues) if issues else "OK"}
