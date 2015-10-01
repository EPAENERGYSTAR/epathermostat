from thermostat import Thermostat

import pandas as pd
import numpy as np
from eemeter.location import zipcode_to_station
from eemeter.weather import ISDWeatherSource
from eemeter.evaluation import Period

import warnings
from datetime import datetime
from datetime import timedelta
import dateutil.parser

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
    metadata = pd.read_csv(metadata_filename,
            dtype={"thermostat_id": str, "zipcode": str, "utc_offset": str, "equipment_type": int })
    interval_data = pd.read_csv(interval_data_filename)


    thermostats = []
    for i, row in metadata.iterrows():

        # make sure this thermostat type is supported.
        if row.equipment_type == 0:
            warnings.warn("Skipping import of thermostat controlling equipment"
                          " of unsupported type. (id={})".format(row.thermostat_id))
            continue

        # filter by thermostat id
        days = interval_data[interval_data.thermostat_id == row.thermostat_id]

        # load indices
        dates = pd.to_datetime(days["date"])
        daily_index = pd.DatetimeIndex(start=dates[0], periods = dates.shape[0], freq="D")
        hourly_index = pd.DatetimeIndex(start=dates[0], periods = dates.shape[0] * 24, freq="H")

        # raise an error if dates are not aligned
        if not all(dates == daily_index):
            message("Dates provided for thermostat_id={} may contain some "
                    "which are out of order, missing, or duplicated.".format(row.thermostat_id))
            raise ValueError(message)

        # load hourly time series values
        temp_in = pd.Series(get_hourly_block(days, "temp_in"), hourly_index)
        cooling_setpoint = pd.Series(get_hourly_block(days, "cooling_setpoint"), hourly_index)
        heating_setpoint = pd.Series(get_hourly_block(days, "heating_setpoint"), hourly_index)

        # load outdoor temperatures
        station = zipcode_to_station(row.zipcode)
        ws_hourly = ISDWeatherSource(station, daily_index[0].year, daily_index[-1].year)
        utc_offset = dateutil.parser.parse("2000-01-01T00:00:00" + row.utc_offset).tzinfo.utcoffset(None)
        temp_out = pd.Series(get_outdoor_temperatures(daily_index, ws_hourly, utc_offset), hourly_index)

        # load daily time series values
        cool_runtime = pd.Series(days["cool_runtime"].values, daily_index)
        heat_runtime = pd.Series(days["heat_runtime"].values, daily_index)
        auxiliary_heat_runtime = pd.Series(days["auxiliary_heat_runtime"].values, daily_index)
        emergency_heat_runtime = pd.Series(days["emergency_heat_runtime"].values, daily_index)

        # create thermostat instance
        thermostat = Thermostat(row.thermostat_id, row.equipment_type, row.zipcode,
                temp_in, temp_out, cooling_setpoint, heating_setpoint,
                cool_runtime, heat_runtime, auxiliary_heat_runtime,
                emergency_heat_runtime)

        thermostats.append(thermostat)

    return thermostats

def get_hourly_block(df, prefix):
    columns = ["{}_{:02d}".format(prefix, i) for i in range(24)]
    values = df[columns].values
    return values.reshape((values.shape[0] * values.shape[1],))

def get_outdoor_temperatures(dates, ws_hourly, utc_offset):
    all_temps = []
    for date in dates:
        date = date - utc_offset
        period = Period(date, date + timedelta(days=1))
        temps = ws_hourly.hourly_temperatures(period, "degF")
        all_temps.append(temps)
    return np.array(all_temps).reshape(dates.shape[0] * 24)
