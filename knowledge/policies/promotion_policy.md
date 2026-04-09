# Promotion Policy

## Promotion Path

```
draft → tested → reviewer_approved → production_approved
                                   ↘ deprecated (from any approved status)
```

## Stage Requirements

### draft → tested
- All required metadata fields are present and valid.
- Asset passes `tools/validators/metadata_validator.py`.
- Asset passes `tools/validators/dependency_checker.py` (no broken references).
- If executable code: passes `tools/validators/code_run_checker.py` (syntax check at minimum).

### tested → reviewer_approved
- A human reviewer has examined the asset.
- A `review_note` record (conforming to `schemas/review_note.schema.json`) exists.
- Review decision is `approved` (not `rejected` or `needs_revision`).

### reviewer_approved → production_approved
- A senior reviewer or domain owner has signed off.
- The asset has been used successfully in at least one real or simulated task.
- A second `review_note` with `level: production` exists.

### Any approved status → deprecated
- A deprecation reason is recorded in the asset card.
- Dependent assets are identified and flagged for review.
- The asset is moved to `data/validated_library/deprecated/`.

## Promotion Records

Every promotion creates a `promotion_record` with:
- `asset_id`, `from_status`, `to_status`, `promoted_by`, `promoted_at`, `reason`
- Stored in the asset registry alongside the asset card.
