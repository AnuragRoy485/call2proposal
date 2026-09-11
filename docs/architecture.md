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

The demo uses a deterministic provider because no LLM credential was available in the connected vault at build time. The boundary is deliberate: a production model provider can implement the same typed response without changing review or verification rules.

## Decisions
- Human review is a product state, not a disclaimer.
- Unknown is a valid output.
- Past proposals supply reusable language, never authority for a new price.
- Retrieval operates on sections rather than sending the whole archive.
- No CRM, auth, billing or email integration in the first build.
