# Knowledge Center — Reading Order

This is the single entry point for all knowledge in the Clinical Coding Center.
Both humans and LLM agents should follow this reading order.

## 1. Scope

Start here to understand what Phase 1 covers and what it does not.

- `scope/phase1_scope.md` — Phase 1 definition
- `scope/in_scope.md` — what is included
- `scope/out_of_scope.md` — what is excluded
- `scope/non_goals.md` — things we explicitly will not pursue

## 2. Policies

Governance rules that control how assets enter, move through, and leave the system.

- `policies/code_governance.md` — admission rules, status levels, approval principles
- `policies/promotion_policy.md` — draft → tested → reviewer-approved → production-approved
- `policies/retrieval_policy.md` — retrieval priority and allowed sources
- `policies/failed_case_policy.md` — how failed cases are recorded
- `policies/metadata_policy.md` — required metadata fields for every asset
- `policies/human_review_policy.md` — human final review and write-back rules

## 3. Task Clarification

Rules for understanding what the user actually needs before generating anything.

- `task_clarification/clarification_rules.md`
- `task_clarification/common_missing_questions.md`
- `task_clarification/task_types.md`

## 4. Standards

Formal definitions that policies reference.

- `standards/asset_metadata_standard.md`
- `standards/validation_status_definition.md`
- `standards/approval_status_definition.md`
- `standards/code_review_standard.md`
- `standards/output_contracts.md`

## 5. References

Domain knowledge and terminology.

- `references/terminology.md`
- `references/document_types.md`
- `references/programming_patterns.md`
- `references/common_clinical_logic.md`

## 6. Schemas

JSON schemas that enforce structure on all data artifacts.

- `schemas/asset_card.schema.json`
- `schemas/task_card.schema.json`
- `schemas/failed_case.schema.json`
- `schemas/review_note.schema.json`
- `schemas/compare_result.schema.json`
- `schemas/promotion_record.schema.json`
