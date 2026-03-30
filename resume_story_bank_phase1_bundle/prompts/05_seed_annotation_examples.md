Optional but recommended: seed the Phase 1 schema with a few representative story annotations.

Read first:
- `resume_story_bank_phase1_bundle/specs/structured_metadata_schema.md`
- `resume_story_bank_phase1_bundle/specs/phase1_acceptance_criteria.md`

Repo files to inspect/edit:
- `resume_story_bank/data/processed/master_story_bank.md`
- optionally any validation fixtures if needed

Tasks:
1. Add `### Structured Metadata` to a small number of representative stories only.
2. Prefer stories that are well-bounded and easy to annotate correctly.
3. Do not attempt a full-bank conversion in this task.
4. Use the annotations to prove the parser/validator/docs contract works in practice.
5. If you flag overloaded stories, note them, but do not perform major split refactors in Phase 1 unless they are extremely small and safe.

Suggested stories to annotate first:
- one tightly scoped story
- one moderately broad story
- optionally one story that highlights caveats/forbidden claims well

Deliverable:
- a minimal set of real annotated stories that validate the new contract
