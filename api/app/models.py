from typing import Literal
from pydantic import BaseModel, Field

class Evidence(BaseModel):
    field: str
    value: str | None = None
    quote: str | None = None
    status: Literal["supported", "unknown", "conflict"] = "unknown"

class ProposalRequest(BaseModel):
    transcript: str = Field(min_length=80, max_length=50000)
    past_proposals: list[str] = Field(min_length=1, max_length=8)

class VerificationFlag(BaseModel):
    severity: Literal["info", "warning", "blocker"]
    code: str
    message: str
    section: str

class ProposalResponse(BaseModel):
    run_id: str
    status: Literal["needs_review"] = "needs_review"
    facts: list[Evidence]
    retrieved_examples: list[str]
    proposal_markdown: str
    flags: list[VerificationFlag]
    provider: str

class ExportRequest(BaseModel):
    proposal_markdown: str = Field(min_length=40, max_length=50000)
    approved: bool = False
    run_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{6,64}$")
