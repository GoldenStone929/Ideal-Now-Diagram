"""Keyword Indexer

Builds and queries a keyword-based inverted index for asset search.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


class KeywordIndexer:
    """Simple inverted index for keyword search."""

    def __init__(self, index_path: str):
        self.index_path = Path(index_path)
        self._index: dict[str, list[str]] = self._load_index()

    def _load_index(self) -> dict[str, list[str]]:
        if self.index_path.exists():
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        return {}

    def _save_index(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(
            json.dumps(self._index, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(self, asset_id: str, text: str) -> None:
        """Index a document by its keywords."""
        tokens = _tokenize(text)
        for token in tokens:
            if token not in self._index:
                self._index[token] = []
            if asset_id not in self._index[token]:
                self._index[token].append(asset_id)
        self._save_index()

    def remove(self, asset_id: str) -> None:
        """Remove an asset from all keyword entries."""
        for token in list(self._index.keys()):
            if asset_id in self._index[token]:
                self._index[token].remove(asset_id)
                if not self._index[token]:
                    del self._index[token]
        self._save_index()

    def search(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Search by keyword overlap. Returns results sorted by match count."""
        tokens = _tokenize(query)
        scores: dict[str, int] = defaultdict(int)

        for token in tokens:
            for asset_id in self._index.get(token, []):
                scores[asset_id] += 1

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            {"asset_id": aid, "score": score / max(len(tokens), 1)}
            for aid, score in ranked[:top_k]
        ]


def _tokenize(text: str) -> list[str]:
    """Lowercase tokenization with basic filtering."""
    tokens = re.findall(r"\b\w{2,}\b", text.lower())
    stopwords = {"the", "is", "at", "of", "and", "or", "in", "to", "for", "a", "an"}
    return [t for t in tokens if t not in stopwords]
