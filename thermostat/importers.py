from thermostat.core import Thermostat

import pandas as pd
from thermostat.stations import get_closest_station_by_zipcode, _MAX_STATION_DISTANCE_KM

from thermostat.eeweather_wrapper import get_indexed_temperatures_eeweather
from eeweather.exceptions import DataNotAvailableError

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
# Cap on concurrent weather fetches. eeweather retrieves over HTTPS from
# NOAA's GHCNh API (and caches locally), so this is a politeness limit on
# simultaneous requests to NOAA, not the old FTP-connection cap. Tune down if
# NOAA rate-limits large runs.
MAX_WEATHER_CONNECTIONS = 8
AVAILABLE_PROCESSES = min(NUMBER_OF_CORES, MAX_WEATHER_CONNECTIONS)


logger = logging.getLogger(__name__)


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


def from_csv(metadata_filename, verbose=False, shuffle=True, quiet=None):
    """
    Creates Thermostat objects from data stored in CSV files.

    Parameters
    ----------
    metadata_filename : str
        Path to a file containing the thermostat metadata.
    verbose : boolean
        Set to True to output a more detailed log of import activity.
    shuffle: boolean
        Shuffle the thermostats into a random order.

    Returns
    -------
    thermostats : iterator over thermostat.Thermostat objects
        Thermostats imported from the given CSV input files.
    """

    if quiet:
        logging.warning('quiet argument has been deprecated. Please remove this flag from your code.')

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

    if shuffle:
        logging.info("Randomizing thermostat order.")
        metadata = metadata.sample(frac=1).reset_index(drop=True)

    p = Pool(AVAILABLE_PROCESSES)
    multiprocess_func_partial = partial(
            multiprocess_func,
            metadata_filename=metadata_filename,
            verbose=verbose)
    result_list = p.imap(multiprocess_func_partial, metadata.iterrows())
    p.close()
    p.join()

    # Bad thermostats return None so remove those.
    results = [x for x in result_list if x is not None]

    # Check for thermostats that were not loaded and log them
    metadata_thermostat_ids = set(metadata.thermostat_id)
    loaded_thermostat_ids = set([x.thermostat_id for x in results])
    missing_thermostats = metadata_thermostat_ids.difference(loaded_thermostat_ids)
    missing_thermostats_num = len(missing_thermostats)
    if missing_thermostats_num > 0:
        logging.warning("Unable to load {} thermostat records because of "
                        "errors. Please check the logs for the following thermostats:".format(
                            missing_thermostats_num))
        for thermostat in missing_thermostats:
            logging.warning(thermostat)

    # Convert this to an iterator to maintain compatibility
    return iter(results)


def multiprocess_func(metadata, metadata_filename, verbose=False):
    """ This function is a partial function for multiproccessing and shares the same arguments as from_csv.
    It is not intended to be called directly."""
    i, row = metadata
    logger.info("Importing thermostat {}".format(row.thermostat_id))
    if verbose and logger.getEffectiveLevel() > logging.INFO:
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
        )
    except ValueError as e:
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

    except DataNotAvailableError as e:
        warnings.warn(
            "Skipping import of thermostat (id={}) because NCEI "
            "does not have data: {}"
            .format(row.thermostat_id, e))
        return

    except Exception as e:
        warnings.warn(
            "Skipping import of thermostat(id={}) because of "
            "the following error: {}"
            .format(row.thermostat_id, e))
        return

    return thermostat


def get_single_thermostat(thermostat_id, zipcode, equipment_type,
                          utc_offset, interval_data_filename):
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

    Returns
    -------
    thermostat : thermostat.Thermostat
        The loaded thermostat object.
    """
    df = pd.read_csv(interval_data_filename)

    heating, cooling, aux_emerg = _get_equipment_type(equipment_type)

    # load indices
    dates = pd.to_datetime(df["date"])
    daily_index = pd.date_range(start=dates[0], periods=dates.shape[0], freq="D")
    hourly_index = pd.date_range(start=dates[0], periods=dates.shape[0] * 24, freq="h")
    hourly_index_utc = pd.date_range(start=dates[0], periods=dates.shape[0] * 24, freq="h", tz=pytz.UTC)

    # raise an error if dates are not aligned
    if not all(dates == daily_index):
        message = ("Dates provided for thermostat_id={} may contain some "
                   "which are out of order, missing, or duplicated.".format(thermostat_id))
        raise RuntimeError(message)

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

    # load outdoor temperatures — select a station that has data for the years
    # this thermostat's interval data actually spans, so a historical run
    # (e.g. 2016) picks a station on that year's data rather than requiring the
    # current calendar year.
    data_years = sorted(set(hourly_index.year))
    station = get_closest_station_by_zipcode(zipcode, required_years=data_years)

    if station is None:
        message = "No weather station with sufficient recent data within " \
                "{} km of ZIP code {}".format(_MAX_STATION_DISTANCE_KM, zipcode)
        raise RuntimeError(message)

    utc_offset = normalize_utc_offset(utc_offset)
    temp_out = get_indexed_temperatures_eeweather(station, hourly_index_utc - utc_offset)
    temp_out.index = hourly_index

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
