Implement the Phase 1 schema/template contract in the existing repo.

Read first:
- `resume_story_bank_phase1_bundle/specs/phase1_architecture_contract.md`
- `resume_story_bank_phase1_bundle/specs/structured_metadata_schema.md`
- `resume_story_bank_phase1_bundle/drop_in_files/story_entry_template.md`

Repo files to inspect/edit:
- `resume_story_bank/templates/story_entry_template.md`
- `resume_story_bank/README.md` (only if schema references need alignment here too)

Tasks:
1. Replace optional `### Tailoring Notes` in the story template with required `### Structured Metadata`.
2. Keep the template markdown-first and easy for humans to edit.
3. Use rigid key-value lines and list syntax shown in the spec.
4. Ensure the template reflects controlled-value fields and examples accurately.
5. Do not add unnecessary schema complexity beyond the Phase 1 spec.

Deliverable:
- updated template file aligned with the spec
- minimal related doc adjustments only if needed for immediate consistency
