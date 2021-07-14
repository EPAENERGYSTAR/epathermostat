from thermostat.importers import from_csv
from thermostat.importers import get_single_thermostat
from thermostat.util.testing import get_data_path
from thermostat.core import Thermostat, CoreDaySet
from tempfile import TemporaryDirectory

import pandas as pd
import numpy as np
from numpy import nan

import pytest

''' Abbreviations used in this file:

    XX - Heating system type: fu (furnace), hp (heat pump),  er (electric resistance), ot (other)
    XX - Cooling system type: ce (central), hp (heat pump), 

    YY - backup: eb (electric backup), ne (non electric backup, df (dual fuel), na (N/A)

    Z - speed: 1 (single stage), 2 (two stage), v (variable)
'''

@pytest.fixture(scope="session", params=["../data/two_stage/metadata_furnace_or_boiler_two_stage_central_two_stage.csv"])
def thermostat_fu_2_ce_2(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/two_stage/metadata_furnace_or_boiler_two_stage_none_single_stage.csv"])
def thermostat_furnace_or_boiler_two_stage_none_single_stage(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/two_stage/metadata_heat_pump_electric_backup_two_stage_heat_pump_two_stage.csv"])
def thermostat_hpeb_2_hp_2(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/two_stage/metadata_none_two_stage_heat_pump_two_stage.csv"])
def thermostat_na_2_hp_2(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session")
def core_heating_day_set_hpeb_2_hp_2_entire(thermostat_hpeb_2_hp_2):
    return thermostat_hpeb_2_hp_2.get_core_heating_days(method="entire_dataset")[0]

@pytest.fixture(scope="session")
def core_cooling_day_set_hpeb_2_hp_2_entire(thermostat_hpeb_2_hp_2):
    return thermostat_hpeb_2_hp_2.get_core_cooling_days(method="entire_dataset")[0]
