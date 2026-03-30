# Structured Metadata Schema — Phase 1

## Purpose

`### Structured Metadata` is the authoritative machine-usable layer for:
- retrieval support
- future constrained rewrite support
- future guardrails against overstatement

It should be human-readable but rigid enough for standard-library parsing.

## Required Story Shape

```md
## Story: <short descriptive title>

### Story ID
SB-XXX

### Context
...

### Actions
- ...

### Outcomes
- ...

### Skills/Keywords
...

### Source References
- ...

### Structured Metadata
- role_family_tags: [ml_engineering, data_science]
- domain_tags: [edtech, assessment]
- capability_tags: [measurement, experimentation, modeling]
- technology_tags: [python, pytorch, sagemaker]
- business_problem_tags: [student_progress, recommendation_quality]
- audience_tags: [product, engineering, leadership]
- ownership_level: individual_contributor
- seniority_scope: mid
- evidence_strength: strong
- recency_bucket: recent
- rewrite_safety: medium
- preferred_resume_angles: [ml_modeling, experimentation, stakeholder_communication]
- wording_constraints: [avoid_production_ownership_claims]
- caveats: [no_confirmed_online_ab_test]
- forbidden_claims: [team_management, shipped_full_production_system]
```

## Evidence Fields

These remain the human-maintained source of truth:
- title
- context
- actions
- outcomes
- skills/keywords
- source references

## Structured Metadata Fields

### Lists
- `role_family_tags`
- `domain_tags`
- `capability_tags`
- `technology_tags`
- `business_problem_tags`
- `audience_tags`
- `preferred_resume_angles`
- `wording_constraints`
- `caveats`
- `forbidden_claims`

### Scalar enums
- `ownership_level`
- `seniority_scope`
- `evidence_strength`
- `recency_bucket`
- `rewrite_safety`

## Controlled Values

### ownership_level
- `supporting`
- `individual_contributor`
- `cross_functional_driver`
- `technical_lead`

### seniority_scope
- `junior`
- `mid`
- `senior`
- `mixed`

### evidence_strength
- `strong`
- `medium`
- `weak`

### recency_bucket
- `current`
- `recent`
- `older`
- `timeless`

### rewrite_safety
- `high`
- `medium`
- `low`

## Population Rules

- Only include tags actually supported by the story.
- Prefer a small number of precise tags over exhaustive tagging.
- `technology_tags` must be evidence-backed, not inferred from adjacent work.
- `preferred_resume_angles` can be mildly interpretive, but must remain plausibly grounded.
- `forbidden_claims` should be explicit wherever evidence is easy to overstate.
- `caveats` should preserve ambiguity rather than trying to smooth it away.

## Derived Artifacts (Not Source of Truth)

These must never be treated as authoritative:
- embeddings
- chunk scores
- rankings
- selected bullets
- rewritten bullets
- generated summaries
- selection reports
