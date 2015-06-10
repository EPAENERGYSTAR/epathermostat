from thermostat import Thermostat

import pandas as pd
from eemeter.consumption import DatetimePeriod

import warnings
from datetime import timedelta


RUNTIME_COLUMNS = [
    "ss_heat_pump_heating",
    "ss_heat_pump_cooling",
    "auxiliary_heat",
    "emergency_heat",
    "ss_heating",
    "ss_central_ac",
]

def from_csv(metadata_filename,interval_data_filename):
    """
    Creates Thermostat objects from data stored in CSV files.

    Parameters
    ----------
    metadata_filename : str
        Path to a file containing the thermostat metadata.
    interval_data_filename : str
        Path to a file containing the thermostat interval readings.

    Returns
    -------
    thermostats : list of thermostat objects
        Thermostats imported from the given CSV input files.
    """
    metadata = pd.read_csv(metadata_filename,dtype={"zipcode":str,"equipment_type":int})
    interval_data = pd.read_csv(interval_data_filename,
                                dtype={
                                    "temperature_in": float,
                                    "temperature_setpoint": float,
                                    "ss_heat_pump_heating": float,
                                    "ss_heat_pump_cooling": float,
                                    "auxiliary_heat": float,
                                    "emergency_heat": float,
                                    "ss_heating": float,
                                    "ss_central_ac": float},
                                parse_dates=["start_datetime","end_datetime"])

    thermostats = []
    for i, row in metadata.iterrows():
        if row.equipment_type == 0:
            warnings.warn("Skipping import of thermostat controlling equipment"
                          " of unsupported type.")
        else:
            intervals = interval_data[interval_data.thermostat_id == row.thermostat_id]
            intervals = reindex_intervals(intervals)
            kwargs = {}
            for column in RUNTIME_COLUMNS:
                if not all(pd.isnull(intervals[column])):
                    kwargs[column] = intervals[column]
            temperature_in = intervals.temperature_in
            temperature_setpoint = intervals.temperature_setpoint
            thermostat = Thermostat(row.thermostat_id,row.equipment_type,temperature_in,temperature_setpoint,**kwargs)
            thermostats.append(thermostat)
    return thermostats

def reindex_intervals(interval_df):
    """
    Takes a dataframe of intervals for a particular thermostat and
    reindexes using a DatetimeIndex

    Parameters
    ----------
    interval_df : pandas.DataFrame
        DataFrame to be reindexed.

    Results
    -------
    out : pandas.DataFrame
        Data reindexed with a DatetimeIndex
    """
    new_index = interval_df.start_datetime
    reindexed_df = interval_df.drop(["start_datetime","end_datetime"],1)
    return reindexed_df.set_index(new_index)

def get_hourly_outdoor_temperature(hourly_index,hourly_weather_source,include_endpoint=True):
    """
    Grabs hourly temperature from NOAA.

    Parameters
    ----------
    hourly_index : pandas.DatetimeIndex
        Index to be used to create index of temperature dataframe.
    include_endpoint : bool, default True
        Whether or not the final value (hourly_index[-1]) should be truncated
        from this provided index, resulting in an index of length
        len(hourly_index) - 1. This is a convenience to help deal with due
        differences between the way pandas handles creation of indices and the
        eemeter handles fetching temperatures from DatetimePeriods with start
        and end dates.

    Results
    -------
    out : pandas.Series
        Temperature data provided by the weather source and indexed by the
        provided datetime index.
    """
    if include_endpoint:
        start, end = hourly_index[0], hourly_index[-1] + timedelta(seconds=3600)
    else:
        start, end = hourly_index[0], hourly_index[-1]
    period = DatetimePeriod(start,end)
    hourly_temps = hourly_weather_source.hourly_temperatures(period,"degF")
    if include_endpoint:
        return pd.Series(hourly_temps,index=hourly_index,name="temperature_out")
    else:
        return pd.Series(hourly_temps,index=hourly_index[:-1],name="temperature_out")
