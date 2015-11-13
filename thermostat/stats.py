import pandas as pd
import numpy as np
import scipy as sp

from collections import OrderedDict

def combine_output_dataframes(dfs):
    return pd.concat(dfs, ignore_index=True)

def compute_summary_statistics(df):
    relevant_column_names = [
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
    stats = OrderedDict()
    for column_name in relevant_column_names:
        column = df[column_name]

        # calculate quantiles
        quantiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]
        stats["{}_mean".format(column_name)] = np.nanmean(column)
        stats["{}_sem".format(column_name)] = sp.stats.sem(column)
        for quantile in quantiles:
            q_val = np.percentile(column, quantile)
            stats["{}_q{}".format(column_name, quantile)] = q_val

    return stats
