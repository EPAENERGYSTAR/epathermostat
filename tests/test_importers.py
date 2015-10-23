from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path

import pandas as pd

import pytest

from fixtures.thermostats import thermostat_type_1

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
