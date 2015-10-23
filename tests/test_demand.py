
import pandas as pd
import numpy as np
from numpy.testing import assert_allclose

import pytest

from fixtures.thermostats import thermostat_type_1
from fixtures.thermostats import heating_season_type_1
from fixtures.thermostats import cooling_season_type_1
from fixtures.thermostats import heating_season_type_1_data
from fixtures.thermostats import cooling_season_type_1_data

RTOL = 1e-3
ATOL = 1e-3

def test_get_cooling_demand_deltaT(thermostat_type_1, cooling_season_type_1, cooling_season_type_1_data):
    deltaT = thermostat_type_1.get_cooling_demand(cooling_season_type_1, method="deltaT")
    assert_allclose(deltaT.mean(), cooling_season_type_1_data["demand_deltaT_mean"], rtol=RTOL, atol=ATOL)

def test_get_heating_demand_deltaT(thermostat_type_1, heating_season_type_1, heating_season_type_1_data):
    deltaT = thermostat_type_1.get_heating_demand(heating_season_type_1, method="deltaT")
    assert_allclose(deltaT.mean(), heating_season_type_1_data["demand_deltaT_mean"], rtol=RTOL, atol=ATOL)


def test_get_cooling_demand_dailyavgCDD(thermostat_type_1, cooling_season_type_1, cooling_season_type_1_data):
    dailyavgCDD, deltaT_base_estimate, alpha_estimate, error = \
            thermostat_type_1.get_cooling_demand(cooling_season_type_1, method="dailyavgCDD")
    assert_allclose(dailyavgCDD.mean(), cooling_season_type_1_data["demand_dailyavgCDD_mean"], rtol=RTOL, atol=ATOL)
    assert_allclose(deltaT_base_estimate, cooling_season_type_1_data["demand_dailyavgCDD_base"], rtol=RTOL, atol=ATOL)
    assert_allclose(alpha_estimate, cooling_season_type_1_data["demand_dailyavgCDD_alpha"], rtol=RTOL, atol=ATOL)
    assert_allclose(error, cooling_season_type_1_data["demand_dailyavgCDD_error"], rtol=RTOL, atol=ATOL)

def test_get_heating_demand_dailyavgHDD(thermostat_type_1, heating_season_type_1, heating_season_type_1_data):
    dailyavgHDD, deltaT_base_estimate, alpha_estimate, error = \
            thermostat_type_1.get_heating_demand(heating_season_type_1, method="dailyavgHDD")
    assert_allclose(dailyavgHDD.mean(), heating_season_type_1_data["demand_dailyavgHDD_mean"], rtol=RTOL, atol=ATOL)
    assert_allclose(deltaT_base_estimate, heating_season_type_1_data["demand_dailyavgHDD_base"], rtol=RTOL, atol=ATOL)
    assert_allclose(alpha_estimate, heating_season_type_1_data["demand_dailyavgHDD_alpha"], rtol=RTOL, atol=ATOL)
    assert_allclose(error, heating_season_type_1_data["demand_dailyavgHDD_error"], rtol=RTOL, atol=ATOL)


def test_get_cooling_demand_hourlyavgCDD(thermostat_type_1, cooling_season_type_1, cooling_season_type_1_data):
    hourlyavgCDD, deltaT_base_estimate, alpha_estimate, error = \
            thermostat_type_1.get_cooling_demand(cooling_season_type_1, method="hourlyavgCDD")
    assert_allclose(hourlyavgCDD.mean(), cooling_season_type_1_data["demand_hourlyavgCDD_mean"], rtol=RTOL, atol=ATOL)
    assert_allclose(deltaT_base_estimate, cooling_season_type_1_data["demand_hourlyavgCDD_base"], rtol=RTOL, atol=ATOL)
    assert_allclose(alpha_estimate, cooling_season_type_1_data["demand_hourlyavgCDD_alpha"], rtol=RTOL, atol=ATOL)
    assert_allclose(error, cooling_season_type_1_data["demand_hourlyavgCDD_error"], rtol=RTOL, atol=ATOL)

def test_get_heating_demand_hourlyavgHDD(thermostat_type_1, heating_season_type_1, heating_season_type_1_data):
    hourlyavgHDD, deltaT_base_estimate, alpha_estimate, error = \
            thermostat_type_1.get_heating_demand(heating_season_type_1, method="hourlyavgHDD")
    assert_allclose(hourlyavgHDD.mean(), heating_season_type_1_data["demand_hourlyavgHDD_mean"], rtol=RTOL, atol=ATOL)
    assert_allclose(deltaT_base_estimate, heating_season_type_1_data["demand_hourlyavgHDD_base"], rtol=RTOL, atol=ATOL)
    assert_allclose(alpha_estimate, heating_season_type_1_data["demand_hourlyavgHDD_alpha"], rtol=RTOL, atol=ATOL)
    assert_allclose(error, heating_season_type_1_data["demand_hourlyavgHDD_error"], rtol=RTOL, atol=ATOL)
