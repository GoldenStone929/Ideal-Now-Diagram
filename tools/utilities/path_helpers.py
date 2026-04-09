"""Path Helpers

Utilities for resolving paths relative to the project root.
Reads config/storage/paths.yaml for path definitions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


_PROJECT_ROOT: Path | None = None
_PATHS_CACHE: dict[str, Any] | None = None


def get_project_root() -> Path:
    """Get the project root directory."""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "pyproject.toml").exists():
                _PROJECT_ROOT = parent
                break
        if _PROJECT_ROOT is None:
            _PROJECT_ROOT = Path.cwd()
    return _PROJECT_ROOT


def load_paths() -> dict[str, Any]:
    """Load path configuration from config/storage/paths.yaml."""
    global _PATHS_CACHE
    if _PATHS_CACHE is None:
        config_file = get_project_root() / "config" / "storage" / "paths.yaml"
        if config_file.exists():
            _PATHS_CACHE = yaml.safe_load(config_file.read_text(encoding="utf-8"))
        else:
            _PATHS_CACHE = {}
    return _PATHS_CACHE


def resolve_path(key: str) -> Path:
    """Resolve a dotted path key (e.g., 'assets.code.sas') to an absolute path."""
    paths = load_paths().get("paths", {})
    parts = key.split(".")

    value = paths
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            break

    if isinstance(value, str):
        return get_project_root() / value
    raise KeyError(f"Path key '{key}' not found or not a string in paths.yaml")
