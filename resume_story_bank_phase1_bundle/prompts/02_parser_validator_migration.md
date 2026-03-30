Implement Phase 1 parser and validator support for structured metadata.

Read first:
- `resume_story_bank_phase1_bundle/specs/phase1_architecture_contract.md`
- `resume_story_bank_phase1_bundle/specs/structured_metadata_schema.md`
- `resume_story_bank_phase1_bundle/specs/phase1_acceptance_criteria.md`

Repo files to inspect/edit:
- `resume_story_bank/scripts/rag_retrieval.py`
- `resume_story_bank/scripts/validate_story_bank.py`
- any nearby utility modules only if truly necessary

Tasks:
1. Extend story parsing so `### Structured Metadata` is parsed into a machine-usable structure.
2. Preserve backward compatibility temporarily for legacy stories missing metadata.
3. Add validation for:
   - presence/format of the structured metadata block (migration-tolerant)
   - parseable list syntax
   - controlled scalar enum values
4. Make error messages story-specific and actionable.
5. Keep the implementation standard-library-first.
6. Do not implement generation logic.
7. Do not overfit the parser to one single story entry; keep it robust for the bank.

Migration preference:
- non-strict behavior first
- easy path to strict mode later

Deliverable:
- updated parser
- updated validator
- concise note in code/comments if any migration switches or assumptions were introduced
