from thermostat.core import Thermostat
from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path

import numpy as np
import pandas as pd

import pytest

@pytest.fixture(params=["metadata.csv"])
def metadata_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["interval_data.csv"])
def interval_data_filename(request):
    return get_data_path(request.param)

@pytest.fixture
def thermostat(metadata_filename, interval_data_filename):
    thermostats = from_csv(metadata_filename, interval_data_filename)
    return thermostats[0]

@pytest.fixture
def thermostat_heating_seasons(thermostat):
    return thermostat.get_heating_seasons()

@pytest.fixture
def thermostat_cooling_seasons(thermostat):
    return thermostat.get_cooling_seasons()

def test_thermostat_get_heating_seasons(thermostat):
    heating_seasons = thermostat.get_heating_seasons()
    assert len(heating_seasons) == 5

def test_thermostat_get_cooling_seasons(thermostat):
    cooling_seasons = thermostat.get_cooling_seasons()
    assert len(cooling_seasons) == 4

def test_thermostat_season_attributes(thermostat_heating_seasons, thermostat_cooling_seasons):

    for season in thermostat_heating_seasons:
        assert isinstance(season.name, str)
        assert isinstance(season.daily, pd.Series)
        assert isinstance(season.hourly, pd.Series)
        assert season.daily.shape == (1461,)
        assert season.hourly.shape == (35064,)
        assert isinstance(season.start_date, np.datetime64)
        assert isinstance(season.end_date, np.datetime64)

    for season in thermostat_cooling_seasons:
        assert isinstance(season.name, str)
        assert isinstance(season.daily, pd.Series)
        assert isinstance(season.hourly, pd.Series)
        assert season.daily.shape == (1461,)
        assert season.hourly.shape == (35064,)
        assert isinstance(season.start_date, np.datetime64)
        assert isinstance(season.end_date, np.datetime64)

def test_thermostat_get_resistance_heat_utilization_bins(thermostat,
        thermostat_heating_seasons):

    for season in thermostat_heating_seasons:
        bins = thermostat.get_resistance_heat_utilization_bins(season)
        assert len(bins) == 12

def test_thermostat_get_season_ignored_days(thermostat, thermostat_heating_seasons):

    for season in thermostat_heating_seasons:
        days_both, days_missing = thermostat.get_season_ignored_days(season)
        assert days_both > 0
        assert days_missing > 0
