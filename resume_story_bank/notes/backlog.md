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

## First Thing

- Review and resolve highest-priority issue note on story-bank inclusion guidelines vs. LLM/embedding/agent tailoring strategy before other backlog work.
  Reference: `/home/daavid/PycharmProjects/resume/resume_story_bank/issues/2026-03-29-master-story-bank-guidelines-and-tailoring-strategy.md`
  Requirement: bring this up first at the start of the next session.

## Next Session (Phase 2 Planning, Provisional)

- Phase 2 is provisional pending Phase 1 migration results, especially parser complexity and metadata coverage.
- Add first-class bullet-bank support for reusable summary and experience bullets.
- Define bullet-level provenance linking each reusable bullet to story ID(s).
- Add bullet handling states: `reuse_verbatim`, `light_rewrite`, `compose_from_story`, `exclude`.
- Add score-based decision logic for when rewrite is worth attempting.
- Add constrained rewrite for top selected bullets only.
  - enforce fact/number preservation checks
  - use `rewrite_safety`, `caveats`, `wording_constraints`, and `forbidden_claims`
  - auto-fallback to original selected bullet on validation failure
- Add adaptive rewrite/generation mode with confidence gating only after the deterministic path is stable.
  - allow evidence-backed new bullet generation only when confidence is high
  - keep deterministic selection-only fallback when confidence is low or API calls fail
- Add evaluation/reporting for why a bullet was reused vs rewritten vs excluded.
- Preserve the deterministic baseline path even when LLM-assisted rewrite is available.
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
- Review `data/raw/manual_user_notes/resume optimization context.md` for additional accomplishment-sized story candidates and corroborating detail.
  - strengthen `SB-108` (Blueprint Churn Prediction) with additional evidence if available
  - decide whether Blueprint product-improvement analysis (`ANOVA` / `t-tests` / `bootstrapping`) should become its own story
- Replace `TBD` metrics with verified numbers where possible.
- Continue migrating legacy stories to `### Structured Metadata`, starting with role-family and evidence-strength coverage.
- Define a first-class `user_profile` concept that contains the story bank as one component rather than treating the story bank as the whole candidate representation.
- Add user-profile sections for broader candidate attributes relevant to job matching and tailoring:
  - domain interests/topics: fraud, legal, rare diseases, sales and marketing
  - personal interests: aviation, gaming
  - identity/background: Jewish, teacher, business owner
  - side projects/portfolio: GitHub projects
  - behavioral/context signals: shopping habits or other consumer-interest patterns if useful
- Add support for company-interest tracking as profile input, including optionally deriving followed companies from LinkedIn or similar sources.
- Decide which profile attributes are used for retrieval/matching vs. only for tailoring/personalization.
- Add one complete one-shot tailoring example in `resumes/tailored/`.
- Add a single `make` pipeline target (e.g., `make pipeline`) to run tailor -> validate model -> generate resume artifacts.
- Add `scripts/fetch_embeddings.py` for explicit embedding precompute runs (resume/JD/story bank).
- Persist tailoring run artifacts under a stable run directory (inputs + model + selection report + metadata).
- Add S3 persistence for story-bank data (`data/raw`, `data/processed`, and tailoring run artifacts) with versioned snapshots.
- Evaluate adopting DaggerML (Aaron Niskin) for pipeline orchestration/versioned data lineage in this project.

## Phase 3 Planning (Provisional)

- Phase 3 is provisional pending how much signal the new structured metadata adds in practice.
- Review overloaded stories and split high-priority ones first.
  - start with `SB-103`, `SB-107`, and possibly `SB-102`
- Add lightweight hygiene checks to flag stories with too many technical centers of gravity or overly broad keyword/topic spread.
- Create `data/processed/candidate_profile.md` or equivalent structured artifact.
- Define how candidate-profile data can influence ranking and framing without being treated as accomplishment evidence.
- Add a cleanup workflow/prompt for periodic story-bank maintenance.
- Revisit retrieval weighting after enough metadata coverage and split-story cleanup has been completed.

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
