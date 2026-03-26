# Codex Setup Prompt (Local Workflow)

Use this repository as a local-first resume story bank.

## Working Rules

- Treat `data/processed/master_story_bank.md` as the single source of truth.
- Keep all prompts, templates, and notes in markdown.
- Keep scripts dependency-free (standard library only).
- Prioritize readability and traceability over clever formatting.

## Typical Tasks

1. Add or update stories in `master_story_bank.md`.
2. Maintain `story_bank_changelog.md` and `source_map.md`.
3. Validate consistency with `scripts/validate_story_bank.py`.
4. Support one-shot resume tailoring using:
   - `prompts/tailoring_prompt.md`
   - `templates/tailoring_request_template.md`

## Guardrails

- Never invent achievements.
- Preserve story IDs once assigned.
- Keep IDs unique (`SB-###`).
- Flag incomplete data rather than filling with assumptions.

## Preferred Commands

```bash
python scripts/validate_story_bank.py
python scripts/split_story_bank.py --help
```
