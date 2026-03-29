# Agent Conventions

This file defines working conventions for agents operating in this repository.

## Project Goal

- The repository’s goal is candidate-job matching and tailoring, not just maintaining a resume story bank.
- Treat the story bank as one component of a broader candidate representation.
- Prefer adding durable structure that supports retrieval, matching, tailoring, and personalization across resumes, outreach, and company targeting.

## Raw Data Handling

- Treat everything under `data/raw/` as source-of-truth raw material.
- Do not rewrite, summarize, normalize, or bulletize user-provided raw notes.
- If raw content must be added, preserve near-verbatim wording and structure.
- Exception: explicit user-directed renames/label changes are allowed.

## Processed Data Expectations

- `data/processed/` files are editable working artifacts and may be reorganized for clarity, schema quality, and retrieval usefulness.
- Preserve factual fidelity when promoting content from `data/raw/` into processed artifacts.
- Do not invent metrics, chronology, employer context, or outcome claims.
- When uncertainty remains, keep the ambiguity explicit instead of silently sharpening the claim.

## Candidate Profile Direction

- Prefer a first-class `user_profile` or equivalent candidate-profile concept that can contain:
  - story-bank evidence
  - interests and domain affinities
  - identity/background context
  - side projects and portfolio material
  - company-interest signals
- Keep a clean distinction between:
  - evidence-backed experience stories
  - softer profile attributes used for matching or personalization
- Do not force non-story profile information into `master_story_bank.md` unless the user explicitly wants that.

## Traceability Requirements

- Story provenance must point to repo-local paths (no dependency on `/home/.../Downloads/...` paths).
- Keep these files aligned when stories/sources change:
  - `data/processed/source_map.md`
  - `data/processed/story_bank_provenance_map.md`
  - `data/processed/summary_to_transcript_map.md`
  - `data/processed/master_story_bank.md` (`Source References` sections)
  - `data/processed/story_bank_changelog.md`

## Source Map Rules

- In `source_map.md`, use one row per source artifact per story.
- Use `primary` for core originating evidence and `supporting` for corroborating evidence.
- Prefer repo-relative paths.
- If a processed artifact draws from multiple raw notes/summaries/transcripts, make that many-to-one relationship explicit instead of collapsing it.

## Summary-to-Transcript Mapping

- Maintain `summary_to_transcript_map.md` for all files in `data/raw/summaries/`.
- Use status values:
  - `exact`
  - `inferred`
  - `no transcript found`
- When new transcripts are imported, update the map immediately.

## Local-Only Notes

- Use `agent.local.md` for machine-local conventions, wording preferences, and temporary guidance.
- `agent.local.md` is gitignored and should not be committed.
- Put durable shared rules in `AGENTS.md`; put personal preferences or ephemeral constraints in `agent.local.md`.

## Backlog Discipline

- Record durable future work in `notes/backlog.md`, not in ad hoc TODO comments scattered across files.
- Keep backlog items framed as concrete repo improvements, schemas, or data-quality tasks.
- If a TODO is file-specific and temporary, keep it adjacent to the file; otherwise move it to `notes/backlog.md`.
