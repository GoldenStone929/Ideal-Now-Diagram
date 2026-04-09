# Task Types (Phase 1)

Phase 1 supports the following task types. Tasks outside this list should be flagged as out of scope.

## Supported Task Types

### ae_summary
Adverse event summary tables (overall, by SOC/PT, by severity, by relationship).

### lab_shift
Lab shift tables (baseline to post-baseline, by parameter, by visit or worst post-baseline).

### disposition
Subject disposition tables (screened, randomized, treated, completed, discontinued with reasons).

### listing
Patient or data listings (AE listings, concomitant medication listings, lab listings).

### qc_compare
Quality control comparison: compare generated output against an existing reference program or output.

## Task Type Metadata

Each task type has:
- `type_id` — machine-readable identifier (e.g., `ae_summary`)
- `display_name` — human-readable name (e.g., "AE Summary Table")
- `required_clarifications` — which clarification questions are mandatory for this type
- `typical_assets` — which asset types are commonly retrieved for this task
- `output_format` — expected output structure (table, listing, dataset, report)

## Adding New Task Types

New task types may be added in later phases by:
1. Defining the type in this file.
2. Adding required clarification questions to `common_missing_questions.md`.
3. Creating or linking relevant assets in `data/assets/`.
4. Updating retrieval config if the new type needs special handling.
