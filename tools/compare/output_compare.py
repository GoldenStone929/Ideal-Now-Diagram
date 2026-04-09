"""Output Compare

Compares actual outputs (tables, datasets) between generated and reference programs.
"""

from __future__ import annotations

from typing import Any


def compare_outputs(
    generated_output: list[list[str]],
    reference_output: list[list[str]],
    tolerance: float = 0.0,
) -> dict[str, Any]:
    """Compare two tabular outputs row by row.

    Args:
        generated_output: List of rows, each row is a list of cell values.
        reference_output: Same structure as generated_output.
        tolerance: Numeric tolerance for float comparisons.

    Returns:
        Dict with 'match' (bool), 'differences' (list), 'similarity_score' (float).
    """
    differences: list[dict[str, Any]] = []
    total_cells = 0
    matching_cells = 0

    max_rows = max(len(generated_output), len(reference_output))

    for i in range(max_rows):
        gen_row = generated_output[i] if i < len(generated_output) else []
        ref_row = reference_output[i] if i < len(reference_output) else []
        max_cols = max(len(gen_row), len(ref_row))

        for j in range(max_cols):
            total_cells += 1
            gen_val = gen_row[j] if j < len(gen_row) else ""
            ref_val = ref_row[j] if j < len(ref_row) else ""

            if _values_match(gen_val, ref_val, tolerance):
                matching_cells += 1
            else:
                differences.append({
                    "location": f"row {i}, col {j}",
                    "expected": str(ref_val),
                    "actual": str(gen_val),
                    "severity": "critical" if i == 0 else "major",
                })

    similarity = matching_cells / total_cells if total_cells > 0 else 1.0

    return {
        "match": len(differences) == 0,
        "differences": differences,
        "similarity_score": round(similarity, 4),
    }


def _values_match(a: str, b: str, tolerance: float) -> bool:
    if a == b:
        return True
    try:
        return abs(float(a) - float(b)) <= tolerance
    except (ValueError, TypeError):
        return a.strip() == b.strip()
