"""Hashing Utilities

Content hashing for change detection and deduplication.
"""

from __future__ import annotations

import hashlib


def content_hash(content: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def file_hash(path: str) -> str:
    """Compute SHA-256 hash of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def short_hash(content: str, length: int = 8) -> str:
    """Return a short hash prefix for display purposes."""
    return content_hash(content)[:length]
