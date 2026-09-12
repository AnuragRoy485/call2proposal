# Submission package index

Everything Crework needs, in one place.

## Links
- Live app: https://call2proposal.vercel.app
- Live API: https://call2proposal-api.vercel.app (`/health` discloses the active provider)
- Repository: https://github.com/AnuragRoy485/call2proposal

## What is in the repo
- `README.md` - what it is, why, how to run locally, deployment layout
- `docs/case-study.md` - the article-style write-up (Shikshita pattern: pain, TLDR, What this builds, numbered steps, prompts and wiring, testing, cost, failure handling)
- `docs/architecture.md` - component and provider design, safety invariants, persistence decision
- `docs/prompts.md` - the provider-neutral prompt contracts
- `docs/evaluation.md` - the safety evaluation matrix and trap cases
- `docs/topic-ideas.md` - five other buildathon topic ideas
- `docs/video-script.md` - the walkthrough video script
- `docs/screenshot-plan.md` - which screenshots document the workflow
- `docs/submission-questions.md` - open questions for Crework about delivery mechanics
- `samples/` - the fully fictional transcript and past proposals
- `backend/tests/` - 15 tests, all passing (evidence, conflicts, price-leak traps, export gate, provider guard)

## Artifacts delivered with the submission
- Screenshots: input view, live result view with evidence quotes and blockers, approved-for-export state
- Screen recording GIF of the full loop
- Walkthrough video (per docs/video-script.md)

## Verified live behavior (production URLs, 2026-09-12)
- Real Gemini 2.5 Flash draft in ~7s, provider disclosed as `gemini` in the run footer
- Missing budget stays "To be confirmed" with a blocker - nothing invented
- Conflicting facts (two different goals) raise a blocker instead of a silent pick
- Retrieved historical sections are visible in the UI and marked as style reference only
- DOCX export returns a valid Word file only after human approval; unapproved export is rejected with HTTP 409
