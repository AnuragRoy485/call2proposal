import re
from hashlib import sha256
from .models import Evidence, ProposalRequest, ProposalResponse, VerificationFlag

FIELD_RULES = {
    "company": [r"(?:we(?:'re| are)|company is) ([A-Z][A-Za-z0-9 &-]{2,40})"],
    "pain": [r"(?:problem|challenge|bottleneck) (?:is|has been) ([^.]{12,180})"],
    "goal": [r"(?:need|want|goal is to|looking to) ([^.]{12,180})"],
    "timeline": [r"(?:by|within|in) ((?:the )?next \d+ (?:days|weeks|months)|Q[1-4]|[A-Z][a-z]+ \d{4})"],
    "budget": [r"(?:budget|approved budget) (?:is|of|around)?\s*([$€£₹][\d,.]+(?:\s*(?:USD|EUR|GBP|INR))?)"],
}

def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.strip()) > 5]

def _extract(transcript: str) -> list[Evidence]:
    facts: list[Evidence] = []
    for field, patterns in FIELD_RULES.items():
        found = None
        for sentence in _sentences(transcript):
            for pattern in patterns:
                match = re.search(pattern, sentence, re.I)
                if match:
                    found = Evidence(field=field, value=match.group(1).strip(), quote=sentence, status="supported")
                    break
            if found:
                break
        facts.append(found or Evidence(field=field, status="unknown"))
    return facts

def _keywords(text: str) -> set[str]:
    stop = {"the","and","for","with","that","this","from","your","our","are","you","will","into","have","not"}
    return {w for w in re.findall(r"[a-z]{4,}", text.lower()) if w not in stop}

def _retrieve(transcript: str, proposals: list[str]) -> list[str]:
    query = _keywords(transcript)
    chunks = []
    for document in proposals:
        for chunk in re.split(r"\n\s*\n", document):
            if len(chunk.strip()) >= 40:
                score = len(query & _keywords(chunk))
                chunks.append((score, chunk.strip()))
    chunks.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
    return [chunk for score, chunk in chunks[:3] if score > 0] or [chunks[0][1]] if chunks else []

def _value(facts: list[Evidence], field: str, fallback: str) -> str:
    match = next((f for f in facts if f.field == field and f.status == "supported"), None)
    return match.value if match and match.value else fallback

def generate(request: ProposalRequest) -> ProposalResponse:
    facts = _extract(request.transcript)
    examples = _retrieve(request.transcript, request.past_proposals)
    company = _value(facts, "company", "the client")
    pain = _value(facts, "pain", "Needs confirmation during proposal review")
    goal = _value(facts, "goal", "Needs confirmation during proposal review")
    timeline = _value(facts, "timeline", "To be confirmed")
    budget = _value(facts, "budget", "To be confirmed")
    markdown = f"""# Proposal for {company}

## Executive summary
Based on the discovery call, the priority is to address: {pain}.

## Desired outcome
{goal}.

## Proposed scope
1. Discovery and workflow mapping
2. A focused implementation against the agreed workflow
3. Validation, handover and operating notes

## Timeline
{timeline}

## Commercials
{budget}

## Assumptions and exclusions
- Final access, stakeholders and acceptance criteria require confirmation.
- No integrations or promises beyond the reviewed scope are included.
- Pricing is not final unless it was stated explicitly in the call and approved by a human reviewer.

## Next step
Review the evidence panel, correct any missing details, and approve this draft before export.
"""
    flags: list[VerificationFlag] = []
    for fact in facts:
        if fact.status == "unknown":
            severity = "blocker" if fact.field == "budget" else "warning"
            flags.append(VerificationFlag(severity=severity, code=f"missing_{fact.field}", message=f"{fact.field.title()} was not found in the transcript. Kept as an explicit unknown.", section="Commercials" if fact.field == "budget" else "Draft"))
    return ProposalResponse(
        run_id=sha256((request.transcript + "||".join(request.past_proposals)).encode()).hexdigest()[:12],
        facts=facts,
        retrieved_examples=examples,
        proposal_markdown=markdown,
        flags=flags,
        provider="deterministic-demo-v1",
    )
