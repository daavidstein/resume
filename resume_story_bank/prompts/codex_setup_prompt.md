# Codex Setup Prompt (Local Workflow)

Use this repository as a local-first resume story bank.

## Working Rules

- Treat `data/processed/master_story_bank.md` as the single source of truth.
- Keep all prompts, templates, and notes in markdown.
- Keep scripts dependency-free (standard library only).
- Prioritize readability and traceability over clever formatting.
- Treat `page_budget` as first-class (`2` default, optional `1`).

## Typical Tasks

1. Add or update stories in `master_story_bank.md`.
2. Maintain `story_bank_changelog.md` and `source_map.md`.
3. Validate consistency with `scripts/validate_story_bank.py`.
4. Support one-shot resume tailoring using:
   - `prompts/tailoring_prompt.md`
   - `templates/tailoring_request_template.md`
5. Validate and render tailored resume models:
   - `scripts/validate_resume_model.py`
   - `scripts/generate_resume_artifacts.py`

## Guardrails

- Never invent achievements.
- Preserve story IDs once assigned.
- Keep IDs unique (`SB-###`).
- Flag incomplete data rather than filling with assumptions.
- Temp workspace policy:
  - Use `/tmp/resume_story_bank_temp` for temporary artifacts.
  - Do not ask for confirmation to create/write files in temp unless total temp usage would exceed 500MB.
  - Do not ask for confirmation to delete files from temp.

## Preferred Commands

```bash
python scripts/validate_story_bank.py
python scripts/validate_resume_model.py --input tests/fixtures/sample_resume_model.json
python scripts/generate_resume_artifacts.py --input-model tests/fixtures/sample_resume_model.json --output-dir resumes/tailored/generated_default
python scripts/split_story_bank.py --help
```
