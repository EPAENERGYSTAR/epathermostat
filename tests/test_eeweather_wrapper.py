"""Tests for thermostat/eeweather_wrapper.py — the single-source (static GHCNh)
temperature fetch against the reshaped eeweather WeatherStation API."""
import numpy as np
import pandas as pd
import pytz
from unittest.mock import patch, MagicMock

from thermostat.eeweather_wrapper import (
    get_indexed_temperatures_eeweather,
    _convert_to_farenheit,
)


def _idx(start, periods):
    return pd.date_range(start, periods=periods, freq="h", tz=pytz.UTC)


def _station_returning(tempC):
    """A mock WeatherStation whose load_data returns tempC as the temperature."""
    station = MagicMock()
    station.load_data.return_value = (pd.DataFrame({"temperature": tempC}), [])
    return station


def test_empty_index_returns_empty_series():
    result = get_indexed_temperatures_eeweather("722880", _idx("2024-01-01", 0))
    assert result.empty


def test_returns_fahrenheit_over_index_from_single_ghcnh_source():
    tempC = pd.Series(np.linspace(0.0, 20.0, 8760), index=_idx("2024-01-01", 8760))
    index = _idx("2024-06-01", 24)

    with patch("thermostat.eeweather_wrapper.WeatherStation") as WS:
        WS.from_usaf.return_value = _station_returning(tempC)
        result = get_indexed_temperatures_eeweather("722880", index)

    WS.from_usaf.assert_called_once_with("722880")
    # one NOAA source (WeatherStation defaults to ghcnh), hourly temperature only
    _args, kwargs = WS.from_usaf.return_value.load_data.call_args
    assert kwargs["variables"] == ("temperature",)
    assert kwargs["frequency"] == "h"
    assert result.index.equals(index)
    pd.testing.assert_series_equal(
        result, _convert_to_farenheit(tempC.reindex(index)), check_names=False
    )


def test_missing_hours_stay_nan_no_fallback():
    values = np.linspace(0.0, 20.0, 8760)
    values[100:200] = np.nan  # a gap the old code would have filled from a 2nd source
    tempC = pd.Series(values, index=_idx("2024-01-01", 8760))
    index = _idx("2024-01-05", 24)  # overlaps the gap

    with patch("thermostat.eeweather_wrapper.WeatherStation") as WS:
        WS.from_usaf.return_value = _station_returning(tempC)
        result = get_indexed_temperatures_eeweather("722880", index)

    # single source: gaps are left as NaN rather than fallback-filled
    assert result.isna().any()


def test_hours_absent_from_source_reindex_to_nan():
    tempC = pd.Series(np.linspace(0, 5, 48), index=_idx("2024-01-01", 48))
    index = _idx("2024-01-01", 72)  # 24 h past what the source returned

    with patch("thermostat.eeweather_wrapper.WeatherStation") as WS:
        WS.from_usaf.return_value = _station_returning(tempC)
        result = get_indexed_temperatures_eeweather("722880", index)

    assert result.iloc[:48].notna().all()
    assert result.iloc[48:].isna().all()
