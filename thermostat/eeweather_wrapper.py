from datetime import datetime
import eeweather

import pandas as pd

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
    tempC = tempC.resample('H').mean()[index]
    tempF = _convert_to_farenheit(tempC)
    return tempF
