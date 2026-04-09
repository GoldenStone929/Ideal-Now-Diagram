"""Comparison Flow

Compares generated code/output against existing reference assets.
Produces a compare_result conforming to schemas/compare_result.schema.json.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def run_comparison(
    task_card: dict[str, Any],
    generated_asset_id: str,
    reference_asset_id: str | None = None,
    logic_compare_fn: Any = None,
    output_compare_fn: Any = None,
) -> dict[str, Any]:
    """Compare generated output against a reference.

    Args:
        task_card: The current task card.
        generated_asset_id: ID of the generated draft asset.
        reference_asset_id: ID of the reference asset (if available).
        logic_compare_fn: Callable for logic-level comparison.
        output_compare_fn: Callable for output-level comparison.

    Returns:
        A compare_result dict.
    """
    logic_match = True
    output_match = True
    differences: list[dict[str, Any]] = []
    similarity_score = 1.0

    if reference_asset_id:
        if logic_compare_fn is not None:
            logic_result = logic_compare_fn(generated_asset_id, reference_asset_id)
            logic_match = logic_result.get("match", True)
            differences.extend(logic_result.get("differences", []))

        if output_compare_fn is not None:
            output_result = output_compare_fn(generated_asset_id, reference_asset_id)
            output_match = output_result.get("match", True)
            differences.extend(output_result.get("differences", []))
            similarity_score = output_result.get("similarity_score", 1.0)

    compare_result = {
        "compare_id": str(uuid.uuid4()),
        "task_id": task_card["task_id"],
        "generated_asset_id": generated_asset_id,
        "reference_asset_id": reference_asset_id,
        "logic_match": logic_match,
        "output_match": output_match,
        "similarity_score": similarity_score,
        "differences": differences,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    task_card.setdefault("comparison_results", []).append(compare_result["compare_id"])

    return compare_result
