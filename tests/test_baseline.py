from thermostat import Thermostat
from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path

import pandas as pd
import numpy as np

from numpy.testing import assert_allclose

import pytest

RTOL = 1e-3
ATOL = 1e-3

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
def heating_season(thermostat):
    return thermostat.get_heating_seasons()[0]

@pytest.fixture
def cooling_season(thermostat):
    return thermostat.get_cooling_seasons()[0]

@pytest.fixture
def heating_demand_deltaT(thermostat, heating_season):
    return thermostat.get_heating_demand(heating_season, method="deltaT")

@pytest.fixture
def cooling_demand_deltaT(thermostat, cooling_season):
    return thermostat.get_cooling_demand(cooling_season, method="deltaT")

def test_get_cooling_season_baseline_setpoint(thermostat, cooling_season):

    baseline = thermostat.get_cooling_season_baseline_setpoint(cooling_season)
    assert_allclose(baseline, 75.0, rtol=RTOL, atol=ATOL)

def test_get_heating_season_baseline_setpoint(thermostat, heating_season):

    baseline = thermostat.get_heating_season_baseline_setpoint(heating_season)
    assert_allclose(baseline, 66.0, rtol=RTOL, atol=ATOL)

def test_get_cooling_season_baseline_deltaT(thermostat, cooling_season):

    baseline = thermostat.get_baseline_cooling_demand(cooling_season, method="deltaT")

    assert_allclose(baseline.mean(), 2.889, rtol=1e-3, atol=1e-3)

def test_get_heating_season_baseline_deltaT(thermostat, heating_season):

    baseline = thermostat.get_baseline_heating_demand(heating_season, method="deltaT")

    assert_allclose(baseline.mean(), 8.915, rtol=1e-3, atol=1e-3)

def test_get_cooling_season_baseline_dailyavgCDD(thermostat, cooling_season):

    baseline = thermostat.get_baseline_cooling_demand(cooling_season, 0.243, method="dailyavgCDD")
    assert_allclose(baseline.mean(), 3.558, rtol=1e-3, atol=1e-3)

    baseline = thermostat.get_baseline_cooling_demand(cooling_season, 0, method="dailyavgCDD")
    assert_allclose(baseline.mean(), 3.371, rtol=1e-3, atol=1e-3)

def test_get_heating_season_baseline_dailyavgHDD(thermostat, heating_season):

    baseline = thermostat.get_baseline_heating_demand(heating_season, -0.001, method="dailyavgHDD")
    assert_allclose(baseline.mean(), 8.917, rtol=1e-3, atol=1e-3)

    baseline = thermostat.get_baseline_heating_demand(heating_season, 0, method="dailyavgHDD")
    assert_allclose(baseline.mean(), 8.916, rtol=1e-3, atol=1e-3)

def test_get_cooling_season_baseline_hourlysumCDD(thermostat, cooling_season):

    baseline = thermostat.get_baseline_cooling_demand(cooling_season, -0.770, method="hourlysumCDD")
    assert_allclose(baseline.mean(), 5.376, rtol=1e-3, atol=1e-3)

    baseline = thermostat.get_baseline_cooling_demand(cooling_season, 0, method="hourlysumCDD")
    assert_allclose(baseline.mean(), 5.78, rtol=1e-3, atol=1e-3)

def test_get_heating_season_baseline_hourlysumHDD(thermostat, heating_season):

    baseline = thermostat.get_baseline_heating_demand(heating_season, 0.428, method="hourlysumHDD")
    assert_allclose(baseline.mean(), 9.324, rtol=1e-3, atol=1e-3)

    baseline = thermostat.get_baseline_heating_demand(heating_season, 0, method="hourlysumHDD")
    assert_allclose(baseline.mean(), 9.680, rtol=1e-3, atol=1e-3)
