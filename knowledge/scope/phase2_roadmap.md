# Phase 2+ Roadmap (Deferred Items)

This document captures features explicitly deferred from Phase 1.
They are designed to build on top of the structured data model established in Phase 1.

## Visual Mind-Map / Graph View

**Status**: Deferred to Phase 2.

**Rationale**: The structured knowledge base (asset registry, tag index, asset links, memory)
provides the data substrate. A visual layer should *derive* from this data, not be the primary
authoring interface.

**Approach when ready**:
1. Read `data/asset_registry/asset_links.json` to build a dependency graph.
2. Read `data/asset_registry/tag_index.json` to build a concept map.
3. Use a graph visualization library (e.g., D3.js, Cytoscape, React Flow) to render.
4. The graph view is **read-only** or **navigation-only** — edits still go through the
   standard workflows and tools.

**Data sources for visualization**:
- `asset_links.json` → dependency edges between assets
- `tag_index.json` → tag-based clustering
- `memory/solved_patterns/` → pattern reuse connections
- `memory/common_failures/` → failure pattern heatmaps
- `promotion_history` in asset cards → lifecycle timelines

## Web UI / Dashboard

**Status**: Deferred to Phase 2+.

Not needed while the system is single-user and local.
When ready, build as a thin layer over the existing workflows and tools.

## Multi-Study Support

**Status**: Deferred to Phase 3+.

Requires namespacing assets by study and managing cross-study reuse policies.

## Automated Promotion (with guardrails)

**Status**: Deferred to Phase 2.

Phase 1 requires manual promotion at every step.
Phase 2 may allow auto-promotion from `draft` → `tested` when all validations pass,
but `tested` → `reviewer_approved` will always require human review.
