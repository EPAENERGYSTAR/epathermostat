import pandas as pd
import numpy as np
from scipy.optimize import leastsq

from datetime import datetime
from collections import namedtuple

from thermostat.regression import runtime_regression
from thermostat.savings import get_daily_avoided_runtime
from thermostat.savings import get_seasonal_percent_savings

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
        Daily runtimes for auxiliary heating equipment controlled by the
        thermostat, measured in seconds. Auxiliary heat runtime is counted when
        both resistance heating and the compressor are running (for heat pump
        systems). No datapoint should exceed 86400 s, which would indicate
        over a day of runtime (impossible).
        Should be indexed by a pandas.DatetimeIndex with daily frequency (i.e.
        :code:`freq='D'`).
    energency_heat_runtime : pandas.Series,
        Daily runtimes for emergency heating equipment controlled by the
        thermostat, measured in seconds. Emergency heat runtime is counted when
        resistance heating is running when the compressor is not (for heat pump
        systems). No datapoint should exceed 86400 s, which would indicate
        over a day of runtime (impossible).
        Should be indexed by a pandas.DatetimeIndex with daily frequency (i.e.
        :code:`freq='D'`).
    """

    def __init__(self, thermostat_id, equipment_type, zipcode, temperature_in,
                 temperature_out, cooling_setpoint, heating_setpoint,
                 cool_runtime, heat_runtime, auxiliary_heat_runtime,
                 emergency_heat_runtime):

        self.thermostat_id = thermostat_id
        self.equipment_type = equipment_type
        self.zipcode = zipcode

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
        pass

    def get_heating_seasons(self, method="year_mid_to_mid"):
        """ Get all data for heating seasons for data associated with this
        thermostat

        Parameters
        ----------
        method : {"year_mid_to_mid"}, default: "year_mid_to_mid"
            Method by which to find heating seasons.

            - "year_mid_to_mid": groups all heating days (days with >= 1 hour of total
              heating and no cooling) from July 1 to June 31 (inclusive) into single
              heating seasons. May overlap with cooling seasons.

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

        # find all potential heating season ranges
        start_year = self.heat_runtime.index[0].year - 1
        end_year = self.heat_runtime.index[-1].year + 1
        potential_seasons = zip(range(start_year, end_year), range(start_year + 1, end_year + 1))

        # compute inclusion thresholds
        meets_heating_thresholds = self.heat_runtime >= 3600
        meets_cooling_thresholds = self.cool_runtime == 0
        meets_thresholds = meets_heating_thresholds & meets_cooling_thresholds

        # for each potential season, look for heating days.
        seasons = []
        for start_year_, end_year_ in potential_seasons:
            start_date = np.datetime64(datetime(start_year_, 7, 1))
            end_date = np.datetime64(datetime(end_year_, 7, 1))
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

    def get_cooling_seasons(self, method="year_end_to_end"):
        """ Get all data for cooling seasons for data associated with this
        thermostat.

        Parameters
        ----------
        method : {"year_end_to_end"}, default: "year_end_to_end"
            Method by which to find cooling seasons.

            - "year_end_to_end": groups all cooling days (days with >= 1 hour of total
              cooling and no heating) from January 1 to December 31 into
              single cooling seasons.

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

        # find all potential cooling season ranges
        start_year = self.cool_runtime.index[0].year
        end_year = self.cool_runtime.index[-1].year
        potential_seasons = range(start_year, end_year + 1)

        # compute inclusion thresholds
        meets_heating_thresholds = self.heat_runtime == 0
        meets_cooling_thresholds = self.cool_runtime >= 3600
        meets_thresholds = meets_heating_thresholds & meets_cooling_thresholds

        # for each potential season, look for cooling days.
        seasons = []
        for year in potential_seasons:
            start_date = np.datetime64(datetime(year, 1, 1))
            end_date = np.datetime64(datetime(year + 1, 1, 1))
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
        bin_step = 5
        if self.equipment_type == 1:
            RHUs = []

            in_season = self._get_range_boolean(season.daily.index,
                    season.start_date, season.end_date)

            temperature_bins = [(i, i+5) for i in range(0, 60, 5)]
            temp_out_daily = self.temperature_out.groupby(
                    self.temperature_out.index.date).mean()
            for low_temp, high_temp in temperature_bins:
                temp_low_enough = temp_out_daily < high_temp
                temp_high_enough = temp_out_daily >= low_temp
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

        has_heating = self.heat_runtime > 0
        has_cooling = self.cool_runtime > 0
        null_heating = pd.isnull(self.heat_runtime)
        null_cooling = pd.isnull(self.cool_runtime)

        n_both = (in_range & has_heating & has_cooling).sum()
        n_incomplete = (in_range & (null_heating | null_cooling)).sum()
        return n_both, n_incomplete


    ##################### DEMAND ################################

    def get_cooling_demand(self, cooling_season, method="deltaT"):
        """
        Calculates a measure of cooling demand.

        Parameters
        ----------
        cooling_season : thermostat.Season
            Season over which to calculate cooling demand.
        method : {"deltaT", "dailyavgCDD", "hourlysumCDD"}, default: "deltaT"
            The method to use during calculation of demand.

            - "deltaT": :math:`\Delta T = temp_{in} - temp_{out}`
            - "dailyavgCDD": :math:`\\text{daily CDD} = \Delta T_{\\text{daily avg}}
              - \Delta T_{\\text{base cool}}` where
              :math:`\Delta T_{\\text{daily avg}} =
              \\frac{\sum_{i=1}^{24} \Delta T_i}{24}`
            - "hourlysumCDD": :math:`\\text{daily CDD} = \sum_{i=1}^{24} \\text{CDH}_i`
              where :math:`\\text{CDH}_i = \Delta T_i - \Delta T_{\\text{base cool}}`

        Returns
        -------
        demand : pd.Series
            Daily demand in the heating season as calculated using one of
            the supported methods.
        deltaT_base_estimate : float
            Estimate of :math:`\Delta T_{\\text{base cool}}`. Only output for
            "hourlysumCDD" and "dailyavgCDD".
        alpha_estimate : float
            Estimate of linear runtime response to demand. Only output for
            "hourlysumCDD" and "dailyavgCDD".
        mean_squared_error : float
            Mean squared error in runtime estimates. Only output for "hourlysumCDD"
            and "dailyavgCDD".
        """
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
        elif method == "hourlysumCDD":
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
        method : {"deltaT", "hourlysumHDD", "dailyavgHDD"} default: "deltaT"
            The method to use during calculation of demand.

            - "deltaT": :math:`\Delta T = temp_{in} - temp_{out}`
            - "dailyavgHDD": :math:`\\text{daily HDD} = \Delta T_{\\text{daily avg}}
              - \Delta T_{\\text{base heat}}` where
              :math:`\Delta T_{\\text{daily avg}} =
              \\frac{\sum_{i=1}^{24} \Delta T_i}{24}`
            - "hourlysumHDD": :math:`\\text{daily HDD} = \sum_{i=1}^{24} \\text{HDH}_i`
              where :math:`\\text{HDH}_i = \Delta T_i - \Delta T_{\\text{base heat}}`

        Returns
        -------
        demand : pd.Series
            Daily demand in the heating season as calculated using one of
            the supported methods.
        deltaT_base_estimate : float
            Estimate of :math:`\Delta T_{\\text{base heat}}`. Only output for
            "hourlysumHDD" and "dailyavgHDD".
        alpha_estimate : float
            Estimate of linear runtime response to demand. Only output for
            "hourlysumHDD" and "dailyavgHDD".
        mean_squared_error : float
            Mean squared error in runtime estimates. Only output for "hourlysumHDD"
            and "dailyavgHDD".
        """
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
        elif method == "hourlysumHDD":
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

    def get_cooling_season_baseline_setpoint(self, cooling_season, method='tenth_percentile'):
        """ Calculate the cooling season baseline setpoint (comfort temperature).

        Parameters
        ----------
        cooling_season : array_like
            Cooling season over which to calculate baseline cooling setpoint.
        method : {"tenth_percentile"}, default: "tenth_percentile"
            Method to use in calculation of the baseline.

            - "tenth_percentile": 10th percentile of cooling season cooling
              setpoints.

        Returns
        -------
        baseline : pandas.Series
            The baseline cooling setpoint for the cooling season as determined
            by the given method.
        """
        if method != 'tenth_percentile':
            raise NotImplementedError
        return self.cooling_setpoint[cooling_season.hourly].quantile(.1)

    def get_heating_season_baseline_setpoint(self, heating_season, method='ninetieth_percentile'):
        """ Calculate the heating season baseline setpoint (comfort temperature).

        Parameters
        ----------
        heating_season : array_like
            Heating season over which to calculate baseline heating setpoint.
        method : {"ninetieth_percentile"}, default: "ninetieth_percentile"
            Method to use in calculation of the baseline.

            - "ninetieth_percentile": 90th percentile of heating season
              heating setpoints.

        Returns
        -------
        baseline : pandas.Series
            The baseline heating setpoint for the heating season as determined
            by the given method.
        """
        if method != 'ninetieth_percentile':
            raise NotImplementedError
        return self.heating_setpoint[heating_season.hourly].quantile(.9)

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
            Used in calculations for "dailyavgHDD" and "hourlysumHDD".
        method : {"deltaT", "dailyavgCDD", "hourlysumCDD"}; default: "deltaT"
            Method to use in calculation of the baseline cdd.

            - "deltaT": :math:`\Delta T_{\\text{base cool}} = \\text{daily avg }
              T_{\\text{outdoor}} - T_{\\text{base cool}}`
            - "dailyavgCDD": :math:`\\text{CDD}_{\\text{base}} = \Delta T_{\\text{base
              cool}} - \Delta T_{\\text{b cool}}` where :math:`\Delta T_{\\text{base
              cool}} = \\text{daily avg } T_{\\text{outdoor}} - T_{\\text{base cool}}`
            - "hourlysumCDD": :math:`\\text{CDD}_{\\text{base}} = \\frac{\sum_{i=1}^
              {24} \\text{CDH}_{\\text{base } i}}{24}` where :math:`\\text{CDH}_{
              \\text{base } i} = \Delta T_{\\text{base cool}} - \Delta T_{\\text{b
              cool}}` and :math:`\Delta T_{\\text{base cool}} = T_{\\text{outdoor}}
              - T_{\\text{base cool}}`

        Returns
        -------
        baseline_cooling_demand : pandas.Series
            A series containing baseline daily heating demand for the cooling season.
        """
        temp_baseline = self.get_cooling_season_baseline_setpoint(cooling_season)
        hourly_temp_out = self.temperature_out[cooling_season.hourly]

        daily_temp_out = np.array([temps.mean() for day, temps in hourly_temp_out.groupby(hourly_temp_out.index.date)])

        if method == "deltaT":
            demand = daily_temp_out - temp_baseline
        elif method == "dailyavgCDD":
            demand = np.maximum(deltaT_base - (temp_baseline - daily_temp_out), 0)
        elif method == "hourlysumCDD":
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
            Used in calculations for "dailyavgHDD" and "hourlysumHDD".
        method : {"deltaT", "dailyavgHDD", "hourlysumHDD"}; default: "deltaT"
            Method to use in calculation of the baseline cdd.

            - "deltaT": :math:`\Delta T_{\\text{base heat}} = T_{\\text{base heat}}
              - \\text{daily avg } T_{\\text{outdoor}}`
            - "dailyavgHDD": :math:`\\text{HDD}_{\\text{base}} = \Delta T_{\\text{base
              heat}} - \Delta T_{\\text{b heat}}` where :math:`\Delta T_{\\text{base
              heat}} = T_{\\text{base heat}} - \\text{daily avg } T_{\\text{outdoor}}`
            - "hourlysumHDD": :math:`\\text{HDD}_{\\text{base}} = \\frac{\sum_{i=1}^
              {24} \\text{HDH}_{\\text{base } i}}{24}` where :math:`\\text{HDH}_{
              \\text{base } i} = \Delta T_{\\text{base heat}} - \Delta T_{\\text{b
              heat}}` and :math:`\Delta T_{\\text{base heat}} = T_{\\text{base heat}}
              - T_{\\text{outdoor}}`

        Returns
        -------
        baseline_heating_demand : pandas.Series
            A series containing baseline daily heating demand for the heating season.
        """
        temp_baseline = self.get_heating_season_baseline_setpoint(heating_season)
        hourly_temp_out = self.temperature_out[heating_season.hourly]

        daily_temp_out = np.array([temps.mean() for day, temps in hourly_temp_out.groupby(hourly_temp_out.index.date)])

        if method == "deltaT":
            demand = temp_baseline - daily_temp_out
        elif method == "dailyavgHDD":
            demand = np.maximum(temp_baseline - daily_temp_out - deltaT_base, 0)
        elif method == "hourlysumHDD":
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
        thermostat : thermostat.Thermostat
            The thermostat for which to estimate total baseline cooling runtime.
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
        total_avoided_runtime = daily_avoided_runtime.sum()
        total_actual_runtime = self.cool_runtime[cooling_season.daily].sum()

        return total_actual_runtime - total_avoided_runtime

    def get_total_baseline_heating_runtime(self, heating_season, daily_avoided_runtime):
        """ Estimate baseline heating runtime given a daily avoided runtimes.

        Parameters
        ----------
        thermostat : thermostat.Thermostat
            The thermostat for which to estimate total baseline heating runtime.
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
        total_avoided_runtime = daily_avoided_runtime.sum()
        total_actual_runtime = self.heat_runtime[heating_season.daily].sum()

        return total_actual_runtime - total_avoided_runtime

    ###################### Metrics #################################

    def calculate_epa_draft_rccs_field_savings_metrics(self):
        """ Calculates metrics for connected thermostat savings as defined by
        the draft specification defined by the EPA and stakeholders during early
        2015.

        Parameters
        ----------
        thermostat : thermostat.Thermostat
            Thermostat instance for which to calculate metrics

        Returns
        -------
        seasonal_metrics : list
            list of dictionaries of output metrics; one per season.
        """
        seasonal_metrics = []

        for cooling_season in self.get_cooling_seasons():
            outputs = {}
            outputs["ct_identifier"] = self.thermostat_id
            outputs["zipcode"] = self.zipcode
            outputs["equipment_type"] = self.equipment_type

            baseline_comfort_temperature = self.get_cooling_season_baseline_setpoint(cooling_season)
            outputs["baseline_comfort_temperature"] = baseline_comfort_temperature

            # calculate demand metrics

            # deltaT
            demand_deltaT = self.get_cooling_demand(cooling_season,
                    method="deltaT")
            daily_runtime = self.cool_runtime[cooling_season.daily]
            slope_deltaT, mean_sq_err_deltaT = runtime_regression(
                    daily_runtime, demand_deltaT)
            outputs["slope_deltaT"] = slope_deltaT
            outputs["mean_squared_error_deltaT"] = mean_sq_err_deltaT

            # dailyavgCDD
            demand_dailyavgCDD, deltaT_base_est_dailyavgCDD, \
                    alpha_est_dailyavgCDD, mean_sq_err_dailyavgCDD = \
                            self.get_cooling_demand(cooling_season, method="dailyavgCDD")
            outputs["deltaT_base_est_dailyavgCDD"] = deltaT_base_est_dailyavgCDD
            outputs["alpha_est_dailyavgCDD"] = alpha_est_dailyavgCDD
            outputs["mean_sq_err_dailyavgCDD"] = mean_sq_err_dailyavgCDD

            # hourlysumCDD
            demand_hourlysumCDD, deltaT_base_est_hourlysumCDD, \
                    alpha_est_hourlysumCDD, mean_sq_err_hourlysumCDD = \
                            self.get_cooling_demand(cooling_season, method="hourlysumCDD")
            outputs["deltaT_base_est_hourlysumCDD"] = deltaT_base_est_hourlysumCDD
            outputs["alpha_est_hourlysumCDD"] = alpha_est_hourlysumCDD
            outputs["mean_sq_err_hourlysumCDD"] = mean_sq_err_hourlysumCDD

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
            demand_baseline_hourlysumCDD = self.get_baseline_cooling_demand(
                    cooling_season, deltaT_base_est_hourlysumCDD,
                    method="hourlysumCDD")

            daily_avoided_runtime_deltaT = get_daily_avoided_runtime(
                    slope_deltaT, -demand_deltaT, demand_baseline_deltaT)
            daily_avoided_runtime_dailyavgCDD = get_daily_avoided_runtime( alpha_est_dailyavgCDD, demand_dailyavgCDD, demand_baseline_dailyavgCDD)
            daily_avoided_runtime_hourlysumCDD = get_daily_avoided_runtime(
                    alpha_est_hourlysumCDD, demand_hourlysumCDD,
                    demand_baseline_hourlysumCDD)

            baseline_seasonal_runtime_deltaT = \
                    self.get_total_baseline_cooling_runtime(cooling_season,
                            daily_avoided_runtime_deltaT)
            baseline_seasonal_runtime_dailyavgCDD = \
                    self.get_total_baseline_cooling_runtime(cooling_season,
                            daily_avoided_runtime_dailyavgCDD)
            baseline_seasonal_runtime_hourlysumCDD = \
                    self.get_total_baseline_cooling_runtime(cooling_season,
                            daily_avoided_runtime_hourlysumCDD)

            outputs["baseline_seasonal_runtime_deltaT"] = baseline_seasonal_runtime_deltaT
            outputs["baseline_seasonal_runtime_dailyavgCDD"] = baseline_seasonal_runtime_dailyavgCDD
            outputs["baseline_seasonal_runtime_hourlysumCDD"] = baseline_seasonal_runtime_hourlysumCDD

            baseline_daily_runtime_deltaT = baseline_seasonal_runtime_deltaT / n_days
            baseline_daily_runtime_dailyavgCDD = baseline_seasonal_runtime_dailyavgCDD / n_days
            baseline_daily_runtime_hourlysumCDD = baseline_seasonal_runtime_hourlysumCDD / n_days

            outputs["baseline_daily_runtime_deltaT"] = baseline_daily_runtime_deltaT
            outputs["baseline_daily_runtime_dailyavgCDD"] = baseline_daily_runtime_dailyavgCDD
            outputs["baseline_daily_runtime_hourlysumCDD"] = baseline_daily_runtime_hourlysumCDD

            seasonal_savings_deltaT = get_seasonal_percent_savings(
                    baseline_seasonal_runtime_deltaT,
                    daily_avoided_runtime_deltaT)
            seasonal_savings_dailyavgCDD = get_seasonal_percent_savings(
                    baseline_seasonal_runtime_dailyavgCDD,
                    daily_avoided_runtime_dailyavgCDD)
            seasonal_savings_hourlysumCDD = get_seasonal_percent_savings(
                    baseline_seasonal_runtime_hourlysumCDD,
                    daily_avoided_runtime_hourlysumCDD)

            outputs["seasonal_savings_deltaT"] = seasonal_savings_deltaT
            outputs["seasonal_savings_dailyavgCDD"] = seasonal_savings_dailyavgCDD
            outputs["seasonal_savings_hourlysumCDD"] = seasonal_savings_hourlysumCDD

            seasonal_avoided_runtime_deltaT = daily_avoided_runtime_deltaT.sum()
            seasonal_avoided_runtime_dailyavgCDD = daily_avoided_runtime_dailyavgCDD.sum()
            seasonal_avoided_runtime_hourlysumCDD = daily_avoided_runtime_hourlysumCDD.sum()

            outputs["seasonal_avoided_runtime_deltaT"] = seasonal_avoided_runtime_deltaT
            outputs["seasonal_avoided_runtime_dailyavgCDD"] = seasonal_avoided_runtime_dailyavgCDD
            outputs["seasonal_avoided_runtime_hourlysumCDD"] = seasonal_avoided_runtime_hourlysumCDD

            n_days_both, n_days_incomplete = self.get_season_ignored_days(cooling_season)

            outputs["n_days_both_heating_and_cooling"] = n_days_both
            outputs["n_days_incomplete"] = n_days_incomplete

            outputs["season_name"] = cooling_season.name

            seasonal_metrics.append(outputs)

        for heating_season in self.get_heating_seasons():
            outputs = {}
            outputs["ct_identifier"] = self.thermostat_id
            outputs["zipcode"] = self.zipcode
            outputs["equipment_type"] = self.equipment_type

            baseline_comfort_temperature = \
                    self.get_heating_season_baseline_setpoint(heating_season)
            outputs["baseline_comfort_temperature"] = baseline_comfort_temperature

            # calculate demand metrics

            # deltaT
            demand_deltaT = self.get_heating_demand(heating_season, method="deltaT")
            daily_runtime = self.heat_runtime[heating_season.daily]
            slope_deltaT, mean_sq_err_deltaT = runtime_regression(
                    daily_runtime, demand_deltaT)
            outputs["slope_deltaT"] = slope_deltaT
            outputs["mean_squared_error_deltaT"] = mean_sq_err_deltaT

            # dailyavgHDD
            demand_dailyavgHDD, deltaT_base_est_dailyavgHDD, \
                    alpha_est_dailyavgHDD, mean_sq_err_dailyavgHDD = \
                        self.get_heating_demand(heating_season, method="dailyavgHDD")
            outputs["deltaT_base_est_dailyavgHDD"] = deltaT_base_est_dailyavgHDD
            outputs["alpha_est_dailyavgHDD"] = alpha_est_dailyavgHDD
            outputs["mean_sq_err_dailyavgHDD"] = mean_sq_err_dailyavgHDD

            # hourlysumHDD
            demand_hourlysumHDD, deltaT_base_est_hourlysumHDD, \
                    alpha_est_hourlysumHDD, mean_sq_err_hourlysumHDD = \
                            self.get_heating_demand(heating_season, method="hourlysumHDD")
            outputs["deltaT_base_est_hourlysumHDD"] = deltaT_base_est_hourlysumHDD
            outputs["alpha_est_hourlysumHDD"] = alpha_est_hourlysumHDD
            outputs["mean_sq_err_hourlysumHDD"] = mean_sq_err_hourlysumHDD

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
            demand_baseline_hourlysumHDD = self.get_baseline_heating_demand(
                    heating_season, deltaT_base_est_hourlysumHDD,
                    method="hourlysumHDD")

            daily_avoided_runtime_deltaT = get_daily_avoided_runtime(
                    slope_deltaT, demand_deltaT, demand_baseline_deltaT)
            daily_avoided_runtime_dailyavgHDD = get_daily_avoided_runtime(
                    alpha_est_dailyavgHDD, demand_dailyavgHDD,
                    demand_baseline_dailyavgHDD)
            daily_avoided_runtime_hourlysumHDD = get_daily_avoided_runtime(
                    alpha_est_hourlysumHDD, demand_hourlysumHDD,
                    demand_baseline_hourlysumHDD)

            baseline_seasonal_runtime_deltaT = \
                    self.get_total_baseline_heating_runtime(heating_season,
                            daily_avoided_runtime_deltaT)
            baseline_seasonal_runtime_dailyavgHDD = \
                    self.get_total_baseline_heating_runtime(heating_season,
                            daily_avoided_runtime_dailyavgHDD)
            baseline_seasonal_runtime_hourlysumHDD = \
                    self.get_total_baseline_heating_runtime(heating_season,
                            daily_avoided_runtime_hourlysumHDD)

            outputs["baseline_seasonal_runtime_deltaT"] = baseline_seasonal_runtime_deltaT
            outputs["baseline_seasonal_runtime_dailyavgHDD"] = baseline_seasonal_runtime_dailyavgHDD
            outputs["baseline_seasonal_runtime_hourlysumHDD"] = baseline_seasonal_runtime_hourlysumHDD

            baseline_daily_runtime_deltaT = baseline_seasonal_runtime_deltaT / n_days
            baseline_daily_runtime_dailyavgHDD = baseline_seasonal_runtime_dailyavgHDD / n_days
            baseline_daily_runtime_hourlysumHDD = baseline_seasonal_runtime_hourlysumHDD / n_days

            outputs["baseline_daily_runtime_deltaT"] = baseline_daily_runtime_deltaT
            outputs["baseline_daily_runtime_dailyavgHDD"] = baseline_daily_runtime_dailyavgHDD
            outputs["baseline_daily_runtime_hourlysumHDD"] = baseline_daily_runtime_hourlysumHDD

            seasonal_savings_deltaT = get_seasonal_percent_savings(
                    baseline_seasonal_runtime_deltaT,
                    daily_avoided_runtime_deltaT)
            seasonal_savings_dailyavgHDD = get_seasonal_percent_savings(
                    baseline_seasonal_runtime_dailyavgHDD,
                    daily_avoided_runtime_dailyavgHDD)
            seasonal_savings_hourlysumHDD = get_seasonal_percent_savings(
                    baseline_seasonal_runtime_hourlysumHDD,
                    daily_avoided_runtime_hourlysumHDD)

            outputs["seasonal_savings_deltaT"] = seasonal_savings_deltaT
            outputs["seasonal_savings_dailyavgHDD"] = seasonal_savings_dailyavgHDD
            outputs["seasonal_savings_hourlysumHDD"] = seasonal_savings_hourlysumHDD

            seasonal_avoided_runtime_deltaT = daily_avoided_runtime_deltaT.sum()
            seasonal_avoided_runtime_dailyavgHDD = daily_avoided_runtime_dailyavgHDD.sum()
            seasonal_avoided_runtime_hourlysumHDD = daily_avoided_runtime_hourlysumHDD.sum()

            outputs["seasonal_avoided_runtime_deltaT"] = seasonal_avoided_runtime_deltaT
            outputs["seasonal_avoided_runtime_dailyavgHDD"] = seasonal_avoided_runtime_dailyavgHDD
            outputs["seasonal_avoided_runtime_hourlysumHDD"] = seasonal_avoided_runtime_hourlysumHDD

            n_days_both, n_days_incomplete = self.get_season_ignored_days(heating_season)

            outputs["n_days_both_heating_and_heating"] = n_days_both
            outputs["n_days_incomplete"] = n_days_incomplete

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
