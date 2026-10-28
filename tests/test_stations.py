"""Tests for thermostat/stations.py — ZCTA->candidate-station selection.

Selection returns a short ranked list rather than one station: whether a
station has usable data is only knowable once it is loaded, so the importer
walks these in order. See test_importers.py for that half."""
import pandas as pd
from unittest.mock import patch, MagicMock

from eeweather.exceptions import UnrecognizedPlaceError

from thermostat.stations import (
    MAX_CANDIDATES_TRIED,
    get_candidate_stations_by_zipcode,
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
        result = get_candidate_stations_by_zipcode("91104", required_years=[2016, 2017])

    # nearest first, and every qualifying candidate is offered
    assert result == ["111111", "222222"]
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
        result = get_candidate_stations_by_zipcode("91104", required_years=[2016])

    assert result == ["222222"]


def test_skips_canadian_stations():
    location = MagicMock()
    location.candidates.return_value = _candidates(["S1", "S2"])
    stations = {"S1": _station("A00001"), "S2": _station("722222")}  # A = Canadian

    with patch("thermostat.stations.WeatherLocation") as WL, patch(
        "thermostat.stations.WeatherStation", side_effect=lambda sid: stations[sid]
    ):
        WL.from_place.return_value = location
        result = get_candidate_stations_by_zipcode("91104", required_years=[2020])

    assert result == ["722222"]


def test_unrecognized_zcta_yields_no_station():
    with patch("thermostat.stations.WeatherLocation") as WL:
        WL.from_place.side_effect = UnrecognizedPlaceError("zcta", "00000")
        result = get_candidate_stations_by_zipcode("00000", required_years=[2020])

    assert result == []


def test_no_qualifying_station_yields_no_station():
    location = MagicMock()
    location.candidates.return_value = _candidates(["S1"])
    stations = {"S1": _station("111111", inv=(2000, 2005))}  # too old

    with patch("thermostat.stations.WeatherLocation") as WL, patch(
        "thermostat.stations.WeatherStation", side_effect=lambda sid: stations[sid]
    ):
        WL.from_place.return_value = location
        result = get_candidate_stations_by_zipcode("91104", required_years=[2020])

    assert result == []


def test_offers_at_most_max_candidates_tried():
    """The walk is bounded: a fleet run against an unresponsive NOAA must not
    turn one site into an unbounded search."""
    location = MagicMock()
    location.candidates.return_value = _candidates(["S1", "S2", "S3", "S4", "S5"])
    stations = {sid: _station("11111%d" % i)
                for i, sid in enumerate(["S1", "S2", "S3", "S4", "S5"])}

    with patch("thermostat.stations.WeatherLocation") as WL, patch(
        "thermostat.stations.WeatherStation", side_effect=lambda sid: stations[sid]
    ):
        WL.from_place.return_value = location
        result = get_candidate_stations_by_zipcode("91104", required_years=[2020])

    assert len(result) == MAX_CANDIDATES_TRIED


def test_candidates_are_nearest_first():
    """Order is the contract -- the importer keeps the first that delivers,
    so a mis-ordered list silently picks a more distant station."""
    location = MagicMock()
    location.candidates.return_value = _candidates(["near", "mid", "far"])
    stations = {"near": _station("111111"), "mid": _station("222222"),
                "far": _station("333333")}

    with patch("thermostat.stations.WeatherLocation") as WL, patch(
        "thermostat.stations.WeatherStation", side_effect=lambda sid: stations[sid]
    ):
        WL.from_place.return_value = location
        result = get_candidate_stations_by_zipcode("91104", required_years=[2020])

    assert result == ["111111", "222222", "333333"]
