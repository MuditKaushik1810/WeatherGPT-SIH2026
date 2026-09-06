"""
Normalizes each connector's own response shape into the ONE internal shape
every downstream consumer (grounding assembler, farmer advisory, trip
planner...) depends on. See CLAUDE.md's "Non-negotiable data contract" and
Architecture doc Section 3.10.

Adding a new field here is safe (additive). Renaming or removing a field is a
breaking change — do that in a visible PR, not quietly.

The forecast metrics (temp/condition/precipitation_chance/humidity/feels_like/
wind_speed) come from the Open-Meteo forecast connector; `aqi` comes from the
SEPARATE Open-Meteo Air Quality connector (US AQI scale — see that module).
"""


def normalize_weather_record(
    location: str,
    open_meteo_data: dict,
    imd_data: dict,
    air_quality_data: dict | None = None,
) -> dict:
    """
    Fold every connector's response into the one internal record shape.

    Handles the case where the live forecast source (Open-Meteo) failed soft
    and returned data_tier="unavailable": rather than reading forecast fields
    that are None and presenting a fake "exact" answer, it returns an honest
    "source_unavailable" record — the ladder's tier-4 gap, paired with whatever
    adjacent data we *do* have (an active IMD warning, and AQI if the separate
    air-quality source is still up), never a bare refusal.

    Note: "source_unavailable" is an additive value on the data_tier set from
    the documented contract (exact / regional_fallback / historical_baseline /
    unresolved_location) — flagged in the PR for the team, not a silent change.
    """
    has_exact_warning = imd_data["data_tier"] == "exact"
    warnings = imd_data["warnings"]
    # AQI is fetched independently of the forecast, so surface it even when the
    # forecast source is down (it may still be None if AQI also failed soft).
    aqi = (air_quality_data or {}).get("aqi")

    if open_meteo_data["data_tier"] == "unavailable":
        # Live forecast is down. Degrade honestly instead of crashing or faking.
        return {
            "location": location,
            "temp": None,
            "condition": None,
            "precipitation_chance": None,
            "humidity": None,
            "feels_like": None,
            "wind_speed": None,
            "aqi": aqi,
            "warnings": warnings,
            "source": "IMD" if (has_exact_warning and warnings) else None,
            "data_tier": "source_unavailable",
            "fetched_at": imd_data["fetched_at"],
            "message": (
                f"Live forecast data is temporarily unavailable for '{location}'. "
                + (
                    "Showing the active official warning below."
                    if warnings
                    else "No official warnings are active either — please try again shortly."
                )
            ),
        }

    return {
        "location": location,
        "temp": open_meteo_data["temp"],
        "condition": open_meteo_data["condition"],
        "precipitation_chance": open_meteo_data["precipitation_chance"],
        # Additive metrics — .get() so a partial/older connector payload degrades
        # to None instead of raising a KeyError.
        "humidity": open_meteo_data.get("humidity"),
        "feels_like": open_meteo_data.get("feels_like"),
        "wind_speed": open_meteo_data.get("wind_speed"),
        "aqi": aqi,
        "warnings": warnings,
        "source": "IMD" if has_exact_warning and warnings else open_meteo_data["source"],
        "data_tier": "exact" if (has_exact_warning or open_meteo_data["data_tier"] == "exact") else "regional_fallback",
        "fetched_at": open_meteo_data["fetched_at"],
    }
