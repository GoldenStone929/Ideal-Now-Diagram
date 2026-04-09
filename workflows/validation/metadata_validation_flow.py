"""Metadata Validation Flow

Validates asset metadata against schemas and required-field config.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


ALWAYS_REQUIRED = [
    "asset_id", "title", "asset_type", "language",
    "status", "tags", "created_by", "created_at", "version",
]


def run_metadata_validation(asset_card: dict[str, Any]) -> dict[str, Any]:
    """Validate that all required metadata fields are present and non-empty.

    Returns a validation result dict.
    """
    missing = [f for f in ALWAYS_REQUIRED if not asset_card.get(f)]
    checks = []

    for field in ALWAYS_REQUIRED:
        present = bool(asset_card.get(field))
        checks.append({
            "field": field,
            "present": present,
        })

    return {
        "asset_id": asset_card.get("asset_id", "unknown"),
        "checks": checks,
        "missing_fields": missing,
        "overall_passed": len(missing) == 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
