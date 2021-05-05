from scipy.stats import norm, randint
import pandas as pd
import numpy as np
import json
from datetime import datetime

import tempfile
from itertools import islice, cycle

import pytest

from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics
from thermostat.exporters import certification_to_csv
from thermostat.columns import EXPORT_COLUMNS
from thermostat.stats import (
        combine_output_dataframes,
        compute_summary_statistics,
        summary_statistics_to_csv,
        )
from .fixtures.single_stage import thermostat_emg_aux_constant_on_outlier


def get_fake_output_df(n_columns):
    columns = EXPORT_COLUMNS

    string_placeholder = ["PLACEHOLDER"] * n_columns
    zero_column = [0 if randint.rvs(0, 30) > 0 else  (None if randint.rvs(0, 2) > 0 else np.inf)
            for i in randint.rvs(0, 1, size=n_columns)]
    one_column = [1 if randint.rvs(0, 30) > 0 else  (None if randint.rvs(0, 2) > 0 else np.inf)
            for i in randint.rvs(0, 1, size=n_columns)]
    float_column = [i if randint.rvs(0, 30) > 0 else (None if randint.rvs(0, 2) > 0 else np.inf)
            for i in norm.rvs(size=n_columns)]
    zipcodes = ["01234", "12345", "23456", "34567", "43210", "54321", "65432", "76543"]
    zipcode_column = [i for i in islice(cycle(zipcodes), None, n_columns)]
    core_day_set_names = ["cooling_2012", "heating_2012-2013", "cooling_2013"]
    core_day_set_name_column = [i for i in islice(cycle(core_day_set_names), None, n_columns)]

    data = {
        'sw_version': string_placeholder,

        'ct_identifier': string_placeholder,
        'heat_type': string_placeholder,
        'heat_stage': string_placeholder,
        'cool_type': string_placeholder,
        'cool_stage': string_placeholder,
        'heating_or_cooling': core_day_set_name_column,
        'station': string_placeholder,
        'zipcode': zipcode_column,
        'climate_zone': string_placeholder,

        'start_date': datetime(2011, 1, 1),
        'end_date': datetime(2012, 1, 1),
        'n_days_both_heating_and_cooling': one_column,
        'n_days_in_inputfile_date_range': one_column,
        'n_days_insufficient_data': zero_column,
        'n_core_heating_days': one_column,

        'baseline_percentile_core_cooling_comfort_temperature': float_column,
        'baseline_percentile_core_heating_comfort_temperature': float_column,
        'regional_average_baseline_cooling_comfort_temperature': float_column,
        'regional_average_baseline_heating_comfort_temperature': float_column,

        'percent_savings_baseline_percentile': float_column,
        'avoided_daily_mean_core_day_runtime_baseline_percentile': float_column,
        'avoided_total_core_day_runtime_baseline_percentile': float_column,
        'baseline_daily_mean_core_day_runtime_baseline_percentile': float_column,
        'baseline_total_core_day_runtime_baseline_percentile': float_column,
        '_daily_mean_core_day_demand_baseline_baseline_percentile': float_column,
        'percent_savings_baseline_regional': float_column,
        'avoided_daily_mean_core_day_runtime_baseline_regional': float_column,
        'avoided_total_core_day_runtime_baseline_regional': float_column,
        'baseline_daily_mean_core_day_runtime_baseline_regional': float_column,
        'baseline_total_core_day_runtime_baseline_regional': float_column,
        '_daily_mean_core_day_demand_baseline_baseline_regional': float_column,
        'mean_demand': float_column,
        'alpha': float_column,
        'tau': float_column,
        'mean_sq_err': float_column,
        'root_mean_sq_err': float_column,
        'cv_root_mean_sq_err': float_column,
        'mean_abs_err': float_column,
        'mean_abs_pct_err': float_column,

        'total_core_cooling_runtime': float_column,
        'total_core_heating_runtime': float_column,
        'total_auxiliary_heating_core_day_runtime': float_column,
        'total_emergency_heating_core_day_runtime': float_column,

        'daily_mean_core_cooling_runtime': float_column,
        'daily_mean_core_heating_runtime': float_column,

        'core_cooling_days_mean_indoor_temperature': float_column,
        'core_cooling_days_mean_outdoor_temperature': float_column,
        'core_heating_days_mean_indoor_temperature': float_column,
        'core_heating_days_mean_outdoor_temperature': float_column,
        'core_mean_indoor_temperature': float_column,
        'core_mean_outdoor_temperature': float_column,

        'rhu1_aux_duty_cycle': float_column,
        'rhu1_emg_duty_cycle': float_column,
        'rhu1_compressor_duty_cycle': float_column,

        'rhu1_00F_to_05F': float_column,
        'rhu1_05F_to_10F': float_column,
        'rhu1_10F_to_15F': float_column,
        'rhu1_15F_to_20F': float_column,
        'rhu1_20F_to_25F': float_column,
        'rhu1_25F_to_30F': float_column,
        'rhu1_30F_to_35F': float_column,
        'rhu1_35F_to_40F': float_column,
        'rhu1_40F_to_45F': float_column,
        'rhu1_45F_to_50F': float_column,
        'rhu1_50F_to_55F': float_column,
        'rhu1_55F_to_60F': float_column,

        'rhu1_00F_to_05F_aux_duty_cycle': float_column,
        'rhu1_05F_to_10F_aux_duty_cycle': float_column,
        'rhu1_10F_to_15F_aux_duty_cycle': float_column,
        'rhu1_15F_to_20F_aux_duty_cycle': float_column,
        'rhu1_20F_to_25F_aux_duty_cycle': float_column,
        'rhu1_25F_to_30F_aux_duty_cycle': float_column,
        'rhu1_30F_to_35F_aux_duty_cycle': float_column,
        'rhu1_35F_to_40F_aux_duty_cycle': float_column,
        'rhu1_40F_to_45F_aux_duty_cycle': float_column,
        'rhu1_45F_to_50F_aux_duty_cycle': float_column,
        'rhu1_50F_to_55F_aux_duty_cycle': float_column,
        'rhu1_55F_to_60F_aux_duty_cycle': float_column,

        'rhu1_00F_to_05F_emg_duty_cycle': float_column,
        'rhu1_05F_to_10F_emg_duty_cycle': float_column,
        'rhu1_10F_to_15F_emg_duty_cycle': float_column,
        'rhu1_15F_to_20F_emg_duty_cycle': float_column,
        'rhu1_20F_to_25F_emg_duty_cycle': float_column,
        'rhu1_25F_to_30F_emg_duty_cycle': float_column,
        'rhu1_30F_to_35F_emg_duty_cycle': float_column,
        'rhu1_35F_to_40F_emg_duty_cycle': float_column,
        'rhu1_40F_to_45F_emg_duty_cycle': float_column,
        'rhu1_45F_to_50F_emg_duty_cycle': float_column,
        'rhu1_50F_to_55F_emg_duty_cycle': float_column,
        'rhu1_55F_to_60F_emg_duty_cycle': float_column,

        'rhu1_00F_to_05F_compressor_duty_cycle': float_column,
        'rhu1_05F_to_10F_compressor_duty_cycle': float_column,
        'rhu1_10F_to_15F_compressor_duty_cycle': float_column,
        'rhu1_15F_to_20F_compressor_duty_cycle': float_column,
        'rhu1_20F_to_25F_compressor_duty_cycle': float_column,
        'rhu1_25F_to_30F_compressor_duty_cycle': float_column,
        'rhu1_30F_to_35F_compressor_duty_cycle': float_column,
        'rhu1_35F_to_40F_compressor_duty_cycle': float_column,
        'rhu1_40F_to_45F_compressor_duty_cycle': float_column,
        'rhu1_45F_to_50F_compressor_duty_cycle': float_column,
        'rhu1_50F_to_55F_compressor_duty_cycle': float_column,
        'rhu1_55F_to_60F_compressor_duty_cycle': float_column,

        'rhu2_aux_duty_cycle': float_column,
        'rhu2_emg_duty_cycle': float_column,
        'rhu2_compressor_duty_cycle': float_column,

        'rhu2_00F_to_05F': float_column,
        'rhu2_05F_to_10F': float_column,
        'rhu2_10F_to_15F': float_column,
        'rhu2_15F_to_20F': float_column,
        'rhu2_20F_to_25F': float_column,
        'rhu2_25F_to_30F': float_column,
        'rhu2_30F_to_35F': float_column,
        'rhu2_35F_to_40F': float_column,
        'rhu2_40F_to_45F': float_column,
        'rhu2_45F_to_50F': float_column,
        'rhu2_50F_to_55F': float_column,
        'rhu2_55F_to_60F': float_column,

        'rhu2_00F_to_05F_aux_duty_cycle': float_column,
        'rhu2_05F_to_10F_aux_duty_cycle': float_column,
        'rhu2_10F_to_15F_aux_duty_cycle': float_column,
        'rhu2_15F_to_20F_aux_duty_cycle': float_column,
        'rhu2_20F_to_25F_aux_duty_cycle': float_column,
        'rhu2_25F_to_30F_aux_duty_cycle': float_column,
        'rhu2_30F_to_35F_aux_duty_cycle': float_column,
        'rhu2_35F_to_40F_aux_duty_cycle': float_column,
        'rhu2_40F_to_45F_aux_duty_cycle': float_column,
        'rhu2_45F_to_50F_aux_duty_cycle': float_column,
        'rhu2_50F_to_55F_aux_duty_cycle': float_column,
        'rhu2_55F_to_60F_aux_duty_cycle': float_column,

        'rhu2_00F_to_05F_emg_duty_cycle': float_column,
        'rhu2_05F_to_10F_emg_duty_cycle': float_column,
        'rhu2_10F_to_15F_emg_duty_cycle': float_column,
        'rhu2_15F_to_20F_emg_duty_cycle': float_column,
        'rhu2_20F_to_25F_emg_duty_cycle': float_column,
        'rhu2_25F_to_30F_emg_duty_cycle': float_column,
        'rhu2_30F_to_35F_emg_duty_cycle': float_column,
        'rhu2_35F_to_40F_emg_duty_cycle': float_column,
        'rhu2_40F_to_45F_emg_duty_cycle': float_column,
        'rhu2_45F_to_50F_emg_duty_cycle': float_column,
        'rhu2_50F_to_55F_emg_duty_cycle': float_column,
        'rhu2_55F_to_60F_emg_duty_cycle': float_column,

        'rhu2_00F_to_05F_compressor_duty_cycle': float_column,
        'rhu2_05F_to_10F_compressor_duty_cycle': float_column,
        'rhu2_10F_to_15F_compressor_duty_cycle': float_column,
        'rhu2_15F_to_20F_compressor_duty_cycle': float_column,
        'rhu2_20F_to_25F_compressor_duty_cycle': float_column,
        'rhu2_25F_to_30F_compressor_duty_cycle': float_column,
        'rhu2_30F_to_35F_compressor_duty_cycle': float_column,
        'rhu2_35F_to_40F_compressor_duty_cycle': float_column,
        'rhu2_40F_to_45F_compressor_duty_cycle': float_column,
        'rhu2_45F_to_50F_compressor_duty_cycle': float_column,
        'rhu2_50F_to_55F_compressor_duty_cycle': float_column,
        'rhu2_55F_to_60F_compressor_duty_cycle': float_column,

        'rhu2_30F_to_45F': float_column,
        'rhu2_30F_to_45F_aux_duty_cycle': float_column,
        'rhu2_30F_to_45F_emg_duty_cycle': float_column,
        'rhu2_30F_to_45F_compressor_duty_cycle': float_column,
    }
    df = pd.DataFrame(data, columns=columns)
    return df


@pytest.fixture
def dataframes():
    df1 = get_fake_output_df(10)
    df2 = get_fake_output_df(10)
    dfs = [df1, df2]
    return dfs


@pytest.fixture
def combined_dataframe():
    df = get_fake_output_df(100)
    return df


def test_combine_output_dataframes(dataframes):
    combined = combine_output_dataframes(dataframes)
    assert combined.shape == (20, 78)


def test_compute_summary_statistics_advanced(combined_dataframe):
    summary_statistics = compute_summary_statistics(combined_dataframe,
            advanced_filtering=True)
    assert [len(s) for s in summary_statistics] == [
            49, 49, 49, 49, 49, 49, 49, 49,
            2049, 901, 2049, 901, 2049, 901, 2049, 901,
            ]


def test_summary_statistics_to_csv(combined_dataframe):
    summary_statistics = compute_summary_statistics(combined_dataframe)


def test_none_summary_statistics_to_csv():
    assert(summary_statistics_to_csv(None, None, None) is None)


def test_compute_summary_statistics(combined_dataframe):
    summary_statistics = compute_summary_statistics(combined_dataframe)
    assert [len(s) for s in summary_statistics] == [
            49, 49, 49, 49,
            2049, 901, 2049, 901,
            ]

    _, fname = tempfile.mkstemp()
    product_id = "FAKE"
    stats_df = summary_statistics_to_csv(summary_statistics, fname, product_id)
    assert isinstance(stats_df, pd.DataFrame)

    stats_df_reread = pd.read_csv(fname)
    assert stats_df_reread.shape == (2133, 5)


def test_none_stats_certification_to_csv():
    assert(certification_to_csv(None, None, None) is None)


def test_certification(combined_dataframe):
    _, fname_stats = tempfile.mkstemp()
    _, fname_cert = tempfile.mkstemp()
    product_id = "FAKE"
    stats_df = compute_summary_statistics(combined_dataframe)
    certification_df = certification_to_csv(stats_df, fname_cert, product_id)
    assert certification_df.shape == (5, 8)


def test_bogus_method():
    with pytest.raises(ValueError):
        compute_summary_statistics(None, target_baseline_method='bogus_method')


def test_empty_metrics():
    df = pd.DataFrame([])
    assert(compute_summary_statistics(df) is None)


def test_iqr_filtering(thermostat_emg_aux_constant_on_outlier):

    thermostats_iqflt = list(thermostat_emg_aux_constant_on_outlier)
    # Run the metrics / statistics with the outlier thermostat in place
    iqflt_metrics = multiple_thermostat_calculate_epa_field_savings_metrics(thermostats_iqflt)
    iqflt_output_dataframe = pd.DataFrame(iqflt_metrics, columns=EXPORT_COLUMNS)
    iqflt_summary_statistics = compute_summary_statistics(iqflt_output_dataframe)

    # Remove the outlier thermostat
    thermostats_noiq = []
    for thermostat in list(thermostats_iqflt):
        if thermostat.thermostat_id != 'thermostat_single_emg_aux_constant_on_outlier':
            thermostats_noiq.append(thermostat)

    if len(thermostats_noiq) == 5:
        raise ValueError("Try again")

    # Re-run the metrics / statistics with the outlier thermostat removed
    noiq_metrics = multiple_thermostat_calculate_epa_field_savings_metrics(thermostats_noiq)
    noiq_output_dataframe = pd.DataFrame(noiq_metrics, columns=EXPORT_COLUMNS)
    noiq_summary_statistics = compute_summary_statistics(noiq_output_dataframe)

    # Verify that the IQFLT removed the outliers by comparing this with the
    # metrics with the outlier thermostat already removed.
    for column in range(0, len(iqflt_summary_statistics)):
        fields_iqflt = [x for x in iqflt_summary_statistics[column] if 'IQFLT' in x]
        for field_iqflt in fields_iqflt:
            field_noiq = field_iqflt.replace('rhu2IQFLT', 'rhu2')
            left_side = iqflt_summary_statistics[column][field_iqflt]
            right_side = noiq_summary_statistics[column][field_noiq]

            if np.isnan(left_side) or np.isnan(right_side):
                assert(np.isnan(left_side) and np.isnan(right_side))
            else:
                assert(left_side == right_side)
