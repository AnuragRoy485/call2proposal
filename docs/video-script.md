# Walkthrough script (2-4 minutes)

## 0:00 - Problem and choice
"I chose the proposal-builder problem because the cost is not writing time alone. A slow proposal loses momentum, while a fast hallucinated proposal creates commercial risk. I optimized for a reviewable draft, not automatic sending."

## 0:25 - Fictional input
Show the Northstar Studio transcript and two past proposals. State that every name and detail is fictional. Point out that the call explicitly withholds a budget.

## 0:45 - Workflow
Show: extraction with exact quotes, section retrieval from historical proposals, structured drafting, verifier, human approval, export.

## 1:20 - Trust design
Point to the missing-budget blocker and `To be confirmed`. Explain that old proposals can supply language but cannot authorize current prices or commitments. Show export disabled before approval.

## 1:55 - Engineering decisions
Show Next.js/FastAPI structure, typed schemas, provider adapter boundary, five tests and deployment. Explain why auth, CRM and sending were cut from a 1-3 day build.

## 2:30 - Test evidence
Run the golden case and mention the historical-price leak test, explicit-budget test and evidence-quote invariant.

## 2:55 - Next step
"The next iteration would add transcript-provider imports and a persistent proposal library while keeping the same evidence and approval contracts."
