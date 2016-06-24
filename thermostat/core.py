import pandas as pd
import numpy as np
from scipy.optimize import leastsq

from datetime import datetime, timedelta
from collections import namedtuple

from thermostat.regression import runtime_regression
from thermostat.savings import get_daily_avoided_runtime
from thermostat.savings import get_seasonal_percent_savings

import inspect

Season = namedtuple("Season", ["name", "daily", "hourly", "start_date", "end_date"])

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

    def get_heating_seasons(self, method="entire_dataset",
            min_minutes_heating=60, max_minutes_cooling=0):
        """ Get all data for heating seasons for data associated with this
        thermostat

        Parameters
        ----------
        method : {"entire_dataset", "year_mid_to_mid"}, default: "entire_dataset"
            Method by which to find heating seasons.

            - "entire_dataset": all heating days in dataset (days with >= 1
              hour of heating runtime and no cooling runtime.
            - "year_mid_to_mid": groups all heating days (days with >= 1 hour
              of total heating and no cooling) from July 1 to June 30
              (inclusive) into individual heating seasons. May overlap with
              cooling seasons.
        min_minutes_heating : int, default 60
            Number of minutes of heating runtime per day required for inclusion
            in season.
        max_minutes_cooling : int, default 0
            Number of minutes of cooling runtime per day beyond which for day
            is considered part of a shoulder season (and is therefore not part
            of the heating season).

        Returns
        -------
        seasons : list of thermostat.core.Season objects
            List of seasons detected; first element of tuple is season, second
            is name. Seasons are represented as pandas Series of boolean values,
            intended to be used as selectors or masks on the thermostat data.
            A value of True at a particular index indicates inclusion of
            of the data at that index in the season. If method is
            "entire_dataset", name of season is "All Heating"; if method
            is "year_mid_to_mid", names of seasons are of the form
            "YYYY-YYYY Heating"
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
            # find all potential heating season ranges
            start_year = data_start_date.item().year - 1
            end_year = data_end_date.item().year + 1
            potential_seasons = zip(range(start_year, end_year),
                                    range(start_year + 1, end_year + 1))

            # for each potential season, look for heating days.
            seasons = []
            for start_year_, end_year_ in potential_seasons:
                season_start_date = np.datetime64(datetime(start_year_, 7, 1))
                season_end_date = np.datetime64(datetime(end_year_, 7, 1))
                start_date = max(season_start_date, data_start_date).item()
                end_date = min(season_end_date, data_end_date).item()
                in_range = self._get_range_boolean(self.heat_runtime.index,
                        start_date, end_date)
                inclusion_daily = pd.Series(in_range & meets_thresholds,
                        index=self.heat_runtime.index)

                if any(inclusion_daily):
                    name = "{}-{} Heating".format(start_year_, end_year_)
                    inclusion_hourly = self._get_hourly_boolean(inclusion_daily)
                    season = Season(name, inclusion_daily, inclusion_hourly,
                            start_date, end_date)
                    seasons.append(season)

            return seasons
        elif method == "entire_dataset":
            inclusion_daily = pd.Series(meets_thresholds, index=self.heat_runtime.index)
            inclusion_hourly = self._get_hourly_boolean(inclusion_daily)
            season = Season("All Heating", inclusion_daily, inclusion_hourly,
                    data_start_date, data_end_date)
            # returned as list for consistency
            return [season]

    def get_cooling_seasons(self, method="entire_dataset",
            min_minutes_cooling=60, max_minutes_heating=0):
        """ Get all data for cooling seasons for data associated with this
        thermostat.

        Parameters
        ----------
        method : {"entire_dataset", "year_end_to_end"}, default: "entire_dataset"
            Method by which to find cooling seasons.

            - "entire_dataset": all cooling days in dataset (days with >= 1
              hour of cooling runtime and no heating runtime.
            - "year_end_to_end": groups all cooling days (days with >= 1 hour
              of total cooling and no heating) from January 1 to December 31
              into individual cooling seasons.
        min_minutes_cooling : int, default 0
            Number of minutes of cooling runtime per day required for inclusion in season.
        max_minutes_heating : int, default 0
            Number of minutes of heating runtime per day beyond which for day is
            considered part of a shoulder season (and is therefore not part of
            the cooling season).

        Returns
        -------
        seasons : list of thermostat.core.Season objects
            List of seasons detected; first element of tuple is season, second
            is name. Seasons are represented as pandas Series of boolean
            values, intended to be used as selectors or masks on the thermostat
            data. A value of True at a particular index indicates inclusion of
            of the data at that index in the season. If method is
            "entire_dataset", name of season is "All Cooling"; if method
            == "year_end_to_end", names of seasons are of the form
            "YYYY Cooling"
        """
        if method not in ["year_end_to_end", "entire_dataset"]:
            raise NotImplementedError

        self._protect_cooling()

        # find all potential cooling season ranges
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
            potential_seasons = range(start_year, end_year + 1)


            # for each potential season, look for cooling days.
            seasons = []
            for year in potential_seasons:
                season_start_date = np.datetime64(datetime(year, 1, 1))
                season_end_date = np.datetime64(datetime(year + 1, 1, 1))
                start_date = max(season_start_date, data_start_date).item()
                end_date = min(season_end_date, data_end_date).item()
                in_range = self._get_range_boolean(self.cool_runtime.index,
                        start_date, end_date)
                inclusion_daily = pd.Series(in_range & meets_thresholds,
                        index=self.cool_runtime.index)

                if any(inclusion_daily):
                    name = "{} Cooling".format(year)
                    inclusion_hourly = self._get_hourly_boolean(inclusion_daily)
                    season = Season(name, inclusion_daily, inclusion_hourly,
                            start_date, end_date)
                    seasons.append(season)

            return seasons
        elif method == "entire_dataset":
            inclusion_daily = pd.Series(meets_thresholds, index=self.cool_runtime.index)
            inclusion_hourly = self._get_hourly_boolean(inclusion_daily)
            season = Season("All Cooling", inclusion_daily, inclusion_hourly,
                    data_start_date, data_end_date)
            return [season]

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

    def total_heating_runtime(self, season):
        """ Calculates total heating runtime.

        Parameters
        ----------
        season : pandas.Series
            Season for which to calculate total runtime.

        Returns
        -------
        total_runtime : float
            Total heating runtime.
        """
        self._protect_heating()
        return self.heat_runtime[season.daily].sum()

    def total_auxiliary_heating_runtime(self, season):
        """ Calculates total auxiliary heating runtime.

        Parameters
        ----------
        season : pandas.Series
            Season for which to calculate total runtime.

        Returns
        -------
        total_runtime : float
            Total auxiliary heating runtime.
        """
        self._protect_aux_emerg()
        return self.auxiliary_heat_runtime[season.hourly].sum()

    def total_emergency_heating_runtime(self, season):
        """ Calculates total emergency heating runtime.

        Parameters
        ----------
        season : pandas.Series
            Season for which to calculate total runtime.

        Returns
        -------
        total_runtime : float
            Total heating runtime.
        """
        self._protect_aux_emerg()
        return self.emergency_heat_runtime[season.hourly].sum()

    def total_cooling_runtime(self, season):
        """ Calculates total cooling runtime.

        Parameters
        ----------
        season : pandas.Series
            Season for which to calculate total runtime.

        Returns
        -------
        total_runtime : float
            Total cooling runtime.
        """
        self._protect_cooling()
        return self.cool_runtime[season.daily].sum()

    def get_resistance_heat_utilization_bins(self, season):
        """ Calculates resistance heat utilization metrics in temperature
        bins of 5 degrees between 0 and 60 degrees Fahrenheit.

        Parameters
        ----------
        heating_season : pandas.Series
            Heating season for which to calculate resistance heat utilization.

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

            in_season = self._get_range_boolean(season.hourly.index,
                    season.start_date, season.end_date)

            temperature_bins = [(i, i+5) for i in range(0, 60, 5)]
            for low_temp, high_temp in temperature_bins:
                temp_low_enough = self.temperature_out < high_temp
                temp_high_enough = self.temperature_out >= low_temp
                temp_bin = temp_low_enough & temp_high_enough & in_season
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

    def get_season_ignored_days(self, season):

        in_range = self._get_range_boolean(season.daily.index,
                season.start_date, season.end_date)

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


    def get_season_n_days(self, season):
        return int(season.daily.sum())

    def get_season_n_days_in_range(self, season):
        delta = (season.end_date - season.start_date)
        if isinstance(delta, timedelta):
            return delta.days
        else:
            return int(delta.astype('timedelta64[D]') / np.timedelta64(1, 'D'))

    ##################### DEMAND ################################

    def get_cooling_demand(self, cooling_season, method="deltaT"):
        """
        Calculates a measure of cooling demand.

        Parameters
        ----------
        cooling_season : thermostat.Season
            Season over which to calculate cooling demand.
        method : {"deltaT", "dailyavgCDD", "hourlyavgCDD"}, default: "deltaT"
            The method to use during calculation of demand.

            - "deltaT": :math:`-\Delta T` where :math:`\Delta T = T_{in} - T_{out}`
            - "dailyavgCDD": :math:`\\text{daily CDD} = \\text{max} \left(
              \Delta T_{\\text{base cool}} - \Delta T_{\\text{daily avg}}
              , 0\\right)`
              where :math:`\Delta T_{\\text{daily avg}} =
              \\frac{\sum_{i=1}^{24} \Delta T_i}{24}`
            - "hourlyavgCDD": :math:`\\text{daily CDD} = \sum_{i=1}^{24} \\text{CDH}_i`
              where :math:`\\text{CDH}_i = \\text{max}\left(
              \Delta T_{\\text{base cool}} - \Delta T_i, 0\\right)`


        Returns
        -------
        demand : pd.Series
            Daily demand in the heating season as calculated using one of
            the supported methods.
        deltaT_base_estimate : float
            Estimate of :math:`\Delta T_{\\text{base cool}}`. Only output for
            "hourlyavgCDD" and "dailyavgCDD".
        alpha_estimate : float
            Estimate of linear runtime response to demand. Only output for
            "hourlyavgCDD" and "dailyavgCDD".
        mean_squared_error : float
            Mean squared error in runtime estimates. Only output for "hourlyavgCDD"
            and "dailyavgCDD".
        """

        self._protect_cooling()

        season_temp_in = self.temperature_in[cooling_season.hourly]
        season_temp_out = self.temperature_out[cooling_season.hourly]
        season_deltaT = season_temp_in - season_temp_out

        daily_avg_deltaT = np.array([temps.mean() for day, temps in season_deltaT.groupby(season_deltaT.index.date)])

        daily_index = cooling_season.daily[cooling_season.daily].index

        if method == "deltaT":
            return pd.Series(-daily_avg_deltaT, index=daily_index)
        elif method == "dailyavgCDD":
            def calc_cdd(deltaT_base):
                return np.maximum(deltaT_base - daily_avg_deltaT, 0)
        elif method == "hourlyavgCDD":
            def calc_cdd(deltaT_base):
                hourly_cdd = (deltaT_base - season_deltaT).apply(lambda x: np.maximum(x, 0))
                # Note - `x / 24` this should be thought of as a unit conversion, not an average.
                return np.array([cdd.sum() / 24 for day, cdd in hourly_cdd.groupby(season_deltaT.index.date)])
        else:
            raise NotImplementedError

        daily_runtime = self.cool_runtime[cooling_season.daily]
        total_runtime = daily_runtime.sum()

        def calc_estimates(deltaT_base):
            cdd = calc_cdd(deltaT_base)
            total_cdd = np.sum(cdd)
            alpha_estimate = total_runtime / total_cdd
            runtime_estimate = cdd * alpha_estimate
            errors = daily_runtime - runtime_estimate
            return cdd, alpha_estimate, errors

        def estimate_errors(deltaT_base_estimate):
            _, _, errors = calc_estimates(deltaT_base_estimate)
            return errors

        deltaT_base_starting_guess = 0
        try:
            y, _ = leastsq(estimate_errors, deltaT_base_starting_guess)
        except TypeError: # len 0
            assert daily_runtime.shape[0] == 0 # make sure no other type errors are sneaking in
            return pd.Series([], index=daily_index), np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

        deltaT_base_estimate = y[0]

        cdd, alpha_estimate, errors = calc_estimates(deltaT_base_estimate)
        mse = np.nanmean((errors)**2)
        rmse = mse ** 0.5
        mean_daily_runtime = np.nanmean(daily_runtime)
        cvrmse = rmse / mean_daily_runtime
        mape = np.nanmean(np.absolute(errors / mean_daily_runtime))
        mae = np.nanmean(np.absolute(errors))

        return pd.Series(cdd, index=daily_index), deltaT_base_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae

    def get_heating_demand(self, heating_season, method="deltaT"):
        """
        Calculates a measure of heating demand.

        Parameters
        ----------
        heating_season : array_like
            Season over which to calculate heating demand.
        method : {"deltaT", "hourlyavgHDD", "dailyavgHDD"} default: "deltaT"
            The method to use during calculation of demand.

            - "deltaT": :math:`\Delta T = T_{in} - T_{out}`
            - "dailyavgHDD": :math:`\\text{daily HDD} = \\text{max}\left(
              \Delta T_{\\text{daily avg}} - \Delta T_{\\text{base heat}}
              , 0\\right)` where
              :math:`\Delta T_{\\text{daily avg}} =
              \\frac{\sum_{i=1}^{24} \Delta T_i}{24}`
            - "hourlyavgHDD": :math:`\\text{daily HDD} = \sum_{i=1}^{24} \\text{HDH}_i`
              where :math:`\\text{HDH}_i = \\text{max}\left(
              \Delta T_i - \Delta T_{\\text{base heat}}
              , 0\\right)`

        Returns
        -------
        demand : pd.Series
            Daily demand in the heating season as calculated using one of
            the supported methods.
        deltaT_base_estimate : float
            Estimate of :math:`\Delta T_{\\text{base heat}}`. Only output for
            "hourlyavgHDD" and "dailyavgHDD".
        alpha_estimate : float
            Estimate of linear runtime response to demand. Only output for
            "hourlyavgHDD" and "dailyavgHDD".
        mean_squared_error : float
            Mean squared error in runtime estimates. Only output for "hourlyavgHDD"
            and "dailyavgHDD".
        """

        self._protect_heating()

        season_temp_in = self.temperature_in[heating_season.hourly]
        season_temp_out = self.temperature_out[heating_season.hourly]
        season_deltaT = season_temp_in - season_temp_out

        daily_avg_deltaT = np.array([temps.mean() for day, temps in season_deltaT.groupby(season_deltaT.index.date)])

        daily_index = heating_season.daily[heating_season.daily].index

        if method == "deltaT":
            return pd.Series(daily_avg_deltaT, index=daily_index)
        elif method == "dailyavgHDD":
            def calc_hdd(deltaT_base):
                return np.maximum(daily_avg_deltaT - deltaT_base, 0)
        elif method == "hourlyavgHDD":
            def calc_hdd(deltaT_base):
                hourly_hdd = (season_deltaT - deltaT_base).apply(lambda x: np.maximum(x, 0))
                # Note - this `x / 24` should be thought of as a unit conversion, not an average.
                return np.array([hdd.sum() / 24 for day, hdd in hourly_hdd.groupby(season_deltaT.index.date)])
        else:
            raise NotImplementedError

        daily_runtime = self.heat_runtime[heating_season.daily]
        total_runtime = daily_runtime.sum()

        def calc_estimates(deltaT_base):
            hdd = calc_hdd(deltaT_base)
            total_hdd = np.sum(hdd)
            alpha_estimate = total_runtime / total_hdd
            runtime_estimate = hdd * alpha_estimate
            errors = daily_runtime - runtime_estimate
            return hdd, alpha_estimate, errors

        def estimate_errors(deltaT_base_estimate):
            _, _, errors = calc_estimates(deltaT_base_estimate)
            return errors

        deltaT_base_starting_guess = 0

        try:
            y, _ = leastsq(estimate_errors, deltaT_base_starting_guess)
        except TypeError: # len 0
            assert daily_runtime.shape[0] == 0 # make sure no other type errors are sneaking in
            return pd.Series([], index=daily_index), np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan

        deltaT_base_estimate = y[0]

        hdd, alpha_estimate, errors = calc_estimates(deltaT_base_estimate)
        mse = np.nanmean((errors)**2)
        rmse = mse ** 0.5
        mean_daily_runtime = np.nanmean(daily_runtime)
        cvrmse = rmse / mean_daily_runtime
        mape = np.nanmean(np.absolute(errors / mean_daily_runtime))
        mae = np.nanmean(np.absolute(errors))

        return (
            pd.Series(hdd, index=daily_index),
            deltaT_base_estimate,
            alpha_estimate,
            mse,
            rmse,
            cvrmse,
            mape,
            mae
        )

    ################## BASELINING ##########################

    def get_cooling_season_baseline_setpoint(self, cooling_season,
            method='tenth_percentile', source='cooling_setpoint'):
        """ Calculate the cooling season baseline setpoint (comfort
        temperature).

        Parameters
        ----------
        cooling_season : array_like
            Cooling season over which to calculate baseline cooling setpoint.
        method : {"tenth_percentile"}, default: "tenth_percentile"
            Method to use in calculation of the baseline.

            - "tenth_percentile": 10th percentile of source temperature.
              (Either cooling setpoint or temperature in).
        source : {"cooling_setpoint", "temperature_in"}, default "cooling_setpoint"
            The source of temperatures to use in baseline calculation.

        Returns
        -------
        baseline : pandas.Series
            The baseline cooling setpoint for the cooling season as determined
            by the given method.
        """

        self._protect_cooling()

        if method == 'tenth_percentile':

            if source == 'cooling_setpoint':
                return self.cooling_setpoint[cooling_season.hourly].dropna().quantile(.1)
            elif source == 'temperature_in':
                return self.temperature_in[cooling_season.hourly].dropna().quantile(.1)
            else:
                raise NotImplementedError

        else:
            raise NotImplementedError


    def get_heating_season_baseline_setpoint(self, heating_season, method='ninetieth_percentile', source='heating_setpoint'):
        """ Calculate the heating season baseline setpoint (comfort temperature).

        Parameters
        ----------
        heating_season : array_like
            Heating season over which to calculate baseline heating setpoint.
        method : {"ninetieth_percentile"}, default: "ninetieth_percentile"
            Method to use in calculation of the baseline.

            - "ninetieth_percentile": 90th percentile of source temperature.
              (Either heating setpoint or indoor temperature).
        source : {"heating_setpoint", "temperature_in"}, default "heating_setpoint"
            The source of temperatures to use in baseline calculation.

        Returns
        -------
        baseline : pandas.Series
            The baseline heating setpoint for the heating season as determined
            by the given method.
        """

        self._protect_heating()

        if method == 'ninetieth_percentile':

            if source == 'heating_setpoint':
                return self.heating_setpoint[heating_season.hourly].dropna().quantile(.9)
            elif source == 'temperature_in':
                return self.temperature_in[heating_season.hourly].dropna().quantile(.9)
            else:
                raise NotImplementedError

        else:
            raise NotImplementedError


    def get_baseline_cooling_demand(self, cooling_season,
            deltaT_base=None, method="deltaT"):
        """ Calculate baseline cooling degree days for a particular cooling
        season and baseline setpoint.

        Parameters
        ----------
        cooling_season : array_like
            Should be an array of booleans with the same length as the data stored
            in the given thermostat object. True indicates presence in the cooling
            season.
        deltaT_base : float, default: None
            Used in calculations for "dailyavgHDD" and "hourlyavgHDD".
        method : {"deltaT", "dailyavgCDD", "hourlyavgCDD"}; default: "deltaT"
            Method to use in calculation of the baseline cdd.

            - "deltaT": :math:`\Delta T_{\\text{base cool}} = \\text{daily avg }
              T_{\\text{outdoor}} - T_{\\text{base cool}}`
            - "dailyavgCDD": :math:`\\text{CDD}_{\\text{base}} = \Delta T_{\\text{base
              cool}} - \Delta T_{\\text{b cool}}` where :math:`\Delta T_{\\text{base
              cool}} = \\text{daily avg } T_{\\text{outdoor}} - T_{\\text{base cool}}`
            - "hourlyavgCDD": :math:`\\text{CDD}_{\\text{base}} = \\frac{\sum_{i=1}^
              {24} \\text{CDH}_{\\text{base } i}}{24}` where :math:`\\text{CDH}_{
              \\text{base } i} = \Delta T_{\\text{base cool}} - \Delta T_{\\text{b
              cool}}` and :math:`\Delta T_{\\text{base cool}} = T_{\\text{outdoor}}
              - T_{\\text{base cool}}`

        Returns
        -------
        baseline_cooling_demand : pandas.Series
            A series containing baseline daily heating demand for the cooling season.
        """
        self._protect_cooling()

        temp_baseline = self.get_cooling_season_baseline_setpoint(cooling_season)
        hourly_temp_out = self.temperature_out[cooling_season.hourly]

        daily_temp_out = np.array([temps.mean() for day, temps in hourly_temp_out.groupby(hourly_temp_out.index.date)])

        if method == "deltaT":
            demand = daily_temp_out - temp_baseline
        elif method == "dailyavgCDD":
            demand = np.maximum(deltaT_base - (temp_baseline - daily_temp_out), 0)
        elif method == "hourlyavgCDD":
            hourly_cdd = (deltaT_base - (temp_baseline - hourly_temp_out)).apply(lambda x: np.maximum(x, 0))
            demand = np.array([cdd.sum() / 24 for day, cdd in hourly_cdd.groupby(hourly_temp_out.index.date)])
        else:
            raise NotImplementedError
        index = cooling_season.daily[cooling_season.daily].index
        return pd.Series(demand, index=index)

    def get_baseline_heating_demand(self, heating_season,
            deltaT_base=None, method="deltaT"):
        """ Calculate baseline heating degree days for a particular heating season
        and baseline setpoint.

        Parameters
        ----------
        heating_season : array_like
            Should be an array of booleans with the same length as the data stored
            in the given thermostat object. True indicates presence in the heating
            season.
        deltaT_base : float, default: None
            Used in calculations for "dailyavgHDD" and "hourlyavgHDD".
        method : {"deltaT", "dailyavgHDD", "hourlyavgHDD"}; default: "deltaT"
            Method to use in calculation of the baseline cdd.

            - "deltaT": :math:`\Delta T_{\\text{base heat}} = T_{\\text{base heat}}
              - \\text{daily avg } T_{\\text{outdoor}}`
            - "dailyavgHDD": :math:`\\text{HDD}_{\\text{base}} = \Delta T_{\\text{base
              heat}} - \Delta T_{\\text{b heat}}` where :math:`\Delta T_{\\text{base
              heat}} = T_{\\text{base heat}} - \\text{daily avg } T_{\\text{outdoor}}`
            - "hourlyavgHDD": :math:`\\text{HDD}_{\\text{base}} = \\frac{\sum_{i=1}^
              {24} \\text{HDH}_{\\text{base } i}}{24}` where :math:`\\text{HDH}_{
              \\text{base } i} = \Delta T_{\\text{base heat}} - \Delta T_{\\text{b
              heat}}` and :math:`\Delta T_{\\text{base heat}} = T_{\\text{base heat}}
              - T_{\\text{outdoor}}`

        Returns
        -------
        baseline_heating_demand : pandas.Series
            A series containing baseline daily heating demand for the heating season.
        """
        self._protect_heating()

        temp_baseline = self.get_heating_season_baseline_setpoint(heating_season)
        hourly_temp_out = self.temperature_out[heating_season.hourly]

        daily_temp_out = np.array([temps.mean() for day, temps in hourly_temp_out.groupby(hourly_temp_out.index.date)])

        if method == "deltaT":
            demand = temp_baseline - daily_temp_out
        elif method == "dailyavgHDD":
            demand = np.maximum(temp_baseline - daily_temp_out - deltaT_base, 0)
        elif method == "hourlyavgHDD":
            hourly_hdd = (temp_baseline - hourly_temp_out - deltaT_base).apply(lambda x: np.maximum(x, 0))
            demand = np.array([hdd.sum() / 24 for day, hdd in hourly_hdd.groupby(hourly_temp_out.index.date)])
        else:
            raise NotImplementedError
        index = heating_season.daily[heating_season.daily].index
        return pd.Series(demand, index=index)

    ######################### SAVINGS ###############################

    def get_total_baseline_cooling_runtime(self, cooling_season, daily_avoided_runtime):
        """ Estimate baseline cooling runtime given a daily avoided runtimes.

        Parameters
        ----------
        cooling_season : pandas.Series
            Timeseries of booleans in hourly resolution representing the cooling
            season for which to estimate total baseline cooling.
        daily_avoided_runtime : pandas.Series
            Timeseries of daily avoided runtime for a particular cooling season.

        Returns
        -------
        total_baseline_cooling_runtime : pandas.Series
            Total baseline cooling runtime for the given season and thermostat.
        """
        self._protect_cooling()

        total_avoided_runtime = daily_avoided_runtime.sum()
        total_actual_runtime = self.cool_runtime[cooling_season.daily].sum()

        return total_actual_runtime - total_avoided_runtime

    def get_total_baseline_heating_runtime(self, heating_season, daily_avoided_runtime):
        """ Estimate baseline heating runtime given a daily avoided runtimes.

        Parameters
        ----------
        heating_season : pandas.Series
            Timeseries of booleans in hourly resolution representing the heating
            season for which to estimate total baseline heating.
        daily_avoided_runtime : pandas.Series
            Timeseries of daily avoided runtime for a particular heating season.

        Returns
        -------
        total_baseline_heating_runtime : pandas.Series
            Total baseline heating runtime for the given season and thermostat.
        """
        self._protect_heating()

        total_avoided_runtime = daily_avoided_runtime.sum()
        total_actual_runtime = self.heat_runtime[heating_season.daily].sum()

        return total_actual_runtime - total_avoided_runtime

    def get_baseline_cooling_runtime(self, baseline_cooling_demand, alpha, tau, method="deltaT"):
        """ Calculate baseline heating runtime given baseline cooling demand
        and fitted physical parameters.

        Parameters
        ----------
        cooling_demand : pandas.Series
            A series containing estimated daily baseline cooling demand.

        Returns
        -------
        baseline_cooling_runtime : pandas.Series
            A series containing estimated daily baseline cooling runtime.
        """
        if method == "deltaT":
             return np.maximum(alpha * (baseline_cooling_demand + tau), 0)
        elif method in ["dailyavgCDD", "hourlyavgCDD"]:
            # np.maximum is in case alpha negative for some reason, or if bad
            # demand data (not strictly non-negative) is used
            return np.maximum(alpha * (baseline_cooling_demand), 0)
        else:
            message = (
                "Method should be one of `deltaT`, `dailyavgCDD`, or `hourlyavgCDD`"
            )
            raise NotImplementedError(message)

    def get_baseline_heating_runtime(self, baseline_heating_demand, alpha, tau, method=True):
        """ Calculate baseline heating runtime given baseline heating demand.
        and fitted physical parameters.

        Parameters
        ----------
        heating_demand : pandas.Series
            A series containing estimated daily baseline heating demand.

        Returns
        -------
        baseline_heating_runtime : pandas.Series
            A series containing estimated daily baseline heating runtime.
        """
        if method == "deltaT":
             return np.maximum(alpha * (baseline_heating_demand - tau), 0)
        elif method in ["dailyavgHDD", "hourlyavgHDD"]:
            # np.maximum is in case alpha negative for some reason, or if bad
            # demand data (not strictly non-negative) is used
            return np.maximum(alpha * (baseline_heating_demand), 0)
        else:
            message = (
                "Method should be one of `deltaT`, `dailyavgHDD`, or `hourlyavgHDD`"
            )
            raise NotImplementedError(message)

    def get_daily_avoided_cooling_runtime(self, baseline_runtime, cooling_season):
        return baseline_runtime - self.cool_runtime[cooling_season]

    def get_daily_avoided_heating_runtime(self, baseline_runtime, heating_season):
        return baseline_runtime - self.heat_runtime[heating_season]

    ###################### Metrics #################################

    def calculate_epa_draft_rccs_field_savings_metrics(self,
            cooling_season_method="entire_dataset",
            heating_season_method="entire_dataset"):
        """ Calculates metrics for connected thermostat savings as defined by
        the draft specification defined by the EPA and stakeholders during early
        2015.

        Parameters
        ----------
        cooling_season_method : {"entire_dataset", "year_end_to_end"}, default: "entire_dataset"
            Method by which to find cooling seasons.

            - "entire_dataset": all cooling days in dataset (days with >= 1
              hour of cooling runtime and no heating runtime.
            - "year_end_to_end": groups all cooling days (days with >= 1 hour of total
              cooling and no heating) from January 1 to December 31 into
              individual cooling seasons.
        heating_season_method : {"entire_dataset", "year_mid_to_mid"}, default: "entire_dataset"
            Method by which to find cooling seasons.

            - "entire_dataset": all heating days in dataset (days with >= 1
              hour of heating runtime and no cooling runtime.
            - "year_mid_to_mid": groups all heating days (days with >= 1 hour
              of total heating and no cooling) from July 1 to June 30 into
              individual heating seasons.

        Returns
        -------
        seasonal_metrics : list
            list of dictionaries of output metrics; one per season.
        """
        seasonal_metrics = []

        if self.equipment_type in self.COOLING_EQUIPMENT_TYPES:
            for cooling_season in self.get_cooling_seasons(
                    method=cooling_season_method):

                baseline_comfort_temperature = \
                    self.get_cooling_season_baseline_setpoint(cooling_season)

                # Calculate demand
                daily_runtime = self.cool_runtime[cooling_season.daily]
                demand_deltaT = self.get_cooling_demand(cooling_season,
                        method="deltaT")

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

                # dailyavgCDD
                (
                    demand_dailyavgCDD,
                    tau_dailyavgCDD,
                    alpha_dailyavgCDD,
                    mse_dailyavgCDD,
                    rmse_dailyavgCDD,
                    cvrmse_dailyavgCDD,
                    mape_dailyavgCDD,
                    mae_dailyavgCDD,
                ) = self.get_cooling_demand(
                        cooling_season, method="dailyavgCDD")

                # hourlyavgCDD
                (
                    demand_hourlyavgCDD,
                    tau_hourlyavgCDD,
                    alpha_hourlyavgCDD,
                    mse_hourlyavgCDD,
                    rmse_hourlyavgCDD,
                    cvrmse_hourlyavgCDD,
                    mape_hourlyavgCDD,
                    mae_hourlyavgCDD,
                ) = self.get_cooling_demand(
                        cooling_season, method="hourlyavgCDD")

                actual_seasonal_runtime = daily_runtime.sum()
                n_days = cooling_season.daily.sum()
                actual_daily_runtime = actual_seasonal_runtime / n_days

                baseline_demand_deltaT = \
                    self.get_baseline_cooling_demand(
                        cooling_season,
                        deltaT_base=None,
                        method="deltaT")
                baseline_demand_dailyavgCDD = \
                    self.get_baseline_cooling_demand(
                        cooling_season,
                        deltaT_base=tau_dailyavgCDD,
                        method="dailyavgCDD")
                baseline_demand_hourlyavgCDD = \
                    self.get_baseline_cooling_demand(
                        cooling_season,
                        deltaT_base=tau_hourlyavgCDD,
                        method="hourlyavgCDD")

                baseline_runtime_deltaT = \
                    self.get_baseline_cooling_runtime(
                        baseline_demand_deltaT,
                        alpha_deltaT,
                        tau_deltaT,
                        method="deltaT")
                baseline_runtime_dailyavgCDD = \
                    self.get_baseline_cooling_runtime(
                        baseline_demand_dailyavgCDD,
                        alpha_dailyavgCDD,
                        tau_dailyavgCDD,
                        method="dailyavgCDD")
                baseline_runtime_hourlyavgCDD = \
                    self.get_baseline_cooling_runtime(
                        baseline_demand_hourlyavgCDD,
                        alpha_hourlyavgCDD,
                        tau_hourlyavgCDD,
                        method="hourlyavgCDD")

                def avoided(baseline, observed):
                    return baseline - observed

                avoided_runtime_deltaT = avoided(
                    baseline_runtime_deltaT, daily_runtime)
                avoided_runtime_dailyavgCDD = avoided(
                    baseline_runtime_dailyavgCDD, daily_runtime)
                avoided_runtime_hourlyavgCDD = avoided(
                    baseline_runtime_hourlyavgCDD, daily_runtime)

                def percent_savings(avoided, baseline):
                    return (avoided.mean() / baseline.mean()) * 100.0

                savings_deltaT = percent_savings(
                    avoided_runtime_deltaT,
                    baseline_runtime_deltaT)
                savings_dailyavgCDD = percent_savings(
                    avoided_runtime_dailyavgCDD,
                    baseline_runtime_dailyavgCDD)
                savings_hourlyavgCDD = percent_savings(
                    avoided_runtime_hourlyavgCDD,
                    baseline_runtime_hourlyavgCDD)

                n_days_both, n_days_insufficient_data = self.get_season_ignored_days(cooling_season)
                n_days_in_season = self.get_season_n_days(cooling_season)
                n_days_in_season_range = self.get_season_n_days_in_range(cooling_season)

                outputs = {
                    "ct_identifier": self.thermostat_id,
                    "zipcode": self.zipcode,
                    "station": self.station,
                    "equipment_type": self.equipment_type,
                    "baseline_comfort_temperature":
                        baseline_comfort_temperature,

                    "mean_demand_deltaT": np.nanmean(demand_deltaT),
                    "alpha_deltaT": alpha_deltaT,
                    "tau_deltaT": tau_deltaT,
                    "mean_sq_err_deltaT": mse_deltaT,
                    "root_mean_sq_err_deltaT": rmse_deltaT,
                    "cv_root_mean_sq_err_deltaT": cvrmse_deltaT,
                    "mean_abs_pct_err_deltaT": mape_deltaT,
                    "mean_abs_err_deltaT": mae_deltaT,

                    "mean_demand_dailyavgCDD": np.nanmean(demand_dailyavgCDD),
                    "tau_dailyavgCDD": tau_dailyavgCDD,
                    "alpha_dailyavgCDD": alpha_dailyavgCDD,
                    "mean_sq_err_dailyavgCDD": mse_dailyavgCDD,
                    "root_mean_sq_err_dailyavgCDD": rmse_dailyavgCDD,
                    "cv_root_mean_sq_err_dailyavgCDD": cvrmse_dailyavgCDD,
                    "mean_abs_pct_err_dailyavgCDD": mape_dailyavgCDD,
                    "mean_abs_err_dailyavgCDD": mae_dailyavgCDD,

                    "mean_demand_hourlyavgCDD":
                        np.nanmean(demand_hourlyavgCDD),
                    "tau_hourlyavgCDD": tau_hourlyavgCDD,
                    "alpha_hourlyavgCDD": alpha_hourlyavgCDD,
                    "mean_sq_err_hourlyavgCDD": mse_hourlyavgCDD,
                    "root_mean_sq_err_hourlyavgCDD": rmse_hourlyavgCDD,
                    "cv_root_mean_sq_err_hourlyavgCDD": cvrmse_hourlyavgCDD,
                    "mean_abs_pct_err_hourlyavgCDD": mape_hourlyavgCDD,
                    "mean_abs_err_hourlyavgCDD": mae_hourlyavgCDD,

                    "actual_daily_runtime": actual_daily_runtime,
                    "actual_seasonal_runtime": actual_seasonal_runtime,

                    "mean_demand_baseline_deltaT":
                        np.nanmean(baseline_demand_deltaT),
                    "mean_demand_baseline_dailyavgCDD":
                        np.nanmean(baseline_demand_dailyavgCDD),
                    "mean_demand_baseline_hourlyavgCDD":
                        np.nanmean(baseline_demand_hourlyavgCDD),

                    "baseline_seasonal_runtime_deltaT":
                        baseline_runtime_deltaT.sum(),
                    "baseline_seasonal_runtime_dailyavgCDD":
                        baseline_runtime_dailyavgCDD.sum(),
                    "baseline_seasonal_runtime_hourlyavgCDD":
                        baseline_runtime_hourlyavgCDD.sum(),

                    "baseline_daily_runtime_deltaT":
                        baseline_runtime_deltaT.mean(),
                    "baseline_daily_runtime_dailyavgCDD":
                        baseline_runtime_dailyavgCDD.mean(),
                    "baseline_daily_runtime_hourlyavgCDD":
                        baseline_runtime_hourlyavgCDD.mean(),

                    "avoided_seasonal_runtime_deltaT":
                        avoided_runtime_deltaT.sum(),
                    "avoided_seasonal_runtime_dailyavgCDD":
                        avoided_runtime_dailyavgCDD.sum(),
                    "avoided_seasonal_runtime_hourlyavgCDD":
                        avoided_runtime_hourlyavgCDD.sum(),

                    "avoided_daily_runtime_deltaT":
                        avoided_runtime_deltaT.mean(),
                    "avoided_daily_runtime_dailyavgCDD":
                        avoided_runtime_dailyavgCDD.mean(),
                    "avoided_daily_runtime_hourlyavgCDD":
                        avoided_runtime_hourlyavgCDD.mean(),

                    "percent_savings_deltaT": savings_deltaT,
                    "percent_savings_dailyavgCDD": savings_dailyavgCDD,
                    "percent_savings_hourlyavgCDD": savings_hourlyavgCDD,

                    "n_days_both_heating_and_cooling": n_days_both,
                    "n_days_insufficient_data": n_days_insufficient_data,
                    "n_days_in_season": n_days_in_season,
                    "n_days_in_season_range": n_days_in_season_range,

                    "total_cooling_runtime":
                        self.total_cooling_runtime(cooling_season),

                    "season_name": cooling_season.name,
                }

                seasonal_metrics.append(outputs)


        if self.equipment_type in self.HEATING_EQUIPMENT_TYPES:
            for heating_season in self.get_heating_seasons(method=heating_season_method):

                baseline_comfort_temperature = \
                        self.get_heating_season_baseline_setpoint(heating_season)

                # deltaT
                daily_runtime = self.heat_runtime[heating_season.daily]
                demand_deltaT = self.get_heating_demand(
                        heating_season, method="deltaT")

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

                # dailyavgHDD
                (
                    demand_dailyavgHDD,
                    tau_dailyavgHDD,
                    alpha_dailyavgHDD,
                    mse_dailyavgHDD,
                    rmse_dailyavgHDD,
                    cvrmse_dailyavgHDD,
                    mape_dailyavgHDD,
                    mae_dailyavgHDD,
                ) = self.get_heating_demand(
                    heating_season, method="dailyavgHDD")

                # hourlyavgHDD
                (
                    demand_hourlyavgHDD,
                    tau_hourlyavgHDD,
                    alpha_hourlyavgHDD,
                    mse_hourlyavgHDD,
                    rmse_hourlyavgHDD,
                    cvrmse_hourlyavgHDD,
                    mape_hourlyavgHDD,
                    mae_hourlyavgHDD,
                ) = self.get_heating_demand(
                    heating_season, method="hourlyavgHDD")

                actual_seasonal_runtime = \
                        self.heat_runtime[heating_season.daily].sum()
                n_days = heating_season.daily.sum()
                actual_daily_runtime = actual_seasonal_runtime / n_days

                baseline_demand_deltaT = \
                    self.get_baseline_heating_demand(
                        heating_season,
                        deltaT_base=None,
                        method="deltaT")
                baseline_demand_dailyavgHDD = \
                    self.get_baseline_heating_demand(
                        heating_season,
                        deltaT_base=tau_dailyavgHDD,
                        method="dailyavgHDD")
                baseline_demand_hourlyavgHDD = \
                    self.get_baseline_heating_demand(
                        heating_season,
                        deltaT_base=tau_hourlyavgHDD,
                        method="hourlyavgHDD")

                baseline_runtime_deltaT = \
                    self.get_baseline_heating_runtime(
                        baseline_demand_deltaT,
                        alpha_deltaT,
                        tau_deltaT,
                        method="deltaT")
                baseline_runtime_dailyavgHDD = \
                    self.get_baseline_heating_runtime(
                        baseline_demand_dailyavgHDD,
                        alpha_dailyavgHDD,
                        tau_dailyavgHDD,
                        method="dailyavgHDD")
                baseline_runtime_hourlyavgHDD = \
                    self.get_baseline_heating_runtime(
                        baseline_demand_hourlyavgHDD,
                        alpha_hourlyavgHDD,
                        tau_hourlyavgHDD,
                        method="hourlyavgHDD")

                def avoided(baseline, observed):
                    return baseline - observed

                avoided_runtime_deltaT = avoided(
                    baseline_runtime_deltaT, daily_runtime)
                avoided_runtime_dailyavgHDD = avoided(
                    baseline_runtime_dailyavgHDD, daily_runtime)
                avoided_runtime_hourlyavgHDD = avoided(
                    baseline_runtime_hourlyavgHDD, daily_runtime)

                def percent_savings(avoided, baseline):
                    return (avoided.mean() / baseline.mean()) * 100.0

                savings_deltaT = percent_savings(
                    avoided_runtime_deltaT,
                    baseline_runtime_deltaT)
                savings_dailyavgHDD = percent_savings(
                    avoided_runtime_dailyavgHDD,
                    baseline_runtime_dailyavgHDD)
                savings_hourlyavgHDD = percent_savings(
                    avoided_runtime_hourlyavgHDD,
                    baseline_runtime_hourlyavgHDD)

                n_days_both, n_days_insufficient_data = \
                    self.get_season_ignored_days(heating_season)
                n_days_in_season = self.get_season_n_days(heating_season)
                n_days_in_season_range = \
                    self.get_season_n_days_in_range(heating_season)

                outputs = {
                    "ct_identifier": self.thermostat_id,
                    "zipcode": self.zipcode,
                    "station": self.station,
                    "equipment_type": self.equipment_type,
                    "baseline_comfort_temperature":
                        baseline_comfort_temperature,

                    "mean_demand_deltaT": np.nanmean(demand_deltaT),
                    "alpha_deltaT": alpha_deltaT,
                    "tau_deltaT": tau_deltaT,
                    "mean_sq_err_deltaT": mse_deltaT,
                    "root_mean_sq_err_deltaT": rmse_deltaT,
                    "cv_root_mean_sq_err_deltaT": cvrmse_deltaT,
                    "mean_abs_pct_err_deltaT": mape_deltaT,
                    "mean_abs_err_deltaT": mae_deltaT,

                    "mean_demand_dailyavgHDD": np.nanmean(demand_dailyavgHDD),
                    "tau_dailyavgHDD": tau_dailyavgHDD,
                    "alpha_dailyavgHDD": alpha_dailyavgHDD,
                    "mean_sq_err_dailyavgHDD": mse_dailyavgHDD,
                    "root_mean_sq_err_dailyavgHDD": rmse_dailyavgHDD,
                    "cv_root_mean_sq_err_dailyavgHDD": cvrmse_dailyavgHDD,
                    "mean_abs_pct_err_dailyavgHDD": mape_dailyavgHDD,
                    "mean_abs_err_dailyavgHDD": mae_dailyavgHDD,

                    "mean_demand_hourlyavgHDD":
                        np.nanmean(demand_hourlyavgHDD),
                    "tau_hourlyavgHDD": tau_hourlyavgHDD,
                    "alpha_hourlyavgHDD": alpha_hourlyavgHDD,
                    "mean_sq_err_hourlyavgHDD": mse_hourlyavgHDD,
                    "root_mean_sq_err_hourlyavgHDD": rmse_hourlyavgHDD,
                    "cv_root_mean_sq_err_hourlyavgHDD": cvrmse_hourlyavgHDD,
                    "mean_abs_pct_err_hourlyavgHDD": mape_hourlyavgHDD,
                    "mean_abs_err_hourlyavgHDD": mae_hourlyavgHDD,

                    "actual_daily_runtime": actual_daily_runtime,
                    "actual_seasonal_runtime": actual_seasonal_runtime,

                    "mean_demand_baseline_deltaT":
                        np.nanmean(baseline_demand_deltaT),
                    "mean_demand_baseline_dailyavgHDD":
                        np.nanmean(baseline_demand_dailyavgHDD),
                    "mean_demand_baseline_hourlyavgHDD":
                        np.nanmean(baseline_demand_hourlyavgHDD),

                    "baseline_seasonal_runtime_deltaT":
                        baseline_runtime_deltaT.sum(),
                    "baseline_seasonal_runtime_dailyavgHDD":
                        baseline_runtime_dailyavgHDD.sum(),
                    "baseline_seasonal_runtime_hourlyavgHDD":
                        baseline_runtime_hourlyavgHDD.sum(),

                    "baseline_daily_runtime_deltaT":
                        baseline_runtime_deltaT.mean(),
                    "baseline_daily_runtime_dailyavgHDD":
                        baseline_runtime_dailyavgHDD.mean(),
                    "baseline_daily_runtime_hourlyavgHDD":
                        baseline_runtime_hourlyavgHDD.mean(),

                    "avoided_seasonal_runtime_deltaT":
                        avoided_runtime_deltaT.sum(),
                    "avoided_seasonal_runtime_dailyavgHDD":
                        avoided_runtime_dailyavgHDD.sum(),
                    "avoided_seasonal_runtime_hourlyavgHDD":
                        avoided_runtime_hourlyavgHDD.sum(),

                    "avoided_daily_runtime_deltaT":
                        avoided_runtime_deltaT.mean(),
                    "avoided_daily_runtime_dailyavgHDD":
                        avoided_runtime_dailyavgHDD.mean(),
                    "avoided_daily_runtime_hourlyavgHDD":
                        avoided_runtime_hourlyavgHDD.mean(),

                    "percent_savings_deltaT": savings_deltaT,
                    "percent_savings_dailyavgHDD": savings_dailyavgHDD,
                    "percent_savings_hourlyavgHDD": savings_hourlyavgHDD,

                    "n_days_both_heating_and_cooling": n_days_both,
                    "n_days_insufficient_data": n_days_insufficient_data,
                    "n_days_in_season": n_days_in_season,
                    "n_days_in_season_range": n_days_in_season_range,

                    "total_heating_runtime":
                        self.total_heating_runtime(heating_season),

                    "season_name": heating_season.name,
                }


                if self.equipment_type in self.AUX_EMERG_EQUIPMENT_TYPES:

                    additional_outputs = {
                        "total_auxiliary_heating_runtime":
                            self.total_auxiliary_heating_runtime(
                                heating_season),
                        "total_emergency_heating_runtime":
                            self.total_emergency_heating_runtime(
                                heating_season),
                    }

                    rhus = self.get_resistance_heat_utilization_bins(heating_season)

                    if rhus is None:
                        for low, high in [(i, i+5) for i in range(0, 60, 5)]:
                            column = "rhu_{:02d}F_to_{:02d}F".format(low, high)
                            additional_outputs[column] = None
                    else:
                        for rhu, (low, high) in zip(rhus, [(i, i+5) for i in range(0, 60, 5)]):
                            column = "rhu_{:02d}F_to_{:02d}F".format(low, high)
                            additional_outputs[column] = rhu

                    outputs.update(additional_outputs)
                seasonal_metrics.append(outputs)

        return seasonal_metrics
