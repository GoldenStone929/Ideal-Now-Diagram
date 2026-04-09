"""Document Parser

Parses markdown and text documents into structured sections.
Used for processing SAPs, specs, and other reference documents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class DocSection:
    level: int
    title: str
    start_line: int
    end_line: int
    content: str


def parse_markdown(source: str) -> list[DocSection]:
    """Parse a markdown document into a list of sections."""
    sections: list[DocSection] = []
    lines = source.split("\n")

    current_title = ""
    current_level = 0
    current_start = 0
    buffer: list[str] = []

    for i, line in enumerate(lines):
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            if buffer or current_title:
                sections.append(DocSection(
                    level=current_level,
                    title=current_title,
                    start_line=current_start,
                    end_line=i - 1,
                    content="\n".join(buffer),
                ))
            current_level = len(heading_match.group(1))
            current_title = heading_match.group(2).strip()
            current_start = i
            buffer = []
        else:
            buffer.append(line)

    if buffer or current_title:
        sections.append(DocSection(
            level=current_level,
            title=current_title,
            start_line=current_start,
            end_line=len(lines) - 1,
            content="\n".join(buffer),
        ))

    return sections


def extract_tables(source: str) -> list[list[list[str]]]:
    """Extract markdown tables as lists of rows (each row is a list of cells)."""
    tables: list[list[list[str]]] = []
    current_table: list[list[str]] = []
    in_table = False

    for line in source.split("\n"):
        if "|" in line and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if re.match(r"^[\s\-:|]+$", line.strip().strip("|")):
                continue
            current_table.append(cells)
            in_table = True
        elif in_table:
            if current_table:
                tables.append(current_table)
            current_table = []
            in_table = False

    if current_table:
        tables.append(current_table)

    return tables
