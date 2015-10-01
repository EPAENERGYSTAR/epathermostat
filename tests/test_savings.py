from thermostat import Thermostat
from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path
from thermostat.savings import get_daily_avoided_runtime
from thermostat.savings import get_seasonal_percent_savings
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
def heating_baseline_setpoint(thermostat, heating_season):
    return thermostat.get_heating_season_baseline_setpoint(heating_season)

@pytest.fixture
def heating_demand_deltaT(thermostat, heating_season):
    return thermostat.get_heating_demand(heating_season, method="deltaT")

@pytest.fixture
def heating_regression_slope_deltaT(thermostat, heating_season,
        heating_demand_deltaT):
    daily_runtime = thermostat.heat_runtime[heating_season.daily]
    slope, _ = runtime_regression(daily_runtime, heating_demand_deltaT)
    return slope

@pytest.fixture
def baseline_heating_demand_deltaT(thermostat, heating_season,
        heating_baseline_setpoint):
    return thermostat.get_baseline_heating_demand(heating_season,
            heating_baseline_setpoint, method="deltaT")

@pytest.fixture
def daily_avoided_heating_runtime_deltaT(thermostat,
        heating_regression_slope_deltaT, heating_demand_deltaT,
        baseline_heating_demand_deltaT):
    return get_daily_avoided_runtime(heating_regression_slope_deltaT,
            heating_demand_deltaT, baseline_heating_demand_deltaT)

@pytest.fixture
def total_baseline_heating_runtime_deltaT(thermostat,
        heating_season, daily_avoided_heating_runtime_deltaT):
    return thermostat.get_total_baseline_heating_runtime(heating_season,
            daily_avoided_heating_runtime_deltaT)

@pytest.fixture
def cooling_season(thermostat):
    return thermostat.get_cooling_seasons()[0]

@pytest.fixture
def cooling_baseline_setpoint(thermostat, cooling_season):
    return thermostat.get_cooling_season_baseline_setpoint(cooling_season)

@pytest.fixture
def cooling_demand_deltaT(thermostat, cooling_season):
    return thermostat.get_cooling_demand(cooling_season, method="deltaT")

@pytest.fixture
def cooling_regression_slope_deltaT(thermostat, cooling_season,
        cooling_demand_deltaT):
    daily_runtime = thermostat.cool_runtime[cooling_season.daily]
    slope, _ = runtime_regression(daily_runtime, cooling_demand_deltaT)
    return slope

@pytest.fixture
def baseline_cooling_demand_deltaT(thermostat, cooling_season,
        cooling_baseline_setpoint):
    return thermostat.get_baseline_cooling_demand(cooling_season,
            cooling_baseline_setpoint, method="deltaT")

@pytest.fixture
def daily_avoided_cooling_runtime_deltaT(thermostat,
        cooling_regression_slope_deltaT, cooling_demand_deltaT,
        baseline_cooling_demand_deltaT):
    return get_daily_avoided_runtime(cooling_regression_slope_deltaT,
            -cooling_demand_deltaT, baseline_cooling_demand_deltaT)

@pytest.fixture
def total_baseline_cooling_runtime_deltaT(thermostat,
        cooling_season, daily_avoided_cooling_runtime_deltaT):
    return thermostat.get_total_baseline_cooling_runtime(cooling_season,
            daily_avoided_cooling_runtime_deltaT)

def test_get_daily_avoided_runtime_cooling_deltaT(
        cooling_regression_slope_deltaT, cooling_demand_deltaT,
        baseline_cooling_demand_deltaT):

    # note the sign change on cooling demand for delta T
    avoided_runtime = get_daily_avoided_runtime(
            cooling_regression_slope_deltaT, -cooling_demand_deltaT,
            baseline_cooling_demand_deltaT)

    assert_allclose(avoided_runtime.mean(), 3517.187, rtol=RTOL, atol=ATOL)

def test_get_daily_avoided_runtime_heating_deltaT(
        heating_regression_slope_deltaT, heating_demand_deltaT,
        baseline_heating_demand_deltaT):

    avoided_runtime = get_daily_avoided_runtime(
            heating_regression_slope_deltaT, heating_demand_deltaT,
            baseline_heating_demand_deltaT)

    assert_allclose(avoided_runtime.mean(), 2944.646, rtol=RTOL, atol=ATOL)

def test_get_total_baseline_cooling_runtime(thermostat, cooling_season,
        daily_avoided_cooling_runtime_deltaT):
    total_baseline = thermostat.get_total_baseline_cooling_runtime(
            cooling_season, daily_avoided_cooling_runtime_deltaT)

    assert_allclose(total_baseline, 283281.489, rtol=RTOL, atol=ATOL)

def test_get_total_baseline_heating_runtime(thermostat, heating_season,
        daily_avoided_heating_runtime_deltaT):
    total_baseline = thermostat.get_total_baseline_heating_runtime(
            heating_season, daily_avoided_heating_runtime_deltaT)

    assert_allclose(total_baseline, 2171855.459, rtol=RTOL, atol=ATOL)

def test_get_seasonal_percent_savings_cooling(total_baseline_cooling_runtime_deltaT,
        daily_avoided_cooling_runtime_deltaT):
    savings = get_seasonal_percent_savings(
            total_baseline_cooling_runtime_deltaT,
            daily_avoided_cooling_runtime_deltaT)
    assert_allclose(savings, 0.496, rtol=RTOL, atol=ATOL)

def test_get_seasonal_percent_savings_heating(total_baseline_heating_runtime_deltaT,
        daily_avoided_heating_runtime_deltaT):
    savings = get_seasonal_percent_savings(
            total_baseline_heating_runtime_deltaT,
            daily_avoided_heating_runtime_deltaT)
    assert_allclose(savings, 0.189, rtol=RTOL, atol=ATOL)
