# Resume Workspace

This repository contains a markdown-first resume tailoring workspace.
The main project lives in `resume_story_bank/`.

## Repo Layout

- `resume_story_bank/`: core pipeline, prompts, data, templates, scripts, tests, and resumes

## Quick Start

```bash
cd resume_story_bank
python3 scripts/validate_story_bank.py
make test-resume-pipeline
```

Sample tailoring run:

```bash
cd resume_story_bank
python3 scripts/tailor_resume_model.py \
  --base-resume resumes/base_resume/daavid_stein_base_resume.md \
  --job-description tests/fixtures/sample_job_description.md \
  --master-story-bank tests/fixtures/sample_story_bank.md \
  --output /tmp/resume_story_bank_temp/model.json \
  --page-budget 2
```

## What's Next

Active TODOs are tracked in:

- `resume_story_bank/README.md` under `Goals (Short Term TO-DO list)`
- `resume_story_bank/notes/backlog.md` for session-ready backlog and tech debt

To avoid drift, keep actionable TODO items in those files only.

## Environment

- Python: `3.11`
- Optional secrets loading via `direnv`:
  - copy `.envrc.local.example` to `.envrc.local`
  - set `OPENAI_API_KEY`
  - run `direnv allow`
