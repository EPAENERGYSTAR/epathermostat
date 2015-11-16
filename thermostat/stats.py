import pandas as pd
import numpy as np

from collections import OrderedDict

REAL_OR_INTEGER_VALUED_COLUMNS = [
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

def combine_output_dataframes(dfs):
    """ Combines output dataframes. Useful when combining output from batches.

    Parameters
    ----------
    dfs : list of pd.DataFrame
        Output dataFrames to combine into one.

    Returns
    -------
    out : pd.DataFrame
        Dataframe with combined output metadata.

    """
    return pd.concat(dfs, ignore_index=True)

def compute_summary_statistics(df, label):
    """ Computes summary statistics for the output dataframe. Computes the
    following statistics for each real-valued or integer valued column in
    the output dataframe: mean, standard error of the mean, 10th, 20th, 30th,
    40th, 50th, 60th, 70th, 80th, and 90th percentiles.

    Parameters
    ----------
    df : pd.DataFrame
        Output for which to compute summary statistics.
    label : str
        Name for this set of thermostat outputs.

    Returns
    -------
    stats : collections.OrderedDict
        An ordered dict containing the summary statistics. Column names are as
        follows, in which ### is a placeholder for the name of the column:

          - mean: ###_mean
          - standard error of the mean: ###_sem
          - 10th quantile: ###_10q
          - 20th quantile: ###_20q
          - 30th quantile: ###_30q
          - 40th quantile: ###_40q
          - 50th quantile: ###_50q
          - 60th quantile: ###_60q
          - 70th quantile: ###_70q
          - 80th quantile: ###_80q
          - 90th quantile: ###_90q

    """
    quantiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]

    stats = OrderedDict()
    stats["label"] = label
    for column_name in REAL_OR_INTEGER_VALUED_COLUMNS:
        column = df[column_name]

        # calculate quantiles
        stats["{}_mean".format(column_name)] = np.nanmean(column)
        stats["{}_sem".format(column_name)] = np.nanstd(column) / (column.count() ** .5)
        for quantile in quantiles:
            stats["{}_q{}".format(column_name, quantile)] = column.quantile(quantile / 100.)

    return stats

def summary_statistics_to_csv(stats, filepath):
    """ Write metric statistics to CSV file.

    Parameters
    ----------
    stats : list of dict
        List of outputs from thermostat.stats.compute_summary_statistics()

    """
    quantiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    columns = ["label"]
    for column_name in REAL_OR_INTEGER_VALUED_COLUMNS:
        columns.append("{}_mean".format(column_name))
        columns.append("{}_sem".format(column_name))
        for quantile in quantiles:
            columns.append("{}_q{}".format(column_name, quantile))

    stats_dataframe = pd.DataFrame(stats, columns=columns)
    stats_dataframe.to_csv(filepath, index=False, columns=columns)
    return stats_dataframe
