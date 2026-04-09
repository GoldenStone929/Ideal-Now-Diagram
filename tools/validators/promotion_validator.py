"""Promotion Validator

Validates that an asset meets all prerequisites for a status promotion.
References config/governance/promotion_rules.yaml.
"""

from __future__ import annotations

from typing import Any

ALLOWED_TRANSITIONS = {
    ("draft", "tested"),
    ("tested", "reviewer_approved"),
    ("reviewer_approved", "production_approved"),
    ("reviewer_approved", "deprecated"),
    ("production_approved", "deprecated"),
}


def validate_promotion(
    asset_card: dict[str, Any],
    target_status: str,
    validation_result: dict[str, Any] | None = None,
    review_note: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Check all prerequisites for promoting an asset.

    Returns:
        Dict with 'eligible' (bool) and 'reasons' (list[str]).
    """
    current = asset_card.get("status", "draft")
    reasons: list[str] = []

    if (current, target_status) not in ALLOWED_TRANSITIONS:
        reasons.append(f"Transition from '{current}' to '{target_status}' is not allowed")

    if target_status == "tested":
        if not validation_result or not validation_result.get("overall_passed"):
            reasons.append("Automated validation must pass before promotion to 'tested'")

    if target_status == "reviewer_approved":
        if not review_note:
            reasons.append("A review note is required for promotion to 'reviewer_approved'")
        elif review_note.get("decision") not in ("approved", "approved_with_changes"):
            reasons.append("Review decision must be 'approved' or 'approved_with_changes'")

    if target_status == "production_approved":
        if not review_note:
            reasons.append("A production-level review note is required")
        elif review_note.get("level") != "production":
            reasons.append("Review note must have level 'production'")

    if target_status == "deprecated":
        if not asset_card.get("deprecation_reason"):
            reasons.append("A deprecation reason is required")

    return {
        "asset_id": asset_card.get("asset_id"),
        "current_status": current,
        "target_status": target_status,
        "eligible": len(reasons) == 0,
        "reasons": reasons,
    }
