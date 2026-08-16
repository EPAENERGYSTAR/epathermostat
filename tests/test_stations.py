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
