# Retrieval Policy

## Retrieval Priority

When searching for reusable assets, the system must follow this priority order:

1. **production_approved** assets — highest trust, use first.
2. **reviewer_approved** assets — vetted but not yet production-proven.
3. **tested** assets — passed automated checks but no human review.
4. **Memory layer** (`data/memory/solved_patterns/`, `reviewer_decisions/`) — prior decisions and patterns.
5. **draft** assets — use only as reference, never as direct output.
6. **failed_cases** — use to avoid known pitfalls, not as positive examples.

## Allowed Sources

| Source | Use as direct output? | Use as context? |
|--------|----------------------|-----------------|
| `data/validated_library/production_approved/` | Yes | Yes |
| `data/validated_library/reviewer_approved/` | Yes (with note) | Yes |
| `data/draft_library/` (tested) | No — must go through review | Yes |
| `data/draft_library/` (draft) | No | Yes (low weight) |
| `data/memory/` | No | Yes |
| `data/assets/failed_cases/` | No | Yes (as negative examples) |
| External references | No | Only if listed in `data/references/` |

## Retrieval Method

- Primary: hybrid search (keyword + embedding) via `tools/retrieval/hybrid_search.py`.
- Re-ranking: `tools/retrieval/reranker.py` with config from `config/retrieval/ranking.yaml`.
- Chunking strategy: defined in `config/retrieval/chunking.yaml`.

## Constraints

- Never return deprecated assets as top results unless explicitly requested.
- Always include the asset's `status` in retrieval results so downstream steps know the trust level.
- Retrieval results must be traceable — log which assets were retrieved in `runs/`.
