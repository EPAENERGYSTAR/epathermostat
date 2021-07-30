import pandas as pd
import numpy as np
import sys
import os
import uuid

from collections import OrderedDict
from itertools import chain
import warnings
from functools import reduce
from pkg_resources import resource_stream
import logging

from functools import partial
from itertools import repeat
import multiprocessing

if os.name == 'nt':
    from multiprocessing.pool import ThreadPool as Pool
else:
    from multiprocessing import Pool

from thermostat import get_version
from thermostat.columns import (
        REAL_OR_INTEGER_VALUED_COLUMNS_HEATING,
        REAL_OR_INTEGER_VALUED_COLUMNS_COOLING,
        REAL_OR_INTEGER_VALUED_COLUMNS_ALL
        )

QUANTILE = [1, 2.5, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 98, 99]
IQR_FILTER_PARAMETER = 1.5
TOP_ONLY_PERCENTILE_FILTER = .05  # Filters top 5 percent for RHU2 calculation
UNFILTERED_PERCENTILE = 1 - TOP_ONLY_PERCENTILE_FILTER

logger = logging.getLogger('epathermostat')
warnings.simplefilter('module', Warning)

target_baseline_method = 'baseline_percentile'

def globalize(func):
    def result(*args, **kwargs):
        return func(*args, **kwargs)
    result.__name__ = result.__qualname__ = uuid.uuid4().hex
    setattr(sys.modules[result.__module__], result.__name__, result)
    return result


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

    if n_rows_total == 0:
        warnings.warn(
            "Not enough data to compute summary_statistics ({}_{})"
            .format(label, heating_or_cooling)
        )
        return []

    for column_name in target_columns:
        column = filtered_df[column_name].replace([np.inf, -np.inf], np.nan).dropna()

        # calculate quantiles and statistics
        col_num = pd.to_numeric(column)
        if col_num.empty:
            mean = np.nan
            sem = np.nan
            lower_bound = np.nan
            upper_bound = np.nan
        else:
            mean = np.nanmean(col_num)
            sem = np.nanstd(column) / (column.count() ** .5)
            lower_bound = mean - (1.96 * sem)
            upper_bound = mean + (1.96 * sem)

        stats["{}_n".format(column_name)] = column.count()
        stats["{}_upper_bound_95_perc_conf".format(column_name)] = upper_bound
        stats["{}_mean".format(column_name)] = mean
        stats["{}_lower_bound_95_perc_conf".format(column_name)] = lower_bound
        stats["{}_sem".format(column_name)] = sem

        for quantile in QUANTILE:
            stats["{}_q{}".format(column_name, quantile)] = column.quantile(quantile / 100.)

        # Calculate IQR for RHU2 and filter outliers
        # This adds an rhu2IQFLT version of the rhu2 column to the output data.
        if 'rhu2_' in column_name:
            iqr_column_name = column_name.replace('rhu2', 'rhu2IQFLT')
            iqr_filter = (column < column.quantile(UNFILTERED_PERCENTILE))
            if bool(iqr_filter.any()) is False:
                iqr_filter = (column == column)
                logging.debug("RHU filtering 5% and min Runtime filtering removed entire dataset from statistics summary for bin. Disabling filter.")
            iqr_filtered_column = column.loc[iqr_filter]

            # calculate quantiles and statistics for RHU2 IQR (IQFLT) and
            # non-IQR filtering (NOIQ)
            iqr_num = pd.to_numeric(iqr_filtered_column)
            if iqr_num.empty:
                iqr_mean = np.nan
                iqr_sem = np.nan
                iqr_lower_bound = np.nan
                iqr_upper_bound = np.nan
            else:
                iqr_mean = np.nanmean(iqr_num)
                iqr_sem = np.nanstd(iqr_filtered_column) / (iqr_filtered_column.count() ** .5)
                iqr_lower_bound = iqr_mean - (1.96 * iqr_sem)
                iqr_upper_bound = iqr_mean + (1.96 * iqr_sem)

            stats["{}_n".format(iqr_column_name)] = iqr_filtered_column.count()
            stats["{}_upper_bound_95_perc_conf".format(iqr_column_name)] = iqr_upper_bound
            stats["{}_mean".format(iqr_column_name)] = iqr_mean
            stats["{}_lower_bound_95_perc_conf".format(iqr_column_name)] = iqr_lower_bound
            stats["{}_sem".format(iqr_column_name)] = iqr_sem

            for quantile in QUANTILE:
                stats["{}_q{}".format(iqr_column_name, quantile)] = iqr_filtered_column.quantile(quantile / 100.)

    return stats


def heating_stats(df, filter_, label, target_baseline_method):
    heating_df = df[["heating" in name for name in df["heating_or_cooling"]]]
    return get_filtered_stats(
        heating_df, filter_, label,
        "heating", REAL_OR_INTEGER_VALUED_COLUMNS_HEATING,
        target_baseline_method)


def cooling_stats(df, filter_, label, target_baseline_method):
    cooling_df = df[["cooling" in name for name in df["heating_or_cooling"]]]
    return get_filtered_stats(
        cooling_df, filter_, label,
        "cooling", REAL_OR_INTEGER_VALUED_COLUMNS_COOLING,
        target_baseline_method)


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
    @globalize
    def _new_filter(row, df):
        return reduce(lambda x, y: x and y(row, df), filters, True)
    return _new_filter


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
          - 1st quantile:  ###_1q
          - 2.5th quantile:###_2.5q
          - 5th quantile:  ###_5q
          - 10th quantile: ###_10q
          - 15th quantile: ###_15q
          - 20th quantile: ###_20q
          - 25th quantile: ###_25q
          - 30th quantile: ###_30q
          - 35th quantile: ###_35q
          - 40th quantile: ###_40q
          - 45th quantile: ###_45q
          - 50th quantile: ###_50q
          - 55th quantile: ###_55q
          - 60th quantile: ###_60q
          - 65th quantile: ###_65q
          - 70th quantile: ###_70q
          - 75th quantile: ###_75q
          - 80th quantile: ###_80q
          - 85th quantile: ###_85q
          - 90th quantile: ###_90q
          - 95th quantile: ###_95q
          - 98th quantile: ###_98q
          - 99th quantile: ###_99q
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

    if len(metrics_df) == 0:
        warnings.warn("No data to compute for summary statistics.")
        return None

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

    no_filter_list = [
            (metrics_df, filter_0, "all_no_filter", target_baseline_method),
            (very_cold_cold_df, filter_0, "very-cold_cold_no_filter", target_baseline_method),
            (mixed_humid_df, filter_0, "mixed-humid_no_filter", target_baseline_method),
            (mixed_dry_hot_dry_df, filter_0, "mixed-dry_hot-dry_no_filter", target_baseline_method),
            (hot_humid_df, filter_0, "hot-humid_no_filter", target_baseline_method),
            (marine_df, filter_0, "marine_no_filter", target_baseline_method),
            ]

    filter_1_heating_list = [
            (metrics_df, filter_1_heating, "all_tau_filter", target_baseline_method),
            (very_cold_cold_df, filter_1_heating, "very-cold_cold_tau_filter", target_baseline_method),
            (mixed_humid_df, filter_1_heating, "mixed-humid_tau_filter", target_baseline_method),
            (mixed_dry_hot_dry_df, filter_1_heating, "mixed-dry_hot-dry_tau_filter", target_baseline_method),
            (hot_humid_df, filter_1_heating, "hot-humid_tau_filter", target_baseline_method),
            (marine_df, filter_1_heating, "marine_tau_filter", target_baseline_method),
            ]

    filter_1_cooling_list = [
            (metrics_df, filter_1_cooling, "all_tau_filter", target_baseline_method),
            (very_cold_cold_df, filter_1_cooling, "very-cold_cold_tau_filter", target_baseline_method),
            (mixed_humid_df, filter_1_cooling, "mixed-humid_tau_filter", target_baseline_method),
            (mixed_dry_hot_dry_df, filter_1_cooling, "mixed-dry_hot-dry_tau_filter", target_baseline_method),
            (hot_humid_df, filter_1_cooling, "hot-humid_tau_filter", target_baseline_method),
            (marine_df, filter_1_cooling, "marine_tau_filter", target_baseline_method),
            ]

    filter_2_heating_list = [
            (metrics_df, filter_2_heating, "all_cvrmse_filter", target_baseline_method),
            (very_cold_cold_df, filter_2_heating, "very-cold_cold_cvrmse_filter", target_baseline_method),
            (mixed_humid_df, filter_2_heating, "mixed-humid_cvrmse_filter", target_baseline_method),
            (mixed_dry_hot_dry_df, filter_2_heating, "mixed-dry_hot-dry_cvrmse_filter", target_baseline_method),
            (hot_humid_df, filter_2_heating, "hot-humid_cvrmse_filter", target_baseline_method),
            (marine_df, filter_2_heating, "marine_cvrmse_filter", target_baseline_method),
            ]

    filter_2_cooling_list = [
            (metrics_df, filter_2_cooling, "all_cvrmse_filter", target_baseline_method),
            (very_cold_cold_df, filter_2_cooling, "very-cold_cold_cvrmse_filter", target_baseline_method),
            (mixed_humid_df, filter_2_cooling, "mixed-humid_cvrmse_filter", target_baseline_method),
            (mixed_dry_hot_dry_df, filter_2_cooling, "mixed-dry_hot-dry_cvrmse_filter", target_baseline_method),
            (hot_humid_df, filter_2_cooling, "hot-humid_cvrmse_filter", target_baseline_method),
            (marine_df, filter_2_cooling, "marine_cvrmse_filter", target_baseline_method),
            ]

    filter_3_heating_list = [
            (metrics_df, filter_3_heating, "all_tau_cvrmse_savings_p01_filter", target_baseline_method),
            (very_cold_cold_df, filter_3_heating, "very-cold_cold_tau_cvrmse_savings_p01_filter", target_baseline_method),
            (mixed_humid_df, filter_3_heating, "mixed-humid_tau_cvrmse_savings_p01_filter", target_baseline_method),
            (mixed_dry_hot_dry_df, filter_3_heating, "mixed-dry_hot-dry_tau_cvrmse_savings_p01_filter", target_baseline_method),
            (hot_humid_df, filter_3_heating, "hot-humid_tau_cvrmse_savings_p01_filter", target_baseline_method),
            (marine_df, filter_3_heating, "marine_tau_cvrmse_savings_p01_filter", target_baseline_method),
            ]

    filter_3_cooling_list = [
            (metrics_df, filter_3_cooling, "all_tau_cvrmse_savings_p01_filter", target_baseline_method),
            (very_cold_cold_df, filter_3_cooling, "very-cold_cold_tau_cvrmse_savings_p01_filter", target_baseline_method),
            (mixed_humid_df, filter_3_cooling, "mixed-humid_tau_cvrmse_savings_p01_filter", target_baseline_method),
            (mixed_dry_hot_dry_df, filter_3_cooling, "mixed-dry_hot-dry_tau_cvrmse_savings_p01_filter", target_baseline_method),
            (hot_humid_df, filter_3_cooling, "hot-humid_tau_cvrmse_savings_p01_filter", target_baseline_method),
            (marine_df, filter_3_cooling, "marine_tau_cvrmse_savings_p01_filter", target_baseline_method),
            ]

    # Windows needs this
    stats_dict = {}
    with Pool() as pool:
        heating_stats_list = pool.starmap(heating_stats, no_filter_list)
        cooling_stats_list = pool.starmap(cooling_stats, no_filter_list)
        heating_stats_filter3_list = pool.starmap(heating_stats, filter_3_heating_list)
        cooling_stats_filter3_list = pool.starmap(cooling_stats, filter_3_cooling_list)

    # Interleave the lists (all_heating, all_cooling, very-cold_heating...)
    no_filter_list = list(chain(*zip(heating_stats_list, cooling_stats_list)))
    filter_3_list = list(chain(*zip(heating_stats_filter3_list, cooling_stats_filter3_list)))

    if advanced_filtering:
        with Pool() as pool:
            heating_stats_filter1_list = pool.starmap(heating_stats, filter_1_heating_list)
            cooling_stats_filter1_list = pool.starmap(cooling_stats, filter_1_cooling_list)
            heating_stats_filter2_list = pool.starmap(heating_stats, filter_2_heating_list)
            cooling_stats_filter2_list = pool.starmap(cooling_stats, filter_2_cooling_list)

        # Interleave the lists (all_heating, all_cooling, very-cold_heating...)
        filter_1_list = list(chain(*zip(heating_stats_filter1_list, cooling_stats_filter1_list)))
        filter_2_list = list(chain(*zip(heating_stats_filter2_list, cooling_stats_filter2_list)))


    if advanced_filtering:
        stats = list(chain.from_iterable([
                no_filter_list,
                filter_1_list,
                filter_2_list,
                filter_3_list]))
    else:
        stats = list(chain.from_iterable([
                no_filter_list,
                filter_3_list]))

    # Remove empty lists that might have sneaked in
    stats = [stat for stat in stats if stat]

    for stat in stats:
        if stat:
            stats_dict.update({stat['label']: stat})

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
                weighted_sum = sum([weight * value for weight, value in results])  # noqa: F812
                sum_of_weights = sum([weight for weight, _ in results])
                return weighted_sum / sum_of_weights

        stats = [
            "mean",
            "q1",
            "q2.5",
            "q5",
            "q10",
            "q15",
            "q20",
            "q25",
            "q30",
            "q35",
            "q40",
            "q45",
            "q50",
            "q55",
            "q60",
            "q65",
            "q70",
            "q75",
            "q80",
            "q85",
            "q90",
            "q95",
            "q98",
            "q99",
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
                    weight * mean for weight, mean in zip(weights_, means)  # noqa: F812

                ])
                weighted_mean = weighted_sum / sum(weights_)  # renormalize

                weighted_sem = sum([
                    (weight*sem) ** 2 for weight, sem in zip(weights_, sems)  # noqa: F812

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

    if stats is None:
        warnings.warn("No summary statistics to export.")
        return None


    drop_columns = [
        'national_weighted_mean_heating_no_filter',
        'national_weighted_mean_heating_tau_cvrmse_savings_p01_filter',
        'national_weighted_mean_cooling_no_filter',
        'national_weighted_mean_cooling_tau_cvrmse_savings_p01_filter',
        'national_weighted_mean_heating_tau_filter',
        'national_weighted_mean_heating_tau_cvrmse_filter',
        'national_weighted_mean_cooling_tau_filter',
        'national_weighted_mean_cooling_tau_cvrmse_filter',
        ]
    columns = [
        "label",
        "product_id",
        "sw_version",
    ]

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
        for quantile in QUANTILE:
            columns.append("{}_q{}".format(column_name, quantile))

    # add product_id
    for row in stats:
        row["product_id"] = product_id

    # transpose for readability.
    stats_dataframe = pd.DataFrame(stats, columns=columns).set_index('label').transpose()
    # Remove certification columns that are no longer in the stats file
    stats_dataframe.drop(
        drop_columns,
        axis=1,
        errors='ignore',
        inplace=True)
    stats_dataframe.to_csv(filepath)
    return stats_dataframe
