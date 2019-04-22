from thermostat.exporters import metrics_to_csv
from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics

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

@pytest.fixture(scope="session")
def metrics_type_1_multiple(thermostat_type_1):
    metrics_type_1 = multiple_thermostat_calculate_epa_field_savings_metrics([thermostat_type_1])
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

def test_multiple_thermostat_calculate_epa_field_savings_metrics_type_1(metrics_type_1_multiple, metrics_type_1_data):
    # Test multiprocessing thermostat code
    assert len(metrics_type_1_multiple) == len(metrics_type_1_data)

    for key in metrics_type_1_multiple[0].keys():
        test_value = metrics_type_1_multiple[0][key]
        target_value = metrics_type_1_data[0][key]
        if isinstance(test_value, six.string_types):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

    for key in metrics_type_1_multiple[1].keys():
        test_value = metrics_type_1_multiple[1][key]
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

            'baseline_percentile_core_cooling_comfort_temperature',
            'baseline_percentile_core_heating_comfort_temperature',
            'regional_average_baseline_cooling_comfort_temperature',
            'regional_average_baseline_heating_comfort_temperature',

            'percent_savings_baseline_percentile',
            'avoided_daily_mean_core_day_runtime_baseline_percentile',
            'avoided_total_core_day_runtime_baseline_percentile',
            'baseline_daily_mean_core_day_runtime_baseline_percentile',
            'baseline_total_core_day_runtime_baseline_percentile',
            '_daily_mean_core_day_demand_baseline_baseline_percentile',
            'percent_savings_baseline_regional',
            'avoided_daily_mean_core_day_runtime_baseline_regional',
            'avoided_total_core_day_runtime_baseline_regional',
            'baseline_daily_mean_core_day_runtime_baseline_regional',
            'baseline_total_core_day_runtime_baseline_regional',
            '_daily_mean_core_day_demand_baseline_baseline_regional',
            'mean_demand',
            'alpha',
            'tau',
            'mean_sq_err',
            'root_mean_sq_err',
            'cv_root_mean_sq_err',
            'mean_abs_err',
            'mean_abs_pct_err',

            'total_core_cooling_runtime',
            'total_core_heating_runtime',
            'total_auxiliary_heating_core_day_runtime',
            'total_emergency_heating_core_day_runtime',

            'daily_mean_core_cooling_runtime',
            'daily_mean_core_heating_runtime',

            'core_cooling_days_mean_indoor_temperature',
            'core_cooling_days_mean_outdoor_temperature',
            'core_heating_days_mean_indoor_temperature',
            'core_heating_days_mean_outdoor_temperature',
            'core_mean_indoor_temperature',
            'core_mean_outdoor_temperature',

	    'rhu1_aux_duty_cycle',
	    'rhu1_emg_duty_cycle',
	    'rhu1_compressor_duty_cycle',

	    'rhu1_00F_to_05F',
	    'rhu1_05F_to_10F',
	    'rhu1_10F_to_15F',
	    'rhu1_15F_to_20F',
	    'rhu1_20F_to_25F',
	    'rhu1_25F_to_30F',
	    'rhu1_30F_to_35F',
	    'rhu1_35F_to_40F',
	    'rhu1_40F_to_45F',
	    'rhu1_45F_to_50F',
	    'rhu1_50F_to_55F',
	    'rhu1_55F_to_60F',

	    'rhu1_05F_to_10F_aux_duty_cycle',
	    'rhu1_10F_to_15F_aux_duty_cycle',
	    'rhu1_15F_to_20F_aux_duty_cycle',
	    'rhu1_20F_to_25F_aux_duty_cycle',
	    'rhu1_25F_to_30F_aux_duty_cycle',
	    'rhu1_30F_to_35F_aux_duty_cycle',
	    'rhu1_35F_to_40F_aux_duty_cycle',
	    'rhu1_40F_to_45F_aux_duty_cycle',
	    'rhu1_45F_to_50F_aux_duty_cycle',
	    'rhu1_50F_to_55F_aux_duty_cycle',
	    'rhu1_55F_to_60F_aux_duty_cycle',

	    'rhu1_00F_to_05F_emg_duty_cycle',
	    'rhu1_05F_to_10F_emg_duty_cycle',
	    'rhu1_10F_to_15F_emg_duty_cycle',
	    'rhu1_15F_to_20F_emg_duty_cycle',
	    'rhu1_20F_to_25F_emg_duty_cycle',
	    'rhu1_25F_to_30F_emg_duty_cycle',
	    'rhu1_30F_to_35F_emg_duty_cycle',
	    'rhu1_35F_to_40F_emg_duty_cycle',
	    'rhu1_40F_to_45F_emg_duty_cycle',
	    'rhu1_45F_to_50F_emg_duty_cycle',
	    'rhu1_50F_to_55F_emg_duty_cycle',
	    'rhu1_55F_to_60F_emg_duty_cycle',

	    'rhu1_00F_to_05F_compressor_duty_cycle',
	    'rhu1_05F_to_10F_compressor_duty_cycle',
	    'rhu1_10F_to_15F_compressor_duty_cycle',
	    'rhu1_15F_to_20F_compressor_duty_cycle',
	    'rhu1_20F_to_25F_compressor_duty_cycle',
	    'rhu1_25F_to_30F_compressor_duty_cycle',
	    'rhu1_30F_to_35F_compressor_duty_cycle',
	    'rhu1_35F_to_40F_compressor_duty_cycle',
	    'rhu1_40F_to_45F_compressor_duty_cycle',
	    'rhu1_45F_to_50F_compressor_duty_cycle',
	    'rhu1_50F_to_55F_compressor_duty_cycle',
	    'rhu1_55F_to_60F_compressor_duty_cycle',

	    'rhu1_less10F',
	    'rhu1_10F_to_20F',
	    'rhu1_20F_to_30F',
	    'rhu1_30F_to_40F',
	    'rhu1_40F_to_50F',
	    'rhu1_50F_to_60F',
	    'rhu1_00F_to_05F_aux_duty_cycle',

	    'rhu1_less10F_aux_duty_cycle',
	    'rhu1_10F_to_20F_aux_duty_cycle',
	    'rhu1_20F_to_30F_aux_duty_cycle',
	    'rhu1_30F_to_40F_aux_duty_cycle',
	    'rhu1_40F_to_50F_aux_duty_cycle',
	    'rhu1_50F_to_60F_aux_duty_cycle',

	    'rhu1_less10F_emg_duty_cycle',
	    'rhu1_10F_to_20F_emg_duty_cycle',
	    'rhu1_20F_to_30F_emg_duty_cycle',
	    'rhu1_30F_to_40F_emg_duty_cycle',
	    'rhu1_40F_to_50F_emg_duty_cycle',
	    'rhu1_50F_to_60F_emg_duty_cycle',

	    'rhu1_less10F_compressor_duty_cycle',
	    'rhu1_10F_to_20F_compressor_duty_cycle',
	    'rhu1_20F_to_30F_compressor_duty_cycle',
	    'rhu1_30F_to_40F_compressor_duty_cycle',
	    'rhu1_40F_to_50F_compressor_duty_cycle',
	    'rhu1_50F_to_60F_compressor_duty_cycle',

	    'rhu2_00F_to_05F',
	    'rhu2_05F_to_10F',
	    'rhu2_10F_to_15F',
	    'rhu2_15F_to_20F',
	    'rhu2_20F_to_25F',
	    'rhu2_25F_to_30F',
	    'rhu2_30F_to_35F',
	    'rhu2_35F_to_40F',
	    'rhu2_40F_to_45F',
	    'rhu2_45F_to_50F',
	    'rhu2_50F_to_55F',
	    'rhu2_55F_to_60F',

	    'rhu2_00F_to_05F_aux_duty_cycle',
	    'rhu2_05F_to_10F_aux_duty_cycle',
	    'rhu2_10F_to_15F_aux_duty_cycle',
	    'rhu2_15F_to_20F_aux_duty_cycle',
	    'rhu2_20F_to_25F_aux_duty_cycle',
	    'rhu2_25F_to_30F_aux_duty_cycle',
	    'rhu2_30F_to_35F_aux_duty_cycle',
	    'rhu2_35F_to_40F_aux_duty_cycle',
	    'rhu2_40F_to_45F_aux_duty_cycle',
	    'rhu2_45F_to_50F_aux_duty_cycle',
	    'rhu2_50F_to_55F_aux_duty_cycle',
	    'rhu2_55F_to_60F_aux_duty_cycle',

	    'rhu2_00F_to_05F_emg_duty_cycle',
	    'rhu2_05F_to_10F_emg_duty_cycle',
	    'rhu2_10F_to_15F_emg_duty_cycle',
	    'rhu2_15F_to_20F_emg_duty_cycle',
	    'rhu2_20F_to_25F_emg_duty_cycle',
	    'rhu2_25F_to_30F_emg_duty_cycle',
	    'rhu2_30F_to_35F_emg_duty_cycle',
	    'rhu2_35F_to_40F_emg_duty_cycle',
	    'rhu2_40F_to_45F_emg_duty_cycle',
	    'rhu2_45F_to_50F_emg_duty_cycle',
	    'rhu2_50F_to_55F_emg_duty_cycle',
	    'rhu2_55F_to_60F_emg_duty_cycle',

	    'rhu2_00F_to_05F_compressor_duty_cycle',
	    'rhu2_05F_to_10F_compressor_duty_cycle',
	    'rhu2_10F_to_15F_compressor_duty_cycle',
	    'rhu2_15F_to_20F_compressor_duty_cycle',
	    'rhu2_20F_to_25F_compressor_duty_cycle',
	    'rhu2_25F_to_30F_compressor_duty_cycle',
	    'rhu2_30F_to_35F_compressor_duty_cycle',
	    'rhu2_35F_to_40F_compressor_duty_cycle',
	    'rhu2_40F_to_45F_compressor_duty_cycle',
	    'rhu2_45F_to_50F_compressor_duty_cycle',
	    'rhu2_50F_to_55F_compressor_duty_cycle',
	    'rhu2_55F_to_60F_compressor_duty_cycle',

	    'rhu2_less10F',
	    'rhu2_10F_to_20F',
	    'rhu2_20F_to_30F',
	    'rhu2_30F_to_40F',
	    'rhu2_40F_to_50F',
	    'rhu2_50F_to_60F',

	    'rhu2_less10F_aux_duty_cycle',
	    'rhu2_10F_to_20F_aux_duty_cycle',
	    'rhu2_20F_to_30F_aux_duty_cycle',
	    'rhu2_30F_to_40F_aux_duty_cycle',
	    'rhu2_40F_to_50F_aux_duty_cycle',
	    'rhu2_50F_to_60F_aux_duty_cycle',

	    'rhu2_less10F_emg_duty_cycle',
	    'rhu2_10F_to_20F_emg_duty_cycle',
	    'rhu2_20F_to_30F_emg_duty_cycle',
	    'rhu2_30F_to_40F_emg_duty_cycle',
	    'rhu2_40F_to_50F_emg_duty_cycle',
	    'rhu2_50F_to_60F_emg_duty_cycle',

	    'rhu2_less10F_compressor_duty_cycle',
	    'rhu2_10F_to_20F_compressor_duty_cycle',
	    'rhu2_20F_to_30F_compressor_duty_cycle',
	    'rhu2_30F_to_40F_compressor_duty_cycle',
	    'rhu2_40F_to_50F_compressor_duty_cycle',
	    'rhu2_50F_to_60F_compressor_duty_cycle',

        ]
