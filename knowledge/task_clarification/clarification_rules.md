# Clarification Rules

## Core Principle

Never generate code until the task is sufficiently clarified. Ambiguity leads to rework.

## Mandatory Clarification Checks

Before proceeding to retrieval or generation, the system must confirm:

1. **Task type** — Which output is expected? (See `task_types.md`)
2. **Population** — Which subjects are included? (ITT, safety, per-protocol, etc.)
3. **Big N** — How is the denominator defined? (randomized, treated, completed, etc.)
4. **Counting unit** — Events vs. subjects vs. event-subject pairs?
5. **Treatment groups** — What are the dose groups / arms? Is there a total column?
6. **Time window** — What defines the analysis period? (e.g., TEAE, on-treatment, follow-up)
7. **Output format** — Table, listing, dataset, or comparison report?
8. **Reference document** — Is there a SAP, mock shell, or annotated CRF?

## When to Ask

- If any mandatory field cannot be inferred from the task description, **ask before proceeding**.
- If the task description matches a known pattern but with missing details, **pre-fill defaults and confirm**.
- If the task type is not in `task_types.md`, **flag it as out of scope for Phase 1**.

## Clarification Record

Each clarification round is logged in the task card (`schemas/task_card.schema.json`) under `clarification_history`, including:
- Question asked
- Answer received
- Whether a default was applied
- Timestamp
