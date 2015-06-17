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
    1: ["ss_heat_pump_heating","auxiliary_heat","emergency_heat"],
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

class Thermostat(object):

    def __init__(self,thermostat_id,equipment_type,
            temperature_in,temperature_setpoint,temperature_out,
            ss_heat_pump_heating=None,
            ss_heat_pump_cooling=None,
            auxiliary_heat=None,
            emergency_heat=None,
            ss_heating=None,
            ss_central_ac=None):

        self.thermostat_id = thermostat_id
        self.equipment_type = equipment_type
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

    def get_heating_seasons(self, method="simple"):
        """ Get all data for heating seasons for data associated with this
        thermostat

        Parameters
        ----------
        method : {"simple"}, default "simple"
            Method by which to find heating seasons.
             - "simple": groups all heating days (days with >= 1 hour of total
               heating and no cooling) from the July 1 to June 31 into single
               heating seasons.

        Returns
        -------
        heating_seasons : list of (pandas.Series,str) tuples
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

        # for each potential season, look for heating days.
        heating_seasons = []
        for start_year_,end_year_ in potential_seasons:
            after_start = np.datetime64(datetime(start_year_,7,1)) <= total_heating.index
            before_end = total_heating.index <= np.datetime64(datetime(end_year_,7,1))
            daily_heating_sums = total_heating.groupby(total_heating.index.date).sum()
            meets_heating_thresholds = np.array([daily_heating_sums[i.date()] >= 3600 for i,total in total_heating.iteritems()])
            if total_cooling is None:
                meets_cooling_thresholds = True
            else:
                daily_cooling_sums = total_cooling.groupby(total_cooling.index.date).sum()
                meets_cooling_thresholds = np.array([daily_cooling_sums[i.date()] < 3600 for i,total in total_cooling.iteritems()])
            inclusion = after_start & before_end & meets_heating_thresholds & meets_cooling_thresholds
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
        method : {"simple"}, default "simple"
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

        # for each potential season, look for cooling days.
        cooling_seasons = []
        for year in potential_seasons:
            after_start = np.datetime64(datetime(year,1,1)) <= total_cooling.index
            before_end = total_cooling.index <= np.datetime64(datetime(year + 1,1,1))
            daily_cooling_sums = total_cooling.groupby(total_cooling.index.date).sum()
            meets_cooling_thresholds = np.array([daily_cooling_sums[i.date()] >= 3600 for i,total in total_cooling.iteritems()])
            if total_heating is None:
                meets_heating_thresholds = True
            else:
                daily_heating_sums = total_heating.groupby(total_heating.index.date).sum()
                meets_heating_thresholds = np.array([daily_heating_sums[i.date()] < 3600 for i,total in total_heating.iteritems()])
            inclusion = after_start & before_end & meets_cooling_thresholds & meets_heating_thresholds
            cooling_season_days = pd.Series(inclusion,index=total_cooling.index)
            if any(cooling_season_days):
                cooling_season_name = "{} Cooling Season".format(year)
                cooling_season = (cooling_season_days,cooling_season_name)
                cooling_seasons.append(cooling_season)

        return cooling_seasons
