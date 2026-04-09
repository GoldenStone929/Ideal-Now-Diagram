# Failed Case Policy

## What Counts as a Failed Case

A failed case is any coding task result that:
- Was rejected during human review.
- Produced incorrect output when compared against a known-good reference.
- Failed validation checks that could not be auto-corrected.
- Was manually flagged by a reviewer as a learning example.

## Recording Requirements

Every failed case must have a `failed_case` record conforming to `schemas/failed_case.schema.json`, including:

| Field | Required | Description |
|-------|----------|-------------|
| `case_id` | Yes | Unique identifier |
| `related_task_id` | Yes | The task that produced this failure |
| `related_asset_id` | If applicable | The asset that was generated or retrieved |
| `failure_type` | Yes | One of: `logic_error`, `data_mismatch`, `missing_context`, `wrong_template`, `validation_failure`, `other` |
| `failure_description` | Yes | Human-readable explanation |
| `root_cause` | If known | What caused the failure |
| `corrective_action` | If applicable | What was done to fix it |
| `created_by` | Yes | Who recorded this case |
| `created_at` | Yes | ISO 8601 timestamp |

## Storage

- Failed case records: `data/assets/failed_cases/`
- Patterns extracted from failures: `data/memory/common_failures/`

## Reuse

- Failed cases are indexed and retrievable as negative examples.
- The retrieval system should surface relevant failed cases to prevent repeat mistakes.
- Failed case patterns should be periodically reviewed and consolidated into `data/memory/common_failures/`.
