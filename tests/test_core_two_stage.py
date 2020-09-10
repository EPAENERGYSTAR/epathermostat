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
        core_heating_day_set_heat_pump_electric_backup_two_stage_heat_pump_two_stage_entire,
        core_cooling_day_set_heat_pump_electric_backup_two_stage_heat_pump_two_stage_entire,
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

@pytest.fixture(params=range(2))
def core_days(request, thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage, core_heating_day_set_heat_pump_electric_backup_two_stage_heat_pump_two_stage_entire,
        core_cooling_day_set_heat_pump_electric_backup_two_stage_heat_pump_two_stage_entire):

    tests = [
        (thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage, core_cooling_day_set_heat_pump_electric_backup_two_stage_heat_pump_two_stage_entire, 0, "cooling"),
        (thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage, core_heating_day_set_heat_pump_electric_backup_two_stage_heat_pump_two_stage_entire, 1, "heating"),
    ]

    return tests[request.param]


def test_day_counts(core_days, metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage_data):
    thermostat, core_day_set, i, heating_or_cooling = core_days
    n_both, n_days_insufficient = thermostat.get_ignored_days(core_day_set)
    n_core_days = thermostat.get_core_day_set_n_days(core_day_set)
    n_days_in_inputfile_date_range = thermostat.get_inputfile_date_range(core_day_set)
    assert n_both == metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage_data[i]["n_days_both_heating_and_cooling"]
    assert n_days_insufficient == metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage_data[i]["n_days_insufficient_data"]
    assert n_core_days == metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage_data[i]["n_core_{}_days".format(heating_or_cooling)]
    assert n_days_in_inputfile_date_range == metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage_data[i]["n_days_in_inputfile_date_range"]
