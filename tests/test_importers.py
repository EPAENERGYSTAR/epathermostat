from thermostat.importers import from_csv
from thermostat.importers import normalize_utc_offset
from thermostat.util.testing import get_data_path
import datetime

import pandas as pd

import pytest

from fixtures.thermostats import (
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
    assert(thermostat_type_1_utc_bad is None)
