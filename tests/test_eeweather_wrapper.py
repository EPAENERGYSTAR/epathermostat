import pytest
import numpy as np
import pandas as pd
import pytz
from unittest.mock import patch, MagicMock

from thermostat.eeweather_wrapper import get_indexed_temperatures_eeweather, NOAA_OUTAGE_DATE


def _utc_hourly_index(start, periods):
    return pd.date_range(start, periods=periods, freq="h", tz=pytz.UTC)


def _full_tempC(start="2025-01-01", periods=8760):
    """A complete year of hourly Celsius data with no NaN."""
    idx = _utc_hourly_index(start, periods)
    return pd.Series(np.linspace(0.0, 20.0, periods), index=idx), []


def _partial_tempC(nan_start_idx=8000, periods=8760):
    """A year of data where the tail is NaN (simulates NOAA outage)."""
    idx = _utc_hourly_index("2025-01-01", periods)
    values = np.linspace(0.0, 20.0, periods)
    values[nan_start_idx:] = np.nan
    return pd.Series(values, index=idx), []


def _ghcnh_fill(index):
    """Synthetic GHCN-H fallback: constant 15.0 °C for every hour in index."""
    return pd.Series(15.0, index=index, dtype=float)


# ---------------------------------------------------------------------------
# Test: fallback NOT called when eeweather data is complete
# ---------------------------------------------------------------------------

def test_no_fallback_when_pre_outage_data_complete():
    """Requests entirely before NOAA_OUTAGE_DATE with no NaN never call GHCN-H."""
    full_ts, warns = _full_tempC("2024-01-01", periods=8760)
    index = _utc_hourly_index("2024-06-01", periods=24)

    with patch("thermostat.eeweather_wrapper.eeweather.load_isd_hourly_temp_data",
               return_value=(full_ts, warns)), \
         patch("thermostat.eeweather_wrapper.weather_fallback.fetch_ghcnh_hourly_temp_data") as mock_ghcnh:

        result = get_indexed_temperatures_eeweather("722880", index)

    mock_ghcnh.assert_not_called()
    assert result.notna().all()


# ---------------------------------------------------------------------------
# Test: fallback fills NaN positions
# ---------------------------------------------------------------------------

def test_fallback_fills_nan_positions():
    partial_ts, warns = _partial_tempC(nan_start_idx=100)
    index = _utc_hourly_index("2025-01-05", periods=24)
    nan_index = partial_ts[partial_ts.isna()].index

    with patch("thermostat.eeweather_wrapper.eeweather.load_isd_hourly_temp_data",
               return_value=(partial_ts, warns)), \
         patch("thermostat.eeweather_wrapper.eeweather.get_isd_station_metadata",
               return_value={"recent_wban_id": "23234"}), \
         patch("thermostat.eeweather_wrapper.weather_fallback.fetch_ghcnh_hourly_temp_data",
               return_value=_ghcnh_fill(nan_index)), \
         patch("thermostat.eeweather_wrapper.eeweather.write_isd_hourly_temp_data_to_cache"):

        result = get_indexed_temperatures_eeweather("722880", index)

    # index is before nan_start_idx, all should be valid
    assert result.notna().all()


def test_fallback_fills_nan_in_tail():
    partial_ts, warns = _partial_tempC(nan_start_idx=8000)
    nan_index = partial_ts[partial_ts.isna()].index
    # Request the last 24 hours (all NaN in eeweather, should be filled)
    index = partial_ts.index[-24:]

    with patch("thermostat.eeweather_wrapper.eeweather.load_isd_hourly_temp_data",
               return_value=(partial_ts, warns)), \
         patch("thermostat.eeweather_wrapper.eeweather.get_isd_station_metadata",
               return_value={"recent_wban_id": "23234"}), \
         patch("thermostat.eeweather_wrapper.weather_fallback.fetch_ghcnh_hourly_temp_data",
               return_value=_ghcnh_fill(nan_index)), \
         patch("thermostat.eeweather_wrapper.eeweather.write_isd_hourly_temp_data_to_cache"):

        result = get_indexed_temperatures_eeweather("722880", index)

    assert result.notna().all()
    # 15 °C → 59 °F
    assert abs(result.iloc[0] - 59.0) < 0.01


# ---------------------------------------------------------------------------
# Test: valid original values are NOT overwritten
# ---------------------------------------------------------------------------

def test_fallback_does_not_overwrite_valid_data():
    partial_ts, warns = _partial_tempC(nan_start_idx=100)
    # Record the original value at position 0
    original_first = partial_ts.iloc[0]
    nan_index = partial_ts[partial_ts.isna()].index
    index = partial_ts.index[:5]  # first 5 hours — all have valid data

    with patch("thermostat.eeweather_wrapper.eeweather.load_isd_hourly_temp_data",
               return_value=(partial_ts, warns)), \
         patch("thermostat.eeweather_wrapper.eeweather.get_isd_station_metadata",
               return_value={"recent_wban_id": "23234"}), \
         patch("thermostat.eeweather_wrapper.weather_fallback.fetch_ghcnh_hourly_temp_data",
               return_value=_ghcnh_fill(nan_index)), \
         patch("thermostat.eeweather_wrapper.eeweather.write_isd_hourly_temp_data_to_cache"):

        result = get_indexed_temperatures_eeweather("722880", index)

    expected_first_f = 1.8 * original_first + 32
    assert abs(result.iloc[0] - expected_first_f) < 0.01


# ---------------------------------------------------------------------------
# Test: graceful degradation when both sources fail
# ---------------------------------------------------------------------------

def test_graceful_degradation_when_fallback_empty():
    all_nan_ts = pd.Series(
        np.nan,
        index=_utc_hourly_index("2025-01-01", 8760),
        dtype=float,
    )
    index = _utc_hourly_index("2025-06-01", 24)
    empty_fallback = pd.Series([], index=pd.DatetimeIndex([], tz=pytz.UTC), dtype=float)

    with patch("thermostat.eeweather_wrapper.eeweather.load_isd_hourly_temp_data",
               return_value=(all_nan_ts, [])), \
         patch("thermostat.eeweather_wrapper.eeweather.get_isd_station_metadata",
               return_value={"recent_wban_id": "23234"}), \
         patch("thermostat.eeweather_wrapper.weather_fallback.fetch_ghcnh_hourly_temp_data",
               return_value=empty_fallback):

        result = get_indexed_temperatures_eeweather("722880", index)

    assert isinstance(result, pd.Series)
    # All NaN is acceptable — no exception raised
    assert result.isna().all()


def test_graceful_degradation_when_no_wban_id():
    partial_ts, warns = _partial_tempC(nan_start_idx=100)
    index = _utc_hourly_index("2025-01-01", 24)

    with patch("thermostat.eeweather_wrapper.eeweather.load_isd_hourly_temp_data",
               return_value=(partial_ts, warns)), \
         patch("thermostat.eeweather_wrapper.eeweather.get_isd_station_metadata",
               return_value={"recent_wban_id": None}), \
         patch("thermostat.eeweather_wrapper.weather_fallback.fetch_ghcnh_hourly_temp_data") as mock_ghcnh:

        result = get_indexed_temperatures_eeweather("722880", index)

    mock_ghcnh.assert_not_called()
    assert isinstance(result, pd.Series)


# ---------------------------------------------------------------------------
# Test: empty index returns empty series (existing contract preserved)
# ---------------------------------------------------------------------------

def test_empty_index_returns_empty_series():
    empty_index = pd.DatetimeIndex([], tz=pytz.UTC)

    with patch("thermostat.eeweather_wrapper.eeweather.load_isd_hourly_temp_data") as mock_load:
        result = get_indexed_temperatures_eeweather("722880", empty_index)

    mock_load.assert_not_called()
    assert isinstance(result, pd.Series)
    assert len(result) == 0


# ---------------------------------------------------------------------------
# Test: date-based auto-routing to GHCN-H at NOAA_OUTAGE_DATE boundary
# ---------------------------------------------------------------------------

def test_ghcnh_called_automatically_for_post_outage_dates():
    """Requests ending on or after NOAA_OUTAGE_DATE trigger GHCN-H without NaN."""
    full_ts, warns = _full_tempC("2025-01-01", periods=8760)
    # No NaN in eeweather response — but date range crosses the outage date.
    post_outage_index = pd.date_range(
        NOAA_OUTAGE_DATE, periods=24, freq="h", tz=pytz.UTC
    )

    with patch("thermostat.eeweather_wrapper.eeweather.load_isd_hourly_temp_data",
               return_value=(full_ts, warns)), \
         patch("thermostat.eeweather_wrapper.eeweather.get_isd_station_metadata",
               return_value={"recent_wban_id": "23234"}), \
         patch("thermostat.eeweather_wrapper.weather_fallback.fetch_ghcnh_hourly_temp_data",
               return_value=_ghcnh_fill(full_ts.index)) as mock_ghcnh, \
         patch("thermostat.eeweather_wrapper.eeweather.write_isd_hourly_temp_data_to_cache"):

        get_indexed_temperatures_eeweather("722880", post_outage_index)

    mock_ghcnh.assert_called_once()


def test_ghcnh_not_called_for_pre_outage_complete_data():
    """Requests ending before NOAA_OUTAGE_DATE with no NaN skip GHCN-H entirely."""
    full_ts, warns = _full_tempC("2024-01-01", periods=8760)
    pre_outage_index = pd.date_range("2024-06-01", periods=24, freq="h", tz=pytz.UTC)

    with patch("thermostat.eeweather_wrapper.eeweather.load_isd_hourly_temp_data",
               return_value=(full_ts, warns)), \
         patch("thermostat.eeweather_wrapper.weather_fallback.fetch_ghcnh_hourly_temp_data") as mock_ghcnh:

        get_indexed_temperatures_eeweather("722880", pre_outage_index)

    mock_ghcnh.assert_not_called()


def test_noaa_outage_date_constant_is_correct():
    assert NOAA_OUTAGE_DATE == pd.Timestamp("2025-08-30", tz="UTC")


# ---------------------------------------------------------------------------
# Test: successful fill writes result back to eeweather cache
# ---------------------------------------------------------------------------

def test_cache_writeback_after_successful_fill():
    """After a GHCN-H fill, write_isd_hourly_temp_data_to_cache is called once per year."""
    partial_ts, warns = _partial_tempC(nan_start_idx=8000)
    nan_index = partial_ts[partial_ts.isna()].index
    index = partial_ts.index[-24:]

    with patch("thermostat.eeweather_wrapper.eeweather.load_isd_hourly_temp_data",
               return_value=(partial_ts, warns)), \
         patch("thermostat.eeweather_wrapper.eeweather.get_isd_station_metadata",
               return_value={"recent_wban_id": "23234"}), \
         patch("thermostat.eeweather_wrapper.weather_fallback.fetch_ghcnh_hourly_temp_data",
               return_value=_ghcnh_fill(nan_index)), \
         patch("thermostat.eeweather_wrapper.eeweather.write_isd_hourly_temp_data_to_cache") as mock_write:

        get_indexed_temperatures_eeweather("722880", index)

    # One call per year covered by the request (2025 only here)
    mock_write.assert_called_once()
    call_args = mock_write.call_args
    assert call_args[0][0] == "722880"
    assert call_args[0][1] == 2025


# ---------------------------------------------------------------------------
# Test: WBAN sentinel "99999" skips GHCN-H entirely
# ---------------------------------------------------------------------------

def test_sentinel_wban_skips_fallback():
    """WBAN id '99999' means unknown station — GHCN-H fetch is never attempted."""
    partial_ts, warns = _partial_tempC(nan_start_idx=100)
    index = _utc_hourly_index("2025-01-01", 24)

    with patch("thermostat.eeweather_wrapper.eeweather.load_isd_hourly_temp_data",
               return_value=(partial_ts, warns)), \
         patch("thermostat.eeweather_wrapper.eeweather.get_isd_station_metadata",
               return_value={"recent_wban_id": "99999"}), \
         patch("thermostat.eeweather_wrapper.weather_fallback.fetch_ghcnh_hourly_temp_data") as mock_ghcnh:

        get_indexed_temperatures_eeweather("725314", index)

    mock_ghcnh.assert_not_called()
