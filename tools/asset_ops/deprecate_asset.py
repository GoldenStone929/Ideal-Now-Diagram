"""Deprecate Asset

Marks an asset as deprecated and updates the registry.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def deprecate_asset(
    asset_card: dict[str, Any],
    reason: str,
    deprecated_by: str,
    registry_path: str = "data/asset_registry/asset_index.json",
) -> dict[str, Any]:
    """Mark an asset as deprecated.

    Returns:
        Dict with 'success' (bool) and 'details' (str).
    """
    if not reason:
        return {"success": False, "details": "Deprecation reason is required"}

    current = asset_card.get("status", "")
    if current not in ("reviewer_approved", "production_approved"):
        return {
            "success": False,
            "details": f"Cannot deprecate asset with status '{current}'",
        }

    old_status = asset_card["status"]
    asset_card["status"] = "deprecated"
    asset_card["deprecation_reason"] = reason
    asset_card.setdefault("promotion_history", []).append({
        "from_status": old_status,
        "to_status": "deprecated",
        "promoted_by": deprecated_by,
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
    })

    reg_file = Path(registry_path)
    if reg_file.exists():
        registry = json.loads(reg_file.read_text(encoding="utf-8"))
        registry["assets"][asset_card["asset_id"]] = asset_card
        reg_file.write_text(
            json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8",
        )

    dependents = _find_dependents(asset_card["asset_id"], registry_path)

    return {
        "success": True,
        "details": f"Asset deprecated. {len(dependents)} dependent assets found.",
        "dependent_assets": dependents,
    }


def _find_dependents(asset_id: str, registry_path: str) -> list[str]:
    """Find assets that depend on the deprecated asset."""
    reg_file = Path(registry_path)
    if not reg_file.exists():
        return []

    registry = json.loads(reg_file.read_text(encoding="utf-8"))
    dependents = []
    for aid, card in registry.get("assets", {}).items():
        if asset_id in card.get("dependencies", []):
            dependents.append(aid)
    return dependents
