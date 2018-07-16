import pandas as pd
import numpy as np
from scipy.stats import norm

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

    'baseline_percentile_core_heating_comfort_temperature',
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

    'total_core_heating_runtime',
    'total_auxiliary_heating_core_day_runtime',
    'total_emergency_heating_core_day_runtime',

    'daily_mean_core_heating_runtime',

    'core_heating_days_mean_indoor_temperature',
    'core_heating_days_mean_outdoor_temperature',
    'core_mean_indoor_temperature',
    'core_mean_outdoor_temperature',

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

    'baseline_percentile_core_cooling_comfort_temperature',
    'regional_average_baseline_cooling_comfort_temperature',

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

    'daily_mean_core_cooling_runtime',

    'core_cooling_days_mean_indoor_temperature',
    'core_cooling_days_mean_outdoor_temperature',
    'core_mean_indoor_temperature',
    'core_mean_outdoor_temperature',
]

REAL_OR_INTEGER_VALUED_COLUMNS_ALL = [
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

    'core_mean_indoor_temperature',
    'core_mean_outdoor_temperature',

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

def get_filtered_stats(
        df, row_filter, label, heating_or_cooling, target_columns,
        target_baseline_method):

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

            for quantile in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
                stats["{}_q{}".format(column_name, quantile)] = column.quantile(quantile / 100.)

        return [stats]
    else:
        warn(
            "Not enough data to compute summary_statistics ({}_{})"
            .format(label, heating_or_cooling)
        )
        return []


def compute_summary_statistics(
        metrics_df,
        target_baseline_method="baseline_percentile",
        advanced_filtering=False):
    """ Computes summary statistics for the output dataframe. Computes the
    following statistics for each real-valued or integer valued column in
    the output dataframe: mean, standard error of the mean, and deciles.

    Parameters
    ----------
    df : pd.DataFrame
        Output for which to compute summary statistics.
    label : str
        Name for this set of thermostat outputs.
    target_baseline_method : {"baseline_percentile", "baseline_regional"}, default "baseline_percentile"
        Baselining method by which samples will be filtered according to bad fits.

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

    if target_baseline_method not in ["baseline_percentile", "baseline_regional"]:
        message = (
            'Baseline method not supported - please use one of'
            ' "baseline_percentile" or "baseline_regional"'
        )
        raise ValueError(message)

    def _identity_filter(row, df):
        return True

    def _range_filter(row, column_name, heating_or_cooling, lower_bound=-np.inf, upper_bound=np.inf, target_baseline=False):
        if target_baseline:
            full_column_selector = "{}_{}".format(column_name, target_baseline_method)
        else:
            full_column_selector = column_name
        column_value = row[full_column_selector]
        return lower_bound < column_value < upper_bound

    def _percentile_range_filter(row, column_name, heating_or_cooling, df, quantile=0.0, target_baseline=False):
        if target_baseline:
            full_column_selector = "{}_{}".format(column_name, target_baseline_method)
        else:
            full_column_selector = column_name
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

    def _combine_filters(filters):
        def _new_filter(row, df):
            return reduce(lambda x, y: x and y(row, df), filters, True)
        return _new_filter

    def heating_stats(df, filter_, label):
        heating_df = df[["heating" in name for name in df["heating_or_cooling"]]]
        return get_filtered_stats(
            heating_df, filter_, label,
            "heating", REAL_OR_INTEGER_VALUED_COLUMNS_HEATING,
            target_baseline_method)

    def cooling_stats(df, filter_, label):
        cooling_df = df[["cooling" in name for name in df["heating_or_cooling"]]]
        return get_filtered_stats(
            cooling_df, filter_, label,
            "cooling", REAL_OR_INTEGER_VALUED_COLUMNS_COOLING,
            target_baseline_method)

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

    if advanced_filtering:
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
        ]))
    else:
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
                weighted_sum = sum([weight * value for weight, value in results])
                sum_of_weights = sum([weight for weight, _ in results])
                return weighted_sum / sum_of_weights

        stats = [
            "mean",
            "q10",
            "q20",
            "q30",
            "q40",
            "q50",
            "q60",
            "q70",
            "q80",
            "q90",
        ]

        key_stats = [
            "{}_{}".format(key, stat)
            for key in keys for stat in stats
        ]

        return {
            "{}_{}".format(key_stat, "national_weighted_mean"): _national_weight(key_stat)
            for key_stat in key_stats
        }

    def _compute_national_weighting_lower_and_upper_bounds(
            stats_by_climate_zone, keys, weights):

        def _compute_bounds(key):

            # compute sem savings
            means, sems, weights_ = [], [], []
            for cz, weight in weights.items():
                stat_cz = stats_by_climate_zone.get(cz)
                if stat_cz is None:
                    mean, sem = None, None
                else:
                    mean = stat_cz.get("{}_mean".format(key), None)
                    sem = stat_cz.get("{}_sem".format(key), None)

                if pd.notnull(weight) and pd.notnull(mean) and pd.notnull(sem):
                    weights_.append(weight)
                    means.append(mean)
                    sems.append(sem)

            if len(weights_) == 0:
                return {}
            else:
                weighted_sum = sum([
                    weight * mean for weight, mean in zip(weights_, means)
                ])
                weighted_mean = weighted_sum / sum(weights_)  # renormalize

                weighted_sem = sum([
                    (weight*sem) ** 2 for weight, sem in zip(weights_, sems)
                ]) ** 0.5

                lower_bound = weighted_mean - (1.96 * weighted_sem)
                upper_bound = weighted_mean + (1.96 * weighted_sem)

                return {
                    "{}_lower_bound_95_perc_conf_national_weighted_mean".format(key): lower_bound,
                    "{}_upper_bound_95_perc_conf_national_weighted_mean".format(key): upper_bound
                }

        items = {}
        for key in keys:
            items.update(_compute_bounds(key))
        return items

    national_weighting_stats = []

    if advanced_filtering:
        filters = [
            "no_filter",
            "tau_filter",
            "tau_cvrmse_filter",
            "tau_cvrmse_savings_p01_filter",
        ]
    else:
        filters = [
            "no_filter",
            "tau_cvrmse_savings_p01_filter",
        ]

    climate_zones = [
        "mixed-humid",
        "mixed-dry_hot-dry",
        "marine",
        "hot-humid",
        "very-cold_cold"
    ]
    methods = [
        "baseline_percentile",
        "baseline_regional",
    ]
    for season_type in ["heating", "cooling"]:
        if season_type == "heating":
            weights = heating_weights
        else:
            weights = cooling_weights

        for filter_ in filters:
            stats_by_climate_zone = {
                cz: stats_dict.get("{}_{}_{}".format(cz, filter_, season_type))
                for cz in climate_zones
            }

            keys = ["percent_savings_{}".format(method) for method in methods]

            national_weightings = _compute_national_weightings(
                stats_by_climate_zone, keys, weights)

            bounds = _compute_national_weighting_lower_and_upper_bounds(
                stats_by_climate_zone, keys, weights)
            national_weightings.update(bounds)

            national_weightings.update(
                {"label": "national_weighted_mean_{}_{}".format(season_type, filter_)}
            )

            national_weighting_stats.append(national_weightings)

    stats = national_weighting_stats + stats

    return stats


def summary_statistics_to_csv(stats, filepath, product_id):
    """ Write metric statistics to CSV file.

    Parameters
    ----------
    stats : list of dict
        List of outputs from thermostat.stats.compute_summary_statistics()
    filepath : str
        Filepath at which to save the suppary statistics
    product_id : str
        A combination of the connected thermostat service plus one or more
        connected thermostat device models that comprises the data set.

    Returns
    -------
    df : pandas.DataFrame
        A pandas dataframe containing the output data.

    """

    columns = [
        "label",
        "product_id",
        "sw_version",
    ]

    methods = [
        "baseline_percentile",
        "baseline_regional",
    ]

    national_weighting_columns = list(chain.from_iterable([
        [
            "percent_savings_{}_mean_national_weighted_mean".format(method),
            "percent_savings_{}_q10_national_weighted_mean".format(method),
            "percent_savings_{}_q20_national_weighted_mean".format(method),
            "percent_savings_{}_q30_national_weighted_mean".format(method),
            "percent_savings_{}_q40_national_weighted_mean".format(method),
            "percent_savings_{}_q50_national_weighted_mean".format(method),
            "percent_savings_{}_q60_national_weighted_mean".format(method),
            "percent_savings_{}_q70_national_weighted_mean".format(method),
            "percent_savings_{}_q80_national_weighted_mean".format(method),
            "percent_savings_{}_q90_national_weighted_mean".format(method),
            "percent_savings_{}_lower_bound_95_perc_conf_national_weighted_mean".format(method),
            "percent_savings_{}_upper_bound_95_perc_conf_national_weighted_mean".format(method),
        ] for method in methods
    ]))

    columns.extend(national_weighting_columns)

    columns.extend([
        "n_thermostat_core_day_sets_total",
        "n_thermostat_core_day_sets_kept",
        "n_thermostat_core_day_sets_discarded",
    ])
    for column_name in REAL_OR_INTEGER_VALUED_COLUMNS_ALL:
        columns.append("{}_n".format(column_name))
        columns.append("{}_upper_bound_95_perc_conf".format(column_name))
        columns.append("{}_mean".format(column_name))
        columns.append("{}_lower_bound_95_perc_conf".format(column_name))
        columns.append("{}_sem".format(column_name))
        for quantile in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
            columns.append("{}_q{}".format(column_name, quantile))

    # add product_id
    for row in stats:
        row["product_id"] = product_id

    # transpose for readability.
    stats_dataframe = pd.DataFrame(stats, columns=columns).set_index('label').transpose()
    stats_dataframe.to_csv(filepath)
    return stats_dataframe
