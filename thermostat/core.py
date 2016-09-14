import pandas as pd
import numpy as np
from scipy.optimize import leastsq

from datetime import datetime, timedelta
from collections import namedtuple

from thermostat.regression import runtime_regression
from thermostat import get_version
from pkg_resources import resource_stream

import inspect

CoreDaySet = namedtuple("CoreDaySet",
    ["name", "daily", "hourly", "start_date", "end_date"]
)

class Thermostat(object):
    """ Main thermostat data container. Each parameter which contains
    timeseries data should be a pandas.Series with a datetimeIndex, and that
    each index should be equivalent.

    Parameters
    ----------
    thermostat_id : object
        An identifier for the thermostat. Can be anything, but should be
        identifying (e.g. an ID provided by the manufacturer).
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
    heating_setpoint : pandas.Series
        Contains target temperature (setpoint) data in degrees Fahrenheit (F),
        with resolution of at least 0.5F used to control heating equipment.
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    cooling_setpoint : pandas.Series
        Contains target temperature (setpoint) data in degrees Fahrenheit (F),
        with resolution of at least 0.5F used to control cooling equipment.
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    temperature_out : pandas.Series
        Contains outdoor temperature (setpoint) data as observed by a relevant
        weather station in degrees Fahrenheit (F), with resolution of at least
        0.5F.
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
    energency_heat_runtime : pandas.Series,
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


    def __init__(self, thermostat_id, equipment_type, zipcode, station, temperature_in,
                 temperature_out, cooling_setpoint, heating_setpoint,
                 cool_runtime, heat_runtime, auxiliary_heat_runtime,
                 emergency_heat_runtime):

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
        function_name = inspect.stack()[1][3]
        if self.equipment_type not in self.HEATING_EQUIPMENT_TYPES:
            message = "The function '{}', which is heating specific, cannot be" \
                      " called for equipment_type {}".format(function_name, self.equipment_type)
            raise ValueError(message)

    def _protect_cooling(self):
        function_name = inspect.stack()[1][3]
        if self.equipment_type not in self.COOLING_EQUIPMENT_TYPES:
            message = "The function '{}', which is cooling specific, cannot be" \
                      " called for equipment_type {}".format(function_name, self.equipment_type)
            raise ValueError(message)

    def _protect_aux_emerg(self):
        function_name = inspect.stack()[1][3]
        if self.equipment_type not in self.AUX_EMERG_EQUIPMENT_TYPES:
            message = "The function '{}', which is auxiliary/emergency heating specific, cannot be" \
                      " called for equipment_type {}".format(function_name, self.equipment_type)
            raise ValueError(message)

    def get_core_heating_days(self, method="entire_dataset",
            min_minutes_heating=60, max_minutes_cooling=0):
        """ Get all data for core heating days for data associated with this
        thermostat

        Parameters
        ----------
        method : {"entire_dataset", "year_mid_to_mid"}, default: "entire_dataset"
            Method by which to find core heating day sets.

            - "entire_dataset": all heating days in dataset (days with >= 1
              hour of heating runtime and no cooling runtime.
            - "year_mid_to_mid": groups all heating days (days with >= 1 hour
              of total heating and no cooling) from July 1 to June 30
              (inclusive) into individual core heating day sets. May overlap
              with core cooling day sets.
        min_minutes_heating : int, default 60
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
            "entire_dataset", name of is "heating_ALL"; if method
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

        # enough temperature_in
        enough_temp_in = \
                self.temperature_in.groupby(self.temperature_in.index.date) \
                .apply(lambda x: x.isnull().sum() <= 2)

        enough_temp_out = \
                self.temperature_out.groupby(self.temperature_out.index.date) \
                .apply(lambda x: x.isnull().sum() <= 2)

        meets_thresholds &= enough_temp_in & enough_temp_out

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
            min_minutes_cooling=60, max_minutes_heating=0):
        """ Get all data for core cooling days for data associated with this
        thermostat.

        Parameters
        ----------
        method : {"entire_dataset", "year_end_to_end"}, default: "entire_dataset"
            Method by which to find core cooling days.

            - "entire_dataset": all cooling days in dataset (days with >= 1
              hour of cooling runtime and no heating runtime.
            - "year_end_to_end": groups all cooling days (days with >= 1 hour
              of total cooling and no heating) from January 1 to December 31
              into individual core cooling sets.
        min_minutes_cooling : int, default 0
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
            == "year_end_to_end", names of core day sets are of the form
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

        # enough temperature_in
        enough_temp_in = \
                self.temperature_in.groupby(self.temperature_in.index.date) \
                .apply(lambda x: x.isnull().sum() <= 2)

        enough_temp_out = \
                self.temperature_out.groupby(self.temperature_out.index.date) \
                .apply(lambda x: x.isnull().sum() <= 2)

        meets_thresholds &= enough_temp_in & enough_temp_out

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
        index = pd.DatetimeIndex(start=daily_boolean.index[0],
                periods=daily_boolean.index.shape[0] * 24, freq="H")
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

    def get_resistance_heat_utilization_bins(self, core_heating_day_set):
        """ Calculates resistance heat utilization metrics in temperature
        bins of 5 degrees between 0 and 60 degrees Fahrenheit.

        Parameters
        ----------
        core_heating_day_set : thermostat.core.CoreDaySet
            Core heating day set for which to calculate total runtime.

        Returns
        -------
        RHUs : numpy.array or None
            Resistance heat utilization for each temperature bin, ordered
            ascending by temperature bin. Returns None if the thermostat does
            not control the appropriate equipment
        """

        self._protect_aux_emerg()

        bin_step = 5
        if self.equipment_type == 1:
            RHUs = []

            in_core_day_set = self._get_range_boolean(
                core_heating_day_set.hourly.index,
                core_heating_day_set.start_date,
                core_heating_day_set.end_date)

            temperature_bins = [(i, i+5) for i in range(0, 60, 5)]
            for low_temp, high_temp in temperature_bins:
                temp_low_enough = self.temperature_out < high_temp
                temp_high_enough = self.temperature_out >= low_temp
                temp_bin = temp_low_enough & temp_high_enough & in_core_day_set
                R_heat = self.heat_runtime[temp_bin].sum()
                R_aux = self.auxiliary_heat_runtime[temp_bin].sum()
                R_emg = self.emergency_heat_runtime[temp_bin].sum()
                try:
                    rhu = float(R_aux + R_emg) / float(R_heat + R_emg)
                except ZeroDivisionError:
                    rhu = 0.
                RHUs.append(rhu)
            return np.array(RHUs)
        else:
            return None

    def get_ignored_days(self, core_day_set):

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
        return int(core_day_set.daily.sum())

    def get_inputfile_date_range(self, core_day_set):
        delta = (core_day_set.end_date - core_day_set.start_date)
        if isinstance(delta, timedelta):
            return delta.days
        else:
            return int(delta.astype('timedelta64[D]') / np.timedelta64(1, 'D'))

    ##################### DEMAND ################################

    def get_cooling_demand(self, core_cooling_day_set, method="deltaT"):
        """
        Calculates a measure of cooling demand.

        Parameters
        ----------
        core_cooling_day_set : thermostat.core.CoreDaySet
            Core day set over which to calculate cooling demand.
        method : {"deltaT", "dailyavgCTD", "hourlyavgCTD"}, default: "deltaT"
            The method to use during calculation of demand.

            - "deltaT": :math:`-\Delta T` where :math:`\Delta T = T_{in} - T_{out}`
            - "dailyavgCTD": :math:`\\text{daily CTD} = \\text{max} \left(
              \Delta T_{\\text{base cool}} - \Delta T_{\\text{daily avg}}
              , 0\\right)`
              where :math:`\Delta T_{\\text{daily avg}} =
              \\frac{\sum_{i=1}^{24} \Delta T_i}{24}`
            - "hourlyavgCTD": :math:`\\text{daily CTD} = \sum_{i=1}^{24} \\text{CDH}_i`
              where :math:`\\text{CDH}_i = \\text{max}\left(
              \Delta T_{\\text{base cool}} - \Delta T_i, 0\\right)`


        Returns
        -------
        demand : pd.Series
            Daily demand in the core heating day set as calculated using one of
            the supported methods.
        tau : float
            Estimate of :math:`\Delta T_{\\text{base cool}}`. Only output for
            "hourlyavgCTD" and "dailyavgCTD".
        alpha_estimate : float
            Estimate of linear runtime response to demand. Only output for
            "hourlyavgCTD" and "dailyavgCTD".
        mean_squared_error : float
            Mean squared error in runtime estimates. Only output for "hourlyavgCTD"
            and "dailyavgCTD".
        """

        self._protect_cooling()

        core_day_set_temp_in = self.temperature_in[core_cooling_day_set.hourly]
        core_day_set_temp_out = self.temperature_out[core_cooling_day_set.hourly]
        core_day_set_deltaT = core_day_set_temp_in - core_day_set_temp_out

        daily_avg_deltaT = np.array([
            temps.mean()
            for day, temps in core_day_set_deltaT.groupby(core_day_set_deltaT.index.date)
        ])

        daily_index = core_cooling_day_set.daily[core_cooling_day_set.daily].index

        if method == "deltaT":
            return pd.Series(-daily_avg_deltaT, index=daily_index)
        elif method == "dailyavgCTD":
            def calc_cdd(tau):
                return np.maximum(tau - daily_avg_deltaT, 0)
        elif method == "hourlyavgCTD":
            def calc_cdd(tau):
                hourly_cdd = (tau - core_day_set_deltaT).apply(lambda x: np.maximum(x, 0))
                # Note - `x / 24` this should be thought of as a unit conversion, not an average.
                return np.array([cdd.sum() / 24 for day, cdd in hourly_cdd.groupby(core_day_set_deltaT.index.date)])
        else:
            raise NotImplementedError

        daily_runtime = self.cool_runtime[core_cooling_day_set.daily]
        total_runtime = daily_runtime.sum()

        def calc_estimates(tau):
            cdd = calc_cdd(tau)
            total_cdd = np.sum(cdd)
            alpha_estimate = total_runtime / total_cdd
            runtime_estimate = cdd * alpha_estimate
            errors = daily_runtime - runtime_estimate
            return cdd, alpha_estimate, errors

        def estimate_errors(tau_estimate):
            _, _, errors = calc_estimates(tau_estimate)
            return errors

        tau_starting_guess = 0
        try:
            y, _ = leastsq(estimate_errors, tau_starting_guess)
        except TypeError: # len 0
            assert daily_runtime.shape[0] == 0 # make sure no other type errors are sneaking in
            return pd.Series([], index=daily_index), np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

        tau_estimate = y[0]

        cdd, alpha_estimate, errors = calc_estimates(tau_estimate)
        mse = np.nanmean((errors)**2)
        rmse = mse ** 0.5
        mean_daily_runtime = np.nanmean(daily_runtime)
        cvrmse = rmse / mean_daily_runtime
        mape = np.nanmean(np.absolute(errors / mean_daily_runtime))
        mae = np.nanmean(np.absolute(errors))

        return pd.Series(cdd, index=daily_index), tau_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae

    def get_heating_demand(self, core_heating_day_set, method="deltaT"):
        """
        Calculates a measure of heating demand.

        Parameters
        ----------
        core_heating_day_set : array_like
            Core day set over which to calculate heating demand.
        method : {"deltaT", "hourlyavgHTD", "dailyavgHTD"} default: "deltaT"
            The method to use during calculation of demand.

            - "deltaT": :math:`\Delta T = T_{in} - T_{out}`
            - "dailyavgHTD": :math:`\\text{daily HTD} = \\text{max}\left(
              \Delta T_{\\text{daily avg}} - \Delta T_{\\text{base heat}}
              , 0\\right)` where
              :math:`\Delta T_{\\text{daily avg}} =
              \\frac{\sum_{i=1}^{24} \Delta T_i}{24}`
            - "hourlyavgHTD": :math:`\\text{daily HTD} = \sum_{i=1}^{24} \\text{HDH}_i`
              where :math:`\\text{HDH}_i = \\text{max}\left(
              \Delta T_i - \Delta T_{\\text{base heat}}
              , 0\\right)`

        Returns
        -------
        demand : pd.Series
            Daily demand in the core heating day set as calculated using one of
            the supported methods.
        tau_estimate : float
            Estimate of :math:`\Delta T_{\\text{base heat}}`. Only output for
            "hourlyavgHTD" and "dailyavgHTD".
        alpha_estimate : float
            Estimate of linear runtime response to demand. Only output for
            "hourlyavgHTD" and "dailyavgHTD".
        mean_squared_error : float
            Mean squared error in runtime estimates. Only output for "hourlyavgHTD"
            and "dailyavgHTD".
        """

        self._protect_heating()

        core_day_set_temp_in = self.temperature_in[core_heating_day_set.hourly]
        core_day_set_temp_out = self.temperature_out[core_heating_day_set.hourly]
        core_day_set_deltaT = core_day_set_temp_in - core_day_set_temp_out

        daily_avg_deltaT = np.array([temps.mean() for day, temps in core_day_set_deltaT.groupby(core_day_set_deltaT.index.date)])

        daily_index = core_heating_day_set.daily[core_heating_day_set.daily].index

        if method == "deltaT":
            return pd.Series(daily_avg_deltaT, index=daily_index)
        elif method == "dailyavgHTD":
            def calc_hdd(tau):
                return np.maximum(daily_avg_deltaT - tau, 0)
        elif method == "hourlyavgHTD":
            def calc_hdd(tau):
                hourly_hdd = (core_day_set_deltaT - tau).apply(lambda x: np.maximum(x, 0))
                # Note - this `x / 24` should be thought of as a unit conversion, not an average.
                return np.array([hdd.sum() / 24 for day, hdd in hourly_hdd.groupby(core_day_set_deltaT.index.date)])
        else:
            raise NotImplementedError

        daily_runtime = self.heat_runtime[core_heating_day_set.daily]
        total_runtime = daily_runtime.sum()

        def calc_estimates(tau):
            hdd = calc_hdd(tau)
            total_hdd = np.sum(hdd)
            alpha_estimate = total_runtime / total_hdd
            runtime_estimate = hdd * alpha_estimate
            errors = daily_runtime - runtime_estimate
            return hdd, alpha_estimate, errors

        def estimate_errors(tau_estimate):
            _, _, errors = calc_estimates(tau_estimate)
            return errors

        tau_starting_guess = 0

        try:
            y, _ = leastsq(estimate_errors, tau_starting_guess)
        except TypeError: # len 0
            assert daily_runtime.shape[0] == 0 # make sure no other type errors are sneaking in
            return pd.Series([], index=daily_index), np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

        tau_estimate = y[0]

        hdd, alpha_estimate, errors = calc_estimates(tau_estimate)
        mse = np.nanmean((errors)**2)
        rmse = mse ** 0.5
        mean_daily_runtime = np.nanmean(daily_runtime)
        cvrmse = rmse / mean_daily_runtime
        mape = np.nanmean(np.absolute(errors / mean_daily_runtime))
        mae = np.nanmean(np.absolute(errors))

        return (
            pd.Series(hdd, index=daily_index),
            tau_estimate,
            alpha_estimate,
            mse,
            rmse,
            cvrmse,
            mape,
            mae
        )

    ################## BASELINING ##########################

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
        source : {"cooling_setpoint", "temperature_in"}, default "cooling_setpoint"
            The source of temperatures to use in baseline calculation.

        Returns
        -------
        baseline : float
            The baseline cooling setpoint for the core cooling days as determined
            by the given method.
        """

        self._protect_cooling()

        if method == 'tenth_percentile':

            if source == 'cooling_setpoint':
                return self.cooling_setpoint[core_cooling_day_set.hourly].dropna().quantile(.1)
            elif source == 'temperature_in':
                return self.temperature_in[core_cooling_day_set.hourly].dropna().quantile(.1)
            else:
                raise NotImplementedError

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
        source : {"heating_setpoint", "temperature_in"}, default "heating_setpoint"
            The source of temperatures to use in baseline calculation.

        Returns
        -------
        baseline : float
            The baseline heating setpoint for the heating day as determined
            by the given method.
        """

        self._protect_heating()

        if method == 'ninetieth_percentile':

            if source == 'heating_setpoint':
                return self.heating_setpoint[core_heating_day_set.hourly].dropna().quantile(.9)
            elif source == 'temperature_in':
                return self.temperature_in[core_heating_day_set.hourly].dropna().quantile(.9)
            else:
                raise NotImplementedError

        else:
            raise NotImplementedError


    def get_baseline_cooling_demand(self, core_cooling_day_set, temp_baseline,
                                    tau=None, demand_method="deltaT"):
        """ Calculate baseline cooling demand for a particular core cooling
        day set and baseline setpoint.

        Parameters
        ----------
        core_cooling_day_set : thermostat.core.CoreDaySet
            Core cooling days over which to calculate baseline cooling demand.
        temp_baseline : float
            Baseline comfort temperature
        tau : float, default: None
            Used in calculations for "dailyavgCTD" and "hourlyavgCTD".
        demand_method : {"deltaT", "dailyavgCTD", "hourlyavgCTD"}; default: "deltaT"
            Demand method to use in calculation of the baseline CTD.

            - "deltaT": :math:`\Delta T_{\\text{base cool}} = \\text{daily avg }
              T_{\\text{outdoor}} - T_{\\text{base cool}}`
            - "dailyavgCTD": :math:`\\text{CTD}_{\\text{base}} = \Delta T_{\\text{base
              cool}} - \Delta T_{\\text{b cool}}` where :math:`\Delta T_{\\text{base
              cool}} = \\text{daily avg } T_{\\text{outdoor}} - T_{\\text{base cool}}`
            - "hourlyavgCTD": :math:`\\text{CTD}_{\\text{base}} = \\frac{\sum_{i=1}^
              {24} \\text{CDH}_{\\text{base } i}}{24}` where :math:`\\text{CDH}_{
              \\text{base } i} = \Delta T_{\\text{base cool}} - \Delta T_{\\text{b
              cool}}` and :math:`\Delta T_{\\text{base cool}} = T_{\\text{outdoor}}
              - T_{\\text{base cool}}`

        Returns
        -------
        baseline_cooling_demand : pandas.Series
            A series containing baseline daily heating demand for the core
            cooling day set.
        """
        self._protect_cooling()

        hourly_temp_out = self.temperature_out[core_cooling_day_set.hourly]

        daily_temp_out = np.array([temps.mean() for day, temps in hourly_temp_out.groupby(hourly_temp_out.index.date)])

        if demand_method == "deltaT":
            demand = daily_temp_out - temp_baseline
        elif demand_method == "dailyavgCTD":
            demand = np.maximum(tau - (temp_baseline - daily_temp_out), 0)
        elif demand_method == "hourlyavgCTD":
            hourly_cdd = (tau - (temp_baseline - hourly_temp_out)).apply(lambda x: np.maximum(x, 0))
            demand = np.array([cdd.sum() / 24 for day, cdd in hourly_cdd.groupby(hourly_temp_out.index.date)])
        else:
            raise NotImplementedError
        index = core_cooling_day_set.daily[core_cooling_day_set.daily].index
        return pd.Series(demand, index=index)

    def get_baseline_heating_demand(self, core_heating_day_set, temp_baseline,
                                    tau=None, demand_method="deltaT"):
        """ Calculate baseline heating degree days for a particular core heating day set
        and baseline setpoint.

        Parameters
        ----------
        core_heating_day_set : thermostat.core.CoreDaySet
            Core heating days over which to calculate baseline cooling demand.
        temp_baseline : float
            Baseline comfort temperature
        tau : float, default: None
            Used in calculations for "dailyavgHTD" and "hourlyavgHTD".
        demand_method : {"deltaT", "dailyavgHTD", "hourlyavgHTD"}; default: "deltaT"
            Demand method to use in calculation of the baseline HTD.

            - "deltaT": :math:`\Delta T_{\\text{base heat}} = T_{\\text{base heat}}
              - \\text{daily avg } T_{\\text{outdoor}}`
            - "dailyavgHTD": :math:`\\text{HTD}_{\\text{base}} = \Delta T_{\\text{base
              heat}} - \Delta T_{\\text{b heat}}` where :math:`\Delta T_{\\text{base
              heat}} = T_{\\text{base heat}} - \\text{daily avg } T_{\\text{outdoor}}`
            - "hourlyavgHTD": :math:`\\text{HTD}_{\\text{base}} = \\frac{\sum_{i=1}^
              {24} \\text{HDH}_{\\text{base } i}}{24}` where :math:`\\text{HDH}_{
              \\text{base } i} = \Delta T_{\\text{base heat}} - \Delta T_{\\text{b
              heat}}` and :math:`\Delta T_{\\text{base heat}} = T_{\\text{base heat}}
              - T_{\\text{outdoor}}`

        Returns
        -------
        baseline_heating_demand : pandas.Series
            A series containing baseline daily heating demand for the core heating days.
        """
        self._protect_heating()

        hourly_temp_out = self.temperature_out[core_heating_day_set.hourly]

        daily_temp_out = np.array([temps.mean() for day, temps in hourly_temp_out.groupby(hourly_temp_out.index.date)])

        if demand_method == "deltaT":
            demand = temp_baseline - daily_temp_out
        elif demand_method == "dailyavgHTD":
            demand = np.maximum(temp_baseline - daily_temp_out - tau, 0)
        elif demand_method == "hourlyavgHTD":
            hourly_hdd = (temp_baseline - hourly_temp_out - tau).apply(lambda x: np.maximum(x, 0))
            demand = np.array([hdd.sum() / 24 for day, hdd in hourly_hdd.groupby(hourly_temp_out.index.date)])
        else:
            raise NotImplementedError
        index = core_heating_day_set.daily[core_heating_day_set.daily].index
        return pd.Series(demand, index=index)

    ######################### SAVINGS ###############################

    def get_baseline_cooling_runtime(self, baseline_cooling_demand, alpha, tau, method="deltaT"):
        """ Calculate baseline heating runtime given baseline cooling demand
        and fitted physical parameters.

        Parameters
        ----------
        baseline_cooling_demand : pandas.Series
            A series containing estimated daily baseline cooling demand.
        alpha : float
            Slope of fitted line
        tau : float
            Intercept of fitted line
        method : float
            Demand method used to find alpha and tau

        Returns
        -------
        baseline_cooling_runtime : pandas.Series
            A series containing estimated daily baseline cooling runtime.
        """
        if method == "deltaT":
             return np.maximum(alpha * (baseline_cooling_demand + tau), 0)
        elif method in ["dailyavgCTD", "hourlyavgCTD"]:
            # np.maximum is in case alpha negative for some reason, or in case bad
            # demand data (e.g., not strictly non-negative) is used
            return np.maximum(alpha * (baseline_cooling_demand), 0)
        else:
            message = (
                "Method should be one of `deltaT`, `dailyavgCTD`, or `hourlyavgCTD`"
            )
            raise NotImplementedError(message)

    def get_baseline_heating_runtime(self, baseline_heating_demand, alpha, tau, method="deltaT"):
        """ Calculate baseline heating runtime given baseline heating demand.
        and fitted physical parameters.

        Parameters
        ----------
        baseline_heating_demand : pandas.Series
            A series containing estimated daily baseline heating demand.
        alpha : float
            Slope of fitted line
        tau : float
            Intercept of fitted line
        method : float
            Demand method used to find alpha and tau

        Returns
        -------
        baseline_heating_runtime : pandas.Series
            A series containing estimated daily baseline heating runtime.
        """
        if method == "deltaT":
             return np.maximum(alpha * (baseline_heating_demand - tau), 0)
        elif method in ["dailyavgHTD", "hourlyavgHTD"]:
            # np.maximum is in case alpha negative for some reason, or in case bad
            # demand data (e.g., not strictly non-negative) is used
            return np.maximum(alpha * (baseline_heating_demand), 0)
        else:
            message = (
                "Method should be one of `deltaT`, `dailyavgHTD`, or `hourlyavgHTD`"
            )
            raise NotImplementedError(message)

    def get_daily_avoided_cooling_runtime(self, baseline_runtime, core_cooling_day_set):
        return baseline_runtime - self.cool_runtime[core_cooling_day_set]

    def get_daily_avoided_heating_runtime(self, baseline_runtime, core_heating_day_set):
        return baseline_runtime - self.heat_runtime[core_heating_day_set]

    ###################### Metrics #################################

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

        def _load_mapping(filename_or_buffer):
            df = pd.read_csv(
                filename_or_buffer,
                usecols=["zipcode", "group"],
                dtype={"zipcode": str, "group": str},
            ).set_index('zipcode').drop('zipcode')
            df = df.where((pd.notnull(df)), None)

            return dict(df.to_records('index'))

        if climate_zone_mapping is None:
            with resource_stream('thermostat.resources',
                                 'Building America Climate Zone to Zipcode Database_Rev2_2016.09.08.csv') as f:
                mapping = _load_mapping(f)
        else:
            try:
                mapping = _load_mapping(climate_zone_mapping)
            except:
                raise ValueError("Could not load climate zone mapping")

        with resource_stream('thermostat.resources', 'regional_baselines.csv') as f:
            df = pd.read_csv(
                f, usecols=[
                    'EIA Climate Zone',
                    'Baseline heating temp (F)',
                    'Baseline cooling temp (F)'
                ])
            df = df.where((pd.notnull(df)), None)
            df = df.set_index('EIA Climate Zone')
            cooling_regional_baseline_temps = { k: v for k, v in df['Baseline cooling temp (F)'].iteritems()}
            heating_regional_baseline_temps = { k: v for k, v in df['Baseline heating temp (F)'].iteritems()}

        climate_zone = mapping.get(self.zipcode)
        baseline_regional_cooling_comfort_temperature = cooling_regional_baseline_temps.get(climate_zone, None)
        baseline_regional_heating_comfort_temperature = heating_regional_baseline_temps.get(climate_zone, None)

        metrics = []

        def avoided(baseline, observed):
            return baseline - observed

        def percent_savings(avoided, baseline):
            return (avoided.mean() / baseline.mean()) * 100.0


        if self.equipment_type in self.COOLING_EQUIPMENT_TYPES:
            for core_cooling_day_set in self.get_core_cooling_days(
                    method=core_cooling_day_set_method):

                baseline10_comfort_temperature = \
                    self.get_core_cooling_day_baseline_setpoint(core_cooling_day_set)

                # Calculate demand
                daily_runtime = self.cool_runtime[core_cooling_day_set.daily]
                demand_deltaT = self.get_cooling_demand(core_cooling_day_set, method="deltaT")

                # deltaT
                try:
                    (
                        alpha_deltaT,
                        tau_deltaT,
                        mse_deltaT,
                        rmse_deltaT,
                        cvrmse_deltaT,
                        mape_deltaT,
                        mae_deltaT,
                    ) = runtime_regression(
                            daily_runtime, demand_deltaT, "cooling")
                except ValueError:
                    alpha_deltaT = np.nan
                    tau_deltaT = np.nan
                    mse_deltaT = np.nan
                    rmse_deltaT = np.nan
                    cvrmse_deltaT = np.nan
                    mape_deltaT = np.nan
                    mae_deltaT = np.nan

                # dailyavgCTD
                (
                    demand_dailyavgCTD,
                    tau_dailyavgCTD,
                    alpha_dailyavgCTD,
                    mse_dailyavgCTD,
                    rmse_dailyavgCTD,
                    cvrmse_dailyavgCTD,
                    mape_dailyavgCTD,
                    mae_dailyavgCTD,
                ) = self.get_cooling_demand(
                        core_cooling_day_set, method="dailyavgCTD")

                # hourlyavgCTD
                (
                    demand_hourlyavgCTD,
                    tau_hourlyavgCTD,
                    alpha_hourlyavgCTD,
                    mse_hourlyavgCTD,
                    rmse_hourlyavgCTD,
                    cvrmse_hourlyavgCTD,
                    mape_hourlyavgCTD,
                    mae_hourlyavgCTD,
                ) = self.get_cooling_demand(
                        core_cooling_day_set, method="hourlyavgCTD")

                total_runtime_core_cooling = daily_runtime.sum()
                n_days = core_cooling_day_set.daily.sum()
                average_daily_cooling_runtime = \
                    total_runtime_core_cooling / n_days

                baseline10_demand_deltaT = \
                    self.get_baseline_cooling_demand(
                        core_cooling_day_set,
                        baseline10_comfort_temperature,
                        tau=None,
                        demand_method="deltaT")
                baseline10_demand_dailyavgCTD = \
                    self.get_baseline_cooling_demand(
                        core_cooling_day_set,
                        baseline10_comfort_temperature,
                        tau=tau_dailyavgCTD,
                        demand_method="dailyavgCTD")
                baseline10_demand_hourlyavgCTD = \
                    self.get_baseline_cooling_demand(
                        core_cooling_day_set,
                        baseline10_comfort_temperature,
                        tau=tau_hourlyavgCTD,
                        demand_method="hourlyavgCTD")

                baseline10_runtime_deltaT = \
                    self.get_baseline_cooling_runtime(
                        baseline10_demand_deltaT,
                        alpha_deltaT,
                        tau_deltaT,
                        method="deltaT")
                baseline10_runtime_dailyavgCTD = \
                    self.get_baseline_cooling_runtime(
                        baseline10_demand_dailyavgCTD,
                        alpha_dailyavgCTD,
                        tau_dailyavgCTD,
                        method="dailyavgCTD")
                baseline10_runtime_hourlyavgCTD = \
                    self.get_baseline_cooling_runtime(
                        baseline10_demand_hourlyavgCTD,
                        alpha_hourlyavgCTD,
                        tau_hourlyavgCTD,
                        method="hourlyavgCTD")

                avoided_runtime_deltaT_baseline10 = avoided(baseline10_runtime_deltaT, daily_runtime)
                avoided_runtime_dailyavgCTD_baseline10 = avoided(baseline10_runtime_dailyavgCTD, daily_runtime)
                avoided_runtime_hourlyavgCTD_baseline10 = avoided(baseline10_runtime_hourlyavgCTD, daily_runtime)

                savings_deltaT_baseline10 = percent_savings(avoided_runtime_deltaT_baseline10, baseline10_runtime_deltaT)
                savings_dailyavgCTD_baseline10 = percent_savings(avoided_runtime_dailyavgCTD_baseline10, baseline10_runtime_dailyavgCTD)
                savings_hourlyavgCTD_baseline10 = percent_savings(avoided_runtime_hourlyavgCTD_baseline10, baseline10_runtime_hourlyavgCTD)

                if baseline_regional_cooling_comfort_temperature is not None:

                    baseline_regional_demand_deltaT = \
                        self.get_baseline_cooling_demand(
                            core_cooling_day_set,
                            baseline_regional_cooling_comfort_temperature,
                            tau=None,
                            demand_method="deltaT")
                    baseline_regional_demand_dailyavgCTD = \
                        self.get_baseline_cooling_demand(
                            core_cooling_day_set,
                            baseline_regional_cooling_comfort_temperature,
                            tau=tau_dailyavgCTD,
                            demand_method="dailyavgCTD")
                    baseline_regional_demand_hourlyavgCTD = \
                        self.get_baseline_cooling_demand(
                            core_cooling_day_set,
                            baseline_regional_cooling_comfort_temperature,
                            tau=tau_hourlyavgCTD,
                            demand_method="hourlyavgCTD")

                    baseline_regional_runtime_deltaT = \
                        self.get_baseline_cooling_runtime(
                            baseline_regional_demand_deltaT,
                            alpha_deltaT,
                            tau_deltaT,
                            method="deltaT")
                    baseline_regional_runtime_dailyavgCTD = \
                        self.get_baseline_cooling_runtime(
                            baseline_regional_demand_dailyavgCTD,
                            alpha_dailyavgCTD,
                            tau_dailyavgCTD,
                            method="dailyavgCTD")
                    baseline_regional_runtime_hourlyavgCTD = \
                        self.get_baseline_cooling_runtime(
                            baseline_regional_demand_hourlyavgCTD,
                            alpha_hourlyavgCTD,
                            tau_hourlyavgCTD,
                            method="hourlyavgCTD")

                    avoided_runtime_deltaT_baseline_regional = avoided(baseline_regional_runtime_deltaT, daily_runtime)
                    avoided_runtime_dailyavgCTD_baseline_regional = avoided(baseline_regional_runtime_dailyavgCTD, daily_runtime)
                    avoided_runtime_hourlyavgCTD_baseline_regional = avoided(baseline_regional_runtime_hourlyavgCTD, daily_runtime)

                    savings_deltaT_baseline_regional = percent_savings(avoided_runtime_deltaT_baseline_regional, baseline_regional_runtime_deltaT)
                    savings_dailyavgCTD_baseline_regional = percent_savings(avoided_runtime_dailyavgCTD_baseline_regional, baseline_regional_runtime_dailyavgCTD)
                    savings_hourlyavgCTD_baseline_regional = percent_savings(avoided_runtime_hourlyavgCTD_baseline_regional, baseline_regional_runtime_hourlyavgCTD)

                    percent_savings_deltaT_cooling_baseline_regional = savings_deltaT_baseline_regional
                    avoided_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional = avoided_runtime_deltaT_baseline_regional.mean()
                    avoided_total_core_day_runtime_deltaT_cooling_baseline_regional = avoided_runtime_deltaT_baseline_regional.sum()
                    baseline_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional = baseline_regional_runtime_deltaT.mean()
                    baseline_total_core_day_runtime_deltaT_cooling_baseline_regional = baseline_regional_runtime_deltaT.sum()
                    _daily_mean_core_day_demand_baseline_deltaT_cooling_baseline_regional = np.nanmean(baseline_regional_demand_deltaT)
                    percent_savings_dailyavgCTD_baseline_regional = savings_dailyavgCTD_baseline_regional
                    avoided_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional = avoided_runtime_dailyavgCTD_baseline_regional.mean()
                    avoided_total_core_day_runtime_dailyavgCTD_baseline_regional = avoided_runtime_dailyavgCTD_baseline_regional.sum()
                    baseline_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional = baseline_regional_runtime_dailyavgCTD.mean()
                    baseline_total_core_day_runtime_dailyavgCTD_baseline_regional = baseline_regional_runtime_dailyavgCTD.sum()
                    _daily_mean_core_day_demand_baseline_dailyavgCTD_baseline_regional = np.nanmean(baseline_regional_demand_dailyavgCTD)
                    percent_savings_hourlyavgCTD_baseline_regional = savings_hourlyavgCTD_baseline_regional
                    avoided_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional = avoided_runtime_hourlyavgCTD_baseline_regional.mean()
                    avoided_total_core_day_runtime_hourlyavgCTD_baseline_regional = avoided_runtime_hourlyavgCTD_baseline_regional.sum()
                    baseline_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional = baseline_regional_runtime_hourlyavgCTD.mean()
                    baseline_total_core_day_runtime_hourlyavgCTD_baseline_regional = baseline_regional_runtime_hourlyavgCTD.sum()
                    _daily_mean_core_day_demand_baseline_hourlyavgCTD_baseline_regional = np.nanmean(baseline_regional_demand_hourlyavgCTD)

                else:

                    baseline_regional_demand_deltaT = None
                    baseline_regional_demand_dailyavgCTD = None
                    baseline_regional_demand_hourlyavgCTD = None
                    baseline_regional_runtime_deltaT = None
                    baseline_regional_runtime_dailyavgCTD = None
                    baseline_regional_runtime_hourlyavgCTD = None

                    avoided_runtime_deltaT_baseline_regional = None
                    avoided_runtime_dailyavgCTD_baseline_regional = None
                    avoided_runtime_hourlyavgCTD_baseline_regional = None

                    savings_deltaT_baseline_regional = None
                    savings_dailyavgCTD_baseline_regional = None
                    savings_hourlyavgCTD_baseline_regional = None

                    percent_savings_deltaT_cooling_baseline_regional = None
                    avoided_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional = None
                    avoided_total_core_day_runtime_deltaT_cooling_baseline_regional = None
                    baseline_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional = None
                    baseline_total_core_day_runtime_deltaT_cooling_baseline_regional = None
                    _daily_mean_core_day_demand_baseline_deltaT_cooling_baseline_regional = None
                    percent_savings_dailyavgCTD_baseline_regional = None
                    avoided_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional = None
                    avoided_total_core_day_runtime_dailyavgCTD_baseline_regional = None
                    baseline_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional = None
                    baseline_total_core_day_runtime_dailyavgCTD_baseline_regional = None
                    _daily_mean_core_day_demand_baseline_dailyavgCTD_baseline_regional = None
                    percent_savings_hourlyavgCTD_baseline_regional = None
                    avoided_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional = None
                    avoided_total_core_day_runtime_hourlyavgCTD_baseline_regional = None
                    baseline_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional = None
                    baseline_total_core_day_runtime_hourlyavgCTD_baseline_regional = None
                    _daily_mean_core_day_demand_baseline_hourlyavgCTD_baseline_regional = None

                n_days_both, n_days_insufficient_data = self.get_ignored_days(core_cooling_day_set)
                n_core_cooling_days = self.get_core_day_set_n_days(core_cooling_day_set)
                n_days_in_inputfile_date_range = self.get_inputfile_date_range(core_cooling_day_set)

                outputs = {
                    "sw_version": get_version(),

                    "ct_identifier": self.thermostat_id,
                    "equipment_type": self.equipment_type,
                    "heating_or_cooling": core_cooling_day_set.name,
                    "zipcode": self.zipcode,
                    "station": self.station,
                    "climate_zone": climate_zone,

                    "start_date": pd.Timestamp(core_cooling_day_set.start_date).to_datetime().isoformat(),
                    "end_date": pd.Timestamp(core_cooling_day_set.end_date).to_datetime().isoformat(),
                    "n_days_in_inputfile_date_range": n_days_in_inputfile_date_range,
                    "n_days_both_heating_and_cooling": n_days_both,
                    "n_days_insufficient_data": n_days_insufficient_data,
                    "n_core_cooling_days": n_core_cooling_days,

                    "baseline10_core_cooling_comfort_temperature": baseline10_comfort_temperature,
                    "regional_average_baseline_cooling_comfort_temperature": baseline_regional_cooling_comfort_temperature,

                    "percent_savings_deltaT_cooling_baseline10": savings_deltaT_baseline10,
                    "avoided_daily_mean_core_day_runtime_deltaT_cooling_baseline10": avoided_runtime_deltaT_baseline10.mean(),
                    "avoided_total_core_day_runtime_deltaT_cooling_baseline10": avoided_runtime_deltaT_baseline10.sum(),
                    "baseline_daily_mean_core_day_runtime_deltaT_cooling_baseline10": baseline10_runtime_deltaT.mean(),
                    "baseline_total_core_day_runtime_deltaT_cooling_baseline10": baseline10_runtime_deltaT.sum(),
                    "_daily_mean_core_day_demand_baseline_deltaT_cooling_baseline10": np.nanmean(baseline10_demand_deltaT),
                    "percent_savings_deltaT_cooling_baseline_regional": percent_savings_deltaT_cooling_baseline_regional,
                    "avoided_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional": avoided_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional,
                    "avoided_total_core_day_runtime_deltaT_cooling_baseline_regional": avoided_total_core_day_runtime_deltaT_cooling_baseline_regional,
                    "baseline_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional": baseline_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional,
                    "baseline_total_core_day_runtime_deltaT_cooling_baseline_regional": baseline_total_core_day_runtime_deltaT_cooling_baseline_regional,
                    "_daily_mean_core_day_demand_baseline_deltaT_cooling_baseline_regional": _daily_mean_core_day_demand_baseline_deltaT_cooling_baseline_regional,
                    "mean_demand_deltaT_cooling": np.nanmean(demand_deltaT),
                    "alpha_deltaT_cooling": alpha_deltaT,
                    "tau_deltaT_cooling": tau_deltaT,
                    "mean_sq_err_deltaT_cooling": mse_deltaT,
                    "root_mean_sq_err_deltaT_cooling": rmse_deltaT,
                    "cv_root_mean_sq_err_deltaT_cooling": cvrmse_deltaT,
                    "mean_abs_pct_err_deltaT_cooling": mape_deltaT,
                    "mean_abs_err_deltaT_cooling": mae_deltaT,

                    "percent_savings_dailyavgCTD_baseline10": savings_dailyavgCTD_baseline10,
                    "avoided_daily_mean_core_day_runtime_dailyavgCTD_baseline10": avoided_runtime_dailyavgCTD_baseline10.mean(),
                    "avoided_total_core_day_runtime_dailyavgCTD_baseline10": avoided_runtime_dailyavgCTD_baseline10.sum(),
                    "baseline_daily_mean_core_day_runtime_dailyavgCTD_baseline10": baseline10_runtime_dailyavgCTD.mean(),
                    "baseline_total_core_day_runtime_dailyavgCTD_baseline10": baseline10_runtime_dailyavgCTD.sum(),
                    "_daily_mean_core_day_demand_baseline_dailyavgCTD_baseline10": np.nanmean(baseline10_demand_dailyavgCTD),
                    "percent_savings_dailyavgCTD_baseline_regional": percent_savings_dailyavgCTD_baseline_regional,
                    "avoided_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional": avoided_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional,
                    "avoided_total_core_day_runtime_dailyavgCTD_baseline_regional": avoided_total_core_day_runtime_dailyavgCTD_baseline_regional,
                    "baseline_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional": baseline_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional,
                    "baseline_total_core_day_runtime_dailyavgCTD_baseline_regional": baseline_total_core_day_runtime_dailyavgCTD_baseline_regional,
                    "_daily_mean_core_day_demand_baseline_dailyavgCTD_baseline_regional": _daily_mean_core_day_demand_baseline_dailyavgCTD_baseline_regional,
                    "mean_demand_dailyavgCTD": np.nanmean(demand_dailyavgCTD),
                    "tau_dailyavgCTD": tau_dailyavgCTD,
                    "alpha_dailyavgCTD": alpha_dailyavgCTD,
                    "mean_sq_err_dailyavgCTD": mse_dailyavgCTD,
                    "root_mean_sq_err_dailyavgCTD": rmse_dailyavgCTD,
                    "cv_root_mean_sq_err_dailyavgCTD": cvrmse_dailyavgCTD,
                    "mean_abs_pct_err_dailyavgCTD": mape_dailyavgCTD,
                    "mean_abs_err_dailyavgCTD": mae_dailyavgCTD,

                    "percent_savings_hourlyavgCTD_baseline10": savings_hourlyavgCTD_baseline10,
                    "avoided_daily_mean_core_day_runtime_hourlyavgCTD_baseline10": avoided_runtime_hourlyavgCTD_baseline10.mean(),
                    "avoided_total_core_day_runtime_hourlyavgCTD_baseline10": avoided_runtime_hourlyavgCTD_baseline10.sum(),
                    "baseline_daily_mean_core_day_runtime_hourlyavgCTD_baseline10": baseline10_runtime_hourlyavgCTD.mean(),
                    "baseline_total_core_day_runtime_hourlyavgCTD_baseline10": baseline10_runtime_hourlyavgCTD.sum(),
                    "_daily_mean_core_day_demand_baseline_hourlyavgCTD_baseline10": np.nanmean(baseline10_demand_hourlyavgCTD),
                    "percent_savings_hourlyavgCTD_baseline_regional": percent_savings_hourlyavgCTD_baseline_regional,
                    "avoided_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional": avoided_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional,
                    "avoided_total_core_day_runtime_hourlyavgCTD_baseline_regional": avoided_total_core_day_runtime_hourlyavgCTD_baseline_regional,
                    "baseline_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional": baseline_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional,
                    "baseline_total_core_day_runtime_hourlyavgCTD_baseline_regional": baseline_total_core_day_runtime_hourlyavgCTD_baseline_regional,
                    "_daily_mean_core_day_demand_baseline_hourlyavgCTD_baseline_regional": _daily_mean_core_day_demand_baseline_hourlyavgCTD_baseline_regional,
                    "mean_demand_hourlyavgCTD": np.nanmean(demand_hourlyavgCTD),
                    "tau_hourlyavgCTD": tau_hourlyavgCTD,
                    "alpha_hourlyavgCTD": alpha_hourlyavgCTD,
                    "mean_sq_err_hourlyavgCTD": mse_hourlyavgCTD,
                    "root_mean_sq_err_hourlyavgCTD": rmse_hourlyavgCTD,
                    "cv_root_mean_sq_err_hourlyavgCTD": cvrmse_hourlyavgCTD,
                    "mean_abs_pct_err_hourlyavgCTD": mape_hourlyavgCTD,
                    "mean_abs_err_hourlyavgCTD": mae_hourlyavgCTD,

                    "total_core_cooling_runtime": total_runtime_core_cooling,

                    "daily_mean_core_cooling_runtime": average_daily_cooling_runtime,
                }

                metrics.append(outputs)


        if self.equipment_type in self.HEATING_EQUIPMENT_TYPES:
            for core_heating_day_set in self.get_core_heating_days(method=core_heating_day_set_method):

                baseline90_comfort_temperature = \
                        self.get_core_heating_day_baseline_setpoint(core_heating_day_set)

                # deltaT
                daily_runtime = self.heat_runtime[core_heating_day_set.daily]
                demand_deltaT = self.get_heating_demand(core_heating_day_set, method="deltaT")

                try:
                    (
                        alpha_deltaT,
                        tau_deltaT,
                        mse_deltaT,
                        rmse_deltaT,
                        cvrmse_deltaT,
                        mape_deltaT,
                        mae_deltaT,
                    ) = runtime_regression(
                        daily_runtime, demand_deltaT, "heating")
                except ValueError:
                    alpha_deltaT = np.nan
                    tau_deltaT = np.nan
                    mse_deltaT = np.nan
                    rmse_deltaT = np.nan
                    cvrmse_deltaT = np.nan
                    mape_deltaT = np.nan
                    mae_deltaT = np.nan

                # dailyavgHTD
                (
                    demand_dailyavgHTD,
                    tau_dailyavgHTD,
                    alpha_dailyavgHTD,
                    mse_dailyavgHTD,
                    rmse_dailyavgHTD,
                    cvrmse_dailyavgHTD,
                    mape_dailyavgHTD,
                    mae_dailyavgHTD,
                ) = self.get_heating_demand(
                    core_heating_day_set, method="dailyavgHTD")

                # hourlyavgHTD
                (
                    demand_hourlyavgHTD,
                    tau_hourlyavgHTD,
                    alpha_hourlyavgHTD,
                    mse_hourlyavgHTD,
                    rmse_hourlyavgHTD,
                    cvrmse_hourlyavgHTD,
                    mape_hourlyavgHTD,
                    mae_hourlyavgHTD,
                ) = self.get_heating_demand(
                    core_heating_day_set, method="hourlyavgHTD")

                total_runtime_core_heating = daily_runtime.sum()
                n_days = core_heating_day_set.daily.sum()
                average_daily_heating_runtime = \
                    total_runtime_core_heating / n_days

                baseline90_demand_deltaT = \
                    self.get_baseline_heating_demand(
                        core_heating_day_set,
                        baseline90_comfort_temperature,
                        tau=None,
                        demand_method="deltaT")
                baseline90_demand_dailyavgHTD = \
                    self.get_baseline_heating_demand(
                        core_heating_day_set,
                        baseline90_comfort_temperature,
                        tau=tau_dailyavgHTD,
                        demand_method="dailyavgHTD")
                baseline90_demand_hourlyavgHTD = \
                    self.get_baseline_heating_demand(
                        core_heating_day_set,
                        baseline90_comfort_temperature,
                        tau=tau_hourlyavgHTD,
                        demand_method="hourlyavgHTD")

                baseline90_runtime_deltaT = \
                    self.get_baseline_heating_runtime(
                        baseline90_demand_deltaT,
                        alpha_deltaT,
                        tau_deltaT,
                        method="deltaT")
                baseline90_runtime_dailyavgHTD = \
                    self.get_baseline_heating_runtime(
                        baseline90_demand_dailyavgHTD,
                        alpha_dailyavgHTD,
                        tau_dailyavgHTD,
                        method="dailyavgHTD")
                baseline90_runtime_hourlyavgHTD = \
                    self.get_baseline_heating_runtime(
                        baseline90_demand_hourlyavgHTD,
                        alpha_hourlyavgHTD,
                        tau_hourlyavgHTD,
                        method="hourlyavgHTD")

                avoided_runtime_deltaT_baseline90 = avoided(baseline90_runtime_deltaT, daily_runtime)
                avoided_runtime_dailyavgHTD_baseline90 = avoided(baseline90_runtime_dailyavgHTD, daily_runtime)
                avoided_runtime_hourlyavgHTD_baseline90 = avoided(baseline90_runtime_hourlyavgHTD, daily_runtime)

                savings_deltaT_baseline90 = percent_savings(avoided_runtime_deltaT_baseline90, baseline90_runtime_deltaT)
                savings_dailyavgHTD_baseline90 = percent_savings(avoided_runtime_dailyavgHTD_baseline90, baseline90_runtime_dailyavgHTD)
                savings_hourlyavgHTD_baseline90 = percent_savings(avoided_runtime_hourlyavgHTD_baseline90, baseline90_runtime_hourlyavgHTD)

                if baseline_regional_heating_comfort_temperature is not None:

                    baseline_regional_demand_deltaT = \
                        self.get_baseline_heating_demand(
                            core_heating_day_set,
                            baseline_regional_heating_comfort_temperature,
                            tau=None,
                            demand_method="deltaT")
                    baseline_regional_demand_dailyavgHTD = \
                        self.get_baseline_heating_demand(
                            core_heating_day_set,
                            baseline_regional_heating_comfort_temperature,
                            tau=tau_dailyavgHTD,
                            demand_method="dailyavgHTD")
                    baseline_regional_demand_hourlyavgHTD = \
                        self.get_baseline_heating_demand(
                            core_heating_day_set,
                            baseline_regional_heating_comfort_temperature,
                            tau=tau_hourlyavgHTD,
                            demand_method="hourlyavgHTD")

                    baseline_regional_runtime_deltaT = \
                        self.get_baseline_heating_runtime(
                            baseline_regional_demand_deltaT,
                            alpha_deltaT,
                            tau_deltaT,
                            method="deltaT")
                    baseline_regional_runtime_dailyavgHTD = \
                        self.get_baseline_heating_runtime(
                            baseline_regional_demand_dailyavgHTD,
                            alpha_dailyavgHTD,
                            tau_dailyavgHTD,
                            method="dailyavgHTD")
                    baseline_regional_runtime_hourlyavgHTD = \
                        self.get_baseline_heating_runtime(
                            baseline_regional_demand_hourlyavgHTD,
                            alpha_hourlyavgHTD,
                            tau_hourlyavgHTD,
                            method="hourlyavgHTD")

                    avoided_runtime_deltaT_baseline_regional = avoided(baseline_regional_runtime_deltaT, daily_runtime)
                    avoided_runtime_dailyavgHTD_baseline_regional = avoided(baseline_regional_runtime_dailyavgHTD, daily_runtime)
                    avoided_runtime_hourlyavgHTD_baseline_regional = avoided(baseline_regional_runtime_hourlyavgHTD, daily_runtime)

                    savings_deltaT_baseline_regional = percent_savings(avoided_runtime_deltaT_baseline_regional, baseline_regional_runtime_deltaT)
                    savings_dailyavgHTD_baseline_regional = percent_savings(avoided_runtime_dailyavgHTD_baseline_regional, baseline_regional_runtime_dailyavgHTD)
                    savings_hourlyavgHTD_baseline_regional = percent_savings(avoided_runtime_hourlyavgHTD_baseline_regional, baseline_regional_runtime_hourlyavgHTD)

                    percent_savings_deltaT_heating_baseline_regional = savings_deltaT_baseline_regional
                    avoided_daily_mean_core_day_runtime_deltaT_heating_baseline_regional = avoided_runtime_deltaT_baseline_regional.mean()
                    avoided_total_core_day_runtime_deltaT_heating_baseline_regional = avoided_runtime_deltaT_baseline_regional.sum()
                    baseline_daily_mean_core_day_runtime_deltaT_heating_baseline_regional = baseline_regional_runtime_deltaT.mean()
                    baseline_total_core_day_runtime_deltaT_heating_baseline_regional = baseline_regional_runtime_deltaT.sum()
                    _daily_mean_core_day_demand_baseline_deltaT_heating_baseline_regional = np.nanmean(baseline_regional_demand_deltaT)
                    percent_savings_dailyavgHTD_baseline_regional = savings_dailyavgHTD_baseline_regional
                    avoided_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional = avoided_runtime_dailyavgHTD_baseline_regional.mean()
                    avoided_total_core_day_runtime_dailyavgHTD_baseline_regional = avoided_runtime_dailyavgHTD_baseline_regional.sum()
                    baseline_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional = baseline_regional_runtime_dailyavgHTD.mean()
                    baseline_total_core_day_runtime_dailyavgHTD_baseline_regional = baseline_regional_runtime_dailyavgHTD.sum()
                    _daily_mean_core_day_demand_baseline_dailyavgHTD_baseline_regional = np.nanmean(baseline_regional_demand_dailyavgHTD)
                    percent_savings_hourlyavgHTD_baseline_regional = savings_hourlyavgHTD_baseline_regional
                    avoided_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional = avoided_runtime_hourlyavgHTD_baseline_regional.mean()
                    avoided_total_core_day_runtime_hourlyavgHTD_baseline_regional = avoided_runtime_hourlyavgHTD_baseline_regional.sum()
                    baseline_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional = baseline_regional_runtime_hourlyavgHTD.mean()
                    baseline_total_core_day_runtime_hourlyavgHTD_baseline_regional = baseline_regional_runtime_hourlyavgHTD.sum()
                    _daily_mean_core_day_demand_baseline_hourlyavgHTD_baseline_regional = np.nanmean(baseline_regional_demand_hourlyavgHTD)

                else:

                    baseline_regional_demand_deltaT = None
                    baseline_regional_demand_dailyavgHTD = None
                    baseline_regional_demand_hourlyavgHTD = None

                    baseline_regional_runtime_deltaT = None
                    baseline_regional_runtime_dailyavgHTD = None
                    baseline_regional_runtime_hourlyavgHTD = None

                    avoided_runtime_deltaT_baseline_regional = None
                    avoided_runtime_dailyavgHTD_baseline_regional = None
                    avoided_runtime_hourlyavgHTD_baseline_regional = None

                    savings_deltaT_baseline_regional = None
                    savings_dailyavgHTD_baseline_regional = None
                    savings_hourlyavgHTD_baseline_regional = None

                    percent_savings_deltaT_heating_baseline_regional = None
                    avoided_daily_mean_core_day_runtime_deltaT_heating_baseline_regional = None
                    avoided_total_core_day_runtime_deltaT_heating_baseline_regional = None
                    baseline_daily_mean_core_day_runtime_deltaT_heating_baseline_regional = None
                    baseline_total_core_day_runtime_deltaT_heating_baseline_regional = None
                    _daily_mean_core_day_demand_baseline_deltaT_heating_baseline_regional = None
                    percent_savings_dailyavgHTD_baseline_regional = None
                    avoided_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional = None
                    avoided_total_core_day_runtime_dailyavgHTD_baseline_regional = None
                    baseline_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional = None
                    baseline_total_core_day_runtime_dailyavgHTD_baseline_regional = None
                    _daily_mean_core_day_demand_baseline_dailyavgHTD_baseline_regional = None
                    percent_savings_hourlyavgHTD_baseline_regional = None
                    avoided_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional = None
                    avoided_total_core_day_runtime_hourlyavgHTD_baseline_regional = None
                    baseline_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional = None
                    baseline_total_core_day_runtime_hourlyavgHTD_baseline_regional = None
                    _daily_mean_core_day_demand_baseline_hourlyavgHTD_baseline_regional = None


                n_days_both, n_days_insufficient_data = self.get_ignored_days(core_heating_day_set)
                n_core_heating_days = self.get_core_day_set_n_days(core_heating_day_set)
                n_days_in_inputfile_date_range = self.get_inputfile_date_range(core_heating_day_set)

                outputs = {
                    "sw_version": get_version(),

                    "ct_identifier": self.thermostat_id,
                    "equipment_type": self.equipment_type,
                    "heating_or_cooling": core_heating_day_set.name,
                    "zipcode": self.zipcode,
                    "station": self.station,
                    "climate_zone": mapping.get(self.zipcode),

                    "start_date": pd.Timestamp(core_heating_day_set.start_date).to_datetime().isoformat(),
                    "end_date": pd.Timestamp(core_heating_day_set.end_date).to_datetime().isoformat(),
                    "n_days_in_inputfile_date_range": n_days_in_inputfile_date_range,
                    "n_days_both_heating_and_cooling": n_days_both,
                    "n_days_insufficient_data": n_days_insufficient_data,
                    "n_core_heating_days": n_core_heating_days,

                    "baseline90_core_heating_comfort_temperature": baseline90_comfort_temperature,
                    "regional_average_baseline_heating_comfort_temperature": baseline_regional_heating_comfort_temperature,

                    "percent_savings_deltaT_heating_baseline90": savings_deltaT_baseline90,
                    "avoided_daily_mean_core_day_runtime_deltaT_heating_baseline90": avoided_runtime_deltaT_baseline90.mean(),
                    "avoided_total_core_day_runtime_deltaT_heating_baseline90": avoided_runtime_deltaT_baseline90.sum(),
                    "baseline_daily_mean_core_day_runtime_deltaT_heating_baseline90": baseline90_runtime_deltaT.mean(),
                    "baseline_total_core_day_runtime_deltaT_heating_baseline90": baseline90_runtime_deltaT.sum(),
                    "_daily_mean_core_day_demand_baseline_deltaT_heating_baseline90": np.nanmean(baseline90_demand_deltaT),
                    "percent_savings_deltaT_heating_baseline_regional": percent_savings_deltaT_heating_baseline_regional,
                    "avoided_daily_mean_core_day_runtime_deltaT_heating_baseline_regional": avoided_daily_mean_core_day_runtime_deltaT_heating_baseline_regional,
                    "avoided_total_core_day_runtime_deltaT_heating_baseline_regional": avoided_total_core_day_runtime_deltaT_heating_baseline_regional,
                    "baseline_daily_mean_core_day_runtime_deltaT_heating_baseline_regional": baseline_daily_mean_core_day_runtime_deltaT_heating_baseline_regional,
                    "baseline_total_core_day_runtime_deltaT_heating_baseline_regional": baseline_total_core_day_runtime_deltaT_heating_baseline_regional,
                    "_daily_mean_core_day_demand_baseline_deltaT_heating_baseline_regional": _daily_mean_core_day_demand_baseline_deltaT_heating_baseline_regional,
                    "mean_demand_deltaT_heating": np.nanmean(demand_deltaT),
                    "alpha_deltaT_heating": alpha_deltaT,
                    "tau_deltaT_heating": tau_deltaT,
                    "mean_sq_err_deltaT_heating": mse_deltaT,
                    "root_mean_sq_err_deltaT_heating": rmse_deltaT,
                    "cv_root_mean_sq_err_deltaT_heating": cvrmse_deltaT,
                    "mean_abs_pct_err_deltaT_heating": mape_deltaT,
                    "mean_abs_err_deltaT_heating": mae_deltaT,

                    "percent_savings_dailyavgHTD_baseline90": savings_dailyavgHTD_baseline90,
                    "avoided_daily_mean_core_day_runtime_dailyavgHTD_baseline90": avoided_runtime_dailyavgHTD_baseline90.mean(),
                    "avoided_total_core_day_runtime_dailyavgHTD_baseline90": avoided_runtime_dailyavgHTD_baseline90.sum(),
                    "baseline_daily_mean_core_day_runtime_dailyavgHTD_baseline90": baseline90_runtime_dailyavgHTD.mean(),
                    "baseline_total_core_day_runtime_dailyavgHTD_baseline90": baseline90_runtime_dailyavgHTD.sum(),
                    "_daily_mean_core_day_demand_baseline_dailyavgHTD_baseline90": np.nanmean(baseline90_demand_dailyavgHTD),
                    "percent_savings_dailyavgHTD_baseline_regional": percent_savings_dailyavgHTD_baseline_regional,
                    "avoided_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional": avoided_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional,
                    "avoided_total_core_day_runtime_dailyavgHTD_baseline_regional": avoided_total_core_day_runtime_dailyavgHTD_baseline_regional,
                    "baseline_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional": baseline_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional,
                    "baseline_total_core_day_runtime_dailyavgHTD_baseline_regional": baseline_total_core_day_runtime_dailyavgHTD_baseline_regional,
                    "_daily_mean_core_day_demand_baseline_dailyavgHTD_baseline_regional": _daily_mean_core_day_demand_baseline_dailyavgHTD_baseline_regional,
                    "mean_demand_dailyavgHTD": np.nanmean(demand_dailyavgHTD),
                    "tau_dailyavgHTD": tau_dailyavgHTD,
                    "alpha_dailyavgHTD": alpha_dailyavgHTD,
                    "mean_sq_err_dailyavgHTD": mse_dailyavgHTD,
                    "root_mean_sq_err_dailyavgHTD": rmse_dailyavgHTD,
                    "cv_root_mean_sq_err_dailyavgHTD": cvrmse_dailyavgHTD,
                    "mean_abs_pct_err_dailyavgHTD": mape_dailyavgHTD,
                    "mean_abs_err_dailyavgHTD": mae_dailyavgHTD,

                    "percent_savings_hourlyavgHTD_baseline90": savings_hourlyavgHTD_baseline90,
                    "avoided_daily_mean_core_day_runtime_hourlyavgHTD_baseline90": avoided_runtime_hourlyavgHTD_baseline90.mean(),
                    "avoided_total_core_day_runtime_hourlyavgHTD_baseline90": avoided_runtime_hourlyavgHTD_baseline90.sum(),
                    "baseline_daily_mean_core_day_runtime_hourlyavgHTD_baseline90": baseline90_runtime_hourlyavgHTD.mean(),
                    "baseline_total_core_day_runtime_hourlyavgHTD_baseline90": baseline90_runtime_hourlyavgHTD.sum(),
                    "_daily_mean_core_day_demand_baseline_hourlyavgHTD_baseline90": np.nanmean(baseline90_demand_hourlyavgHTD),
                    "percent_savings_hourlyavgHTD_baseline_regional": savings_hourlyavgHTD_baseline_regional,
                    "avoided_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional": avoided_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional,
                    "avoided_total_core_day_runtime_hourlyavgHTD_baseline_regional": avoided_total_core_day_runtime_hourlyavgHTD_baseline_regional,
                    "baseline_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional": baseline_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional,
                    "baseline_total_core_day_runtime_hourlyavgHTD_baseline_regional": baseline_total_core_day_runtime_hourlyavgHTD_baseline_regional,
                    "_daily_mean_core_day_demand_baseline_hourlyavgHTD_baseline_regional": _daily_mean_core_day_demand_baseline_hourlyavgHTD_baseline_regional,
                    "mean_demand_hourlyavgHTD": np.nanmean(demand_hourlyavgHTD),
                    "tau_hourlyavgHTD": tau_hourlyavgHTD,
                    "alpha_hourlyavgHTD": alpha_hourlyavgHTD,
                    "mean_sq_err_hourlyavgHTD": mse_hourlyavgHTD,
                    "root_mean_sq_err_hourlyavgHTD": rmse_hourlyavgHTD,
                    "cv_root_mean_sq_err_hourlyavgHTD": cvrmse_hourlyavgHTD,
                    "mean_abs_pct_err_hourlyavgHTD": mape_hourlyavgHTD,
                    "mean_abs_err_hourlyavgHTD": mae_hourlyavgHTD,

                    "total_core_heating_runtime": total_runtime_core_heating,

                    "daily_mean_core_heating_runtime": average_daily_heating_runtime,
                }


                if self.equipment_type in self.AUX_EMERG_EQUIPMENT_TYPES:

                    additional_outputs = {
                        "total_auxiliary_heating_core_day_runtime":
                            self.total_auxiliary_heating_runtime(
                                core_heating_day_set),
                        "total_emergency_heating_core_day_runtime":
                            self.total_emergency_heating_runtime(
                                core_heating_day_set),
                    }

                    rhus = self.get_resistance_heat_utilization_bins(core_heating_day_set)

                    if rhus is None:
                        for low, high in [(i, i+5) for i in range(0, 60, 5)]:
                            column = "rhu_{:02d}F_to_{:02d}F".format(low, high)
                            additional_outputs[column] = None
                    else:
                        for rhu, (low, high) in zip(rhus, [(i, i+5) for i in range(0, 60, 5)]):
                            column = "rhu_{:02d}F_to_{:02d}F".format(low, high)
                            additional_outputs[column] = rhu

                    outputs.update(additional_outputs)
                metrics.append(outputs)

        return metrics
