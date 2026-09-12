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


def test_explicit_budget_is_preserved_with_evidence():
    transcript = TRANSCRIPT.replace("We have not approved a budget yet", "The approved budget is $24,000 USD")
    result = generate(ProposalRequest(transcript=transcript, past_proposals=[PAST]))
    budget = next(f for f in result.facts if f.field == "budget")
    assert budget.value == "$24,000 USD"
    assert budget.quote and "$24,000 USD" in budget.quote
    assert not any(f.code == "missing_budget" for f in result.flags)

def test_past_proposal_price_does_not_leak_into_current_draft():
    priced_history = PAST + "\nA previous client paid $99,999 USD."
    result = generate(ProposalRequest(transcript=TRANSCRIPT, past_proposals=[priced_history]))
    assert "$99,999" not in result.proposal_markdown

def test_conflicting_timeline_is_blocked():
    transcript = TRANSCRIPT + " Later: We need it in the next 9 weeks."
    result = generate(ProposalRequest(transcript=transcript, past_proposals=[PAST]))
    timeline = next(f for f in result.facts if f.field == "timeline")
    assert timeline.status == "conflict"
    assert any(f.code == "conflicting_timeline" and f.severity == "blocker" for f in result.flags)
