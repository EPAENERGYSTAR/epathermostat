from thermostat.core import Thermostat
from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path
from thermostat.regression import runtime_regression

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

def test_runtime_regression_heating(thermostat, heating_season, heating_demand_deltaT):
    daily_runtime = thermostat.heat_runtime[heating_season.daily].values
    slope, mean_sq_err = runtime_regression(daily_runtime, heating_demand_deltaT)

    assert_allclose(slope, 2400.482, rtol=RTOL, atol=ATOL)
    assert_allclose(mean_sq_err, 369356.647, rtol=RTOL, atol=ATOL)

def test_runtime_regression_cooling(thermostat, cooling_season, cooling_demand_deltaT):
    daily_runtime = thermostat.cool_runtime[cooling_season.daily].values
    slope, mean_sq_err = runtime_regression(daily_runtime, cooling_demand_deltaT)

    assert_allclose(slope, -2405.618, rtol=RTOL, atol=ATOL)
    assert_allclose(mean_sq_err, 1058435.360, rtol=RTOL, atol=ATOL)
