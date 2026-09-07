from app.core import geocoding


def test_static_city_resolves_without_network_call():
    result = geocoding.resolve_location("Delhi")
    assert result is not None
    assert result["resolved_via"] == "static_table"
    assert -90 <= result["lat"] <= 90
    assert -180 <= result["lon"] <= 180


def test_lookup_is_case_insensitive():
    result = geocoding.resolve_location("  DELHI  ")
    assert result is not None
    assert result["resolved_via"] == "static_table"


def test_unknown_place_falls_back_to_nominatim(monkeypatch):
    def fake_nominatim(name):
        return {"lat": 12.34, "lon": 56.78, "resolved_via": "nominatim"}

    monkeypatch.setattr(geocoding, "_resolve_via_nominatim", fake_nominatim)
    result = geocoding.resolve_location("SomeVillageNotInTable")
    assert result["resolved_via"] == "nominatim"


def test_expanded_table_resolves_many_cities_without_network():
    # Cities that were NOT in the original ~40-city seed now resolve from the
    # static table (GeoNames-sourced expansion), including low-population capitals.
    for city in ["Noida", "Gurugram", "Kota", "Gangtok", "Itanagar", "Leh"]:
        result = geocoding.resolve_location(city)
        assert result is not None, city
        assert result["resolved_via"] == "static_table", city
