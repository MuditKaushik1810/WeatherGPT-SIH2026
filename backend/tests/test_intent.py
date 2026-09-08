"""
Intent fast-path tests (Architecture doc §3.5). Pure logic, no network — the
gazetteer is the real static table (loaded in-process), so location extraction
is exercised end-to-end without hitting Nominatim.
"""
from app.core import intent


def test_realtime_forecast_query_extracts_location_and_time():
    r = intent.extract_intent("Will it rain tomorrow in Delhi?")
    assert r["location"] == "Delhi"
    assert r["query_class"] == "realtime"   # near-future forecast still uses live data
    assert r["time_range"] == "tomorrow"
    assert r["hazard"] is None
    assert r["resolved_by"] == "fast_path"


def test_current_conditions_query():
    r = intent.extract_intent("Current temperature in Chennai")
    assert r["location"] == "Chennai"
    assert r["query_class"] == "realtime"
    assert r["time_range"] == "now"


def test_historical_query_by_phrase_and_by_year():
    r = intent.extract_intent("How was rainfall last year in Kolkata")
    assert r["location"] == "Kolkata"
    assert r["query_class"] == "historical"
    assert r["time_range"] == "past"

    r2 = intent.extract_intent("monsoon in 2015 for Pune")
    assert r2["query_class"] == "historical"   # bare 4-digit year triggers historical
    assert r2["location"] == "Pune"
    assert r2["time_range"] == "past"          # ...and reads as a past time range


def test_safety_query_detects_hazard_and_routes_to_safety():
    r = intent.extract_intent("Cyclone warning for Chennai")
    assert r["query_class"] == "safety"
    assert r["hazard"] == "cyclone"
    assert r["location"] == "Chennai"


def test_safety_outranks_trip_when_a_severe_hazard_is_present():
    # "travel" would read as trip, but an active flood is a safety-first situation.
    r = intent.extract_intent("Is it safe to travel with the flooding in Patna?")
    assert r["query_class"] == "safety"
    assert r["hazard"] == "flood"
    assert r["location"] == "Patna"


def test_thunderstorm_is_noted_but_not_force_routed_to_safety():
    # Thunderstorm/lightning are common weather, not auto-emergencies: hazard is
    # flagged, but without alert/warning language the class stays realtime.
    r = intent.extract_intent("any lightning near Kolkata")
    assert r["hazard"] == "thunderstorm"
    assert r["query_class"] == "realtime"


def test_farmer_query():
    r = intent.extract_intent("Best time to sow wheat in Ludhiana")
    assert r["query_class"] == "farmer"
    assert r["location"] == "Ludhiana"


def test_trip_query_extracts_first_city():
    r = intent.extract_intent("Road trip from Delhi to Jaipur")
    assert r["query_class"] == "trip"
    assert r["location"] == "Delhi"   # fast path grabs the first city; routing splits it later


def test_multiword_city_beats_its_substring():
    r = intent.extract_intent("weather in new delhi")
    assert r["location"] == "New Delhi"   # not "Delhi"


def test_no_location_and_no_weather_signal_defaults_to_realtime():
    r = intent.extract_intent("thank you very much")
    assert r["location"] is None          # signal that an LLM fallback is worthwhile
    assert r["query_class"] == "realtime"
    assert r["resolved_by"] == "fast_path"
