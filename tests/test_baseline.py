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

def test_get_cooling_season_baseline_setpoint(thermostat_type_1, cooling_season_type_1, cooling_season_type_1_data):

    baseline = thermostat_type_1.get_cooling_season_baseline_setpoint(cooling_season_type_1)
    assert_allclose(baseline, cooling_season_type_1_data["baseline_setpoint"], rtol=RTOL, atol=ATOL)

def test_get_heating_season_baseline_setpoint(thermostat_type_1, heating_season_type_1, heating_season_type_1_data):

    baseline = thermostat_type_1.get_heating_season_baseline_setpoint(heating_season_type_1)
    assert_allclose(baseline, heating_season_type_1_data["baseline_setpoint"], rtol=RTOL, atol=ATOL)

def test_get_cooling_season_baseline_deltaT(thermostat_type_1, cooling_season_type_1, cooling_season_type_1_data):

    baseline = thermostat_type_1.get_baseline_cooling_demand(cooling_season_type_1, method="deltaT")

    assert_allclose(baseline.mean(), cooling_season_type_1_data["baseline_demand_deltaT_mean"], rtol=RTOL, atol=ATOL)

def test_get_heating_season_baseline_deltaT(thermostat_type_1, heating_season_type_1, heating_season_type_1_data):

    baseline = thermostat_type_1.get_baseline_heating_demand(heating_season_type_1, method="deltaT")

    assert_allclose(baseline.mean(), heating_season_type_1_data["baseline_demand_deltaT_mean"], rtol=RTOL, atol=ATOL)

def test_get_cooling_season_baseline_dailyavgCDD(thermostat_type_1, cooling_season_type_1, cooling_season_type_1_data):

    baseline = thermostat_type_1.get_baseline_cooling_demand(cooling_season_type_1, 0, method="dailyavgCDD")
    assert_allclose(baseline.mean(), cooling_season_type_1_data["baseline_demand_dailyavgCDD_mean"], rtol=RTOL, atol=ATOL)

def test_get_heating_season_baseline_dailyavgHDD(thermostat_type_1, heating_season_type_1, heating_season_type_1_data):

    baseline = thermostat_type_1.get_baseline_heating_demand(heating_season_type_1, 0, method="dailyavgHDD")
    assert_allclose(baseline.mean(), heating_season_type_1_data["baseline_demand_dailyavgHDD_mean"], rtol=RTOL, atol=ATOL)

def test_get_cooling_season_baseline_hourlyavgCDD(thermostat_type_1, cooling_season_type_1, cooling_season_type_1_data):

    baseline = thermostat_type_1.get_baseline_cooling_demand(cooling_season_type_1, 0, method="hourlyavgCDD")
    assert_allclose(baseline.mean(), cooling_season_type_1_data["baseline_demand_hourlyavgCDD_mean"], rtol=RTOL, atol=ATOL)

def test_get_heating_season_baseline_hourlyavgHDD(thermostat_type_1, heating_season_type_1, heating_season_type_1_data):

    baseline = thermostat_type_1.get_baseline_heating_demand(heating_season_type_1, 0, method="hourlyavgHDD")
    assert_allclose(baseline.mean(), heating_season_type_1_data["baseline_demand_hourlyavgHDD_mean"], rtol=RTOL, atol=ATOL)
