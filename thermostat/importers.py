import csv
from thermostat.core import Thermostat
from thermostat.equipment_type import (
        has_heating,
        has_cooling,
        has_auxiliary,
        has_emergency,
        has_two_stage_cooling,
        has_two_stage_heating,
        has_multi_stage_cooling,
        has_multi_stage_heating,
        first_stage_capacity_ratio,
        )

import pandas as pd
from thermostat.zipcode_lookup import ZIPCODE_LOOKUP

from thermostat.eeweather_wrapper import get_indexed_temperatures_eeweather
from eeweather.cache import KeyValueStore
from eeweather.exceptions import ISDDataNotAvailableError
import json

import warnings
import dateutil.parser
import os
import pytz
from multiprocessing import Pool, cpu_count
from functools import partial
import logging

try:
    NUMBER_OF_CORES = len(os.sched_getaffinity(0))
except AttributeError:
    NUMBER_OF_CORES = cpu_count()
MAX_FTP_CONNECTIONS = 3
AVAILABLE_PROCESSES = min(NUMBER_OF_CORES, MAX_FTP_CONNECTIONS)


logger = logging.getLogger(__name__)
warnings.simplefilter('module', Warning)

INTERVAL_COLUMNS = {
    'datetime',
    'cool_runtime_stg1',
    'cool_runtime_stg2',
    'cool_runtime_equiv',
    'heat_runtime_stg1',
    'heat_runtime_stg2',
    'heat_runtime_equiv',
    'emergency_heat_runtime',
    'auxiliary_heat_runtime',
    'temp_in',
    }


METADATA_COLUMNS = {
    'thermostat_id',
    'heat_type',
    'heat_stage',
    'cool_type',
    'cool_stage',
    'zipcode',
    'utc_offset',
    'interval_data_filename'
    }


class ZIPCodeError(Exception):
    pass


def _prime_eeweather_cache():
    """ Primes the eemeter / eeweather caches by doing a non-existent query
    This creates the cache directories sooner than if they were created
    during normal processing (which can lead to a race condition and missing
    thermostats)
    """
    sql_json = KeyValueStore()
    if sql_json.key_exists('0') is not False:
        raise Exception("eeweather cache was not properly primed. Aborting.")


def save_json_cache(index, thermostat_id, station, cache_path=None):
    """ Saves the cached results from eeweather into a JSON file.

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

    json_cache = {}

    sqlite_json_store = KeyValueStore()
    years = index.groupby(index.year).keys()
    for year in years:
        filename = "ISD-{station}-{year}.json".format(
                station=station,
                year=year)
        json_cache[filename] = sqlite_json_store.retrieve_json(filename)

    if cache_path is None:
        directory = os.path.join(
            os.curdir,
            "epathermostat_weather_data")
    else:
        directory = os.path.normpath(
            cache_path)

    thermostat_filename = "{thermostat_id}.json".format(thermostat_id=thermostat_id)
    thermostat_path = os.path.join(directory, thermostat_filename)
    try:
        os.makedirs(os.path.dirname(directory), exist_ok=True)
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

        if isinstance(utc_offset, int):
            symbol = ""
            if utc_offset >= 0:
                symbol = "+"
            utc_offset = symbol + str(utc_offset)

        if utc_offset == '0':
            utc_offset = '+0'

        delta = dateutil.parser.parse(
            "2000-01-01T00:00:00" + str(utc_offset)).tzinfo.utcoffset(None)
        return delta

    except (ValueError, TypeError, AttributeError) as e:
        raise TypeError("Invalid UTC offset: can't convert {} to a valid offset. Please prefix with + or -. ({})".format(
           utc_offset,
           e))


def from_csv(metadata_filename, verbose=False, save_cache=False, shuffle=True,
             cache_path=None, log_error=True, log_error_filename='thermostat_import_errors.csv'):
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
    shuffle: boolean
        Shuffles the thermostats to give them random ordering if desired (helps with caching).
    cache_path: str
        Directory path to save the cached data.
    log_error: boolean
        Create a log file of thermostats that weren't imported and the reason they weren't imported.
    log_error_filename: boolean
        Name of the file to use for logging the thermostats that weren't imported.

    Returns
    -------
    thermostats : iterator over thermostat.Thermostat objects
        Thermostats imported from the given CSV input files.
    """

    _prime_eeweather_cache()

    metadata = pd.read_csv(
        metadata_filename,
        dtype={
            "thermostat_id": str,
            "heat_type": str,
            "heat_stage": str,
            "cool_type": str,
            "cool_stage": str,
            "zipcode": str,
            "utc_offset": str,
            "interval_data_filename": str
        }
    )
    metadata.fillna('', inplace=True)
    metadata.columns = map(str.lower, metadata.columns)
    if not METADATA_COLUMNS.issubset(metadata.columns):
        missing_columns = list(METADATA_COLUMNS.difference(metadata.columns))
        message = "Columns missing from metadata data file: {}".format(missing_columns)
        raise ValueError(message)


    # Shuffle the results to help alleviate cache issues
    if shuffle:
        logging.info("Metadata randomized to prevent collisions in cache.")
        metadata = metadata.sample(frac=1).reset_index(drop=True)

    p = Pool(AVAILABLE_PROCESSES)
    multiprocess_func_partial = partial(
            _multiprocess_func,
            metadata_filename=metadata_filename,
            verbose=verbose,
            save_cache=save_cache,
            cache_path=cache_path)
    result_list = p.imap(multiprocess_func_partial, metadata.iterrows())
    p.close()
    p.join()

    results = []
    error_list = []

    for result in result_list:
        if result['thermostat'] is None:
            for error in result['errors']:
                logging.warning(result['thermostat_id'] + ': ' + error)
                error_dict = {}
                error_dict['thermostat_id'] = result['thermostat_id']
                error_dict['error'] = error
            error_list.append(error_dict)
        else:
            results.append(result['thermostat'])

    if log_error and error_list:
        fieldnames = ['thermostat_id', 'error']
        with open(log_error_filename, 'w') as error_file:
            writer = csv.DictWriter(error_file, fieldnames=fieldnames, dialect='excel')
            writer.writeheader()
            for thermostat_error in error_list:
                writer.writerow(thermostat_error)

    # Convert this to an iterator to maintain compatibility
    return iter(results)


def _multiprocess_func(metadata, metadata_filename, verbose=False, save_cache=False, cache_path=None):
    """ This function is a partial function for multiproccessing and shares the same arguments as from_csv.
    It is not intended to be called directly."""
    i, row = metadata
    logger.info("Importing thermostat {}".format(row.thermostat_id))
    if verbose and logger.getEffectiveLevel() > logging.INFO:
        print("Importing thermostat {}".format(row.thermostat_id))

    interval_data_filename = os.path.join(os.path.dirname(metadata_filename), row.interval_data_filename)

    status_metadata = {
        'thermostat_id': row.thermostat_id,
        'errors': [],
        'thermostat': None,
    }
    errors = []
    thermostat = None

    zipcode = row.zipcode.zfill(5)  # Ensure that we have 5 characters, and if not left-pad it with zeroes.

    try:
        thermostat = get_single_thermostat(
            thermostat_id=row.thermostat_id,
            zipcode=zipcode,
            heat_type=row.heat_type,
            heat_stage=row.heat_stage,
            cool_type=row.cool_type,
            cool_stage=row.cool_stage,
            utc_offset=row.utc_offset,
            interval_data_filename=interval_data_filename,
            save_cache=save_cache,
            cache_path=cache_path,
        )
    except ZIPCodeError as e:
        # Could not locate a station for the thermostat. Warn and skip.
        errors.append(
            "Skipping import of thermostat because "
            "a sufficient source of outdoor weather data could not"
            f"be located using the given ZIP code ({row.zipcode})."
            f"\nError Message: {e}"
            )

    except ISDDataNotAvailableError as e:
        errors.append(
            "Skipping import of thermostat because the NCDC "
            f"does not have data: {e}"
            )

    except Exception as e:
        errors.append(
            f"Skipping import of thermostat because of "
            f"the following error: {e}")

    status_metadata['errors'] = errors
    status_metadata['thermostat'] = thermostat
    return status_metadata


def get_single_thermostat(thermostat_id, zipcode,
                          heat_type, heat_stage, cool_type, cool_stage,
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
    # load outdoor temperatures
    station = ZIPCODE_LOOKUP[zipcode]['station']

    if station is None:
        message = "Could not locate a valid source of outdoor temperature " \
                "data for ZIP code {}".format(zipcode)
        raise ZIPCodeError(message)

    df = pd.read_csv(interval_data_filename)

    df.columns = map(str.lower, df.columns)
    if not INTERVAL_COLUMNS.issubset(df.columns):
        missing_columns = list(INTERVAL_COLUMNS.difference(df.columns))
        message = "Columns missing from interval data file: {}".format(missing_columns)
        raise ValueError(message)

    # load indices
    date_time = pd.to_datetime(df["datetime"])
    df['datetime'] = date_time
    # daily_index = pd.date_range(start=date_time[0], periods=date_time.shape[0] / 24, freq="D")
    hourly_index = pd.date_range(start=date_time[0], periods=date_time.shape[0], freq="H")
    hourly_index_utc = pd.date_range(start=date_time[0], periods=date_time.shape[0], freq="H", tz=pytz.UTC)

    # raise an error if dates are not aligned
    if not all(date_time == hourly_index):
        missing_hours = set(hourly_index).difference(set(date_time))
        duplicates = list(date_time[date_time.duplicated()])
        message = ("Dates provided for thermostat_id={} may contain some "
                   "which are out of order, missing, or duplicated.".format(thermostat_id))
        if len(duplicates) > 0:
            message += " (Possible duplicated hours: {})".format(duplicates)
        elif len(missing_hours) > 0:
            message += " (Possible missing hours: {})".format(missing_hours)
        raise RuntimeError(message)

    # Export the data from the cache
    if save_cache:
        save_json_cache(hourly_index, thermostat_id, station, cache_path)

    # load hourly time series values
    temp_in = _create_series(df.temp_in, hourly_index)

    utc_offset = normalize_utc_offset(utc_offset)
    temp_out = get_indexed_temperatures_eeweather(station, hourly_index_utc - utc_offset)
    temp_out.index = hourly_index

    # load daily time series values
    auxiliary_heat_runtime, emergency_heat_runtime = _calculate_aux_emerg_runtime(df, thermostat_id, heat_type, heat_stage, hourly_index)
    cool_runtime = _calculate_cool_runtime(df, thermostat_id, cool_type, cool_stage, hourly_index)
    heat_runtime = _calculate_heat_runtime(df, thermostat_id, heat_type, heat_stage, hourly_index)

    # Give the thermostats the benefit of the doubt (especially if the runtime is None)
    enough_cool_runtime = True
    enough_heat_runtime = True

    # Currently checks hourly runtime, not daily
    if cool_runtime is not None:
        enough_cool_runtime = _enough_runtime(cool_runtime)
    if heat_runtime is not None:
        enough_heat_runtime = _enough_runtime(heat_runtime)

    if not(enough_cool_runtime and enough_heat_runtime):
        message = "Not enough runtime for thermostat "
        if not enough_heat_runtime:
            message += "(Heat runtime has over 5% missing data) "
        if not enough_cool_runtime:
            message += "(Cool runtime has over 5% missing data) "
        raise ValueError(message)

    # create thermostat instance
    thermostat = Thermostat(
        thermostat_id,
        heat_type,
        heat_stage,
        cool_type,
        cool_stage,
        zipcode,
        station,
        temp_in,
        temp_out,
        cool_runtime,
        heat_runtime,
        auxiliary_heat_runtime,
        emergency_heat_runtime
    )
    return thermostat


def _calculate_cool_runtime(df, thermostat_id, cool_type, cool_stage, hourly_index):
    if has_cooling(cool_type):
        if df.cool_runtime_stg1.gt(60).any() or \
                df.cool_runtime_stg2.gt(60).any() or \
                df.cool_runtime_equiv.gt(60).any():
            warnings.warn("For thermostat {}, cooling runtime data was larger than 60 minutes"
                          " for one or more hours, which is impossible. Please check the data file."
                          .format(thermostat_id))
            return

        if has_multi_stage_cooling(cool_stage):
            warnings.warn("Multi-stage cooling isn't supported (yet)")
            return

        if has_two_stage_cooling(cool_stage):
            # Use cool equivalent runtime if it exists, otherwise calculate it
            if df.cool_runtime_equiv.max() > 0.0:
                cool_runtime = _create_series(df.cool_runtime_equiv, hourly_index)
            else:
                cool_runtime_both_stg = (first_stage_capacity_ratio(cool_type) * (df.cool_runtime_stg1 - df.cool_runtime_stg2)) + df.cool_runtime_stg2
                cool_runtime = _create_series(cool_runtime_both_stg, hourly_index)
        else:
            cool_runtime = _create_series(df.cool_runtime_stg1, hourly_index)
    else:
        cool_runtime = None
    return cool_runtime


def _calculate_heat_runtime(df, thermostat_id, heat_type, heat_stage, hourly_index):
    if has_heating(heat_type):
        if df.heat_runtime_stg1.gt(60).any() or \
                df.heat_runtime_stg2.gt(60).any() or \
                df.heat_runtime_equiv.gt(60).any():
            warnings.warn("For thermostat {}, heating runtime data was larger than 60 minutes"
                          " for one or more hours, which is impossible. Please check the data file."
                          .format(thermostat_id))
            return

        if has_multi_stage_heating(heat_stage):
            warnings.warn("Multi-stage heating isn't supported (yet)")
            return

        if has_two_stage_heating(heat_stage):
            # Use heat equivalent runtime if it exists, otherwise calculate it
            if df.heat_runtime_equiv.max() > 0.0:
                heat_runtime = _create_series(df.heat_runtime_equiv, hourly_index)
            else:
                heat_runtime_both_stg = (first_stage_capacity_ratio(heat_type) * (df.heat_runtime_stg1 - df.heat_runtime_stg2)) + df.heat_runtime_stg2
                heat_runtime = _create_series(heat_runtime_both_stg, hourly_index)
        else:
            heat_runtime = _create_series(df.heat_runtime_stg1, hourly_index)
    else:
        heat_runtime = None
    return heat_runtime


def _calculate_aux_emerg_runtime(df, thermostat_id, heat_type, heat_stage, hourly_index):
    if has_auxiliary(heat_type) and has_emergency(heat_type):
        auxiliary_heat_runtime = _create_series(df.auxiliary_heat_runtime, hourly_index)
        emergency_heat_runtime = _create_series(df.emergency_heat_runtime, hourly_index)
        if auxiliary_heat_runtime.gt(60).any():
            warnings.warn("For thermostat {}, auxiliary runtime data was larger than 60 minutes"
                          " for one or more hours, which is impossible. Please check the data file."
                          .format(thermostat_id))
            return
        if emergency_heat_runtime.gt(60).any():
            warnings.warn("For thermostat {}, emergency runtime data was larger than 60 minutes"
                          " for one or more hours, which is impossible. Please check the data file."
                          .format(thermostat_id))
            return
    else:
        auxiliary_heat_runtime = None
        emergency_heat_runtime = None
    return auxiliary_heat_runtime, emergency_heat_runtime


def _create_series(df, index):
    series = df
    series.index = index
    return series


def _enough_runtime(series):
    if series is None:
        return False

    num_elements = len(series)
    num_dropped_elements = len(series.dropna())
    return (num_dropped_elements / num_elements) > 0.95
