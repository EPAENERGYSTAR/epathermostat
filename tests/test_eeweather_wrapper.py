import pytest
import pandas as pd
from thermostat.eeweather_wrapper import get_indexed_temperatures_eeweather
from .fixtures.single_stage import thermostat_type_1


def test_get_indexed_temperatures_eeweather_empty_index():
    empty_index = pd.DataFrame([])
    results = get_indexed_temperatures_eeweather('720648', empty_index)
    assert results.empty is True


def test_get_index_temperatures_eeweather():
    begin_timestamp = pd.Timestamp('2011-01-01 00:00:00')
    periods = 8766
    hourly_index = pd.date_range(begin_timestamp, periods=periods, freq='H', tz='UTC')
    results = get_indexed_temperatures_eeweather('720648', hourly_index)
    assert results.shape == (8766,)
