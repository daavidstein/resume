## Story Bank Data Model

The repository uses three classes of information:

1. **Evidence fields**
   - Human-maintained source-of-truth story content.
   - Used for auditability and final claim grounding.
2. **Structured metadata**
   - Human/agent-maintained retrieval and generation-control fields.
   - Used for ranking, match interpretation, and rewrite guardrails.
3. **Derived artifacts**
   - Embeddings, chunk rankings, selected bullets, and generated outputs.
   - These are disposable and must never be treated as source of truth.

## Tailoring Strategy

The tailoring system is intentionally hybrid:
- first retrieve and score existing reusable bullets and story evidence
- then decide whether each candidate should be reused, lightly rewritten, composed from evidence, or excluded
- always preserve traceability from tailored bullet back to story ID(s)

Deterministic reuse remains the default first pass. Rewrite/generation is a refinement layer used only when it creates a meaningful fit improvement.

## Candidate Profile Separation

Softer matching / personalization data should live outside `master_story_bank.md` in a separate candidate-profile artifact.
This information may influence ranking and framing, but it must not be used as direct evidence for accomplishment claims.

## Migration Note

Structured metadata rollout should be staged:
- update template and parser first
- allow temporary backward compatibility for legacy stories
- validate non-strictly during migration
- tighten validation once enough of the story bank has been upgraded
