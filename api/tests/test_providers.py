import json
import httpx
import pytest
from app.engine import generate
from app.models import ProposalRequest
from app.providers import DeterministicProvider, OpenAIProvider, get_provider

TRANSCRIPT = """Host: Thanks for joining. Our company is Northstar Studio. The problem is proposals take two days after a sales call. We want to send a reviewed draft within 30 minutes. We need this in the next 6 weeks. Speaker: We have not approved a budget yet."""
PAST = """Delivery approach\nWe begin with discovery and workflow mapping, then deliver a focused implementation and handover.\n\nCommercials\nPricing is agreed only after scope validation."""

PRICED_TRANSCRIPT = TRANSCRIPT.replace("We have not approved a budget yet", "The approved budget is $24,000 USD")


class StubProvider:
    name = "stub-llm"

    def __init__(self, text=None, error=None):
        self.text = text
        self.error = error
        self.prompts = []

    def draft(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return self.text


def test_default_provider_is_deterministic(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    assert isinstance(get_provider(), DeterministicProvider)


def test_real_provider_without_key_is_loud(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="LLM_API_KEY"):
        get_provider()


def test_openai_adapter_payload_and_parse(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "draft text"}}]})

    provider = OpenAIProvider(api_key="sk-test", model="gpt-4o-mini", transport=httpx.MockTransport(handler))
    assert provider.draft("hello") == "draft text"
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["auth"] == "Bearer sk-test"
    assert captured["body"]["messages"][0]["content"] == "hello"


def test_llm_draft_with_invented_amount_is_rejected():
    dirty = "# Proposal for Northstar Studio\n\n## Commercials\n$50,000 USD fixed fee."
    stub = StubProvider(text=dirty)
    result = generate(ProposalRequest(transcript=PRICED_TRANSCRIPT, past_proposals=[PAST]), provider=stub)
    assert "$50,000" not in result.proposal_markdown
    assert "$24,000 USD" in result.proposal_markdown
    assert any(f.code == "unverified_llm_amount" and f.severity == "blocker" for f in result.flags)
    assert result.provider == "stub-llm-rejected-deterministic"


def test_llm_draft_using_only_transcript_amount_is_accepted():
    clean = "# Proposal for Northstar Studio\n\n## Commercials\n$24,000 USD as stated on the call."
    stub = StubProvider(text=clean)
    result = generate(ProposalRequest(transcript=PRICED_TRANSCRIPT, past_proposals=[PAST]), provider=stub)
    assert result.proposal_markdown == clean
    assert result.provider == "stub-llm"
    assert not any(f.code == "unverified_llm_amount" for f in result.flags)


def test_llm_failure_falls_back_to_deterministic_draft():
    stub = StubProvider(error=httpx.ConnectError("down"))
    result = generate(ProposalRequest(transcript=TRANSCRIPT, past_proposals=[PAST]), provider=stub)
    assert "To be confirmed" in result.proposal_markdown
    assert any(f.code == "llm_unavailable" for f in result.flags)
    assert result.provider == "stub-llm-fallback-deterministic"


def test_prompt_carries_facts_and_quotes():
    stub = StubProvider(text="# x")
    generate(ProposalRequest(transcript=TRANSCRIPT, past_proposals=[PAST]), provider=stub)
    prompt = stub.prompts[0]
    assert "VERIFIED FACTS" in prompt
    assert "budget: UNKNOWN" in prompt
    assert "never invent" in prompt.lower()
    assert "style and scope reference only" in prompt.lower() or "not evidence" in prompt.lower()
