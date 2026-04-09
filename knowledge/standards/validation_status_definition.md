# Validation Status Definition

## Overview

Validation status tracks whether an asset has passed automated checks. It is distinct from approval status (which requires human judgment).

## Statuses

### not_validated
- Default state on asset creation.
- No automated checks have been run.

### metadata_valid
- All required metadata fields are present and conform to schema.
- Checked by `tools/validators/metadata_validator.py`.

### dependency_valid
- All declared dependencies exist and are accessible.
- No circular dependency chains.
- Checked by `tools/validators/dependency_checker.py`.

### syntax_valid
- Code parses without syntax errors in its declared language.
- Checked by language-specific parsers in `tools/parsers/`.

### run_valid
- Code executes without runtime errors on test data (if applicable).
- Checked by `tools/validators/code_run_checker.py`.

### fully_validated
- All of the above checks pass.
- Asset is eligible for promotion from `draft` to `tested`.

## Validation Failures

- Each failed check produces a validation result record.
- The asset remains at its current validation status until the issue is fixed and re-validated.
- Persistent validation failures may trigger a `failed_case` record.
