import pandas as pd
import numpy as np
from scipy.stats import norm

from eemeter.location import _load_zipcode_to_lat_lng_index
from eemeter.location import _load_zipcode_to_station_index

from collections import OrderedDict
from collections import defaultdict
from itertools import chain
from warnings import warn
import json
from functools import reduce
from pkg_resources import resource_stream

from thermostat import get_version

REAL_OR_INTEGER_VALUED_COLUMNS_HEATING = [
    'n_days_in_inputfile_date_range',
    'n_days_both_heating_and_cooling',
    'n_days_insufficient_data',
    'n_core_heating_days',

    'baseline90_core_heating_comfort_temperature',
    'regional_average_baseline_heating_comfort_temperature',

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

    'total_core_heating_runtime',
    'total_auxiliary_heating_core_day_runtime',
    'total_emergency_heating_core_day_runtime',

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

REAL_OR_INTEGER_VALUED_COLUMNS_COOLING = [
    'n_days_in_inputfile_date_range',
    'n_days_both_heating_and_cooling',
    'n_days_insufficient_data',
    'n_core_cooling_days',

    'baseline10_core_cooling_comfort_temperature',
    'regional_average_baseline_cooling_comfort_temperature',

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

    'total_core_cooling_runtime',

    'daily_mean_core_cooling_runtime',
]

REAL_OR_INTEGER_VALUED_COLUMNS_ALL = [
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


def _get_method(heating_or_cooling, target_demand_method, target_baseline_method=None):
    if heating_or_cooling == "heating":
        if target_demand_method == "deltaT":
            method = "deltaT_heating"
        else:
            method = "{}HTD".format(target_demand_method)

        if target_baseline_method == "baseline_percentile":
            method += "_baseline90"
        elif target_baseline_method == "baseline_regional":
            method += "_baseline_regional"
    else:
        if target_demand_method == "deltaT":
            method = "deltaT_cooling"
        else:
            method = "{}CTD".format(target_demand_method)

        if target_baseline_method == "baseline_percentile":
            method += "_baseline10"
        elif target_baseline_method == "baseline_regional":
            method += "_baseline_regional"
    return method


def get_filtered_stats(
        df, row_filter, label,
        statistical_power_confidence, statistical_power_ratio,
        heating_or_cooling, target_columns,
        target_demand_method, target_baseline_method):

    def _statistical_power_estimate(
            stats, statistical_power_confidence, statistical_power_ratio,
            heating_or_cooling, target_demand_method, target_baseline_method):

        method = _get_method(heating_or_cooling, target_demand_method, target_baseline_method)

        stat_power_target_mean = "percent_savings_{}_mean".format(method)
        stat_power_target_sem = "percent_savings_{}_sem".format(method)
        stat_power_target_n = "percent_savings_{}_n".format(method)

        mean = stats[stat_power_target_mean]
        sem = stats[stat_power_target_sem]
        n = stats[stat_power_target_n]

        n_std_devs = norm.ppf(1 - (1 - statistical_power_confidence)/2)
        std = sem * (n**.5)
        target_interval = mean * statistical_power_ratio
        target_n = (std * n_std_devs / target_interval) ** 2.
        return target_n

    n_rows_total = df.shape[0]

    filtered_df = df[[row_filter(row, df) for i, row in df.iterrows()]]

    n_rows_kept = filtered_df.shape[0]
    n_rows_discarded = n_rows_total - n_rows_kept

    stats = OrderedDict()
    stats["label"] = "{}_{}".format(label, heating_or_cooling)
    stats["sw_version"] = get_version()
    stats["n_thermostat_core_day_sets_total"] = n_rows_total
    stats["n_thermostat_core_day_sets_kept"] = n_rows_kept
    stats["n_thermostat_core_day_sets_discarded"] = n_rows_discarded

    if n_rows_total > 0:

        quantiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]

        for column_name in target_columns:
            column = filtered_df[column_name].replace([np.inf, -np.inf], np.nan).dropna()

            # calculate quantiles and statistics
            mean = np.nanmean(column)
            sem = np.nanstd(column) / (column.count() ** .5)
            lower_bound = mean - (1.96 * sem)
            upper_bound = mean + (1.96 * sem)
            stats["{}_n".format(column_name)] = column.count()
            stats["{}_upper_bound_95_perc_conf".format(column_name)] = upper_bound
            stats["{}_mean".format(column_name)] = mean
            stats["{}_lower_bound_95_perc_conf".format(column_name)] = lower_bound
            stats["{}_sem".format(column_name)] = sem

            for quantile in quantiles:
                stats["{}_q{}".format(column_name, quantile)] = column.quantile(quantile / 100.)

        stats["n_enough_statistical_power"] = _statistical_power_estimate(
                stats, statistical_power_confidence, statistical_power_ratio,
                heating_or_cooling, target_demand_method, target_baseline_method)

        return [stats]
    else:
        warn(
            "Not enough data to compute summary_statistics ({}_{})"
            .format(label, heating_or_cooling)
        )
        return []


def compute_summary_statistics(
        metrics_df,
        target_demand_method="dailyavg",
        target_baseline_method="baseline_percentile",
        target_error_metric="CVRMSE",
        target_error_max_value=np.inf,
        statistical_power_confidence=.95,
        statistical_power_ratio=.05):
    """ Computes summary statistics for the output dataframe. Computes the
    following statistics for each real-valued or integer valued column in
    the output dataframe: mean, standard error of the mean, and deciles.

    Parameters
    ----------
    df : pd.DataFrame
        Output for which to compute summary statistics.
    label : str
        Name for this set of thermostat outputs.
    target_demand_method : {"dailyavg", "hourlyavg", "deltaT"}, default "dailyavg"
        Demand metric method by which samples will be filtered according to bad fits, and
        for which statistical power extrapolation is desired.
    target_baseline_method : {"baseline_percentile", "baseline_regional"}, default "baseline_percentile"
        Baselining method by which samples will be filtered according to bad fits, and
        for which statistical power extrapolation is desired.
    target_error_metric : {"MSE", "RMSE", "CVRMSE", "MAE", "MAPE"}, default "CVRMSE"
        Error metric to use when determining thermostat-core-day-set inclusion in
        statistics output.
    target_error_max_value : float, default np.inf
        Maximum acceptable value for error metric defined by target_error_metric.
    statistical_power_confidence : float in range 0 to 1, default .95
        Confidence interval to use in estimated statistical power calculation.
    statistical_power_ratio : float in range 0 to 1, default .05
        Ratio of standard error to mean desired in statistical power calculation.

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
          - number of non-null core day sets: ###_n

        The following general values are also output:

          - label: label
          - number of total core day sets: n_total_core_day_sets

    """

    if target_demand_method not in ["dailyavg", "hourlyavg", "deltaT"]:
        message = 'Demand method not supported - please use one of "dailyavg",' \
                '"hourlyavg", or "deltaT"'
        raise ValueError(message)

    if target_baseline_method not in ["baseline_percentile", "baseline_regional"]:
        message = 'Baseline method not supported - please use one of "baseline_percentile",' \
                '"baseline_regional"'
        raise ValueError(message)

    def _identity_filter(row, df):
        return True

    def _range_filter(row, column_name, heating_or_cooling, lower_bound=-np.inf, upper_bound=np.inf, target_baseline=False):
        if target_baseline:
            method = _get_method(heating_or_cooling, target_demand_method, target_baseline_method)
        else:
            method = _get_method(heating_or_cooling, target_demand_method)
        full_column_selector = "{}_{}".format(column_name, method)
        column_value = row[full_column_selector]
        return lower_bound < column_value < upper_bound

    def _percentile_range_filter(row, column_name, heating_or_cooling, df, quantile=0.0, target_baseline=False):
        if target_baseline:
            method = _get_method(heating_or_cooling, target_demand_method, target_baseline_method)
        else:
            method = _get_method(heating_or_cooling, target_demand_method)
        full_column_selector = "{}_{}".format(column_name, method)
        lower_bound = df[full_column_selector].dropna().quantile(0.0 + quantile)
        upper_bound = df[full_column_selector].dropna().quantile(1.0 - quantile)
        return _range_filter(row, column_name, heating_or_cooling, lower_bound, upper_bound, target_baseline)

    def _tau_filter_heating(row, df):
        return _range_filter(row, "tau", "heating", 0, 25)

    def _tau_filter_cooling(row, df):
        return _range_filter(row, "tau", "cooling", 0, 25)

    def _cvrmse_filter_heating(row, df):
        return _range_filter(row, "cv_root_mean_sq_err", "heating", upper_bound=0.6)

    def _cvrmse_filter_cooling(row, df):
        return _range_filter(row, "cv_root_mean_sq_err", "cooling", upper_bound=0.6)

    def _savings_filter_p01_heating(row, df):
        return _percentile_range_filter(row, "percent_savings", "heating", df, 0.01, True)

    def _savings_filter_p01_cooling(row, df):
        return _percentile_range_filter(row, "percent_savings", "cooling", df, 0.01, True)

    def _savings_filter_p02_heating(row, df):
        return _percentile_range_filter(row, "percent_savings", "heating", df, 0.02, True)

    def _savings_filter_p02_cooling(row, df):
        return _percentile_range_filter(row, "percent_savings", "cooling", df, 0.02, True)

    def _savings_filter_p05_heating(row, df):
        return _percentile_range_filter(row, "percent_savings", "heating", df, 0.05, True)

    def _savings_filter_p05_cooling(row, df):
        return _percentile_range_filter(row, "percent_savings", "cooling", df, 0.05, True)

    def _combine_filters(filters):
        def _new_filter(row, df):
            return reduce(lambda x, y: x and y(row, df), filters, True)
        return _new_filter

    def heating_stats(df, filter_, label):
        heating_df = df[["heating" in name for name in df["heating_or_cooling"]]]
        return get_filtered_stats(
            heating_df, filter_, label,
            statistical_power_confidence, statistical_power_ratio,
            "heating", REAL_OR_INTEGER_VALUED_COLUMNS_HEATING,
            target_demand_method, target_baseline_method)

    def cooling_stats(df, filter_, label):
        cooling_df = df[["cooling" in name for name in df["heating_or_cooling"]]]
        return get_filtered_stats(
            cooling_df, filter_, label,
            statistical_power_confidence, statistical_power_ratio,
            "cooling", REAL_OR_INTEGER_VALUED_COLUMNS_COOLING,
            target_demand_method, target_baseline_method)

    very_cold_cold_df = metrics_df[[
        (cz is not None) and "Very-Cold/Cold" in cz
        for cz in metrics_df["climate_zone"]
    ]]
    mixed_humid_df = metrics_df[[
        (cz is not None) and "Mixed-Humid" in cz
        for cz in metrics_df["climate_zone"]
    ]]
    mixed_dry_hot_dry_df = metrics_df[[
        (cz is not None) and "Mixed-Dry/Hot-Dry" in cz
        for cz in metrics_df["climate_zone"]
    ]]
    hot_humid_df = metrics_df[[
        (cz is not None) and "Hot-Humid" in cz
        for cz in metrics_df["climate_zone"]
    ]]
    marine_df = metrics_df[[
        (cz is not None) and "Marine" in cz
        for cz in metrics_df["climate_zone"]
    ]]

    filter_0 = _identity_filter
    filter_1_heating = _combine_filters([_tau_filter_heating])
    filter_1_cooling = _combine_filters([_tau_filter_cooling])
    filter_2_heating = _combine_filters([_tau_filter_heating, _cvrmse_filter_heating])
    filter_2_cooling = _combine_filters([_tau_filter_cooling, _cvrmse_filter_cooling])
    filter_3_heating = _combine_filters([_tau_filter_heating, _cvrmse_filter_heating, _savings_filter_p01_heating])
    filter_3_cooling = _combine_filters([_tau_filter_cooling, _cvrmse_filter_cooling, _savings_filter_p01_cooling])
    filter_4_heating = _combine_filters([_tau_filter_heating, _cvrmse_filter_heating, _savings_filter_p02_heating])
    filter_4_cooling = _combine_filters([_tau_filter_cooling, _cvrmse_filter_cooling, _savings_filter_p02_cooling])
    filter_5_heating = _combine_filters([_tau_filter_heating, _cvrmse_filter_heating, _savings_filter_p05_heating])
    filter_5_cooling = _combine_filters([_tau_filter_cooling, _cvrmse_filter_cooling, _savings_filter_p05_cooling])

    stats = list(chain.from_iterable([
        heating_stats(metrics_df, filter_0, "all_no_filter"),
        cooling_stats(metrics_df, filter_0, "all_no_filter"),
        heating_stats(very_cold_cold_df, filter_0, "very-cold_cold_no_filter"),
        cooling_stats(very_cold_cold_df, filter_0, "very-cold_cold"),
        heating_stats(mixed_humid_df, filter_0, "mixed-humid_no_filter"),
        cooling_stats(mixed_humid_df, filter_0, "mixed-humid_no_filter"),
        heating_stats(mixed_dry_hot_dry_df, filter_0, "mixed-dry_hot-dry_no_filter"),
        cooling_stats(mixed_dry_hot_dry_df, filter_0, "mixed-dry_hot-dry_no_filter"),
        heating_stats(hot_humid_df, filter_0, "hot-humid_no_filter"),
        cooling_stats(hot_humid_df, filter_0, "hot-humid_no_filter"),
        heating_stats(marine_df, filter_0, "marine_no_filter"),
        cooling_stats(marine_df, filter_0, "marine_no_filter"),

        heating_stats(metrics_df, filter_1_heating, "all_tau_filter"),
        cooling_stats(metrics_df, filter_1_cooling, "all_tau_filter"),
        heating_stats(very_cold_cold_df, filter_1_heating, "very-cold_cold_tau_filter"),
        cooling_stats(very_cold_cold_df, filter_1_cooling, "very-cold_cold_tau_filter"),
        heating_stats(mixed_humid_df, filter_1_heating, "mixed-humid_tau_filter"),
        cooling_stats(mixed_humid_df, filter_1_cooling, "mixed-humid_tau_filter"),
        heating_stats(mixed_dry_hot_dry_df, filter_1_heating, "mixed-dry_hot-dry_tau_filter"),
        cooling_stats(mixed_dry_hot_dry_df, filter_1_cooling, "mixed-dry_hot-dry_tau_filter"),
        heating_stats(hot_humid_df, filter_1_heating, "hot-humid_tau_filter"),
        cooling_stats(hot_humid_df, filter_1_cooling, "hot-humid_tau_filter"),
        heating_stats(marine_df, filter_1_heating, "marine_tau_filter"),
        cooling_stats(marine_df, filter_1_cooling, "marine_tau_filter"),

        heating_stats(metrics_df, filter_2_heating, "all_tau_cvrmse_filter"),
        cooling_stats(metrics_df, filter_2_cooling, "all_tau_cvrmse_filter"),
        heating_stats(very_cold_cold_df, filter_2_heating, "very-cold_cold_tau_cvrmse_filter"),
        cooling_stats(very_cold_cold_df, filter_2_cooling, "very-cold_cold_tau_cvrmse_filter"),
        heating_stats(mixed_humid_df, filter_2_heating, "mixed-humid_tau_cvrmse_filter"),
        cooling_stats(mixed_humid_df, filter_2_cooling, "mixed-humid_tau_cvrmse_filter"),
        heating_stats(mixed_dry_hot_dry_df, filter_2_heating, "mixed-dry_hot-dry_tau_cvrmse_filter"),
        cooling_stats(mixed_dry_hot_dry_df, filter_2_cooling, "mixed-dry_hot-dry_tau_cvrmse_filter"),
        heating_stats(hot_humid_df, filter_2_heating, "hot-humid_tau_cvrmse_filter"),
        cooling_stats(hot_humid_df, filter_2_cooling, "hot-humid_tau_cvrmse_filter"),
        heating_stats(marine_df, filter_2_heating, "marine_tau_cvrmse_filter"),
        cooling_stats(marine_df, filter_2_cooling, "marine_tau_cvrmse_filter"),

        heating_stats(metrics_df, filter_3_heating, "all_tau_cvrmse_savings_p01_filter"),
        cooling_stats(metrics_df, filter_3_cooling, "all_tau_cvrmse_savings_p01_filter"),
        heating_stats(very_cold_cold_df, filter_3_heating, "very-cold_cold_tau_cvrmse_savings_p01_filter"),
        cooling_stats(very_cold_cold_df, filter_3_cooling, "very-cold_cold_tau_cvrmse_savings_p01_filter"),
        heating_stats(mixed_humid_df, filter_3_heating, "mixed-humid_tau_cvrmse_savings_p01_filter"),
        cooling_stats(mixed_humid_df, filter_3_cooling, "mixed-humid_tau_cvrmse_savings_p01_filter"),
        heating_stats(mixed_dry_hot_dry_df, filter_3_heating, "mixed-dry_hot-dry_tau_cvrmse_savings_p01_filter"),
        cooling_stats(mixed_dry_hot_dry_df, filter_3_cooling, "mixed-dry_hot-dry_tau_cvrmse_savings_p01_filter"),
        heating_stats(hot_humid_df, filter_3_heating, "hot-humid_tau_cvrmse_savings_p01_filter"),
        cooling_stats(hot_humid_df, filter_3_cooling, "hot-humid_tau_cvrmse_savings_p01_filter"),
        heating_stats(marine_df, filter_3_heating, "marine_tau_cvrmse_savings_p01_filter"),
        cooling_stats(marine_df, filter_3_cooling, "marine_tau_cvrmse_savings_p01_filter"),

        heating_stats(metrics_df, filter_4_heating, "all_tau_cvrmse_savings_p02_filter"),
        cooling_stats(metrics_df, filter_4_cooling, "all_tau_cvrmse_savings_p02_filter"),
        heating_stats(very_cold_cold_df, filter_4_heating, "very-cold_cold_tau_cvrmse_savings_p02_filter"),
        cooling_stats(very_cold_cold_df, filter_4_cooling, "very-cold_cold_tau_cvrmse_savings_p02_filter"),
        heating_stats(mixed_humid_df, filter_4_heating, "mixed-humid_tau_cvrmse_savings_p02_filter"),
        cooling_stats(mixed_humid_df, filter_4_cooling, "mixed-humid_tau_cvrmse_savings_p02_filter"),
        heating_stats(mixed_dry_hot_dry_df, filter_4_heating, "mixed-dry_hot-dry_tau_cvrmse_savings_p02_filter"),
        cooling_stats(mixed_dry_hot_dry_df, filter_4_cooling, "mixed-dry_hot-dry_tau_cvrmse_savings_p02_filter"),
        heating_stats(hot_humid_df, filter_4_heating, "hot-humid_tau_cvrmse_savings_p02_filter"),
        cooling_stats(hot_humid_df, filter_4_cooling, "hot-humid_tau_cvrmse_savings_p02_filter"),
        heating_stats(marine_df, filter_4_heating, "marine_tau_cvrmse_savings_p02_filter"),
        cooling_stats(marine_df, filter_4_cooling, "marine_tau_cvrmse_savings_p02_filter"),

        heating_stats(metrics_df, filter_5_heating, "all_tau_cvrmse_savings_p05_filter"),
        cooling_stats(metrics_df, filter_5_cooling, "all_tau_cvrmse_savings_p05_filter"),
        heating_stats(very_cold_cold_df, filter_5_heating, "very-cold_cold_tau_cvrmse_savings_p05_filter"),
        cooling_stats(very_cold_cold_df, filter_5_cooling, "very-cold_cold_tau_cvrmse_savings_p05_filter"),
        heating_stats(mixed_humid_df, filter_5_heating, "mixed-humid_tau_cvrmse_savings_p05_filter"),
        cooling_stats(mixed_humid_df, filter_5_cooling, "mixed-humid_tau_cvrmse_savings_p05_filter"),
        heating_stats(mixed_dry_hot_dry_df, filter_5_heating, "mixed-dry_hot-dry_tau_cvrmse_savings_p05_filter"),
        cooling_stats(mixed_dry_hot_dry_df, filter_5_cooling, "mixed-dry_hot-dry_tau_cvrmse_savings_p05_filter"),
        heating_stats(hot_humid_df, filter_5_heating, "hot-humid_tau_cvrmse_savings_p05_filter"),
        cooling_stats(hot_humid_df, filter_5_cooling, "hot-humid_tau_cvrmse_savings_p05_filter"),
        heating_stats(marine_df, filter_5_heating, "marine_tau_cvrmse_savings_p05_filter"),
        cooling_stats(marine_df, filter_5_cooling, "marine_tau_cvrmse_savings_p05_filter"),
    ]))

    stats_dict = {stat["label"]: stat for stat in stats}

    def _load_climate_zone_weights(filename_or_buffer):
        climate_zone_keys = {
            "Very-Cold/Cold": "very-cold_cold",
            "Mixed-Humid": "mixed-humid",
            "Mixed-Dry/Hot-Dry": "mixed-dry_hot-dry",
            "Hot-Humid": "hot-humid",
            "Marine": "marine",
        }
        df = pd.read_csv(
            filename_or_buffer,
            usecols=["climate_zone", "heating_weight", "cooling_weight"],
        ).set_index("climate_zone")

        heating_weights = {climate_zone_keys[cz]: weight for cz, weight in df["heating_weight"].iteritems()}
        cooling_weights = {climate_zone_keys[cz]: weight for cz, weight in df["cooling_weight"].iteritems()}

        return heating_weights, cooling_weights

    with resource_stream('thermostat.resources', 'NationalAverageClimateZoneWeightings.csv') as f:
        heating_weights, cooling_weights = _load_climate_zone_weights(f)

    def _compute_national_weightings(stats_by_climate_zone, keys, weights):
        def _national_weight(key):
            results = []
            for cz, weight in weights.items():
                stat_cz = stats_by_climate_zone.get(cz)
                if stat_cz is None:
                    value = None
                else:
                    value = stat_cz.get(key)
                if pd.notnull(weight) and pd.notnull(value):
                    results.append((weight, value))
            if len(results) == 0:
                return None
            else:
                return sum([r[0] * r[1] for r in results]) / sum([r[0] for r in results])

        return {"{}_{}".format(key, "national_weighted_mean"): _national_weight(key) for key in keys}

    national_weighting_stats = []

    filters = [
        "no_filter",
        "tau_filter",
        "tau_cvrmse_filter",
        "tau_cvrmse_savings_p01_filter",
        "tau_cvrmse_savings_p02_filter",
        "tau_cvrmse_savings_p05_filter",
    ]
    climate_zones = [
        "mixed-humid",
        "mixed-dry_hot-dry",
        "marine",
        "hot-humid",
        "very-cold_cold"
    ]
    heating_methods = [
        "deltaT_heating_baseline90",
        "deltaT_heating_baseline_regional",
        "dailyavgHTD_baseline90",
        "dailyavgHTD_baseline_regional",
        "hourlyavgHTD_baseline90",
        "hourlyavgHTD_baseline_regional",
    ]
    cooling_methods = [
        "deltaT_cooling_baseline10",
        "deltaT_cooling_baseline_regional",
        "dailyavgCTD_baseline10",
        "dailyavgCTD_baseline_regional",
        "hourlyavgCTD_baseline10",
        "hourlyavgCTD_baseline_regional",
    ]
    for season_type in ["heating", "cooling"]:
        if season_type == "heating":
            weights = heating_weights
            methods = heating_methods
        else:
            weights = cooling_weights
            methods = cooling_methods

        for filter_ in filters:
            stats_by_climate_zone = {
                cz: stats_dict.get("{}_{}_{}".format(cz, filter_, season_type))
                for cz in climate_zones
            }

            keys = list(chain.from_iterable([
                ["percent_savings_{}_mean".format(method) for method in methods],
                ["percent_savings_{}_q50".format(method) for method in methods],
                ["percent_savings_{}_lower_bound_95_perc_conf".format(method) for method in methods],
            ]))

            national_weightings = _compute_national_weightings(
                stats_by_climate_zone, keys, weights)
            national_weightings.update({"label": "national_weighted_mean_{}".format(filter_)})
            national_weighting_stats.append(national_weightings)

    stats.extend(national_weighting_stats)

    return stats


def summary_statistics_to_csv(stats, filepath):
    """ Write metric statistics to CSV file.

    Parameters
    ----------
    stats : list of dict
        List of outputs from thermostat.stats.compute_summary_statistics()
    filepath : str
        Filepath at which to save the suppary statistics

    Returns
    -------
    df : pandas.DataFrame
        A pandas dataframe containing the output data.

    """
    quantiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    columns = [
        "label",
        "sw_version",
        "n_thermostat_core_day_sets_total",
        "n_thermostat_core_day_sets_kept",
        "n_thermostat_core_day_sets_discarded",
        "n_enough_statistical_power"
    ]
    for column_name in REAL_OR_INTEGER_VALUED_COLUMNS_ALL:
        columns.append("{}_n".format(column_name))
        columns.append("{}_upper_bound_95_perc_conf".format(column_name))
        columns.append("{}_mean".format(column_name))
        columns.append("{}_lower_bound_95_perc_conf".format(column_name))
        columns.append("{}_sem".format(column_name))
        for quantile in quantiles:
            columns.append("{}_q{}".format(column_name, quantile))

    methods = [
        "deltaT_heating_baseline90",
        "deltaT_heating_baseline_regional",
        "dailyavgHTD_baseline90",
        "dailyavgHTD_baseline_regional",
        "hourlyavgHTD_baseline90",
        "hourlyavgHTD_baseline_regional",
        "deltaT_cooling_baseline10",
        "deltaT_cooling_baseline_regional",
        "dailyavgCTD_baseline10",
        "dailyavgCTD_baseline_regional",
        "hourlyavgCTD_baseline10",
        "hourlyavgCTD_baseline_regional",
    ]
    national_weighting_columns = list(chain.from_iterable([
        [
            "percent_savings_{}_mean_national_weighted_mean".format(method),
            "percent_savings_{}_q50_national_weighted_mean".format(method),
            "percent_savings_{}_lower_bound_95_perc_conf_national_weighted_mean".format(method),
        ] for method in methods
    ]))

    columns.extend(national_weighting_columns)

    # transpose for readability.
    stats_dataframe = pd.DataFrame(stats, columns=columns).set_index('label').transpose()
    stats_dataframe.to_csv(filepath)
    return stats_dataframe
