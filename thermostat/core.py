import pandas as pd
import numpy as np
from scipy.optimize import leastsq

from datetime import datetime
from collections import namedtuple

from thermostat.regression import runtime_regression
from thermostat.savings import get_daily_avoided_runtime
from thermostat.savings import get_seasonal_percent_savings

import inspect

Season = namedtuple("Season", ["name", "daily", "hourly", "start_date", "end_date"])

HEATING_EQUIPMENT_TYPES = [1,2,3,4]
COOLING_EQUIPMENT_TYPES = [1,2,3,5]
AUX_EMERG_EQUIPMENT_TYPES = [1]

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
        in seconds. No datapoint should exceed 86400 s, which would indicate
        over a day of runtime (impossible).
        Should be indexed by a pandas.DatetimeIndex with daily frequency (i.e.
        :code:`freq='D'`).
    heat_runtime : pandas.Series,
        Daily runtimes for heating equipment controlled by the thermostat, measured
        in seconds. No datapoint should exceed 86400 s, which would indicate
        over a day of runtime (impossible).
        Should be indexed by a pandas.DatetimeIndex with daily frequency (i.e.
        :code:`freq='D'`).
    auxiliary_heat_runtime : pandas.Series,
        Hourly runtimes for auxiliary heating equipment controlled by the
        thermostat, measured in seconds. Auxiliary heat runtime is counted when
        both resistance heating and the compressor are running (for heat pump
        systems). No datapoint should exceed 86400 s, which would indicate
        over a day of runtime (impossible).
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    energency_heat_runtime : pandas.Series,
        Hourly runtimes for emergency heating equipment controlled by the
        thermostat, measured in seconds. Emergency heat runtime is counted when
        resistance heating is running when the compressor is not (for heat pump
        systems). No datapoint should exceed 86400 s, which would indicate
        over a day of runtime (impossible).
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    """

    def __init__(self, thermostat_id, equipment_type, zipcode, station, temperature_in,
                 temperature_out, cooling_setpoint, heating_setpoint,
                 cool_runtime, heat_runtime, auxiliary_heat_runtime,
                 emergency_heat_runtime):

        self.thermostat_id = thermostat_id
        self.equipment_type = equipment_type
        self.zipcode = zipcode
        self.station = station

        self.temperature_in = temperature_in
        self.temperature_out = temperature_out
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

        if self.equipment_type in HEATING_EQUIPMENT_TYPES:
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

        if self.equipment_type in COOLING_EQUIPMENT_TYPES:
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

        if self.equipment_type in AUX_EMERG_EQUIPMENT_TYPES:
            if self.auxiliary_heat_runtime is None or self.emergency_heat_runtime is None:
                message = "For thermostat {}, aux and emergency runtime data were not provided," \
                          " despite equipment type of {}, which requires these columns of data."\
                          " If none is available, please change to equipment_type 2," \
                          " or provide columns of 0s".format(self.thermostat_id, self.equipment_type)
                raise ValueError(message)

    def _protect_heating(self):
        function_name = inspect.stack()[1][3]
        if self.equipment_type not in HEATING_EQUIPMENT_TYPES:
            message = "The function '{}', which is heating specific, cannot be" \
                      " called for equipment_type {}".format(function_name, self.equipment_type)
            raise ValueError(message)

    def _protect_cooling(self):
        function_name = inspect.stack()[1][3]
        if self.equipment_type not in COOLING_EQUIPMENT_TYPES:
            message = "The function '{}', which is cooling specific, cannot be" \
                      " called for equipment_type {}".format(function_name, self.equipment_type)
            raise ValueError(message)

    def _protect_aux_emerg(self):
        function_name = inspect.stack()[1][3]
        if self.equipment_type not in AUX_EMERG_EQUIPMENT_TYPES:
            message = "The function '{}', which is auxiliary/emergency heating specific, cannot be" \
                      " called for equipment_type {}".format(function_name, self.equipment_type)
            raise ValueError(message)

    def get_heating_seasons(self, method="year_mid_to_mid",
            min_seconds_heating=3600, max_seconds_cooling=0):
        """ Get all data for heating seasons for data associated with this
        thermostat

        Parameters
        ----------
        method : {"year_mid_to_mid"}, default: "year_mid_to_mid"
            Method by which to find heating seasons.

            - "year_mid_to_mid": groups all heating days (days with >= 1 hour of total
              heating and no cooling) from July 1 to June 31 (inclusive) into single
              heating seasons. May overlap with cooling seasons.
        min_seconds_heating : int, default 3600
            Number of seconds of heating runtime per day required for inclusion in season.
        max_seconds_cooling : int, default 0
            Number of seconds of cooling runtime per day beyond which for day is
            considered part of a shoulder season (and is therefore not part of
            the heating season).

        Returns
        -------
        seasons : list of thermostat.core.Season objects
            List of seasons detected; first element of tuple is season, second
            is name. Seasons are represented as pandas Series of boolean values,
            intended to be used as selectors or masks on the thermostat data.
            A value of True at a particular index indicates inclusion of
            of the data at that index in the season. Names are of the form
            "YYYY-YYYY Heating"
        """
        if method != "year_mid_to_mid":
            raise NotImplementedError

        self._protect_heating()

        # find all potential heating season ranges
        data_start_date = np.datetime64(self.heat_runtime.index[0])
        data_end_date = np.datetime64(self.heat_runtime.index[-1])
        start_year = data_start_date.item().year - 1
        end_year = data_end_date.item().year + 1
        potential_seasons = zip(range(start_year, end_year), range(start_year + 1, end_year + 1))

        # compute inclusion thresholds
        meets_heating_thresholds = self.heat_runtime >= min_seconds_heating

        if self.equipment_type in COOLING_EQUIPMENT_TYPES:
            meets_cooling_thresholds = self.cool_runtime <= max_seconds_cooling
        else:
            meets_cooling_thresholds = True

        meets_thresholds = meets_heating_thresholds & meets_cooling_thresholds

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

    def get_cooling_seasons(self, method="year_end_to_end",
            min_seconds_cooling=3600, max_seconds_heating=0):
        """ Get all data for cooling seasons for data associated with this
        thermostat.

        Parameters
        ----------
        method : {"year_end_to_end"}, default: "year_end_to_end"
            Method by which to find cooling seasons.

            - "year_end_to_end": groups all cooling days (days with >= 1 hour of total
              cooling and no heating) from January 1 to December 31 into
              single cooling seasons.
        min_seconds_cooling : int, default 3600
            Number of seconds of cooling runtime per day required for inclusion in season.
        max_seconds_heating : int, default 0
            Number of seconds of heating runtime per day beyond which for day is
            considered part of a shoulder season (and is therefore not part of
            the cooling season).

        Returns
        -------
        seasons : list of thermostat.core.Season objects
            List of seasons detected; first element of tuple is season, second
            is name. Seasons are represented as pandas Series of boolean
            values, intended to be used as selectors or masks on the thermostat
            data. A value of True at a particular index indicates inclusion of
            of the data at that index in the season. Names are of the form
            "YYYY Cooling"
        """
        if method != "year_end_to_end":
            raise NotImplementedError

        self._protect_cooling()

        # find all potential cooling season ranges
        data_start_date = np.datetime64(self.cool_runtime.index[0])
        data_end_date = np.datetime64(self.cool_runtime.index[-1])
        start_year = data_start_date.item().year
        end_year = data_end_date.item().year
        potential_seasons = range(start_year, end_year + 1)

        # compute inclusion thresholds
        if self.equipment_type in HEATING_EQUIPMENT_TYPES:
            meets_heating_thresholds = self.heat_runtime <= max_seconds_heating
        else:
            meets_heating_thresholds = True

        meets_cooling_thresholds = self.cool_runtime >= min_seconds_cooling
        meets_thresholds = meets_heating_thresholds & meets_cooling_thresholds

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

        if self.equipment_type in HEATING_EQUIPMENT_TYPES:
            has_heating = self.heat_runtime > 0
            null_heating = pd.isnull(self.heat_runtime)
        else:
            has_heating = False
            null_heating = False # shouldn't be counted, so False, not True

        if self.equipment_type in COOLING_EQUIPMENT_TYPES:
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
        return (season.end_date - season.start_date).days

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

            - "deltaT": :math:`\Delta T = temp_{in} - temp_{out}`
            - "dailyavgCDD": :math:`\\text{daily CDD} = \Delta T_{\\text{daily avg}}
              - \Delta T_{\\text{base cool}}` where
              :math:`\Delta T_{\\text{daily avg}} =
              \\frac{\sum_{i=1}^{24} \Delta T_i}{24}`
            - "hourlyavgCDD": :math:`\\text{daily CDD} = \sum_{i=1}^{24} \\text{CDH}_i`
              where :math:`\\text{CDH}_i = \Delta T_i - \Delta T_{\\text{base cool}}`

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
            return pd.Series(daily_avg_deltaT, index=daily_index)
        elif method == "dailyavgCDD":
            def calc_cdd(deltaT_base):
                return np.maximum(deltaT_base - daily_avg_deltaT, 0)
        elif method == "hourlyavgCDD":
            def calc_cdd(deltaT_base):
                hourly_cdd = (deltaT_base - season_deltaT).apply(lambda x: np.maximum(x, 0))
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
        y, _ = leastsq(estimate_errors, deltaT_base_starting_guess)
        deltaT_base_estimate = y[0]

        cdd, alpha_estimate, errors = calc_estimates(deltaT_base_estimate)
        mean_squared_error = np.mean((errors)**2)

        return pd.Series(cdd, index=daily_index), deltaT_base_estimate, alpha_estimate, mean_squared_error

    def get_heating_demand(self, heating_season, method="deltaT"):
        """
        Calculates a measure of heating demand.

        Parameters
        ----------
        heating_season : array_like
            Season over which to calculate heating demand.
        method : {"deltaT", "hourlyavgHDD", "dailyavgHDD"} default: "deltaT"
            The method to use during calculation of demand.

            - "deltaT": :math:`\Delta T = temp_{in} - temp_{out}`
            - "dailyavgHDD": :math:`\\text{daily HDD} = \Delta T_{\\text{daily avg}}
              - \Delta T_{\\text{base heat}}` where
              :math:`\Delta T_{\\text{daily avg}} =
              \\frac{\sum_{i=1}^{24} \Delta T_i}{24}`
            - "hourlyavgHDD": :math:`\\text{daily HDD} = \sum_{i=1}^{24} \\text{HDH}_i`
              where :math:`\\text{HDH}_i = \Delta T_i - \Delta T_{\\text{base heat}}`

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
                return np.maximum(daily_avg_deltaT - deltaT_base,0)
        elif method == "hourlyavgHDD":
            def calc_hdd(deltaT_base):
                hourly_hdd = (season_deltaT - deltaT_base).apply(lambda x: np.maximum(x,0))
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
        y, _ = leastsq(estimate_errors, deltaT_base_starting_guess)
        deltaT_base_estimate = y[0]

        hdd, alpha_estimate, errors = calc_estimates(deltaT_base_estimate)
        mean_squared_error = np.mean((errors)**2)

        return pd.Series(hdd, index=daily_index), deltaT_base_estimate, alpha_estimate, mean_squared_error

    ################## BASELINING ##########################

    def get_cooling_season_baseline_setpoint(self, cooling_season, method='tenth_percentile', source='cooling_setpoint'):
        """ Calculate the cooling season baseline setpoint (comfort temperature).

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
                return self.cooling_setpoint[cooling_season.hourly].quantile(.1)
            elif source == 'temperature_in':
                return self.temperature_in[cooling_season.hourly].quantile(.1)
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
                return self.heating_setpoint[heating_season.hourly].quantile(.9)
            elif source == 'temperature_in':
                return self.temperature_in[heating_season.hourly].quantile(.9)
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


    ###################### Metrics #################################

    def calculate_epa_draft_rccs_field_savings_metrics(self):
        """ Calculates metrics for connected thermostat savings as defined by
        the draft specification defined by the EPA and stakeholders during early
        2015.

        Returns
        -------
        seasonal_metrics : list
            list of dictionaries of output metrics; one per season.
        """
        seasonal_metrics = []

        if self.equipment_type in COOLING_EQUIPMENT_TYPES:
            for cooling_season in self.get_cooling_seasons():
                outputs = {}
                outputs["ct_identifier"] = self.thermostat_id
                outputs["zipcode"] = self.zipcode
                outputs["station"] = self.station
                outputs["equipment_type"] = self.equipment_type

                baseline_comfort_temperature = self.get_cooling_season_baseline_setpoint(cooling_season)
                outputs["baseline_comfort_temperature"] = baseline_comfort_temperature

                # calculate demand metrics

                # deltaT
                demand_deltaT = self.get_cooling_demand(cooling_season,
                        method="deltaT")
                daily_runtime = self.cool_runtime[cooling_season.daily]
                try:
                    slope_deltaT, intercept_deltaT, mean_sq_err_deltaT = runtime_regression(
                            daily_runtime, demand_deltaT)
                    outputs["slope_deltaT"] = slope_deltaT
                    outputs["intercept_deltaT"] = intercept_deltaT
                    outputs["mean_squared_error_deltaT"] = mean_sq_err_deltaT
                except ValueError: # too many values to unpack
                    outputs["slope_deltaT"] = np.nan
                    outputs["intercept_deltaT"] = np.nan
                    outputs["mean_squared_error_deltaT"] = np.nan

                # dailyavgCDD
                demand_dailyavgCDD, deltaT_base_est_dailyavgCDD, \
                        alpha_est_dailyavgCDD, mean_sq_err_dailyavgCDD = \
                                self.get_cooling_demand(cooling_season, method="dailyavgCDD")
                outputs["deltaT_base_est_dailyavgCDD"] = deltaT_base_est_dailyavgCDD
                outputs["alpha_est_dailyavgCDD"] = alpha_est_dailyavgCDD
                outputs["mean_sq_err_dailyavgCDD"] = mean_sq_err_dailyavgCDD

                # hourlyavgCDD
                demand_hourlyavgCDD, deltaT_base_est_hourlyavgCDD, \
                        alpha_est_hourlyavgCDD, mean_sq_err_hourlyavgCDD = \
                                self.get_cooling_demand(cooling_season, method="hourlyavgCDD")
                outputs["deltaT_base_est_hourlyavgCDD"] = deltaT_base_est_hourlyavgCDD
                outputs["alpha_est_hourlyavgCDD"] = alpha_est_hourlyavgCDD
                outputs["mean_sq_err_hourlyavgCDD"] = mean_sq_err_hourlyavgCDD

                actual_seasonal_runtime = self.cool_runtime[cooling_season.daily].sum()

                n_days = cooling_season.daily.sum()

                actual_daily_runtime = actual_seasonal_runtime / n_days

                outputs["actual_daily_runtime"] = actual_daily_runtime
                outputs["actual_seasonal_runtime"] = actual_seasonal_runtime

                demand_baseline_deltaT = self.get_baseline_cooling_demand(
                        cooling_season, method="deltaT")
                demand_baseline_dailyavgCDD = self.get_baseline_cooling_demand(
                        cooling_season, deltaT_base_est_dailyavgCDD,
                        method="dailyavgCDD")
                demand_baseline_hourlyavgCDD = self.get_baseline_cooling_demand(
                        cooling_season, deltaT_base_est_hourlyavgCDD,
                        method="hourlyavgCDD")

                daily_avoided_runtime_deltaT = get_daily_avoided_runtime(
                        slope_deltaT, -demand_deltaT, demand_baseline_deltaT)
                daily_avoided_runtime_dailyavgCDD = get_daily_avoided_runtime( alpha_est_dailyavgCDD, demand_dailyavgCDD, demand_baseline_dailyavgCDD)
                daily_avoided_runtime_hourlyavgCDD = get_daily_avoided_runtime(
                        alpha_est_hourlyavgCDD, demand_hourlyavgCDD,
                        demand_baseline_hourlyavgCDD)

                baseline_seasonal_runtime_deltaT = \
                        self.get_total_baseline_cooling_runtime(cooling_season,
                                daily_avoided_runtime_deltaT)
                baseline_seasonal_runtime_dailyavgCDD = \
                        self.get_total_baseline_cooling_runtime(cooling_season,
                                daily_avoided_runtime_dailyavgCDD)
                baseline_seasonal_runtime_hourlyavgCDD = \
                        self.get_total_baseline_cooling_runtime(cooling_season,
                                daily_avoided_runtime_hourlyavgCDD)

                outputs["baseline_seasonal_runtime_deltaT"] = baseline_seasonal_runtime_deltaT
                outputs["baseline_seasonal_runtime_dailyavgCDD"] = baseline_seasonal_runtime_dailyavgCDD
                outputs["baseline_seasonal_runtime_hourlyavgCDD"] = baseline_seasonal_runtime_hourlyavgCDD

                baseline_daily_runtime_deltaT = baseline_seasonal_runtime_deltaT / n_days
                baseline_daily_runtime_dailyavgCDD = baseline_seasonal_runtime_dailyavgCDD / n_days
                baseline_daily_runtime_hourlyavgCDD = baseline_seasonal_runtime_hourlyavgCDD / n_days

                outputs["baseline_daily_runtime_deltaT"] = baseline_daily_runtime_deltaT
                outputs["baseline_daily_runtime_dailyavgCDD"] = baseline_daily_runtime_dailyavgCDD
                outputs["baseline_daily_runtime_hourlyavgCDD"] = baseline_daily_runtime_hourlyavgCDD

                seasonal_savings_deltaT = get_seasonal_percent_savings(
                        baseline_seasonal_runtime_deltaT,
                        daily_avoided_runtime_deltaT)
                seasonal_savings_dailyavgCDD = get_seasonal_percent_savings(
                        baseline_seasonal_runtime_dailyavgCDD,
                        daily_avoided_runtime_dailyavgCDD)
                seasonal_savings_hourlyavgCDD = get_seasonal_percent_savings(
                        baseline_seasonal_runtime_hourlyavgCDD,
                        daily_avoided_runtime_hourlyavgCDD)

                outputs["seasonal_savings_deltaT"] = seasonal_savings_deltaT
                outputs["seasonal_savings_dailyavgCDD"] = seasonal_savings_dailyavgCDD
                outputs["seasonal_savings_hourlyavgCDD"] = seasonal_savings_hourlyavgCDD

                seasonal_avoided_runtime_deltaT = daily_avoided_runtime_deltaT.sum()
                seasonal_avoided_runtime_dailyavgCDD = daily_avoided_runtime_dailyavgCDD.sum()
                seasonal_avoided_runtime_hourlyavgCDD = daily_avoided_runtime_hourlyavgCDD.sum()

                outputs["seasonal_avoided_runtime_deltaT"] = seasonal_avoided_runtime_deltaT
                outputs["seasonal_avoided_runtime_dailyavgCDD"] = seasonal_avoided_runtime_dailyavgCDD
                outputs["seasonal_avoided_runtime_hourlyavgCDD"] = seasonal_avoided_runtime_hourlyavgCDD

                n_days_both, n_days_insufficient_data = self.get_season_ignored_days(cooling_season)
                n_days_in_season = self.get_season_n_days(cooling_season)
                n_days_in_season_range = self.get_season_n_days_in_range(cooling_season)

                outputs["n_days_both_heating_and_cooling"] = n_days_both
                outputs["n_days_insufficient_data"] = n_days_insufficient_data
                outputs["n_days_in_season"] = n_days_in_season
                outputs["n_days_in_season_range"] = n_days_in_season_range

                outputs["season_name"] = cooling_season.name

                seasonal_metrics.append(outputs)


        if self.equipment_type in HEATING_EQUIPMENT_TYPES:
            for heating_season in self.get_heating_seasons():
                outputs = {}
                outputs["ct_identifier"] = self.thermostat_id
                outputs["zipcode"] = self.zipcode
                outputs["station"] = self.station
                outputs["equipment_type"] = self.equipment_type

                baseline_comfort_temperature = \
                        self.get_heating_season_baseline_setpoint(heating_season)
                outputs["baseline_comfort_temperature"] = baseline_comfort_temperature

                # calculate demand metrics

                # deltaT
                demand_deltaT = self.get_heating_demand(heating_season, method="deltaT")
                daily_runtime = self.heat_runtime[heating_season.daily]

                try:
                    slope_deltaT, intercept_deltaT, mean_sq_err_deltaT = runtime_regression(
                            daily_runtime, demand_deltaT)
                    outputs["slope_deltaT"] = slope_deltaT
                    outputs["intercept_deltaT"] = intercept_deltaT
                    outputs["mean_squared_error_deltaT"] = mean_sq_err_deltaT
                except ValueError: # too many values to unpack
                    outputs["slope_deltaT"] = np.nan
                    outputs["intercept_deltaT"] = np.nan
                    outputs["mean_squared_error_deltaT"] = np.nan

                # dailyavgHDD
                demand_dailyavgHDD, deltaT_base_est_dailyavgHDD, \
                        alpha_est_dailyavgHDD, mean_sq_err_dailyavgHDD = \
                            self.get_heating_demand(heating_season, method="dailyavgHDD")
                outputs["deltaT_base_est_dailyavgHDD"] = deltaT_base_est_dailyavgHDD
                outputs["alpha_est_dailyavgHDD"] = alpha_est_dailyavgHDD
                outputs["mean_sq_err_dailyavgHDD"] = mean_sq_err_dailyavgHDD

                # hourlyavgHDD
                demand_hourlyavgHDD, deltaT_base_est_hourlyavgHDD, \
                        alpha_est_hourlyavgHDD, mean_sq_err_hourlyavgHDD = \
                                self.get_heating_demand(heating_season, method="hourlyavgHDD")
                outputs["deltaT_base_est_hourlyavgHDD"] = deltaT_base_est_hourlyavgHDD
                outputs["alpha_est_hourlyavgHDD"] = alpha_est_hourlyavgHDD
                outputs["mean_sq_err_hourlyavgHDD"] = mean_sq_err_hourlyavgHDD

                actual_seasonal_runtime = self.heat_runtime[heating_season.daily].sum()

                n_days = heating_season.daily.sum()

                actual_daily_runtime = actual_seasonal_runtime / n_days

                outputs["actual_daily_runtime"] = actual_daily_runtime
                outputs["actual_seasonal_runtime"] = actual_seasonal_runtime

                demand_baseline_deltaT = self.get_baseline_heating_demand(
                        heating_season, method="deltaT")
                demand_baseline_dailyavgHDD = self.get_baseline_heating_demand(
                        heating_season, deltaT_base_est_dailyavgHDD,
                        method="dailyavgHDD")
                demand_baseline_hourlyavgHDD = self.get_baseline_heating_demand(
                        heating_season, deltaT_base_est_hourlyavgHDD,
                        method="hourlyavgHDD")

                daily_avoided_runtime_deltaT = get_daily_avoided_runtime(
                        slope_deltaT, demand_deltaT, demand_baseline_deltaT)
                daily_avoided_runtime_dailyavgHDD = get_daily_avoided_runtime(
                        alpha_est_dailyavgHDD, demand_dailyavgHDD,
                        demand_baseline_dailyavgHDD)
                daily_avoided_runtime_hourlyavgHDD = get_daily_avoided_runtime(
                        alpha_est_hourlyavgHDD, demand_hourlyavgHDD,
                        demand_baseline_hourlyavgHDD)

                baseline_seasonal_runtime_deltaT = \
                        self.get_total_baseline_heating_runtime(heating_season,
                                daily_avoided_runtime_deltaT)
                baseline_seasonal_runtime_dailyavgHDD = \
                        self.get_total_baseline_heating_runtime(heating_season,
                                daily_avoided_runtime_dailyavgHDD)
                baseline_seasonal_runtime_hourlyavgHDD = \
                        self.get_total_baseline_heating_runtime(heating_season,
                                daily_avoided_runtime_hourlyavgHDD)

                outputs["baseline_seasonal_runtime_deltaT"] = baseline_seasonal_runtime_deltaT
                outputs["baseline_seasonal_runtime_dailyavgHDD"] = baseline_seasonal_runtime_dailyavgHDD
                outputs["baseline_seasonal_runtime_hourlyavgHDD"] = baseline_seasonal_runtime_hourlyavgHDD

                baseline_daily_runtime_deltaT = baseline_seasonal_runtime_deltaT / n_days
                baseline_daily_runtime_dailyavgHDD = baseline_seasonal_runtime_dailyavgHDD / n_days
                baseline_daily_runtime_hourlyavgHDD = baseline_seasonal_runtime_hourlyavgHDD / n_days

                outputs["baseline_daily_runtime_deltaT"] = baseline_daily_runtime_deltaT
                outputs["baseline_daily_runtime_dailyavgHDD"] = baseline_daily_runtime_dailyavgHDD
                outputs["baseline_daily_runtime_hourlyavgHDD"] = baseline_daily_runtime_hourlyavgHDD

                seasonal_savings_deltaT = get_seasonal_percent_savings(
                        baseline_seasonal_runtime_deltaT,
                        daily_avoided_runtime_deltaT)
                seasonal_savings_dailyavgHDD = get_seasonal_percent_savings(
                        baseline_seasonal_runtime_dailyavgHDD,
                        daily_avoided_runtime_dailyavgHDD)
                seasonal_savings_hourlyavgHDD = get_seasonal_percent_savings(
                        baseline_seasonal_runtime_hourlyavgHDD,
                        daily_avoided_runtime_hourlyavgHDD)

                outputs["seasonal_savings_deltaT"] = seasonal_savings_deltaT
                outputs["seasonal_savings_dailyavgHDD"] = seasonal_savings_dailyavgHDD
                outputs["seasonal_savings_hourlyavgHDD"] = seasonal_savings_hourlyavgHDD

                seasonal_avoided_runtime_deltaT = daily_avoided_runtime_deltaT.sum()
                seasonal_avoided_runtime_dailyavgHDD = daily_avoided_runtime_dailyavgHDD.sum()
                seasonal_avoided_runtime_hourlyavgHDD = daily_avoided_runtime_hourlyavgHDD.sum()

                outputs["seasonal_avoided_runtime_deltaT"] = seasonal_avoided_runtime_deltaT
                outputs["seasonal_avoided_runtime_dailyavgHDD"] = seasonal_avoided_runtime_dailyavgHDD
                outputs["seasonal_avoided_runtime_hourlyavgHDD"] = seasonal_avoided_runtime_hourlyavgHDD

                n_days_both, n_days_insufficient_data = self.get_season_ignored_days(heating_season)
                n_days_in_season = self.get_season_n_days(heating_season)
                n_days_in_season_range = self.get_season_n_days_in_range(heating_season)

                outputs["n_days_both_heating_and_cooling"] = n_days_both
                outputs["n_days_insufficient_data"] = n_days_insufficient_data
                outputs["n_days_in_season"] = n_days_in_season
                outputs["n_days_in_season_range"] = n_days_in_season_range

                if self.equipment_type in AUX_EMERG_EQUIPMENT_TYPES:
                    rhus = self.get_resistance_heat_utilization_bins(heating_season)
                    if rhus is None:
                        for low, high in [(i,i+5) for i in range(0,60,5)]:
                            outputs["rhu_{:02d}F_to_{:02d}F".format(low,high)] = None
                    else:
                        for rhu, (low, high) in zip(rhus,[(i,i+5) for i in range(0,60,5)]):
                            outputs["rhu_{:02d}F_to_{:02d}F".format(low,high)] = rhu

                outputs["season_name"] = heating_season.name

                seasonal_metrics.append(outputs)

        return seasonal_metrics
