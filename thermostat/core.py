from datetime import datetime, timedelta
from collections import namedtuple
import inspect
from warnings import warn
import logging

import pandas as pd
import numpy as np
from scipy.optimize import leastsq

from thermostat import get_version
from thermostat.climate_zone import retrieve_climate_zone

CoreDaySet = namedtuple("CoreDaySet", ["name", "daily", "hourly", "start_date", "end_date"])

logger = logging.getLogger('epathermostat')

VAR_MIN_RHU_RUNTIME = 30 * 60  # Unit is in minutes (30 hours * 60 minutes)


def _ratio(numerator, denominator, name, thermostat_id):
    """ Divides, reporting a non-finite result as a missing value.

    These divisions used to sit under ``except ZeroDivisionError``, which
    never fires: numpy and pandas floats return +/-inf or NaN on a zero
    denominator rather than raising.  A non-finite ratio is not a metric, so
    it is logged and reported as NaN, which is what the handler always meant.
    """
    result = numerator / denominator
    if not np.isfinite(result):
        logger.debug(
            '%s is not finite: %s / %s for thermostat_id %s' % (
                name, numerator, denominator, thermostat_id))
        return np.nan
    return result


# A day with more missing hourly temperature readings than this is not a
# core day. Regulated threshold; was written as a bare 2 in both
# get_core_heating_days and get_core_cooling_days.
MAX_MISSING_HOURS_PER_DAY = 2

RESISTANCE_HEAT_USE_BINS_MIN_TEMP = 0  # Unit is 1 degree F.
RESISTANCE_HEAT_USE_BINS_MAX_TEMP = 60  # Unit is 1 degree F.
RESISTANCE_HEAT_USE_BIN_TEMP_WIDTH = 5  # Unit is 1 degree F.
RESISTANCE_HEAT_USE_BIN_FIRST = list(t for t in range(
    RESISTANCE_HEAT_USE_BINS_MIN_TEMP,
    RESISTANCE_HEAT_USE_BINS_MAX_TEMP + RESISTANCE_HEAT_USE_BIN_TEMP_WIDTH,
    RESISTANCE_HEAT_USE_BIN_TEMP_WIDTH))
RESISTANCE_HEAT_USE_BIN_FIRST_TUPLE = [(RESISTANCE_HEAT_USE_BIN_FIRST[i], RESISTANCE_HEAT_USE_BIN_FIRST[i+1])
                                       for i in range(0, len(RESISTANCE_HEAT_USE_BIN_FIRST) - 1)]

RESISTANCE_HEAT_USE_BIN_SECOND = [-np.inf, 10, 20, 30, 40, 50, 60]
RESISTANCE_HEAT_USE_BIN_SECOND_TUPLE = [(RESISTANCE_HEAT_USE_BIN_SECOND[i], RESISTANCE_HEAT_USE_BIN_SECOND[i+1])
                                        for i in range(0, len(RESISTANCE_HEAT_USE_BIN_SECOND) - 1)]


# --- season descriptors ---------------------------------------------------
#
# The heating and cooling arms of calculate_epa_field_savings_metrics were the
# same ~150-line algorithm written out twice with cool<->heat,
# baseline10<->baseline90 and cdd<->hdd swapped. Everything that genuinely
# differs between them is named here: the methods that supply that season's
# day sets, runtime, demand and baselines, and the eight schema columns whose
# names carry the season.
#
# The duplication had already produced drift. The cooling dict read
# `percent_savings_baseline_regional` from one local and the heating dict read
# `savings_baseline_regional` from another -- the same value, by luck, since
# the first is assigned from the second -- and the nan warning said "Total
# Runtime Core Cooling Days" on one side and "Total Runtime Core Heating" on
# the other. Written once, neither can happen again.

Season = namedtuple("Season", [
    "name",                        # "cooling" / "heating"
    "title",                       # "Cooling" / "Heating", for warning text
    "equipment_types",             # attribute naming the applicable types
    "protect",                     # raises if the thermostat lacks the equipment
    "demand_sign",                 # +1 accumulates (deltaT - tau), -1 the reverse
    "day_sets",                    # -> list of CoreDaySet
    "baseline_setpoint",           # -> percentile comfort temperature
    "runtime",                     # daily runtime Series attribute
    "demand",                      # -> (demand, tau, alpha, mse, ...)
    "baseline_demand",
    "baseline_runtime",
    "regional_comfort",            # field on the climate-zone record
    "n_core_days_column",
    "comfort_column",
    "regional_comfort_column",
    "total_runtime_column",
    "daily_mean_runtime_column",
    "mean_indoor_column",
    "mean_outdoor_column",
])


COOLING_SEASON = Season(
    name="cooling",
    title="Cooling",
    equipment_types="COOLING_EQUIPMENT_TYPES",
    protect="_protect_cooling",
    demand_sign=-1,
    day_sets="get_core_cooling_days",
    baseline_setpoint="get_core_cooling_day_baseline_setpoint",
    runtime="cool_runtime",
    demand="get_cooling_demand",
    baseline_demand="get_baseline_cooling_demand",
    baseline_runtime="get_baseline_cooling_runtime",
    regional_comfort="baseline_regional_cooling_comfort_temperature",
    n_core_days_column="n_core_cooling_days",
    comfort_column="baseline_percentile_core_cooling_comfort_temperature",
    regional_comfort_column="regional_average_baseline_cooling_comfort_temperature",
    total_runtime_column="total_core_cooling_runtime",
    daily_mean_runtime_column="daily_mean_core_cooling_runtime",
    mean_indoor_column="core_cooling_days_mean_indoor_temperature",
    mean_outdoor_column="core_cooling_days_mean_outdoor_temperature",
)


HEATING_SEASON = Season(
    name="heating",
    title="Heating",
    equipment_types="HEATING_EQUIPMENT_TYPES",
    protect="_protect_heating",
    demand_sign=1,
    day_sets="get_core_heating_days",
    baseline_setpoint="get_core_heating_day_baseline_setpoint",
    runtime="heat_runtime",
    demand="get_heating_demand",
    baseline_demand="get_baseline_heating_demand",
    baseline_runtime="get_baseline_heating_runtime",
    regional_comfort="baseline_regional_heating_comfort_temperature",
    n_core_days_column="n_core_heating_days",
    comfort_column="baseline_percentile_core_heating_comfort_temperature",
    regional_comfort_column="regional_average_baseline_heating_comfort_temperature",
    total_runtime_column="total_core_heating_runtime",
    daily_mean_runtime_column="daily_mean_core_heating_runtime",
    mean_indoor_column="core_heating_days_mean_indoor_temperature",
    mean_outdoor_column="core_heating_days_mean_outdoor_temperature",
)


class Thermostat(object):
    """ Main thermostat data container. Each parameter which contains
    timeseries data should be a pandas.Series with a datetimeIndex, and that
    each index should be equivalent.

    Parameters
    ----------
    thermostat_id : object
        An identifier for the thermostat. Can be anything, but should be
        identifying (e.g., an ID provided by the manufacturer).
    equipment_type : { 0, 1, 2, 3, 4, 5 }
        - :code:`0`: Other - e.g. multi-zone multi-stage, modulating. Note: module will
          not output savings data for this type.
        - :code:`1`: Single stage heat pump with aux and/or emergency heat
        - :code:`2`: Single stage heat pump without aux or emergency heat
        - :code:`3`: Single stage non heat pump with single-stage central air conditioning
        - :code:`4`: Single stage non heat pump without central air conditioning
        - :code:`5`: Single stage central air conditioning without central heating
    zipcode : str
        Installation ZIP code for the thermostat.
    station : str
        USAF identifier for weather station used to pull outdoor temperature data.
    temperature_in : pandas.Series
        Contains internal temperature data in degrees Fahrenheit (F),
        with resolution of at least 0.5F.
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    temperature_out : pandas.Series
        Contains outdoor temperature data as observed by a relevant
        weather station in degrees Fahrenheit (F), with resolution of at least
        0.5F.
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    cooling_setpoint : pandas.Series
        Contains target temperature (setpoint) data in degrees Fahrenheit (F),
        with resolution of at least 0.5F used to control cooling equipment.
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    heating_setpoint : pandas.Series
        Contains target temperature (setpoint) data in degrees Fahrenheit (F),
        with resolution of at least 0.5F used to control heating equipment.
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    cool_runtime : pandas.Series,
        Daily runtimes for cooling equipment controlled by the thermostat, measured
        in minutes. No datapoint should exceed 1440 mins, which would indicate
        over a day of runtime (impossible).
        Should be indexed by a pandas.DatetimeIndex with daily frequency (i.e.
        :code:`freq='D'`).
    heat_runtime : pandas.Series,
        Daily runtimes for heating equipment controlled by the thermostat, measured
        in minutes. No datapoint should exceed 1440 mins, which would indicate
        over a day of runtime (impossible).
        Should be indexed by a pandas.DatetimeIndex with daily frequency (i.e.
        :code:`freq='D'`).
    auxiliary_heat_runtime : pandas.Series,
        Hourly runtimes for auxiliary heating equipment controlled by the
        thermostat, measured in minutes. Auxiliary heat runtime is counted when
        both resistance heating and the compressor are running (for heat pump
        systems). No datapoint should exceed 60 mins, which would indicate
        over a hour of runtime (impossible).
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    emergency_heat_runtime : pandas.Series,
        Hourly runtimes for emergency heating equipment controlled by the
        thermostat, measured in minutes. Emergency heat runtime is counted when
        resistance heating is running when the compressor is not (for heat pump
        systems). No datapoint should exceed 60 mins, which would indicate
        over a hour of runtime (impossible).
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    """

    HEATING_EQUIPMENT_TYPES = set([1, 2, 3, 4])
    COOLING_EQUIPMENT_TYPES = set([1, 2, 3, 5])
    AUX_EMERG_EQUIPMENT_TYPES = set([1])

    def __init__(
            self, thermostat_id, equipment_type, zipcode, station,
            temperature_in, temperature_out, cooling_setpoint,
            heating_setpoint, cool_runtime, heat_runtime,
            auxiliary_heat_runtime, emergency_heat_runtime):

        self.thermostat_id = thermostat_id
        self.equipment_type = equipment_type
        self.zipcode = zipcode
        self.station = station

        self.temperature_in = self._interpolate(temperature_in, method="linear")
        self.temperature_out = self._interpolate(temperature_out, method="linear")
        self.cooling_setpoint = cooling_setpoint
        self.heating_setpoint = heating_setpoint

        self.cool_runtime = cool_runtime
        self.heat_runtime = heat_runtime
        self.auxiliary_heat_runtime = auxiliary_heat_runtime
        self.emergency_heat_runtime = emergency_heat_runtime

        self.validate()

    def validate(self):
        self._validate_heating()
        self._validate_cooling()
        self._validate_aux_emerg()

    def _format_rhu(self, rhu_type, low, high, duty_cycle):
        format_string = "{rhu_type}_{low:02d}F_to_{high:02d}F"
        if low == -np.inf:
            format_string = "{rhu_type}_less{high:02d}F"
            low = 0  # Don't need this value so we zero it out
        if high == np.inf:
            format_string = "{rhu_type}_greater{low:02d}F"
            high = 0  # Don't need this value so we zero it out

        result = format_string.format(
                rhu_type=rhu_type,
                low=int(low),
                high=int(high))
        if duty_cycle is not None:
            result = '_'.join((result, duty_cycle))
        return result

    def _validate_heating(self):

        if self.equipment_type in self.HEATING_EQUIPMENT_TYPES:
            if self.heat_runtime is None:
                message = "For thermostat {}, heating runtime data was not provided," \
                          " despite equipment type of {}, which requires heating data.".format(self.thermostat_id, self.equipment_type)
                raise ValueError(message)

            if self.heating_setpoint is None:
                message = "For thermostat {}, heating setpoint data was not provided," \
                          " despite equipment type of {}, which requires heating data." \
                          " If only one setpoint is used, (or if there is no distinction" \
                          " between the heating and cooling setpoints, please" \
                          " explicitly provide two copies of the available setpoint data" \
                          .format(self.thermostat_id, self.equipment_type)
                raise ValueError(message)

    def _validate_cooling(self):

        if self.equipment_type in self.COOLING_EQUIPMENT_TYPES:
            if self.cool_runtime is None:
                message = "For thermostat {}, cooling runtime data was not provided," \
                          " despite equipment type of {}, which requires cooling data.".format(self.thermostat_id, self.equipment_type)
                raise ValueError(message)

            if self.cooling_setpoint is None:
                message = "For thermostat {}, cooling setpoint data was not provided," \
                          " despite equipment type of {}, which requires heating data." \
                          " If only one setpoint is used, (or if there is no distinction" \
                          " between the heating and cooling setpoints, please" \
                          " explicitly provide two copies of the available setpoint data" \
                          .format(self.thermostat_id, self.equipment_type)
                raise ValueError(message)

    def _validate_aux_emerg(self):

        if self.equipment_type in self.AUX_EMERG_EQUIPMENT_TYPES:
            if self.auxiliary_heat_runtime is None or self.emergency_heat_runtime is None:
                message = "For thermostat {}, aux and emergency runtime data were not provided," \
                          " despite equipment type of {}, which requires these columns of data."\
                          " If none is available, please change to equipment_type 2," \
                          " or provide columns of 0s".format(self.thermostat_id, self.equipment_type)
                raise ValueError(message)

    def _interpolate(self, series, method="linear"):
        if method not in ["linear"]:
            return series
        return series.interpolate(method="linear", limit=1, limit_direction="both")

    def _protect_heating(self):
        if self.equipment_type not in self.HEATING_EQUIPMENT_TYPES:
            function_name = inspect.stack()[1][3]
            message = "The function '{}', which is heating specific, cannot be" \
                      " called for equipment_type {}".format(function_name, self.equipment_type)
            raise ValueError(message)

    def _protect_cooling(self):
        if self.equipment_type not in self.COOLING_EQUIPMENT_TYPES:
            function_name = inspect.stack()[1][3]
            message = "The function '{}', which is cooling specific, cannot be" \
                      " called for equipment_type {}".format(function_name, self.equipment_type)
            raise ValueError(message)

    def _protect_aux_emerg(self):
        if self.equipment_type not in self.AUX_EMERG_EQUIPMENT_TYPES:
            function_name = inspect.stack()[1][3]
            message = "The function '{}', which is auxiliary/emergency heating specific, cannot be" \
                      " called for equipment_type {}".format(function_name, self.equipment_type)
            raise ValueError(message)

    def _enough_hourly_temperature(self):
        """ Days with enough indoor and outdoor hourly temperature to use.

        Both core day set methods applied this test, identically, as a
        copy-pasted block with the threshold written out as a bare 2.

        Returns
        -------
        enough : pandas.Series
            Boolean, indexed daily; True where both the indoor and the
            outdoor series have at most MAX_MISSING_HOURS_PER_DAY missing
            hours on that day.
        """
        def enough(series):
            return series.groupby(series.index.date).apply(
                lambda x: x.isnull().sum() <= MAX_MISSING_HOURS_PER_DAY)

        return enough(self.temperature_in) & enough(self.temperature_out)

    def get_core_heating_days(self, method="entire_dataset",
            min_minutes_heating=30, max_minutes_cooling=0):
        """ Determine core heating days from data associated with this thermostat

        Parameters
        ----------
        method : {"entire_dataset", "year_mid_to_mid"}, default: "entire_dataset"
            Method by which to find core heating day sets.

            - "entire_dataset": all heating days in dataset (days with >= 30 min
              of heating runtime and no cooling runtime. (default)
            - "year_mid_to_mid": groups all heating days (days with >= 30 min
              of total heating and no cooling) from July 1 to June 30
              (inclusive) into individual core heating day sets. May overlap
              with core cooling day sets.
        min_minutes_heating : int, default 30
            Number of minutes of heating runtime per day required for inclusion
            in core heating day set.
        max_minutes_cooling : int, default 0
            Number of minutes of cooling runtime per day beyond which the day
            is considered part of a shoulder season (and is therefore not part
            of the core heating day set).

        Returns
        -------
        core_heating_day_sets : list of thermostat.core.CoreDaySet objects
            List of core day sets detected; Core day sets are represented as
            pandas Series of boolean values, intended to be used as selectors
            or masks on the thermostat data at hourly and daily frequencies.

            A value of True at a particular index indicates inclusion of
            of the data at that index in the core day set. If method is
            "entire_dataset", name of core day sets are "heating_ALL"; if method
            is "year_mid_to_mid", names of core day sets are of the form
            "heating_YYYY-YYYY"
        """

        if method not in ["year_mid_to_mid", "entire_dataset"]:
            raise NotImplementedError

        self._protect_heating()

        # compute inclusion thresholds
        meets_heating_thresholds = self.heat_runtime >= min_minutes_heating

        if self.equipment_type in self.COOLING_EQUIPMENT_TYPES:
            meets_cooling_thresholds = self.cool_runtime <= max_minutes_cooling
        else:
            meets_cooling_thresholds = True

        meets_thresholds = meets_heating_thresholds & meets_cooling_thresholds

        meets_thresholds &= self._enough_hourly_temperature()

        data_start_date = np.datetime64(self.heat_runtime.index[0])
        data_end_date = np.datetime64(self.heat_runtime.index[-1])

        if method == "year_mid_to_mid":
            # find all potential core heating day ranges
            start_year = data_start_date.item().year - 1
            end_year = data_end_date.item().year + 1
            potential_core_day_sets = zip(range(start_year, end_year),
                                    range(start_year + 1, end_year + 1))

            # for each potential core day set, look for core heating days.
            core_heating_day_sets = []
            for start_year_, end_year_ in potential_core_day_sets:
                core_day_set_start_date = np.datetime64(datetime(start_year_, 7, 1))
                core_day_set_end_date = np.datetime64(datetime(end_year_, 7, 1))
                start_date = max(core_day_set_start_date, data_start_date).item()
                end_date = min(core_day_set_end_date, data_end_date).item()
                in_range = self._get_range_boolean(self.heat_runtime.index,
                        start_date, end_date)
                inclusion_daily = pd.Series(in_range & meets_thresholds,
                        index=self.heat_runtime.index)

                if any(inclusion_daily):
                    name = "heating_{}-{}".format(start_year_, end_year_)
                    inclusion_hourly = self._get_hourly_boolean(inclusion_daily)
                    core_day_set = CoreDaySet(name, inclusion_daily, inclusion_hourly,
                            start_date, end_date)
                    core_heating_day_sets.append(core_day_set)

            return core_heating_day_sets

        elif method == "entire_dataset":
            inclusion_daily = pd.Series(meets_thresholds, index=self.heat_runtime.index)
            inclusion_hourly = self._get_hourly_boolean(inclusion_daily)
            core_heating_day_set = CoreDaySet(
                "heating_ALL",
                inclusion_daily,
                inclusion_hourly,
                data_start_date,
                data_end_date)
            # returned as list for consistency
            core_heating_day_sets = [core_heating_day_set]
            return core_heating_day_sets

    def get_core_cooling_days(self, method="entire_dataset",
            min_minutes_cooling=30, max_minutes_heating=0):
        """ Determine core cooling days from data associated with this
        thermostat.

        Parameters
        ----------
        method : {"entire_dataset", "year_end_to_end"}, default: "entire_dataset"
            Method by which to find core cooling days.

            - "entire_dataset": all cooling days in dataset (days with >= 30 min
              of cooling runtime and no heating runtime.
            - "year_end_to_end": groups all cooling days (days with >= 30 min
              of total cooling and no heating) from January 1 to December 31
              into individual core cooling sets.
        min_minutes_cooling : int, default 30
            Number of minutes of core cooling runtime per day required for
            inclusion in core cooling day set.
        max_minutes_heating : int, default 0
            Number of minutes of heating runtime per day beyond which the day is
            considered part of a shoulder season (and is therefore not part of
            the core cooling day set).

        Returns
        -------
        core_cooling_day_sets : list of thermostat.core.CoreDaySet objects
            List of core day sets detected; Core day sets are represented as
            pandas Series of boolean values, intended to be used as selectors
            or masks on the thermostat data at hourly and daily frequencies.

            A value of True at a particular index indicates inclusion of
            of the data at that index in the core day set. If method is
            "entire_dataset", name of core day set is "cooling_ALL"; if method
            is "year_end_to_end", names of core day sets are of the form
            "cooling_YYYY"
        """
        if method not in ["year_end_to_end", "entire_dataset"]:
            raise NotImplementedError

        self._protect_cooling()

        # find all potential core cooling day ranges
        data_start_date = np.datetime64(self.cool_runtime.index[0])
        data_end_date = np.datetime64(self.cool_runtime.index[-1])

        # compute inclusion thresholds
        if self.equipment_type in self.HEATING_EQUIPMENT_TYPES:
            meets_heating_thresholds = self.heat_runtime <= max_minutes_heating
        else:
            meets_heating_thresholds = True

        meets_cooling_thresholds = self.cool_runtime >= min_minutes_cooling
        meets_thresholds = meets_heating_thresholds & meets_cooling_thresholds

        meets_thresholds &= self._enough_hourly_temperature()

        if method == "year_end_to_end":
            start_year = data_start_date.item().year
            end_year = data_end_date.item().year
            potential_core_day_sets = range(start_year, end_year + 1)


            # for each potential core day set, look for cooling days.
            core_cooling_day_sets = []
            for year in potential_core_day_sets:
                core_day_set_start_date = np.datetime64(datetime(year, 1, 1))
                core_day_set_end_date = np.datetime64(datetime(year + 1, 1, 1))
                start_date = max(core_day_set_start_date, data_start_date).item()
                end_date = min(core_day_set_end_date, data_end_date).item()
                in_range = self._get_range_boolean(self.cool_runtime.index,
                        start_date, end_date)
                inclusion_daily = pd.Series(in_range & meets_thresholds,
                        index=self.cool_runtime.index)

                if any(inclusion_daily):
                    name = "cooling_{}".format(year)
                    inclusion_hourly = self._get_hourly_boolean(inclusion_daily)
                    core_day_set = CoreDaySet(name, inclusion_daily, inclusion_hourly,
                            start_date, end_date)
                    core_cooling_day_sets.append(core_day_set)

            return core_cooling_day_sets
        elif method == "entire_dataset":
            inclusion_daily = pd.Series(meets_thresholds, index=self.cool_runtime.index)
            inclusion_hourly = self._get_hourly_boolean(inclusion_daily)
            core_day_set = CoreDaySet(
                "cooling_ALL",
                inclusion_daily,
                inclusion_hourly,
                data_start_date,
                data_end_date)
            core_cooling_day_sets = [core_day_set]
            return core_cooling_day_sets

    def _get_range_boolean(self, dt_index, start_date, end_date):
        after_start = dt_index >= start_date
        before_end = dt_index < end_date
        return after_start & before_end

    def _get_hourly_boolean(self, daily_boolean):
        values = np.repeat(daily_boolean.values, 24)
        index = pd.date_range(start=daily_boolean.index[0],
                periods=daily_boolean.index.shape[0] * 24, freq="h")
        hourly_boolean = pd.Series(values, index)
        return hourly_boolean

    def total_heating_runtime(self, core_day_set):
        """ Calculates total heating runtime.

        Parameters
        ----------
        core_day_set : thermostat.core.CoreDaySet
            Core day set for which to calculate total runtime.

        Returns
        -------
        total_runtime : float
            Total heating runtime.
        """
        self._protect_heating()
        return self.heat_runtime[core_day_set.daily].sum()

    def total_auxiliary_heating_runtime(self, core_day_set):
        """ Calculates total auxiliary heating runtime.

        Parameters
        ----------
        core_day_set : thermostat.core.CoreDaySet
            Core day set for which to calculate total runtime.

        Returns
        -------
        total_runtime : float
            Total auxiliary heating runtime.
        """
        self._protect_aux_emerg()
        return self.auxiliary_heat_runtime[core_day_set.hourly].sum()

    def total_emergency_heating_runtime(self, core_day_set):
        """ Calculates total emergency heating runtime.

        Parameters
        ----------
        core_day_set : thermostat.core.CoreDaySet
            Core day set for which to calculate total runtime.

        Returns
        -------
        total_runtime : float
            Total heating runtime.
        """
        self._protect_aux_emerg()
        return self.emergency_heat_runtime[core_day_set.hourly].sum()

    def total_cooling_runtime(self, core_day_set):
        """ Calculates total cooling runtime.

        Parameters
        ----------
        core_day_set : thermostat.core.CoreDaySet
            Core day set for which to calculate total runtime.

        Returns
        -------
        total_runtime : float
            Total cooling runtime.
        """
        self._protect_cooling()
        return self.cool_runtime[core_day_set.daily].sum()

    def get_resistance_heat_utilization_runtime(self, core_heating_day_set):
        """ Calculates resistance heat utilization runtime and filters based on
        the core heating days

        Parameters
        ----------
        core_heating_day_set : thermostat.core.CoreDaySet
            Core heating day set for which to calculate total runtime.

        Returns
        -------
        runtime_temp : pandas.DataFrame or None
            A pandas DataFrame which includes the outdoor temperature, heat
            runtime, aux runtime, and emergency runtime, filtered by the core
            heating day set. Returns None if the thermostat does
            not control the appropriate equipment.
        """

        self._protect_aux_emerg()

        if self.equipment_type != 1:
            return None

        in_core_day_set_daily = self._get_range_boolean(
            core_heating_day_set.daily.index,
            core_heating_day_set.start_date,
            core_heating_day_set.end_date)

        # convert hourly to daily
        temp_out_daily = self.temperature_out.resample('D').mean()
        aux_daily = self.auxiliary_heat_runtime.resample('D').sum()
        emg_daily = self.emergency_heat_runtime.resample('D').sum()

        # Build the initial DataFrame based on daily readings
        runtime_temp = pd.DataFrame()
        runtime_temp['temperature'] = temp_out_daily
        runtime_temp['heat_runtime'] = self.heat_runtime
        runtime_temp['aux_runtime'] = aux_daily
        runtime_temp['emg_runtime'] = emg_daily
        runtime_temp['in_core_daily'] = in_core_day_set_daily
        runtime_temp['total_minutes'] = 1440  # default number of minutes per day

        # Filter out records that aren't part of the core day set
        runtime_temp = runtime_temp[runtime_temp['in_core_daily'].map(lambda x: x is True)]

        return runtime_temp

    def get_resistance_heat_utilization_bins(self, runtime_temp, bins, core_heating_day_set, min_runtime_minutes=None):
        """ Calculates the resistance heat utilization in
        bins (provided by the bins parameter)

        Parameters
        ----------
        runtime_temp: DataFrame
            Runtime Temperatures Dataframe from get_resistance_heat_utilization_runtime
        bins : list
            List of the bins (rightmost-edge aligned) for binning
        core_heating_day_set : thermostat.core.CoreDaySet
            Core heating day set for which to calculate total runtime.

        Returns
        -------
        RHUs : pandas.DataFrame or None
            Resistance heat utilization for each temperature bin, ordered
            ascending by temperature bin. Returns None if the thermostat does
            not control the appropriate equipment or if the runtime_temp is None.
        """
        self._protect_aux_emerg()

        if self.equipment_type != 1:
            return None

        if runtime_temp is None:
            return None

        # Create the bins and group by them. assign() copies: this frame is
        # the caller's, and it is reused across the rhu1/rhu2 passes, so
        # writing 'bins' into it leaked the first pass's column into the
        # second.
        runtime_temp = runtime_temp.assign(
            bins=pd.cut(runtime_temp['temperature'], bins))
        runtime_rhu = runtime_temp.groupby('bins', observed=False)[
            ['heat_runtime', 'aux_runtime', 'emg_runtime', 'total_minutes']].sum()

        # Calculate the RHU based on the bins
        runtime_rhu['rhu'] = (runtime_rhu['aux_runtime'] + runtime_rhu['emg_runtime']) / (runtime_rhu['heat_runtime'] + runtime_rhu['emg_runtime'])

        # Currently treating aux_runtime as separate from heat_runtime
        runtime_rhu['total_runtime'] = runtime_rhu.heat_runtime + runtime_rhu.aux_runtime + runtime_rhu.emg_runtime
        # Changed to use the number of minutes per eligible day
        runtime_rhu['aux_duty_cycle'] = runtime_rhu.aux_runtime / runtime_rhu.total_minutes
        runtime_rhu['emg_duty_cycle'] = runtime_rhu.emg_runtime / runtime_rhu.total_minutes
        runtime_rhu['compressor_duty_cycle'] = runtime_rhu.heat_runtime / runtime_rhu.total_minutes

        # If we're passed min_runtime_minutes (RHU2) then treat the thermostat as not having run during that period
        if min_runtime_minutes:
            below_min = runtime_rhu.total_runtime < min_runtime_minutes
            runtime_rhu.loc[below_min, 'rhu'] = np.nan
            runtime_rhu.loc[below_min, 'aux_duty_cycle'] = np.nan
            runtime_rhu.loc[below_min, 'emg_duty_cycle'] = np.nan
            runtime_rhu.loc[below_min, 'compressor_duty_cycle'] = np.nan
            runtime_rhu.loc[below_min, 'total_runtime'] = np.nan

        runtime_rhu['data_is_nonsense'] = (runtime_rhu['aux_runtime'] > runtime_rhu['heat_runtime'])
        runtime_rhu.loc[runtime_rhu.data_is_nonsense == True, 'rhu'] = np.nan  # noqa: E712

        if runtime_rhu.data_is_nonsense.any():
            for item in runtime_rhu.itertuples():
                if item.data_is_nonsense:
                    warn(
                        'WARNING: '
                        'aux heat runtime %s > compressor runtime %s '
                        'for %sF <= temperature < %sF '
                        'for thermostat_id %s '
                        'from %s to %s inclusive' % (
                            item.aux_runtime,
                            item.heat_runtime,
                            item.Index.left,
                            item.Index.right,
                            self.thermostat_id,
                            core_heating_day_set.start_date,
                            core_heating_day_set.end_date))

        return runtime_rhu

    def get_ignored_days(self, core_day_set):
        """ Determine how many days are ignored for a particular core day set

        Returns
        -------

        n_both : int
            Number of days excluded from core day set because of presence of
            both heating and cooling runtime.
        n_days_insufficient : int
            Number of days excluded from core day set because of null runtime
            data.
        """

        in_range = self._get_range_boolean(
            core_day_set.daily.index,
            core_day_set.start_date,
            core_day_set.end_date)

        if self.equipment_type in self.HEATING_EQUIPMENT_TYPES:
            has_heating = self.heat_runtime > 0
            null_heating = pd.isnull(self.heat_runtime)
        else:
            has_heating = False
            null_heating = False # shouldn't be counted, so False, not True

        if self.equipment_type in self.COOLING_EQUIPMENT_TYPES:
            has_cooling = self.cool_runtime > 0
            null_cooling = pd.isnull(self.cool_runtime)
        else:
            has_cooling = False
            null_cooling = False # shouldn't be counted, so False, not True


        n_both = (in_range & has_heating & has_cooling).sum()
        n_days_insufficient = (in_range & (null_heating | null_cooling)).sum()
        return n_both, n_days_insufficient

    def get_core_day_set_n_days(self, core_day_set):
        """ Returns number of days in the core day set.
        """
        return int(core_day_set.daily.sum())

    def get_inputfile_date_range(self, core_day_set):
        """ Returns number of days of data provided in input data file.
        """
        delta = (core_day_set.end_date - core_day_set.start_date)
        if isinstance(delta, timedelta):
            return delta.days
        else:
            # The divisor is the constant one day, so this cannot fail.
            return int(delta.astype('timedelta64[D]') / np.timedelta64(1, 'D'))

    def get_cooling_demand(self, core_cooling_day_set):
        r"""
        Calculates a measure of cooling demand using the hourlyavgCTD method.

        Starting with an assumed value of zero for Tau :math:`(\\tau_c)`,
        calculate the daily Cooling Thermal Demand :math:`(\\text{daily CTD}_d)`, as follows

        :math:`\\text{daily CTD}_d = \\frac{\sum_{i=1}^{24} [\\tau_c - \\text{hourly} \Delta T_{d.n}]_{+}}{24}`, where

        :math:`\\text{hourly} \Delta T_{d.n} (^{\circ} F) = \\text{hourly indoor} T_{d.n} - \\text{hourly outdoor} T_{d.n}`, and

        :math:`d` is the core cooling day; :math:`\left(001, 002, 003 ... x \\right)`,

        :math:`n` is the hour; :math:`\left(01, 02, 03 ... 24 \\right)`,

        :math:`\\tau_c` (cooling) is the :math:`\Delta T` associated with :math:`CTD=0` (zero cooling runtime), and

        :math:`[]_{+}` indicates that the term is zero if its value would be negative.

        For the set of all core cooling days in the CT interval data file, use
        ratio estimation to calculate :math:`\\alpha_c`, the home's
        responsiveness to cooling, which should be positive.

        :math:`\\alpha_c \left(\\frac{\\text{minutes}}{^{\circ} F}\\right) = \\frac{RT_\\text{actual cool}}{\sum_{d=1}^{x} \\text{daily CTD}_d}`, where

        :math:`RT_\\text{actual cool}` is the sum of cooling run times for all core cooling days in the CT interval data file.

        For the set of all core cooling days in the CT interval data file,
        optimize :math:`\\tau_c` that results in minimization of the sum of
        squares of the difference between daily run times reported by the CT,
        and calculated daily cooling run times.

        Next recalculate :math:`\\alpha_c` (in accordance with the above step)
        and record the model's parameters :math:`\left(\\alpha_c, \\tau_c \\right)`

        Parameters
        ----------
        core_cooling_day_set : thermostat.core.CoreDaySet
            Core day set over which to calculate cooling demand.

        Returns
        -------
        demand : pd.Series
            Daily demand in the core heating day set as calculated using the
            method described above.
        tau : float
            Estimate of :math:`\\tau_c`.
        alpha : float
            Estimate of :math:`\\alpha_c`
        mse : float
            Mean squared error in runtime estimates.
        rmse : float
            Root mean squared error in runtime estimates.
        cvrmse : float
            Coefficient of variation of root mean squared error in runtime estimates.
        mape : float
            Mean absolute percent error
        mae : float
            Mean absolute error
        """

        return self._fit_demand(COOLING_SEASON, core_cooling_day_set)

    def get_heating_demand(self, core_heating_day_set):
        r"""
        Calculates a measure of heating demand using the hourlyavgCTD method.

        :math:`\\text{daily HTD}_d = \\frac{\sum_{i=1}^{24} [\\text{hourly} \Delta T_{d.n} - \\tau_h]_{+}}{24}`, where

        :math:`\\text{hourly} \Delta T_{d.n} (^{\circ} F) = \\text{hourly indoor} T_{d.n} - \\text{hourly outdoor} T_{d.n}`, and

        :math:`d` is the core heating day; :math:`\left(001, 002, 003 ... x \\right)`,

        :math:`n` is the hour; :math:`\left(01, 02, 03 ... 24 \\right)`,

        :math:`\\tau_h` (heating) is the :math:`\Delta T` associated with :math:`HTD=0`, reflecting that homes with no heat running tend to be warmer that the outdoors, and

        :math:`[]_{+}` indicates that the term is zero if its value would be negative.

        For the set of all core heating days in the CT interval data file, use
        ratio estimation to calculate :math:`\\alpha_h`, the home's
        responsiveness to heating, which should be positive.

        :math:`\\alpha_h \left(\\frac{\\text{minutes}}{^{\circ} F}\\right) = \\frac{RT_\\text{actual heat}}{\sum_{d=1}^{x} \\text{daily HTD}_d}`, where

        :math:`RT_\\text{actual heat}` is the sum of heating run times for all core heating days in the CT interval data file.

        For the set of all core heating days in the CT interval data file,
        optimize :math:`\\tau_h` that results in minimization of the sum of
        squares of the difference between daily run times reported by the CT,
        and calculated daily heating run times.

        Next recalculate :math:`\\alpha_h` (in accordance with the above step)
        and record the model's parameters :math:`\left(\\alpha_h, \\tau_h \\right)`

        Parameters
        ----------
        core_heating_day_set : array_like
            Core day set over which to calculate heating demand.

        Returns
        -------
        demand : pd.Series
            Daily demand in the core heating day set as calculated using the
            method described above.
        tau : float
            Estimate of :math:`\\tau_h`.
        alpha : float
            Estimate of :math:`\\alpha_h`
        mse : float
            Mean squared error in runtime estimates.
        rmse : float
            Root mean squared error in runtime estimates.
        cvrmse : float
            Coefficient of variation of root mean squared error in runtime estimates.
        mape : float
            Mean absolute percent error
        mae : float
            Mean absolute error
        """

        return self._fit_demand(HEATING_SEASON, core_heating_day_set)

    def _fit_demand(self, season, core_day_set):
        """ Fit the daily demand model for one core day set.

        hourlyavgCTD and hourlyavgHTD are the same procedure. They differ
        only in the sign of the degree-day term -- cooling accumulates
        :math:`[\\tau - \\Delta T]_{+}`, heating accumulates
        :math:`[\\Delta T - \\tau]_{+}` -- which is what
        ``season.demand_sign`` carries. get_cooling_demand and
        get_heating_demand are the documented entry points; this is their
        shared body.

        Parameters
        ----------
        season : thermostat.core.Season
            COOLING_SEASON or HEATING_SEASON.
        core_day_set : thermostat.core.CoreDaySet
            Core day set over which to calculate demand.

        Returns
        -------
        demand, tau, alpha, mse, rmse, cvrmse, mape, mae
            As documented on get_cooling_demand.
        """
        getattr(self, season.protect)()

        core_day_set_temp_in = self.temperature_in[core_day_set.hourly]
        core_day_set_temp_out = self.temperature_out[core_day_set.hourly]
        core_day_set_deltaT = core_day_set_temp_in - core_day_set_temp_out

        daily_index = core_day_set.daily[core_day_set.daily].index

        # leastsq calls this once per iteration, so it is the hot path of the
        # whole calculation. .clip is the vectorized form of the elementwise
        # apply(np.maximum) it replaces and gives bit-identical results.
        by_day = core_day_set_deltaT.index.date

        def calc_degree_days(tau):
            hourly_dd = (
                season.demand_sign * (core_day_set_deltaT - tau)
            ).clip(lower=0)
            # Note - `x / 24` should be thought of as a unit conversion, not
            # an average.
            return np.array([dd.sum() / 24 for day, dd
                             in hourly_dd.groupby(by_day)])

        daily_runtime = getattr(self, season.runtime)[core_day_set.daily]
        total_runtime = daily_runtime.sum()

        def calc_estimates(tau):
            degree_days = calc_degree_days(tau)
            total_degree_days = np.sum(degree_days)
            alpha_estimate = _ratio(
                total_runtime, total_degree_days,
                'alpha_estimate', self.thermostat_id)
            runtime_estimate = degree_days * alpha_estimate
            errors = daily_runtime - runtime_estimate
            return degree_days, alpha_estimate, errors

        def estimate_errors(tau_estimate):
            _, _, errors = calc_estimates(tau_estimate)
            return errors

        tau_starting_guess = 0

        try:
            y, _ = leastsq(estimate_errors, tau_starting_guess)
        except TypeError:  # len 0
            # make sure no other type errors are sneaking in
            assert daily_runtime.shape[0] == 0
            return (pd.Series([], index=daily_index), np.nan, np.nan, np.nan,
                    np.nan, np.nan, np.nan, np.nan)

        tau_estimate = y[0]

        degree_days, alpha_estimate, errors = calc_estimates(tau_estimate)
        mse = np.nanmean((errors)**2)
        rmse = mse ** 0.5
        mean_daily_runtime = np.nanmean(daily_runtime)
        cvrmse = _ratio(
            rmse, mean_daily_runtime, 'CVRMSE', self.thermostat_id)

        mape = np.nanmean(np.absolute(errors / mean_daily_runtime))
        mae = np.nanmean(np.absolute(errors))

        return (
            pd.Series(degree_days, index=daily_index),
            tau_estimate,
            alpha_estimate,
            mse,
            rmse,
            cvrmse,
            mape,
            mae
        )

    def _baseline_demand(self, season, core_day_set, temp_baseline, tau):
        """ Baseline demand for one core day set at a fixed comfort setpoint.

        Shared body of get_baseline_cooling_demand and
        get_baseline_heating_demand, which differed only in the sign of the
        degree-day term.

        Parameters
        ----------
        season : thermostat.core.Season
            COOLING_SEASON or HEATING_SEASON.
        core_day_set : thermostat.core.CoreDaySet
            Core days over which to calculate baseline demand.
        temp_baseline : float
            Baseline comfort temperature.
        tau : float
            From the fitted demand model.

        Returns
        -------
        baseline_demand : pandas.Series
            Baseline daily demand for the core day set.
        """
        getattr(self, season.protect)()

        hourly_temp_out = self.temperature_out[core_day_set.hourly]

        hourly_dd = (
            season.demand_sign * ((temp_baseline - hourly_temp_out) - tau)
        ).clip(lower=0)
        demand = np.array([dd.sum() / 24 for day, dd
                           in hourly_dd.groupby(hourly_temp_out.index.date)])

        index = core_day_set.daily[core_day_set.daily].index
        return pd.Series(demand, index=index)

    def get_core_cooling_day_baseline_setpoint(self, core_cooling_day_set,
            method='tenth_percentile', source='temperature_in'):
        """ Calculate the core cooling day baseline setpoint (comfort
        temperature).

        Parameters
        ----------
        core_cooling_day_set : thermost.core.CoreDaySet
            Core cooling days over which to calculate baseline cooling setpoint.
        method : {"tenth_percentile"}, default: "tenth_percentile"
            Method to use in calculation of the baseline.

            - "tenth_percentile": 10th percentile of source temperature.
              (Either cooling setpoint or temperature in).
        source : {"cooling_setpoint", "temperature_in"}, default "temperature_in"
            The source of temperatures to use in baseline calculation.

        Returns
        -------
        baseline : float
            The baseline cooling setpoint for the core cooling days as determined
            by the given method.
        """

        self._protect_cooling()

        if method != 'tenth_percentile':
            raise NotImplementedError

        if source == 'cooling_setpoint':
            return self.cooling_setpoint[core_cooling_day_set.hourly].dropna().quantile(.1)
        elif source == 'temperature_in':
            return self.temperature_in[core_cooling_day_set.hourly].dropna().quantile(.1)
        else:
            raise NotImplementedError


    def get_core_heating_day_baseline_setpoint(self, core_heating_day_set,
            method='ninetieth_percentile', source='temperature_in'):
        """ Calculate the core heating day baseline setpoint (comfort temperature).

        Parameters
        ----------
        core_heating_day_set : thermostat.core.CoreDaySet
            Core heating days over which to calculate baseline heating setpoint.
        method : {"ninetieth_percentile"}, default: "ninetieth_percentile"
            Method to use in calculation of the baseline.

            - "ninetieth_percentile": 90th percentile of source temperature.
              (Either heating setpoint or indoor temperature).
        source : {"heating_setpoint", "temperature_in"}, default "temperature_in"
            The source of temperatures to use in baseline calculation.

        Returns
        -------
        baseline : float
            The baseline heating setpoint for the heating day as determined
            by the given method.
        """

        self._protect_heating()

        if method != 'ninetieth_percentile':
            raise NotImplementedError

        if source == 'heating_setpoint':
            return self.heating_setpoint[core_heating_day_set.hourly].dropna().quantile(.9)
        elif source == 'temperature_in':
            return self.temperature_in[core_heating_day_set.hourly].dropna().quantile(.9)
        else:
            raise NotImplementedError


    def get_baseline_cooling_demand(self, core_cooling_day_set, temp_baseline, tau):
        r""" Calculate baseline cooling demand for a particular core cooling
        day set and fitted physical parameters.

        :math:`\\text{daily CTD base}_d = \\frac{\sum_{i=1}^{24} [\\tau_c - \\text{hourly } \Delta T \\text{ base cool}_{d.n}]_{+}}{24}`, where

        :math:`\\text{hourly } \Delta T \\text{ base cool}_{d.n} (^{\circ} F) = \\text{base heat} T_{d.n} - \\text{hourly outdoor} T_{d.n}`, and

        :math:`d` is the core cooling day; :math:`\left(001, 002, 003 ... x \\right)`,

        :math:`n` is the hour; :math:`\left(01, 02, 03 ... 24 \\right)`,

        :math:`\\tau_c` (cooling), determined earlier, is a constant that is part of the CT/home's thermal/HVAC cooling run time model, and

        :math:`[]_{+}` indicates that the term is zero if its value would be negative.

        Parameters
        ----------
        core_cooling_day_set : thermostat.core.CoreDaySet
            Core cooling days over which to calculate baseline cooling demand.
        temp_baseline : float
            Baseline comfort temperature
        tau : float, default: None
            From fitted demand model.

        Returns
        -------
        baseline_cooling_demand : pandas.Series
            A series containing baseline daily heating demand for the core
            cooling day set.
        """
        return self._baseline_demand(
            COOLING_SEASON, core_cooling_day_set, temp_baseline, tau)

    def get_baseline_heating_demand(self, core_heating_day_set, temp_baseline, tau):
        r""" Calculate baseline heating demand for a particular core heating day
        set and fitted physical parameters.

        :math:`\\text{daily HTD base}_d = \\frac{\sum_{i=1}^{24} [\\text{hourly } \Delta T \\text{ base heat}_{d.n} - \\tau_h]_{+}}{24}`, where

        :math:`\\text{hourly } \Delta T \\text{ base heat}_{d.n} (^{\circ} F) = \\text{base cool} T_{d.n} - \\text{hourly outdoor} T_{d.n}`, and

        :math:`d` is the core heating day; :math:`\left(001, 002, 003 ... x \\right)`,

        :math:`n` is the hour; :math:`\left(01, 02, 03 ... 24 \\right)`,

        :math:`\\tau_h` (heating), determined earlier, is a constant that is part of the CT/home's thermal/HVAC heating run time model, and

        :math:`[]_{+}` indicates that the term is zero if its value would be negative.

        Parameters
        ----------
        core_heating_day_set : thermostat.core.CoreDaySet
            Core heating days over which to calculate baseline cooling demand.
        temp_baseline : float
            Baseline comfort temperature
        tau : float, default: None
            From fitted demand model.

        Returns
        -------
        baseline_heating_demand : pandas.Series
            A series containing baseline daily heating demand for the core heating days.
        """
        return self._baseline_demand(
            HEATING_SEASON, core_heating_day_set, temp_baseline, tau)

    def get_baseline_cooling_runtime(self, baseline_cooling_demand, alpha):
        r""" Calculate baseline cooling runtime given baseline cooling demand
        and fitted physical parameters.

        :math:`RT_{\\text{base cool}} (\\text{minutes}) = \\alpha_c \cdot \\text{daily CTD base}_d`

        Parameters
        ----------
        baseline_cooling_demand : pandas.Series
            A series containing estimated daily baseline cooling demand.
        alpha : float
            Slope of fitted line

        Returns
        -------
        baseline_cooling_runtime : pandas.Series
            A series containing estimated daily baseline cooling runtime.
        """
        return np.maximum(alpha * (baseline_cooling_demand), 0)

    def get_baseline_heating_runtime(self, baseline_heating_demand, alpha):
        r""" Calculate baseline heating runtime given baseline heating demand.
        and fitted physical parameters.

        :math:`RT_{\\text{base heat}} (\\text{minutes}) = \\alpha_h \cdot \\text{daily HTD base}_d`

        Parameters
        ----------
        baseline_heating_demand : pandas.Series
            A series containing estimated daily baseline heating demand.
        alpha : float
            Slope of fitted line

        Returns
        -------
        baseline_heating_runtime : pandas.Series
            A series containing estimated daily baseline heating runtime.
        """
        return np.maximum(alpha * (baseline_heating_demand), 0)

    def calculate_epa_field_savings_metrics(self,
            core_cooling_day_set_method="entire_dataset",
            core_heating_day_set_method="entire_dataset",
            climate_zone_mapping=None):
        """ Calculates metrics for connected thermostat savings as defined by
        the specification defined by the EPA Energy Star program and stakeholders.

        Parameters
        ----------
        core_cooling_day_set_method : {"entire_dataset", "year_end_to_end"}, default: "entire_dataset"
            Method by which to find core cooling day sets.

            - "entire_dataset": all core cooling days in dataset (days with >= 1
              hour of cooling runtime and no heating runtime.
            - "year_end_to_end": groups all core cooling days (days with >= 1 hour of total
              cooling and no heating) from January 1 to December 31 into
              independent core cooling day sets.
        core_heating_day_set_method : {"entire_dataset", "year_mid_to_mid"}, default: "entire_dataset"
            Method by which to find core heating day sets.

            - "entire_dataset": all core heating days in dataset (days with >= 1
              hour of heating runtime and no cooling runtime.
            - "year_mid_to_mid": groups all core heating days (days with >= 1 hour
              of total heating and no cooling) from July 1 to June 30 into
              independent core heating day sets.

        climate_zone_mapping : filename, default: None

            A mapping from climate zone to zipcode. If None is provided, uses
            default zipcode to climate zone mapping provided in tutorial.

            :download:`default mapping <./resources/Building America Climate Zone to Zipcode Database_Rev2_2016.09.08.csv>`

        Returns
        -------
        metrics : list
            list of dictionaries of output metrics; one per set of core heating
            or cooling days.
        """

        climate_zone_record = retrieve_climate_zone(
            climate_zone_mapping, self.zipcode)
        climate_zone = climate_zone_record.climate_zone

        metrics = []

        for season, day_set_method in (
                (COOLING_SEASON, core_cooling_day_set_method),
                (HEATING_SEASON, core_heating_day_set_method)):

            if self.equipment_type not in getattr(self, season.equipment_types):
                continue

            regional_comfort_temperature = getattr(
                climate_zone_record, season.regional_comfort)

            for core_day_set in getattr(self, season.day_sets)(
                    method=day_set_method):
                metrics.append(self._core_day_set_metrics(
                    season,
                    core_day_set,
                    climate_zone,
                    regional_comfort_temperature))

        return metrics

    def _percent_savings(self, avoided, baseline):
        return _ratio(
            avoided.mean(), baseline.mean(),
            'percent_savings', self.thermostat_id) * 100.0

    def _core_day_set_metrics(self, season, core_day_set, climate_zone,
                              regional_comfort_temperature):
        """ Savings metrics for a single core day set.

        This is the body that calculate_epa_field_savings_metrics used to
        carry twice, once per season. See the Season descriptors above for
        what differs between the two.

        Parameters
        ----------
        season : thermostat.core.Season
            COOLING_SEASON or HEATING_SEASON.
        core_day_set : thermostat.core.CoreDaySet
            The core day set to summarize.
        climate_zone : str
            EPA climate zone for this thermostat's zipcode.
        regional_comfort_temperature : float or None
            Regional average baseline comfort temperature for the climate
            zone, or None if the zone has no regional baseline.

        Returns
        -------
        outputs : dict
            One output record, keyed by the names in thermostat.schema.
        """
        comfort_temperature = getattr(self, season.baseline_setpoint)(
            core_day_set)

        daily_runtime = getattr(self, season.runtime)[core_day_set.daily]

        (
            demand,
            tau,
            alpha,
            mse,
            rmse,
            cvrmse,
            mape,
            mae,
        ) = getattr(self, season.demand)(core_day_set)

        total_runtime = daily_runtime.sum()
        n_days = core_day_set.daily.sum()

        if np.isnan(total_runtime):
            warn("WARNING: Total Runtime Core {} Days is nan.".format(
                season.title))

        if n_days == 0:
            warn("WARNING: Number of valid {} days is zero.".format(
                season.name))

        # No valid days means no average; guard the division rather than
        # flipping global numpy error state to catch it.
        if n_days == 0:
            average_daily_runtime = np.nan
        else:
            average_daily_runtime = total_runtime / n_days

        get_baseline_demand = getattr(self, season.baseline_demand)
        get_baseline_runtime = getattr(self, season.baseline_runtime)

        percentile_demand = get_baseline_demand(
            core_day_set, comfort_temperature, tau)
        percentile_runtime = get_baseline_runtime(percentile_demand, alpha)
        avoided_percentile = percentile_runtime - daily_runtime

        if regional_comfort_temperature is not None:
            regional_demand = get_baseline_demand(
                core_day_set, regional_comfort_temperature, tau)
            regional_runtime = get_baseline_runtime(regional_demand, alpha)
            avoided_regional = regional_runtime - daily_runtime

            percent_savings_baseline_regional = self._percent_savings(
                avoided_regional, regional_runtime)
            avoided_daily_mean_regional = avoided_regional.mean()
            avoided_total_regional = avoided_regional.sum()
            baseline_daily_mean_regional = regional_runtime.mean()
            baseline_total_regional = regional_runtime.sum()
            daily_mean_demand_regional = np.nanmean(regional_demand)
        else:
            percent_savings_baseline_regional = None
            avoided_daily_mean_regional = None
            avoided_total_regional = None
            baseline_daily_mean_regional = None
            baseline_total_regional = None
            daily_mean_demand_regional = None

        n_days_both, n_days_insufficient_data = self.get_ignored_days(
            core_day_set)
        n_core_days = self.get_core_day_set_n_days(core_day_set)
        n_days_in_inputfile_date_range = self.get_inputfile_date_range(
            core_day_set)

        mean_indoor_temperature = \
            self.temperature_in[core_day_set.hourly].mean()
        mean_outdoor_temperature = \
            self.temperature_out[core_day_set.hourly].mean()

        outputs = {
            "sw_version": get_version(),

            "ct_identifier": self.thermostat_id,
            "equipment_type": self.equipment_type,
            "heating_or_cooling": core_day_set.name,
            "zipcode": self.zipcode,
            "station": self.station,
            "climate_zone": climate_zone,

            "start_date": pd.Timestamp(core_day_set.start_date).to_pydatetime().isoformat(),
            "end_date": pd.Timestamp(core_day_set.end_date).to_pydatetime().isoformat(),
            "n_days_in_inputfile_date_range": n_days_in_inputfile_date_range,
            "n_days_both_heating_and_cooling": n_days_both,
            "n_days_insufficient_data": n_days_insufficient_data,
            season.n_core_days_column: n_core_days,

            season.comfort_column: comfort_temperature,
            season.regional_comfort_column: regional_comfort_temperature,

            "percent_savings_baseline_percentile": self._percent_savings(
                avoided_percentile, percentile_runtime),
            "avoided_daily_mean_core_day_runtime_baseline_percentile": avoided_percentile.mean(),
            "avoided_total_core_day_runtime_baseline_percentile": avoided_percentile.sum(),
            "baseline_daily_mean_core_day_runtime_baseline_percentile": percentile_runtime.mean(),
            "baseline_total_core_day_runtime_baseline_percentile": percentile_runtime.sum(),
            "_daily_mean_core_day_demand_baseline_baseline_percentile": np.nanmean(percentile_demand),

            "percent_savings_baseline_regional": percent_savings_baseline_regional,
            "avoided_daily_mean_core_day_runtime_baseline_regional": avoided_daily_mean_regional,
            "avoided_total_core_day_runtime_baseline_regional": avoided_total_regional,
            "baseline_daily_mean_core_day_runtime_baseline_regional": baseline_daily_mean_regional,
            "baseline_total_core_day_runtime_baseline_regional": baseline_total_regional,
            "_daily_mean_core_day_demand_baseline_baseline_regional": daily_mean_demand_regional,

            "mean_demand": np.nanmean(demand),
            "tau": tau,
            "alpha": alpha,
            "mean_sq_err": mse,
            "root_mean_sq_err": rmse,
            "cv_root_mean_sq_err": cvrmse,
            "mean_abs_pct_err": mape,
            "mean_abs_err": mae,

            season.total_runtime_column: total_runtime,
            season.daily_mean_runtime_column: average_daily_runtime,

            season.mean_indoor_column: mean_indoor_temperature,
            season.mean_outdoor_column: mean_outdoor_temperature,
            "core_mean_indoor_temperature": mean_indoor_temperature,
            "core_mean_outdoor_temperature": mean_outdoor_temperature,
        }

        if (season is HEATING_SEASON
                and self.equipment_type in self.AUX_EMERG_EQUIPMENT_TYPES):
            outputs.update(self._resistance_heat_metrics(core_day_set))

        return outputs

    def _resistance_heat_metrics(self, core_heating_day_set):
        """ Auxiliary/emergency heat metrics for a core heating day set.

        Only equipment in AUX_EMERG_EQUIPMENT_TYPES reports these; for
        everything else the columns are absent and the exporter fills NaN.

        Parameters
        ----------
        core_heating_day_set : thermostat.core.CoreDaySet
            Core heating days over which to calculate resistance heat use.

        Returns
        -------
        additional_outputs : dict
            Aux/emergency runtime totals and the 147 resistance-heat-use
            columns that thermostat.schema generates.
        """
        additional_outputs = {
            "total_auxiliary_heating_core_day_runtime":
                self.total_auxiliary_heating_runtime(
                    core_heating_day_set),
            "total_emergency_heating_core_day_runtime":
                self.total_emergency_heating_runtime(
                    core_heating_day_set),
        }

        # Add RHU Calculations
        #
        # The runtime frame does not depend on rhu_type, so it is
        # built once rather than per iteration.
        rhu_runtime = self.get_resistance_heat_utilization_runtime(
            core_heating_day_set)

        # Thermostat-level duty cycles. These are sums over the whole runtime
        # frame and so are also independent of rhu_type; emitting them inside
        # the loop produced rhu2_*_duty_cycle keys numerically identical to
        # the rhu1_* ones, which the exporter then dropped silently because
        # only the rhu1_* names are in COLUMNS. Computed once here under the
        # names the schema declares.
        if rhu_runtime is not None:
            total_minutes = rhu_runtime.total_minutes.sum()
            additional_outputs['rhu1_aux_duty_cycle'] = \
                rhu_runtime.aux_runtime.sum() / total_minutes
            additional_outputs['rhu1_emg_duty_cycle'] = \
                rhu_runtime.emg_runtime.sum() / total_minutes
            additional_outputs['rhu1_compressor_duty_cycle'] = \
                rhu_runtime.heat_runtime.sum() / total_minutes

        for rhu_type in ('rhu1', 'rhu2'):
            if rhu_type == 'rhu2':
                min_runtime_minutes = VAR_MIN_RHU_RUNTIME
            else:
                min_runtime_minutes = None

            for bins, bin_tuples in (
                    (RESISTANCE_HEAT_USE_BIN_FIRST,
                     RESISTANCE_HEAT_USE_BIN_FIRST_TUPLE),
                    (RESISTANCE_HEAT_USE_BIN_SECOND,
                     RESISTANCE_HEAT_USE_BIN_SECOND_TUPLE)):

                rhu = self.get_resistance_heat_utilization_bins(
                    rhu_runtime,
                    bins,
                    core_heating_day_set,
                    min_runtime_minutes)

                for duty_cycle in (None, 'aux_duty_cycle', 'emg_duty_cycle',
                                   'compressor_duty_cycle'):
                    if rhu is None:
                        for (low, high) in bin_tuples:
                            column = self._format_rhu(
                                rhu_type, low, high, duty_cycle)
                            additional_outputs[column] = None
                        continue

                    for item in rhu.itertuples():
                        column = self._format_rhu(
                            rhu_type=rhu_type,
                            low=item.Index.left,
                            high=item.Index.right,
                            duty_cycle=duty_cycle)
                        if duty_cycle is None:
                            additional_outputs[column] = item.rhu
                        else:
                            additional_outputs[column] = getattr(
                                item, duty_cycle)

        return additional_outputs
