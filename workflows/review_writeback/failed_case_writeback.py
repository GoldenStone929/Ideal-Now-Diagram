"""Failed Case Write-back Flow

Creates structured failed-case records and writes them to the
appropriate storage locations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def create_failed_case_record(
    task_id: str,
    asset_id: str | None,
    failure_type: str,
    failure_description: str,
    created_by: str,
    root_cause: str | None = None,
    corrective_action: str | None = None,
) -> dict[str, Any]:
    """Create a failed case record conforming to schemas/failed_case.schema.json."""
    valid_types = [
        "logic_error", "data_mismatch", "missing_context",
        "wrong_template", "validation_failure", "other",
    ]
    if failure_type not in valid_types:
        raise ValueError(f"Invalid failure_type '{failure_type}'. Must be one of {valid_types}")

    record: dict[str, Any] = {
        "case_id": str(uuid.uuid4()),
        "related_task_id": task_id,
        "failure_type": failure_type,
        "failure_description": failure_description,
        "created_by": created_by,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if asset_id:
        record["related_asset_id"] = asset_id
    if root_cause:
        record["root_cause"] = root_cause
    if corrective_action:
        record["corrective_action"] = corrective_action

    return record


def run_failed_case_writeback(
    task_card: dict[str, Any],
    review_note: dict[str, Any],
    write_fn: Any = None,
) -> dict[str, Any]:
    """Create and store a failed case from a rejected review.

    Args:
        task_card: The task card that produced the failure.
        review_note: The review note with decision 'rejected'.
        write_fn: Callable(record, path) to persist the record. If None, returns without writing.

    Returns:
        The failed case record.
    """
    record = create_failed_case_record(
        task_id=task_card["task_id"],
        asset_id=review_note.get("asset_id"),
        failure_type="other",
        failure_description=review_note.get("comments", "Rejected during review"),
        created_by=review_note["reviewer_id"],
    )

    if write_fn:
        write_fn(record, f"data/assets/failed_cases/{record['case_id']}.json")

    return record
