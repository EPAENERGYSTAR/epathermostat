import pandas as pd
import numpy as np

from numpy.testing import assert_allclose

import pytest

from fixtures.thermostats import thermostat_type_1
from fixtures.thermostats import core_heating_day_set_type_1_entire
from fixtures.thermostats import core_cooling_day_set_type_1_entire
from fixtures.thermostats import seasonal_metrics_type_1_data
from fixtures.thermostats import thermostat_template

from thermostat.core import CoreDaySet
from datetime import datetime

RTOL = 1e-3
ATOL = 1e-3

@pytest.fixture(params=[
    ("deltaT", "mean_demand_baseline_deltaT", None),
    ("dailyavgCTD", "mean_demand_baseline_dailyavgCTD", "tau_dailyavgCTD"),
    ("hourlyavgCTD", "mean_demand_baseline_hourlyavgCTD", "tau_hourlyavgCTD"),
    ])
def cooling_baseline_types(request):
    return request.param

@pytest.fixture(params=[
    ("deltaT", "mean_demand_baseline_deltaT", None),
    ("dailyavgHTD", "mean_demand_baseline_dailyavgHTD", "tau_dailyavgHTD"),
    ("hourlyavgHTD", "mean_demand_baseline_hourlyavgHTD", "tau_hourlyavgHTD"),
    ])
def heating_baseline_types(request):
    return request.param


@pytest.mark.slow
def test_get_core_cooling_day_baseline_setpoint(thermostat_type_1, core_cooling_day_set_type_1_entire, seasonal_metrics_type_1_data):

    baseline = thermostat_type_1.get_core_cooling_day_baseline_setpoint(core_cooling_day_set_type_1_entire)
    assert_allclose(baseline, seasonal_metrics_type_1_data[0]["baseline_comfort_temperature"], rtol=RTOL, atol=ATOL)

@pytest.mark.slow
def test_get_core_heating_day_baseline_setpoint(thermostat_type_1, core_heating_day_set_type_1_entire, seasonal_metrics_type_1_data):

    baseline = thermostat_type_1.get_core_heating_day_baseline_setpoint(core_heating_day_set_type_1_entire)
    assert_allclose(baseline, seasonal_metrics_type_1_data[1]["baseline_comfort_temperature"], rtol=RTOL, atol=ATOL)

def test_get_core_heating_day_baseline_setpoint_null_temperature_in(thermostat_template):

    index = pd.date_range(start=datetime(2011, 1, 1), periods=3, freq='D')
    thermostat_template.temperature_in = pd.Series([0, 1, 2], index=index)
    thermostat_template.equipment_type = 1

    season_selector = pd.Series([True, True, True], index=index)
    core_day_set = CoreDaySet("FAKE", season_selector, season_selector, None, None)

    sp = thermostat_template.get_core_heating_day_baseline_setpoint(
            core_day_set, source='heating_setpoint')
    assert pd.isnull(sp)

    sp = thermostat_template.get_core_heating_day_baseline_setpoint(
            core_day_set, source='temperature_in')
    assert_allclose(sp, 1.8)

    thermostat_template.temperature_in = pd.Series([np.nan, 1, 2], index=index)
    sp = thermostat_template.get_core_heating_day_baseline_setpoint(
            core_day_set, source='temperature_in')
    assert_allclose(sp, 1.9)

    thermostat_template.temperature_in = pd.Series([0, 1, np.nan], index=index)
    sp = thermostat_template.get_core_heating_day_baseline_setpoint(
            core_day_set, source='temperature_in')
    assert_allclose(sp, 0.9)

    thermostat_template.temperature_in = pd.Series([np.nan, np.nan, np.nan], index=index)
    sp = thermostat_template.get_core_heating_day_baseline_setpoint(
            core_day_set, source='temperature_in')
    assert pd.isnull(sp)

def test_get_core_cooling_day_baseline_setpoint_null_temperature_in(thermostat_template):

    index = pd.date_range(start=datetime(2011, 1, 1), periods=3, freq='D')
    thermostat_template.temperature_in = pd.Series([0, 1, 2], index=index)
    thermostat_template.equipment_type = 1

    season_selector = pd.Series([True, True, True], index=index)
    core_day_set = CoreDaySet("FAKE", season_selector, season_selector, None, None)

    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(
            core_day_set, source='cooling_setpoint')
    assert pd.isnull(sp)

    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(
            core_day_set, source='temperature_in')
    assert_allclose(sp, 0.2)

    thermostat_template.temperature_in = pd.Series([np.nan, 1, 2], index=index)
    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(
            core_day_set, source='temperature_in')
    assert_allclose(sp, 1.1)

    thermostat_template.temperature_in = pd.Series([0, 1, np.nan], index=index)
    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(
            core_day_set, source='temperature_in')
    assert_allclose(sp, 0.1)

    thermostat_template.temperature_in = pd.Series([np.nan, np.nan, np.nan], index=index)
    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(
            core_day_set, source='temperature_in')
    assert pd.isnull(sp)

def test_get_core_heating_day_baseline_setpoint_null_heating_setpoint(thermostat_template):

    index = pd.date_range(start=datetime(2011, 1, 1), periods=3, freq='D')
    thermostat_template.heating_setpoint = pd.Series([0, 1, 2], index=index)
    thermostat_template.equipment_type = 1

    season_selector = pd.Series([True, True, True], index=index)
    core_day_set = CoreDaySet("FAKE", season_selector, season_selector, None, None)

    sp = thermostat_template.get_core_heating_day_baseline_setpoint(
            core_day_set, source='temperature_in')
    assert pd.isnull(sp)

    sp = thermostat_template.get_core_heating_day_baseline_setpoint(
            core_day_set, source='heating_setpoint')
    assert_allclose(sp, 1.8)

    thermostat_template.heating_setpoint = pd.Series([np.nan, 1, 2], index=index)
    sp = thermostat_template.get_core_heating_day_baseline_setpoint(
            core_day_set, source='heating_setpoint')
    assert_allclose(sp, 1.9)

    thermostat_template.heating_setpoint = pd.Series([0, 1, np.nan], index=index)
    sp = thermostat_template.get_core_heating_day_baseline_setpoint(
            core_day_set, source='heating_setpoint')
    assert_allclose(sp, 0.9)

    thermostat_template.heating_setpoint = pd.Series([np.nan, np.nan, np.nan], index=index)
    sp = thermostat_template.get_core_heating_day_baseline_setpoint(
            core_day_set, source='heating_setpoint')
    assert pd.isnull(sp)

def test_get_core_cooling_day_baseline_setpoint_null_cooling_setpoint(thermostat_template):

    index = pd.date_range(start=datetime(2011, 1, 1), periods=3, freq='D')
    thermostat_template.cooling_setpoint = pd.Series([0, 1, 2], index=index)
    thermostat_template.equipment_type = 1

    season_selector = pd.Series([True, True, True], index=index)
    core_day_set = CoreDaySet("FAKE", season_selector, season_selector, None, None)

    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(
            core_day_set, source='temperature_in')
    assert pd.isnull(sp)

    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(
            core_day_set, source='cooling_setpoint')
    assert_allclose(sp, 0.2)

    thermostat_template.cooling_setpoint = pd.Series([np.nan, 1, 2], index=index)
    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(
            core_day_set, source='cooling_setpoint')
    assert_allclose(sp, 1.1)

    thermostat_template.cooling_setpoint = pd.Series([0, 1, np.nan], index=index)
    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(
            core_day_set, source='cooling_setpoint')
    assert_allclose(sp, 0.1)

    thermostat_template.cooling_setpoint = pd.Series([np.nan, np.nan, np.nan], index=index)
    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(
            core_day_set, source='cooling_setpoint')
    assert pd.isnull(sp)

@pytest.mark.slow
def test_get_core_cooling_day_baseline_deltaT(thermostat_type_1, core_cooling_day_set_type_1_entire, seasonal_metrics_type_1_data, cooling_baseline_types):

    demand_method, result_name, deltaT_base_name = cooling_baseline_types

    target = seasonal_metrics_type_1_data[0][result_name]

    if deltaT_base_name is None:
        deltaT_base = None
    else:
        deltaT_base = seasonal_metrics_type_1_data[0][deltaT_base_name]

    baseline = thermostat_type_1.get_baseline_cooling_demand(core_cooling_day_set_type_1_entire, deltaT_base, method=demand_method)

    assert_allclose(baseline.mean(), target, rtol=RTOL, atol=ATOL)

@pytest.mark.slow
def test_get_core_heating_day_baseline_deltaT(thermostat_type_1, core_heating_day_set_type_1_entire, seasonal_metrics_type_1_data, heating_baseline_types):

    demand_method, result_name, deltaT_base_name = heating_baseline_types

    if deltaT_base_name is None:
        deltaT_base = None
    else:
        deltaT_base = seasonal_metrics_type_1_data[1][deltaT_base_name]

    baseline = thermostat_type_1.get_baseline_heating_demand(core_heating_day_set_type_1_entire, deltaT_base,  method=demand_method)

    target = seasonal_metrics_type_1_data[1][result_name]

    assert_allclose(baseline.mean(), target, rtol=RTOL, atol=ATOL)
