"""Reranker

Re-ranks search results using status-based boosting and optional
cross-encoder scoring.
"""

from __future__ import annotations

from typing import Any

DEFAULT_STATUS_BOOST = {
    "production_approved": 1.5,
    "reviewer_approved": 1.2,
    "tested": 1.0,
    "draft": 0.5,
    "deprecated": 0.1,
}


def rerank(
    results: list[dict[str, Any]],
    status_boost: dict[str, float] | None = None,
    cross_encoder_fn: Any = None,
    query: str = "",
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Re-rank results with status boosting and optional cross-encoder.

    Args:
        results: Raw search results with 'asset_id', 'score', 'metadata'.
        status_boost: Map of status -> multiplier. Uses defaults if None.
        cross_encoder_fn: Optional callable(query, text) -> float for re-scoring.
        query: Original query text (needed for cross-encoder).
        top_k: Number of results to keep.

    Returns:
        Re-ranked results.
    """
    boosts = status_boost or DEFAULT_STATUS_BOOST

    for r in results:
        status = r.get("metadata", {}).get("status", "draft")
        boost = boosts.get(status, 1.0)
        r["boosted_score"] = r.get("score", 0) * boost

        if cross_encoder_fn and query:
            text = r.get("metadata", {}).get("text", "")
            if text:
                ce_score = cross_encoder_fn(query, text)
                r["boosted_score"] = r["boosted_score"] * 0.5 + ce_score * 0.5

    results.sort(key=lambda x: x.get("boosted_score", 0), reverse=True)
    return results[:top_k]
