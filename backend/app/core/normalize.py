"""
Normalizes each connector's own response shape into the ONE internal shape
every downstream consumer (grounding assembler, farmer advisory, trip
planner...) depends on. See CLAUDE.md's "Non-negotiable data contract" and
Architecture doc Section 3.10.

Adding a new field here is safe (additive). Renaming or removing a field is a
breaking change — do that in a visible PR, not quietly.
"""


def normalize_weather_record(location: str, open_meteo_data: dict, imd_data: dict) -> dict:
    has_exact_warning = imd_data["data_tier"] == "exact"
    return {
        "location": location,
        "temp": open_meteo_data["temp"],
        "condition": open_meteo_data["condition"],
        "precipitation_chance": open_meteo_data["precipitation_chance"],
        "warnings": imd_data["warnings"],
        "source": "IMD" if has_exact_warning and imd_data["warnings"] else open_meteo_data["source"],
        "data_tier": "exact" if (has_exact_warning or open_meteo_data["data_tier"] == "exact") else "regional_fallback",
        "fetched_at": open_meteo_data["fetched_at"],
    }
