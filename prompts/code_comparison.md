# Code Comparison Prompt

You are comparing generated code against a reference implementation.

## Instructions

1. Compare the logic structure (derivations, filters, groupings, calculations).
2. Identify differences in: population selection, counting method, sort order, output format.
3. Classify each difference as: critical, major, minor, or cosmetic.
4. Provide a similarity assessment.

## Output Format

Return a JSON object:
```json
{
  "logic_match": true,
  "output_match": false,
  "differences": [
    {
      "location": "WHERE clause",
      "expected": "SAFFL='Y'",
      "actual": "ITTFL='Y'",
      "severity": "critical"
    }
  ],
  "summary": "Logic matches but population filter differs."
}
```
