import pandas as pd
import numpy as np
from scipy.stats import norm

from eemeter.location import _load_zipcode_to_lat_lng_index
from eemeter.location import _load_zipcode_to_station_index

from collections import OrderedDict
from collections import defaultdict
from warnings import warn

REAL_OR_INTEGER_VALUED_COLUMNS_HEATING = [
    "n_days_both_heating_and_cooling",
    "n_days_insufficient_data",
    "n_days_in_season",
    "n_days_in_season_range",
    "slope_deltaT",
    "intercept_deltaT",
    "alpha_est_dailyavgHDD",
    "alpha_est_hourlyavgHDD",
    "mean_sq_err_dailyavgHDD",
    "mean_sq_err_hourlyavgHDD",
    "mean_squared_error_deltaT",
    "deltaT_base_est_dailyavgHDD",
    "deltaT_base_est_hourlyavgHDD",
    "baseline_daily_runtime_deltaT",
    "baseline_daily_runtime_dailyavgHDD",
    "baseline_daily_runtime_hourlyavgHDD",
    "baseline_seasonal_runtime_deltaT",
    "baseline_seasonal_runtime_dailyavgHDD",
    "baseline_seasonal_runtime_hourlyavgHDD",
    "baseline_comfort_temperature",
    "actual_daily_runtime",
    "actual_seasonal_runtime",
    "seasonal_avoided_runtime_deltaT",
    "seasonal_avoided_runtime_dailyavgHDD",
    "seasonal_avoided_runtime_hourlyavgHDD",
    "seasonal_savings_deltaT",
    "seasonal_savings_dailyavgHDD",
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

REAL_OR_INTEGER_VALUED_COLUMNS_COOLING = [
    "n_days_both_heating_and_cooling",
    "n_days_insufficient_data",
    "n_days_in_season",
    "n_days_in_season_range",
    "slope_deltaT",
    "intercept_deltaT",
    "alpha_est_dailyavgCDD",
    "alpha_est_hourlyavgCDD",
    "mean_sq_err_dailyavgCDD",
    "mean_sq_err_hourlyavgCDD",
    "mean_squared_error_deltaT",
    "deltaT_base_est_dailyavgCDD",
    "deltaT_base_est_hourlyavgCDD",
    "baseline_daily_runtime_deltaT",
    "baseline_daily_runtime_dailyavgCDD",
    "baseline_daily_runtime_hourlyavgCDD",
    "baseline_seasonal_runtime_deltaT",
    "baseline_seasonal_runtime_dailyavgCDD",
    "baseline_seasonal_runtime_hourlyavgCDD",
    "baseline_comfort_temperature",
    "actual_daily_runtime",
    "actual_seasonal_runtime",
    "seasonal_avoided_runtime_deltaT",
    "seasonal_avoided_runtime_dailyavgCDD",
    "seasonal_avoided_runtime_hourlyavgCDD",
    "seasonal_savings_deltaT",
    "seasonal_savings_dailyavgCDD",
    "seasonal_savings_hourlyavgCDD",
]

REAL_OR_INTEGER_VALUED_COLUMNS_ALL = [
    "n_days_both_heating_and_cooling",
    "n_days_insufficient_data",
    "n_days_in_season",
    "n_days_in_season_range",
    "slope_deltaT",
    "intercept_deltaT",
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

class ZipcodeGroupSpec(object):
    """ Mapping from zipcodes to groups. Must supply either filepath or
    dictionary.

    Parameters
    ----------
    filepath : str, None
        Path to CSV file containing the columns "zipcode" and "group".
        Each row should map the zipcode column to a target group. E.g.::

            zipcode,group
            01234,group_a
            12345,group_a
            23456,group_a
            43210,groub_b
            54321,group_b
            65432,group_c

        This creates the following grouping:

        - **group_a**: 01234,12345,23456
        - **group_b**: 43210,54321
        - **group_c**: 65432

    dictionary : dict, None
        Dictionary with zipcodes as keys and groups as values. E.g.::

            dictionary = {
                "01234": "group_a",
                "12345": "group_a",
                "23456": "group_a",
                "43210": "group_b",
                "54321": "group_b",
                "65432": "group_c",
            }

        This creates the following grouping:

        - **group_a**: 01234,12345,23456
        - **group_b**: 43210,54321
        - **group_c**: 65432

    label : str
        Extra label identifying the grouping method, for use in cases in which
        there might be ambiguity.
    """

    def __init__(self, filepath=None, dictionary=None, label=None):
        if filepath is not None:
            self.spec = self._load_spec_csv(filepath)
        elif dictionary is not None:
            self.spec = dictionary
        else:
            message = "Please supply either filepath or dictionary."
            raise ValueError(message)

        self.label = label

    def _load_spec_csv(self, filepath):
        df = pd.read_csv(filepath,
                usecols=["zipcode", "group"],
                dtype={"zipcode":str, "group":str})
        return {row["zipcode"]: row["group"] for _,row in df.iterrows()}

    def iter_groups(self, df):
        """ Iterate over groups (in no particular order.)

        Parameters
        ----------
        df : pd.Dataframe
            Dataframe containing all output data from which to draw groupings.
        """

        # avoid adding extra column to input df
        df = df.copy()

        df["_group"] = pd.Series([self.spec.get(zipcode) for zipcode in df["zipcode"]])
        for group, grouped in df.groupby("_group"):
            group_name = group if self.label is None else "{}_{}".format(group, self.label)
            yield group_name, grouped

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

def compute_summary_statistics(df, label, statistical_power_target="dailyavg", confidence=.95, ratio=.05):
    """ Computes summary statistics for the output dataframe. Computes the
    following statistics for each real-valued or integer valued column in
    the output dataframe: mean, standard error of the mean, and deciles.

    Parameters
    ----------
    df : pd.DataFrame
        Output for which to compute summary statistics.
    label : str
        Name for this set of thermostat outputs.
    statistical_power_target : {"dailyavg", "hourlyavg", "deltaT"}, default "dailyavg"
        Method for which statistical power extrapolation is desired.
    confidence : float in range 0 to 1, default .95
        Confidence interval to use in estimated statistical power calculation.
    ratio : float in range 0 to 1, default .05
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
          - number of non-null seasons: ###_n

        The following general values are also output:

          - label: label
          - number of total seasons: n_total_seasons

    """

    if statistical_power_target not in ["dailyavg", "hourlyavg", "deltaT"]:
        message = 'Method not supported - please use one of "dailyavg",' \
                '"hourlyavg", or "deltaT"'
        raise ValueError(message)

    def _statistical_power_estimate(mean, sem, n):
        n_std_devs = norm.ppf(1 - (1 - confidence)/2)
        std = sem * (n**.5)
        target_interval = mean * ratio
        target_n = (std * n_std_devs / target_interval) ** 2.
        return target_n

    def _get_season_type_stats(season_type_df, season_type, season_type_columns):
        n_seasons = season_type_df.shape[0]

        season_type_stats = OrderedDict()
        season_type_stats["label"] = "{}_{}".format(label, season_type)
        season_type_stats["n_seasons"] = n_seasons

        if n_seasons > 0:

            quantiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]

            for column_name in season_type_columns:
                column = season_type_df[column_name]

                # calculate quantiles
                season_type_stats["{}_mean".format(column_name)] = np.nanmean(column)
                season_type_stats["{}_sem".format(column_name)] = np.nanstd(column) / (column.count() ** .5)
                season_type_stats["{}_n".format(column_name)] = column.count()
                for quantile in quantiles:
                    season_type_stats["{}_q{}".format(column_name, quantile)] = column.quantile(quantile / 100.)

            if season_type == "heating":
                if statistical_power_target == "deltaT":
                    method = statistical_power_target
                else:
                    method = "{}HDD".format(statistical_power_target)

                stat_power_target_mean = "seasonal_savings_{}_mean".format(method)
                stat_power_target_sem = "seasonal_savings_{}_sem".format(method)
                stat_power_target_n = "seasonal_savings_{}_n".format(method)
            else:
                if statistical_power_target == "deltaT":
                    method = statistical_power_target
                else:
                    method = "{}CDD".format(statistical_power_target)

                stat_power_target_mean = "seasonal_savings_{}_mean".format(method)
                stat_power_target_sem = "seasonal_savings_{}_sem".format(method)
                stat_power_target_n = "seasonal_savings_{}_n".format(method)

            season_type_stats["n_enough_statistical_power"] = _statistical_power_estimate(
                    season_type_stats[stat_power_target_mean],
                    season_type_stats[stat_power_target_sem],
                    season_type_stats[stat_power_target_n])

            return [season_type_stats]
        else:
            message = "Not enough data to compute summary_statistics for {} {}".format(label, season_type)
            warn(message)
            return []


    heating_df = df[["Heating" in name for name in df["season_name"]]]
    cooling_df = df[["Cooling" in name for name in df["season_name"]]]

    stats = _get_season_type_stats(heating_df, "heating", REAL_OR_INTEGER_VALUED_COLUMNS_HEATING)
    stats.extend(_get_season_type_stats(cooling_df, "cooling", REAL_OR_INTEGER_VALUED_COLUMNS_COOLING))

    return stats

def compute_summary_statistics_by_zipcode_group(df,
        filepath=None, dictionary=None, group_spec=None,
        statistical_power_target="dailyavg", confidence=.95, ratio=.05):
    """ Filepath to zipcode -> group mapping. Note that this mapping should
    include all zipcodes that may appear in the raw output file dataframe. Any
    zipcodes which do not appear in the mapping but do occur in the ouput data
    will be ignored. The mapping can, however, include zipcodes that do not
    appear in the raw output data.

    Parameters
    ----------
    filepath : str, None
        Path to CSV file containing the columns "zipcode" and "group".
        Each row should map the zipcode column to a target group. E.g.::

            zipcode,group
            01234,group_a
            12345,group_a
            23456,group_a
            43210,groub_b
            54321,group_b
            65432,group_c

        This creates the following grouping:

        - **group_a**: 01234,12345,23456
        - **group_b**: 43210,54321
        - **group_c**: 65432

    dictionary : dict, None
        Dictionary with zipcodes as keys and groups as values. E.g.::

            dictionary = {
                "01234": "group_a",
                "12345": "group_a",
                "23456": "group_a",
                "43210": "group_b",
                "54321": "group_b",
                "65432": "group_c",
            }

        This creates the following grouping:

        - **group_a**: 01234,12345,23456
        - **group_b**: 43210,54321
        - **group_c**: 65432

    group_spec : ZipcodeGroupSpec object
        Initialized group spec object containing a zipcode -> group mapping.
    statistical_power_target : {"dailyavg", "hourlyavg", "deltaT"}, default "dailyavg"
        Method for which statistical power extrapolation is desired.
    confidence : float in range 0 to 1, default .95
        Confidence interval to use in estimated statistical power calculation.
    ratio : float in range 0 to 1, default .05
        Ratio of standard error to mean desired in statistical power calculation.

    Returns
    -------
    stats : list of dict
        List of stats dictionaries computed by group.

    """
    if group_spec is not None:
        pass
    elif filepath is not None:
        group_spec = ZipcodeGroupSpec(filepath=filepath)
    elif dictionary is not None:
        group_spec = ZipcodeGroupSpec(dictionary=dictionary)
    else:
        message = "Please supply either the filepath of a CSV file, a" \
                "dictionary, or a ZipcodeGroupSpec object"
        raise ValueError(message)

    stats = []
    for label, group_df in group_spec.iter_groups(df):
        stats.extend(compute_summary_statistics(group_df, label,
                statistical_power_target=statistical_power_target,
                confidence=confidence,
                ratio=ratio))

    return stats

def compute_summary_statistics_by_zipcode(df, statistical_power_target="dailyavg", confidence=.95, ratio=.05):
    """ Compute summary statistics for a particular dataframe by zipcode.

    Parameters
    ----------
    df : pd.Dataframe
        Contains combined (not yet grouped) output data for all thermostats in
        the sample.
    statistical_power_target : {"dailyavg", "hourlyavg", "deltaT"}, default "dailyavg"
        Method for which statistical power extrapolation is desired.
    confidence : float in range 0 to 1, default .95
        Confidence interval to use in estimated statistical power calculation.
    ratio : float in range 0 to 1, default .05
        Ratio of standard error to mean desired in statistical power calculation.

    Returns
    -------
    stats : list of dict
        Summary statistics for the input dataframe grouped by USPS ZIP code.
    """
    # Map zipcodes to themselves.
    zipcode_dict = { z: z for z in _load_zipcode_to_lat_lng_index().keys()}
    group_spec = ZipcodeGroupSpec(dictionary=zipcode_dict)

    stats = compute_summary_statistics_by_zipcode_group(df, group_spec=group_spec,
            statistical_power_target=statistical_power_target,
            confidence=confidence,
            ratio=ratio)
    return stats

def compute_summary_statistics_by_weather_station(df, statistical_power_target="dailyavg", confidence=.95, ratio=.05):
    """ Compute summary statistics for a particular dataframe by weather
    weather station used to find outdoor temperature data

    Parameters
    ----------
    df : pd.Dataframe
        Contains combined (not yet grouped) output data for all thermostats in
        the sample.
    statistical_power_target : {"dailyavg", "hourlyavg", "deltaT"}, default "dailyavg"
        Method for which statistical power extrapolation is desired.
    confidence : float in range 0 to 1, default .95
        Confidence interval to use in estimated statistical power calculation.
    ratio : float in range 0 to 1, default .05
        Ratio of standard error to mean desired in statistical power calculation.

    Returns
    -------
    stats : list of dict
        Summary statistics for the input dataframe grouped by weather station
        used to find outdoor temperature data.
    """
    # Map zipcodes to stations. This is the same mapping used to match outdoor
    # temperature data.
    zipcode_dict = _load_zipcode_to_station_index()
    group_spec = ZipcodeGroupSpec(dictionary=zipcode_dict)

    stats = compute_summary_statistics_by_zipcode_group(df, group_spec=group_spec,
            statistical_power_target=statistical_power_target,
            confidence=confidence,
            ratio=ratio)
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
    columns = ["label", "n_seasons", "n_enough_statistical_power"]
    for column_name in REAL_OR_INTEGER_VALUED_COLUMNS_ALL:
        columns.append("{}_mean".format(column_name))
        columns.append("{}_sem".format(column_name))
        columns.append("{}_n".format(column_name))
        for quantile in quantiles:
            columns.append("{}_q{}".format(column_name, quantile))

    stats_dataframe = pd.DataFrame(stats, columns=columns)
    stats_dataframe.to_csv(filepath, index=False, columns=columns)
    return stats_dataframe
