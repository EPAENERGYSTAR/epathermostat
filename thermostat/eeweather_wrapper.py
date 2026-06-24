from datetime import datetime
import logging
import eeweather

import pandas as pd
import pytz

from thermostat import weather_fallback

# First date for which the NOAA global-hourly API stopped returning data.
# Any request whose end date falls on or after this date routes directly to
# GHCN-H for the affected portion rather than waiting for a NaN-detection pass.
NOAA_OUTAGE_DATE = pd.Timestamp("2025-08-30", tz="UTC")

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


def _fill_gaps_with_ghcnh(tempC, usaf_id, start, end):
    """Fill NaN values in tempC using NOAA GHCN-H data for the same station.

    Only NaN positions are overwritten; valid cached data is preserved.
    Returns tempC unchanged if the station has no WBAN ID or the fallback
    returns no data.
    """
    try:
        metadata = eeweather.get_isd_station_metadata(usaf_id)
        wban_id = metadata.get("recent_wban_id")
    except Exception:
        return tempC

    if not wban_id:
        return tempC

    nan_count = int(tempC.isna().sum())
    fallback = weather_fallback.fetch_ghcnh_hourly_temp_data(wban_id, start, end)

    if fallback.empty:
        return tempC

    filled = tempC.fillna(fallback.reindex(tempC.index))
    filled_count = nan_count - int(filled.isna().sum())
    logger.warning(
        "Station %s: NOAA global-hourly data unavailable for %s to %s; "
        "filled %d of %d missing hours from NOAA GHCN-H.",
        usaf_id, start.date(), end.date(), filled_count, nan_count,
    )
    return filled


def get_indexed_temperatures_eeweather(usaf_id, index):
    """ Helper routine to return average temperatures over the given index in Fahrenheit

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
    start = pd.to_datetime(datetime(years[0], 1, 1), utc=True)
    end = pd.to_datetime(datetime(years[-1], 12, 31, 23, 59), utc=True)
    tempC, warnings = eeweather.load_isd_hourly_temp_data(usaf_id, start, end)
    # Route to GHCN-H without waiting for NaN detection when the request
    # overlaps the known NOAA outage period, or as a general NaN fallback.
    if end >= NOAA_OUTAGE_DATE or tempC.isna().any():
        tempC = _fill_gaps_with_ghcnh(tempC, usaf_id, start, end)
    tempC = tempC.resample('h').mean()[index]
    tempF = _convert_to_farenheit(tempC)
    return tempF
