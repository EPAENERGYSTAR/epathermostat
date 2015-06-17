import pytest
from thermostat.demand import get_cooling_demand
from thermostat.demand import get_heating_demand

from thermostat import Thermostat

import pandas as pd
import numpy as np
from numpy.testing import assert_allclose

RTOL = 1e-6
ATOL = 1e-6

@pytest.fixture
def valid_thermostat_id():
    return "10912098123"

@pytest.fixture
def valid_datetimeindex():
    return pd.DatetimeIndex(start="2012-01-01T00:00:00",freq='H',periods=400)

@pytest.fixture
def valid_temperature_setpoint(valid_datetimeindex):
    return pd.Series(np.zeros((400,)),index=valid_datetimeindex)

def test_get_cooling_demand_deltaT(valid_thermostat_id,valid_temperature_setpoint,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.tile(90,(400,)),index=valid_datetimeindex)

    ss_heat_pump_cooling = pd.Series(np.tile(3600,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,valid_temperature_setpoint,temp_out,
            ss_heat_pump_cooling=ss_heat_pump_cooling,ss_heat_pump_heating=ss_heat_pump_heating)

    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    deltaT = get_cooling_demand(thermostat_type_2,cooling_season,method="deltaT")
    assert_allclose(deltaT,np.tile(-20,(400,)),rtol=RTOL,atol=ATOL)

def test_get_heating_demand_deltaT(valid_thermostat_id,valid_temperature_setpoint,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.tile(50,(400,)),index=valid_datetimeindex)

    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(3600,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,valid_temperature_setpoint,temp_out,
            ss_heat_pump_cooling=ss_heat_pump_cooling,ss_heat_pump_heating=ss_heat_pump_heating)

    heating_season, name = thermostat_type_2.get_heating_seasons()[0]
    deltaT = get_heating_demand(thermostat_type_2,heating_season,method="deltaT")
    assert_allclose(deltaT,np.tile(20,(400,)),rtol=RTOL,atol=ATOL)

