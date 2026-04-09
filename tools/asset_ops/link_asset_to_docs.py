"""Link Asset to Docs

Creates and manages relationships between assets and reference documents.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def link_asset(
    asset_id: str,
    related_asset_id: str,
    relationship: str = "depends_on",
    links_path: str = "data/asset_registry/asset_links.json",
) -> dict[str, Any]:
    """Create a link between two assets.

    Args:
        asset_id: The source asset.
        related_asset_id: The target asset or document.
        relationship: Type of relationship (depends_on, references, derived_from, replaces).
        links_path: Path to the links registry.

    Returns:
        Dict with 'success' (bool) and 'details' (str).
    """
    valid_relationships = ["depends_on", "references", "derived_from", "replaces"]
    if relationship not in valid_relationships:
        return {
            "success": False,
            "details": f"Invalid relationship '{relationship}'. Must be one of {valid_relationships}",
        }

    links_file = Path(links_path)
    links_file.parent.mkdir(parents=True, exist_ok=True)
    if links_file.exists():
        data = json.loads(links_file.read_text(encoding="utf-8"))
    else:
        data = {"links": {}}

    if asset_id not in data["links"]:
        data["links"][asset_id] = []

    link_entry = {
        "related_asset_id": related_asset_id,
        "relationship": relationship,
    }

    existing = [
        l for l in data["links"][asset_id]
        if l["related_asset_id"] == related_asset_id and l["relationship"] == relationship
    ]
    if existing:
        return {"success": True, "details": "Link already exists"}

    data["links"][asset_id].append(link_entry)
    links_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    return {"success": True, "details": "Link created"}
