from app.engine import generate
from app.models import ProposalRequest

TRANSCRIPT = """Host: Thanks for joining. Our company is Northstar Studio. The problem is proposals take two days after a sales call. We want to send a reviewed draft within 30 minutes. We need this in the next 6 weeks. Speaker: We have not approved a budget yet."""
PAST = """Delivery approach\nWe begin with discovery and workflow mapping, then deliver a focused implementation and handover.\n\nCommercials\nPricing is agreed only after scope validation."""

def test_missing_budget_is_blocked_and_not_invented():
    result = generate(ProposalRequest(transcript=TRANSCRIPT, past_proposals=[PAST]))
    assert "To be confirmed" in result.proposal_markdown
    assert any(f.code == "missing_budget" and f.severity == "blocker" for f in result.flags)

def test_every_supported_fact_has_quote():
    result = generate(ProposalRequest(transcript=TRANSCRIPT, past_proposals=[PAST]))
    assert all(f.quote for f in result.facts if f.status == "supported")

def test_status_requires_review():
    result = generate(ProposalRequest(transcript=TRANSCRIPT, past_proposals=[PAST]))
    assert result.status == "needs_review"
