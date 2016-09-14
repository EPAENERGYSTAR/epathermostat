import pandas as pd
import numpy as np
from numpy.testing import assert_allclose

import pytest

from fixtures.thermostats import thermostat_type_1
from fixtures.thermostats import core_heating_day_set_type_1_entire as core_heating_day_set_type_1
from fixtures.thermostats import core_cooling_day_set_type_1_entire as core_cooling_day_set_type_1
from fixtures.thermostats import core_heating_day_set_type_1_empty
from fixtures.thermostats import core_cooling_day_set_type_1_empty
from fixtures.thermostats import metrics_type_1_data

RTOL = 1e-3
ATOL = 1e-3

def test_get_cooling_demand_deltaT(thermostat_type_1, core_cooling_day_set_type_1, metrics_type_1_data):
    deltaT = thermostat_type_1.get_cooling_demand(core_cooling_day_set_type_1, method="deltaT")
    assert_allclose(deltaT.mean(), metrics_type_1_data[0]["mean_demand_deltaT_cooling"], rtol=RTOL, atol=ATOL)

def test_get_heating_demand_deltaT(thermostat_type_1, core_heating_day_set_type_1, metrics_type_1_data):
    deltaT = thermostat_type_1.get_heating_demand(core_heating_day_set_type_1, method="deltaT")
    assert_allclose(deltaT.mean(), metrics_type_1_data[1]["mean_demand_deltaT_heating"], rtol=RTOL, atol=ATOL)

def test_get_cooling_demand_dailyavgCTD(thermostat_type_1, core_cooling_day_set_type_1, metrics_type_1_data):
    dailyavgCTD, tau_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae = \
            thermostat_type_1.get_cooling_demand(core_cooling_day_set_type_1, method="dailyavgCTD")
    assert_allclose(dailyavgCTD.mean(), metrics_type_1_data[0]["mean_demand_dailyavgCTD"], rtol=RTOL, atol=ATOL)

def test_get_heating_demand_dailyavgHTD(thermostat_type_1, core_heating_day_set_type_1, metrics_type_1_data):
    dailyavgHTD, tau_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae = \
            thermostat_type_1.get_heating_demand(core_heating_day_set_type_1, method="dailyavgHTD")
    assert_allclose(dailyavgHTD.mean(), metrics_type_1_data[1]["mean_demand_dailyavgHTD"], rtol=RTOL, atol=ATOL)

def test_get_cooling_demand_dailyavgCTD_empty(thermostat_type_1, core_cooling_day_set_type_1_empty, metrics_type_1_data):
    dailyavgCTD, tau_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae = \
            thermostat_type_1.get_cooling_demand(core_cooling_day_set_type_1_empty, method="dailyavgCTD")

def test_get_cooling_demand_dailyavgHTD_empty(thermostat_type_1, core_heating_day_set_type_1_empty, metrics_type_1_data):
    dailyavgCTD, tau_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae = \
            thermostat_type_1.get_heating_demand(core_heating_day_set_type_1_empty, method="dailyavgHTD")


def test_get_cooling_demand_hourlyavgCTD(thermostat_type_1, core_cooling_day_set_type_1, metrics_type_1_data):
    hourlyavgCTD, tau_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae = \
            thermostat_type_1.get_cooling_demand(core_cooling_day_set_type_1, method="hourlyavgCTD")
    assert_allclose(hourlyavgCTD.mean(), metrics_type_1_data[0]["mean_demand_hourlyavgCTD"], rtol=RTOL, atol=ATOL)

def test_get_heating_demand_hourlyavgHTD(thermostat_type_1, core_heating_day_set_type_1, metrics_type_1_data):
    hourlyavgHTD, tau_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae = \
            thermostat_type_1.get_heating_demand(core_heating_day_set_type_1, method="hourlyavgHTD")
    assert_allclose(hourlyavgHTD.mean(), metrics_type_1_data[1]["mean_demand_hourlyavgHTD"], rtol=RTOL, atol=ATOL)
