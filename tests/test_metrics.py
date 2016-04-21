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

@pytest.fixture(scope="session")
def seasonal_metrics_type_1(thermostat_type_1):
    seasonal_metrics_type_1 = thermostat_type_1.calculate_epa_draft_rccs_field_savings_metrics()
    return seasonal_metrics_type_1

RTOL = 1e-3
ATOL = 1e-3

def test_calculate_epa_draft_rccs_field_savings_metrics_type_1(seasonal_metrics_type_1, seasonal_metrics_type_1_data):
    assert len(seasonal_metrics_type_1) == len(seasonal_metrics_type_1_data)

    for key in seasonal_metrics_type_1[0].keys():
        test_value = seasonal_metrics_type_1[0][key]
        target_value = seasonal_metrics_type_1_data[0][key]
        if isinstance(test_value, str):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

    for key in seasonal_metrics_type_1[1].keys():
        test_value = seasonal_metrics_type_1[1][key]
        target_value = seasonal_metrics_type_1_data[1][key]
        if isinstance(test_value, str):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

def test_calculate_epa_draft_rccs_field_savings_metrics_type_2(thermostat_type_2):
    seasonal_metrics_type_2_entire = thermostat_type_2.calculate_epa_draft_rccs_field_savings_metrics()
    assert len(seasonal_metrics_type_2_entire) == 2

    seasonal_metrics_type_2_yearly = thermostat_type_2.calculate_epa_draft_rccs_field_savings_metrics(
            cooling_season_method="year_end_to_end",
            heating_season_method="year_mid_to_mid")
    assert len(seasonal_metrics_type_2_yearly) == 9

def test_calculate_epa_draft_rccs_field_savings_metrics_type_3(thermostat_type_3):
    seasonal_metrics_type_3 = thermostat_type_3.calculate_epa_draft_rccs_field_savings_metrics()
    assert len(seasonal_metrics_type_3) == 2

def test_calculate_epa_draft_rccs_field_savings_metrics_type_4(thermostat_type_4):
    seasonal_metrics_type_4 = thermostat_type_4.calculate_epa_draft_rccs_field_savings_metrics()
    assert len(seasonal_metrics_type_4) == 1

def test_calculate_epa_draft_rccs_field_savings_metrics_type_5(thermostat_type_5):
    seasonal_metrics_type_5 = thermostat_type_5.calculate_epa_draft_rccs_field_savings_metrics()
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

            'seasonal_savings_dailyavgCDD',
            'seasonal_savings_dailyavgHDD',
            'seasonal_savings_deltaT',
            'seasonal_savings_hourlyavgCDD',
            'seasonal_savings_hourlyavgHDD',

            'seasonal_avoided_runtime_dailyavgCDD',
            'seasonal_avoided_runtime_dailyavgHDD',
            'seasonal_avoided_runtime_deltaT',
            'seasonal_avoided_runtime_hourlyavgCDD',
            'seasonal_avoided_runtime_hourlyavgHDD',

            'total_auxiliary_heating_runtime',
            'total_emergency_heating_runtime',
            'total_heating_runtime',
            'total_cooling_runtime',

            'actual_daily_runtime',
            'actual_seasonal_runtime',

            'baseline_comfort_temperature',

            'baseline_daily_runtime_dailyavgCDD',
            'baseline_daily_runtime_dailyavgHDD',
            'baseline_daily_runtime_deltaT',
            'baseline_daily_runtime_hourlyavgCDD',
            'baseline_daily_runtime_hourlyavgHDD',

            'baseline_seasonal_runtime_dailyavgCDD',
            'baseline_seasonal_runtime_dailyavgHDD',
            'baseline_seasonal_runtime_deltaT',
            'baseline_seasonal_runtime_hourlyavgCDD',
            'baseline_seasonal_runtime_hourlyavgHDD',

            'mean_demand_dailyavgCDD',
            'mean_demand_dailyavgHDD',
            'mean_demand_deltaT',
            'mean_demand_hourlyavgCDD',
            'mean_demand_hourlyavgHDD',

            'mean_demand_baseline_dailyavgCDD',
            'mean_demand_baseline_dailyavgHDD',
            'mean_demand_baseline_deltaT',
            'mean_demand_baseline_hourlyavgCDD',
            'mean_demand_baseline_hourlyavgHDD',

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

            'slope_deltaT',
            'alpha_est_dailyavgCDD',
            'alpha_est_dailyavgHDD',
            'alpha_est_hourlyavgCDD',
            'alpha_est_hourlyavgHDD',

            'intercept_deltaT',
            'deltaT_base_est_dailyavgCDD',
            'deltaT_base_est_dailyavgHDD',
            'deltaT_base_est_hourlyavgCDD',
            'deltaT_base_est_hourlyavgHDD',

            'mean_sq_err_dailyavgCDD',
            'mean_sq_err_dailyavgHDD',
            'mean_sq_err_deltaT',
            'mean_sq_err_hourlyavgCDD',
            'mean_sq_err_hourlyavgHDD',

            'root_mean_sq_err_dailyavgCDD',
            'root_mean_sq_err_dailyavgHDD',
            'root_mean_sq_err_deltaT',
            'root_mean_sq_err_hourlyavgCDD',
            'root_mean_sq_err_hourlyavgHDD',

            'cv_root_mean_sq_err_dailyavgCDD',
            'cv_root_mean_sq_err_dailyavgHDD',
            'cv_root_mean_sq_err_deltaT',
            'cv_root_mean_sq_err_hourlyavgCDD',
            'cv_root_mean_sq_err_hourlyavgHDD',

            'mean_abs_err_dailyavgCDD',
            'mean_abs_err_dailyavgHDD',
            'mean_abs_err_deltaT',
            'mean_abs_err_hourlyavgCDD',
            'mean_abs_err_hourlyavgHDD',

            'mean_abs_pct_err_dailyavgCDD',
            'mean_abs_pct_err_dailyavgHDD',
            'mean_abs_pct_err_deltaT',
            'mean_abs_pct_err_hourlyavgCDD',
            'mean_abs_pct_err_hourlyavgHDD',
        ]
