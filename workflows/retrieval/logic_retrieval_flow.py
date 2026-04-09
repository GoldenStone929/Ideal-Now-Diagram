"""Logic Retrieval Flow

Specialized retrieval for logic fragments and derivation rules.
Searches data/assets/logic/ and data/memory/solved_patterns/.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def run_logic_retrieval(
    task_card: dict[str, Any],
    search_fn: Any = None,
) -> dict[str, Any]:
    """Retrieve logic-specific assets for the task.

    Focuses on derivation rules, counting logic, grouping logic,
    and solved patterns from memory.
    """
    query = {
        "text": task_card["description"],
        "task_type": task_card["task_type"],
        "asset_types": ["logic"],
        "include_memory": True,
    }

    results = []
    if search_fn is not None:
        results = search_fn(query)

    return {
        "task_id": task_card["task_id"],
        "retrieved_logic": results,
        "retrieval_method": "logic_focused" if search_fn else "none",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
