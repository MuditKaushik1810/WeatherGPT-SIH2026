"""
Forecast retrieval for future-dated chat queries (Sprint 2).

When intent extraction tags a query with time_range "tomorrow" / "this week",
/chat needs the forecast for those days — not current conditions. This module
does ONE forecast fetch (via the same primary→fallback path the ladder uses) and
summarizes the requested day offsets into grounded day records.

Fails soft like everything else: an unresolvable location or a dead forecast
source returns a record with data_tier "unresolved_location" / "source_unavailable"
and an empty `days` list plus a message — the grounding assembler turns that into
an honest answer, never a bare refusal.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.connectors import open_meteo
from app.core import degradation_ladder, geocoding

_IST = ZoneInfo("Asia/Kolkata")
_OFFSET_LABELS = {0: "Today", 1: "Tomorrow"}


def _label(offset: int, date_str: str) -> str:
    return _OFFSET_LABELS.get(offset) or datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")


def get_daily_forecast(location: str, offsets: list[int], now: datetime | None = None) -> dict:
    """
    Return a forecast record for `location` over the given day `offsets`
    (0 = today, 1 = tomorrow, ...), in IST.

    Shape:
        {
          "location": str,
          "source": str | None,
          "data_tier": "exact" | "source_unavailable" | "unresolved_location",
          "fetched_at": str | None,
          "days": [ {date, offset, label, peak_temp, low_temp, peak_feels_like,
                     max_precip_chance, max_wind, condition}, ... ],  # only days
                                                                      # actually in range
          "message": str | None,   # honest note when days is empty / partial
        }

    `now` is injectable for deterministic tests.
    """
    coords = geocoding.resolve_location(location)
    if coords is None:
        return {
            "location": location, "source": None, "data_tier": "unresolved_location",
            "fetched_at": None, "days": [],
            "message": f"Could not resolve '{location}'. Try a nearby major city or district name.",
        }

    forecast_data = degradation_ladder.fetch_forecast_with_fallback(coords)
    raw_hourly = forecast_data.get("_raw_hourly")
    if not raw_hourly:
        return {
            "location": location, "source": forecast_data.get("source"),
            "data_tier": "source_unavailable", "fetched_at": forecast_data.get("fetched_at"),
            "days": [],
            "message": f"Live forecast for '{location}' is temporarily unavailable — please try again shortly.",
        }

    now = now or datetime.now(_IST)
    days = []
    for offset in offsets:
        date_str = (now + timedelta(days=offset)).strftime("%Y-%m-%d")
        summary = open_meteo.summarize_day(raw_hourly, date_str)
        if summary["peak_temp"] is None and summary["max_precip_chance"] is None:
            continue  # that day is beyond the fetched horizon — skip honestly
        days.append({"offset": offset, "label": _label(offset, date_str), **summary})

    message = None
    if not days:
        message = (
            f"The forecast for '{location}' doesn't reach that far ahead on the free tier — "
            "I can give the next couple of days."
        )
    return {
        "location": location,
        "source": forecast_data.get("source"),
        "data_tier": "exact" if days else "source_unavailable",
        "fetched_at": forecast_data.get("fetched_at"),
        "days": days,
        "message": message,
    }
