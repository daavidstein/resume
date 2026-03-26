# Resume Story Bank

`resume_story_bank` is a local, markdown-first knowledge base for reusable career stories.  
It is designed for fast resume tailoring now, and easy transition to local RAG later.

## Goals (Overall/Long-Term)

- Keep one source of truth for stories in a human-readable format.
- Preserve raw inputs (transcripts, summaries, reviews) for traceability.
- Make one-shot tailoring repeatable with prompt and template scaffolds.
- Stay lightweight: no framework, no external dependencies.

## Goals (Short Term TO-DO list)

- Implement a pre-tailoring analysis step that identifies:
  - company culture signals
  - team culture signals (for the specific function, e.g., engineering, data science)
  - implied role expectations that are not explicitly written
- Preserve the applicant's voice in final resume output (avoid generic LLM phrasing)
  - Build a voice profile and enforce it during rewriting
  - Add a scoring step to detect and correct tone drift
  - Compare outputs against baseline LLM resume generation
## Current Structure

- `prompts/`: reusable prompts for extraction and tailoring.
- `data/raw/`: source notes and interview artifacts.
- `data/processed/master_story_bank.md`: single-file source of truth.
- `data/processed/story_bank_changelog.md`: log of content-level changes.
- `data/processed/source_map.md`: link stories back to source artifacts.
- `templates/`: standard markdown templates for story entries and tailoring requests.
- `resumes/base_resume/`: canonical resume variants.
- `resumes/tailored/`: job-specific resume outputs.
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
6. Save output resume in `resumes/tailored/`.

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

## Scripts

- `scripts/validate_story_bank.py`
  - Checks each story block has an ID
  - Verifies required headers exist for each story
  - Detects duplicate story IDs
- `scripts/split_story_bank.py`
  - Placeholder utility for future migration to one-story-per-file

## Conventions

- Story IDs: `SB-###` (example: `SB-001`)
- Keep story entries complete enough to support STAR/CAR bullet generation.
- Keep `master_story_bank.md` authoritative until splitting is required.

## Quick Start

```bash
cd resume_story_bank
python3 scripts/validate_story_bank.py
python3 scripts/split_story_bank.py --help
make validate
```

## Optional: Auto-Run On Commit

To run validation automatically before each commit, configure this project's hook path once:

```bash
cd /home/daavid/PycharmProjects/resume
git config core.hooksPath resume_story_bank/.githooks
```

After that, each `git commit` will execute:

- `python3 scripts/validate_story_bank.py` from `resume_story_bank/.githooks/pre-commit`
