import pytest
import numpy as np
from numpy.testing import assert_allclose
from numpy import isnan
import pandas as pd

from datetime import datetime

from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path

from .fixtures.two_stage import (
        thermostat_none_two_stage_heat_pump_two_stage,
        thermostat_furnace_or_boiler_two_stage_central_two_stage,
        thermostat_furnace_or_boiler_two_stage_none_single_stage,
        thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage,
        metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage_data,
        )


def test_thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage_get_core_heating_days(thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage):
    core_heating_day_sets = thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage.get_core_heating_days(
            method="year_mid_to_mid")
    assert len(core_heating_day_sets) == 2


def test_thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage_get_core_cooling_days(thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage):
    core_cooling_day_sets = thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage.get_core_cooling_days(
            method="year_end_to_end")
    assert len(core_cooling_day_sets) == 1


def test_thermostat_none_two_stage_heat_pump_two_stage(thermostat_none_two_stage_heat_pump_two_stage):
    with pytest.raises(ValueError):
        core_heating_day_sets = thermostat_none_two_stage_heat_pump_two_stage.get_core_heating_days(
                method="year_mid_to_mid")

def test_thermostat_furnace_or_boiler_two_stage_none_single_stage(thermostat_furnace_or_boiler_two_stage_none_single_stage):
    with pytest.raises(ValueError):
        core_cooling_day_sets = thermostat_furnace_or_boiler_two_stage_none_single_stage.get_core_cooling_days(
                method="year_end_to_end")
