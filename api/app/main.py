from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import ProposalRequest, ProposalResponse
from .engine import generate

app = FastAPI(title="Call2Proposal API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok", "provider": "deterministic-demo-v1"}

@app.post("/v1/proposals", response_model=ProposalResponse)
def create_proposal(request: ProposalRequest):
    return generate(request)
