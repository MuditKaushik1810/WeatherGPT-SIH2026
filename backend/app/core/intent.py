"""
Intent + entity extraction — the rule/keyword FAST PATH (Architecture doc §3.5,
Sprint 2).

Pulls the structured fields the router needs — `location`, `query_class`,
`time_range`, `hazard` — from a free-text query with ZERO LLM calls and ZERO
network. It covers the common cases instantly and for free; the LLM
structured-output step (a later PR) is meant to run only for queries this fast
path can't confidently resolve (e.g. no location found, or an ambiguous class).

`query_class` mirrors the degradation-router's own branches (doc §3.1 graph):
    realtime | historical | safety | farmer | trip
so the /chat handler can route each class to the right subsystem (live forecast,
historical DB, hazard guide, farmer advisory, trip planner). A near-future
forecast question ("will it rain tomorrow") is still `realtime` — it uses the
live forecast source — with the future-ness captured in `time_range`.
"""
import re

from app.core import geocoding

# --- Hazard vocabulary (the 5 NDMA Hazard Safety Guide types, doc §3.9) --------
# phrase -> canonical hazard. Longer phrases first so "heat wave" isn't missed.
_HAZARD_PATTERNS = [
    ("cyclone", "cyclone"), ("storm surge", "cyclone"),
    ("flooding", "flood"), ("flood", "flood"),
    ("heatwave", "heatwave"), ("heat wave", "heatwave"),
    ("coldwave", "coldwave"), ("cold wave", "coldwave"),
    ("thunderstorm", "thunderstorm"), ("lightning", "thunderstorm"),
]
# Hazards severe enough that merely mentioning them routes to the safety subsystem.
_SEVERE_HAZARDS = {"cyclone", "flood", "heatwave", "coldwave"}
# Explicit emergency/advisory language that routes to safety regardless of hazard.
_SAFETY_WORDS = (
    "warning", "alert", "emergency", "evacuat", "disaster", "landslide",
    "is it safe", "safe to", "red alert", "orange alert",
)

_FARMER_WORDS = (
    "crop", "sow", "sowing", "harvest", "irrigat", "pesticide", "pest",
    "fungal", "farming", "farmer", "my field", "my farm",
    "wheat", "rice", "paddy", "cotton", "soybean", "sugarcane", "maize", "mustard",
)
_TRIP_WORDS = ("trip", "travel", "journey", "road trip", "driving", "drive from", "route")

_HISTORICAL_WORDS = (
    "last year", "last month", "historical", "history", "on average", "average",
    "trend", "compared to", "compared with", "normally", "usually", "in the past",
    "past decade", "10-year", "10 year", "climate", "this time last",
)

# --- Location gazetteer regex (built once from the static city table) ----------
# One big word-boundary alternation, longest names first so "new delhi" wins over
# "delhi". ~510 names; compiled once at import — no per-call rebuild, no network.
_CITY_RE = re.compile(
    r"\b(" + "|".join(re.escape(name) for name in geocoding.known_city_names()) + r")\b"
)
_YEAR_RE = re.compile(r"\b(19|20)\d\d\b")


def _detect_hazard(q: str) -> str | None:
    for phrase, canonical in _HAZARD_PATTERNS:
        if phrase in q:
            return canonical
    return None


def _is_safety(q: str, hazard: str | None) -> bool:
    if hazard in _SEVERE_HAZARDS:
        return True
    return any(word in q for word in _SAFETY_WORDS)


def _is_historical(q: str) -> bool:
    return any(word in q for word in _HISTORICAL_WORDS) or bool(_YEAR_RE.search(q))


def _time_range(q: str) -> str | None:
    # Most-specific first; historical markers win so "last year" / "in 2019" read as past.
    if any(w in q for w in ("last year", "last month", "in the past", "past", "historical")) \
            or _YEAR_RE.search(q):
        return "past"
    if "tomorrow" in q:
        return "tomorrow"
    if "today" in q or "tonight" in q:
        return "today"
    if any(w in q for w in ("right now", "currently", "current", "at the moment", " now")):
        return "now"
    if any(w in q for w in ("this week", "next week", "weekend", "next few days", "coming days",
                            "monday", "tuesday", "wednesday", "thursday", "friday",
                            "saturday", "sunday")):
        return "week"
    return None


def _extract_location(q: str) -> str | None:
    m = _CITY_RE.search(q)
    return m.group(1).title() if m else None


def extract_intent(query: str) -> dict:
    """
    Extract the structured intent of a free-text weather query via the fast path.

    Returns:
        {
          "raw_query":    str,              # the original query
          "location":     str | None,       # first gazetteer city found, Title-Cased
          "query_class":  str,              # realtime | historical | safety | farmer | trip
          "time_range":   str | None,       # now | today | tomorrow | week | past
          "hazard":       str | None,       # flood | cyclone | heatwave | coldwave | thunderstorm
          "resolved_by":  "fast_path",      # provenance (vs a future "llm" fallback)
        }

    Never raises. `location is None` is the signal that an LLM fallback (or a
    clarifying follow-up) is worthwhile — the fast path itself always returns a
    best-effort class rather than refusing.
    """
    q = f" {query.lower().strip()} "  # pad so leading/trailing word checks (" now ") match
    hazard = _detect_hazard(q)

    if _is_safety(q, hazard):
        query_class = "safety"
    elif any(word in q for word in _FARMER_WORDS):
        query_class = "farmer"
    elif any(word in q for word in _TRIP_WORDS):
        query_class = "trip"
    elif _is_historical(q):
        query_class = "historical"
    else:
        query_class = "realtime"

    return {
        "raw_query": query,
        "location": _extract_location(q),
        "query_class": query_class,
        "time_range": _time_range(q),
        "hazard": hazard,
        "resolved_by": "fast_path",
    }
