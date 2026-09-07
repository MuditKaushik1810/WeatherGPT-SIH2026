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


# --- broadened rules: today's peaks + feels-like / humidity / wind ---

def test_peak_heat_later_today_beats_mild_now():
    # Mild right now (28°C), but today peaks at 41°C — safety looks ahead.
    r = build_recommendation(_record(temp=28), today={"peak_temp": 41})
    assert r["title"] == "Beat the heat"


def test_peak_feels_like_triggers_heat():
    r = build_recommendation(_record(temp=30), today={"peak_feels_like": 46})
    assert r["title"] == "Beat the heat"


def test_low_temp_today_triggers_bundle_up():
    r = build_recommendation(_record(temp=18), today={"low_temp": 4})
    assert r["title"] == "Bundle up"


def test_strong_wind():
    r = build_recommendation(_record(), today={"max_wind": 46})
    assert r["title"] == "Expect strong winds"


def test_muggy_uses_humidity_and_feels_like():
    r = build_recommendation(_record(humidity=88, feels_like=34))
    assert r["title"] == "Muggy out"


def test_falls_back_to_current_when_no_today_summary():
    # today=None -> safety rules use the current reading; comfortable stays default.
    assert build_recommendation(_record())["title"] == "Good time for a short outing"
    assert build_recommendation(_record(temp=41))["title"] == "Beat the heat"
