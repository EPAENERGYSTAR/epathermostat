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

def test_runtime_regression_heating(heating_daily_runtime_type_1, heating_demand_deltaT_type_1, heating_season_type_1_data):
    slope, mean_sq_err = runtime_regression(heating_daily_runtime_type_1, heating_demand_deltaT_type_1)

    assert_allclose(slope, heating_season_type_1_data["regression_slope"], rtol=RTOL, atol=ATOL)
    assert_allclose(mean_sq_err, heating_season_type_1_data["regression_mean_sq_error"], rtol=RTOL, atol=ATOL)

def test_runtime_regression_cooling(cooling_daily_runtime_type_1, cooling_demand_deltaT_type_1, cooling_season_type_1_data):
    slope, mean_sq_err = runtime_regression(cooling_daily_runtime_type_1, cooling_demand_deltaT_type_1)

    assert_allclose(slope, cooling_season_type_1_data["regression_slope"], rtol=RTOL, atol=ATOL)
    assert_allclose(mean_sq_err, cooling_season_type_1_data["regression_mean_sq_error"], rtol=RTOL, atol=ATOL)
