You are working inside the existing `daavidstein/resume` repository.
This is **not** a greenfield project.

Your job is to implement **Phase 1 only** for the existing `resume_story_bank/` project.

Read these local bundle files first:
- `resume_story_bank_phase1_bundle/specs/phase1_architecture_contract.md`
- `resume_story_bank_phase1_bundle/specs/structured_metadata_schema.md`
- `resume_story_bank_phase1_bundle/specs/phase1_acceptance_criteria.md`
- `resume_story_bank_phase1_bundle/patch_notes/phase1_repo_touch_points.md`

Then inspect these existing repo files:
- `resume_story_bank/templates/story_entry_template.md`
- `resume_story_bank/scripts/rag_retrieval.py`
- `resume_story_bank/scripts/validate_story_bank.py`
- `resume_story_bank/README.md`
- `resume_story_bank/AGENTS.md`
- `resume_story_bank/notes/backlog.md`

Execution rules:
1. Do not redesign the project from scratch.
2. Modify existing files in place where appropriate.
3. Keep migration staged and backward-compatible where possible.
4. Do not implement Phase 2 or Phase 3 logic yet.
5. When finished, summarize:
   - files changed
   - migration assumptions
   - any remaining blockers

After reading, proceed through the remaining prompts in order.
