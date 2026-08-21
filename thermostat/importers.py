from thermostat.core import Thermostat

import pandas as pd
from thermostat.stations import get_closest_station_by_zipcode, _MAX_STATION_DISTANCE_KM

from thermostat.eeweather_wrapper import get_indexed_temperatures_eeweather
from eeweather.exceptions import DataNotAvailableError
from thermostat.exceptions import (
    StationNotFoundError,
    InvalidIntervalDataError,
    InvalidUTCOffsetError,
)
from thermostat.run_summary import (
    DropOut,
    RunSummary,
    INVALID_INTERVAL_DATA,
    INVALID_UTC_OFFSET,
    STATION_NOT_FOUND,
    UNEXPECTED_ERROR,
    UNSUPPORTED_EQUIPMENT_TYPE,
    WEATHER_DATA_NOT_AVAILABLE,
)

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
        raise InvalidUTCOffsetError("Invalid UTC offset: {} ({})".format(
           utc_offset,
           e))


class ImportedThermostats(object):
    """ The thermostats a run loaded, plus the account of the ones it lost.

    Iterating over this yields Thermostat objects exactly as the plain
    iterator that :func:`from_csv` used to return did, so existing callers
    are unaffected. ``.summary`` is the addition: a
    :class:`thermostat.run_summary.RunSummary` recording how many records
    were asked for and why each missing one is missing.
    """

    def __init__(self, thermostats, summary):
        self.summary = summary
        self._iterator = iter(thermostats)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._iterator)


def from_csv(metadata_filename, verbose=False, shuffle=True, seed=None,
             quiet=None, weather_source=None):
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
    seed : int, optional
        Seed for the shuffle. Without one the order -- and therefore the
        order of rows in the output -- varies between runs on identical
        input. Pass a seed when reproducibility matters.
    weather_source : callable, optional
        Override for the outdoor temperature lookup, called as
        ``weather_source(station, index)`` and returning a pandas Series of
        degrees Fahrenheit over ``index``. Defaults to
        :func:`thermostat.eeweather_wrapper.get_indexed_temperatures_eeweather`.
        Supplying one lets a caller (notably the test suite) run without
        network access. It is dispatched to worker processes, so it must be
        picklable -- a module-level function, not a lambda or closure.

    Returns
    -------
    thermostats : ImportedThermostats
        Iterator over the imported thermostat.Thermostat objects. Its
        ``.summary`` attribute carries the run's drop-out accounting; see
        :mod:`thermostat.run_summary`.
    """

    if quiet:
        logger.warning(
            'quiet argument has been deprecated. Please remove this flag from your code.')

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
        logger.info("Randomizing thermostat order.")
        metadata = metadata.sample(frac=1, random_state=seed).reset_index(drop=True)

    p = Pool(AVAILABLE_PROCESSES)
    multiprocess_func_partial = partial(
            multiprocess_func,
            metadata_filename=metadata_filename,
            verbose=verbose,
            weather_source=weather_source)
    result_list = p.imap(multiprocess_func_partial, metadata.iterrows())
    p.close()
    p.join()

    # A record that could not be imported comes back as a DropOut naming the
    # reason, rather than as a bare None that says only "something happened".
    results = []
    summary = RunSummary(requested=len(metadata))
    for item in result_list:
        if isinstance(item, DropOut):
            summary.extend([item])
        else:
            results.append(item)

    if summary.dropped:
        logger.warning(
            "Unable to load %d of %d thermostat records:\n%s",
            summary.dropped, summary.requested, summary.describe())
        for drop_out in summary.drop_outs:
            logger.warning("  %s (%s): %s -- %s", drop_out.thermostat_id,
                           drop_out.zipcode, drop_out.reason, drop_out.detail)

    return ImportedThermostats(results, summary)


def multiprocess_func(metadata, metadata_filename, verbose=False,
                      weather_source=None):
    """ This function is a partial function for multiproccessing and shares the same arguments as from_csv.
    It is not intended to be called directly.

    Returns either a Thermostat or, when the record cannot be imported, a
    thermostat.run_summary.DropOut naming the reason."""
    i, row = metadata
    logger.info("Importing thermostat {}".format(row.thermostat_id))
    if verbose and logger.getEffectiveLevel() > logging.INFO:
        print("Importing thermostat {}".format(row.thermostat_id))

    def dropped(reason, detail):
        warnings.warn("Skipping import of thermostat (id={}): {}".format(
            row.thermostat_id, detail))
        return DropOut(
            thermostat_id=row.thermostat_id, zipcode=row.zipcode,
            station=None, stage="import", reason=reason, detail=detail)

    # make sure this thermostat type is supported.
    if row.equipment_type not in [1, 2, 3, 4, 5]:
        return dropped(
            UNSUPPORTED_EQUIPMENT_TYPE,
            "it controls equipment of unsupported type {}".format(
                row.equipment_type))

    interval_data_filename = os.path.join(os.path.dirname(metadata_filename), row.interval_data_filename)

    try:
        thermostat = get_single_thermostat(
                row.thermostat_id,
                row.zipcode,
                row.equipment_type,
                row.utc_offset,
                interval_data_filename,
                weather_source=weather_source,
        )
    except StationNotFoundError:
        return dropped(
            STATION_NOT_FOUND,
            "a sufficient source of outdoor weather data could not be "
            "located using the given ZIP code ({}). This is likely due to "
            "the discrepancy between US Postal Service ZIP codes (which do "
            "not always map well to locations) and Census Bureau ZCTAs "
            "(which usually do). Please supply a zipcode which corresponds "
            "to a US Census Bureau ZCTA.".format(row.zipcode))

    except DataNotAvailableError as e:
        return dropped(
            WEATHER_DATA_NOT_AVAILABLE,
            "NCEI does not have data: {}".format(e))

    except InvalidUTCOffsetError as e:
        return dropped(
            INVALID_UTC_OFFSET,
            "its UTC offset could not be read: {}".format(e))

    except (InvalidIntervalDataError, ValueError) as e:
        return dropped(
            INVALID_INTERVAL_DATA,
            "its interval data could not be read: {}".format(e))

    except Exception as e:
        # Last resort. Log the traceback rather than only the message: this
        # handler turns any bug -- a typo, a schema mistake -- into a silently
        # missing output row, so the detail has to go somewhere.
        logger.exception(
            "Unexpected error importing thermostat %s", row.thermostat_id)
        return dropped(
            UNEXPECTED_ERROR, "{}: {}".format(type(e).__name__, e))

    return thermostat


def get_single_thermostat(thermostat_id, zipcode, equipment_type,
                          utc_offset, interval_data_filename,
                          weather_source=None):
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
    weather_source : callable, optional
        Override for the outdoor temperature lookup; see :func:`from_csv`.

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
        raise InvalidIntervalDataError(message)

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
        raise StationNotFoundError(message)

    utc_offset = normalize_utc_offset(utc_offset)
    fetch_temperatures = weather_source or get_indexed_temperatures_eeweather
    temp_out = fetch_temperatures(station, hourly_index_utc - utc_offset)
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
