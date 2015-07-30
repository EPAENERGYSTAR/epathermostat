from thermostat import Thermostat

import pandas as pd
import numpy as np
from eemeter.consumption import DatetimePeriod
from eemeter.location import zipcode_to_tmy3
from eemeter.weather import ISDWeatherSource

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
    thermostats : list of thermostat.Thermostat objects
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
            station = zipcode_to_tmy3(row.zipcode)
            weather_source = ISDWeatherSource(station,intervals.index[0].year,intervals.index[-1].year)
            temperature_out = get_hourly_outdoor_temperature(intervals.index,weather_source)
            thermostat = Thermostat(row.thermostat_id,row.equipment_type,row.zipcode,temperature_in,temperature_setpoint,temperature_out,**kwargs)
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

    Returns
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
    hourly_weather_source : eemeter.weather.ISDWeatherSource
        Should give hourly temperatures for the relevant date-time period from
        a particular weather station.
    include_endpoint : bool, default True
        Whether or not the final value :code:`hourly_index[-1]` should be
        truncated from this provided index, resulting in an index of length
        :code:`len(hourly_index) - 1`. This is a convenience to help deal with
        differences between the way pandas handles creation of indices and the
        way eemeter handles fetching temperatures from DatetimePeriods with
        start and end dates.

    Returns
    -------
    out : pandas.Series
        Temperature data provided by the weather source and indexed by the
        provided datetime index.
    """
    hourly_temps = [hourly_weather_source.data.get(dt.strftime("%Y%m%d%H"),np.nan)
            for dt in hourly_index]
    return pd.Series(hourly_temps,index=hourly_index,name="temperature_out")
