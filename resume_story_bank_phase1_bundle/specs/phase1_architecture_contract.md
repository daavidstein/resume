# Phase 1 Architecture Contract

## Scope

Phase 1 is a **schema-and-contract alignment** phase for the existing `resume_story_bank/` project.

It should establish a stable foundation for later hybrid tailoring without yet implementing bullet rewrite/generation.

## What Phase 1 Must Achieve

1. Replace optional `### Tailoring Notes` with required `### Structured Metadata` in the story template.
2. Define a parseable metadata schema suitable for retrieval and generation guardrails.
3. Update parser code so metadata can be read from the story bank.
4. Update validator behavior so migration can proceed in stages:
   - non-strict/tolerant behavior first
   - easy path to stricter enforcement later
5. Align repo guidance so these concepts are explicit:
   - evidence fields
   - structured metadata
   - derived artifacts
6. Add backlog entries for Phase 2 and Phase 3, but do not implement them now.

## What Phase 1 Must Not Do

- Do not implement LLM bullet generation.
- Do not replace deterministic selection logic with generation.
- Do not force a full-bank manual metadata rewrite before parser support exists.
- Do not turn the story bank into the whole candidate profile.

## Tailoring Philosophy to Preserve

- Deterministic reuse is the default first pass.
- Existing strong bullets should often be reused as-is.
- Later rewrite/generation should be a refinement layer only.
- Every tailored bullet must remain traceable to story evidence.
- JD wording may influence phrasing only where truthful.

## Candidate Data Separation

The repo should explicitly distinguish:

### Story bank
Evidence-backed, reusable accomplishment stories.

### Candidate profile (future artifact)
Softer matching / personalization signals such as domain interests, background context, or preferred narrative framing.

Candidate profile data may influence ranking or framing later, but not accomplishment claims.

## Anti-Bloat Rule

A story may include multiple actions only if they support one primary accomplishment arc.
If different subsets of the story would plausibly generate different resume bullets for different role families, split the story.

## Migration Rule

Phase 1 should be staged so the repo stays usable during migration.
