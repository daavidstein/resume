# Resume Story Bank

`resume_story_bank` is a local, markdown-first knowledge base for reusable career stories.
It is designed for fast resume tailoring now, and deterministic resume generation (JSON -> Markdown -> PDF).

## Goals (Overall/Long-Term)

- Keep one source of truth for stories in a human-readable format.
- Preserve raw inputs (transcripts, summaries, reviews) for traceability.
- Make one-shot tailoring repeatable with prompt and template scaffolds.
- Stay lightweight: no framework, Python standard library scripts.

## Goals (Short Term TO-DO list)

- Implement a pre-tailoring analysis step that identifies:
  - company culture signals
  - team culture signals (for the specific function, e.g., engineering, data science)
  - implied role expectations that are not explicitly written
- Preserve the applicant's voice in final resume output (avoid generic LLM phrasing)
  - Build a voice profile and enforce it during rewriting
  - Add a scoring step to detect and correct tone drift
  - Compare outputs against baseline LLM resume generation
- Auditability/Visualization:
  - Add story ID -> human-readable story name mapping for user-facing displays.
  - Explain why each story was selected (for example: keyword overlap, high similarity to specific JD segments).
- Tailoring roadmap:
  - V1: add constrained rewrite for top selected bullets only (fact-preserving, with automatic fallback to original bullet).
  - V2: add adaptive rewrite/generation with confidence gating and stricter evidence validation.

See [notes/backlog.md](/home/daavid/PycharmProjects/resume/resume_story_bank/notes/backlog.md) for the session-ready checklist and tech-debt queue.
## Current Structure

- `prompts/`: reusable prompts for extraction and tailoring.
- `data/raw/`: source notes and interview artifacts.
- `data/processed/master_story_bank.md`: single-file source of truth.
- `data/processed/story_bank_changelog.md`: log of content-level changes.
- `data/processed/source_map.md`: link stories back to source artifacts.
- `templates/`: standard markdown templates for story entries and tailoring requests.
- `resumes/base_resume/`: canonical resume variants.
- `resumes/tailored/`: job-specific resume outputs.
- `tests/`: pipeline tests and fixtures.
- `jobs/`: job descriptions and company notes.
- `scripts/`: lightweight utilities for validation and future splitting.
- `notes/`: working backlog and story ID index notes.

## Core Workflow (Single-File Source of Truth)

1. Capture raw inputs in `data/raw/`.
2. Normalize stories into `data/processed/master_story_bank.md` using `templates/story_entry_template.md`.
3. Update `source_map.md` and `story_bank_changelog.md` when adding/editing stories.
4. Run validation:
   - `python scripts/validate_story_bank.py`
5. For a target role:
   - Save JD in `jobs/job_descriptions/`
   - Gather company/team culture signals and save notes in `jobs/company_notes/`
     - Prefer primary sources such as company careers page, mission/values pages, and team blogs
     - Extract "read-between-the-lines" expectations (example: "define what quality content looks like" may imply ownership of standards, editorial judgment, stakeholder alignment, and KPI definition)
   - Copy `templates/tailoring_request_template.md` into `notes/` or a working file
   - Use `prompts/tailoring_prompt.md` with:
     - base resume from `resumes/base_resume/`
     - `master_story_bank.md`
     - target JD/company context
6. Save tailored JSON model and generated artifacts in `resumes/tailored/`.

## One-Shot Resume Tailoring (Practical Pass)

Use this minimum input set:

- one base resume file
- one job description file
- one company/team context note file (recommended)
- current `master_story_bank.md`

Then run a single tailoring pass with `prompts/tailoring_prompt.md`, selecting stories by evidence and relevance after a short role interpretation pass:

- What the role appears to own day-to-day
- What "good" likely looks like in this org/team
- Which story evidence best matches those implied expectations
- How to preserve candidate voice while aligning with role language

The tailoring output should be a structured JSON resume model with:

- `page_budget` (`2` default, optional `1`)
- `summary` bullets with `bullet_id`
- `experience` bullets with `bullet_id`
- `traceability` mapping each `bullet_id` to story ID(s)

### Programmatic Tailoring (Current Baseline)

You can generate `model.json` directly from base resume + JD + story bank:

```bash
python3 scripts/tailor_resume_model.py \
  --base-resume resumes/base_resume/daavid_stein_base_resume.md \
  --job-description jobs/job_descriptions/example_role.md \
  --master-story-bank data/processed/master_story_bank.md \
  --output /tmp/resume_story_bank_temp/model.json \
  --page-budget 2
```

Supported JD input formats for `--job-description`:

- `.md`
- `.txt`
- `.html` / `.htm`

You can also fetch a JD directly from URL (for example, a Greenhouse posting page):

```bash
python3 scripts/tailor_resume_model.py \
  --base-resume resumes/base_resume/daavid_stein_base_resume.md \
  --job-description-url 'https://boards.greenhouse.io/<company>/jobs/<id>' \
  --master-story-bank data/processed/master_story_bank.md \
  --output /tmp/resume_story_bank_temp/model.json \
  --page-budget 2
```

Embedding cache:

- Tailoring reuses cached embeddings for JD, story, and resume text to avoid repeated embedding calls.
- Default cache path: `~/.cache/resume_story_bank/embedding_cache.json`
- Embedding backend can be selected with `--embedding-backend` (`local_hash_v1` or `openai`).
- OpenAI model can be selected with `--embedding-model` (default `text-embedding-3-small`).
- Override with `--embedding-cache <path>` or disable with `--no-embedding-cache`.

Job-description URL fetch cache:

- When using `--job-description-url`, tailoring writes the raw fetched payload (`.html` or `.txt`) plus metadata JSON.
- Default directory: `~/.cache/resume_story_bank/job_description_fetches`
- Override with `--jd-fetch-cache-dir <path>` or disable with `--no-jd-fetch-cache`.

Then render/export artifacts:

```bash
python3 scripts/generate_resume_artifacts.py \
  --input-model /tmp/resume_story_bank_temp/model.json \
  --output-dir resumes/tailored/example_role
```

Implementation note: tailoring now uses a hybrid scoring baseline (semantic similarity + lexical overlap) to select existing summary and experience bullets. This keeps the output deterministic and does not rewrite/generate new bullet text yet.

Base resume format expectation for `tailor_resume_model.py`:

- Must include `## About Me`
- Must include `## Professional Experience`
- Must include one or more role sections under experience (`### <Role>`) with `- ` bullets

Then generate artifacts with:

```bash
python3 scripts/generate_resume_artifacts.py \
  --input-model tests/fixtures/sample_resume_model.json \
  --output-dir resumes/tailored/example_default
```

Public artifact policy:

- `resume.md` and `resume.pdf` are always end-user safe and do not include `gaps` or `traceability`.
- Internal sections are available only with `--include-internal`, which writes `resume_internal.md`.

For one-page mode:

```bash
python3 scripts/generate_resume_artifacts.py \
  --input-model tests/fixtures/sample_resume_model.json \
  --output-dir resumes/tailored/example_one_page \
  --page-budget 1
```

If `pandoc` is not installed, add `--skip-pdf` to still generate `resume.json` and `resume.md`.

## Scripts

- `scripts/validate_story_bank.py`
  - Checks each story block has an ID
  - Verifies required headers exist for each story
  - Detects duplicate story IDs
- `scripts/validate_story_bank_metadata.py`
  - Checks consistency between `master_story_bank.md`, `source_map.md`, and `story_bank_changelog.md`
- `scripts/split_story_bank.py`
  - Placeholder utility for future migration to one-story-per-file
- `scripts/validate_resume_model.py`
  - Validates structured resume JSON, budget caps, and traceability coverage
- `scripts/render_resume_md.py`
  - Renders ATS-safe single-column markdown from validated JSON
- `scripts/export_pdf.py`
  - Exports markdown to PDF using `pandoc` with budget-specific profile
- `scripts/generate_resume_artifacts.py`
  - End-to-end generator for `resume.json`, `resume.md`, and optional `resume.pdf`
- `scripts/tailor_resume_model.py`
  - Deterministic baseline generator for `model.json` from base resume + JD + story bank

## Conventions

- Story IDs: `SB-###` (example: `SB-001`)
- Keep story entries complete enough to support STAR/CAR bullet generation.
- Keep `master_story_bank.md` authoritative until splitting is required.

## Quick Start

```bash
cd resume_story_bank
python3 scripts/validate_story_bank.py
python3 scripts/tailor_resume_model.py --base-resume tests/fixtures/sample_base_resume.md --job-description tests/fixtures/sample_job_description.md --master-story-bank tests/fixtures/sample_story_bank.md --output /tmp/resume_story_bank_temp/model.json --page-budget 2
python3 scripts/validate_resume_model.py --input /tmp/resume_story_bank_temp/model.json
python3 scripts/generate_resume_artifacts.py --input-model /tmp/resume_story_bank_temp/model.json --output-dir resumes/tailored/generated_from_tailor --skip-pdf
python3 scripts/validate_resume_model.py --input tests/fixtures/sample_resume_model.json
python3 scripts/generate_resume_artifacts.py --input-model tests/fixtures/sample_resume_model.json --output-dir resumes/tailored/generated_default
python3 scripts/generate_resume_artifacts.py --input-model tests/fixtures/sample_resume_model.json --output-dir resumes/tailored/generated_one_page --page-budget 1 --skip-pdf
python3 scripts/split_story_bank.py --help
make validate
make test-resume-pipeline
```

## Make Targets

- `make validate`: validate story bank
- `make validate-story-metadata`
- `make validate-resume-model MODEL=<path>`
- `make validate-resume-model-strict MODEL=<path>`
- `make tailor-resume-model BASE_RESUME=<path> JOB_DESCRIPTION=<path> STORY_BANK=<path> MODEL=<path> PAGE_BUDGET=2|1`
- `make generate-resume MODEL=<path> OUTPUT=<dir> PAGE_BUDGET=2|1`
- `make export-pdf OUTPUT=<dir> PAGE_BUDGET=2|1`
- `make test-resume-pipeline`
- `make temp-dir`: create shared temp workspace (`/tmp/resume_story_bank_temp` by default)
- `make clean-temp`: delete files under shared temp workspace

## Shared Temp Workspace

Use `/tmp/resume_story_bank_temp` for agent-generated temporary artifacts and test outputs.

- Agents may create, overwrite, and delete files in this directory.
- The path is configurable with `TEMP_DIR=<path>` for make targets.
- This directory is ephemeral and should not store source-of-truth content.
- Confirmation policy:
  - No confirmation needed for create/write in temp unless total temp usage would exceed 500MB.
  - No confirmation needed for delete operations in temp.

## Secrets (direnv)

Use `direnv` at repo root to load API keys only for this project.

1. From `/home/daavid/PycharmProjects/resume`, copy `.envrc.local.example` to `.envrc.local`.
2. Set `OPENAI_API_KEY` in `.envrc.local`.
3. Run `direnv allow`.

Notes:

- `.envrc` is tracked and loads `.envrc.local` if present.
- `.envrc.local` is gitignored.

## Optional: Auto-Run On Commit

To run validation automatically before each commit, configure this project's hook path once:

```bash
cd /home/daavid/PycharmProjects/resume
git config core.hooksPath resume_story_bank/.githooks
```

After that, each `git commit` will execute:

- `python3 scripts/validate_story_bank.py` from `resume_story_bank/.githooks/pre-commit`
