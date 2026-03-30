# Resume Story Bank — Phase 1 Codex Bundle

This bundle is for the existing `daavidstein/resume` repository.
It assumes the current repo root contains `resume_story_bank/` and that Codex will modify existing files in place.

## Goal

Implement **Phase 1 only**:
- replace optional Tailoring Notes with required structured metadata
- align template, parser, validator, README, and AGENTS guidance
- keep migration staged and backward-compatible during rollout
- do **not** implement Phase 2 bullet rewrite/generation logic yet

## Use Order

Run these prompts in order.

1. `prompts/00_phase1_orchestrator.md`
2. `prompts/01_schema_template_contract.md`
3. `prompts/02_parser_validator_migration.md`
4. `prompts/03_docs_and_agent_guidance.md`
5. `prompts/04_backlog_phase_updates.md`
6. `prompts/05_seed_annotation_examples.md` (optional but recommended)

## Files Included

### Specs
- `specs/phase1_architecture_contract.md`
- `specs/structured_metadata_schema.md`
- `specs/phase1_acceptance_criteria.md`

### Drop-in content
- `drop_in_files/story_entry_template.md`
- `drop_in_files/AGENTS_phase1_addition.md`
- `drop_in_files/README_phase1_addition.md`
- `drop_in_files/backlog_phase2_phase3_append.md`

### Patch notes
- `patch_notes/phase1_repo_touch_points.md`

## Expected Repo Touch Points

These are the main files Codex should inspect or edit:
- `resume_story_bank/templates/story_entry_template.md`
- `resume_story_bank/scripts/rag_retrieval.py`
- `resume_story_bank/scripts/validate_story_bank.py`
- `resume_story_bank/README.md`
- `resume_story_bank/AGENTS.md`
- `resume_story_bank/notes/backlog.md`
- optionally `resume_story_bank/data/processed/master_story_bank.md`

## Important Constraints

- Stay markdown-first and lightweight.
- Keep standard-library-first parsing if possible.
- Backward compatibility is preferred during migration.
- Structured metadata is authoritative for retrieval/generation guardrails.
- Embeddings, rankings, and generated bullets are derived artifacts only.
- Deterministic reuse remains the default first pass; generation belongs to later phases.
