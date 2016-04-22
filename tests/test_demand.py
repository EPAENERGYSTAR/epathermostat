
import pandas as pd
import numpy as np
from numpy.testing import assert_allclose

import pytest

from fixtures.thermostats import thermostat_type_1
from fixtures.thermostats import heating_season_type_1_entire as heating_season_type_1
from fixtures.thermostats import cooling_season_type_1_entire as cooling_season_type_1
from fixtures.thermostats import heating_season_type_1_empty
from fixtures.thermostats import cooling_season_type_1_empty
from fixtures.thermostats import seasonal_metrics_type_1_data

RTOL = 1e-3
ATOL = 1e-3

def test_get_cooling_demand_deltaT(thermostat_type_1, cooling_season_type_1, seasonal_metrics_type_1_data):
    deltaT = thermostat_type_1.get_cooling_demand(cooling_season_type_1, method="deltaT")
    assert_allclose(deltaT.mean(), seasonal_metrics_type_1_data[0]["mean_demand_deltaT"], rtol=RTOL, atol=ATOL)

def test_get_heating_demand_deltaT(thermostat_type_1, heating_season_type_1, seasonal_metrics_type_1_data):
    deltaT = thermostat_type_1.get_heating_demand(heating_season_type_1, method="deltaT")
    assert_allclose(deltaT.mean(), seasonal_metrics_type_1_data[1]["mean_demand_deltaT"], rtol=RTOL, atol=ATOL)

def test_get_cooling_demand_dailyavgCDD(thermostat_type_1, cooling_season_type_1, seasonal_metrics_type_1_data):
    dailyavgCDD, deltaT_base_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae = \
            thermostat_type_1.get_cooling_demand(cooling_season_type_1, method="dailyavgCDD")
    assert_allclose(dailyavgCDD.mean(), seasonal_metrics_type_1_data[0]["mean_demand_dailyavgCDD"], rtol=RTOL, atol=ATOL)

def test_get_heating_demand_dailyavgHDD(thermostat_type_1, heating_season_type_1, seasonal_metrics_type_1_data):
    dailyavgHDD, deltaT_base_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae = \
            thermostat_type_1.get_heating_demand(heating_season_type_1, method="dailyavgHDD")
    assert_allclose(dailyavgHDD.mean(), seasonal_metrics_type_1_data[1]["mean_demand_dailyavgHDD"], rtol=RTOL, atol=ATOL)

def test_get_cooling_demand_dailyavgCDD_empty(thermostat_type_1, cooling_season_type_1_empty, seasonal_metrics_type_1_data):
    dailyavgCDD, deltaT_base_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae = \
            thermostat_type_1.get_cooling_demand(cooling_season_type_1_empty, method="dailyavgCDD")

def test_get_cooling_demand_dailyavgHDD_empty(thermostat_type_1, heating_season_type_1_empty, seasonal_metrics_type_1_data):
    dailyavgCDD, deltaT_base_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae = \
            thermostat_type_1.get_heating_demand(heating_season_type_1_empty, method="dailyavgHDD")


def test_get_cooling_demand_hourlyavgCDD(thermostat_type_1, cooling_season_type_1, seasonal_metrics_type_1_data):
    hourlyavgCDD, deltaT_base_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae = \
            thermostat_type_1.get_cooling_demand(cooling_season_type_1, method="hourlyavgCDD")
    assert_allclose(hourlyavgCDD.mean(), seasonal_metrics_type_1_data[0]["mean_demand_hourlyavgCDD"], rtol=RTOL, atol=ATOL)

def test_get_heating_demand_hourlyavgHDD(thermostat_type_1, heating_season_type_1, seasonal_metrics_type_1_data):
    hourlyavgHDD, deltaT_base_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae = \
            thermostat_type_1.get_heating_demand(heating_season_type_1, method="hourlyavgHDD")
    assert_allclose(hourlyavgHDD.mean(), seasonal_metrics_type_1_data[1]["mean_demand_hourlyavgHDD"], rtol=RTOL, atol=ATOL)
