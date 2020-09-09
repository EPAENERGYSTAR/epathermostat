from thermostat.importers import from_csv
from thermostat.importers import get_single_thermostat
from thermostat.util.testing import get_data_path
from thermostat.core import Thermostat, CoreDaySet
from tempfile import TemporaryDirectory

import pandas as pd
import numpy as np
from numpy import nan

import pytest

# will be modified, recreate every time by scoping to function
@pytest.fixture(scope='function')
def thermostat_template():
    thermostat_id = "FAKE"
    heat_type = None
    heat_stage = None
    cool_type = None
    cool_stage = None
    zipcode = "FAKE"
    station = "FAKE"
    temperature_in = pd.Series([], dtype="Float64")
    temperature_out = pd.Series([], dtype="Float64")
    cool_runtime = pd.Series([], dtype="Float64")
    heat_runtime = pd.Series([], dtype="Float64")
    auxiliary_heat_runtime = pd.Series([], dtype="Float64")
    emergency_heat_runtime = pd.Series([], dtype="Float64")

    thermostat = Thermostat(
        thermostat_id,
        heat_type,
        heat_stage,
        cool_type,
        cool_stage,
        zipcode,
        station,
        temperature_in,
        temperature_out,
        cool_runtime,
        heat_runtime,
        auxiliary_heat_runtime,
        emergency_heat_runtime
    )
    return thermostat
