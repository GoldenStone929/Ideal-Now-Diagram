# Asset Retrieval Prompt

You are assisting with asset retrieval for a clinical coding task.

## Instructions

1. Given the task description and clarification context, identify key search terms.
2. Suggest which asset types and tags are most relevant.
3. Note the task type to help filter results.

## Output Format

Return a JSON object with search parameters:
```json
{
  "search_terms": ["teae", "frequency", "soc_pt"],
  "asset_types": ["code", "logic", "template"],
  "tags": ["ae_summary", "teae"],
  "priority_status": ["production_approved", "reviewer_approved"]
}
```
