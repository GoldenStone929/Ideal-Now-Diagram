"""Hybrid Search

Combines keyword and embedding search results with configurable weights.
"""

from __future__ import annotations

from typing import Any


def hybrid_search(
    keyword_results: list[dict[str, Any]],
    semantic_results: list[dict[str, Any]],
    keyword_weight: float = 0.3,
    semantic_weight: float = 0.7,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Merge keyword and semantic search results using weighted scoring.

    Args:
        keyword_results: Results from KeywordIndexer.search().
        semantic_results: Results from EmbedIndexer.search().
        keyword_weight: Weight for keyword scores (0-1).
        semantic_weight: Weight for semantic scores (0-1).
        top_k: Number of results to return.

    Returns:
        Merged and re-ranked results.
    """
    scores: dict[str, float] = {}
    metadata: dict[str, dict] = {}

    for r in keyword_results:
        aid = r["asset_id"]
        scores[aid] = scores.get(aid, 0) + r["score"] * keyword_weight
        if "metadata" in r:
            metadata[aid] = r["metadata"]

    for r in semantic_results:
        aid = r["asset_id"]
        scores[aid] = scores.get(aid, 0) + r["score"] * semantic_weight
        if "metadata" in r:
            metadata[aid] = r["metadata"]

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return [
        {
            "asset_id": aid,
            "score": score,
            "match_type": _determine_match_type(aid, keyword_results, semantic_results),
            "metadata": metadata.get(aid, {}),
        }
        for aid, score in ranked[:top_k]
    ]


def _determine_match_type(
    asset_id: str,
    keyword_results: list[dict],
    semantic_results: list[dict],
) -> str:
    in_keyword = any(r["asset_id"] == asset_id for r in keyword_results)
    in_semantic = any(r["asset_id"] == asset_id for r in semantic_results)
    if in_keyword and in_semantic:
        return "exact"
    elif in_semantic:
        return "semantic"
    return "keyword"
