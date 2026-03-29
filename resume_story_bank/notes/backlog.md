# Backlog

## Backlog Hygiene Rules

- At end of each work session, update this file before commit.
- For each item touched that session, do exactly one:
  - mark it completed by appending `DONE (YYYY-MM-DD, <short note or commit>)`
  - mark it `WONTDO (YYYY-MM-DD, <reason>)`
  - keep it open and add a one-line blocker note
- Do not leave partially addressed items without a status update.
- If an item is split, replace it with explicit child items and close the parent as `DONE (split)`.
- During planning, prefer deleting stale TODOs over carrying ambiguous duplicates forward.

## Next Session (Embedding Tailoring)

- Implement embedding-driven story selection in production mode:
  - set `--embedding-backend openai` as default for real runs
  - keep `local_hash_v1` only as offline fallback/test mode
- Add story-name mapping in `selection_report.json` and user-facing outputs:
  - map `story_id` -> story title from `master_story_bank.md`
- Add richer selection rationale:
  - show matched JD chunk text, semantic score, lexical overlap, and final weighted score
  - include top matched story chunk label (`context/actions/outcomes/skills`)
- Add one end-to-end “real JD URL -> tailored resume” example command to README.

## Near Term

- Add at least 10 high-quality stories from existing career material.
- Replace `TBD` metrics with verified numbers where possible.
- Add role-family tags (e.g., platform, data, product, leadership).
- Add one complete one-shot tailoring example in `resumes/tailored/`.
- Add `scripts/fetch_embeddings.py` for explicit embedding precompute runs (resume/JD/story bank).
- Persist tailoring run artifacts under a stable run directory (inputs + model + selection report + metadata).

## Medium Term

- Improve validation checks (e.g., source reference path existence).
- Define story quality rubric (evidence strength, relevance, recency).
- Add script support for generating traceability maps.
- Add retry/backoff and clear failure handling for OpenAI embedding API calls.
- Add cache versioning/invalidation when embedding model changes.
- Add optional cache compaction/pruning command.

## Future (RAG Readiness)

- Consider splitting stories into per-file markdown when corpus grows.
- Replace line-based JD chunking with section-aware semantic chunking.
- Add hybrid retrieval (semantic + keyword/BM25) and optional reranker.
- Define retrieval evaluation set for tailoring quality.
- Add offline eval metrics (top-k recall of expected stories, explanation quality checks).
