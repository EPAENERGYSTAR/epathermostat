from thermostat.exporters import seasonal_metrics_to_csv

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
from fixtures.thermostats import seasonal_metrics_type_1_data
import six

@pytest.fixture(scope="session")
def seasonal_metrics_type_1(thermostat_type_1):
    seasonal_metrics_type_1 = thermostat_type_1.calculate_epa_field_savings_metrics()
    return seasonal_metrics_type_1

RTOL = 1e-3
ATOL = 1e-3

def test_calculate_epa_field_savings_metrics_type_1(seasonal_metrics_type_1, seasonal_metrics_type_1_data):
    assert len(seasonal_metrics_type_1) == len(seasonal_metrics_type_1_data)

    for key in seasonal_metrics_type_1[0].keys():
        test_value = seasonal_metrics_type_1[0][key]
        target_value = seasonal_metrics_type_1_data[0][key]
        if isinstance(test_value, six.string_types):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

    for key in seasonal_metrics_type_1[1].keys():
        test_value = seasonal_metrics_type_1[1][key]
        target_value = seasonal_metrics_type_1_data[1][key]
        if isinstance(test_value, six.string_types):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

def test_calculate_epa_field_savings_metrics_type_2(thermostat_type_2):
    seasonal_metrics_type_2_entire = thermostat_type_2.calculate_epa_field_savings_metrics()
    assert len(seasonal_metrics_type_2_entire) == 2

    seasonal_metrics_type_2_yearly = thermostat_type_2.calculate_epa_field_savings_metrics(
            core_cooling_day_set_method="year_end_to_end",
            core_heating_day_set_method="year_mid_to_mid")
    assert len(seasonal_metrics_type_2_yearly) == 9

def test_calculate_epa_field_savings_metrics_type_3(thermostat_type_3):
    seasonal_metrics_type_3 = thermostat_type_3.calculate_epa_field_savings_metrics()
    assert len(seasonal_metrics_type_3) == 2

def test_calculate_epa_field_savings_metrics_type_4(thermostat_type_4):
    seasonal_metrics_type_4 = thermostat_type_4.calculate_epa_field_savings_metrics()
    assert len(seasonal_metrics_type_4) == 1

def test_calculate_epa_field_savings_metrics_type_5(thermostat_type_5):
    seasonal_metrics_type_5 = thermostat_type_5.calculate_epa_field_savings_metrics()
    assert len(seasonal_metrics_type_5) == 1

def test_seasonal_metrics_to_csv(seasonal_metrics_type_1):

    fd, fname = tempfile.mkstemp()
    df = seasonal_metrics_to_csv(seasonal_metrics_type_1, fname)

    assert isinstance(df, pd.DataFrame)
    assert df.columns[0] == "ct_identifier"
    assert df.columns[1] == "equipment_type"

    with open(fname,'r') as f:
        lines = f.readlines()
        assert len(lines) == 3
        column_heads = lines[0].strip().split(',')
        assert column_heads == [
            'ct_identifier',
            'equipment_type',
            'season_name',
            'station',
            'zipcode',

            'n_days_in_season_range',
            'n_days_in_season',
            'n_days_both_heating_and_cooling',
            'n_days_insufficient_data',

            'percent_savings_deltaT',
            'avoided_daily_runtime_deltaT',
            'avoided_seasonal_runtime_deltaT',
            'baseline_daily_runtime_deltaT',
            'baseline_seasonal_runtime_deltaT',
            'mean_demand_deltaT',
            'mean_demand_baseline_deltaT',
            'alpha_deltaT',
            'tau_deltaT',
            'mean_sq_err_deltaT',
            'root_mean_sq_err_deltaT',
            'cv_root_mean_sq_err_deltaT',
            'mean_abs_err_deltaT',
            'mean_abs_pct_err_deltaT',

            'percent_savings_dailyavgCTD',
            'avoided_daily_runtime_dailyavgCTD',
            'avoided_seasonal_runtime_dailyavgCTD',
            'baseline_daily_runtime_dailyavgCTD',
            'baseline_seasonal_runtime_dailyavgCTD',
            'mean_demand_dailyavgCTD',
            'mean_demand_baseline_dailyavgCTD',
            'alpha_dailyavgCTD',
            'tau_dailyavgCTD',
            'mean_sq_err_dailyavgCTD',
            'root_mean_sq_err_dailyavgCTD',
            'cv_root_mean_sq_err_dailyavgCTD',
            'mean_abs_err_dailyavgCTD',
            'mean_abs_pct_err_dailyavgCTD',

            'percent_savings_hourlyavgCTD',
            'avoided_daily_runtime_hourlyavgCTD',
            'avoided_seasonal_runtime_hourlyavgCTD',
            'baseline_daily_runtime_hourlyavgCTD',
            'baseline_seasonal_runtime_hourlyavgCTD',
            'mean_demand_hourlyavgCTD',
            'mean_demand_baseline_hourlyavgCTD',
            'alpha_hourlyavgCTD',
            'tau_hourlyavgCTD',
            'mean_sq_err_hourlyavgCTD',
            'root_mean_sq_err_hourlyavgCTD',
            'cv_root_mean_sq_err_hourlyavgCTD',
            'mean_abs_err_hourlyavgCTD',
            'mean_abs_pct_err_hourlyavgCTD',

            'percent_savings_dailyavgHTD',
            'avoided_daily_runtime_dailyavgHTD',
            'avoided_seasonal_runtime_dailyavgHTD',
            'baseline_daily_runtime_dailyavgHTD',
            'baseline_seasonal_runtime_dailyavgHTD',
            'mean_demand_dailyavgHTD',
            'mean_demand_baseline_dailyavgHTD',
            'alpha_dailyavgHTD',
            'tau_dailyavgHTD',
            'mean_sq_err_dailyavgHTD',
            'root_mean_sq_err_dailyavgHTD',
            'cv_root_mean_sq_err_dailyavgHTD',
            'mean_abs_err_dailyavgHTD',
            'mean_abs_pct_err_dailyavgHTD',

            'percent_savings_hourlyavgHTD',
            'avoided_daily_runtime_hourlyavgHTD',
            'avoided_seasonal_runtime_hourlyavgHTD',
            'baseline_daily_runtime_hourlyavgHTD',
            'baseline_seasonal_runtime_hourlyavgHTD',
            'mean_demand_hourlyavgHTD',
            'mean_demand_baseline_hourlyavgHTD',
            'alpha_hourlyavgHTD',
            'tau_hourlyavgHTD',
            'mean_sq_err_hourlyavgHTD',
            'root_mean_sq_err_hourlyavgHTD',
            'cv_root_mean_sq_err_hourlyavgHTD',
            'mean_abs_err_hourlyavgHTD',
            'mean_abs_pct_err_hourlyavgHTD',

            'total_auxiliary_heating_runtime',
            'total_emergency_heating_runtime',
            'total_heating_runtime',
            'total_cooling_runtime',

            'actual_daily_runtime',
            'actual_seasonal_runtime',

            'baseline_comfort_temperature',

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
