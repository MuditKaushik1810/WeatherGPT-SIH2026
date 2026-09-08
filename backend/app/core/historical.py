"""
Loader for the preloaded historical baselines (built by
backend/scripts/build_historical_baselines.py). A read-only accessor the Trend
Engine (Sprint 3) builds on — per-city day-of-year climatology + annual series.

Loaded lazily at import (a few MB of JSON), so nothing pays the cost unless the
historical/trend features are actually used.
"""
import json
import os

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "historical_baselines.json")

with open(_DATA_PATH) as f:
    _BASELINES = json.load(f)
    _BASELINES.pop("_comment", None)


def get_baseline(location: str) -> dict | None:
    """
    Return the preloaded historical baseline for a location, or None if not present.

    Shape:
        {
          "clim_temp":     [366 floats],  # day-of-year avg mean temperature (°C)
          "clim_precip":   [366 floats],  # day-of-year avg daily precipitation (mm)
          "years":         [int, ...],    # e.g. 2016..2025
          "annual_temp":   [float, ...],  # annual mean temperature per year
          "annual_precip": [float, ...],  # annual total precipitation per year (mm)
        }

    Case-insensitive; keys match the geocoding table's lowercase city names, so
    any city in the static table has a baseline here.
    """
    return _BASELINES.get(location.strip().lower())
