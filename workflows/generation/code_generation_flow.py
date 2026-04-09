"""Code Generation Flow

Generates code based on the task card, retrieved assets, and clarification context.
The output is always a draft asset — never directly validated.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


def build_generation_context(
    task_card: dict[str, Any],
    retrieved_assets: list[dict[str, Any]],
    logic_fragments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble the context that will be sent to the coding LLM."""
    return {
        "task_description": task_card["description"],
        "task_type": task_card["task_type"],
        "clarifications": task_card.get("clarification_history", []),
        "reference_assets": retrieved_assets,
        "logic_fragments": logic_fragments or [],
    }


def create_draft_asset_card(
    title: str,
    language: str,
    task_type: str,
    file_path: str,
    tags: list[str],
) -> dict[str, Any]:
    """Create a draft asset card for the generated code."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "asset_id": str(uuid.uuid4()),
        "title": title,
        "asset_type": "code",
        "language": language,
        "status": "draft",
        "tags": tags,
        "task_types": [task_type],
        "created_by": "system:code_generation",
        "created_at": now,
        "version": "1.0.0",
        "file_path": file_path,
    }


def run_generation(
    task_card: dict[str, Any],
    retrieved_assets: list[dict[str, Any]],
    generate_fn: Any = None,
    target_language: str = "sas",
) -> dict[str, Any]:
    """Main entry point for code generation.

    Args:
        task_card: Task card with status 'in_progress'.
        retrieved_assets: Assets returned by the retrieval step.
        generate_fn: Callable(context) -> str. The LLM generation function.
                     If None, returns a placeholder.
        target_language: Target programming language.

    Returns:
        Dict with 'asset_card' and 'generated_code'.
    """
    context = build_generation_context(task_card, retrieved_assets)

    if generate_fn is not None:
        generated_code = generate_fn(context)
    else:
        generated_code = f"/* Placeholder: generation not yet connected */\n"

    asset_id = str(uuid.uuid4())
    file_path = f"draft_library/generated_code/{asset_id}.{target_language}"

    asset_card = create_draft_asset_card(
        title=f"Generated {task_card['task_type']} code for task {task_card['task_id'][:8]}",
        language=target_language,
        task_type=task_card["task_type"],
        file_path=file_path,
        tags=[task_card["task_type"], target_language, "generated"],
    )
    asset_card["asset_id"] = asset_id

    task_card.setdefault("generated_assets", []).append(asset_id)

    return {
        "asset_card": asset_card,
        "generated_code": generated_code,
        "file_path": file_path,
    }
