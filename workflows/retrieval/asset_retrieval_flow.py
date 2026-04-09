"""Asset Retrieval Flow

Searches the asset registry for relevant assets based on the task card.
Uses the retrieval priority defined in config/governance/retrieval_priority.yaml.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_query(task_card: dict[str, Any]) -> dict[str, Any]:
    """Build a search query from a task card's description and clarification answers."""
    query_text = task_card["description"]

    clarifications = task_card.get("clarification_history", [])
    context_parts = [f"{c['question']}: {c['answer']}" for c in clarifications]
    if context_parts:
        query_text += "\n" + "\n".join(context_parts)

    return {
        "text": query_text,
        "task_type": task_card["task_type"],
        "tags": _extract_tags(task_card),
    }


def _extract_tags(task_card: dict[str, Any]) -> list[str]:
    """Extract searchable tags from task description and clarification."""
    tags = [task_card["task_type"]]
    for entry in task_card.get("clarification_history", []):
        answer = entry.get("answer", "")
        if answer:
            tags.extend(answer.lower().split())
    return list(set(tags))


def run_retrieval(
    task_card: dict[str, Any],
    search_fn: Any = None,
) -> dict[str, Any]:
    """Main entry point for asset retrieval.

    Args:
        task_card: A task card with status 'ready'.
        search_fn: Callable(query) -> list[results]. If None, returns empty results
                   (actual search is handled by tools/retrieval/).

    Returns:
        A retrieval result dict conforming to the output contract.
    """
    if task_card.get("status") != "ready":
        raise ValueError(
            f"Task must be in 'ready' status for retrieval, got '{task_card.get('status')}'"
        )

    query = build_query(task_card)

    results = []
    if search_fn is not None:
        results = search_fn(query)

    retrieval_result = {
        "task_id": task_card["task_id"],
        "retrieved_assets": results,
        "retrieval_method": "hybrid" if search_fn else "none",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    task_card["retrieved_assets"] = results
    task_card["status"] = "in_progress"

    return retrieval_result
