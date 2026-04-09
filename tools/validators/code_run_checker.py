"""Code Run Checker

Performs basic runnability checks on code assets.
For Phase 1, this is limited to syntax checking via parsers.
"""

from __future__ import annotations

from typing import Any

from tools.parsers import sas_parser, r_parser, sql_parser


SYNTAX_CHECKERS = {
    "sas": sas_parser.check_syntax,
    "r": r_parser.check_syntax,
    "sql": sql_parser.check_syntax,
}


def check_code(code_content: str, language: str) -> dict[str, Any]:
    """Run syntax check for the given language.

    Returns:
        Dict with 'passed' (bool) and 'details' (str).
    """
    checker = SYNTAX_CHECKERS.get(language)
    if checker is None:
        return {
            "passed": True,
            "details": f"No syntax checker available for '{language}'",
        }
    return checker(code_content)
