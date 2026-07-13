"""Tests for thermostat/climate_zone.py — pandas 2.0 compatibility."""

import pytest
from thermostat.climate_zone import retrieve_climate_zone


def test_retrieve_climate_zone_known_zipcode():
    """retrieve_climate_zone must not raise AttributeError for a known zipcode.

    Regression test: pandas 2.0 removed Series.iteritems(); calls to it inside
    retrieve_climate_zone raised AttributeError, making every pipeline batch fail.
    """
    result = retrieve_climate_zone(None, '60601')
    assert result.climate_zone is not None
    assert result.baseline_regional_cooling_comfort_temperature is not None
    assert result.baseline_regional_heating_comfort_temperature is not None


def test_retrieve_climate_zone_unknown_zipcode_returns_none_temps():
    """An unrecognized zipcode returns None baseline temps without raising."""
    result = retrieve_climate_zone(None, '00000')
    assert result.climate_zone is None
    assert result.baseline_regional_cooling_comfort_temperature is None
    assert result.baseline_regional_heating_comfort_temperature is None


def test_retrieve_climate_zone_baseline_temps_are_numeric():
    """Baseline temps for a valid zipcode are numeric, not strings."""
    result = retrieve_climate_zone(None, '10001')
    assert isinstance(result.baseline_regional_cooling_comfort_temperature, (int, float))
    assert isinstance(result.baseline_regional_heating_comfort_temperature, (int, float))
