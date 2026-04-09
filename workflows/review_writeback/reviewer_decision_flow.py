"""Reviewer Decision Flow

Processes a human reviewer's decision and updates the asset accordingly.
Creates review notes, triggers promotion or failed-case recording.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def create_review_note(
    asset_id: str,
    reviewer_id: str,
    decision: str,
    comments: str = "",
    level: str = "standard",
) -> dict[str, Any]:
    """Create a review note conforming to schemas/review_note.schema.json."""
    valid_decisions = ["approved", "approved_with_changes", "needs_revision", "rejected"]
    if decision not in valid_decisions:
        raise ValueError(f"Invalid decision '{decision}'. Must be one of {valid_decisions}")

    return {
        "review_id": str(uuid.uuid4()),
        "asset_id": asset_id,
        "reviewer_id": reviewer_id,
        "review_date": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "decision": decision,
        "comments": comments,
    }


def process_decision(
    asset_card: dict[str, Any],
    review_note: dict[str, Any],
    promote_fn: Any = None,
    create_failed_case_fn: Any = None,
) -> dict[str, Any]:
    """Process the reviewer's decision.

    Returns an action summary describing what was done.
    """
    decision = review_note["decision"]
    actions: list[str] = []

    if decision in ("approved", "approved_with_changes"):
        if promote_fn:
            promote_fn(asset_card, review_note)
        actions.append(f"Asset promoted based on '{decision}' decision")

    elif decision == "needs_revision":
        asset_card["status"] = "draft"
        actions.append("Asset returned to draft for revision")

    elif decision == "rejected":
        if create_failed_case_fn:
            create_failed_case_fn(asset_card, review_note)
        actions.append("Asset rejected; failed case record created")

    asset_card.setdefault("review_notes", []).append(review_note["review_id"])

    return {
        "asset_id": asset_card["asset_id"],
        "decision": decision,
        "actions": actions,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
