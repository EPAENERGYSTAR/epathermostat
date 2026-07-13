"""Tests for thermostat/stations.py — both-year cache filter and fallback logic."""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from eeweather.exceptions import UnrecognizedZCTAError

from thermostat.stations import (
    _get_both_year_station,
    get_closest_station_by_zipcode,
    lookup_usaf_station_by_zipcode,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ranking(entries):
    """Build a minimal rank_stations-style DataFrame.

    entries: list of (usaf_id, distance_m) tuples, in order.
    """
    rows = []
    for usaf, dist in entries:
        rows.append({
            'distance_meters': float(dist),
            'rough_quality': 'high',
            'enumerated_quality': 0,
            'latitude': 40.0,
            'longitude': -90.0,
            'elevation': 100.0,
            'iecc_climate_zone': '5A',
            'iecc_moisture_regime': 'A',
            'ba_climate_zone': '5A',
            'ca_climate_zone': None,
            'rank': idx + 1,
            'is_tmy3': False,
            'is_cz2010': False,
            'difference_elevation_meters': 0.0,
            'state': 'IL',
            'tmy3_class': None,
        } for idx, (usaf, dist) in enumerate(entries) if True)
        break
    # Build properly indexed DataFrame
    data = {
        'distance_meters': [float(d) for _, d in entries],
        'rough_quality': ['high'] * len(entries),
        'enumerated_quality': [0] * len(entries),
    }
    index = pd.Index([u for u, _ in entries], name='usaf_id')
    return pd.DataFrame(data, index=index)


# ---------------------------------------------------------------------------
# Tests for _get_both_year_station
# ---------------------------------------------------------------------------

def test_both_year_station_returns_first_qualifying():
    """Should skip rank-1 (no 2025 data) and return rank-2 (both years)."""
    ranking = _make_ranking([
        ('725300', 10_000),   # rank 1: no 2025 data
        ('725340', 25_000),   # rank 2: both years
    ])

    def fake_key_exists(key):
        if '725300' in key and '2025' in key:
            return False
        return True  # 725300-2026 and 725340-both exist

    with patch('thermostat.stations._rank_stations_by_distance_and_quality', return_value=ranking):
        with patch('eeweather.connections.key_value_store_proxy') as mock_proxy:
            mock_store = MagicMock()
            mock_store.key_exists.side_effect = fake_key_exists
            mock_proxy.get_store.return_value = mock_store

            result = _get_both_year_station(40.0, -90.0)

    assert result == '725340'


def test_both_year_station_returns_none_beyond_distance_cap():
    """No station within 500 km with both years → return None."""
    ranking = _make_ranking([
        ('725300', 600_000),  # 600 km — beyond cap
    ])

    with patch('thermostat.stations._rank_stations_by_distance_and_quality', return_value=ranking):
        with patch('eeweather.connections.key_value_store_proxy') as mock_proxy:
            mock_store = MagicMock()
            mock_store.key_exists.return_value = True  # has both years, but too far
            mock_proxy.get_store.return_value = mock_store

            result = _get_both_year_station(40.0, -90.0)

    assert result is None


def test_both_year_station_skips_canadian_stations():
    """Stations with USAF IDs starting with 'A' are skipped."""
    ranking = _make_ranking([
        ('A00001', 5_000),   # Canadian — should be skipped
        ('725300', 20_000),  # US — should be accepted
    ])

    with patch('thermostat.stations._rank_stations_by_distance_and_quality', return_value=ranking):
        with patch('eeweather.connections.key_value_store_proxy') as mock_proxy:
            mock_store = MagicMock()
            mock_store.key_exists.return_value = True
            mock_proxy.get_store.return_value = mock_store

            result = _get_both_year_station(49.0, -100.0)

    assert result == '725300'


def test_both_year_station_defaults_to_current_window():
    """With no required_years, the filter checks [today.year-1, today.year]."""
    from datetime import date
    ranking = _make_ranking([('725300', 10_000)])
    years_checked = []

    def fake_key_exists(key):
        years_checked.append(key.rsplit('-', 1)[-1])
        return True

    with patch('thermostat.stations._rank_stations_by_distance_and_quality', return_value=ranking):
        with patch('eeweather.connections.key_value_store_proxy') as mock_proxy:
            mock_store = MagicMock()
            mock_store.key_exists.side_effect = fake_key_exists
            mock_proxy.get_store.return_value = mock_store

            _get_both_year_station(40.0, -90.0)

    y = date.today().year
    assert set(years_checked) == {str(y - 1), str(y)}


def test_both_year_station_honors_requested_years():
    """A historical run can request specific years; the filter checks exactly
    those years, not the current calendar year."""
    ranking = _make_ranking([('725300', 10_000)])
    years_checked = []

    def fake_key_exists(key):
        years_checked.append(key.rsplit('-', 1)[-1])
        return True

    with patch('thermostat.stations._rank_stations_by_distance_and_quality', return_value=ranking):
        with patch('eeweather.connections.key_value_store_proxy') as mock_proxy:
            mock_store = MagicMock()
            mock_store.key_exists.side_effect = fake_key_exists
            mock_proxy.get_store.return_value = mock_store

            result = _get_both_year_station(40.0, -90.0, required_years=[2015, 2016])

    assert result == '725300'
    assert set(years_checked) == {'2015', '2016'}


# ---------------------------------------------------------------------------
# Tests for get_closest_station_by_zipcode
# ---------------------------------------------------------------------------

def test_unrecognized_zcta_falls_back_to_json():
    """UnrecognizedZCTAError must use the JSON map, not return None."""
    with patch('thermostat.stations.zcta_to_lat_long', side_effect=UnrecognizedZCTAError('00000')):
        with patch('thermostat.stations.lookup_usaf_station_by_zipcode', return_value='999999') as mock_json:
            result = get_closest_station_by_zipcode('00000')

    mock_json.assert_called_once_with('00000')
    assert result == '999999'


def test_no_both_year_station_falls_back_to_json():
    """If _get_both_year_station returns None, fall back to JSON."""
    with patch('thermostat.stations.zcta_to_lat_long', return_value=(40.0, -90.0)):
        with patch('thermostat.stations._get_both_year_station', return_value=None):
            with patch('thermostat.stations.lookup_usaf_station_by_zipcode', return_value='725300') as mock_json:
                result = get_closest_station_by_zipcode('60601')

    mock_json.assert_called_once_with('60601')
    assert result == '725300'


def test_both_year_station_returned_without_json_fallback():
    """When a both-year station is found, return it directly — no JSON lookup."""
    with patch('thermostat.stations.zcta_to_lat_long', return_value=(40.0, -90.0)):
        with patch('thermostat.stations._get_both_year_station', return_value='725300'):
            with patch('thermostat.stations.lookup_usaf_station_by_zipcode') as mock_json:
                result = get_closest_station_by_zipcode('60601')

    mock_json.assert_not_called()
    assert result == '725300'


def test_get_closest_station_forwards_required_years():
    """required_years is passed through to the both-year filter (historical run)."""
    with patch('thermostat.stations.zcta_to_lat_long', return_value=(40.0, -90.0)):
        with patch('thermostat.stations._get_both_year_station', return_value='725300') as mock_filter:
            result = get_closest_station_by_zipcode('60601', required_years=[2015, 2016])

    assert result == '725300'
    _, kwargs = mock_filter.call_args
    assert kwargs.get('required_years') == [2015, 2016]


def test_get_closest_station_defaults_required_years_to_none():
    """Default call forwards required_years=None so the filter uses today's window."""
    with patch('thermostat.stations.zcta_to_lat_long', return_value=(40.0, -90.0)):
        with patch('thermostat.stations._get_both_year_station', return_value='725300') as mock_filter:
            get_closest_station_by_zipcode('60601')

    _, kwargs = mock_filter.call_args
    assert kwargs.get('required_years') is None
