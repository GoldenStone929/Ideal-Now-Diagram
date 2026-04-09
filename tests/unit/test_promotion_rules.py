"""Tests for promotion validation rules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.validators.promotion_validator import validate_promotion


def _make_card(status="draft"):
    return {
        "asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "status": status,
    }


def test_draft_to_tested_with_validation():
    card = _make_card("draft")
    validation = {"overall_passed": True}
    result = validate_promotion(card, "tested", validation_result=validation)
    assert result["eligible"] is True


def test_draft_to_tested_without_validation_fails():
    card = _make_card("draft")
    result = validate_promotion(card, "tested", validation_result=None)
    assert result["eligible"] is False


def test_skip_level_not_allowed():
    card = _make_card("draft")
    result = validate_promotion(card, "reviewer_approved")
    assert result["eligible"] is False
    assert any("not allowed" in r for r in result["reasons"])


def test_tested_to_reviewer_approved_with_review():
    card = _make_card("tested")
    review = {"decision": "approved", "review_id": "r-001"}
    result = validate_promotion(card, "reviewer_approved", review_note=review)
    assert result["eligible"] is True


def test_tested_to_reviewer_approved_without_review_fails():
    card = _make_card("tested")
    result = validate_promotion(card, "reviewer_approved")
    assert result["eligible"] is False


def test_deprecation_requires_reason():
    card = _make_card("production_approved")
    result = validate_promotion(card, "deprecated")
    assert result["eligible"] is False
    assert any("deprecation reason" in r for r in result["reasons"])


def test_deprecation_with_reason():
    card = _make_card("production_approved")
    card["deprecation_reason"] = "Replaced by v2"
    result = validate_promotion(card, "deprecated")
    assert result["eligible"] is True
