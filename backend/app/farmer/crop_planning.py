"""
Crop Planning — "what should I grow?" (Architecture §3.10 GET /farmer/crop-planning).

The crop-SELECTION workflow (distinct from Crop Watch's monitoring). It ranks the
current season's crops by how well the location's temperature fits each crop's
curated optimal band, and returns ~4 with a short reason and an approximate
harvest window.

Grounded, not invented (CLAUDE.md): the season comes from the date, the crop set
and their optimal temperature bands come from the curated `crop_rules.json` (shared
with Crop Watch), and the "reason" is templated from those facts + the live
temperature — the LLM is not involved. Fails soft: if live weather is unavailable
the recommendations fall back to season-only (no fabricated temperature).
"""
from datetime import datetime, timedelta, timezone

from app.core import degradation_ladder
# Reuse the curated crop table + the plateau fit score from the Crop Risk Index.
from app.farmer.crop_watch import parameter_score, _CROPS


def _season_for_month(month: int) -> str:
    """Broad Indian cropping season for a month (matches the crop table's `season`)."""
    return "Kharif" if 6 <= month <= 10 else "Rabi"


def _suitability(fit: float) -> str:
    if fit >= 0.9:
        return "Excellent"
    if fit >= 0.7:
        return "Good"
    if fit >= 0.5:
        return "Fair"
    return "Marginal"


def get_crop_planning(location: str, now=None) -> dict:
    """
    Composite Crop Planning view (§3.10). Never raises; always returns the documented
    shape, degrading to season-only recommendations when live weather is unavailable.
    """
    now = now or datetime.now(timezone.utc)
    season = _season_for_month(now.month)

    # Environmental signal: the location's current temperature (grounded, live),
    # fetched through the fail-soft degradation ladder.
    record = degradation_ladder.get_weather(location) if location else None
    resolved = (record.get("location") if record else None) or location or "your area"
    has_live = bool(record) and record.get("data_tier") != "unresolved_location"
    temp = record.get("temp") if has_live else None
    weather_source = record.get("source") if record else None

    # Candidates: crops grown in this season (plus any all-season crop).
    candidates = [(key, rule) for key, rule in _CROPS.items() if rule.get("season") in (season, "All")]
    scored = []
    for key, rule in candidates:
        lo, hi = rule["temp_opt"]
        fit = parameter_score(temp, lo, hi) if temp is not None else 0.7  # neutral without live temp
        scored.append((fit, key, rule, lo, hi))
    scored.sort(key=lambda item: item[0], reverse=True)

    recommendations = []
    for fit, key, rule, lo, hi in scored[:4]:
        stage_days = rule.get("stage_days", 120)
        harvest = (now + timedelta(days=stage_days)).strftime("%B")
        if temp is not None:
            within = lo <= temp <= hi
            temp_note = f"the area's ~{round(temp)}°C is {'within' if within else 'near'} its {lo}–{hi}°C comfort range"
        else:
            temp_note = f"its comfortable range is {lo}–{hi}°C"
        recommendations.append({
            "crop": key.capitalize(),
            "suitability": _suitability(fit),
            "reason": f"Suited to the {season} season; {temp_note}.",
            "harvest_window": f"around {harvest} (~{stage_days}-day crop)",
        })

    source_bits = [b for b in [weather_source if has_live else None, "WeatherGPT crop rules"] if b]
    return {
        "data_tier": record.get("data_tier") if has_live else "seasonal",
        "source": " + ".join(source_bits),
        "location": resolved,
        "season": season,
        "climate_context": {
            "summary": (f"{season}-season crops for {resolved}, ranked by how well the area's "
                        "temperature fits each crop."),
            "historical_note": ("Suitability is a temperature-fit heuristic over the curated crop table; "
                                "confirm sowing windows against a local package-of-practices."),
        },
        "recommendations": recommendations,
    }
