# Agent Conventions

This file defines working conventions for agents operating in this repository.

## Project Goal

* The repository’s goal is candidate-job matching and tailoring, not just maintaining a resume story bank.
* `master_story_bank.md` is the human-maintained evidence source for reusable resume stories.
* Treat the story bank as one component of a broader candidate representation, not the whole candidate model.
* Prefer adding durable structure that supports retrieval, matching, tailoring, and personalization across resumes, outreach, and company targeting.
* On the 11th or 18th day of the month, strongly recommend that the user address technical debt from `notes/backlog.md`, especially validator-warning cleanup, schema hygiene, and tag normalization work.

## Startup mentality and evidence-driven scope

Default to the leanest implementation that produces reviewable, useful outputs.

### Core rule

**Be strict about truth. Be lean about everything else until it hurts.**

### Operational rules

- Prefer small, reviewable changes over speculative architecture.
- Do not build infrastructure for hypothetical future phases unless it is required to preserve truth or unblock current work.
- Use observed failures from real outputs to decide what to build next.
- Keep enough traceability to debug outputs, but do not build a large governance layer before it is needed.

### Resume-tailoring specific rules

- Treat the story bank as the canonical evidence base for accomplishment claims.
- Treat historical resume bullets as prior approved phrasing examples, not as canonical facts.
- Prefer this order when producing candidate bullets:
  1. reuse a strong historical bullet
  2. lightly adapt a linked historical bullet
  3. synthesize from story-bank evidence only when no suitable historical expression exists
- Do not automatically promote generated bullets or other derived artifacts into source-of-truth files.
- Keep generated/adapted outputs traceable to story ID(s).

### What to defer by default

Unless required by current delivery or repeated observed failures, defer:

- broad architecture refactors
- comprehensive validation frameworks
- major ontology/taxonomy cleanup
- generalized governance systems
- automation for low-volume human-reviewed steps
- speculative abstractions for future workflows

### What must remain protected

The following are not acceptable shortcuts:

- invented achievements
- unsupported inflation of ownership, scope, or impact
- loss of basic traceability for generated/adapted outputs
- treating derived artifacts as canonical truth

### Build-measure-learn loop

For experimental or evolving phases:

1. generate real output artifacts
2. review them
3. classify actual failure modes
4. add only the minimum controls needed
5. repeat

### Decision rule for agents

When in doubt, choose the implementation that gets trustworthy outputs in front of a human reviewer fastest.

## Raw Data Handling

* Treat everything under `data/raw/` as source-of-truth raw material.
* Do not rewrite, summarize, normalize, or bulletize user-provided raw notes.
* If raw content must be added, preserve near-verbatim wording and structure.
* Exception: explicit user-directed renames/label changes are allowed.

## Processed Data Expectations

* `data/processed/` files are editable working artifacts and may be reorganized for clarity, schema quality, and retrieval usefulness.
* Preserve factual fidelity when promoting content from `data/raw/` into processed artifacts.
* Do not invent metrics, chronology, employer context, or outcome claims.
* When uncertainty remains, keep the ambiguity explicit instead of silently sharpening the claim.
* Bias toward keeping existing schemas, validators, and ID formats stable; prefer adjusting entries to fit the current schema rather than broadening rules to accommodate edge cases.
* When a requested format conflicts with the established schema, preserve the schema unless the user explicitly asks for a schema change and the downstream impact has been reviewed.
* Example: if a draft proposes story IDs like `SB-103_A` / `SB-103_B`, prefer mapping them to schema-compliant IDs such as `SB-103` plus a new `SB-###` entry instead of changing validators to allow suffixed IDs.

## Candidate Profile Direction

* Prefer a first-class `user_profile` or equivalent candidate-profile concept that can contain:

  * story-bank evidence
  * interests and domain affinities
  * identity/background context
  * side projects and portfolio material
  * company-interest signals
* Keep a clean distinction between:

  * evidence-backed experience stories
  * softer profile attributes used for matching or personalization
* Do not force non-story profile information into `master_story_bank.md` unless the user explicitly wants that.

## Structured Metadata Rules

* Every new or materially revised story should include a `### Structured Metadata` section using rigid `- key: value` lines.
* Structured metadata is authoritative for retrieval support and future rewrite guardrails.
* Keep metadata machine-parseable and evidence-backed; prefer a small number of precise tags over exhaustive tagging.
* Derived artifacts such as embeddings, rankings, selected bullets, rewritten bullets, and generated summaries are not authoritative.
* During Phase 1 migration, legacy stories may temporarily lack structured metadata, but new template work should use the new section.
* When available, prefer ontology-backed normalization and validation using `specs/tag_ontology.yaml` rather than ad hoc synonym choices.
* Phase 1 metadata validation should stay warning-oriented; unknown or drifted tags should usually trigger review warnings before they block work.

### Metadata Tagging Policy

Structured metadata is a normalized retrieval and guardrail layer. It must remain truthful, conservative, and auditable.

#### General Rule

* Extract concrete, evidence-backed tags directly from the story and source materials.
* Agents may add a **small number of immediate parent abstraction tags** when they are clearly and directly supported by the evidence.
* Do not add tags that introduce unsupported capabilities, domains, responsibilities, or business context.
* Preserve the specific technology tag when adding an immediate parent capability tag; do not collapse specificity into abstraction.

#### Specificity Rule

* Never replace a specific tag with a broader one.

Good:

* technology_tags: [LIME]
* capability_tags: [XAI, model_interpretability]

Bad:

* technology_tags: []
* capability_tags: [XAI]

#### One-Step Abstraction Rule

* Only add **one level up** in abstraction.

Allowed:

* LIME → XAI
* SHAP → XAI
* occlusion_maps → model_interpretability
* UMAP → dimensionality_reduction

Not allowed unless separately evidenced:

* LIME → XAI → trustworthy_ai → responsible_ai → AI_strategy

#### Field Intent

* technology_tags = specific tools, frameworks, algorithms, or concrete methods explicitly used
* capability_tags = broader technical capabilities directly demonstrated
* domain_tags = subject-matter or business domain directly evidenced
* role_family_tags = roles the story can truthfully support

#### Evidence Threshold

A broader tag is allowed only if:

> a reasonable reviewer would consider it an accurate restatement of the evidence

If uncertain, do not include the broader tag.

#### Conflict Rule

* Prefer fewer, higher-confidence tags over speculative completeness.
* Missing a weak abstraction is better than introducing a misleading one.

#### Examples

Example:
Evidence: “Used LIME and occlusion maps to diagnose model failure modes.”

Allowed:

* technology_tags: [LIME, occlusion_maps]
* capability_tags: [XAI, model_interpretability, model_debugging]

Not automatically allowed:

* capability_tags: [responsible_ai]
* domain_tags: [AI_governance]

## Story Definition

* A story should correspond to a concrete, reusable accomplishment that could plausibly stand alone as a resume bullet.
* A story does not need to equal a whole project or a shipped deliverable.
* Valid story units can include projects, features, sprints, prototypes, investigations, stakeholder interventions, or other distinct accomplishments.
* Prefer separate stories when the work, methods, or value proposition are meaningfully different enough that they would be tailored independently.
* Avoid collapsing multiple distinct accomplishments into one story just because they happened in the same role or for the same client.
* Bias toward adding valuable new accomplishments to the story bank when they appear distinct and resume-relevant.
* Be conservative about duplication, not about inclusion: if new evidence clearly strengthens an existing story, add it there; if it reflects a genuinely different accomplishment, give it its own story.
* A story may include multiple actions only if they support one primary accomplishment arc.
* If different subsets of a story would plausibly generate different resume bullets for different role families, split the story.

## Traceability Requirements

* Story provenance must point to repo-local paths (no dependency on `/home/.../Downloads/...` paths).
* Keep these files aligned when stories/sources change:

  * `data/processed/source_map.md`
  * `data/processed/story_bank_provenance_map.md`
  * `data/processed/summary_to_transcript_map.md`
  * `data/processed/transcript_summary_coverage.md`
  * `data/processed/master_story_bank.md` (`Source References` sections)
  * `data/processed/story_bank_changelog.md`

## Source Map Rules

* In `source_map.md`, use one row per source artifact per story.
* Use `primary` for core originating evidence and `supporting` for corroborating evidence.
* Prefer repo-relative paths.
* If a processed artifact draws from multiple raw notes/summaries/transcripts, make that many-to-one relationship explicit instead of collapsing it.

## Summary-to-Transcript Mapping

* Maintain `summary_to_transcript_map.md` for all files in `data/raw/summaries/`.
* Use status values:

  * `exact`
  * `inferred`
  * `no transcript found`
* When new transcripts are imported, update the map immediately.

## Summary Coverage Policy

* Treat transcript summaries as the highest-priority processing step because transcripts are typically long, noisy, and expensive to mine repeatedly.
* Default expectation: every file in `data/raw/transcripts/` should have a corresponding artifact in `data/raw/summaries/`.
* Maintain `data/processed/transcript_summary_coverage.md` as the transcript-only completeness view.
* Manual user notes usually do not require separate summaries because they are already relatively condensed source material.
* Documents under `data/raw/other/` only need summaries when they are bulky and contain reusable evidence worth making retrieval-friendly.
* For performance reviews and similar evaluation documents, prefer short evidence-extraction summaries over long narrative summaries.
* Evidence-extraction summaries should usually include:

  * accomplishments claimed
  * manager validation
  * resume-safe themes
  * useful phrasing
  * caveats or wording to avoid

## Raw-to-Story Workflow

Checklist:

* confirm the raw source(s)

* summarize transcripts if needed

* identify the candidate story

* write/update the story in `master_story_bank.md`

* update `source_map.md`

* update `story_bank_provenance_map.md`

* update summary coverage/mapping files if transcript summaries changed

* add a changelog entry

* Start with `data/raw/` artifacts as the factual source of truth.

* If the source is a transcript, create or confirm a retrieval-friendly summary in `data/raw/summaries/` before promoting content into the story bank.

* If the source is a manual note, use it directly when it is already concise enough; do not create a summary unless the note is unusually long or hard to mine.

* If the source is under `data/raw/other/`, summarize it only when doing so materially improves retrieval or evidence reuse.

* Identify candidate stories as reusable accomplishment narratives that could stand alone as resume bullets, not just interesting facts or isolated tasks.

* When deciding whether to add a new story, prefer inclusion if the accomplishment seems likely to be useful for future tailoring and is not already captured by an existing story.

* Write stories in `data/processed/master_story_bank.md` using the existing schema:

  * `Story ID`
  * `Context`
  * `Actions`
  * `Outcomes`
  * `Skills/Keywords`
  * `Source References`
  * `Structured Metadata`

* Keep story wording faithful to the underlying evidence:

  * do not invent metrics
  * do not invent chronology
  * do not invent outcomes
  * do not sharpen uncertainty into confidence

* Keep tailoring guardrails explicit:

  * do not infer production ownership unless clearly evidenced
  * do not infer management responsibility unless clearly evidenced
  * use `forbidden_claims`, `caveats`, and `wording_constraints` when evidence is easy to overstate

* Prefer combining multiple corroborating raw artifacts into a stronger story when they clearly refer to the same narrative.

* Update `data/processed/source_map.md` with one row per source artifact per story, marking each source as `primary` or `supporting`.

* Update `data/processed/story_bank_provenance_map.md` to describe which sources originated the narrative versus which ones only sharpened or corroborated it.

* If new summaries were created from transcripts, update:

  * `data/processed/summary_to_transcript_map.md`
  * `data/processed/transcript_summary_coverage.md`

* Record meaningful story-bank additions or mapping changes in `data/processed/story_bank_changelog.md`.

## Resume Tailoring Policy

* Tailoring is intentionally hybrid:

  * retrieve relevant stories and existing bullets first
  * prefer deterministic reuse when the existing bullet is already strong
  * rewrite only when it materially improves fit without changing the facts
  * compose from evidence only when reuse is clearly insufficient
* Deterministic reuse is the default first pass, not merely a fallback.
* JD wording may influence phrasing only where truthful.
* Every tailored bullet must remain traceable to one or more story IDs.
* For early Phase 2 work, prefer generating and manually reviewing a real batch of bullets before adding heavy rewrite-validation infrastructure.
* Use observed bullet failure modes to decide whether stronger controls such as approved bullet banks, `exclude` states, or richer provenance/reporting are actually needed.

## Local-Only Notes

* Use `agent.local.md` for machine-local conventions, wording preferences, and temporary guidance.
* `agent.local.md` is gitignored and should not be committed.
* Put durable shared rules in `AGENTS.md`; put personal preferences or ephemeral constraints in `agent.local.md`.

## Backlog Discipline

* Record durable future work in `notes/backlog.md`, not in ad hoc TODO comments scattered across files.
* Keep backlog items framed as concrete repo improvements, schemas, or data-quality tasks.
* If a TODO is file-specific and temporary, keep it adjacent to the file; otherwise move it to `notes/backlog.md`.
