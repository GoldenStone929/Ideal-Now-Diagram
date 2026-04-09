# In Scope

The following are explicitly within the scope of this project (Phase 1):

## Knowledge Management
- Storing and retrieving clinical coding rules, logic fragments, and reusable templates.
- Maintaining a structured asset registry with metadata, tags, and dependency links.
- Recording failed cases as first-class knowledge assets.

## Task Types (Initial Set)
- AE (adverse event) summary tables
- Lab shift tables
- Disposition tables
- Listings (patient listings, data listings)
- QC compare (generated vs. existing code comparison)

## Languages
- SAS (primary)
- R
- SQL
- Python (supporting role)

## Asset Lifecycle
- Draft creation (manual or LLM-generated)
- Metadata validation
- Promotion through status levels
- Deprecation of outdated assets

## Workflows
- Task intake and clarification
- Asset retrieval (hybrid: keyword + embedding)
- Code generation with context
- Comparison against existing code
- Validation checks (metadata, dependencies, runnability)
- Human review and write-back
- Failed case recording

## Infrastructure
- Local file-based storage (JSON, YAML, Markdown)
- Configuration-driven behavior (no hard-coded rules in code)
- Lightweight prompt templates
