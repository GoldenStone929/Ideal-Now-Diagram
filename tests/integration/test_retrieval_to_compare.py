"""Integration test: retrieval -> comparison pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from workflows.task_intake.intake_flow import run_intake
from workflows.clarification.clarification_flow import run_clarification, record_answer, identify_gaps
from workflows.retrieval.asset_retrieval_flow import run_retrieval
from workflows.comparison.compare_existing_vs_generated import run_comparison


def test_retrieval_to_compare_flow():
    task_card = run_intake({
        "description": "QC comparison of AE table",
        "task_type": "qc_compare",
        "requester": "test_user",
    })

    gaps = identify_gaps(task_card)
    for gap in gaps:
        task_card = record_answer(task_card, gap, f"test_{gap}")
    task_card = run_clarification(task_card)
    assert task_card["status"] == "ready"

    retrieval_result = run_retrieval(task_card, search_fn=None)
    assert retrieval_result["task_id"] == task_card["task_id"]
    assert task_card["status"] == "in_progress"

    compare_result = run_comparison(
        task_card,
        generated_asset_id="gen-001",
        reference_asset_id=None,
    )
    assert compare_result["logic_match"] is True
    assert compare_result["output_match"] is True
    assert compare_result["task_id"] == task_card["task_id"]
