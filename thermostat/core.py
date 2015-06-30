import pandas as pd
import numpy as np

from datetime import datetime

# tuples of columns are "at least one of"
EQUIPMENT_TYPE_REQUIRED_COLUMNS = {
    0: [],
    1: ["ss_heat_pump_heating","ss_heat_pump_cooling",("auxiliary_heat","emergency_heat")],
    2: ["ss_heat_pump_heating","ss_heat_pump_cooling"],
    3: ["ss_heating","ss_central_ac"],
    4: ["ss_heating"],
    5: ["ss_central_ac"],
}

EQUIPMENT_TYPE_DISALLOWED_COLUMNS = {
    0: [],
    1: [],
    2: ["auxiliary_heat","emergency_heat"],
    3: [],
    4: ["ss_central_ac"],
    5: ["ss_heating"],
}

EQUIPMENT_TYPE_HEATING_COLUMNS = {
    0: [],
    1: ["ss_heat_pump_heating"],
    2: ["ss_heat_pump_heating"],
    3: ["ss_heating"],
    4: ["ss_heating"],
    5: [],
}

EQUIPMENT_TYPE_COOLING_COLUMNS = {
    0: [],
    1: ["ss_heat_pump_cooling"],
    2: ["ss_heat_pump_cooling"],
    3: ["ss_central_ac"],
    4: [],
    5: ["ss_central_ac"],
}

EQUIPMENT_TYPE_RESISTANCE_HEAT_COLUMNS = {
    0: [],
    1: ["auxiliary_heat","emergency_heat"],
    2: [],
    3: [],
    4: [],
    5: [],
}

class Thermostat(object):
    """ Main thermostat data container. Each parameter which contains
    timeseries data should be a pandas.Series with a datetimeIndex, and that
    each index should be equivalent.

    Parameters
    ----------
    thermostat_id : object
        An identifier for the thermostat. Can be anything, but should be
        identifying (e.g. an ID provided by the manufacturer).
    equipment_type : {0,1,2,3,4,5}
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
    temperature_setpoint : pandas.Series
        Contains target temperature (setpoint) data in degrees Fahrenheit (F),
        with resolution of at least 0.5F.
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    temperature_out : pandas.Series
        Contains outdoor temperature (setpoint) data as observed by a relevant
        weather station in degrees Fahrenheit (F), with resolution of at least
        0.5F.
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    ss_heat_pump_heating : pandas.Series,
        Heating run times for a single single-stage heat pump controlled by the
        thermostat, measured in seconds. No datapoint should exceed 3600 s,
        which would indicate over an hour of heating within one hour.
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    ss_heat_pump_cooling : pandas.Series,
        Cooling run times for a single single-stage heat pump controlled by the
        thermostat, measured in seconds. No datapoint should exceed 3600 s,
        which would indicate over an hour of heating within one hour.
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    auxiliary_heat : pandas.Series,
        Auxiliary heat run times for equipment controlled by the
        thermostat, measured in seconds. No datapoint should exceed 3600 s,
        which would indicate over an hour of heating within one hour.
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    emergency_heat : pandas.Series,
        Emergency heat run times for equipment controlled by the
        thermostat, measured in seconds. No datapoint should exceed 3600 s,
        which would indicate over an hour of heating within one hour.
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    ss_heating : pandas.Series,
        Heating run times for single-stage heating equipment controlled by the
        thermostat, measured in seconds. No datapoint should exceed 3600 s,
        which would indicate over an hour of heating within one hour.
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    ss_central_ac : pandas.Series):
        Cooling run times for single-stage central air conditioning equipment
        controlled by the thermostat, measured in seconds. No datapoint should
        exceed 3600 s, which would indicate over an hour of heating within one
        hour.
        Should be indexed by a pandas.DatetimeIndex with hourly frequency (i.e.
        :code:`freq='H'`).
    """

    def __init__(self,thermostat_id,equipment_type,zipcode,
            temperature_in,temperature_setpoint,temperature_out,
            ss_heat_pump_heating=None,
            ss_heat_pump_cooling=None,
            auxiliary_heat=None,
            emergency_heat=None,
            ss_heating=None,
            ss_central_ac=None):

        self.thermostat_id = thermostat_id
        self.equipment_type = equipment_type
        self.zipcode = zipcode
        self.temperature_in = temperature_in
        self.temperature_setpoint = temperature_setpoint
        self.temperature_out = temperature_out

        self._match_equipment_type_columns(
                ss_heat_pump_heating,
                ss_heat_pump_cooling,
                auxiliary_heat,
                emergency_heat,
                ss_heating,
                ss_central_ac)

    def _match_equipment_type_columns(self,
            ss_heat_pump_heating,
            ss_heat_pump_cooling,
            auxiliary_heat,
            emergency_heat,
            ss_heating,
            ss_central_ac):

        columns = {
                "ss_heat_pump_heating": ss_heat_pump_heating,
                "ss_heat_pump_cooling": ss_heat_pump_cooling,
                "auxiliary_heat": auxiliary_heat,
                "emergency_heat": emergency_heat,
                "ss_heating": ss_heating,
                "ss_central_ac": ss_central_ac
                }

        # Make sure we have a valid equipment type
        if not self.equipment_type in EQUIPMENT_TYPE_REQUIRED_COLUMNS.keys():
            message = "Unrecognized equipment_type. Should be one of {}"\
                    .format(EQUIPMENT_TYPE_REQUIRED_COLUMNS.keys())
            raise ValueError(message)

        # Make sure required columns are present, add them as attributes if
        # they are, and complain if they're not.
        for required_column in EQUIPMENT_TYPE_REQUIRED_COLUMNS[self.equipment_type]:
            if type(required_column) == tuple:
                if any([columns[column_name] is not None for column_name in required_column]):
                    for column_name in required_column:
                        self.__dict__[column_name] = columns[column_name]
                else:
                    message = ("The columns {} are missing, but at least one "
                               "of them must be supplied for equipment_type {}.")\
                            .format(required_column,self.equipment_type)
                    raise ValueError(message)
            else:
                if columns[required_column] is None:
                    message = ("The column '{}' is missing, but is required for "
                               "equipment_type {}.").format(required_column,self.equipment_type)
                    raise ValueError(message)
                else:
                    self.__dict__[required_column] = columns[required_column]

        # Make sure disallowed columns are not present and complain if they are.
        disallowed_columns = EQUIPMENT_TYPE_DISALLOWED_COLUMNS[self.equipment_type]
        for column_name, column in columns.iteritems():
            if column is not None and column_name in disallowed_columns:
                    message = ("The column '{}' is not allowed for"
                               "equipment type {}.").format(column_name,self.equipment_type)
                    raise ValueError(message)

    def get_heating_columns(self):
        """ Get all data for heating equipment this thermostat controls.

        Returns
        -------
        heating_columns : list of pandas.Series
            All columns representing heating equipment for this thermostat.
        """
        heating_column_names = EQUIPMENT_TYPE_HEATING_COLUMNS[self.equipment_type]
        heating_columns = []
        for column_name in heating_column_names:
            column = self.__dict__.get(column_name)
            if column is not None:
                heating_columns.append(column)
        return heating_columns

    def get_cooling_columns(self):
        """ Get all data for cooling equipment this thermostat controls.

        Returns
        -------
        cooling_columns : list of pandas.Series
            All columns representing cooling equipment for this thermostat.
        """
        cooling_column_names = EQUIPMENT_TYPE_COOLING_COLUMNS[self.equipment_type]
        cooling_columns = []
        for column_name in cooling_column_names:
            column = self.__dict__.get(column_name)
            if column is not None:
                cooling_columns.append(column)
        return cooling_columns

    def get_resistance_heat_columns(self):
        """ Get all data for resistance heating equipment this thermostat
        controls.

        Returns
        -------
        rh_columns : list of pandas.Series
            All columns representing resistance heating equipment for this
            thermostat.
        """
        rh_column_names = EQUIPMENT_TYPE_RESISTANCE_HEAT_COLUMNS[self.equipment_type]
        rh_columns = []
        for column_name in rh_column_names:
            column = self.__dict__.get(column_name)
            if column is not None:
                rh_columns.append(column)
        return rh_columns

    def get_heating_seasons(self, method="simple"):
        """ Get all data for heating seasons for data associated with this
        thermostat

        Parameters
        ----------
        method : {"simple"}, default: "simple"
            Method by which to find heating seasons.

            - "simple": groups all heating days (days with >= 1 hour of total
              heating and no cooling) from the July 1 to June 31 into single
              heating seasons.

        Returns
        -------
        heating_seasons : list of (pandas.Series, str) tuples
            List of seasons detected; first element of tuple is season, second
            is name. Seasons are represented as pandas Series of boolean values,
            intended to be used as selectors or masks on the thermostat data.
            A value of True at a particular index indicates inclusion of
            of the data at that index in the season. Names are of the form
            "YYYY-YYYY Heating Season"
        """

        # combine columns to get total heating.
        heating_columns = self.get_heating_columns()
        if heating_columns == []:
            return []
        total_heating = pd.DataFrame(heating_columns).sum(axis=0)

        # need cooling so that we exclude heating days which also have cooling
        cooling_columns = self.get_cooling_columns()
        if cooling_columns == []:
            total_cooling = None
        else:
            total_cooling = pd.DataFrame(cooling_columns).sum(axis=0)

        # find all potential heating season ranges
        start_year = total_heating.index[0].year - 1
        end_year = total_heating.index[-1].year + 1
        potential_seasons = zip(range(start_year,end_year),range(start_year+1,end_year+1))

        # compute inclusion thresholds
        daily_heating_sums = total_heating.groupby(total_heating.index.date).sum()
        meets_heating_thresholds = np.array([daily_heating_sums[i.date()] >= 3600 for i,total in total_heating.iteritems()])

        daily_heating_counts = total_heating.groupby(total_heating.index.date).count()
        day_is_complete = np.array([daily_heating_counts[i.date()] == 24 for i,total in total_heating.iteritems()])

        if total_cooling is None:
            meets_cooling_thresholds = True
        else:
            daily_cooling_sums = total_cooling.groupby(total_cooling.index.date).sum()
            meets_cooling_thresholds = np.array([daily_cooling_sums[i.date()] <= 0 for i,total in total_cooling.iteritems()])

        # for each potential season, look for heating days.
        heating_seasons = []
        for start_year_,end_year_ in potential_seasons:
            after_start = np.datetime64(datetime(start_year_,7,1)) <= total_heating.index
            before_end = total_heating.index <= np.datetime64(datetime(end_year_,7,1))
            inclusion = after_start & before_end & meets_heating_thresholds & meets_cooling_thresholds & day_is_complete
            heating_season_days = pd.Series(inclusion,index=total_heating.index)
            if any(heating_season_days):
                heating_season_name = "{}-{} Heating Season".format(start_year_,end_year_)
                heating_season = (heating_season_days,heating_season_name)
                heating_seasons.append(heating_season)

        return heating_seasons

    def get_cooling_seasons(self, method="simple"):
        """ Get all data for cooling seasons for data associated with this
        thermostat.

        Parameters
        ----------
        method : {"simple"}, default: "simple"
            Method by which to find cooling seasons.

            - "simple": groups all cooling days (days with >= 1 hour of total
              cooling and no heating) from January 1 to December 31 into
              single cooling seasons.

        Returns
        -------
        cooling_seasons : list of (pandas.Series,str) tuples
            List of seasons detected; first element of tuple is season, second
            is name. Seasons are represented as pandas Series of boolean values,
            intended to be used as selectors or masks on the thermostat data.
            A value of True at a particular index indicates inclusion of
            of the data at that index in the season. Names are of the form
            "YYYY Cooling Season"
        """

        # combine columns to get total cooling.
        cooling_columns = self.get_cooling_columns()
        if cooling_columns == []:
            return []
        total_cooling = pd.DataFrame(cooling_columns).sum(axis=0)

        # need heating so that we exclude cooling days which also have heating
        heating_columns = self.get_heating_columns()
        if heating_columns == []:
            total_heating = None
        else:
            total_heating = pd.DataFrame(heating_columns).sum(axis=0)

        # find all potential cooling season ranges
        start_year = total_cooling.index[0].year
        end_year = total_cooling.index[-1].year
        potential_seasons = range(start_year,end_year + 1)

        # compute inclusion thresholds
        daily_cooling_sums = total_cooling.groupby(total_cooling.index.date).sum()
        meets_cooling_thresholds = np.array([daily_cooling_sums[i.date()] >= 3600 for i,total in total_cooling.iteritems()])

        daily_cooling_counts = total_cooling.groupby(total_cooling.index.date).count()
        day_is_complete = np.array([daily_cooling_counts[i.date()] == 24 for i,total in total_cooling.iteritems()])

        if total_heating is None:
            meets_heating_thresholds = True
        else:
            daily_heating_sums = total_heating.groupby(total_heating.index.date).sum()
            meets_heating_thresholds = np.array([daily_heating_sums[i.date()] <= 0 for i,total in total_heating.iteritems()])

        # for each potential season, look for cooling days.
        cooling_seasons = []
        for year in potential_seasons:
            after_start = np.datetime64(datetime(year,1,1)) <= total_cooling.index
            before_end = total_cooling.index <= np.datetime64(datetime(year + 1,1,1))
            inclusion = after_start & before_end & meets_cooling_thresholds & meets_heating_thresholds & day_is_complete
            cooling_season_days = pd.Series(inclusion,index=total_cooling.index)
            if any(cooling_season_days):
                cooling_season_name = "{} Cooling Season".format(year)
                cooling_season = (cooling_season_days,cooling_season_name)
                cooling_seasons.append(cooling_season)

        return cooling_seasons

    def get_heating_season_total_runtime(self,heating_season):
        """
        Seasonal heating times for a particular heating season

        Parameters
        ----------
        heating_season : pd.Series
            Boolean array indicating presence in heating season.

        Returns
        -------
        runtimes : list of int
            Runtimes for each heating column in the order returned by self.get_heating_columns()
        """
        heating_columns = self.get_heating_columns()
        runtimes = []
        for column in heating_columns:
            runtimes.append(column[heating_season].sum())
        return runtimes

    def get_cooling_season_total_runtime(self,cooling_season):
        """
        Seasonal cooling times for a particular cooling season

        Parameters
        ----------
        cooling_season : pd.Series
            Boolean array indicating presence in cooling season.

        Returns
        -------
        runtimes : list of int
            Runtimes for each cooling column in the order returned by self.get_cooling_columns()
        """
        cooling_columns = self.get_cooling_columns()
        runtimes = []
        for column in cooling_columns:
            runtimes.append(column[cooling_season].sum())
        return runtimes

    def get_resistance_heat_utilization(self,heating_season,bin_step=5):
        """ Calculates resistance heat utilization metrics in temperature
        bins between 0 and 60 degrees Fahrenheit.

        Parameters
        ----------
        heating_season : pandas.Series
            Heating season for which to calculate resistance heat utilization.
        bin_step : int, default: 5
            Step size of temperature bins.

        Returns
        -------
        RHUs : numpy.array or None
            Resistance heat utilization for each temperature bin, ordered
            ascending by temperature bin. Returns None if the thermostat does
            not control the appropriate equipment
        """
        bin_step = 5
        resistance_heat_columns = self.get_resistance_heat_columns()
        if self.equipment_type == 1 and len(resistance_heat_columns) == 2:
            RHUs = []
            temperature_bins = [(i,i+5)for i in range(0,60,5)]
            for low_temp,high_temp in temperature_bins:
                temp_bin = self.temperature_out[low_temp <= self.temperature_out] < high_temp
                R_heat = self.ss_heat_pump_heating.sum()
                R_aux = self.auxiliary_heat.sum()
                R_emg = self.emergency_heat.sum()
                rhu = float(R_aux + R_emg) / float(R_heat + R_emg)
                RHUs.append(rhu)
            return np.array(RHUs)
        else:
            return None

    def get_season_ignored_days(self,season_name):
        season_range = None
        if "Cooling" in season_name:
            season_range = datetime(int(season_name[:4]),7,1),datetime(int(season_name[:4]) + 1,7,1)
        elif "Heating" in season_name:
            season_range = datetime(int(season_name[:4]),1,1),datetime(int(season_name[:4]) + 1,1,1)
        else:
            raise NotImplementedError

        # cooling
        cooling_columns = self.get_cooling_columns()
        if cooling_columns == []:
            total_cooling = None
        else:
            total_cooling = pd.DataFrame(cooling_columns).sum(axis=0)
            after_start = np.datetime64(season_range[0]) <= total_cooling.index
            before_end = total_cooling.index <= np.datetime64(season_range[1])

        if total_cooling is None:
            meets_cooling_thresholds = False
        else:
            daily_cooling_sums = total_cooling.groupby(total_cooling.index.date).sum()
            meets_cooling_thresholds = np.array([daily_cooling_sums[i.date()] > 0 for i,total in total_cooling.iteritems()])

        # heating
        heating_columns = self.get_heating_columns()
        if heating_columns == []:
            total_heating = None
        else:
            total_heating = pd.DataFrame(heating_columns).sum(axis=0)
            after_start = np.datetime64(season_range[0]) <= total_heating.index
            before_end = total_heating.index <= np.datetime64(season_range[1])

        if total_heating is None:
            meets_heating_thresholds = False
        else:
            daily_heating_sums = total_heating.groupby(total_heating.index.date).sum()
            meets_heating_thresholds = np.array([daily_heating_sums[i.date()] > 0 for i,total in total_heating.iteritems()])

        # completeness
        if "Cooling" in season_name:
            daily_cooling_counts = total_cooling.groupby(total_cooling.index.date).count()
            day_is_incomplete = np.array([daily_cooling_counts[i.date()] != 24 for i,total in total_cooling.iteritems()])
        elif "Heating" in season_name:
            daily_heating_counts = total_heating.groupby(total_heating.index.date).count()
            day_is_incomplete = np.array([daily_heating_counts[i.date()] != 24 for i,total in total_heating.iteritems()])

        has_both = pd.Series(meets_heating_thresholds & meets_cooling_thresholds & after_start & before_end, index=self.temperature_in.index)
        is_incomplete = pd.Series(after_start & before_end & day_is_incomplete, index=self.temperature_in.index)

        n_days_both = sum(has_both.groupby(has_both.index.date).sum() > 0)
        n_days_incomplete = sum(is_incomplete.groupby(is_incomplete.index.date).sum() > 0)
        return n_days_both, n_days_incomplete
