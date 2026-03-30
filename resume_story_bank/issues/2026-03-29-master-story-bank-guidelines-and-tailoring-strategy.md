# Master Story Bank Guidelines And Tailoring Strategy

Date: 2026-03-29
Priority: Highest
Status: Open

## User Question

What are our current guidelines for content inclusion in the master story bank? How is it currently being used / how do we plan to use it for tailoring resumes? Since we will be using LLMs and embedding/chunking approaches as well as agents to do tailoring, do those guidelines need to be updated?

## Response

### Current Guidelines

The current inclusion rule is evidence-first and fairly broad: a story belongs in the master bank if it is a concrete, reusable accomplishment that could plausibly stand alone as a resume bullet, even if it is only a feature, sprint, investigation, prototype, or intervention rather than a full project.

The repo explicitly biases toward inclusion of distinct, resume-relevant accomplishments and against collapsing meaningfully different work into one story.

The other strong rule is factual fidelity:

- processed artifacts can be reorganized for retrieval usefulness
- they cannot invent metrics, chronology, employer context, or outcomes
- uncertainty should stay explicit
- provenance is mandatory via `Source References`, `source_map.md`, and related provenance/changelog files

### How It Is Currently Used

In the docs, the intended use is:

- raw materials -> reviewed story bank -> resume tailoring with JD + company notes + base resume

The story bank is supposed to provide evidence for story selection and traceability, not be the whole candidate model.

In the code, the current baseline is narrower than the docs imply:

- `tailor_resume_model.py` selects and orders existing summary and experience bullets from the base resume
- the master story bank is used to rank stories against the JD and attach `traceability` story IDs to chosen bullets
- it does not yet generate new bullets from story-bank content
- current tailoring is deterministic selection only, not rewrite/generation

Also important: retrieval currently embeds only these story fields:

- `title`
- `context`
- `actions`
- `outcomes`
- `skills_keywords`

Optional `Tailoring Notes` are present in the template but are not currently consumed by the parser/chunker.

### Whether The Guidelines Need Updating

Yes, but mainly by extension rather than replacement.

The current rules already establish the right fundamentals for LLM and agent use:

- evidence-backed only
- explicit provenance
- story bank is not the whole profile
- deterministic fallback exists

What is missing is guidance for retrieval-oriented and agent-oriented structure.

Recommended updates:

- Distinguish `evidence fields` from `retrieval fields`.
- Require normalized tailoring metadata for each story, such as role-family tags, domain tags, recency, ownership level, and confidence.
- Either promote `Tailoring Notes` into the parsed schema or stop implying they matter operationally.
- Turn story quality into an explicit rubric: evidence strength, relevance, recency, and rewrite safety.
- Add explicit generation constraints for agentic tailoring.

Suggested operating rule:

Keep the current inclusion policy, but update the schema and guidelines so the story bank is optimized for three separate uses:

- retrieval
- generation
- audit

Right now it is strong for audit, decent for retrieval, and only partially ready for LLM and agent generation.

## Follow-Up Recommendation

Convert this into:

- a doc update in `AGENTS.md`
- a doc update in `README.md`
- a schema extension proposal for `master_story_bank.md`
