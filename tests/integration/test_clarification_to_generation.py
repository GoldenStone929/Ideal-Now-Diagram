"""Integration test: clarification -> generation pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from workflows.task_intake.intake_flow import run_intake
from workflows.clarification.clarification_flow import (
    run_clarification, record_answer, identify_gaps,
)
from workflows.generation.code_generation_flow import run_generation


def test_intake_to_generation_flow():
    task_card = run_intake({
        "description": "Create TEAE summary table by SOC and PT",
        "task_type": "ae_summary",
        "requester": "test_user",
    })
    assert task_card["status"] == "intake"

    task_card = run_clarification(task_card)
    assert task_card["status"] == "clarifying"

    gaps = identify_gaps(task_card)
    for gap in gaps:
        task_card = record_answer(task_card, gap, f"default_{gap}", default_applied=True)

    task_card = run_clarification(task_card)
    assert task_card["status"] == "ready"

    task_card["status"] = "in_progress"
    result = run_generation(
        task_card,
        retrieved_assets=[],
        generate_fn=None,
        target_language="sas",
    )

    assert "asset_card" in result
    assert result["asset_card"]["status"] == "draft"
    assert result["asset_card"]["language"] == "sas"
    assert len(task_card["generated_assets"]) == 1
