from datetime import datetime, timezone
import logging

import pandas as pd

from eeweather import WeatherStation
from eeweather.sources.vocabulary import imputed_fraction_name

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


# Wall-clock seconds one station's outdoor-temperature fetch may spend on the
# network before eeweather raises FetchDeadlineExceeded. Bounds an unattended
# fleet run against an unresponsive NOAA, which otherwise retries indefinitely.
WEATHER_FETCH_DEADLINE_SECONDS = 600

# Above this fraction of fabricated (gap-interpolated) hours, the outdoor
# series is thin enough to warn about even though it passed station selection.
_HIGH_IMPUTED_FRACTION = 0.10


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
    """
    if index.shape == (0,):
        return pd.Series([], index=index, dtype=float)

    years = sorted(index.groupby(index.year).keys())
    start = datetime(years[0], 1, 1, tzinfo=timezone.utc)
    end = datetime(years[-1], 12, 31, 23, 59, tzinfo=timezone.utc)

    station = WeatherStation.from_usaf(usaf_id)
    df, warnings = station.load_data(
        start, end, frequency="h", variables=("temperature",),
        imputation=True, deadline=WEATHER_FETCH_DEADLINE_SECONDS,
    )
    for warning in warnings:
        logger.warning(
            "eeweather %s for station %s: %s",
            warning.qualified_name, usaf_id, warning.description,
        )

    # eeweather now labels which hours were fabricated by gap interpolation
    # rather than observed. The interpolated values are still used (the Method
    # interpolates gaps up to two hours), but a station leaning heavily on
    # interpolation is worth flagging even when it cleared station selection.
    fraction = df[imputed_fraction_name("temperature")]
    fabricated = float((fraction == 1.0).mean())
    if fabricated > _HIGH_IMPUTED_FRACTION:
        logger.warning(
            "Station %s: %.0f%% of outdoor hours %d-%d were gap-interpolated,"
            " not observed.", usaf_id, 100 * fabricated, start.year, end.year)

    tempC = df["temperature"].reindex(index)
    return _convert_to_farenheit(tempC)
