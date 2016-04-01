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
    (pd.Series([1,2,3,4,5,6]), pd.Series([2,4,6,8,10,12]), .5, 0, 0),
    (pd.Series([2,4,10,8,6]), pd.Series([1,2,5,4,3]), 2, 0, 0),
    (pd.Series([4,5,6,7]), pd.Series([1,2,3,4]), 1, 3, 0),
    (pd.Series([4,5,6,np.nan]), pd.Series([1,2,3,4]), 1, 3, 0),
    (pd.Series([4,2,1]), pd.Series([1,2,1]), -0.50, 3.0, 1.50),
    (pd.Series([4,2,np.nan]), pd.Series([1,2,1]), -2.0, 6.0, 0),
    (pd.Series([4,2]), pd.Series([1,2]), -2.0, 6.0, 0.0),
    (pd.Series([4]), pd.Series([1]), np.nan, np.nan, np.nan),
    (pd.Series([]), pd.Series([]), np.nan, np.nan, np.nan),
    ])
def regression_fixture(request):
    return request.param

def test_runtime_regression(regression_fixture):
    daily_runtime, daily_demand, slope, intercept, mse = regression_fixture
    slope_, intercept_, mse_, rmse_, cvrmse_, mape_, mae_  = runtime_regression(daily_runtime, daily_demand)

    assert_allclose(slope_, slope, rtol=RTOL, atol=ATOL)
    assert_allclose(intercept_, intercept, rtol=RTOL, atol=ATOL)
    assert_allclose(mse_, mse, rtol=RTOL, atol=ATOL)
