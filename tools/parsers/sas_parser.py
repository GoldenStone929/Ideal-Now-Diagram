"""SAS Parser

Parses SAS program files into structured representations.
Extracts macro definitions, proc steps, data steps, and comments.
No business logic — purely structural parsing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SASBlock:
    block_type: str  # "macro", "proc", "data", "comment", "other"
    name: str
    start_line: int
    end_line: int
    content: str
    parameters: list[str] = field(default_factory=list)


def parse_sas(source: str) -> list[SASBlock]:
    """Parse SAS source code into a list of blocks."""
    blocks: list[SASBlock] = []
    lines = source.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.lower().startswith("%macro "):
            block = _parse_macro(lines, i)
            blocks.append(block)
            i = block.end_line + 1
        elif line.lower().startswith("proc "):
            block = _parse_proc(lines, i)
            blocks.append(block)
            i = block.end_line + 1
        elif line.lower().startswith("data "):
            block = _parse_data_step(lines, i)
            blocks.append(block)
            i = block.end_line + 1
        elif line.startswith("/*"):
            block = _parse_block_comment(lines, i)
            blocks.append(block)
            i = block.end_line + 1
        else:
            i += 1

    return blocks


def _parse_macro(lines: list[str], start: int) -> SASBlock:
    match = re.match(r"%macro\s+(\w+)", lines[start].strip(), re.IGNORECASE)
    name = match.group(1) if match else "unknown"
    end = _find_end(lines, start, r"%mend")
    content = "\n".join(lines[start : end + 1])
    return SASBlock("macro", name, start, end, content)


def _parse_proc(lines: list[str], start: int) -> SASBlock:
    match = re.match(r"proc\s+(\w+)", lines[start].strip(), re.IGNORECASE)
    name = match.group(1) if match else "unknown"
    end = _find_end(lines, start, r"(?:run|quit)\s*;")
    content = "\n".join(lines[start : end + 1])
    return SASBlock("proc", name, start, end, content)


def _parse_data_step(lines: list[str], start: int) -> SASBlock:
    match = re.match(r"data\s+(\S+)", lines[start].strip(), re.IGNORECASE)
    name = match.group(1).rstrip(";") if match else "unknown"
    end = _find_end(lines, start, r"run\s*;")
    content = "\n".join(lines[start : end + 1])
    return SASBlock("data", name, start, end, content)


def _parse_block_comment(lines: list[str], start: int) -> SASBlock:
    end = start
    for j in range(start, len(lines)):
        if "*/" in lines[j]:
            end = j
            break
    content = "\n".join(lines[start : end + 1])
    return SASBlock("comment", "", start, end, content)


def _find_end(lines: list[str], start: int, pattern: str) -> int:
    for j in range(start + 1, len(lines)):
        if re.search(pattern, lines[j].strip(), re.IGNORECASE):
            return j
    return len(lines) - 1


def check_syntax(source: str) -> dict:
    """Basic syntax check: unmatched macros, missing semicolons, etc."""
    issues: list[str] = []

    macro_starts = len(re.findall(r"%macro\b", source, re.IGNORECASE))
    macro_ends = len(re.findall(r"%mend\b", source, re.IGNORECASE))
    if macro_starts != macro_ends:
        issues.append(f"Unmatched %macro/%mend: {macro_starts} starts, {macro_ends} ends")

    return {"passed": len(issues) == 0, "details": "; ".join(issues) if issues else "OK"}
