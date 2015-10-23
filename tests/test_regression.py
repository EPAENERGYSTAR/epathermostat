from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path
from thermostat.regression import runtime_regression

import pandas as pd
import numpy as np
from numpy.testing import assert_allclose

import pytest

RTOL = 1e-3
ATOL = 1e-3

from fixtures.thermostats import thermostat_type_1
from fixtures.thermostats import heating_season_type_1
from fixtures.thermostats import cooling_season_type_1
from fixtures.thermostats import heating_demand_deltaT_type_1
from fixtures.thermostats import cooling_demand_deltaT_type_1
from fixtures.thermostats import heating_daily_runtime_type_1
from fixtures.thermostats import cooling_daily_runtime_type_1
from fixtures.thermostats import heating_season_type_1_data
from fixtures.thermostats import cooling_season_type_1_data

@pytest.fixture(params=[
    (pd.Series([1,2,3,4,5,6]), pd.Series([2,4,6,8,10,12]), .5, 0),
    (pd.Series([2,4,10,8,6]), pd.Series([1,2,5,4,3]), 2, 0),
    (pd.Series([4,5,6,7]), pd.Series([1,2,3,4]), 2, 1.5),
    (pd.Series([4]), pd.Series([1]), 4, np.nan),
    (pd.Series([]), pd.Series([]), np.nan, np.nan),
    ])
def regression_fixture(request):
    return request.param

def test_runtime_regression_heating(heating_daily_runtime_type_1, heating_demand_deltaT_type_1, heating_season_type_1_data):
    slope, mean_sq_err = runtime_regression(heating_daily_runtime_type_1, heating_demand_deltaT_type_1)

    assert_allclose(slope, heating_season_type_1_data["regression_slope"], rtol=RTOL, atol=ATOL)
    assert_allclose(mean_sq_err, heating_season_type_1_data["regression_mean_sq_error"], rtol=RTOL, atol=ATOL)

def test_runtime_regression_cooling(cooling_daily_runtime_type_1, cooling_demand_deltaT_type_1, cooling_season_type_1_data):
    slope, mean_sq_err = runtime_regression(cooling_daily_runtime_type_1, cooling_demand_deltaT_type_1)

    assert_allclose(slope, cooling_season_type_1_data["regression_slope"], rtol=RTOL, atol=ATOL)
    assert_allclose(mean_sq_err, cooling_season_type_1_data["regression_mean_sq_error"], rtol=RTOL, atol=ATOL)

def test_runtime_regression_general(regression_fixture):
    daily_runtime, daily_demand, slope, mean_sq_err = regression_fixture
    slope_, mean_sq_err_ = runtime_regression(daily_runtime, daily_demand)

    assert_allclose(slope_, slope, rtol=RTOL, atol=ATOL)
    assert_allclose(mean_sq_err_, mean_sq_err, rtol=RTOL, atol=ATOL)
