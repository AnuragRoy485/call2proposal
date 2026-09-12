import re
from hashlib import sha256
from .models import Evidence, ProposalRequest, ProposalResponse, VerificationFlag
from .providers import DeterministicProvider, DraftProvider, get_provider

FIELD_RULES = {
    "company": [r"(?:we(?:'re| are)|company is) ([A-Z][A-Za-z0-9 &-]{2,40})"],
    "pain": [r"(?:problem|challenge|bottleneck) (?:is|has been) ([^.]{12,180})"],
    "goal": [r"(?:need|want|goal is to|looking to) ([^.]{12,180})"],
    "timeline": [r"(?:by|within|in) ((?:the )?next \d+ (?:days|weeks|months)|Q[1-4]|[A-Z][a-z]+ \d{4})"],
    "budget": [r"(?:budget|approved budget) (?:is|of|around)?\s*([$€£₹][\d,.]+(?:\s*(?:USD|EUR|GBP|INR))?)"],
}

MONEY_PATTERN = re.compile(r"[$€£₹]\s?[\d,.]+|\b\d[\d,.]*\s?(?:USD|EUR|GBP|INR)\b")

def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.strip()) > 5]

def _extract(transcript: str) -> list[Evidence]:
    facts: list[Evidence] = []
    for field, patterns in FIELD_RULES.items():
        matches: list[tuple[str, str]] = []
        for sentence in _sentences(transcript):
            for pattern in patterns:
                match = re.search(pattern, sentence, re.I)
                if match:
                    pair = (match.group(1).strip(), sentence)
                    if pair[0].lower() not in {v.lower() for v, _ in matches}:
                        matches.append(pair)
        if len(matches) > 1:
            facts.append(Evidence(field=field, value=" | ".join(v for v, _ in matches), quote=" || ".join(q for _, q in matches), status="conflict"))
        elif matches:
            value, quote = matches[0]
            facts.append(Evidence(field=field, value=value, quote=quote, status="supported"))
        else:
            facts.append(Evidence(field=field, status="unknown"))
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

def _template_draft(facts: list[Evidence]) -> str:
    company = _value(facts, "company", "the client")
    pain = _value(facts, "pain", "Needs confirmation during proposal review")
    goal = _value(facts, "goal", "Needs confirmation during proposal review")
    timeline = _value(facts, "timeline", "To be confirmed")
    budget = _value(facts, "budget", "To be confirmed")
    return f"""# Proposal for {company}

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

def _draft_prompt(facts: list[Evidence], examples: list[str]) -> str:
    fact_lines = "\n".join(
        f"- {f.field}: {f.value or 'UNKNOWN'} (status: {f.status})"
        + (f"\n  source quote: \"{f.quote}\"" if f.quote else "")
        for f in facts
    )
    example_block = "\n\n---\n\n".join(examples) if examples else "(no historical sections retrieved)"
    return f"""You are drafting a sales proposal from verified discovery-call facts.

Rules you must follow:
- Use ONLY the facts below. Every fact carries its verbatim source quote.
- Any field marked UNKNOWN or conflict must appear in the proposal as "To be confirmed" - never invent a value.
- Never state a price, discount, date, or commitment that does not appear verbatim in the facts.
- Historical sections are style and scope reference only. They are not evidence for this deal.
- Output markdown with these sections: Executive summary, Desired outcome, Proposed scope, Timeline, Commercials, Assumptions and exclusions, Next step.

VERIFIED FACTS:
{fact_lines}

HISTORICAL SECTIONS FOR STYLE REFERENCE (not evidence):
{example_block}
"""

def _unverified_amounts(draft: str, transcript: str) -> list[str]:
    allowed = {m.group(0).replace(" ", "") for m in MONEY_PATTERN.finditer(transcript)}
    found = []
    for match in MONEY_PATTERN.finditer(draft):
        token = match.group(0).replace(" ", "")
        if token not in allowed:
            found.append(match.group(0))
    return found

def _flags_for(facts: list[Evidence]) -> list[VerificationFlag]:
    flags: list[VerificationFlag] = []
    for fact in facts:
        if fact.status == "unknown":
            severity = "blocker" if fact.field == "budget" else "warning"
            flags.append(VerificationFlag(severity=severity, code=f"missing_{fact.field}", message=f"{fact.field.title()} was not found in the transcript. Kept as an explicit unknown.", section="Commercials" if fact.field == "budget" else "Draft"))
        elif fact.status == "conflict":
            flags.append(VerificationFlag(severity="blocker", code=f"conflicting_{fact.field}", message=f"Conflicting {fact.field} values were found. A reviewer must choose the correct one.", section="Commercials" if fact.field == "budget" else "Draft"))
    return flags

def generate(request: ProposalRequest, provider: DraftProvider | None = None) -> ProposalResponse:
    provider = provider if provider is not None else get_provider()
    facts = _extract(request.transcript)
    examples = _retrieve(request.transcript, request.past_proposals)
    flags = _flags_for(facts)

    markdown = _template_draft(facts)
    provider_name = "deterministic-demo-v1"
    if not isinstance(provider, DeterministicProvider):
        provider_name = provider.name
        try:
            llm_draft = provider.draft(_draft_prompt(facts, examples))
        except Exception:
            flags.append(VerificationFlag(severity="warning", code="llm_unavailable", message="The configured model call failed, so the deterministic draft was used instead.", section="Draft"))
            provider_name = f"{provider.name}-fallback-deterministic"
        else:
            bad_amounts = _unverified_amounts(llm_draft, request.transcript)
            if bad_amounts:
                flags.append(VerificationFlag(severity="blocker", code="unverified_llm_amount", message=f"The model draft contained amounts with no transcript evidence ({', '.join(sorted(set(bad_amounts)))}). The deterministic draft was used instead.", section="Commercials"))
                provider_name = f"{provider.name}-rejected-deterministic"
            else:
                markdown = llm_draft
    return ProposalResponse(
        run_id=sha256((request.transcript + "||".join(request.past_proposals)).encode()).hexdigest()[:12],
        facts=facts,
        retrieved_examples=examples,
        proposal_markdown=markdown,
        flags=flags,
        provider=provider_name,
    )
