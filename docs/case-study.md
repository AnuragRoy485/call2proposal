# I Cut the Gap Between a Sales Call and a Reviewable Proposal

## A human-reviewed workflow that turns transcript evidence and past proposal language into a grounded draft

**TLDR:** Sales-led service businesses often lose momentum after a strong discovery call because producing a tailored proposal takes days. Call2Proposal turns a transcript into a reviewable draft in minutes, retrieves useful delivery language from past proposals, links every extracted fact to an exact quote, and blocks export until a human reviews it. It does not invent pricing and it never sends anything.

## The problem

A founder or account director finishes a promising call. The prospect's pain, timing and desired outcome are still fresh, but the details sit inside a transcript while someone searches old proposals, copies sections and tries to remember what was actually promised. The delay costs momentum. A fast generic draft creates a different risk: unsupported prices, dates or promises can leave the company looking careless.

The target user is a 50-300 person service business in North America or MENA, matching Crework's ICP. The fictional test company, Northstar Studio, has 75 people and six account directors.

## What this builds

- A transcript and proposal-library input
- Structured deal facts, each with an exact source quote
- Section-level retrieval from past proposal language
- A proposal draft that preserves unknowns
- A verifier that blocks unsupported money claims
- A review gate that must be approved before export
- A run ID and clear workflow status for auditability

## Step 1: Create a safe fictional test case

The demonstration uses no real client or personal data. The call includes a company, pain, goal and timeline, while deliberately withholding budget. Two fictional historical proposals provide delivery and safety language, including a stale price trap in automated tests.

## Step 2: Extract facts with evidence

The extraction contract returns a value, exact quote and status for each field. Missing facts return `unknown`; conflicting facts return `conflict`. Price, timeline, legal terms and commitments are never inferred.

## Step 3: Retrieve reusable proposal sections

Past proposals are split into sections and ranked against transcript concepts. Historical content may guide wording and delivery structure, but it is not evidence for the current deal. Tests confirm an old price never appears in the new proposal.

## Step 4: Generate a structured draft

The generator produces an executive summary, needs, scope, deliverables, timeline, commercials, assumptions, exclusions and next step. If the current call does not support pricing, Commercials reads `To be confirmed`.

## Step 5: Verify risky claims

A separate verification stage compares the draft to current-call evidence. Unsupported money is a blocker. Missing context is visible rather than silently filled. This is the difference between a proposal assistant and a one-prompt wrapper.

## Step 6: Hold for human review

The review gate is part of the workflow state. Export is disabled until the reviewer approves. There is no external send feature in the build, so a generated draft cannot accidentally reach a prospect.

## Step 7: Test the failure paths

The first test suite covers:
- budget missing -> blocker plus `To be confirmed`
- supported facts -> exact quotes present
- every generated result -> `needs_review`
- explicit budget -> copied with evidence
- price from a historical proposal -> never leaked into a current draft

## Architecture

Next.js on the frontend and FastAPI/Pydantic on the backend. The current build uses a deterministic provider so the full workflow is testable without a paid key; a provider-neutral prompt contract documents the production LLM path. The hosted build should use a live provider only after an existing key is connected securely.

## What I deliberately did not build

Authentication, billing, a CRM connection, meeting-platform ingestion and email sending. None is required to prove the workflow, and each would weaken the 1-3 day focus. The next useful integrations would be transcript import and a proposal-template store, still behind the same review gate.

## Other ideas considered

1. Support escalation brief: turn a long customer thread into an evidence-linked internal handoff.
2. Renewal-risk review: combine call notes and usage exports into an account-manager briefing.
3. RFP requirement matrix: map each requirement to supporting company evidence and flag gaps.
4. Client onboarding pack: convert a signed scope into tasks, kickoff agenda and client checklist.
5. MENA localization reviewer: flag unsupported cultural or regulatory assumptions before campaign approval.
