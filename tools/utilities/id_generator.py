"""ID Generator

Generates unique identifiers for assets, tasks, and records.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


def generate_asset_id() -> str:
    """Generate a UUID v4 for an asset."""
    return str(uuid.uuid4())


def generate_task_id() -> str:
    """Generate a UUID v4 for a task."""
    return str(uuid.uuid4())


def generate_run_id() -> str:
    """Generate a UUID v4 for a run trace."""
    return str(uuid.uuid4())


def generate_timestamped_id(prefix: str = "") -> str:
    """Generate an ID with a timestamp prefix for sortability.

    Format: {prefix}{YYYYMMDD_HHMMSS}_{short_uuid}
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    short = str(uuid.uuid4())[:8]
    if prefix:
        return f"{prefix}_{ts}_{short}"
    return f"{ts}_{short}"
