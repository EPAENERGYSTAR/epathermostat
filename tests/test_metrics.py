from thermostat.exporters import metrics_to_csv

import pandas as pd
import numpy as np
from numpy.testing import assert_allclose

import tempfile

import pytest

from fixtures.thermostats import thermostat_type_1
from fixtures.thermostats import thermostat_type_2
from fixtures.thermostats import thermostat_type_3
from fixtures.thermostats import thermostat_type_4
from fixtures.thermostats import thermostat_type_5
from fixtures.thermostats import metrics_type_1_data
import six

@pytest.fixture(scope="session")
def metrics_type_1(thermostat_type_1):
    metrics_type_1 = thermostat_type_1.calculate_epa_field_savings_metrics()
    return metrics_type_1

RTOL = 1e-3
ATOL = 1e-3

def test_calculate_epa_field_savings_metrics_type_1(metrics_type_1, metrics_type_1_data):
    assert len(metrics_type_1) == len(metrics_type_1_data)

    for key in metrics_type_1[0].keys():
        test_value = metrics_type_1[0][key]
        target_value = metrics_type_1_data[0][key]
        if isinstance(test_value, six.string_types):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

    for key in metrics_type_1[1].keys():
        test_value = metrics_type_1[1][key]
        target_value = metrics_type_1_data[1][key]
        if isinstance(test_value, six.string_types):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

def test_calculate_epa_field_savings_metrics_type_2(thermostat_type_2):
    metrics_type_2_entire = thermostat_type_2.calculate_epa_field_savings_metrics()
    assert len(metrics_type_2_entire) == 2

    metrics_type_2_yearly = thermostat_type_2.calculate_epa_field_savings_metrics(
            core_cooling_day_set_method="year_end_to_end",
            core_heating_day_set_method="year_mid_to_mid")
    assert len(metrics_type_2_yearly) == 9

def test_calculate_epa_field_savings_metrics_type_3(thermostat_type_3):
    metrics_type_3 = thermostat_type_3.calculate_epa_field_savings_metrics()
    assert len(metrics_type_3) == 2

def test_calculate_epa_field_savings_metrics_type_4(thermostat_type_4):
    metrics_type_4 = thermostat_type_4.calculate_epa_field_savings_metrics()
    assert len(metrics_type_4) == 1

def test_calculate_epa_field_savings_metrics_type_5(thermostat_type_5):
    metrics_type_5 = thermostat_type_5.calculate_epa_field_savings_metrics()
    assert len(metrics_type_5) == 1

def test_metrics_to_csv(metrics_type_1):

    fd, fname = tempfile.mkstemp()
    df = metrics_to_csv(metrics_type_1, fname)

    assert isinstance(df, pd.DataFrame)
    assert df.columns[0] == "sw_version"
    assert df.columns[1] == "ct_identifier"

    with open(fname,'r') as f:
        lines = f.readlines()
        assert len(lines) == 3
        column_heads = lines[0].strip().split(',')
        assert column_heads == [
            'sw_version',

            'ct_identifier',
            'equipment_type',
            'heating_or_cooling',
            'zipcode',
            'station',
            'climate_zone',

            'start_date',
            'end_date',
            'n_days_in_inputfile_date_range',
            'n_days_both_heating_and_cooling',
            'n_days_insufficient_data',
            'n_core_cooling_days',
            'n_core_heating_days',

            'baseline10_core_cooling_comfort_temperature',
            'baseline90_core_heating_comfort_temperature',
            'regional_average_baseline_cooling_comfort_temperature',
            'regional_average_baseline_heating_comfort_temperature',

            'percent_savings_deltaT_cooling_baseline10',
            'avoided_daily_mean_core_day_runtime_deltaT_cooling_baseline10',
            'avoided_total_core_day_runtime_deltaT_cooling_baseline10',
            'baseline_daily_mean_core_day_runtime_deltaT_cooling_baseline10',
            'baseline_total_core_day_runtime_deltaT_cooling_baseline10',
            '_daily_mean_core_day_demand_baseline_deltaT_cooling_baseline10',
            'percent_savings_deltaT_cooling_baseline_regional',
            'avoided_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional',
            'avoided_total_core_day_runtime_deltaT_cooling_baseline_regional',
            'baseline_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional',
            'baseline_total_core_day_runtime_deltaT_cooling_baseline_regional',
            '_daily_mean_core_day_demand_baseline_deltaT_cooling_baseline_regional',
            'mean_demand_deltaT_cooling',
            'alpha_deltaT_cooling',
            'tau_deltaT_cooling',
            'mean_sq_err_deltaT_cooling',
            'root_mean_sq_err_deltaT_cooling',
            'cv_root_mean_sq_err_deltaT_cooling',
            'mean_abs_err_deltaT_cooling',
            'mean_abs_pct_err_deltaT_cooling',

            'percent_savings_dailyavgCTD_baseline10',
            'avoided_daily_mean_core_day_runtime_dailyavgCTD_baseline10',
            'avoided_total_core_day_runtime_dailyavgCTD_baseline10',
            'baseline_daily_mean_core_day_runtime_dailyavgCTD_baseline10',
            'baseline_total_core_day_runtime_dailyavgCTD_baseline10',
            '_daily_mean_core_day_demand_baseline_dailyavgCTD_baseline10',
            'percent_savings_dailyavgCTD_baseline_regional',
            'avoided_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional',
            'avoided_total_core_day_runtime_dailyavgCTD_baseline_regional',
            'baseline_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional',
            'baseline_total_core_day_runtime_dailyavgCTD_baseline_regional',
            '_daily_mean_core_day_demand_baseline_dailyavgCTD_baseline_regional',
            'mean_demand_dailyavgCTD',
            'alpha_dailyavgCTD',
            'tau_dailyavgCTD',
            'mean_sq_err_dailyavgCTD',
            'root_mean_sq_err_dailyavgCTD',
            'cv_root_mean_sq_err_dailyavgCTD',
            'mean_abs_err_dailyavgCTD',
            'mean_abs_pct_err_dailyavgCTD',

            'percent_savings_hourlyavgCTD_baseline10',
            'avoided_daily_mean_core_day_runtime_hourlyavgCTD_baseline10',
            'avoided_total_core_day_runtime_hourlyavgCTD_baseline10',
            'baseline_daily_mean_core_day_runtime_hourlyavgCTD_baseline10',
            'baseline_total_core_day_runtime_hourlyavgCTD_baseline10',
            '_daily_mean_core_day_demand_baseline_hourlyavgCTD_baseline10',
            'percent_savings_hourlyavgCTD_baseline_regional',
            'avoided_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional',
            'avoided_total_core_day_runtime_hourlyavgCTD_baseline_regional',
            'baseline_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional',
            'baseline_total_core_day_runtime_hourlyavgCTD_baseline_regional',
            '_daily_mean_core_day_demand_baseline_hourlyavgCTD_baseline_regional',
            'mean_demand_hourlyavgCTD',
            'alpha_hourlyavgCTD',
            'tau_hourlyavgCTD',
            'mean_sq_err_hourlyavgCTD',
            'root_mean_sq_err_hourlyavgCTD',
            'cv_root_mean_sq_err_hourlyavgCTD',
            'mean_abs_err_hourlyavgCTD',
            'mean_abs_pct_err_hourlyavgCTD',

            'percent_savings_deltaT_heating_baseline90',
            'avoided_daily_mean_core_day_runtime_deltaT_heating_baseline90',
            'avoided_total_core_day_runtime_deltaT_heating_baseline90',
            'baseline_daily_mean_core_day_runtime_deltaT_heating_baseline90',
            'baseline_total_core_day_runtime_deltaT_heating_baseline90',
            '_daily_mean_core_day_demand_baseline_deltaT_heating_baseline90',
            'percent_savings_deltaT_heating_baseline_regional',
            'avoided_daily_mean_core_day_runtime_deltaT_heating_baseline_regional',
            'avoided_total_core_day_runtime_deltaT_heating_baseline_regional',
            'baseline_daily_mean_core_day_runtime_deltaT_heating_baseline_regional',
            'baseline_total_core_day_runtime_deltaT_heating_baseline_regional',
            '_daily_mean_core_day_demand_baseline_deltaT_heating_baseline_regional',
            'mean_demand_deltaT_heating',
            'alpha_deltaT_heating',
            'tau_deltaT_heating',
            'mean_sq_err_deltaT_heating',
            'root_mean_sq_err_deltaT_heating',
            'cv_root_mean_sq_err_deltaT_heating',
            'mean_abs_err_deltaT_heating',
            'mean_abs_pct_err_deltaT_heating',

            'percent_savings_dailyavgHTD_baseline90',
            'avoided_daily_mean_core_day_runtime_dailyavgHTD_baseline90',
            'avoided_total_core_day_runtime_dailyavgHTD_baseline90',
            'baseline_daily_mean_core_day_runtime_dailyavgHTD_baseline90',
            'baseline_total_core_day_runtime_dailyavgHTD_baseline90',
            '_daily_mean_core_day_demand_baseline_dailyavgHTD_baseline90',
            'percent_savings_dailyavgHTD_baseline_regional',
            'avoided_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional',
            'avoided_total_core_day_runtime_dailyavgHTD_baseline_regional',
            'baseline_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional',
            'baseline_total_core_day_runtime_dailyavgHTD_baseline_regional',
            '_daily_mean_core_day_demand_baseline_dailyavgHTD_baseline_regional',
            'mean_demand_dailyavgHTD',
            'alpha_dailyavgHTD',
            'tau_dailyavgHTD',
            'mean_sq_err_dailyavgHTD',
            'root_mean_sq_err_dailyavgHTD',
            'cv_root_mean_sq_err_dailyavgHTD',
            'mean_abs_err_dailyavgHTD',
            'mean_abs_pct_err_dailyavgHTD',

            'percent_savings_hourlyavgHTD_baseline90',
            'avoided_daily_mean_core_day_runtime_hourlyavgHTD_baseline90',
            'avoided_total_core_day_runtime_hourlyavgHTD_baseline90',
            'baseline_daily_mean_core_day_runtime_hourlyavgHTD_baseline90',
            'baseline_total_core_day_runtime_hourlyavgHTD_baseline90',
            '_daily_mean_core_day_demand_baseline_hourlyavgHTD_baseline90',
            'percent_savings_hourlyavgHTD_baseline_regional',
            'avoided_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional',
            'avoided_total_core_day_runtime_hourlyavgHTD_baseline_regional',
            'baseline_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional',
            'baseline_total_core_day_runtime_hourlyavgHTD_baseline_regional',
            '_daily_mean_core_day_demand_baseline_hourlyavgHTD_baseline_regional',
            'mean_demand_hourlyavgHTD',
            'alpha_hourlyavgHTD',
            'tau_hourlyavgHTD',
            'mean_sq_err_hourlyavgHTD',
            'root_mean_sq_err_hourlyavgHTD',
            'cv_root_mean_sq_err_hourlyavgHTD',
            'mean_abs_err_hourlyavgHTD',
            'mean_abs_pct_err_hourlyavgHTD',

            'total_core_cooling_runtime',
            'total_core_heating_runtime',
            'total_auxiliary_heating_core_day_runtime',
            'total_emergency_heating_core_day_runtime',

            'daily_mean_core_cooling_runtime',
            'daily_mean_core_heating_runtime',

            'rhu_00F_to_05F',
            'rhu_05F_to_10F',
            'rhu_10F_to_15F',
            'rhu_15F_to_20F',
            'rhu_20F_to_25F',
            'rhu_25F_to_30F',
            'rhu_30F_to_35F',
            'rhu_35F_to_40F',
            'rhu_40F_to_45F',
            'rhu_45F_to_50F',
            'rhu_50F_to_55F',
            'rhu_55F_to_60F',
        ]
