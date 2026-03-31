# Resume Story Bank

`resume_story_bank` is a local, markdown-first knowledge base for reusable career stories.
It is designed for fast resume tailoring now, and deterministic resume generation (JSON -> Markdown -> PDF).

## Goals (Overall/Long-Term)

- Keep one source of truth for stories in a human-readable format.
- Preserve raw inputs (transcripts, summaries, reviews) for traceability.
- Make one-shot tailoring repeatable with prompt and template scaffolds.
- Stay lightweight: no framework, Python standard library scripts.

## Story Bank Data Model

The repository uses three classes of information:

1. **Evidence fields**
   - Human-maintained source-of-truth story content.
   - Includes `Context`, `Actions`, `Outcomes`, `Skills/Keywords`, and `Source References`.
   - Used for auditability and final claim grounding.
2. **Structured metadata**
   - Human/agent-maintained retrieval and rewrite-control fields under `### Structured Metadata`.
   - Used for ranking support, match interpretation, and future rewrite guardrails.
   - This metadata is authoritative for machine-usable tailoring constraints.
   - `specs/tag_ontology.yaml` provides the canonical normalization and lightweight validation layer for ontology-controlled tags.
3. **Derived artifacts**
   - Embeddings, chunk rankings, selected bullets, rewritten bullets, generated summaries, and selection reports.
   - These are disposable outputs and must never be treated as source of truth.

## Project Guidelines (Hybrid Tailoring)

- Deterministic reuse remains the default first pass for tailoring.
- Tailoring is intentionally hybrid:
  - retrieve and score existing stories and reusable bullets first
  - prefer reuse when the existing bullet is already strong
  - use rewrite only when it creates a meaningful fit improvement
  - keep every tailored bullet traceable to story ID(s)
- Preserve traceability: outputs must keep explicit source references and never invent achievements.
- Treat model outputs as draft artifacts; all source-of-truth updates still require local validation before merge.
- Keep deterministic heuristics available for offline operation, reproducibility checks, and regression testing.
- Use `caveats`, `wording_constraints`, and `forbidden_claims` to prevent overstatement during later rewrite phases.

# Project Guideline Addendum: Agent Behavior and Startup Execution

## Why this addendum exists

The project already encodes a reuse-first, truth-preserving tailoring strategy. This addendum makes the expected execution style explicit so that agents do not drift into infrastructure-first planning.

## Operating principle

**Be strict about truth. Be lean about everything else until it hurts.**

This means:

- ship useful capability early
- learn from real outputs
- avoid speculative architecture
- add infrastructure only when it solves an observed problem
- preserve truth and traceability even when moving quickly

## Execution rules

### 1. Prefer reviewable outputs over elegant architecture
When choosing between a lightweight implementation and a more comprehensive one, prefer the lightweight implementation unless the heavier one is needed to:

- preserve factual integrity
- prevent repeated observed failures
- unblock current delivery

### 2. Reuse before generation
For resume-tailoring work, prefer this order:

1. reuse strong historical bullets
2. lightly adapt linked historical bullets
3. generate new bullets from story-bank evidence only when necessary

Historical resumes should be treated as a seed bullet corpus and style prior, not as the canonical evidence source.

### 3. Keep the evidence model clear
- The story bank remains the canonical reviewed evidence base for accomplishment claims.
- Historical bullets are expression artifacts and prior approved wording examples.
- Generated outputs are draft artifacts unless explicitly reviewed and promoted.

### 4. Defer scope by default
Unless required by current work or observed failures, defer:

- broad refactors
- full governance systems
- comprehensive validators
- major ontology cleanup
- speculative abstractions for future phases

### 5. Use observed failures to drive guardrails
Do not build large control systems before reviewing real outputs.

For new workflow stages:

1. generate output
2. review manually
3. classify failure modes
4. add the minimum controls needed

### 6. Keep minimum observability
Even when moving fast, keep enough visibility to answer basic questions like:

- what source story or stories produced this output?
- was this reused, adapted, or newly synthesized?
- what path or prompt created it?

This is the minimum needed to make failures diagnosable without overbuilding provenance infrastructure.

## Summary

The intended repo behavior is:

- evidence-grounded
- reuse-first
- review-driven
- startup-minded
- skeptical of speculative architecture

## Candidate Profile Separation

The story bank is not the full candidate model.
Softer matching and personalization signals should live in a separate candidate-profile artifact rather than inside `master_story_bank.md`.
Candidate-profile data may influence ranking or framing later, but it must not be treated as evidence for accomplishment claims.

### Design Decision: Transcript Extraction Cost Strategy

- Transcript-to-story extraction is currently a ChatGPT/manual step, not an automated embedding pipeline.
- Rationale: transcript/story volume is expected to stay finite and slow-growing, so recurring embedding/indexing cost and complexity are not justified right now.
- Implication: use prompt-driven extraction for new transcripts, then run local validators before merging into `master_story_bank.md`.

## Migration Note

Structured metadata rollout is intentionally staged:

- update template and parser first
- allow temporary backward compatibility for legacy stories
- validate non-strictly during migration
- prefer ontology-backed warnings and normalization over brittle hard enforcement
- tighten validation later with `python scripts/validate_story_bank.py --strict-structured-metadata`

## Phase 2 Operating Rule

Do not overengineer Phase 2 before reviewing real generated bullets.

- The main near-term experiment is `story bank -> bullets`, not transcript validation.
- Manual review is sufficient for the lower-volume promotion steps:
  - `transcript -> summary`
  - `summary -> story bank`
- The main automated risk is later compression and presentation:
  - `story bank -> bullets`
  - `bullets -> resume`
- Before building heavy bullet-risk infrastructure, review a meaningful first batch of generated bullets and use observed failure modes to drive guardrails.
- Preserve only minimum observability during the first pass:
  - which story or stories a bullet came from
  - whether it was reused vs more synthetic/rephrased
  - what prompt/path generated it
- `wording_constraints`, `caveats`, and `forbidden_claims` should be treated as lightweight truth-preserving airlocks, not as a reason to build a large governance layer upfront.

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
- Project management:
  - Add better issue tracking and scheduling so planning work is visible outside the session-local backlog.
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
- `data/processed/story_bank_provenance_map.md`: narrative provenance notes with primary/supporting evidence and legacy ID crosswalks.
- `data/processed/summary_to_transcript_map.md`: map summaries to upstream transcripts with match confidence status.
- `templates/`: standard markdown templates for story entries and tailoring requests.
- `resumes/base_resume/`: canonical resume variants.
- `resumes/tailored/`: job-specific resume outputs.
- `tests/`: pipeline tests and fixtures.
- `jobs/`: job descriptions and company notes.
- `scripts/`: lightweight utilities for validation and future splitting.
- `notes/`: working backlog and story ID index notes.

## Core Workflow (Single-File Source of Truth)

1. Capture raw inputs in `data/raw/`.
2. Generate draft story candidates from transcripts:
   - `python3 scripts/extract_story_candidates.py --input data/raw/transcripts/<file>.md --master-story-bank data/processed/master_story_bank.md --output /tmp/resume_story_bank_temp/candidate_stories.md`
3. Normalize reviewed stories into `data/processed/master_story_bank.md` using `templates/story_entry_template.md`.
4. Update `source_map.md`, `story_bank_provenance_map.md`, and `story_bank_changelog.md` when adding/editing stories.
5. Run validation:
   - `python scripts/validate_story_bank.py`
6. For a target role:
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
- `scripts/ingest_historical_resumes.py`
  - Ingests historical resumes from `.md`, `.txt`, and `.pdf`
  - Uses `pdftotext` for PDF extraction and emits a normalized historical bullet inventory
- `scripts/link_historical_bullets.py`
  - Links extracted historical bullets to story-bank stories using lightweight heuristic similarity
- `scripts/report_story_coverage.py`
  - Reports which stories are well represented, partially represented, or uncovered by historical bullets
- `scripts/generate_candidate_bullets.py`
  - Generates reviewable candidate bullets with reuse-first origin labels:
    - `historical_reuse`
    - `historical_adaptation`
    - `story_synthesis`
- `scripts/extract_story_candidates.py`
  - Heuristic transcript-to-candidate-story extractor (deterministic, standard-library-only)
  - Emits markdown candidate entries, mapping notes, and open questions for review
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
- New or updated stories should include `### Structured Metadata` using the schema in `templates/story_entry_template.md`.
- Keep `master_story_bank.md` authoritative until splitting is required.

## Phase 2 Workflow

Phase 2 is reuse-first and history-aware.

1. Ingest historical resumes into a normalized bullet inventory:
   - `python3 scripts/ingest_historical_resumes.py --resume resumes/base_resume/daavid_stein_base_resume.md --resume resumes/tailored/medium/resume.pdf --output /tmp/resume_story_bank_temp/historical_bullets.json --format both`
2. Link extracted bullets to reviewed stories:
   - `python3 scripts/link_historical_bullets.py --historical-bullets /tmp/resume_story_bank_temp/historical_bullets.json --master-story-bank data/processed/master_story_bank.md --output /tmp/resume_story_bank_temp/linked_historical_bullets.json --format both`
3. Produce a coverage report:
   - `python3 scripts/report_story_coverage.py --linked-historical-bullets /tmp/resume_story_bank_temp/linked_historical_bullets.json --master-story-bank data/processed/master_story_bank.md --output /tmp/resume_story_bank_temp/story_coverage.json --format both`
4. Generate candidate bullets with reuse/adaptation before synthesis:
   - `python3 scripts/generate_candidate_bullets.py --linked-historical-bullets /tmp/resume_story_bank_temp/linked_historical_bullets.json --master-story-bank data/processed/master_story_bank.md --job-description jobs/job_descriptions/example_role.md --output /tmp/resume_story_bank_temp/candidate_bullets.json --format both`

PDF notes:

- PDF resume ingestion uses `pdftotext`; scanned or image-only PDFs are not supported in Phase 2.
- Extracted PDF bullets are best-effort review artifacts, not canonical source material.
- `pdfinfo` is used only for page-count/debug metadata when available.

Review labels for early manual evaluation:

- `factually_unsupported`
- `overstated_ownership`
- `overstated_impact`
- `wrong_emphasis`
- `redundant_or_low_value`
- `acceptable_with_edits`
- `strong_as_is`

## Quick Start

```bash
cd resume_story_bank
python3 scripts/validate_story_bank.py
python3 scripts/ingest_historical_resumes.py --resume tests/fixtures/sample_base_resume.md --resume resumes/tailored/medium/resume.pdf --output /tmp/resume_story_bank_temp/historical_bullets.json --format both
python3 scripts/link_historical_bullets.py --historical-bullets /tmp/resume_story_bank_temp/historical_bullets.json --master-story-bank tests/fixtures/sample_story_bank.md --output /tmp/resume_story_bank_temp/linked_historical_bullets.json --format both
python3 scripts/report_story_coverage.py --linked-historical-bullets /tmp/resume_story_bank_temp/linked_historical_bullets.json --master-story-bank tests/fixtures/sample_story_bank.md --output /tmp/resume_story_bank_temp/story_coverage.json --format both
python3 scripts/generate_candidate_bullets.py --linked-historical-bullets /tmp/resume_story_bank_temp/linked_historical_bullets.json --master-story-bank tests/fixtures/sample_story_bank.md --job-description tests/fixtures/sample_job_description.md --output /tmp/resume_story_bank_temp/candidate_bullets.json --format both
python3 scripts/extract_story_candidates.py --input tests/fixtures/sample_transcript.md --master-story-bank tests/fixtures/sample_story_bank.md --output /tmp/resume_story_bank_temp/candidate_stories.md
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
- `make extract-story-candidates TRANSCRIPT=<path> STORY_BANK=<path> EXTRACTION_OUTPUT=<path>`
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
