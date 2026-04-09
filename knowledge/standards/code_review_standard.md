# Code Review Standard

## Review Checklist

Every code asset under review must be evaluated against these criteria:

### Correctness
- [ ] Logic matches the stated derivation rules or SAP specification.
- [ ] Edge cases are handled (missing values, zero counts, unexpected data).
- [ ] Output format matches the expected contract (`standards/output_contracts.md`).

### Completeness
- [ ] All required columns / rows / sections are present.
- [ ] Header information (title, footnotes, population, Big N) is correct.
- [ ] Sort order matches specification.

### Reusability
- [ ] Parameters are externalized (not hard-coded study-specific values).
- [ ] Macro variables / function arguments are clearly named.
- [ ] Code can be adapted to similar tasks with minimal changes.

### Documentation
- [ ] Inline comments explain non-obvious logic (not every line).
- [ ] Asset metadata is complete and accurate.
- [ ] Dependencies are declared.

### Compliance
- [ ] No patient-identifiable data is embedded in the asset.
- [ ] Follows the coding patterns in `references/programming_patterns.md`.
- [ ] Uses standard variable names per `references/terminology.md` where applicable.

## Review Note Requirements

A review note must include:
- `reviewer_id`, `review_date`, `decision`, `comments`
- Specific line references for any issues found
- Suggested fixes for `needs_revision` decisions
