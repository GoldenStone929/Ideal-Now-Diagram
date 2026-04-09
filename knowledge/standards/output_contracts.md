# Output Contracts

## Purpose

Defines what each workflow step must produce. Downstream steps depend on these contracts.

## Workflow Output Contracts

### task_intake → task_card
```json
{
  "task_id": "string (UUID)",
  "task_type": "enum (ae_summary | lab_shift | disposition | listing | qc_compare)",
  "description": "string",
  "requester": "string",
  "created_at": "ISO 8601",
  "status": "enum (intake | clarifying | ready | in_progress | completed | failed)",
  "clarification_history": [],
  "retrieved_assets": [],
  "generated_assets": [],
  "comparison_results": [],
  "review_notes": [],
  "run_id": "string (UUID)"
}
```

### clarification → updated task_card
- `clarification_history` populated with Q&A pairs.
- `status` changed to `ready` when all mandatory questions are answered.

### retrieval → retrieval_result
```json
{
  "task_id": "string",
  "retrieved_assets": [
    {
      "asset_id": "string",
      "title": "string",
      "status": "string",
      "relevance_score": "float",
      "match_type": "enum (exact | semantic | keyword)"
    }
  ],
  "retrieval_method": "string",
  "timestamp": "ISO 8601"
}
```

### generation → draft asset + asset_card
- A new file in `data/draft_library/generated_code/`.
- An `asset_card` with `status: draft`.

### comparison → compare_result
```json
{
  "task_id": "string",
  "generated_asset_id": "string",
  "reference_asset_id": "string",
  "logic_match": "boolean",
  "output_match": "boolean",
  "differences": [],
  "similarity_score": "float",
  "timestamp": "ISO 8601"
}
```

### validation → validation_result
```json
{
  "asset_id": "string",
  "checks": [
    { "check_name": "string", "passed": "boolean", "details": "string" }
  ],
  "overall_passed": "boolean",
  "timestamp": "ISO 8601"
}
```

### review_writeback → review_note + promotion_record (or failed_case)
- If approved: `review_note` + `promotion_record`, asset moved.
- If rejected: `review_note` + `failed_case`, asset stays or archived.
