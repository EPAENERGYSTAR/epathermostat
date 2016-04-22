import pandas as pd
import numpy as np

from numpy.testing import assert_allclose

import pytest

from fixtures.thermostats import thermostat_type_1
from fixtures.thermostats import heating_season_type_1_entire
from fixtures.thermostats import cooling_season_type_1_entire
from fixtures.thermostats import seasonal_metrics_type_1_data

RTOL = 1e-3
ATOL = 1e-3

@pytest.fixture(params=[
    ("deltaT", "mean_demand_baseline_deltaT", None),
    ("dailyavgCDD", "mean_demand_baseline_dailyavgCDD", "deltaT_base_est_dailyavgCDD"),
    ("hourlyavgCDD", "mean_demand_baseline_hourlyavgCDD", "deltaT_base_est_hourlyavgCDD"),
    ])
def cooling_baseline_types(request):
    return request.param

@pytest.fixture(params=[
    ("deltaT", "mean_demand_baseline_deltaT", None),
    ("dailyavgHDD", "mean_demand_baseline_dailyavgHDD", "deltaT_base_est_dailyavgHDD"),
    ("hourlyavgHDD", "mean_demand_baseline_hourlyavgHDD", "deltaT_base_est_hourlyavgHDD"),
    ])
def heating_baseline_types(request):
    return request.param


def test_get_cooling_season_baseline_setpoint(thermostat_type_1, cooling_season_type_1_entire, seasonal_metrics_type_1_data):

    baseline = thermostat_type_1.get_cooling_season_baseline_setpoint(cooling_season_type_1_entire)
    assert_allclose(baseline, seasonal_metrics_type_1_data[0]["baseline_comfort_temperature"], rtol=RTOL, atol=ATOL)

def test_get_heating_season_baseline_setpoint(thermostat_type_1, heating_season_type_1_entire, seasonal_metrics_type_1_data):

    baseline = thermostat_type_1.get_heating_season_baseline_setpoint(heating_season_type_1_entire)
    assert_allclose(baseline, seasonal_metrics_type_1_data[1]["baseline_comfort_temperature"], rtol=RTOL, atol=ATOL)


def test_get_cooling_season_baseline_deltaT(thermostat_type_1, cooling_season_type_1_entire, seasonal_metrics_type_1_data, cooling_baseline_types):

    demand_method, result_name, deltaT_base_name = cooling_baseline_types

    target = seasonal_metrics_type_1_data[0][result_name]

    if deltaT_base_name is None:
        deltaT_base = None
    else:
        deltaT_base = seasonal_metrics_type_1_data[0][deltaT_base_name]

    baseline = thermostat_type_1.get_baseline_cooling_demand(cooling_season_type_1_entire, deltaT_base, method=demand_method)

    assert_allclose(baseline.mean(), target, rtol=RTOL, atol=ATOL)

def test_get_heating_season_baseline_deltaT(thermostat_type_1, heating_season_type_1_entire, seasonal_metrics_type_1_data, heating_baseline_types):

    demand_method, result_name, deltaT_base_name = heating_baseline_types

    if deltaT_base_name is None:
        deltaT_base = None
    else:
        deltaT_base = seasonal_metrics_type_1_data[1][deltaT_base_name]

    baseline = thermostat_type_1.get_baseline_heating_demand(heating_season_type_1_entire, deltaT_base,  method=demand_method)

    target = seasonal_metrics_type_1_data[1][result_name]

    assert_allclose(baseline.mean(), target, rtol=RTOL, atol=ATOL)
