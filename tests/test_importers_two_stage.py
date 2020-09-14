import datetime
import pandas as pd
import pytest

from thermostat.importers import (
        from_csv,
        normalize_utc_offset,
        )

from thermostat.util.testing import get_data_path

from .fixtures.two_stage import (
        thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage,
        )

def test_import_csv(thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage):

    def assert_is_series_with_shape(series, shape):
        assert isinstance(series, pd.Series)
        assert series.shape == shape

    assert_is_series_with_shape(thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage.cool_runtime_daily, (365,))
    assert_is_series_with_shape(thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage.heat_runtime_daily, (365,))

    assert_is_series_with_shape(thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage.cool_runtime_hourly, (8760,))
    assert_is_series_with_shape(thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage.heat_runtime_hourly, (8760,))

    assert_is_series_with_shape(thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage.auxiliary_heat_runtime, (8760,))
    assert_is_series_with_shape(thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage.emergency_heat_runtime, (8760,))

    assert_is_series_with_shape(thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage.temperature_in, (8760,))
    assert_is_series_with_shape(thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage.temperature_out, (8760,))
