from app.core import historical


def test_baseline_for_a_known_city_has_the_expected_shape():
    baseline = historical.get_baseline("Delhi")
    assert baseline is not None
    assert len(baseline["clim_temp"]) == 366
    assert len(baseline["clim_precip"]) == 366
    assert len(baseline["years"]) == len(baseline["annual_temp"]) == len(baseline["annual_precip"])
    # sanity: in India, the January baseline is cooler than mid-July
    assert baseline["clim_temp"][0] < baseline["clim_temp"][195]


def test_baseline_lookup_is_case_insensitive():
    assert historical.get_baseline("  DELHI  ") is not None


def test_unknown_location_returns_none():
    assert historical.get_baseline("ZzzNotARealPlaceXyz123") is None
