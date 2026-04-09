"""Promotion Check Flow

Validates whether an asset is eligible for promotion to the next status level.
References config/governance/promotion_rules.yaml.
"""

from __future__ import annotations

from typing import Any

ALLOWED_TRANSITIONS = {
    "draft": "tested",
    "tested": "reviewer_approved",
    "reviewer_approved": "production_approved",
}


def check_promotion_eligibility(
    asset_card: dict[str, Any],
    target_status: str,
    validation_result: dict[str, Any] | None = None,
    review_note: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Check if an asset can be promoted to the target status.

    Returns eligibility result with reasons if ineligible.
    """
    current = asset_card.get("status", "draft")
    reasons: list[str] = []

    expected_next = ALLOWED_TRANSITIONS.get(current)
    if target_status == "deprecated":
        if not asset_card.get("deprecation_reason"):
            reasons.append("Deprecation requires a reason")
    elif expected_next != target_status:
        reasons.append(
            f"Cannot promote from '{current}' to '{target_status}'. "
            f"Expected next status: '{expected_next}'"
        )

    if target_status == "tested":
        if validation_result and not validation_result.get("overall_passed"):
            reasons.append("Automated validation did not pass")

    if target_status in ("reviewer_approved", "production_approved"):
        if not review_note:
            reasons.append("Human review note is required")
        elif review_note.get("decision") not in ("approved", "approved_with_changes"):
            reasons.append(f"Review decision is '{review_note.get('decision')}', not approved")

    return {
        "asset_id": asset_card.get("asset_id"),
        "current_status": current,
        "target_status": target_status,
        "eligible": len(reasons) == 0,
        "reasons": reasons,
    }
