# Troubleshooting: Common Issues

## Metadata Validation Fails

**Symptom**: `validate_metadata` returns `passed: False`.

**Check**:
1. Are all required fields present? See `knowledge/policies/metadata_policy.md`.
2. Is `tags` a non-empty list?
3. Is `version` in semver format (e.g., `1.0.0`)?
4. Is `asset_id` a valid UUID v4?

## Promotion Blocked

**Symptom**: `validate_promotion` returns `eligible: False`.

**Check**:
1. Is the transition allowed? See `config/governance/asset_status.yaml`.
2. For `tested`: did automated validation pass?
3. For `reviewer_approved`: is there a review note with `approved` decision?
4. For `deprecated`: is there a deprecation reason?

## Retrieval Returns No Results

**Symptom**: Search returns empty results.

**Check**:
1. Are there any assets in the registry? Check `data/asset_registry/asset_index.json`.
2. Is the embedding index populated? Check `tools/retrieval/embed_indexer.py`.
3. Does the query match any tags? Check `data/asset_registry/tag_index.json`.

## Import Errors

**Symptom**: `ModuleNotFoundError` when running tools or workflows.

**Check**:
1. Are you running from the project root directory?
2. Is the virtual environment activated?
3. Run `pip install -r requirements.txt` to ensure dependencies are installed.
