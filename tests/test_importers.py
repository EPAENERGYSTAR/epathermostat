from thermostat.importers import from_csv
from thermostat.importers import normalize_utc_offset
from thermostat.util.testing import get_data_path
import datetime

import pandas as pd

import pytest

from .fixtures.thermostats import (
        thermostat_type_1,
        thermostat_type_1_utc,
        thermostat_type_1_utc_bad,)

def test_import_csv(thermostat_type_1):

    def assert_is_series_with_shape(series, shape):
        assert isinstance(series, pd.Series)
        assert series.shape == shape

    assert_is_series_with_shape(thermostat_type_1.cool_runtime, (1461,))
    assert_is_series_with_shape(thermostat_type_1.heat_runtime, (1461,))

    assert_is_series_with_shape(thermostat_type_1.auxiliary_heat_runtime, (35064,))
    assert_is_series_with_shape(thermostat_type_1.emergency_heat_runtime, (35064,))

    assert_is_series_with_shape(thermostat_type_1.cooling_setpoint, (35064,))
    assert_is_series_with_shape(thermostat_type_1.heating_setpoint, (35064,))

    assert_is_series_with_shape(thermostat_type_1.temperature_in, (35064,))
    assert_is_series_with_shape(thermostat_type_1.temperature_out, (35064,))

def test_utc_offset(thermostat_type_1_utc, thermostat_type_1_utc_bad):
    assert(normalize_utc_offset("+0") == datetime.timedelta(0))
    assert(normalize_utc_offset("-0") == datetime.timedelta(0))
    assert(normalize_utc_offset("0") == datetime.timedelta(0))
    assert(normalize_utc_offset(0) == datetime.timedelta(0))
    assert(normalize_utc_offset("+6") == datetime.timedelta(0, 21600))
    assert(normalize_utc_offset("-6") == datetime.timedelta(-1, 64800))
    assert(normalize_utc_offset(-6) == datetime.timedelta(-1, 64800))

    with pytest.raises(TypeError) as excinfo:
        normalize_utc_offset(6)
    assert "Invalid UTC" in str(excinfo)

    # Load a thermostat with utc offset == 0
    assert(isinstance(thermostat_type_1_utc.cool_runtime, pd.Series))
    # the bad utc_offset row is skipped, so no thermostat is imported
    assert thermostat_type_1_utc_bad == []


def constant_60F(station, index):
    """A weather_source stand-in: 60 F for every hour, no network."""
    return pd.Series(60.0, index=index, dtype=float)


def test_from_csv_accepts_a_weather_source():
    """from_csv can be handed temperatures instead of fetching them.

    Without this seam every fixture in the suite reaches NOAA during import,
    which is what made the regression tests depend on network availability.
    """
    thermostats = list(from_csv(
        # NB: get_data_path resolves relative to the *calling* file
        get_data_path("data/metadata_type_1_single.csv"),
        shuffle=False,
        weather_source=constant_60F,
    ))

    assert len(thermostats) == 1
    temp_out = thermostats[0].temperature_out
    assert isinstance(temp_out, pd.Series)
    assert (temp_out == 60.0).all()
    # the index is the thermostat's own local hourly index, not the fetch index
    assert temp_out.index.equals(thermostats[0].temperature_in.index)
