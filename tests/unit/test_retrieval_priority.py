"""Tests for retrieval ranking and reranking."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.retrieval.reranker import rerank


def test_status_boosting():
    results = [
        {"asset_id": "draft_1", "score": 0.9, "metadata": {"status": "draft"}},
        {"asset_id": "prod_1", "score": 0.7, "metadata": {"status": "production_approved"}},
        {"asset_id": "rev_1", "score": 0.8, "metadata": {"status": "reviewer_approved"}},
    ]

    reranked = rerank(results, top_k=3)

    ids = [r["asset_id"] for r in reranked]
    assert ids[0] == "prod_1", "production_approved should rank first due to 1.5x boost"
    assert ids[1] == "rev_1", "reviewer_approved should rank second due to 1.2x boost"


def test_deprecated_assets_ranked_last():
    results = [
        {"asset_id": "dep_1", "score": 0.95, "metadata": {"status": "deprecated"}},
        {"asset_id": "draft_1", "score": 0.5, "metadata": {"status": "draft"}},
    ]

    reranked = rerank(results, top_k=2)
    assert reranked[0]["asset_id"] == "draft_1"


def test_top_k_limits_results():
    results = [
        {"asset_id": f"asset_{i}", "score": 0.5, "metadata": {"status": "draft"}}
        for i in range(10)
    ]

    reranked = rerank(results, top_k=3)
    assert len(reranked) == 3
