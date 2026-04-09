"""Logic Compare

Compares the derivation logic between two code assets.
Extracts key logic patterns and checks for structural equivalence.
"""

from __future__ import annotations

from typing import Any


def compare_logic(
    generated_code: str,
    reference_code: str,
    language: str = "sas",
) -> dict[str, Any]:
    """Compare logic between generated and reference code.

    This is a structural comparison, not a character-level diff.
    Looks for matching patterns like: populations, derivations, groupings.

    Returns:
        Dict with 'match' (bool), 'differences' (list), 'details' (str).
    """
    gen_patterns = _extract_logic_patterns(generated_code, language)
    ref_patterns = _extract_logic_patterns(reference_code, language)

    differences: list[dict[str, str]] = []

    for key in set(ref_patterns.keys()) | set(gen_patterns.keys()):
        ref_val = ref_patterns.get(key)
        gen_val = gen_patterns.get(key)
        if ref_val != gen_val:
            differences.append({
                "location": key,
                "expected": str(ref_val),
                "actual": str(gen_val),
                "severity": "major" if key in ("population", "derivation") else "minor",
            })

    return {
        "match": len(differences) == 0,
        "differences": differences,
        "details": f"Compared {len(ref_patterns)} logic patterns",
    }


def _extract_logic_patterns(code: str, language: str) -> dict[str, str]:
    """Extract high-level logic patterns from code.

    This is a simplified placeholder. A production implementation would
    use language-specific AST analysis.
    """
    patterns: dict[str, str] = {}
    code_lower = code.lower()

    if "where" in code_lower:
        patterns["has_where_clause"] = "true"
    if any(kw in code_lower for kw in ["saffl", "ittfl", "pprotfl"]):
        patterns["population"] = "flag_based"
    if "group by" in code_lower or "by " in code_lower:
        patterns["grouping"] = "present"
    if any(kw in code_lower for kw in ["count", "freq", "n("]):
        patterns["counting"] = "present"

    return patterns
