"""
Recommendation engine tests — pure function, no external calls.

Locks the safety-first priority order and the "never bare-refuse" behaviour.
"""
from app.core.recommendation import build_recommendation


def _record(**overrides):
    base = {"temp": 25, "aqi": 50, "precipitation_chance": 0.1, "warnings": []}
    base.update(overrides)
    return base


def test_active_warning_outranks_everything():
    r = build_recommendation(_record(warnings=["Heavy rainfall warning"], temp=42, aqi=300))
    assert r["title"] == "Stay alert"


def test_no_data_is_honest_not_bare():
    r = build_recommendation(
        {"temp": None, "aqi": None, "precipitation_chance": None, "warnings": []}
    )
    assert r["title"] == "Limited data right now"
    assert r["message"]  # never empty / never a bare refusal


def test_extreme_heat():
    assert build_recommendation(_record(temp=41))["title"] == "Beat the heat"


def test_extreme_cold():
    assert build_recommendation(_record(temp=3))["title"] == "Bundle up"


def test_poor_aqi_before_rain():
    assert build_recommendation(_record(aqi=180, precipitation_chance=0.9))["title"] == "Limit outdoor time"


def test_high_rain():
    assert build_recommendation(_record(precipitation_chance=0.7))["title"] == "Carry an umbrella"


def test_moderate_aqi():
    assert build_recommendation(_record(aqi=120))["title"] == "Sensitive groups, take care"


def test_comfortable_default():
    assert build_recommendation(_record())["title"] == "Good time for a short outing"
