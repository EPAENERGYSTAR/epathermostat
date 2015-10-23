from thermostat.savings import get_daily_avoided_runtime
from thermostat.savings import get_seasonal_percent_savings

import numpy as np

from numpy.testing import assert_allclose

import pytest

from fixtures.thermostats import thermostat_type_1
from fixtures.thermostats import heating_season_type_1
from fixtures.thermostats import cooling_season_type_1
from fixtures.thermostats import heating_demand_deltaT_type_1
from fixtures.thermostats import cooling_demand_deltaT_type_1
from fixtures.thermostats import baseline_heating_demand_deltaT_type_1
from fixtures.thermostats import baseline_cooling_demand_deltaT_type_1
from fixtures.thermostats import daily_avoided_heating_runtime_deltaT_type_1
from fixtures.thermostats import daily_avoided_cooling_runtime_deltaT_type_1

from fixtures.thermostats import heating_season_type_1_data
from fixtures.thermostats import cooling_season_type_1_data

RTOL = 1e-3
ATOL = 1e-3

@pytest.fixture(params=[
    (10, 1, np.tile(10,(3,)), np.tile(0,(3,))),
    ])
def avoided_runtime_fixture(request):
    return request.param

@pytest.fixture(params=[
    (.2, 100, np.tile(1, (20,))),
    (.2, 100, np.concatenate((np.tile(2, (10,)), np.tile(np.nan,(10,))))),
    ])
def seasonal_percent_savings_fixture(request):
    return request.param

def test_get_daily_avoided_runtime(avoided_runtime_fixture):
    avoided_runtime_mean, alpha, demand_baseline, demand = avoided_runtime_fixture
    avoided_runtime = get_daily_avoided_runtime(alpha, demand, demand_baseline)
    assert_allclose(avoided_runtime.mean(), avoided_runtime_mean, rtol=RTOL, atol=ATOL)

def test_get_seasonal_percent_savings(seasonal_percent_savings_fixture):
    percent_savings, baseline, avoided = seasonal_percent_savings_fixture
    savings = get_seasonal_percent_savings(baseline, avoided)
    assert_allclose(savings, percent_savings, rtol=RTOL, atol=ATOL)

def test_get_total_baseline_cooling_runtime(thermostat_type_1, cooling_season_type_1,
        daily_avoided_cooling_runtime_deltaT_type_1, cooling_season_type_1_data):

    total_baseline = thermostat_type_1.get_total_baseline_cooling_runtime(
            cooling_season_type_1, daily_avoided_cooling_runtime_deltaT_type_1)

    assert_allclose(total_baseline, cooling_season_type_1_data["total_baseline"], rtol=RTOL, atol=ATOL)

def test_get_total_baseline_heating_runtime(thermostat_type_1, heating_season_type_1,
        daily_avoided_heating_runtime_deltaT_type_1, heating_season_type_1_data):

    total_baseline = thermostat_type_1.get_total_baseline_heating_runtime(
            heating_season_type_1, daily_avoided_heating_runtime_deltaT_type_1)

    assert_allclose(total_baseline, heating_season_type_1_data["total_baseline"], rtol=RTOL, atol=ATOL)
