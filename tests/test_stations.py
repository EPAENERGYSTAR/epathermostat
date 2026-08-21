"""Tests for thermostat/stations.py — ZCTA->station selection against the
reshaped eeweather WeatherLocation/WeatherStation API (registry-inventory based,
no primed-cache probe)."""
import pandas as pd
from unittest.mock import patch, MagicMock

from eeweather.exceptions import UnrecognizedPlaceError

from thermostat.stations import (
    get_closest_station_by_zipcode,
    lookup_usaf_station_by_zipcode,
)


def _candidates(station_ids):
    """A distance-ranked candidates frame, nearest first, indexed by station id."""
    return pd.DataFrame(index=pd.Index(station_ids, name="id"))


def _station(usaf, inv=(2015, 2025)):
    st = MagicMock()
    st.inventory_years = {"ghcnh": inv} if inv else {}
    st.ids = {"usaf": (usaf,)} if usaf else {}
    return st


def test_returns_nearest_station_covering_years():
    location = MagicMock()
    location.candidates.return_value = _candidates(["S1", "S2"])
    stations = {"S1": _station("111111"), "S2": _station("222222")}

    with patch("thermostat.stations.WeatherLocation") as WL, patch(
        "thermostat.stations.WeatherStation", side_effect=lambda sid: stations[sid]
    ):
        WL.from_place.return_value = location
        result = get_closest_station_by_zipcode("91104", required_years=[2016, 2017])

    # nearest candidate that covers the years wins
    assert result == "111111"
    WL.from_place.assert_called_once_with("zcta", "91104", sources=("ghcnh",))


def test_skips_station_missing_years():
    location = MagicMock()
    location.candidates.return_value = _candidates(["S1", "S2"])
    stations = {
        "S1": _station("111111", inv=(2020, 2021)),  # does not cover 2016
        "S2": _station("222222", inv=(2010, 2025)),
    }

    with patch("thermostat.stations.WeatherLocation") as WL, patch(
        "thermostat.stations.WeatherStation", side_effect=lambda sid: stations[sid]
    ):
        WL.from_place.return_value = location
        result = get_closest_station_by_zipcode("91104", required_years=[2016])

    assert result == "222222"


def test_skips_canadian_stations():
    location = MagicMock()
    location.candidates.return_value = _candidates(["S1", "S2"])
    stations = {"S1": _station("A00001"), "S2": _station("722222")}  # A = Canadian

    with patch("thermostat.stations.WeatherLocation") as WL, patch(
        "thermostat.stations.WeatherStation", side_effect=lambda sid: stations[sid]
    ):
        WL.from_place.return_value = location
        result = get_closest_station_by_zipcode("91104", required_years=[2020])

    assert result == "722222"


def test_unrecognized_zcta_falls_back_to_json():
    with patch("thermostat.stations.WeatherLocation") as WL, patch(
        "thermostat.stations.lookup_usaf_station_by_zipcode", return_value="JSONSTN"
    ) as json_fallback:
        WL.from_place.side_effect = UnrecognizedPlaceError("zcta", "00000")
        result = get_closest_station_by_zipcode("00000", required_years=[2020])

    assert result == "JSONSTN"
    json_fallback.assert_called_once()


def test_no_qualifying_station_falls_back_to_json():
    location = MagicMock()
    location.candidates.return_value = _candidates(["S1"])
    stations = {"S1": _station("111111", inv=(2000, 2005))}  # too old

    with patch("thermostat.stations.WeatherLocation") as WL, patch(
        "thermostat.stations.WeatherStation", side_effect=lambda sid: stations[sid]
    ), patch(
        "thermostat.stations.lookup_usaf_station_by_zipcode", return_value="JSONSTN"
    ):
        WL.from_place.return_value = location
        result = get_closest_station_by_zipcode("91104", required_years=[2020])

    assert result == "JSONSTN"


def test_lookup_usaf_station_by_zipcode_reads_static_map():
    # smoke test on the static JSON fallback map
    assert lookup_usaf_station_by_zipcode("00000-not-a-zip") is None


def test_reported_during_is_permissive_without_the_coverage_api():
    """Behavior is unchanged until eeweather exposes coverage."""
    from thermostat import stations

    with patch.object(stations, "get_station_coverage", None):
        assert stations._reported_during(MagicMock(), [2011, 2012]) is True


def test_reported_during_uses_inventory_coverage_when_available():
    from thermostat import stations

    station = MagicMock()
    station.id = "USI0000KSVE"

    with patch.object(stations, "get_station_coverage", return_value=0.0):
        assert stations._reported_during(station, [2011, 2014]) is False
    with patch.object(stations, "get_station_coverage", return_value=0.95):
        assert stations._reported_during(station, [2011, 2014]) is True


def test_spans_years_is_only_a_necessary_condition():
    """A span encloses the years; it does not mean data exists in them."""
    from thermostat import stations

    station = MagicMock()
    station.inventory_years = {"ghcnh": (1973, 2026)}
    assert stations._spans_years(station, [2011, 2014]) is True

    station.inventory_years = {"ghcnh": (1973, 1996)}
    assert stations._spans_years(station, [2011, 2014]) is False

    station.inventory_years = {}
    assert stations._spans_years(station, [2011, 2014]) is False


def test_usaf_id_skips_canadian_and_missing_ids():
    from thermostat import stations

    station = MagicMock()
    station.ids = {"usaf": ["722880"]}
    assert stations._usaf_id(station) == "722880"

    station.ids = {"usaf": ["A00001"]}
    assert stations._usaf_id(station) is None

    station.ids = {}
    assert stations._usaf_id(station) is None
