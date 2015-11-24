from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path

import numpy as np
import pandas as pd

from datetime import datetime

import pytest

from fixtures.thermostats import thermostat_type_1
from fixtures.thermostats import thermostat_type_2
from fixtures.thermostats import thermostat_type_3
from fixtures.thermostats import thermostat_type_4
from fixtures.thermostats import thermostat_type_5
from fixtures.thermostats import heating_season_type_1
from fixtures.thermostats import heating_season_type_2
from fixtures.thermostats import heating_season_type_3
from fixtures.thermostats import heating_season_type_4
from fixtures.thermostats import cooling_season_type_1
from fixtures.thermostats import cooling_season_type_2
from fixtures.thermostats import cooling_season_type_3
from fixtures.thermostats import cooling_season_type_5

def test_thermostat_type_1_get_heating_seasons(thermostat_type_1):
    heating_seasons = thermostat_type_1.get_heating_seasons()
    assert len(heating_seasons) == 5

def test_thermostat_type_1_get_cooling_seasons(thermostat_type_1):
    cooling_seasons = thermostat_type_1.get_cooling_seasons()
    assert len(cooling_seasons) == 4

def test_thermostat_type_2_get_heating_seasons(thermostat_type_2):
    heating_seasons = thermostat_type_2.get_heating_seasons()
    assert len(heating_seasons) == 5

def test_thermostat_type_2_get_cooling_seasons(thermostat_type_2):
    cooling_seasons = thermostat_type_2.get_cooling_seasons()
    assert len(cooling_seasons) == 4

def test_thermostat_type_3_get_heating_seasons(thermostat_type_3):
    heating_seasons = thermostat_type_3.get_heating_seasons()
    assert len(heating_seasons) == 5

def test_thermostat_type_3_get_cooling_seasons(thermostat_type_3):
    cooling_seasons = thermostat_type_3.get_cooling_seasons()
    assert len(cooling_seasons) == 4

def test_thermostat_type_4_get_heating_seasons(thermostat_type_4):
    heating_seasons = thermostat_type_4.get_heating_seasons()
    assert len(heating_seasons) == 5

def test_thermostat_type_4_get_cooling_seasons(thermostat_type_4):
    with pytest.raises(ValueError):
        cooling_seasons = thermostat_type_4.get_cooling_seasons()

def test_thermostat_type_5_get_heating_seasons(thermostat_type_5):
    with pytest.raises(ValueError):
        heating_seasons = thermostat_type_5.get_heating_seasons()

def test_thermostat_type_5_get_cooling_seasons(thermostat_type_5):
    cooling_seasons = thermostat_type_5.get_cooling_seasons()
    assert len(cooling_seasons) == 4

def test_thermostat_type_1_get_heating_seasons_with_params(thermostat_type_1):
    heating_seasons = thermostat_type_1.get_heating_seasons(min_seconds_heating=0, max_seconds_cooling=0)
    assert len(heating_seasons) == 5

def test_thermostat_type_1_get_cooling_seasons_with_params(thermostat_type_1):
    heating_seasons = thermostat_type_1.get_cooling_seasons(min_seconds_cooling=0, max_seconds_heating=0)
    assert len(heating_seasons) == 4

def test_thermostat_heating_season_attributes(heating_season_type_1):

    assert isinstance(heating_season_type_1.name, str)
    assert isinstance(heating_season_type_1.daily, pd.Series)
    assert isinstance(heating_season_type_1.hourly, pd.Series)
    assert heating_season_type_1.daily.shape == (1461,)
    assert heating_season_type_1.hourly.shape == (35064,)
    assert isinstance(heating_season_type_1.start_date, datetime)
    assert isinstance(heating_season_type_1.end_date, datetime)

def test_thermostat_cooling_season_attributes(cooling_season_type_1):

    assert isinstance(cooling_season_type_1.name, str)
    assert isinstance(cooling_season_type_1.daily, pd.Series)
    assert isinstance(cooling_season_type_1.hourly, pd.Series)
    assert cooling_season_type_1.daily.shape == (1461,)
    assert cooling_season_type_1.hourly.shape == (35064,)
    assert isinstance(cooling_season_type_1.start_date, datetime)
    assert isinstance(cooling_season_type_1.end_date, datetime)

def test_thermostat_type_1_get_resistance_heat_utilization_bins(thermostat_type_1,
        heating_season_type_1):

    bins = thermostat_type_1.get_resistance_heat_utilization_bins(heating_season_type_1)
    assert len(bins) == 12

def test_thermostat_types_2_3_4_5_get_resistance_heat_utilization_bins(heating_season_type_1,
        thermostat_type_2, thermostat_type_3, thermostat_type_4, thermostat_type_5):

    for thermostat in [thermostat_type_2, thermostat_type_3, thermostat_type_4, thermostat_type_5]:
        with pytest.raises(ValueError):
            thermostat.get_resistance_heat_utilization_bins(heating_season_type_1)

def test_thermostat_type_1_get_heating_season_ignored_days(thermostat_type_1, heating_season_type_1):
    assert (21, 1) == thermostat_type_1.get_season_ignored_days(heating_season_type_1)

def test_thermostat_type_1_get_cooling_season_ignored_days(thermostat_type_1, cooling_season_type_1):
    assert (50, 3) == thermostat_type_1.get_season_ignored_days(cooling_season_type_1)

def test_thermostat_type_2_get_heating_season_ignored_days(thermostat_type_2, heating_season_type_2):
    assert (21, 0) == thermostat_type_2.get_season_ignored_days(heating_season_type_2)

def test_thermostat_type_2_get_cooling_season_ignored_days(thermostat_type_2, cooling_season_type_2):
    assert (50, 2) == thermostat_type_2.get_season_ignored_days(cooling_season_type_2)

def test_thermostat_type_3_get_heating_season_ignored_days(thermostat_type_3, heating_season_type_3):
    assert (32, 5) == thermostat_type_3.get_season_ignored_days(heating_season_type_3)

def test_thermostat_type_3_get_cooling_season_ignored_days(thermostat_type_3, cooling_season_type_3):
    assert (59, 10) == thermostat_type_3.get_season_ignored_days(cooling_season_type_3)

def test_thermostat_type_4_get_heating_season_ignored_days(thermostat_type_4, heating_season_type_4):
    assert (0, 1) == thermostat_type_4.get_season_ignored_days(heating_season_type_4)

def test_thermostat_type_5_get_cooling_season_ignored_days(thermostat_type_5, cooling_season_type_5):
    assert (0, 3) == thermostat_type_5.get_season_ignored_days(cooling_season_type_5)
