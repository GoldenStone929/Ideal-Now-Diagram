"""Embedding Indexer

Creates and manages embedding-based indexes for asset content.
Delegates embedding generation to the configured embedding model.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class EmbedIndexer:
    """Manages an embedding index stored as a JSON file."""

    def __init__(self, index_path: str, embed_fn: Any = None):
        """
        Args:
            index_path: Path to the index JSON file.
            embed_fn: Callable(text) -> list[float]. The embedding function.
        """
        self.index_path = Path(index_path)
        self.embed_fn = embed_fn
        self._index: dict[str, Any] = self._load_index()

    def _load_index(self) -> dict[str, Any]:
        if self.index_path.exists():
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        return {"entries": {}}

    def _save_index(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(
            json.dumps(self._index, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(self, asset_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        """Add or update an entry in the index."""
        embedding = self.embed_fn(text) if self.embed_fn else []
        self._index["entries"][asset_id] = {
            "text": text[:500],
            "embedding": embedding,
            "metadata": metadata or {},
        }
        self._save_index()

    def remove(self, asset_id: str) -> None:
        """Remove an entry from the index."""
        self._index["entries"].pop(asset_id, None)
        self._save_index()

    def search(self, query_text: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search the index by embedding similarity.

        Returns top_k results sorted by cosine similarity (descending).
        Requires embed_fn to be set.
        """
        if not self.embed_fn:
            return []

        query_embedding = self.embed_fn(query_text)
        results = []

        for asset_id, entry in self._index["entries"].items():
            if entry.get("embedding"):
                score = _cosine_similarity(query_embedding, entry["embedding"])
                results.append({
                    "asset_id": asset_id,
                    "score": score,
                    "metadata": entry.get("metadata", {}),
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
