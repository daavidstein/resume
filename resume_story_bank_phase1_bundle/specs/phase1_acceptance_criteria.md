# Phase 1 Acceptance Criteria

Phase 1 is complete when all of the following are true.

## Schema / Template

- `templates/story_entry_template.md` uses `### Structured Metadata` instead of `### Tailoring Notes`.
- The template clearly shows required keys and valid example values.

## Parser

- Story parsing can read structured metadata from `master_story_bank.md`.
- Missing metadata does not immediately hard-fail the repo during migration.
- Parsed metadata is available in a machine-usable structure for later retrieval work.

## Validator

- Validation covers metadata syntax and known controlled-value fields.
- Validation supports a staged rollout strategy.
- Errors are actionable and story-specific.

## Repo Guidance

- `AGENTS.md` explains the story bank purpose, anti-bloat rule, hybrid tailoring policy, and anti-overstatement rules.
- `README.md` explains the distinction between evidence fields, structured metadata, and derived artifacts.
- Guidance explicitly states that deterministic reuse remains the default first pass.

## Backlog

- `notes/backlog.md` contains explicit Phase 2 items for hybrid bullet handling.
- `notes/backlog.md` contains explicit Phase 3 items for story-bank cleanup and candidate profile separation.
- Backlog wording makes clear that Phase 2/3 plans are provisional pending Phase 1 implementation results.

## Non-Goals Verified

- No Phase 2 bullet rewrite/generation implementation shipped in this phase.
