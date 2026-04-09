"""File Operations

Safe file read/write utilities used by other tools and workflows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: str) -> Any:
    """Read and parse a JSON file."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(file_path.read_text(encoding="utf-8"))


def write_json(path: str, data: Any, indent: int = 2) -> None:
    """Write data to a JSON file, creating parent directories if needed."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        json.dumps(data, indent=indent, ensure_ascii=False),
        encoding="utf-8",
    )


def read_text(path: str) -> str:
    """Read a text file."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return file_path.read_text(encoding="utf-8")


def write_text(path: str, content: str) -> None:
    """Write text to a file, creating parent directories if needed."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def ensure_dir(path: str) -> Path:
    """Create a directory (and parents) if it doesn't exist."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path
