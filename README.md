# Call2Proposal

Turn a sales-call transcript into an evidence-backed proposal draft, grounded in a company's past proposals and held behind a human review gate.

Built for Crework's AI Engineer Intern buildathon, Option B.

## Why this exists

Sales-led SMEs lose momentum between a strong call and a proposal. Call2Proposal reduces the mechanical work without letting a model invent prices, dates, or promises.

## Workflow

1. Paste a transcript and one or more past proposals.
2. Extract deal facts with exact transcript evidence.
3. Retrieve relevant reusable language from past proposals.
4. Draft a proposal.
5. Verify every risky claim and surface unknowns.
6. Review and approve before export. Nothing is sent automatically.

## Monorepo

- `web/` - Next.js 15 frontend
- `api/` - FastAPI backend
- `samples/` - fully fictional demonstration data
- `docs/` - architecture, prompts, evaluation and case-study draft

## Local setup

```bash
# API
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Web
cd web
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

The API defaults to `DEMO_MODE=true`, a deterministic provider that makes the project runnable without a paid API. A real provider can be added behind `ProposalProvider` without changing the workflow contract. The submission must disclose which provider actually powered the deployed demo.

## Safety contract

- Pricing is copied only when explicitly stated in the transcript. Otherwise the draft says `To be confirmed`.
- Every extracted fact carries a source quote.
- The verifier flags unsupported money, dates and commitments.
- Export is disabled until a reviewer approves the draft.
- There is no email-send path.

## Tests

```bash
cd api && pytest
```
