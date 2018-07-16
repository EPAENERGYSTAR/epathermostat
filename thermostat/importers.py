from thermostat.core import Thermostat

import pandas as pd
import numpy as np
from eemeter.weather.location import zipcode_to_usaf_station
from eemeter.weather import ISDWeatherSource
from eemeter.weather.cache import SqliteJSONStore
import json

import warnings
from datetime import datetime
from datetime import timedelta
import dateutil.parser
import os
import errno
import pytz
from multiprocessing import Pool, cpu_count
from functools import partial

try:
    NUMBER_OF_CORES = len(os.sched_getaffinity(0))
except AttributeError:
    NUMBER_OF_CORES = cpu_count()
MAX_FTP_CONNECTIONS = 3
AVAILABLE_PROCESSES = min(NUMBER_OF_CORES, MAX_FTP_CONNECTIONS)


def save_json_cache(index, thermostat_id, station, cache_path=None):
    """ Saves the cached results from eemeter into a JSON file.

    Parameters
    ----------
    index : pd.DatetimeIndex
        hourly index used to compute the years needed.
    thermostat_id : str
        A unique identifier for the termostat (used for the filename)
    station : str
        Station ID used to retrieve the weather data.
    cache_path : str
        Directory path to save the cached data
    """
    if cache_path is None:
        directory = os.path.join(
            os.curdir,
            "epathermostat_weather_data")
    else:
        directory = os.path.normpath(
            cache_path)

    try:
        os.mkdir(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    json_cache = {}
    sqlite_json_store = SqliteJSONStore()
    years = index.groupby(index.year).keys()
    for year in years:
        filename = "ISD-{station}-{year}.json".format(
                station=station,
                year=year)
        json_cache[filename] = sqlite_json_store.retrieve_json(filename)

    thermostat_filename = "{thermostat_id}.json".format(thermostat_id=thermostat_id)
    thermostat_path = os.path.join(directory, thermostat_filename)
    try:
        with open(thermostat_path, 'w') as outfile:
            json.dump(json_cache, outfile)

    except Exception as e:
        warnings.warn("Unable to write JSON file: {}".format(e))


def normalize_utc_offset(utc_offset):
    """
    Normalizes the UTC offset
    Returns the UTC offset based on the string passed in.

    Parameters
    ----------
    utc_offset : str
        String representation of the UTC offset

    Returns
    -------
    datetime timdelta offset
    """
    try:
        if int(utc_offset) == 0:
            utc_offset = "+0"
        delta = dateutil.parser.parse(
            "2000-01-01T00:00:00" + str(utc_offset)).tzinfo.utcoffset(None)
        return delta

    except (ValueError, TypeError, AttributeError) as e:
        raise TypeError("Invalid UTC offset: {} ({})".format(
           utc_offset,
           e))


def from_csv(metadata_filename, verbose=False, save_cache=False, cache_path=None):
    """
    Creates Thermostat objects from data stored in CSV files.

    Parameters
    ----------
    metadata_filename : str
        Path to a file containing the thermostat metadata.
    verbose : boolean
        Set to True to output a more detailed log of import activity.
    save_cache: boolean
        Set to True to save the cached data to a json file (based on Thermostat ID).
    cache_path: str
        Directory path to save the cached data

    Returns
    -------
    thermostats : iterator over thermostat.Thermostat objects
        Thermostats imported from the given CSV input files.
    """
    metadata = pd.read_csv(
        metadata_filename,
        dtype={
            "thermostat_id": str,
            "zipcode": str,
            "utc_offset": str,
            "equipment_type": int,
            "interval_data_filename": str
        }
    )

    p = Pool(AVAILABLE_PROCESSES)
    multiprocess_func_partial = partial(
            multiprocess_func,
            metadata_filename=metadata_filename,
            verbose=verbose,
            save_cache=save_cache,
            cache_path=cache_path)
    result_list = p.imap(multiprocess_func_partial, metadata.iterrows())
    p.close()
    p.join()

    # Bad thermostats return None so remove those.
    results = [x for x in result_list if x is not None]

    # Convert this to an iterator to maintain compatibility
    return iter(results)


def multiprocess_func(metadata, metadata_filename, verbose=False, save_cache=False, cache_path=None):
    i, row = metadata
    if verbose:
        print("Importing thermostat {}".format(row.thermostat_id))

    # make sure this thermostat type is supported.
    if row.equipment_type not in [1, 2, 3, 4, 5]:
        warnings.warn(
            "Skipping import of thermostat controlling equipment"
            " of unsupported type. (id={})".format(row.thermostat_id))
        return

    interval_data_filename = os.path.join(os.path.dirname(metadata_filename), row.interval_data_filename)

    try:
        thermostat = get_single_thermostat(
                row.thermostat_id,
                row.zipcode,
                row.equipment_type,
                row.utc_offset,
                interval_data_filename,
                save_cache=save_cache,
                cache_path=cache_path,
        )
    except ValueError:
        # Could not locate a station for the thermostat. Warn and skip.
        warnings.warn(
            "Skipping import of thermostat (id={}) for which "
            "a sufficient source of outdoor weather data could not"
            "be located using the given ZIP code ({}). This likely "
            "due to the discrepancy between US Postal Service ZIP "
            "codes (which do not always map well to locations) and "
            "Census Bureau ZCTAs (which usually do). Please supply "
            "a zipcode which corresponds to a US Census Bureau ZCTA."
            .format(row.thermostat_id, row.zipcode))
        return

    except Exception as e:
        warnings.warn(
            "Skipping import of thermostat(id={}) because of"
            "the following error: {}"
            .format(row.thermostat_id, e))
        return

    return thermostat


def get_single_thermostat(thermostat_id, zipcode, equipment_type,
                          utc_offset, interval_data_filename, save_cache=False, cache_path=None):
    """ Load a single thermostat directly from an interval data file.

    Parameters
    ----------
    thermostat_id : str
        A unique identifier for the thermostat.
    zipcode : str
        The zipcode of the thermostat, e.g. `"01234"`.
    equipment_type : str
        The equipment type of the thermostat.
    utc_offset : str
        A string representing the UTC offset of the interval data, e.g. `"-0700"`.
        Could also be `"Z"` (UTC), or just `"+7"` (equivalent to `"+0700"`),
        or any other timezone format recognized by the library
        method dateutil.parser.parse.
    interval_data_filename : str
        The path to the CSV in which the interval data is stored.
    save_cache: boolean
        Set to True to save the cached data to a json file (based on Thermostat ID).
    cache_path: str
        Directory path to save the cached data

    Returns
    -------
    thermostat : thermostat.Thermostat
        The loaded thermostat object.
    """
    df = pd.read_csv(interval_data_filename)

    heating, cooling, aux_emerg = _get_equipment_type(equipment_type)

    # load indices
    dates = pd.to_datetime(df["date"])
    daily_index = pd.DatetimeIndex(start=dates[0], periods = dates.shape[0], freq="D")
    hourly_index = pd.DatetimeIndex(start=dates[0], periods = dates.shape[0] * 24, freq="H")
    hourly_index_utc = pd.DatetimeIndex(start=dates[0], periods = dates.shape[0] * 24, freq="H", tz=pytz.UTC)

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
    station = zipcode_to_usaf_station(zipcode)

    if station is None:
        message = "Could not locate a valid source of outdoor temperature " \
                "data for ZIP code {}".format(zipcode)
        raise ValueError(message)

    ws_hourly = ISDWeatherSource(station)
    utc_offset = normalize_utc_offset(utc_offset)
    temp_out = ws_hourly.indexed_temperatures(hourly_index_utc - utc_offset, "degF")
    temp_out.index = hourly_index

    # Export the data from the cache
    if save_cache:
        save_json_cache(hourly_index, thermostat_id, station, cache_path)

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
    thermostat = Thermostat(
        thermostat_id,
        equipment_type,
        zipcode,
        station,
        temp_in,
        temp_out,
        cooling_setpoint,
        heating_setpoint,
        cool_runtime,
        heat_runtime,
        auxiliary_heat_runtime,
        emergency_heat_runtime
    )
    return thermostat

def _get_hourly_block(df, prefix):
    columns = ["{}_{:02d}".format(prefix, i) for i in range(24)]
    values = df[columns].values
    return values.reshape((values.shape[0] * values.shape[1],))


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
    # heating, cooling, aux_emerg
    equipment_type_dict = {
        1: (True, True, True),
        2: (True, True, False),
        3: (True, True, False),
        4: (True, False, False),
        5: (False, True, False),
        }

    return(equipment_type_dict.get(equipment_type, None))
