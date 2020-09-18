import datetime
import pandas as pd
import pytest

from thermostat.importers import (
        from_csv,
        normalize_utc_offset,
        )

from thermostat.util.testing import get_data_path

from .fixtures.two_stage import (
        thermostat_hpeb_2_hp_2,
        )

def test_import_csv(thermostat_hpeb_2_hp_2):

    def assert_is_series_with_shape(series, shape):
        assert isinstance(series, pd.Series)
        assert series.shape == shape

    assert_is_series_with_shape(thermostat_hpeb_2_hp_2.cool_runtime_daily, (365,))
    assert_is_series_with_shape(thermostat_hpeb_2_hp_2.heat_runtime_daily, (365,))

    assert_is_series_with_shape(thermostat_hpeb_2_hp_2.cool_runtime_hourly, (8760,))
    assert_is_series_with_shape(thermostat_hpeb_2_hp_2.heat_runtime_hourly, (8760,))

    assert_is_series_with_shape(thermostat_hpeb_2_hp_2.auxiliary_heat_runtime, (8760,))
    assert_is_series_with_shape(thermostat_hpeb_2_hp_2.emergency_heat_runtime, (8760,))

    assert_is_series_with_shape(thermostat_hpeb_2_hp_2.temperature_in, (8760,))
    assert_is_series_with_shape(thermostat_hpeb_2_hp_2.temperature_out, (8760,))
