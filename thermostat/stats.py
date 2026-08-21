import pandas as pd
import numpy as np

from collections import OrderedDict, namedtuple
from itertools import chain
from warnings import warn
from functools import lru_cache, reduce
from importlib.resources import files
import logging

from thermostat import get_version
from thermostat.schema import (
    REAL_OR_INTEGER_VALUED_COLUMNS_ALL,
    REAL_OR_INTEGER_VALUED_COLUMNS_COOLING,
    REAL_OR_INTEGER_VALUED_COLUMNS_HEATING,
)

QUANTILE = [1, 2.5, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 98, 99]

# The five EIA climate zones the Method requires the sample to be split into,
# each with the display name that appears in the metrics `climate_zone` column
# and the slug that appears in every statistics label. These two spellings
# used to be written out separately in four places -- the frame subsetting,
# the 48 hand-typed dispatch calls, the weighting-table key map, and the list
# the national weighting re-derived its labels from. A disagreement between
# any two of them made `stats_dict.get()` return None and silently dropped a
# zone out of the national average.
ClimateZone = namedtuple("ClimateZone", ["name", "slug"])

CLIMATE_ZONES = (
    ClimateZone("Very-Cold/Cold", "very-cold_cold"),
    ClimateZone("Mixed-Humid", "mixed-humid"),
    ClimateZone("Mixed-Dry/Hot-Dry", "mixed-dry_hot-dry"),
    ClimateZone("Hot-Humid", "hot-humid"),
    ClimateZone("Marine", "marine"),
)

# The unsegmented frame is reported alongside the zones under the slug "all".
NATIONAL = ClimateZone(None, "all")
REPORTED_ZONES = (NATIONAL,) + CLIMATE_ZONES

SEASONS = ("heating", "cooling")

# Filter names in the order they are reported. advanced_filtering=True reports
# all four; the default reports the unfiltered population and the fully
# filtered one.
FILTER_NAMES = (
    "no_filter",
    "tau_filter",
    "tau_cvrmse_filter",
    "tau_cvrmse_savings_p01_filter",
)
BASIC_FILTER_NAMES = ("no_filter", "tau_cvrmse_savings_p01_filter")
TOP_ONLY_PERCENTILE_FILTER = .05  # Filters top 5 percent for RHU2 calculation
# regulated filter thresholds, previously inline literals
TAU_MINIMUM = 0
TAU_MAXIMUM = 25
CVRMSE_MAXIMUM = 0.6
SAVINGS_PERCENTILE_FILTER = 0.01
UNFILTERED_PERCENTILE = 1 - TOP_ONLY_PERCENTILE_FILTER

logger = logging.getLogger('epathermostat')




# 1.96 standard errors is the two-sided 95% normal interval the Program
# Requirements report against. It appeared as a bare literal eight times.
Z_95 = 1.96

# The national weighting retyped QUANTILE as strings here; generate it so the
# two cannot drift.
NATIONAL_WEIGHTED_STATISTICS = ["mean"] + [
    "q{}".format(quantile) for quantile in QUANTILE]


def _load_climate_zone_weights(filename_or_buffer):
    climate_zone_keys = {zone.name: zone.slug for zone in CLIMATE_ZONES}
    df = pd.read_csv(
        filename_or_buffer,
        usecols=["climate_zone", "heating_weight", "cooling_weight"],
    ).set_index("climate_zone")

    heating_weights = {climate_zone_keys[cz]: weight for cz, weight in df["heating_weight"].items()}
    cooling_weights = {climate_zone_keys[cz]: weight for cz, weight in df["cooling_weight"].items()}

    return heating_weights, cooling_weights

@lru_cache(maxsize=1)
def climate_zone_weights():
    """The packaged national weighting table, loaded once per process.

    Returns (heating_weights, cooling_weights), each keyed on the zone slug
    and **in the file's row order** -- the weighted sums iterate these dicts,
    so reordering them would change the floating-point result.
    """
    with (files('thermostat.resources')
          / 'NationalAverageClimateZoneWeightings.csv').open('rb') as f:
        return _load_climate_zone_weights(f)

# Every filter takes the frame and returns a boolean Series. NaN
# compares False in both directions, which is the same exclusion the
# per-row `lower < value < upper` gave.
def _column(column_name, target_baseline, target_baseline_method):
    if target_baseline:
        return "{}_{}".format(column_name, target_baseline_method)

    return column_name

def _identity_filter(df):
    return pd.Series(True, index=df.index)

def _range_filter(column_name, lower_bound=-np.inf, upper_bound=np.inf,
                  target_baseline=False, target_baseline_method=None):
    def _filter(df):
        column = df[_column(column_name, target_baseline, target_baseline_method)]

        return (column > lower_bound) & (column < upper_bound)

    return _filter

def _percentile_range_filter(column_name, quantile=0.0, target_baseline=False,
                             target_baseline_method=None):
    """Bounds from the quantiles of the frame being filtered.

    The bounds are a property of the whole frame, so they are computed
    once here rather than once per row as they were before.
    """
    def _filter(df):
        values = df[_column(column_name, target_baseline, target_baseline_method)].dropna()
        lower_bound = values.quantile(0.0 + quantile)
        upper_bound = values.quantile(1.0 - quantile)

        return _range_filter(
            column_name, lower_bound, upper_bound, target_baseline,
            target_baseline_method
        )(df)

    return _filter

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

    stats = NATIONAL_WEIGHTED_STATISTICS

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

            lower_bound = weighted_mean - (Z_95 * weighted_sem)
            upper_bound = weighted_mean + (Z_95 * weighted_sem)

            return {
                "{}_lower_bound_95_perc_conf_national_weighted_mean".format(key): lower_bound,
                "{}_upper_bound_95_perc_conf_national_weighted_mean".format(key): upper_bound
            }

    items = {}
    for key in keys:
        items.update(_compute_bounds(key))
    return items


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
        df, keep_mask, label, heating_or_cooling, target_columns):
    """Summary statistics over the rows ``keep_mask`` selects.

    ``keep_mask`` is called once with the whole frame and returns a boolean
    Series. It used to be a per-row predicate applied through iterrows(),
    with the percentile filters recomputing whole-column quantiles inside
    that loop -- O(n^2) on the population-statistics path.
    """
    n_rows_total = df.shape[0]

    filtered_df = df[keep_mask(df)]

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
            mean = np.nanmean(pd.to_numeric(column))

            if column.count() != 0:
                sem = np.nanstd(column) / (column.count() ** .5)
            else:
                sem = np.nan
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
            if 'rhu2' in column_name:
                iqr_filter = (column < column.quantile(UNFILTERED_PERCENTILE))
                if bool(iqr_filter.any()) is False:
                    iqr_filter = (column == column)
                    warn("RHU filtering 5% and min Runtime filtering removed entire dataset from statistics summary for bin. Disabling filter.")
                iqr_filtered_column = column.loc[iqr_filter]

                # calculate quantiles and statistics for RHU2 IQR (IQFLT) and
                # non-IQR filtering (NOIQ)
                iqr_mean = np.nanmean(pd.to_numeric(iqr_filtered_column))
                iqr_sem = np.nanstd(iqr_filtered_column) / (iqr_filtered_column.count() ** .5)
                iqr_lower_bound = iqr_mean - (1.96 * iqr_sem)
                iqr_upper_bound = iqr_mean + (1.96 * iqr_sem)

                noiq_mean = np.nanmean(pd.to_numeric(column))
                noiq_sem = np.nanstd(column) / (column.count() ** .5)
                noiq_lower_bound = noiq_mean - (1.96 * noiq_sem)
                noiq_upper_bound = noiq_mean + (1.96 * noiq_sem)

                stats["{}_n_IQFLT".format(column_name)] = iqr_filtered_column.count()
                stats["{}_upper_bound_95_perc_conf_IQFLT".format(column_name)] = iqr_upper_bound
                stats["{}_mean_IQFLT".format(column_name)] = iqr_mean
                stats["{}_lower_bound_95_perc_conf_IQFLT".format(column_name)] = iqr_lower_bound
                stats["{}_sem_IQFLT".format(column_name)] = iqr_sem
                stats["{}_n_NOIQ".format(column_name)] = column.count()
                stats["{}_upper_bound_95_perc_conf_NOIQ".format(column_name)] = noiq_upper_bound
                stats["{}_mean_NOIQ".format(column_name)] = noiq_mean
                stats["{}_lower_bound_95_perc_conf_NOIQ".format(column_name)] = noiq_lower_bound
                stats["{}_sem_NOIQ".format(column_name)] = noiq_sem

                for quantile in QUANTILE:
                    stats["{}_q{}_IQFLT".format(column_name, quantile)] = iqr_filtered_column.quantile(quantile / 100.)
                    stats["{}_q{}_NOIQ".format(column_name, quantile)] = column.quantile(quantile / 100.)

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

    heating_weights, cooling_weights = climate_zone_weights()

    _tau_filter = _range_filter("tau", TAU_MINIMUM, TAU_MAXIMUM)
    _cvrmse_filter = _range_filter(
        "cv_root_mean_sq_err", upper_bound=CVRMSE_MAXIMUM
    )
    _savings_filter_p01 = _percentile_range_filter(
        "percent_savings", SAVINGS_PERCENTILE_FILTER, target_baseline=True,
        target_baseline_method=target_baseline_method
    )

    def _combine_filters(filters):
        def _new_filter(df):
            return reduce(lambda mask, f: mask & f(df), filters,
                          pd.Series(True, index=df.index))

        return _new_filter

    def season_stats(df, filter_, label, season):
        """Summary statistics for one (frame, filter, season) combination."""
        season_df = df[df["heating_or_cooling"].str.contains(season)]
        columns = (REAL_OR_INTEGER_VALUED_COLUMNS_HEATING if season == "heating"
                   else REAL_OR_INTEGER_VALUED_COLUMNS_COOLING)

        return get_filtered_stats(season_df, filter_, label, season, columns)

    # Zone membership is a substring test because the metrics column carries
    # the display name. Reading it off the frame rather than looping in Python
    # also makes a NaN climate_zone -- what you get from re-reading a written
    # metrics.csv, as opposed to the None the in-memory path produces --
    # simply not match, instead of raising TypeError.
    zone_names = metrics_df["climate_zone"].astype("object").where(
        metrics_df["climate_zone"].notna(), "")
    frames = {NATIONAL.slug: metrics_df}
    for zone in CLIMATE_ZONES:
        frames[zone.slug] = metrics_df[
            zone_names.str.contains(zone.name, regex=False)]

    # The heating and cooling variants of each filter were identical: the
    # season argument threaded through _range_filter was never read.
    filters = {
        "no_filter": _identity_filter,
        "tau_filter": _combine_filters([_tau_filter]),
        "tau_cvrmse_filter": _combine_filters([_tau_filter, _cvrmse_filter]),
        "tau_cvrmse_savings_p01_filter": _combine_filters(
            [_tau_filter, _cvrmse_filter, _savings_filter_p01]),
    }

    active_filters = FILTER_NAMES if advanced_filtering else BASIC_FILTER_NAMES

    # This product replaces 96 lines of hand-typed calls -- 48 of them, then
    # 24 of the same ones retyped in an else: branch -- whose labels were
    # rebuilt by format string 160 lines further down against separate
    # hardcoded lists. Filter, then zone, then season is the order the output
    # rows have always been in.
    stats = list(chain.from_iterable(
        season_stats(frames[zone.slug], filters[filter_name],
                     "{}_{}".format(zone.slug, filter_name), season)
        for filter_name in active_filters
        for zone in REPORTED_ZONES
        for season in SEASONS
    ))

    stats_dict = {stat["label"]: stat for stat in stats}

    national_weighting_stats = []

    methods = [
        "baseline_percentile",
        "baseline_regional",
    ]
    for season_type in SEASONS:
        if season_type == "heating":
            weights = heating_weights
        else:
            weights = cooling_weights

        for filter_ in active_filters:
            # The same slug that built the label above, so the two can no
            # longer drift apart and quietly drop a zone from the average.
            stats_by_climate_zone = {
                zone.slug: stats_dict.get(
                    "{}_{}_{}".format(zone.slug, filter_, season_type))
                for zone in CLIMATE_ZONES
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
            "percent_savings_{}_q1_national_weighted_mean".format(method),
            "percent_savings_{}_q2.5_national_weighted_mean".format(method),
            "percent_savings_{}_q5_national_weighted_mean".format(method),
            "percent_savings_{}_q10_national_weighted_mean".format(method),
            "percent_savings_{}_q15_national_weighted_mean".format(method),
            "percent_savings_{}_q20_national_weighted_mean".format(method),
            "percent_savings_{}_q25_national_weighted_mean".format(method),
            "percent_savings_{}_q30_national_weighted_mean".format(method),
            "percent_savings_{}_q35_national_weighted_mean".format(method),
            "percent_savings_{}_q40_national_weighted_mean".format(method),
            "percent_savings_{}_q45_national_weighted_mean".format(method),
            "percent_savings_{}_q50_national_weighted_mean".format(method),
            "percent_savings_{}_q55_national_weighted_mean".format(method),
            "percent_savings_{}_q60_national_weighted_mean".format(method),
            "percent_savings_{}_q65_national_weighted_mean".format(method),
            "percent_savings_{}_q70_national_weighted_mean".format(method),
            "percent_savings_{}_q75_national_weighted_mean".format(method),
            "percent_savings_{}_q80_national_weighted_mean".format(method),
            "percent_savings_{}_q85_national_weighted_mean".format(method),
            "percent_savings_{}_q90_national_weighted_mean".format(method),
            "percent_savings_{}_q95_national_weighted_mean".format(method),
            "percent_savings_{}_q98_national_weighted_mean".format(method),
            "percent_savings_{}_q99_national_weighted_mean".format(method),
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
        for quantile in QUANTILE:
            columns.append("{}_q{}".format(column_name, quantile))

    for rhu_column in [column for column in columns if 'rhu2' in column]:
        columns.append(rhu_column + '_IQFLT')

    for rhu_column in [column for column in columns if 'IQFLT' in column]:
        columns.append(rhu_column.replace('IQFLT', 'NOIQ'))

    # add product_id
    for row in stats:
        row["product_id"] = product_id

    # transpose for readability.
    stats_dataframe = pd.DataFrame(stats, columns=columns).set_index('label').transpose()
    stats_dataframe.to_csv(filepath)
    return stats_dataframe
