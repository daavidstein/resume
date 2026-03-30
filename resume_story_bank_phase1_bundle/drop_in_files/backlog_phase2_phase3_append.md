## Phase 2 — Hybrid tailoring pipeline

- Introduce first-class bullet-bank support for reusable summary/experience bullets.
- Define bullet-level provenance linking each reusable bullet to story ID(s).
- Add bullet handling states: `reuse_verbatim`, `light_rewrite`, `compose_from_story`, `exclude`.
- Add score-based decision logic for when rewrite is worth attempting.
- Add constrained rewrite rules using `rewrite_safety`, `caveats`, `wording_constraints`, and `forbidden_claims`.
- Add evaluation/reporting for why a bullet was reused vs rewritten vs excluded.
- Preserve deterministic baseline path even when LLM-assisted rewrite is available.

## Phase 3 — Bloat control and candidate profile separation

- Review overloaded stories and split high-priority ones first (`SB-103`, `SB-107`, possibly `SB-102`).
- Add lightweight hygiene checks to flag stories with too many technical centers of gravity or overly broad keyword/topic spread.
- Create `data/processed/candidate_profile.md` or equivalent structured artifact.
- Define how candidate-profile data can influence ranking/framing without being treated as accomplishment evidence.
- Add cleanup workflow/prompt for periodic story-bank maintenance.
- Revisit retrieval weighting after enough metadata and split-story cleanup has been completed.

## Planning note

- Phase 2 and Phase 3 plans are intentionally provisional.
- Implement Phase 1 first, then revise later phases based on parser complexity, migration friction, and how much signal the new structured metadata actually adds in practice.
