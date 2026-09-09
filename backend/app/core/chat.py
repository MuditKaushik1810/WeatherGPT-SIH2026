"""
Conversational core (Architecture doc §3.5, Sprint 2) — the generation half of
the pipeline, tying the pieces together for POST /chat:

    query -> intent.extract_intent      (location, query_class, ...)
          -> degradation_ladder.get_weather(location)   (grounded, tiered data)
          -> grounding.build_grounding_context           (factual context block)
          -> generate_answer via the LLM                 (rephrase ONLY the facts)

The two rules hold here end-to-end: the LLM is handed only the grounding block
(never raw freedom to invent weather), and if the LLM is unavailable we fall
back to a deterministic answer built straight from the grounded facts — so the
endpoint never bare-refuses, with or without an LLM key configured.
"""
from app.connectors import llm
from app.core import cache, degradation_ladder, forecast, grounding, intent

# Chat answers embed live weather, so cache them only briefly — long enough to
# spare repeated LLM calls for the same question, short enough to stay current.
_CHAT_TTL_SECONDS = 300

# Future-dated queries pull the forecast for these day offsets instead of current
# conditions (0 = today, 1 = tomorrow). Kept small — the free forecast tier is
# ~3 days, and forecast.get_daily_forecast skips any day beyond the horizon.
_FUTURE_OFFSETS = {"tomorrow": [1], "week": [1, 2]}

# Language code -> name for the "respond in X" instruction. Unknown codes fall
# back to English (the LLM still receives the user's original wording).
_LANGUAGES = {"en": "English", "hi": "Hindi", "bn": "Bengali", "ta": "Tamil", "mr": "Marathi", "pa": "Punjabi"}

_ROLE = (
    "You are WeatherGPT, a concise weather assistant for India. Answer the user's "
    "question by rephrasing ONLY the grounded FACTS provided below — never add a "
    "weather value, forecast, or any crop/agricultural, medical, or travel-safety "
    "recommendation that is not in the FACTS. If the user asks for something not in "
    "the FACTS, say that specific detail isn't available right now."
)


def _need_location_record() -> dict:
    """Honest 'which place?' record when the fast path found no location in the query."""
    return {
        "location": None, "temp": None, "condition": None, "precipitation_chance": None,
        "humidity": None, "feels_like": None, "wind_speed": None, "aqi": None,
        "warnings": [], "source": None, "data_tier": "unresolved_location", "fetched_at": None,
        "message": "Tell me a city or district and I'll pull its weather (e.g. 'weather in Jaipur').",
    }


def _system_prompt(ctx: dict, language: str) -> str:
    language_name = _LANGUAGES.get(language, "English")
    rules = "\n- ".join(ctx["constraints"])
    return f"{_ROLE}\n\nRules:\n- {rules}\n\nRespond in {language_name}."


def _deterministic_answer(ctx: dict) -> str:
    """
    Grounded answer with no LLM — the fail-soft path. Reads the facts back plainly
    (English), tagged honestly by tier, and always ends with any gap guidance.
    Never empty, never a bare refusal.
    """
    location = ctx["location"] or "that location"
    if ctx["facts"]:
        tier = ctx["data_tier"]
        if ctx.get("kind") == "forecast":
            prefix = f"Forecast for {location}"
        elif tier == "historical_baseline":
            prefix = f"Live data is unavailable for {location}, so here are the typical values for this date"
        elif tier == "source_unavailable":
            prefix = f"Live forecast is temporarily unavailable for {location}; here's what I have"
        elif tier == "regional_fallback":
            prefix = f"Nearest available data for {location}"
        else:
            prefix = f"Current conditions for {location}"
        answer = f"{prefix}: " + "; ".join(ctx["facts"]) + "."
    else:
        answer = ctx["gap_guidance"] or (
            "I don't have weather data for that right now — try a nearby major city."
        )
    if ctx["facts"] and ctx["gap_guidance"]:
        answer += " " + ctx["gap_guidance"]
    return answer


def generate_answer(ctx: dict, query: str, language: str = "en") -> str:
    """
    Produce the user-facing answer from a grounding context. Uses the LLM to
    rephrase the grounded facts; if no LLM is available, falls back to a
    deterministic grounded summary. Always returns a non-empty answer.
    """
    system = _system_prompt(ctx, language)
    user = f"{ctx['context_block']}\n\nUser question: {query}"
    text = llm.complete(system, user)
    if text and text.strip():
        return text.strip()
    return _deterministic_answer(ctx)


def answer_query(query: str, language: str = "en", user_id: str | None = None) -> dict:
    """
    Full POST /chat pipeline. Returns the documented contract shape (§3.10):
    {answer, data_tier, source, query_class, audio_url}. `audio_url` is None —
    voice output is a browser-side (Web Speech) concern, added later.
    """
    cache_key = f"chat:{language}:{query.strip().lower()}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    parsed = intent.extract_intent(query)
    location = parsed["location"]
    query_class = parsed["query_class"]
    time_range = parsed["time_range"]

    if location and time_range in _FUTURE_OFFSETS:
        # Future-dated query — ground the forecast for the requested day(s).
        fc = forecast.get_daily_forecast(location, _FUTURE_OFFSETS[time_range])
        ctx = grounding.build_forecast_context(fc, query_class)
    else:
        # Current conditions (or an honest "which place?" when no location parsed).
        record = degradation_ladder.get_weather(location) if location else _need_location_record()
        ctx = grounding.build_grounding_context(record, query_class=query_class)

    answer = generate_answer(ctx, query, language)

    result = {
        "answer": answer,
        "data_tier": ctx["data_tier"],
        "source": ctx["source"],
        "query_class": query_class,
        "audio_url": None,
    }
    # Cache only settled tiers — a "live is down" state (source_unavailable) or an
    # unresolved location is re-tried each request, never served stale.
    if ctx["data_tier"] in ("exact", "regional_fallback", "historical_baseline"):
        cache.set(cache_key, result, ttl=_CHAT_TTL_SECONDS)
    return result
