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
import os

def from_csv(metadata_filename, verbose=False):
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
            dtype={"thermostat_id": str, "zipcode": str, "utc_offset": str, "equipment_type": int, "interval_data_filename": str})


    thermostats = []
    for i, row in metadata.iterrows():
        if verbose:
            print("Importing thermostat {}".format(row.thermostat_id))

        # make sure this thermostat type is supported.
        if row.equipment_type not in [1,2,3,4,5]:
            warnings.warn("Skipping import of thermostat controlling equipment"
                          " of unsupported type. (id={})".format(row.thermostat_id))
            continue

        interval_data_filename = os.path.join(os.path.dirname(metadata_filename), row.interval_data_filename)

        thermostat = get_single_thermostat(
                row.thermostat_id, row.zipcode, row.equipment_type, row.utc_offset, interval_data_filename )

        thermostats.append(thermostat)

    return thermostats

def get_single_thermostat(thermostat_id, zipcode, equipment_type, utc_offset, interval_data_filename):
    df = pd.read_csv(interval_data_filename)

    heating, cooling, aux_emerg = _get_equipment_type(equipment_type)

    # load indices
    dates = pd.to_datetime(df["date"])
    daily_index = pd.DatetimeIndex(start=dates[0], periods = dates.shape[0], freq="D")
    hourly_index = pd.DatetimeIndex(start=dates[0], periods = dates.shape[0] * 24, freq="H")

    # raise an error if dates are not aligned
    if not all(dates == daily_index):
        message("Dates provided for thermostat_id={} may contain some "
                "which are out of order, missing, or duplicated.".format(thermostat_id))
        raise ValueError(message)

    # load hourly time series values
    temp_in = pd.Series(_get_hourly_block(df, "temp_in"), hourly_index)

    if heating:
        heating_setpoint = pd.Series(_get_hourly_block(df, "heating_setpoint"), hourly_index)
    else:
        heating_setpoint = None

    if cooling:
        cooling_setpoint = pd.Series(_get_hourly_block(df, "cooling_setpoint"), hourly_index)
    else:
        cooling_setpoint = None

    if aux_emerg:
        auxiliary_heat_runtime = pd.Series(_get_hourly_block(df, "auxiliary_heat_runtime"), hourly_index)
        emergency_heat_runtime = pd.Series(_get_hourly_block(df, "emergency_heat_runtime"), hourly_index)
    else:
        auxiliary_heat_runtime = None
        emergency_heat_runtime = None

    # load outdoor temperatures
    station = zipcode_to_station(zipcode)
    ws_hourly = ISDWeatherSource(station, daily_index[0].year, daily_index[-1].year)
    utc_offset = dateutil.parser.parse("2000-01-01T00:00:00" + utc_offset).tzinfo.utcoffset(None)
    temp_out = pd.Series(_get_outdoor_temperatures(daily_index, ws_hourly, utc_offset), hourly_index)

    # load daily time series values
    if cooling:
        cool_runtime = pd.Series(df["cool_runtime"].values, daily_index)
    else:
        cool_runtime = None
    if heating:
        heat_runtime = pd.Series(df["heat_runtime"].values, daily_index)
    else:
        heat_runtime = None

    # create thermostat instance
    thermostat = Thermostat(thermostat_id, equipment_type, zipcode, station,
            temp_in, temp_out, cooling_setpoint, heating_setpoint,
            cool_runtime, heat_runtime, auxiliary_heat_runtime,
            emergency_heat_runtime)
    return thermostat

def _get_hourly_block(df, prefix):
    columns = ["{}_{:02d}".format(prefix, i) for i in range(24)]
    values = df[columns].values
    return values.reshape((values.shape[0] * values.shape[1],))

def _get_outdoor_temperatures(dates, ws_hourly, utc_offset):
    all_temps = []
    for date in dates:
        date = date - utc_offset
        period = Period(date, date + timedelta(days=1))
        temps = ws_hourly.hourly_temperatures(period, "degF")
        all_temps.append(temps)
    return np.array(all_temps).reshape(dates.shape[0] * 24)

def _get_equipment_type(equipment_type):
    """
    Returns
    -------
    heating : boolean
        True if the equipment type has heating equipment
    cooling : boolean
        True if the equipment type has cooling equipment
    aux_emerg : boolean
        True if the equipment type has auxiliary/emergency heat equipment
    """
    if equipment_type == 1:
        return True, True, True
    elif equipment_type == 2:
        return True, True, False
    elif equipment_type == 3:
        return True, True, False
    elif equipment_type == 4:
        return True, False, False
    elif equipment_type == 5:
        return False, True, False
    else:
        return None
