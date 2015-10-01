from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path

import pandas as pd

import pytest

@pytest.fixture(params=["metadata.csv"])
def metadata_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["interval_data.csv"])
def interval_data_filename(request):
    return get_data_path(request.param)

def test_import_csv(metadata_filename, interval_data_filename):
    thermostats = from_csv(metadata_filename,interval_data_filename)

    assert len(thermostats) == 1
    thermostat = thermostats[0]

    def assert_is_series_with_shape(series, shape):
        assert isinstance(series, pd.Series)
        assert series.shape == shape

    assert_is_series_with_shape(thermostat.cool_runtime, (1461,))
    assert_is_series_with_shape(thermostat.heat_runtime, (1461,))
    assert_is_series_with_shape(thermostat.auxiliary_heat_runtime, (1461,))
    assert_is_series_with_shape(thermostat.emergency_heat_runtime, (1461,))

    assert_is_series_with_shape(thermostat.cooling_setpoint, (35064,))
    assert_is_series_with_shape(thermostat.heating_setpoint, (35064,))
    assert_is_series_with_shape(thermostat.temperature_in, (35064,))
    assert_is_series_with_shape(thermostat.temperature_out, (35064,))
