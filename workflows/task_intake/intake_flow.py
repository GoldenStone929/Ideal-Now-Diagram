"""Task Intake Flow

Receives a raw coding request and creates a structured task card.
This is the entry point for every coding task in the system.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def create_task_card(
    description: str,
    task_type: str,
    requester: str,
) -> dict[str, Any]:
    """Create a new task card from a raw request.

    Returns a task card dict conforming to schemas/task_card.schema.json.
    """
    now = datetime.now(timezone.utc).isoformat()
    return {
        "task_id": str(uuid.uuid4()),
        "task_type": task_type,
        "description": description,
        "requester": requester,
        "created_at": now,
        "status": "intake",
        "clarification_history": [],
        "retrieved_assets": [],
        "generated_assets": [],
        "comparison_results": [],
        "review_notes": [],
        "run_id": str(uuid.uuid4()),
    }


def run_intake(raw_request: dict[str, Any]) -> dict[str, Any]:
    """Main entry point for the intake flow.

    Args:
        raw_request: Must contain 'description', 'task_type', 'requester'.

    Returns:
        A task card ready for the clarification step.
    """
    required_fields = ["description", "task_type", "requester"]
    missing = [f for f in required_fields if f not in raw_request]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")

    valid_task_types = [
        "ae_summary", "lab_shift", "disposition", "listing", "qc_compare",
    ]
    if raw_request["task_type"] not in valid_task_types:
        raise ValueError(
            f"Unknown task_type '{raw_request['task_type']}'. "
            f"Valid types: {valid_task_types}"
        )

    task_card = create_task_card(
        description=raw_request["description"],
        task_type=raw_request["task_type"],
        requester=raw_request["requester"],
    )
    return task_card
