# Architecture and decision record

## Persona
Northstar Studio is a fictional 75-person product design and development agency serving North America and MENA. Six account directors run discovery calls. Proposal turnaround currently takes two to three days.

## Success metrics
- First reviewable draft in under 30 minutes
- 100% of extracted facts linked to transcript evidence
- Zero invented price, timeline or commitment
- External send rate: zero (out of scope)

## Pipeline
`Transcript + past proposals -> extraction -> retrieval -> drafting -> verifier -> human review -> export`

The demo defaults to a deterministic provider because no LLM credential was available in the connected vault at build time. The provider seam is implemented in `api/app/providers.py`: setting `LLM_PROVIDER` (`openai`/`anthropic`/`gemini`), `LLM_API_KEY` and optionally `LLM_MODEL` switches drafting to a live model with no code change.

The boundary is deliberate and enforced:

1. Extraction is always deterministic - every fact carries a verbatim transcript quote, so evidence linking never depends on model behavior.
2. The model receives only the extracted facts plus retrieved historical sections, with instructions that unknowns stay "To be confirmed" and history is style reference, never evidence.
3. A post-draft guard scans the model output for currency amounts; any amount not present verbatim in the transcript voids the draft (deterministic fallback + blocker flag). A model can polish prose, it cannot introduce a price.
4. A failed model call falls back to the deterministic draft with a warning flag - the workflow never hard-depends on model availability.

`/health` reports the active provider so the deployment discloses what actually generated drafts.

## Decisions
- Human review is a product state, not a disclaimer.
- Unknown is a valid output.
- Past proposals supply reusable language, never authority for a new price.
- Retrieval operates on sections rather than sending the whole archive.
- No CRM, auth, billing or email integration in the first build.
