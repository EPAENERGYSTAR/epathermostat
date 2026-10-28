from datetime import datetime, timezone
import logging
import threading

import pandas as pd

from eeweather import WeatherStation

# This routine is a compact and distilled version of code that was originally
# released as eeweather_wrapper.py
# https://github.com/openeemeter/eemeter/blob/345afcb40ce5786bfbd117cb51536d7ca807a32c/eemeter/weather/eeweather_wrapper.py
#
# Copyright 2017 Open Energy Efficiency
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

logger = logging.getLogger(__name__)


# Wall-clock seconds one station's outdoor-temperature fetch may take before
# it is abandoned. eeweather retries each station-year three times at a 120
# second socket timeout and caps nothing in total, so against an unresponsive
# NOAA a four-year fetch can hold an unattended fleet run for ~25 minutes per
# station.
WEATHER_FETCH_DEADLINE_SECONDS = 600


class WeatherFetchTimeout(Exception):
    """A station's weather fetch outlived WEATHER_FETCH_DEADLINE_SECONDS."""


def _load_within_deadline(station, start, end, usaf_id):
    """``station.load_data`` for hourly temperature, abandoned at the deadline.

    eeweather has no deadline of its own, so the load runs on a daemon thread
    that is waited on for at most the deadline. A thread cannot be cancelled:
    an abandoned load keeps retrying in the background until eeweather gives
    up, but nothing waits on it, and as a daemon it never holds up exit.
    """
    outcome = {}

    def load():
        try:
            outcome["result"] = station.load_data(
                start, end, frequency="h", variables=("temperature",))
        except BaseException as error:  # re-raised on the calling thread
            outcome["error"] = error

    worker = threading.Thread(
        target=load, name="eeweather-{}".format(usaf_id), daemon=True)
    worker.start()
    worker.join(WEATHER_FETCH_DEADLINE_SECONDS)
    if worker.is_alive():
        raise WeatherFetchTimeout(
            "weather fetch for station {} exceeded {}s".format(
                usaf_id, WEATHER_FETCH_DEADLINE_SECONDS))
    if "error" in outcome:
        raise outcome["error"]

    return outcome["result"]


def _convert_to_farenheit(x):
    """ Converts Celsius to Fahrenheit
    Parameters
    ----------
    x : float
        Temperature in Celsius

    Returns
    -------
    float
    """
    return 1.8 * x + 32


def get_indexed_temperatures_eeweather(usaf_id, index):
    """ Helper routine to return average temperatures over the given index in Fahrenheit

    Temperatures come from a single NOAA source: the station's GHCNh
    observations, fetched by eeweather (default ``sources=("ghcnh",)``) from
    NOAA's GHCNh access API. There is no cache priming, expiry workaround, or
    second-source gap fill; hours the station did not report are returned as
    NaN. eeweather's data-coverage warnings are logged rather than discarded.

    Parameters
    ----------
    usaf_id : string
        USAF ID of the station to look up
    index : pandas.DatetimeIndex
        Index over which to supply average temperatures.

    Returns
    -------
    temperatures : pandas.Series with DatetimeIndex
        Average temperatures over series indexed by :code:`index`.

    Raises
    ------
    WeatherFetchTimeout
        If the fetch outlives :data:`WEATHER_FETCH_DEADLINE_SECONDS`.
    """
    if index.shape == (0,):
        return pd.Series([], index=index, dtype=float)

    years = sorted(index.groupby(index.year).keys())
    start = datetime(years[0], 1, 1, tzinfo=timezone.utc)
    end = datetime(years[-1], 12, 31, 23, 59, tzinfo=timezone.utc)

    station = WeatherStation.from_usaf(usaf_id)
    df, warnings = _load_within_deadline(station, start, end, usaf_id)
    for warning in warnings:
        logger.warning(
            "eeweather %s for station %s: %s",
            warning.qualified_name, usaf_id, warning.description,
        )

    tempC = df["temperature"].reindex(index)
    return _convert_to_farenheit(tempC)
