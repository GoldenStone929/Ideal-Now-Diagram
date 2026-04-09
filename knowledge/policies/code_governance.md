# Code Governance Policy

## Admission Rules

An asset may enter the system only if it meets **all** of the following criteria:

1. It has a valid `asset_card` conforming to `schemas/asset_card.schema.json`.
2. It has at least: `asset_id`, `title`, `asset_type`, `language`, `created_by`, `created_at`, `status`.
3. Its `status` is set to `draft` on first entry — no exceptions.
4. It is placed in `data/draft_library/` (never directly into `data/validated_library/`).

## Status Levels

| Status | Meaning | Location |
|--------|---------|----------|
| `draft` | Newly created or LLM-generated; not yet reviewed | `data/draft_library/` |
| `tested` | Passed automated validation checks | `data/draft_library/` |
| `reviewer_approved` | Passed human review | `data/validated_library/reviewer_approved/` |
| `production_approved` | Approved for production use | `data/validated_library/production_approved/` |
| `deprecated` | No longer recommended for use | `data/validated_library/deprecated/` |

## Approval Principles

- **No skip-level promotion**: an asset must pass through each status in order.
- **Human review is mandatory**: no asset reaches `reviewer_approved` without human sign-off.
- **Every promotion creates a `promotion_record`** conforming to `schemas/promotion_record.schema.json`.
- **Deprecation requires a reason** and must be recorded in the asset card.

## Governance Enforcement

- Workflows must call `tools/validators/promotion_validator.py` before any status change.
- Config values in `config/governance/` override any hard-coded defaults.
