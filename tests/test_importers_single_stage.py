import datetime
import pandas as pd
import pytest

from thermostat.importers import (
        from_csv,
        normalize_utc_offset,
        )

from thermostat.util.testing import get_data_path

from .fixtures.single_stage import (
        thermostat_type_1,
        thermostat_type_1_utc,
        thermostat_type_1_utc_bad,
        thermostat_type_1_too_many_minutes,
        thermostat_type_1_utc_bad,
        thermostat_type_1_zip_bad,
        thermostat_type_1_data_out_of_order,
        thermostat_type_1_data_missing_header,
        thermostat_type_1_cache,
        thermostat_missing_hours,
        thermostat_missing_days,
        )

def test_import_csv(thermostat_type_1):

    def assert_is_series_with_shape(series, shape):
        assert isinstance(series, pd.Series)
        assert series.shape == shape

    assert_is_series_with_shape(thermostat_type_1.cool_runtime_daily, (1461,))
    assert_is_series_with_shape(thermostat_type_1.heat_runtime_daily, (1461,))

    assert_is_series_with_shape(thermostat_type_1.cool_runtime_hourly, (35064,))
    assert_is_series_with_shape(thermostat_type_1.heat_runtime_hourly, (35064,))

    assert_is_series_with_shape(thermostat_type_1.auxiliary_heat_runtime, (35064,))
    assert_is_series_with_shape(thermostat_type_1.emergency_heat_runtime, (35064,))

    assert_is_series_with_shape(thermostat_type_1.temperature_in, (35064,))
    assert_is_series_with_shape(thermostat_type_1.temperature_out, (35064,))

def test_import_csv_cache(thermostat_type_1_cache):
    assert thermostat_type_1_cache is not None

def test_utc_offset(thermostat_type_1_utc, thermostat_type_1_utc_bad):
    assert(normalize_utc_offset("+0") == datetime.timedelta(0))
    assert(normalize_utc_offset("-0") == datetime.timedelta(0))
    assert(normalize_utc_offset("0") == datetime.timedelta(0))
    assert(normalize_utc_offset(0) == datetime.timedelta(0))
    assert(normalize_utc_offset("+6") == datetime.timedelta(0, 21600))
    assert(normalize_utc_offset("-6") == datetime.timedelta(-1, 64800))
    assert(normalize_utc_offset("-0600") == datetime.timedelta(-1, 64800))
    assert(normalize_utc_offset(-6) == datetime.timedelta(-1, 64800))

    with pytest.raises(TypeError) as excinfo:
        normalize_utc_offset('+O')
    assert "Invalid UTC" in str(excinfo)

    with pytest.raises(TypeError) as excinfo:
        normalize_utc_offset('6')
    assert "Invalid UTC" in str(excinfo)

    # Load a thermostat with utc offset == 0
    assert(isinstance(thermostat_type_1_utc.cool_runtime_daily, pd.Series))
    assert(isinstance(thermostat_type_1_utc.cool_runtime_hourly, pd.Series))
    assert(thermostat_type_1_utc_bad is None)

def test_too_many_minutes(thermostat_type_1_too_many_minutes):
    # None of the thermostats in this list should import
    assert len(thermostat_type_1_too_many_minutes) == 0

def test_missing_hours(thermostat_missing_hours):
    missing_hours = thermostat_missing_hours.heat_runtime_hourly[thermostat_missing_hours.heat_runtime_hourly.isna()]
    missing_hours_days = set(missing_hours.index.date)
    missing_daily = thermostat_missing_hours.heat_runtime_daily[thermostat_missing_hours.heat_runtime_daily.isna()]
    missing_daily_days = set(missing_daily.index.date)
    assert missing_daily_days.difference(missing_hours_days) == set()

def test_missing_days(thermostat_missing_days):
    # Checking what happens
    assert len(thermostat_missing_days) == 0

def test_bad_zipcode(thermostat_type_1_zip_bad):
    assert len(thermostat_type_1_zip_bad) == 0

def test_data_out_of_order(thermostat_type_1_data_out_of_order):
    assert len(thermostat_type_1_data_out_of_order) == 0

def test_data_missing_headers(thermostat_type_1_data_missing_header):
    assert len(thermostat_type_1_data_missing_header) == 0
