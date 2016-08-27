from thermostat.stats import combine_output_dataframes
from thermostat.stats import compute_summary_statistics
from thermostat.stats import summary_statistics_to_csv
from thermostat.stats import ZipcodeGroupSpec
from thermostat.stats import compute_summary_statistics_by_zipcode
from thermostat.stats import compute_summary_statistics_by_weather_station
from thermostat.stats import compute_summary_statistics_by_zipcode_group

from scipy.stats import norm, randint
import pandas as pd
import numpy as np
import json

import tempfile
from itertools import islice, cycle

import pytest

def get_fake_output_df(n_columns):
    columns = [
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

    string_placeholder = ["PLACEHOLDER"] * n_columns
    zero_column = [0 if randint.rvs(0, 30) > 0 else  (None if randint.rvs(0, 2) > 0 else np.inf)
                  for i in randint.rvs(0, 1, size=n_columns)]
    one_column = [1 if randint.rvs(0, 30) > 0 else  (None if randint.rvs(0, 2) > 0 else np.inf)
                  for i in randint.rvs(0, 1, size=n_columns)]
    float_column = [i if randint.rvs(0, 30) > 0 else (None if randint.rvs(0, 2) > 0 else np.inf)
                    for i in norm.rvs(size=n_columns)]
    zipcodes = ["01234", "12345", "23456", "34567", "43210", "54321", "65432", "76543"]
    zipcode_column = [i for i in islice(cycle(zipcodes), None, n_columns)]
    season_names = ["Cooling 2012", "Heating 2012-2013", "Cooling 2013"]
    season_name_column = [i for i in islice(cycle(season_names), None, n_columns)]
    data = {
        "ct_identifier": string_placeholder,
        "equipment_type": string_placeholder,
        "season_name": season_name_column,
        "station": string_placeholder,
        "zipcode": zipcode_column,

        "n_days_both_heating_and_cooling": one_column,
        "n_days_in_season": one_column,
        "n_days_in_season_range": one_column,
        "n_days_insufficient_data": zero_column,

        'percent_savings_deltaT': float_column,
        'avoided_daily_runtime_deltaT': float_column,
        'avoided_seasonal_runtime_deltaT': float_column,
        'baseline_daily_runtime_deltaT': float_column,
        'baseline_seasonal_runtime_deltaT': float_column,
        'mean_demand_deltaT': float_column,
        'mean_demand_baseline_deltaT': float_column,
        'alpha_deltaT': float_column,
        'tau_deltaT': float_column,
        'mean_sq_err_deltaT': float_column,
        'root_mean_sq_err_deltaT': float_column,
        'cv_root_mean_sq_err_deltaT': float_column,
        'mean_abs_err_deltaT': float_column,
        'mean_abs_pct_err_deltaT': float_column,
        'percent_savings_dailyavgCTD': float_column,
        'avoided_daily_runtime_dailyavgCTD': float_column,
        'avoided_seasonal_runtime_dailyavgCTD': float_column,
        'baseline_daily_runtime_dailyavgCTD': float_column,
        'baseline_seasonal_runtime_dailyavgCTD': float_column,
        'mean_demand_dailyavgCTD': float_column,
        'mean_demand_baseline_dailyavgCTD': float_column,
        'alpha_dailyavgCTD': float_column,
        'tau_dailyavgCTD': float_column,
        'mean_sq_err_dailyavgCTD': float_column,
        'root_mean_sq_err_dailyavgCTD': float_column,
        'cv_root_mean_sq_err_dailyavgCTD': float_column,
        'mean_abs_err_dailyavgCTD': float_column,
        'mean_abs_pct_err_dailyavgCTD': float_column,
        'percent_savings_hourlyavgCTD': float_column,
        'avoided_daily_runtime_hourlyavgCTD': float_column,
        'avoided_seasonal_runtime_hourlyavgCTD': float_column,
        'baseline_daily_runtime_hourlyavgCTD': float_column,
        'baseline_seasonal_runtime_hourlyavgCTD': float_column,
        'mean_demand_hourlyavgCTD': float_column,
        'mean_demand_baseline_hourlyavgCTD': float_column,
        'alpha_hourlyavgCTD': float_column,
        'tau_hourlyavgCTD': float_column,
        'mean_sq_err_hourlyavgCTD': float_column,
        'root_mean_sq_err_hourlyavgCTD': float_column,
        'cv_root_mean_sq_err_hourlyavgCTD': float_column,
        'mean_abs_err_hourlyavgCTD': float_column,
        'mean_abs_pct_err_hourlyavgCTD': float_column,
        'percent_savings_dailyavgHTD': float_column,
        'avoided_daily_runtime_dailyavgHTD': float_column,
        'avoided_seasonal_runtime_dailyavgHTD': float_column,
        'baseline_daily_runtime_dailyavgHTD': float_column,
        'baseline_seasonal_runtime_dailyavgHTD': float_column,
        'mean_demand_dailyavgHTD': float_column,
        'mean_demand_baseline_dailyavgHTD': float_column,
        'alpha_dailyavgHTD': float_column,
        'tau_dailyavgHTD': float_column,
        'mean_sq_err_dailyavgHTD': float_column,
        'root_mean_sq_err_dailyavgHTD': float_column,
        'cv_root_mean_sq_err_dailyavgHTD': float_column,
        'mean_abs_err_dailyavgHTD': float_column,
        'mean_abs_pct_err_dailyavgHTD': float_column,
        'percent_savings_hourlyavgHTD': float_column,
        'avoided_daily_runtime_hourlyavgHTD': float_column,
        'avoided_seasonal_runtime_hourlyavgHTD': float_column,
        'baseline_daily_runtime_hourlyavgHTD': float_column,
        'baseline_seasonal_runtime_hourlyavgHTD': float_column,
        'mean_demand_hourlyavgHTD': float_column,
        'mean_demand_baseline_hourlyavgHTD': float_column,
        'alpha_hourlyavgHTD': float_column,
        'tau_hourlyavgHTD': float_column,
        'mean_sq_err_hourlyavgHTD': float_column,
        'root_mean_sq_err_hourlyavgHTD': float_column,
        'cv_root_mean_sq_err_hourlyavgHTD': float_column,
        'mean_abs_err_hourlyavgHTD': float_column,
        'mean_abs_pct_err_hourlyavgHTD': float_column,
        'total_auxiliary_heating_runtime': float_column,
        'total_emergency_heating_runtime': float_column,
        'total_heating_runtime': float_column,
        'total_cooling_runtime': float_column,
        'actual_daily_runtime': float_column,
        'actual_seasonal_runtime': float_column,
        'baseline_comfort_temperature': float_column,
        'rhu_00F_to_05F': float_column,
        'rhu_05F_to_10F': float_column,
        'rhu_10F_to_15F': float_column,
        'rhu_15F_to_20F': float_column,
        'rhu_20F_to_25F': float_column,
        'rhu_25F_to_30F': float_column,
        'rhu_30F_to_35F': float_column,
        'rhu_35F_to_40F': float_column,
        'rhu_40F_to_45F': float_column,
        'rhu_45F_to_50F': float_column,
        'rhu_50F_to_55F': float_column,
        'rhu_55F_to_60F': float_column,

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

@pytest.fixture
def zipcode_group_spec_csv_filepath():
    _, fname = tempfile.mkstemp()
    with open(fname, 'w') as f:
        file_contents = \
                "zipcode,group\n" \
                "01234,group_a\n" \
                "12345,group_a\n" \
                "23456,group_a\n" \
                "43210,group_b\n" \
                "54321,group_b\n" \
                "65432,group_c"
        f.write(file_contents)
    return fname

@pytest.fixture
def zipcode_group_spec_dict():
    dictionary = {
        "01234": "group_a",
        "12345": "group_a",
        "23456": "group_a",
        "43210": "group_b",
        "54321": "group_b",
        "65432": "group_c",
    }
    return dictionary

@pytest.fixture
def zipcode_group_spec():
    dictionary = {
        "01234": "group_a",
        "12345": "group_a",
        "23456": "group_a",
        "43210": "group_b",
        "54321": "group_b",
        "65432": "group_c",
    }
    return ZipcodeGroupSpec(dictionary=dictionary)

@pytest.fixture
def groups_df():
    df = pd.DataFrame({
        "zipcode": [
            "01234",
            "12345",
            "23456",
            "23456",
            "43210",
            "54321",
            "65432",
            "76543"],
        "value": [ 1, 2, 3, 4, 5, 6, 7, 8],
        }, columns=["zipcode", "value"])
    return df

def test_combine_output_dataframes(dataframes):
    combined = combine_output_dataframes(dataframes)
    assert combined.shape == (20, 98)

def test_compute_summary_statistics(combined_dataframe):
    summary_statistics = compute_summary_statistics(combined_dataframe, "label")
    assert len(summary_statistics) == 2
    assert len(summary_statistics[0]) == 12 * 64 + 5
    assert len(summary_statistics[1]) == 12 * 50 + 5
    assert summary_statistics[0]["label"] == "label_heating"
    for key, value in summary_statistics[0].items():
        if key not in ["label"]:
            assert pd.notnull(value)
            assert not np.isinf(value)

def test_summary_statistics_to_csv(combined_dataframe):
    summary_statistics = compute_summary_statistics(combined_dataframe, "label")

    _, fname = tempfile.mkstemp()
    stats_df = summary_statistics_to_csv(summary_statistics, fname)
    assert isinstance(stats_df, pd.DataFrame)

    with open(fname, 'r') as f:
        columns = f.readline().split(",")
        assert len(columns) == 12 * 93 + 15

def test_zipcode_group_spec_csv(zipcode_group_spec_csv_filepath, groups_df):
    group_spec = ZipcodeGroupSpec(filepath=zipcode_group_spec_csv_filepath)
    groups = dict([i for i in group_spec.iter_groups(groups_df)])
    assert len(groups) == 3
    assert len(groups["group_a"]) == 4
    assert len(groups["group_b"]) == 2
    assert len(groups["group_c"]) == 1

def test_zipcode_group_spec_dict(zipcode_group_spec_dict, groups_df):
    group_spec = ZipcodeGroupSpec(dictionary=zipcode_group_spec_dict)
    groups = dict([i for i in group_spec.iter_groups(groups_df)])
    assert len(groups) == 3
    assert len(groups["group_a"]) == 4
    assert len(groups["group_b"]) == 2
    assert len(groups["group_c"]) == 1

def test_compute_summary_statistics_by_zipcode_group(combined_dataframe, zipcode_group_spec):
    _, fname = tempfile.mkstemp()

    weights = {
        "heating": {
            "Group 1": {
                "components": [
                    "group_a",
                    "group_b",
                ],
                "weight": 0.4,
            },
            "Group 2": {
                "components": [
                    "group_c",
                ],
                "weight": 0.6,
            }
        },
        "cooling": {
            "Group 1": {
                "components": [
                    "group_a",
                ],
                "weight": 1.,
            },
            "Group 2": {
                "components": [
                    "group_b",
                    "group_c",
                ],
                "weight": 2.,
            }
        }
    }

    with open(fname, 'w') as f:
        json.dump(weights, f)

    stats = compute_summary_statistics_by_zipcode_group(combined_dataframe,
            group_spec=zipcode_group_spec, weights=fname)

    assert len(stats) == 8
    assert stats[0]["label"] == "group_a_heating"
    assert stats[7]["label"] == "national_cooling"

    stats = compute_summary_statistics_by_zipcode_group(combined_dataframe,
            group_spec=zipcode_group_spec)

    assert len(stats) == 6
    assert stats[0]["label"] == "group_a_heating"

def test_compute_summary_statistics_by_zipcode(combined_dataframe):
    stats = compute_summary_statistics_by_zipcode(combined_dataframe)
    assert len(stats) == 6
    assert stats[0]["label"] == "23456_heating"

def test_compute_summary_statistics_by_weather_station(combined_dataframe):
    stats = compute_summary_statistics_by_weather_station(combined_dataframe)
    assert len(stats) == 6
    assert stats[0]["label"] == "722575_heating"

def test_zipcode_group_spec_no_input():
    with pytest.raises(ValueError):
        group_spec = ZipcodeGroupSpec()
