# Runbook: Asset Lifecycle

## Creating a New Asset

1. Generate or manually create the asset file.
2. Create an asset card (see `knowledge/schemas/asset_card.schema.json`).
3. Register using `tools/asset_ops/register_asset.py`.
4. Asset enters the system with status `draft`.

## Promoting an Asset

### draft → tested

1. Run metadata validation: `tools/validators/metadata_validator.py`
2. Run dependency check: `tools/validators/dependency_checker.py`
3. Run syntax check: `tools/validators/code_run_checker.py`
4. If all pass, promote via `tools/asset_ops/promote_asset.py`

### tested → reviewer_approved

1. Assign a human reviewer.
2. Reviewer evaluates per `knowledge/standards/code_review_standard.md`.
3. Reviewer creates a review note.
4. If approved, promote via `tools/asset_ops/promote_asset.py`.

### reviewer_approved → production_approved

1. Assign a second (senior) reviewer.
2. Review note must have `level: production`.
3. Asset should have been successfully used in at least one task.
4. Promote via `tools/asset_ops/promote_asset.py`.

## Deprecating an Asset

1. Document the deprecation reason.
2. Identify dependent assets.
3. Run `tools/asset_ops/deprecate_asset.py`.
4. Notify owners of dependent assets.

## Recording a Failed Case

1. Create a failed case record per `knowledge/schemas/failed_case.schema.json`.
2. Store in `data/assets/failed_cases/`.
3. Extract patterns to `data/memory/common_failures/`.
