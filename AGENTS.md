# AGENTS.md — Entry Guide for Cursor / AI Agents

## Reading Order

When you first enter this project, read these files **in order**:

1. `README.md` — project goals, scope, directory overview
2. `knowledge/index.md` — knowledge entry point and reading order
3. `knowledge/scope/phase1_scope.md` — what Phase 1 covers
4. `knowledge/scope/in_scope.md` / `out_of_scope.md` / `non_goals.md`
5. `knowledge/policies/` — governance, promotion, retrieval, metadata, review policies
6. `knowledge/standards/` — metadata standards, validation/approval definitions
7. `knowledge/schemas/` — JSON schemas for asset cards, task cards, etc.
8. `config/` — runtime configuration (do NOT hard-code values from here)

## Current Boundaries (Phase 1)

- You are building a **validated coding knowledge base**, not a production automation system.
- Every generated artifact is `draft` until promoted by human review.
- Do NOT invent governance rules — always reference `knowledge/policies/` and `config/governance/`.
- Do NOT hard-code file paths — use `config/storage/paths.yaml`.
- Do NOT put business logic in prompt templates — prompts are lightweight wrappers only.

## What NOT to Do

- Do NOT modify files under `data/validated_library/` without going through `workflows/review_writeback/`.
- Do NOT skip the clarification step — always check `knowledge/task_clarification/`.
- Do NOT treat `tools/` as a place for high-level decision-making.
- Do NOT commit secrets or real patient data.

## Collaboration Model

- Workflows orchestrate; tools execute.
- Knowledge and config are the single source of truth for rules and parameters.
- Memory (`data/memory/`) is append-only during normal operation.
- All changes to validated assets require a promotion record.
