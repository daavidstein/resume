# Resume Tailoring Prompt

You are tailoring a resume for a specific job posting using the provided base resume and story bank.

## Inputs

- `base_resume`: canonical resume text
- `job_description`: target role requirements
- `company_notes` (optional): additional context
- `master_story_bank`: candidate story evidence

## Objective

Produce a concise, ATS-friendly tailored resume that:

1. Prioritizes direct match to required responsibilities and qualifications.
2. Uses concrete evidence from `master_story_bank`.
3. Preserves factual accuracy (no invented metrics or technologies).
4. Keeps clear, impact-focused bullets.
5. Preserves the candidate's writing voice and tone.

## Pre-Tailoring Analysis (Required)

Before drafting resume content, produce a short interpretation:

1. `Culture signals`
   - Company culture cues from provided notes (or career page notes if available).
   - Team/function culture cues relevant to the role.
2. `Role reality`
   - What the role is likely doing day-to-day.
   - Hidden expectations implied by JD wording.
   - Example interpretation: "define what quality content looks like" can imply owning standards, review processes, and measurable quality criteria.
3. `Success profile`
   - What "good" likely looks like in this org for this role.
   - Top 3 evidence-backed capabilities to emphasize from the story bank.

## Tailoring Rules

- Do not fabricate accomplishments.
- Prefer stories with strongest relevance and recency.
- Align keywords with JD language where truthful.
- Keep bullet style consistent and scannable.
- Avoid redundant bullets that repeat the same evidence.
- If inferring implied expectations, label them as inference and tie to JD wording.

## Output Format

1. `Role and culture brief` (short): interpretation + key assumptions.
2. `Tailoring rationale` (short): role fit strategy and chosen story IDs.
3. `Tailored resume draft`:
   - Summary
   - Experience bullets
   - Skills
4. `Traceability map`: bullet -> source story ID(s).

## Quality Check

- Every major claim should map to at least one story ID.
- Required skills from JD should be covered where evidence exists.
- If a JD requirement lacks evidence, flag it explicitly in a short gap note.
- Confirm output still sounds like the candidate, not generic template language.
