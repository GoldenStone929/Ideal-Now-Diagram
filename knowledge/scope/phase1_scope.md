# Phase 1 Scope

Phase 1 delivers a **validated coding knowledge base** for clinical programming.

## What Phase 1 Is

- A structured repository of coding rules, logic fragments, templates, and failed cases.
- A metadata-driven asset lifecycle: draft → tested → reviewer-approved → production-approved.
- A retrieval-augmented workflow: intake → clarification → retrieval → generation → comparison → validation → human review → write-back.
- A local system that runs on a single machine with file-based storage.

## What Phase 1 Is NOT

- Not a production job scheduler or batch execution engine.
- Not a multi-tenant web application.
- Not a visual mind-map tool (graph views may come in Phase 2+).
- Not a replacement for human review — LLM output is always `draft`.

## Success Criteria

1. One end-to-end flow works: a coding task enters, gets clarified, retrieves relevant assets, generates code, compares with existing code, validates, and reaches human review.
2. All assets carry structured metadata conforming to `schemas/asset_card.schema.json`.
3. Failed cases are captured and written back to `data/memory/`.
4. Governance rules live in `knowledge/` and `config/`, not scattered in code.
