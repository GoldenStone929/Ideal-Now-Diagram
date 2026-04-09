"""Clarification Flow

Checks a task card for missing information and generates clarification
questions based on knowledge/task_clarification/ rules.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

MANDATORY_FIELDS_BY_TYPE: dict[str, list[str]] = {
    "ae_summary": [
        "population", "big_n_definition", "counting_unit",
        "treatment_groups", "time_window", "output_format",
    ],
    "lab_shift": [
        "population", "lab_parameters", "baseline_definition",
        "shift_categories", "treatment_groups", "output_format",
    ],
    "disposition": [
        "population", "milestones", "discontinuation_reasons",
        "treatment_groups", "output_format",
    ],
    "listing": [
        "population", "listing_columns", "sort_order",
        "output_format",
    ],
    "qc_compare": [
        "reference_program", "comparison_scope", "tolerance",
    ],
}


def identify_gaps(task_card: dict[str, Any]) -> list[str]:
    """Identify mandatory clarification fields that are missing.

    Returns a list of field names that still need answers.
    """
    task_type = task_card.get("task_type", "")
    required = MANDATORY_FIELDS_BY_TYPE.get(task_type, [])

    answered = {
        entry["question"]
        for entry in task_card.get("clarification_history", [])
    }
    return [f for f in required if f not in answered]


def generate_questions(gaps: list[str]) -> list[str]:
    """Turn gap field names into human-readable questions."""
    question_map = {
        "population": "Which population should be used? (safety, ITT, per-protocol, other)",
        "big_n_definition": "How is Big N (column denominator) defined? (randomized, treated, etc.)",
        "counting_unit": "Should counts be based on events or subjects?",
        "treatment_groups": "What are the treatment groups / dose arms? Is there a total column?",
        "time_window": "What defines the analysis time window? (TEAE, on-treatment, etc.)",
        "output_format": "What is the expected output format? (table, listing, dataset)",
        "lab_parameters": "Which lab parameters should be included?",
        "baseline_definition": "How is baseline defined? (last pre-dose, screening, etc.)",
        "shift_categories": "What shift categories? (Low/Normal/High, CTCAE grades, etc.)",
        "milestones": "Which disposition milestones to include?",
        "discontinuation_reasons": "Where do discontinuation reasons come from?",
        "listing_columns": "Which columns should appear in the listing?",
        "sort_order": "What sort order? (by subject, by date, by frequency, etc.)",
        "reference_program": "What is the reference program or output to compare against?",
        "comparison_scope": "Compare logic only, output only, or both?",
        "tolerance": "What tolerance for numeric differences? (exact match, rounding, etc.)",
    }
    return [question_map.get(g, f"Please clarify: {g}") for g in gaps]


def record_answer(
    task_card: dict[str, Any],
    question: str,
    answer: str,
    default_applied: bool = False,
) -> dict[str, Any]:
    """Record a clarification answer on the task card."""
    entry = {
        "question": question,
        "answer": answer,
        "default_applied": default_applied,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    task_card.setdefault("clarification_history", []).append(entry)
    return task_card


def run_clarification(task_card: dict[str, Any]) -> dict[str, Any]:
    """Main entry point for the clarification flow.

    Returns the task card with status updated:
    - 'clarifying' if gaps remain
    - 'ready' if all mandatory questions are answered
    """
    gaps = identify_gaps(task_card)

    if gaps:
        task_card["status"] = "clarifying"
        task_card["_pending_questions"] = generate_questions(gaps)
    else:
        task_card["status"] = "ready"
        task_card.pop("_pending_questions", None)

    return task_card
