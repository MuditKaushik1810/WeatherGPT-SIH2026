"""
LLM connector — the generation step's access to a hosted model, via REST so we
add no SDK dependency (just `requests`).

Primary: Google Gemini Flash (free tier). Fallback: Groq (free tier,
OpenAI-compatible) if Gemini is missing/rate-limited/errors. Both are keyed via
env (`GEMINI_API_KEY` / `GROQ_API_KEY`), so a shared deployment IP is never the
constraint the way a keyless API would be.

CRITICAL: this connector fails SOFT like every other one (CLAUDE.md). On a
missing key, network error, non-2xx, or unexpected payload it returns None — it
NEVER raises. `complete()` returning None is the signal for the caller
(core/chat.py) to fall back to a deterministic, grounded answer rather than
bare-refuse. The LLM is only ever a rephraser of already-grounded facts; if it's
down, the facts still get delivered.
"""
import logging
import os

import requests

logger = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Free-tier defaults; overridable via env. Default to the always-latest Flash
# (Flash line = free-tier friendly; "latest" tracks the newest release).
_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
_GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


def _try_gemini(system: str, user: str, temperature: float, max_tokens: int) -> str | None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        resp = requests.post(
            GEMINI_URL.format(model=_GEMINI_MODEL),
            # Key as a header, not a query param, so it never lands in logged URLs.
            headers={"x-goog-api-key": api_key},
            json={
                "system_instruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    # This is a grounded rephrase, not a reasoning task — disable
                    # "thinking" so Flash models spend their budget on the ANSWER,
                    # not internal thought (which otherwise returns empty text).
                    "thinkingConfig": {"thinkingBudget": 0},
                },
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            # e.g. the whole prompt was safety-blocked — surface it, don't fail silent.
            logger.warning("Gemini returned no candidates: %s", str(data)[:300])
            return None
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            logger.warning("Gemini returned empty text (finishReason=%s)",
                           candidates[0].get("finishReason"))
            return None
        return text
    except Exception as exc:
        logger.warning("Gemini generation failed: %r", exc)
        return None


def _try_groq(system: str, user: str, temperature: float, max_tokens: int) -> str | None:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        resp = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": _GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=20,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        return text or None
    except Exception as exc:
        logger.warning("Groq generation failed: %r", exc)
        return None


def complete(system: str, user: str, *, temperature: float = 0.3, max_tokens: int = 1024) -> str | None:
    """
    Generate a completion from the primary LLM, falling back to the secondary.

    Returns the model's text, or None if no provider is configured/reachable —
    never raises. A None result means "no LLM available"; the caller must then
    deliver the grounded facts deterministically, never a bare refusal.
    """
    return (
        _try_gemini(system, user, temperature, max_tokens)
        or _try_groq(system, user, temperature, max_tokens)
    )
