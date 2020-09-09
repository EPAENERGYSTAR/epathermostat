from thermostat.importers import from_csv
from thermostat.importers import get_single_thermostat
from thermostat.util.testing import get_data_path
from thermostat.core import Thermostat, CoreDaySet
from tempfile import TemporaryDirectory

import pandas as pd
import numpy as np
from numpy import nan

import pytest


@pytest.fixture(scope="session", params=["../data/two_stage/metadata_furnace_or_boiler_two_stage_central_two_stage.csv"])
def thermostat_furnace_or_boiler_two_stage_central_two_stage(request):
    thermostats = from_csv(get_data_path(request.param))
    return thermostats

@pytest.fixture(scope="session", params=["../data/two_stage/metadata_furnace_or_boiler_two_stage_none_single_stage.csv"])
def thermostat_furnace_or_boiler_two_stage_none_single_stage(request):
    thermostats = from_csv(get_data_path(request.param))
    return thermostats

@pytest.fixture(scope="session", params=["../data/two_stage/metadata_heat_pump_electric_backup_two_stage_heat_pump_two_stage.csv"])
def thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage(request):
    thermostats = from_csv(get_data_path(request.param))
    return thermostats

@pytest.fixture(scope="session", params=["../data/two_stage/metadata_none_two_stage_heat_pump_two_stage.csv"])
def thermostat_none_two_stage_heat_pump_two_stage(request):
    thermostats = from_csv(get_data_path(request.param))
    return thermostats
