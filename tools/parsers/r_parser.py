"""R Parser

Parses R script files into structured representations.
Extracts function definitions, library calls, and comments.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class RBlock:
    block_type: str  # "function", "library", "comment", "other"
    name: str
    start_line: int
    end_line: int
    content: str
    parameters: list[str] = field(default_factory=list)


def parse_r(source: str) -> list[RBlock]:
    """Parse R source code into a list of blocks."""
    blocks: list[RBlock] = []
    lines = source.split("\n")

    for i, line in enumerate(lines):
        stripped = line.strip()

        func_match = re.match(r"(\w+)\s*<-\s*function\s*\(", stripped)
        if func_match:
            name = func_match.group(1)
            end = _find_function_end(lines, i)
            content = "\n".join(lines[i : end + 1])
            blocks.append(RBlock("function", name, i, end, content))

        lib_match = re.match(r"(?:library|require)\(([^)]+)\)", stripped)
        if lib_match:
            blocks.append(RBlock("library", lib_match.group(1).strip('"\''), i, i, stripped))

    return blocks


def _find_function_end(lines: list[str], start: int) -> int:
    """Find end of function by tracking brace nesting."""
    depth = 0
    for j in range(start, len(lines)):
        depth += lines[j].count("{") - lines[j].count("}")
        if depth == 0 and j > start:
            return j
    return len(lines) - 1


def check_syntax(source: str) -> dict:
    """Basic syntax check for R code."""
    issues: list[str] = []

    open_parens = source.count("(")
    close_parens = source.count(")")
    if open_parens != close_parens:
        issues.append(f"Unmatched parentheses: {open_parens} open, {close_parens} close")

    open_braces = source.count("{")
    close_braces = source.count("}")
    if open_braces != close_braces:
        issues.append(f"Unmatched braces: {open_braces} open, {close_braces} close")

    return {"passed": len(issues) == 0, "details": "; ".join(issues) if issues else "OK"}
