"""
Grounding assembler tests (Architecture doc §3.5). Pure logic — no mocks needed.

The assembler is the anti-hallucination step, so the tests pin down exactly the
two guarantees it exists to make: (1) only facts actually present are grounded —
nothing is invented for a None metric; and (2) it never produces an empty /
bare-refusal block — every tier, including a total gap, yields tier framing +
honest guidance the LLM can answer from.
"""
from app.core import grounding


def _exact_record():
    return {
        "location": "Delhi", "temp": 31.9, "condition": "light rain shower",
        "precipitation_chance": 0.77, "humidity": 84, "feels_like": 32.4,
        "wind_speed": 11.5, "aqi": 158, "warnings": [], "source": "WeatherAPI",
        "data_tier": "exact", "fetched_at": "2026-09-09T09:00:00Z",
    }


def test_exact_record_grounds_every_present_metric():
    ctx = grounding.build_grounding_context(_exact_record(), query_class="realtime")

    assert ctx["answerable"] is True
    assert ctx["data_tier"] == "exact"
    assert ctx["source"] == "WeatherAPI"
    assert ctx["query_class"] == "realtime"
    blob = "\n".join(ctx["facts"])
    assert "Temperature: 31.9°C" in blob
    assert "Condition: light rain shower" in blob
    assert "Feels like: 32.4°C" in blob
    assert "Humidity: 84%" in blob
    assert "Wind speed: 11.5 km/h" in blob
    assert "Chance of precipitation: 77%" in blob   # 0.77 -> 77%
    assert "Air quality (US AQI): 158" in blob
    # The rendered block carries the facts + tier line for prompt injection.
    assert "FACTS:" in ctx["context_block"]
    assert "DATA TIER: exact" in ctx["context_block"]


def test_none_metrics_are_omitted_never_invented():
    # Only temp + aqi are known; the rest failed soft (None). They must not appear.
    record = {
        "location": "Delhi", "temp": 28.0, "condition": None,
        "precipitation_chance": None, "humidity": None, "feels_like": None,
        "wind_speed": None, "aqi": 158, "warnings": [], "source": "WeatherAPI",
        "data_tier": "exact", "fetched_at": "2026-09-09T09:00:00Z",
    }
    ctx = grounding.build_grounding_context(record)

    joined = "\n".join(ctx["facts"])
    assert "Temperature: 28.0°C" in joined
    assert "Air quality (US AQI): 158" in joined
    assert "Humidity" not in joined      # absent metric -> absent fact, not a guess
    assert "Wind speed" not in joined
    assert "Feels like" not in joined
    assert ctx["answerable"] is True


def test_historical_baseline_labels_temp_as_typical():
    record = {
        "location": "Delhi", "temp": 28.7, "condition": None,
        "precipitation_chance": None, "humidity": None, "feels_like": None,
        "wind_speed": None, "aqi": 164, "warnings": [], "source": "Historical",
        "data_tier": "historical_baseline", "fetched_at": "2026-09-09T09:00:00Z",
        "message": "Live forecast for 'Delhi' is temporarily unavailable...",
    }
    ctx = grounding.build_grounding_context(record)

    assert any("Typical temperature for this date: 28.7°C" in f for f in ctx["facts"])
    assert not any(f.startswith("Temperature:") for f in ctx["facts"])  # not framed as live
    assert "typical" in ctx["tier_note"].lower()
    assert ctx["gap_guidance"] == record["message"]
    assert ctx["answerable"] is True


def test_active_warning_is_grounded():
    record = _exact_record()
    record["warnings"] = ["Heavy rainfall warning - Delhi"]
    ctx = grounding.build_grounding_context(record)
    assert any("Heavy rainfall warning - Delhi" in f for f in ctx["facts"])


def test_source_unavailable_with_no_metrics_still_never_bare_refuses():
    record = {
        "location": "Delhi", "temp": None, "condition": None,
        "precipitation_chance": None, "humidity": None, "feels_like": None,
        "wind_speed": None, "aqi": None, "warnings": [], "source": None,
        "data_tier": "source_unavailable", "fetched_at": None,
        "message": "Live forecast data is temporarily unavailable for 'Delhi'.",
    }
    ctx = grounding.build_grounding_context(record)

    assert ctx["answerable"] is False
    assert ctx["facts"] == []
    assert ctx["gap_guidance"]                       # honest next step, never empty
    assert "FACTS: (none could be retrieved)" in ctx["context_block"]
    assert "GUIDANCE:" in ctx["context_block"]


def test_unresolved_location_yields_guidance_not_a_blank():
    record = {
        "location": "ZzzNotARealPlace", "temp": None, "condition": None,
        "precipitation_chance": None, "humidity": None, "feels_like": None,
        "wind_speed": None, "aqi": None, "warnings": [], "source": None,
        "data_tier": "unresolved_location", "fetched_at": None,
        "message": "Could not resolve 'ZzzNotARealPlace' to a location. Try a nearby major city.",
    }
    ctx = grounding.build_grounding_context(record)

    assert ctx["answerable"] is False
    assert ctx["gap_guidance"] == record["message"]
    assert "nearby major city" in ctx["context_block"]


def test_constraints_carry_the_two_non_negotiable_rules_every_time():
    for tier_record in (_exact_record(), {"data_tier": "unresolved_location", "warnings": []}):
        ctx = grounding.build_grounding_context(tier_record)
        joined = " ".join(ctx["constraints"]).lower()
        assert "never invent" in joined                    # no-hallucination rule
        assert "never reply with a bare" in joined          # no-bare-refuse rule
        assert len(ctx["constraints"]) >= 4


def test_build_forecast_context_grounds_day_summaries():
    fc = {
        "location": "Delhi", "source": "WeatherAPI", "data_tier": "exact", "fetched_at": "x",
        "days": [{
            "offset": 1, "label": "Tomorrow", "date": "2026-09-10", "peak_temp": 34.0,
            "low_temp": 27.0, "peak_feels_like": 37.0, "max_precip_chance": 0.7,
            "max_wind": 15.0, "condition": "Patchy rain",
        }],
        "message": None,
    }
    ctx = grounding.build_forecast_context(fc, "realtime")
    assert ctx["answerable"] is True
    assert ctx["data_tier"] == "exact"
    assert any("Tomorrow (2026-09-10)" in f for f in ctx["facts"])
    assert any("70% chance of rain" in f for f in ctx["facts"])
    assert any("high 34.0°C, low 27.0°C" in f for f in ctx["facts"])
    assert "FORECAST:" in ctx["context_block"]
    joined = " ".join(ctx["constraints"]).lower()
    assert "never invent" in joined and "never reply with a bare" in joined


def test_build_forecast_context_empty_never_bare_refuses():
    fc = {"location": "Delhi", "source": "WeatherAPI", "data_tier": "source_unavailable",
          "fetched_at": None, "days": [], "message": "forecast doesn't reach that far"}
    ctx = grounding.build_forecast_context(fc)
    assert ctx["answerable"] is False
    assert ctx["gap_guidance"] == "forecast doesn't reach that far"
    assert "FORECAST: (none could be retrieved)" in ctx["context_block"]
