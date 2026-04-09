# Human Review Policy

## When Human Review Is Required

- Before any asset moves from `tested` to `reviewer_approved`.
- Before any asset moves from `reviewer_approved` to `production_approved`.
- When a generated code differs significantly from the retrieved reference (flagged by comparison).
- When validation checks pass but with warnings.

## Reviewer Responsibilities

1. **Verify correctness**: Does the code/logic produce the expected output?
2. **Check completeness**: Are edge cases handled (e.g., missing data, zero counts)?
3. **Assess reusability**: Is the asset generic enough to be useful beyond the original task?
4. **Record decision**: Create a `review_note` conforming to `schemas/review_note.schema.json`.

## Review Decisions

| Decision | Effect |
|----------|--------|
| `approved` | Asset is promoted to the next status level |
| `approved_with_changes` | Reviewer's edits are applied, then promoted |
| `needs_revision` | Asset is sent back to draft with reviewer comments |
| `rejected` | Asset is marked as a failed case |

## Write-Back Rules

- Approved assets: moved to `data/validated_library/` at the appropriate level.
- Rejected assets: a `failed_case` record is created per `failed_case_policy.md`.
- Reviewer decisions are stored in `data/memory/reviewer_decisions/` for future reference.
- All review actions are logged in `runs/` for traceability.

## Escalation

- If a reviewer is uncertain, the asset stays at its current status.
- Production approval requires a second, independent review.
