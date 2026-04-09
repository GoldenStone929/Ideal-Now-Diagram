"""Tests for asset registration."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.asset_ops.register_asset import register_asset


def _make_valid_card():
    return {
        "asset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "title": "Test Asset",
        "asset_type": "code",
        "language": "sas",
        "status": "draft",
        "tags": ["test"],
        "created_by": "test_user",
        "created_at": "2026-04-08T12:00:00Z",
        "version": "1.0.0",
    }


def test_register_new_asset():
    with tempfile.TemporaryDirectory() as tmpdir:
        reg_path = str(Path(tmpdir) / "asset_index.json")
        tag_path = str(Path(tmpdir) / "tag_index.json")

        result = register_asset(
            _make_valid_card(),
            registry_path=reg_path,
            tag_index_path=tag_path,
        )
        assert result["success"] is True

        registry = json.loads(Path(reg_path).read_text())
        assert "a1b2c3d4-e5f6-7890-abcd-ef1234567890" in registry["assets"]


def test_duplicate_registration_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        reg_path = str(Path(tmpdir) / "asset_index.json")
        tag_path = str(Path(tmpdir) / "tag_index.json")

        register_asset(_make_valid_card(), registry_path=reg_path, tag_index_path=tag_path)
        result = register_asset(
            _make_valid_card(), registry_path=reg_path, tag_index_path=tag_path,
        )
        assert result["success"] is False
        assert "already exists" in result["details"]


def test_invalid_metadata_fails():
    card = _make_valid_card()
    del card["title"]

    with tempfile.TemporaryDirectory() as tmpdir:
        reg_path = str(Path(tmpdir) / "asset_index.json")
        tag_path = str(Path(tmpdir) / "tag_index.json")
        result = register_asset(card, registry_path=reg_path, tag_index_path=tag_path)
        assert result["success"] is False
