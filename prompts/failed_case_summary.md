# Failed Case Summary Prompt

You are documenting a failed coding case for future learning.

## Instructions

1. Summarize what went wrong in 1-2 sentences.
2. Identify the root cause category (logic_error, data_mismatch, missing_context, wrong_template, validation_failure, other).
3. Describe the corrective action taken (if any).
4. Extract reusable patterns or lessons that could prevent similar failures.

## Output Format

Return a JSON object conforming to `schemas/failed_case.schema.json`:
```json
{
  "failure_type": "logic_error",
  "failure_description": "...",
  "root_cause": "...",
  "corrective_action": "...",
  "related_patterns": ["pattern_tag_1", "pattern_tag_2"]
}
```
