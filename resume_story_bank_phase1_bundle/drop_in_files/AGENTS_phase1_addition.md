## Story Bank Purpose

- `master_story_bank.md` is the human-maintained evidence source for reusable resume stories.
- It is optimized for three uses:
  - retrieval
  - constrained generation
  - audit / traceability
- The story bank is **not** the full candidate model.
- Softer matching / personalization data belongs in a separate candidate-profile artifact unless the user explicitly requests otherwise.

## Story Construction Rules

- Prefer atomic, reusable accomplishment stories over umbrella stories.
- A story may describe a feature, sprint, investigation, prototype, intervention, or communication effort if it could plausibly support a resume bullet.
- Do not merge adjacent but distinct accomplishments merely because they came from the same role or project.
- If a story could reasonably support different bullet themes for different role families, split it.

## Structured Metadata Rules

- Every story should include a `### Structured Metadata` section using rigid key-value lines.
- Metadata must remain machine-parseable and should not rely on free-form prose.
- Metadata is authoritative for retrieval and generation guardrails.
- Derived artifacts such as embeddings, similarity scores, selected bullets, and rewritten bullets are not authoritative.

## Resume Tailoring Policy

- Use a hybrid strategy:
  1. retrieve relevant stories and existing bullets first
  2. prefer reuse when the existing bullet is already strong
  3. use rewrite only when it creates a meaningful fit improvement
  4. use composition from story evidence only when reuse is clearly insufficient
- All tailored bullets must remain traceable to one or more story IDs.
- Tailoring may adapt wording to the JD where truthful, but must not invent technologies, ownership, scale, or production scope.
- Deterministic reuse is the default first pass, not merely a fallback.

## Anti-Overstatement Rules

- Do not infer production ownership unless clearly evidenced.
- Do not infer management responsibility unless clearly evidenced.
- Do not invent deployment scope, user scale, revenue impact, or experimentation results.
- Preserve ambiguity explicitly when the source evidence is ambiguous.
- Use `forbidden_claims`, `caveats`, and `wording_constraints` to constrain rewrite behavior.

## Story Splitting Rule

- A story may include multiple actions only if they support one primary accomplishment arc.
- If different subsets of a story would plausibly generate different resume bullets for different role families, split the story.
- Trigger targeted review when a story contains more than one primary business/problem frame or more than three distinct technical centers of gravity.

## Cleanup / Hygiene Policy

- Periodically flag potentially overloaded stories.
- Prefer targeted cleanup of flagged stories over broad stylistic rewrites of the entire bank.
- Story splitting is an ongoing quality-control mechanism, not a one-time cleanup only.
