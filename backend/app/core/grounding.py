"""
Grounding assembler — Architecture doc §3.5 (the single most important design
decision) and Sprint 2.

The anti-hallucination step between retrieval and generation. It turns a
normalized weather record (whatever tier the degradation ladder produced) into
a structured, factual context block that the answer-generation LLM is allowed
to rephrase — and nothing more. The LLM never invents a weather value; it only
restates the facts assembled here. And it must never bare-refuse: even a sparse
or unresolved record yields an honest block plus a concrete next step, never an
empty "insufficient data" reply.

This is where CLAUDE.md's two rules live: (1) never let the LLM answer without
grounding, and (2) never let the LLM bare-refuse. Pure Python, deterministic,
no LLM/network — fully unit-testable. The LLM client (a later PR) embeds
`context_block` + `constraints` into its prompt; it does not re-derive them.
"""

# Human-facing confidence note per data tier — tells the LLM how to frame certainty.
_TIER_NOTES = {
    "exact": "Live current-conditions data for the requested location.",
    "regional_fallback": (
        "Nearest available grid/regional data — not a station reading for the exact spot."
    ),
    "historical_baseline": (
        "Live forecast is unavailable, so these are TYPICAL values for this date from a "
        "10-year historical average — not a current reading."
    ),
    "source_unavailable": (
        "Live forecast is temporarily unavailable; only the data points listed below "
        "could be retrieved."
    ),
    "unresolved_location": (
        "The location could not be resolved, so no weather data was retrieved."
    ),
}

# The invariants the answer-generation prompt must enforce. Kept here — with the
# assembler — so the rule lives in one place, not scattered across prompt strings.
GROUNDING_CONSTRAINTS = [
    "Only state weather facts that appear in FACTS below. Never invent, estimate, or "
    "infer any value that is not listed.",
    "If the user asks about a metric not in FACTS, say that specific data isn't "
    "available right now — do not guess it.",
    "Respect the data tier: if it is not 'exact', make the reduced certainty explicit "
    "(e.g. say values are typical-for-this-date for a historical baseline).",
    "Never reply with a bare 'I don't have enough data'. If facts are sparse or "
    "missing, give whatever IS available plus a concrete next step (e.g. try a nearby "
    "major city, or check back shortly).",
    "Answer the user's question directly and in their language; keep it concise.",
]


def _round(value):
    """Round floats to 1 decimal for display; leave ints/None untouched."""
    return round(value, 1) if isinstance(value, float) else value


def _facts_from_record(record: dict) -> list[str]:
    """
    Build the grounded fact strings — one per metric that is actually present.

    A metric that is None (its source failed soft) is simply omitted, never
    rendered as a guess or a zero. Temperature is labelled as "typical for this
    date" when the record is a historical baseline, so the LLM can't present it
    as a live reading.
    """
    facts: list[str] = []
    tier = record.get("data_tier")

    temp = record.get("temp")
    if temp is not None:
        label = "Typical temperature for this date" if tier == "historical_baseline" else "Temperature"
        facts.append(f"{label}: {_round(temp)}°C")
    if record.get("condition") is not None:
        facts.append(f"Condition: {record['condition']}")
    if record.get("feels_like") is not None:
        facts.append(f"Feels like: {_round(record['feels_like'])}°C")
    if record.get("humidity") is not None:
        facts.append(f"Humidity: {_round(record['humidity'])}%")
    if record.get("wind_speed") is not None:
        facts.append(f"Wind speed: {_round(record['wind_speed'])} km/h")
    precip = record.get("precipitation_chance")
    if precip is not None:
        facts.append(f"Chance of precipitation: {round(precip * 100)}%")
    if record.get("aqi") is not None:
        facts.append(f"Air quality (US AQI): {record['aqi']}")
    warnings = record.get("warnings") or []
    if warnings:
        facts.append("Active official warnings: " + "; ".join(warnings))
    return facts


_FORECAST_TIER_NOTES = {
    "exact": "Forecast for the requested day(s).",
    "source_unavailable": "The live forecast is temporarily unavailable.",
    "unresolved_location": "The location could not be resolved, so no forecast was retrieved.",
}


def _forecast_day_fact(day: dict) -> str:
    """One grounded line per forecast day — only the parts that are present."""
    parts = []
    if day.get("condition"):
        parts.append(str(day["condition"]))
    peak, low = day.get("peak_temp"), day.get("low_temp")
    if peak is not None and low is not None:
        parts.append(f"high {_round(peak)}°C, low {_round(low)}°C")
    elif peak is not None:
        parts.append(f"around {_round(peak)}°C")
    if day.get("max_precip_chance") is not None:
        parts.append(f"up to {round(day['max_precip_chance'] * 100)}% chance of rain")
    if day.get("max_wind") is not None:
        parts.append(f"wind up to {_round(day['max_wind'])} km/h")
    head = f"{day.get('label', 'That day')} ({day.get('date')})"
    return f"{head}: " + ", ".join(parts) if parts else f"{head}: no details available"


def build_forecast_context(forecast_record: dict, query_class: str = "realtime") -> dict:
    """
    Grounding context for a FUTURE-dated query — same output shape as
    build_grounding_context, but the facts are per-day forecast summaries (from
    forecast.get_daily_forecast) rather than current conditions. Same invariants:
    only the retrieved days are grounded, and an empty forecast still yields an
    honest block + guidance rather than a bare refusal.
    """
    tier = forecast_record.get("data_tier", "source_unavailable")
    days = forecast_record.get("days") or []
    facts = [_forecast_day_fact(d) for d in days]
    tier_note = _FORECAST_TIER_NOTES.get(tier, _FORECAST_TIER_NOTES["source_unavailable"])
    gap_guidance = forecast_record.get("message") if (not facts or tier != "exact") else None

    location = forecast_record.get("location")
    lines = [f"LOCATION: {location}" if location else "LOCATION: (unresolved)"]
    lines.append(f"DATA TIER: {tier} — {tier_note}")
    if forecast_record.get("source"):
        lines.append(f"SOURCE: {forecast_record['source']}")
    lines.append("")
    if facts:
        lines.append("FORECAST:")
        lines.extend(f"- {f}" for f in facts)
    else:
        lines.append("FORECAST: (none could be retrieved)")
    if gap_guidance:
        lines.append("")
        lines.append(f"GUIDANCE: {gap_guidance}")

    return {
        "location": location,
        "query_class": query_class,
        "kind": "forecast",
        "data_tier": tier,
        "source": forecast_record.get("source"),
        "fetched_at": forecast_record.get("fetched_at"),
        "facts": facts,
        "tier_note": tier_note,
        "constraints": list(GROUNDING_CONSTRAINTS),
        "answerable": bool(facts),
        "gap_guidance": gap_guidance,
        "context_block": "\n".join(lines),
    }


def build_grounding_context(record: dict, query_class: str = "realtime") -> dict:
    """
    Assemble the grounding context for the answer-generation step.

    `record` is a normalized weather record from the degradation ladder (any
    tier: exact / regional_fallback / historical_baseline / source_unavailable /
    unresolved_location). `query_class` is the resolved intent class (e.g.
    "realtime", "historical", "safety"), carried through for the prompt.

    Returns a dict with:
        location, query_class, data_tier, source, fetched_at,
        facts          -- only the metrics actually present (never guessed),
        tier_note      -- confidence framing for this tier,
        constraints    -- the anti-hallucination / anti-refusal rules,
        answerable     -- True iff at least one grounded fact exists,
        gap_guidance   -- honest next step when data is sparse/absent (else None),
        context_block  -- ready-to-inject text for the LLM prompt.

    Never raises and never returns an empty block: a record with no metrics
    still carries a tier note + gap guidance so the LLM can answer honestly
    instead of bare-refusing.
    """
    tier = record.get("data_tier", "source_unavailable")
    facts = _facts_from_record(record)
    tier_note = _TIER_NOTES.get(tier, _TIER_NOTES["source_unavailable"])

    # Honest next-step guidance when we couldn't ground a full answer. The ladder
    # usually attaches a `message`; prefer it, else derive a sensible default.
    gap_guidance = None
    if tier == "unresolved_location":
        gap_guidance = record.get("message") or (
            "That location couldn't be found — try a nearby major city or district name."
        )
    elif not facts:
        gap_guidance = record.get("message") or (
            "Live data is temporarily unavailable for this location — please try again shortly."
        )
    elif tier in ("source_unavailable", "historical_baseline"):
        # Facts exist but the live forecast is degraded — surface the ladder's note.
        gap_guidance = record.get("message")

    location = record.get("location")
    lines = [f"LOCATION: {location}" if location else "LOCATION: (unresolved)"]
    lines.append(f"DATA TIER: {tier} — {tier_note}")
    if record.get("source"):
        lines.append(f"SOURCE: {record['source']}")
    if record.get("fetched_at"):
        lines.append(f"FETCHED AT: {record['fetched_at']}")
    lines.append("")
    if facts:
        lines.append("FACTS:")
        lines.extend(f"- {f}" for f in facts)
    else:
        lines.append("FACTS: (none could be retrieved)")
    if gap_guidance:
        lines.append("")
        lines.append(f"GUIDANCE: {gap_guidance}")
    context_block = "\n".join(lines)

    return {
        "location": location,
        "query_class": query_class,
        "kind": "current",
        "data_tier": tier,
        "source": record.get("source"),
        "fetched_at": record.get("fetched_at"),
        "facts": facts,
        "tier_note": tier_note,
        "constraints": list(GROUNDING_CONSTRAINTS),
        "answerable": bool(facts),
        "gap_guidance": gap_guidance,
        "context_block": context_block,
    }
