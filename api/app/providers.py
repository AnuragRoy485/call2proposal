"""Provider seam for the drafting step.

Extraction and verification stay deterministic regardless of provider:
facts must carry verbatim transcript quotes, and any currency amount in an
LLM draft that is not present in the transcript evidence voids the draft.
The LLM only ever polishes prose around already-verified facts.
"""
import os
from typing import Protocol

import httpx

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5",
    "gemini": "gemini-2.0-flash",
}


class DraftProvider(Protocol):
    name: str

    def draft(self, prompt: str) -> str:
        ...


class DeterministicProvider:
    name = "deterministic-demo-v1"

    def draft(self, prompt: str) -> str:
        raise RuntimeError("Deterministic provider does not draft prose")


class _HttpJsonProvider:
    endpoint = ""
    name = "http"

    def __init__(self, api_key: str, model: str, transport: httpx.BaseTransport | None = None):
        self.api_key = api_key
        self.model = model
        self._transport = transport

    def _payload(self, prompt: str) -> tuple[dict, dict, str]:
        raise NotImplementedError

    def _parse(self, data: dict) -> str:
        raise NotImplementedError

    def draft(self, prompt: str) -> str:
        headers, payload, url = self._payload(prompt)
        with httpx.Client(timeout=30.0, transport=self._transport) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
        return self._parse(response.json())


class OpenAIProvider(_HttpJsonProvider):
    endpoint = "https://api.openai.com/v1/chat/completions"
    name = "openai"

    def _payload(self, prompt: str):
        return (
            {"Authorization": f"Bearer {self.api_key}"},
            {"model": self.model, "max_tokens": 1200, "messages": [{"role": "user", "content": prompt}]},
            self.endpoint,
        )

    def _parse(self, data: dict) -> str:
        return data["choices"][0]["message"]["content"]


class AnthropicProvider(_HttpJsonProvider):
    endpoint = "https://api.anthropic.com/v1/messages"
    name = "anthropic"

    def _payload(self, prompt: str):
        return (
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            {"model": self.model, "max_tokens": 1200, "messages": [{"role": "user", "content": prompt}]},
            self.endpoint,
        )

    def _parse(self, data: dict) -> str:
        return "".join(block.get("text", "") for block in data["content"])


class GeminiProvider(_HttpJsonProvider):
    name = "gemini"

    def _payload(self, prompt: str):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        return (
            {"x-goog-api-key": self.api_key},
            {"contents": [{"parts": [{"text": prompt}]}]},
            url,
        )

    def _parse(self, data: dict) -> str:
        return data["candidates"][0]["content"]["parts"][0]["text"]


_ADAPTERS = {"openai": OpenAIProvider, "anthropic": AnthropicProvider, "gemini": GeminiProvider}


def get_provider() -> DraftProvider:
    """Resolve the configured provider. Deterministic unless LLM_PROVIDER names
    a real adapter, which then requires LLM_API_KEY. LLM_MODEL overrides the
    default model per provider."""
    kind = os.environ.get("LLM_PROVIDER", "deterministic").strip().lower()
    if kind in ("", "deterministic"):
        return DeterministicProvider()
    if kind not in _ADAPTERS:
        raise RuntimeError(f"Unknown LLM_PROVIDER '{kind}'. Expected one of: {sorted(_ADAPTERS)} or 'deterministic'.")
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(f"LLM_PROVIDER={kind} requires LLM_API_KEY in the environment.")
    model = os.environ.get("LLM_MODEL", "").strip() or DEFAULT_MODELS[kind]
    return _ADAPTERS[kind](api_key=api_key, model=model)
