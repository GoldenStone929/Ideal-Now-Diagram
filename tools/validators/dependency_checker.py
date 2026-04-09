"""Dependency Checker

Validates that all declared dependencies of an asset exist and are reachable.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def check_dependencies(
    asset_card: dict[str, Any],
    registry_path: str = "data/asset_registry/asset_index.json",
) -> dict[str, Any]:
    """Check that all dependencies in the asset card exist in the registry.

    Returns:
        Dict with 'passed' (bool) and 'details' (str).
    """
    dependencies = asset_card.get("dependencies", [])
    if not dependencies:
        return {"passed": True, "details": "No dependencies declared"}

    registry_file = Path(registry_path)
    if not registry_file.exists():
        return {
            "passed": False,
            "details": f"Registry not found at {registry_path}",
        }

    registry = json.loads(registry_file.read_text(encoding="utf-8"))
    known_assets = set(registry.get("assets", {}).keys())

    missing = [d for d in dependencies if d not in known_assets]

    if missing:
        return {
            "passed": False,
            "details": f"Missing dependencies: {missing}",
        }

    return {"passed": True, "details": "All dependencies resolved"}


def check_circular_dependencies(
    asset_id: str,
    registry_path: str = "data/asset_registry/asset_index.json",
) -> dict[str, Any]:
    """Detect circular dependency chains."""
    registry_file = Path(registry_path)
    if not registry_file.exists():
        return {"passed": True, "details": "Registry not found, skipping circular check"}

    registry = json.loads(registry_file.read_text(encoding="utf-8"))
    assets = registry.get("assets", {})

    visited: set[str] = set()
    stack: list[str] = [asset_id]

    while stack:
        current = stack.pop()
        if current in visited:
            return {
                "passed": False,
                "details": f"Circular dependency detected involving {current}",
            }
        visited.add(current)
        card = assets.get(current, {})
        stack.extend(card.get("dependencies", []))

    return {"passed": True, "details": "No circular dependencies"}
