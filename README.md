# Call2Proposal

Turn a sales-call transcript into an evidence-backed proposal draft, grounded in a company's past proposals and held behind a human review gate.

Built for Crework's AI Engineer Intern buildathon, Option B.

## Live demo

- App: https://call2proposal.vercel.app
- API: https://call2proposal-api.vercel.app (`/health` reports the active provider)
- The hosted demo drafts with Gemini 2.5 Flash behind the deterministic evidence guard; the deterministic provider remains the default for local runs and the automatic fallback.

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
- `backend/` - FastAPI backend (deploys as Vercel Python serverless functions)
- `samples/` - fully fictional demonstration data
- `docs/` - architecture, prompts, evaluation and case-study draft

## Local setup

```bash
# API
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Web
cd web
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

The API defaults to a deterministic provider (`deterministic-demo-v1`) so the project runs without any API key. A live model is configured entirely through environment variables, with no code change:

| Variable | Purpose |
| --- | --- |
| `LLM_PROVIDER` | `openai`, `anthropic` or `gemini` (unset = deterministic demo) |
| `LLM_API_KEY` | API key for the chosen provider |
| `LLM_MODEL` | Optional model override (defaults: `gpt-4o-mini`, `claude-haiku-4-5`, `gemini-2.5-flash`) |

The live provider only ever polishes prose around already-extracted facts. Extraction and verification stay deterministic: every fact must carry a verbatim transcript quote, and any currency amount in a model draft that does not appear in the transcript voids the draft (the deterministic version is used and a blocker is raised). `/health` reports the active provider, so the deployed demo discloses exactly what powered it.

## Deployment (Vercel)

Two Vercel projects from this one repo:

1. **Frontend** - root directory `web/`, framework Next.js. Set `NEXT_PUBLIC_API_URL` to the backend project's URL.
2. **Backend** - root directory `backend/`. `backend/api/index.py` exposes the FastAPI app as a Python serverless function and `backend/vercel.json` routes all paths to it. Set `LLM_PROVIDER` / `LLM_API_KEY` (and optionally `LLM_MODEL`) in the project's environment variables; leave them unset for the deterministic demo provider.

CORS on the API is open (no credentials are used), so the two projects can live on their default `*.vercel.app` URLs.

## Safety contract

- Pricing is copied only when explicitly stated in the transcript. Otherwise the draft says `To be confirmed`.
- Every extracted fact carries a source quote.
- The verifier flags unsupported money, dates and commitments.
- Export is disabled until a reviewer approves the draft.
- There is no email-send path.

## Tests

```bash
cd backend && pytest
```
