import pytest

from thermostat.regression import runtime_regression
from thermostat.demand import get_cooling_demand
from thermostat.demand import get_heating_demand

from thermostat import Thermostat

import pandas as pd
import numpy as np

from numpy.testing import assert_allclose

@pytest.fixture
def valid_thermostat_id():
    return "10912098123"

@pytest.fixture
def valid_zipcode():
    return "10912098123"

@pytest.fixture
def valid_datetimeindex():
    return pd.DatetimeIndex(start="2012-01-01T00:00:00",freq='H',periods=400)

@pytest.fixture
def valid_temperature_setpoint(valid_datetimeindex):
    return pd.Series(np.zeros((400,)),index=valid_datetimeindex)

def test_runtime_regression_cooling(valid_thermostat_id,valid_zipcode,valid_temperature_setpoint,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(80,90,num=400),index=valid_datetimeindex)

    hourly_alpha = 20
    daily_alpha = hourly_alpha * 24

    ss_heat_pump_cooling = pd.Series(np.maximum((temp_out - temp_in) * hourly_alpha,0),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,valid_zipcode,temp_in,valid_temperature_setpoint,temp_out,
            ss_heat_pump_cooling=ss_heat_pump_cooling,ss_heat_pump_heating=ss_heat_pump_heating)

    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]

    daily_cooling_demand, _, _, _ = get_cooling_demand(thermostat_type_2,cooling_season,method="dailyavgCDD")
    hourly_runtime = ss_heat_pump_cooling[cooling_season]
    slope,intercept, mean_sq_err = runtime_regression(hourly_runtime,daily_cooling_demand)

    assert_allclose(slope,daily_alpha,rtol=0.01,atol=0.01)
    assert_allclose(intercept,0,rtol=0.01,atol=0.01)
    assert_allclose(mean_sq_err,0,rtol=0.01,atol=0.01)

def test_runtime_regression_heating(valid_thermostat_id,valid_zipcode,valid_temperature_setpoint, valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(60,50,num=400),index=valid_datetimeindex)

    hourly_alpha = 20
    daily_alpha = hourly_alpha * 24

    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.maximum((temp_in - temp_out) * hourly_alpha,0),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,valid_zipcode,temp_in,valid_temperature_setpoint,temp_out,
            ss_heat_pump_cooling=ss_heat_pump_cooling,ss_heat_pump_heating=ss_heat_pump_heating)

    heating_season, name = thermostat_type_2.get_heating_seasons()[0]

    daily_heating_demand, _, _, _ = get_heating_demand(thermostat_type_2,heating_season,method="dailyavgHDD")
    hourly_runtime = ss_heat_pump_heating[heating_season]

    slope, intercept, mean_sq_err = runtime_regression(hourly_runtime,daily_heating_demand)

    assert_allclose(slope,daily_alpha,rtol=0.01,atol=0.01)
    assert_allclose(intercept,0,rtol=0.01,atol=0.01)
    assert_allclose(mean_sq_err,0,rtol=0.01,atol=0.01)

