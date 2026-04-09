"""Metadata Validator

Validates asset cards against the JSON schema and required-field config.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:
    jsonschema = None  # type: ignore[assignment]


ALWAYS_REQUIRED = [
    "asset_id", "title", "asset_type", "language",
    "status", "tags", "created_by", "created_at", "version",
]


def validate_metadata(
    asset_card: dict[str, Any],
    schema_path: str | None = None,
) -> dict[str, Any]:
    """Validate an asset card against required fields and optional JSON schema.

    Returns:
        Dict with 'passed' (bool) and 'details' (str).
    """
    errors: list[str] = []

    missing = [f for f in ALWAYS_REQUIRED if not asset_card.get(f)]
    if missing:
        errors.append(f"Missing required fields: {missing}")

    tags = asset_card.get("tags", [])
    if isinstance(tags, list) and len(tags) == 0:
        errors.append("tags must have at least one entry")

    if schema_path and jsonschema:
        schema_file = Path(schema_path)
        if schema_file.exists():
            schema = json.loads(schema_file.read_text(encoding="utf-8"))
            try:
                jsonschema.validate(asset_card, schema)
            except jsonschema.ValidationError as e:
                errors.append(f"Schema validation error: {e.message}")

    return {
        "passed": len(errors) == 0,
        "details": "; ".join(errors) if errors else "OK",
    }
