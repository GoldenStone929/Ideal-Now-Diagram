"""Promote Asset

Handles the status promotion of an asset and creates a promotion record.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.validators.promotion_validator import validate_promotion


def promote_asset(
    asset_card: dict[str, Any],
    target_status: str,
    promoted_by: str,
    reason: str = "",
    validation_result: dict[str, Any] | None = None,
    review_note: dict[str, Any] | None = None,
    registry_path: str = "data/asset_registry/asset_index.json",
) -> dict[str, Any]:
    """Promote an asset to the next status level.

    Returns:
        Dict with 'success' (bool), 'promotion_record' (dict | None), 'details' (str).
    """
    eligibility = validate_promotion(
        asset_card, target_status, validation_result, review_note,
    )

    if not eligibility["eligible"]:
        return {
            "success": False,
            "promotion_record": None,
            "details": f"Not eligible: {eligibility['reasons']}",
        }

    old_status = asset_card["status"]

    promotion_record = {
        "promotion_id": str(uuid.uuid4()),
        "asset_id": asset_card["asset_id"],
        "from_status": old_status,
        "to_status": target_status,
        "promoted_by": promoted_by,
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
    }
    if review_note:
        promotion_record["review_note_id"] = review_note.get("review_id")

    asset_card["status"] = target_status
    asset_card.setdefault("promotion_history", []).append({
        "from_status": old_status,
        "to_status": target_status,
        "promoted_by": promoted_by,
        "promoted_at": promotion_record["promoted_at"],
        "reason": reason,
    })

    _update_registry(asset_card, registry_path)

    return {
        "success": True,
        "promotion_record": promotion_record,
        "details": f"Promoted from '{old_status}' to '{target_status}'",
    }


def _update_registry(asset_card: dict[str, Any], registry_path: str) -> None:
    reg_file = Path(registry_path)
    if not reg_file.exists():
        return
    registry = json.loads(reg_file.read_text(encoding="utf-8"))
    registry["assets"][asset_card["asset_id"]] = asset_card
    reg_file.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
