"""Integration test: review -> writeback pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from workflows.review_writeback.reviewer_decision_flow import (
    create_review_note, process_decision,
)
from workflows.review_writeback.failed_case_writeback import run_failed_case_writeback


def _make_task_card():
    return {
        "task_id": "t-001-0000-0000-0000-000000000001",
        "task_type": "ae_summary",
        "description": "Test task",
        "requester": "test_user",
        "created_at": "2026-04-08T12:00:00Z",
        "status": "in_progress",
        "run_id": "r-001",
    }


def test_approval_flow():
    asset_card = {
        "asset_id": "a-001-0000-0000-0000-000000000001",
        "status": "tested",
        "review_notes": [],
    }

    review = create_review_note(
        asset_id=asset_card["asset_id"],
        reviewer_id="reviewer_001",
        decision="approved",
        comments="Looks correct",
    )

    result = process_decision(asset_card, review)
    assert result["decision"] == "approved"
    assert len(asset_card["review_notes"]) == 1


def test_rejection_creates_failed_case():
    task_card = _make_task_card()
    asset_card = {
        "asset_id": "a-002-0000-0000-0000-000000000002",
        "status": "tested",
        "review_notes": [],
    }

    review = create_review_note(
        asset_id=asset_card["asset_id"],
        reviewer_id="reviewer_001",
        decision="rejected",
        comments="Logic error in TEAE counting",
    )

    result = process_decision(asset_card, review)
    assert result["decision"] == "rejected"

    failed_case = run_failed_case_writeback(task_card, review)
    assert failed_case["related_task_id"] == task_card["task_id"]
    assert failed_case["related_asset_id"] == asset_card["asset_id"]
