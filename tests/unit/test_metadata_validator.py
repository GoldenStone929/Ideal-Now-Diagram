"""Tests for metadata validator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.validators.metadata_validator import validate_metadata


def _make_valid_card():
    return {
        "asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "title": "AE Summary Table - TEAE by SOC and PT",
        "asset_type": "code",
        "language": "sas",
        "status": "draft",
        "tags": ["ae_summary", "teae"],
        "created_by": "user_001",
        "created_at": "2026-04-08T12:00:00Z",
        "version": "1.0.0",
    }


def test_valid_card_passes():
    result = validate_metadata(_make_valid_card())
    assert result["passed"] is True
    assert result["details"] == "OK"


def test_missing_required_field_fails():
    card = _make_valid_card()
    del card["title"]
    result = validate_metadata(card)
    assert result["passed"] is False
    assert "title" in result["details"]


def test_empty_tags_fails():
    card = _make_valid_card()
    card["tags"] = []
    result = validate_metadata(card)
    assert result["passed"] is False
    assert "tags" in result["details"]


def test_missing_multiple_fields():
    card = _make_valid_card()
    del card["asset_id"]
    del card["status"]
    result = validate_metadata(card)
    assert result["passed"] is False
    assert "asset_id" in result["details"]
    assert "status" in result["details"]
