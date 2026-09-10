"""
Crop Watch — the Farmer Crop Risk Index and the composite /farmer/crop-watch view
(Architecture doc §3.7 and §3.10).

Answers "what's happening to my planted crop, and why?" for an already-planted
crop. The score is a **weighted crop-stress model**: each comparable weather
parameter (temperature, humidity, soil moisture) is scored 0-1 by how close it
sits to the middle of that crop's curated optimal band, combined with weights and
inverted to a 0-100 risk. It is FAIL-SOFT — a missing parameter is dropped and the
weights renormalize over what's available (CLAUDE.md's data contract: any metric
may be None).

Rainfall is handled as an explicit THREAT (heavy rain -> waterlogging/fungal risk),
not a fit term, because live precipitation and a crop's seasonal rainfall need are
different scales (decision locked Sprint 3). Disease suitability contributes one
explained "disease" threat via each crop's key-disease rule.

Every number the advice rests on comes from data/crop_rules.json. Its optimal-
temperature bands and key-disease conditions are sourced/cited there (so the
response's `provisional` flag is data-driven — false while those hold); the humidity
and soil-moisture bands remain documented approximations.

External calls (weather, soil moisture) are made through fail-soft connectors and
are mocked in tests — nothing here hits a live endpoint from the suite.
"""
import json
import os

from app.core import degradation_ladder, geocoding
from app.connectors import open_meteo_soil

_RULES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "crop_rules.json")
with open(_RULES_PATH, encoding="utf-8") as _f:
    _RULES = json.load(_f)

_CROPS = _RULES["crops"]
_ADVISORIES = _RULES["advisories"]

# The response's `provisional` flag is data-driven: false once the load-bearing,
# advice-driving numbers — the temperature fit band and the key-disease conditions —
# are sourced (see crop_rules.json `_meta`). Humidity and soil-moisture bands remain
# documented approximations there, but the flag tracks the verified thresholds.
_V = _RULES["_meta"]["verified"]
_PROVISIONAL = not (_V.get("temperature_opt") is True and _V.get("key_disease") is True)

# Fit weights. Only the two parameters with a well-defined per-crop optimal band are
# fit terms: temperature (dominant) and soil moisture. HUMIDITY is deliberately NOT a
# fit term — humidity risk is crop- and growth-stage-specific, so it is expressed
# through the stage-aware disease threat, not a generic "comfort band". Rainfall is a
# threat too. Weights renormalize over whichever fit params are present (fail-soft).
_WEIGHTS = {"temperature": 0.6, "soil_moisture": 0.4}

# Generic growth stages by fraction of the crop's total duration.
_STAGES = ["Germination", "Vegetative", "Flowering", "Yield Formation", "Maturity"]
_STAGE_BOUNDS = [0.10, 0.45, 0.65, 0.85, 1.01]  # upper fraction bound per stage


def parameter_score(actual: float, low: float, high: float) -> float:
    """
    Fit of `actual` to a crop's optimal range [low, high], on 0-1.

    Plateau model: 1.0 anywhere INSIDE the optimal range (being in-range is ideal,
    including at the edges), then a linear fall-off OUTSIDE it — reaching 0 one
    band-width beyond either edge. This is truer to "optimal range" semantics than a
    triangular peak, which would wrongly score the range's own edges as max stress.
    """
    if low <= actual <= high:
        return 1.0
    span = (high - low) or 1.0
    dist = (low - actual) if actual < low else (actual - high)
    return max(0.0, 1 - dist / span)


def _risk_level(score: int) -> str:
    if score < 25:
        return "Low"
    if score < 50:
        return "Moderate"
    if score < 75:
        return "High"
    return "Very High"


def _stress_level(stress: float) -> str:
    return "High" if stress >= 0.6 else "Moderate" if stress >= 0.35 else "Low"


def _growth_stage(days_after_sowing, stage_days: int):
    """Return (stage, next_stage) from days-after-sowing and total crop duration."""
    if days_after_sowing is None or not stage_days:
        return None, None
    frac = max(0.0, days_after_sowing / stage_days)
    for i, bound in enumerate(_STAGE_BOUNDS):
        if frac < bound:
            nxt = _STAGES[i + 1] if i + 1 < len(_STAGES) else "Harvest"
            return _STAGES[i], nxt
    return "Maturity", "Harvest"


def _advisory(key: str, disease: str | None = None) -> dict:
    """Curated action for a problem key, with {disease} interpolated when present."""
    entry = _ADVISORIES.get(key, _ADVISORIES["comfortable"])
    title = entry["title"].replace("{disease}", disease or "disease")
    items = [item.replace("{disease}", disease or "disease") for item in entry["items"]]
    return {"title": title, "items": items}


def _fit_threats(rule, temp, soil):
    """A threat per stressed fit parameter (temperature, soil moisture), each explaining WHY."""
    threats = []
    checks = [
        ("temperature", temp, rule["temp_opt"], "°C",
         ("heat", "Heat Stress"), ("cold", "Cold Stress"), "high_temp", "low_temp"),
        ("soil_moisture", soil, rule["soil_moisture_opt"], " m³/m³",
         ("waterlogging", "Waterlogging"), ("dry_soil", "Low Soil Moisture"),
         "high_soil_moisture", "low_soil_moisture"),
    ]
    for name, actual, (lo, hi), unit, high_t, low_t, high_key, low_key in checks:
        if actual is None:
            continue
        stress = 1 - parameter_score(actual, lo, hi)
        if stress < 0.35:
            continue
        above = actual > (lo + hi) / 2
        tid, label = high_t if above else low_t
        problem_key = high_key if above else low_key
        side = "above" if above else "below"
        threats.append({
            "id": tid, "label": label, "level": _stress_level(stress),
            "detail": f"{actual}{unit} is {side} the {lo}–{hi}{unit} comfort range for this crop.",
            "_problem": problem_key,
        })
    return threats


def _disease_threat(rule, temp, humidity, crop_stage):
    """
    The crop's key-disease threat — crop- AND growth-stage-specific (not a blanket
    "humidity > 90% is bad"). Humidity + temperature must favour the disease; the
    LEVEL and the explanation are then modulated by whether the crop is at a stage
    the disease actually damages (`susceptible_stages`).
    """
    if temp is None or humidity is None:
        return None
    disease = rule.get("key_disease")
    if not disease:
        return None
    favors = disease["favors"]
    t_lo, t_hi = favors["temp"]
    if not (t_lo <= temp <= t_hi):
        return None

    hmin = favors.get("humidity_min")
    hmax = favors.get("humidity_max")
    if hmin is not None:
        if humidity < hmin:
            return None
        strong = humidity >= hmin + 10
        cond = f"{humidity}% humidity and ~{temp}°C"
    elif hmax is not None:
        if humidity > hmax:
            return None
        strong = humidity <= hmax - 10
        cond = f"dry air ({humidity}% humidity) and warm ~{temp}°C"
    else:
        strong, cond = False, f"~{temp}°C"

    name = disease["name"]
    susceptible = disease.get("susceptible_stages", [])
    if crop_stage in susceptible:                     # at a vulnerable stage — the real risk
        level = "High" if strong else "Moderate"
        detail = f"At the {crop_stage} stage — a susceptible window for {name} — {cond} favour it."
    elif crop_stage is None:                          # no sowing date → can't stage-resolve
        level = "Moderate" if strong else "Low"
        detail = f"{cond.capitalize()} favour {name}; set your sowing date for stage-specific risk."
    else:                                             # favoured, but not a vulnerable stage
        level = "Low"
        nxt = susceptible[0] if susceptible else "a susceptible stage"
        detail = (f"{cond.capitalize()} favour {name}, but {crop_stage} is a lower-risk stage "
                  f"for it — keep watching toward {nxt}.")
    return {"id": "disease", "label": "Disease", "level": level,
            "detail": detail, "_problem": "disease", "_disease": name}


def _rain_threat(precip_chance):
    """A heavy-rain threat from precipitation chance (rainfall as a threat, not a fit term)."""
    if precip_chance is None or precip_chance < 0.6:
        return None
    level = "High" if precip_chance >= 0.8 else "Moderate"
    pct = round(precip_chance * 100)
    return {"id": "rain", "label": "Heavy Rain", "level": level,
            "detail": f"{pct}% chance of rain — plan for drainage and hold off spraying.",
            "_problem": "heavy_rain"}


_LEVEL_RANK = {"High": 3, "Moderate": 2, "Low": 1}


def _unresolved(location, crop, days_after_sowing, message):
    """Honest fail-soft composite — stable shape, no fabricated risk."""
    return {
        "data_tier": "unresolved_location", "source": None, "provisional": _PROVISIONAL,
        "location": location, "crop": crop, "days_after_sowing": days_after_sowing,
        "crop_stage": None, "next_stage": None,
        "risk_score": None, "risk_level": None, "components": {}, "threats": [],
        "recommended_action": {"title": message, "items": []},
        "climate_context": None, "message": message,
    }


def get_crop_watch(crop: str, location: str, days_after_sowing=None) -> dict:
    """
    Composite Crop Watch view for a planted crop (Architecture §3.10
    `GET /farmer/crop-watch`). Never raises; returns a stable shape even when the
    crop is unknown or live data is unavailable (honest, never a bare refusal).
    """
    crop_key = (crop or "").strip().lower()
    rule = _CROPS.get(crop_key)
    if rule is None:
        supported = ", ".join(sorted(_CROPS))
        return _unresolved(location, crop, days_after_sowing,
                           f"'{crop}' isn't in the crop rule table yet. Supported: {supported}.")

    coords = geocoding.resolve_location(location)
    record = degradation_ladder.get_weather(location) if location else None
    if not coords or record is None or record.get("data_tier") == "unresolved_location":
        return _unresolved(location, crop,
                           days_after_sowing, f"Couldn't resolve a location for '{location}'.")

    temp = record.get("temp")
    humidity = record.get("humidity")
    precip_chance = record.get("precipitation_chance")
    soil = open_meteo_soil.fetch_soil_moisture(coords["lat"], coords["lon"]).get("soil_moisture")

    # Weighted crop-stress fit (temperature + soil moisture), renormalized over the
    # parameters actually available. Humidity is not a fit term — see the disease threat.
    available = {
        "temperature": (temp, rule["temp_opt"]),
        "soil_moisture": (soil, rule["soil_moisture_opt"]),
    }
    components, total_w, weighted = {}, 0.0, 0.0
    for name, (actual, (lo, hi)) in available.items():
        if actual is None:
            continue
        s = round(parameter_score(actual, lo, hi), 2)
        components[name] = s
        total_w += _WEIGHTS[name]
        weighted += _WEIGHTS[name] * s

    stage, next_stage = _growth_stage(days_after_sowing, rule["stage_days"])
    soil_source = " + Open-Meteo (soil moisture)" if soil is not None else ""
    base = {
        "data_tier": record.get("data_tier"),
        "source": f"{record.get('source')}{soil_source}" if record.get("source") else None,
        "provisional": _PROVISIONAL,
        "location": record.get("location") or location,
        "crop": crop_key,
        "days_after_sowing": days_after_sowing,
        "crop_stage": stage, "next_stage": next_stage,
        "components": components,
    }

    if total_w == 0:
        # No comparable parameter available — honest, no fabricated score.
        base.update({"risk_score": None, "risk_level": None, "threats": [],
                     "recommended_action": _advisory("comfortable"),
                     "climate_context": None,
                     "message": "Live crop-weather data is temporarily unavailable."})
        return base

    fit = weighted / total_w
    risk_score = round((1 - fit) * 100)
    risk_level = _risk_level(risk_score)

    # Threats (each explained), then the action for the most severe one.
    threats = _fit_threats(rule, temp, soil)
    disease = _disease_threat(rule, temp, humidity, stage)
    if disease:
        threats.append(disease)
    rain = _rain_threat(precip_chance)
    if rain:
        threats.append(rain)
    threats.sort(key=lambda th: _LEVEL_RANK.get(th["level"], 0), reverse=True)

    if threats:
        top = threats[0]
        action = _advisory(top["_problem"], disease=top.get("_disease"))
    else:
        action = _advisory("comfortable")

    # Strip internal keys from the public threats.
    public_threats = [{k: v for k, v in th.items() if not k.startswith("_")} for th in threats]

    base.update({
        "risk_score": risk_score,
        "risk_level": risk_level,
        "threats": public_threats,
        "recommended_action": action,
        "climate_context": {
            "title": "Current-season conditions",
            "level": risk_level,
            "detail": (f"Based on live weather for {base['location']}. Historical/trend context "
                       "will refine this in a later update."),
        },
    })
    return base
