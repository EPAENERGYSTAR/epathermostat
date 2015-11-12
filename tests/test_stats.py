from thermostat.stats import combine_output_dataframes
from thermostat.stats import compute_summary_statistics

from scipy.stats import norm, randint

import pandas as pd

import pytest

def get_fake_output_df(n_columns):
    columns = [
        "ct_identifier",
        "equipment_type",
        "season_name",
        "station",
        "zipcode",
        "n_days_both_heating_and_cooling",
        "n_days_insufficient_data",
        "n_days_in_season",
        "n_days_in_season_range",
        "slope_deltaT",
        "alpha_est_dailyavgCDD",
        "alpha_est_dailyavgHDD",
        "alpha_est_hourlyavgCDD",
        "alpha_est_hourlyavgHDD",
        "mean_sq_err_dailyavgCDD",
        "mean_sq_err_dailyavgHDD",
        "mean_sq_err_hourlyavgCDD",
        "mean_sq_err_hourlyavgHDD",
        "mean_squared_error_deltaT",
        "deltaT_base_est_dailyavgCDD",
        "deltaT_base_est_dailyavgHDD",
        "deltaT_base_est_hourlyavgCDD",
        "deltaT_base_est_hourlyavgHDD",
        "baseline_daily_runtime_deltaT",
        "baseline_daily_runtime_dailyavgCDD",
        "baseline_daily_runtime_dailyavgHDD",
        "baseline_daily_runtime_hourlyavgCDD",
        "baseline_daily_runtime_hourlyavgHDD",
        "baseline_seasonal_runtime_deltaT",
        "baseline_seasonal_runtime_dailyavgCDD",
        "baseline_seasonal_runtime_dailyavgHDD",
        "baseline_seasonal_runtime_hourlyavgCDD",
        "baseline_seasonal_runtime_hourlyavgHDD",
        "baseline_comfort_temperature",
        "actual_daily_runtime",
        "actual_seasonal_runtime",
        "seasonal_avoided_runtime_deltaT",
        "seasonal_avoided_runtime_dailyavgCDD",
        "seasonal_avoided_runtime_dailyavgHDD",
        "seasonal_avoided_runtime_hourlyavgCDD",
        "seasonal_avoided_runtime_hourlyavgHDD",
        "seasonal_savings_deltaT",
        "seasonal_savings_dailyavgCDD",
        "seasonal_savings_dailyavgHDD",
        "seasonal_savings_hourlyavgCDD",
        "seasonal_savings_hourlyavgHDD",
        "rhu_00F_to_05F",
        "rhu_05F_to_10F",
        "rhu_10F_to_15F",
        "rhu_15F_to_20F",
        "rhu_20F_to_25F",
        "rhu_25F_to_30F",
        "rhu_30F_to_35F",
        "rhu_35F_to_40F",
        "rhu_40F_to_45F",
        "rhu_45F_to_50F",
        "rhu_50F_to_55F",
        "rhu_55F_to_60F",
    ]

    string_placeholder = ["PLACEHOLDER"] * n_columns
    int_column = randint.rvs(0, 1, size=n_columns)
    float_column = norm.rvs(size=n_columns)
    data = {
        "ct_identifier": string_placeholder,
        "equipment_type": string_placeholder,
        "season_name": string_placeholder,
        "station": string_placeholder,
        "zipcode": string_placeholder,
        "n_days_both_heating_and_cooling": int_column,
        "n_days_insufficient_data": int_column,
        "n_days_in_season": int_column,
        "n_days_in_season_range": int_column,
        "slope_deltaT": float_column,
        "alpha_est_dailyavgCDD": float_column,
        "alpha_est_dailyavgHDD": float_column,
        "alpha_est_hourlyavgCDD": float_column,
        "alpha_est_hourlyavgHDD": float_column,
        "mean_sq_err_dailyavgCDD": float_column,
        "mean_sq_err_dailyavgHDD": float_column,
        "mean_sq_err_hourlyavgCDD": float_column,
        "mean_sq_err_hourlyavgHDD": float_column,
        "mean_squared_error_deltaT": float_column,
        "deltaT_base_est_dailyavgCDD": float_column,
        "deltaT_base_est_dailyavgHDD": float_column,
        "deltaT_base_est_hourlyavgCDD": float_column,
        "deltaT_base_est_hourlyavgHDD": float_column,
        "baseline_daily_runtime_deltaT": float_column,
        "baseline_daily_runtime_dailyavgCDD": float_column,
        "baseline_daily_runtime_dailyavgHDD": float_column,
        "baseline_daily_runtime_hourlyavgCDD": float_column,
        "baseline_daily_runtime_hourlyavgHDD": float_column,
        "baseline_seasonal_runtime_deltaT": float_column,
        "baseline_seasonal_runtime_dailyavgCDD": float_column,
        "baseline_seasonal_runtime_dailyavgHDD": float_column,
        "baseline_seasonal_runtime_hourlyavgCDD": float_column,
        "baseline_seasonal_runtime_hourlyavgHDD": float_column,
        "baseline_comfort_temperature": float_column,
        "actual_daily_runtime": float_column,
        "actual_seasonal_runtime": float_column,
        "seasonal_avoided_runtime_deltaT": float_column,
        "seasonal_avoided_runtime_dailyavgCDD": float_column,
        "seasonal_avoided_runtime_dailyavgHDD": float_column,
        "seasonal_avoided_runtime_hourlyavgCDD": float_column,
        "seasonal_avoided_runtime_hourlyavgHDD": float_column,
        "seasonal_savings_deltaT": float_column,
        "seasonal_savings_dailyavgCDD": float_column,
        "seasonal_savings_dailyavgHDD": float_column,
        "seasonal_savings_hourlyavgCDD": float_column,
        "seasonal_savings_hourlyavgHDD": float_column,
        "rhu_00F_to_05F": float_column,
        "rhu_05F_to_10F": float_column,
        "rhu_10F_to_15F": float_column,
        "rhu_15F_to_20F": float_column,
        "rhu_20F_to_25F": float_column,
        "rhu_25F_to_30F": float_column,
        "rhu_30F_to_35F": float_column,
        "rhu_35F_to_40F": float_column,
        "rhu_40F_to_45F": float_column,
        "rhu_45F_to_50F": float_column,
        "rhu_50F_to_55F": float_column,
        "rhu_55F_to_60F": float_column,
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
    assert combined.shape == (20, 58)

def test_compute_summary_statistics(combined_dataframe):
    summary_statistics = compute_summary_statistics(combined_dataframe)
    assert len(summary_statistics) == 11 * 53
