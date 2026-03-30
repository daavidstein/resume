# Phase 1 Repo Touch Points

## Existing project assumptions

This bundle is designed for the current repo shape, not a greenfield scaffold.

Expected existing files:
- `resume_story_bank/templates/story_entry_template.md`
- `resume_story_bank/scripts/rag_retrieval.py`
- `resume_story_bank/scripts/validate_story_bank.py`
- `resume_story_bank/README.md`
- `resume_story_bank/AGENTS.md`
- `resume_story_bank/notes/backlog.md`

## Suggested implementation sequence inside the repo

1. Update story template.
2. Update parser structures in `scripts/rag_retrieval.py`.
3. Update validation behavior in `scripts/validate_story_bank.py`.
4. Update repo guidance in `AGENTS.md` and `README.md`.
5. Append provisional Phase 2 / 3 items to `notes/backlog.md`.
6. Optionally annotate a few representative stories in `data/processed/master_story_bank.md` to prove the contract.

## Migration guidance

- Prefer backward compatibility for legacy stories during the first pass.
- Do not require all old stories to have metadata before parser changes land.
- Non-strict validation first; strict validation later.

## Design guardrails

- Preserve standard-library-first implementation.
- Do not implement generation logic in this phase.
- Keep deterministic reuse as the default first-pass philosophy.
