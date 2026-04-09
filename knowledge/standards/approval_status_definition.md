# Approval Status Definition

## Overview

Approval status tracks human decisions about an asset's fitness for use. It is separate from validation status (automated checks).

## Statuses

### pending_review
- Asset has passed automated validation (`tested` status).
- Awaiting human reviewer assignment.

### under_review
- A reviewer has been assigned and is actively evaluating the asset.

### approved
- Reviewer has approved the asset.
- Asset is promoted to `reviewer_approved`.

### approved_with_changes
- Reviewer approved with modifications.
- Changes are applied, then asset is promoted.

### needs_revision
- Reviewer found issues that require author correction.
- Asset remains in `draft` or `tested` status; reviewer comments are attached.

### rejected
- Reviewer determined the asset is not suitable.
- A `failed_case` record is created.

### production_approved
- A second-level review confirmed production readiness.
- Asset is promoted to `production_approved`.

## Relationship to Lifecycle Status

| Lifecycle Status | Requires Approval Status |
|-----------------|-------------------------|
| `draft` | N/A |
| `tested` | N/A (automated only) |
| `reviewer_approved` | `approved` or `approved_with_changes` |
| `production_approved` | `production_approved` |
| `deprecated` | Deprecation decision recorded |
