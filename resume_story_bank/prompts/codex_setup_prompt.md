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
4. Validate story metadata linkage with `scripts/validate_story_bank_metadata.py`.
5. Support one-shot resume tailoring using:
   - `prompts/tailoring_prompt.md`
   - `templates/tailoring_request_template.md`
6. Validate and render tailored resume models:
   - `scripts/validate_resume_model.py`
   - `scripts/generate_resume_artifacts.py`
7. Generate tailored resume models programmatically:
   - `scripts/tailor_resume_model.py`

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
python scripts/extract_story_candidates.py --input tests/fixtures/sample_transcript.md --master-story-bank tests/fixtures/sample_story_bank.md --output /tmp/resume_story_bank_temp/candidate_stories.md
python scripts/validate_story_bank_metadata.py
python scripts/tailor_resume_model.py --base-resume tests/fixtures/sample_base_resume.md --job-description tests/fixtures/sample_job_description.md --master-story-bank tests/fixtures/sample_story_bank.md --output /tmp/resume_story_bank_temp/model.json --page-budget 2
python scripts/validate_resume_model.py --input tests/fixtures/sample_resume_model.json
python scripts/generate_resume_artifacts.py --input-model tests/fixtures/sample_resume_model.json --output-dir resumes/tailored/generated_default
python scripts/split_story_bank.py --help
```
