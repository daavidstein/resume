# Story Extraction Prompt

You are extracting reusable resume stories from raw interview/career material.

## Inputs

- Transcript(s), notes, or summaries from `data/raw/`
- Existing `master_story_bank.md` (to avoid duplicates)

## Task

Convert raw material into normalized story entries using the template fields in:

- `templates/story_entry_template.md`

## Extraction Rules

- Keep entries factual and auditable.
- Capture concrete actions and measurable outcomes where available.
- Separate distinct stories; do not merge unrelated situations.
- If metrics are missing, keep placeholders as `TBD` rather than guessing.
- Suggest tags/skills that improve retrieval later.

## Deduplication Guidance

- Reuse existing story IDs when content is materially the same.
- Create a new story ID when scope, problem, or outcome differs.

## Output

1. Candidate story entries in markdown.
2. Proposed story IDs (`SB-###`).
3. Mapping notes from source material -> story IDs.
4. Open questions for missing facts.
