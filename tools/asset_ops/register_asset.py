"""Register Asset

Adds a new asset to the asset registry.
Validates metadata before registration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.validators.metadata_validator import validate_metadata


def register_asset(
    asset_card: dict[str, Any],
    registry_path: str = "data/asset_registry/asset_index.json",
    tag_index_path: str = "data/asset_registry/tag_index.json",
    schema_path: str | None = None,
) -> dict[str, Any]:
    """Register a new asset in the registry.

    Returns:
        Dict with 'success' (bool), 'asset_id' (str), 'details' (str).
    """
    validation = validate_metadata(asset_card, schema_path)
    if not validation["passed"]:
        return {
            "success": False,
            "asset_id": asset_card.get("asset_id", ""),
            "details": f"Metadata validation failed: {validation['details']}",
        }

    asset_id = asset_card["asset_id"]

    reg_file = Path(registry_path)
    reg_file.parent.mkdir(parents=True, exist_ok=True)
    if reg_file.exists():
        registry = json.loads(reg_file.read_text(encoding="utf-8"))
    else:
        registry = {"assets": {}}

    if asset_id in registry["assets"]:
        return {
            "success": False,
            "asset_id": asset_id,
            "details": f"Asset {asset_id} already exists in registry",
        }

    registry["assets"][asset_id] = asset_card
    reg_file.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")

    _update_tag_index(asset_id, asset_card.get("tags", []), tag_index_path)

    return {
        "success": True,
        "asset_id": asset_id,
        "details": "Asset registered successfully",
    }


def _update_tag_index(asset_id: str, tags: list[str], tag_index_path: str) -> None:
    tag_file = Path(tag_index_path)
    tag_file.parent.mkdir(parents=True, exist_ok=True)
    if tag_file.exists():
        index = json.loads(tag_file.read_text(encoding="utf-8"))
    else:
        index = {"tags": {}}

    for tag in tags:
        if tag not in index["tags"]:
            index["tags"][tag] = []
        if asset_id not in index["tags"][tag]:
            index["tags"][tag].append(asset_id)

    tag_file.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
