from thermostat.core import Thermostat

import pandas as pd
import numpy as np

import pytest

@pytest.fixture(params=[0])
def valid_equipment_type(request):
    return request.param

@pytest.fixture(params=[6,"foo"])
def invalid_equipment_type(request):
    return request.param

@pytest.fixture
def valid_thermostat_id():
    return "10912098123"

@pytest.fixture
def valid_datetimeindex():
    return pd.DatetimeIndex(start="2012-01-01T00:00:00",freq='H',periods=96)

@pytest.fixture
def valid_temperature_in(valid_datetimeindex):
    return pd.Series(np.zeros((96,)),index=valid_datetimeindex)

@pytest.fixture
def valid_temperature_setpoint(valid_datetimeindex):
    return pd.Series(np.zeros((96,)),index=valid_datetimeindex)

@pytest.fixture
def valid_thermostat_id():
    return "10912098123"

def test_thermostat_with_invalid_equipment_type(invalid_equipment_type, valid_thermostat_id):
    with pytest.raises(ValueError):
        thermostat = Thermostat(valid_thermostat_id,invalid_equipment_type,None,None)

def test_thermostat_with_valid_equipment_type(valid_equipment_type, valid_thermostat_id):
    thermostat = Thermostat(valid_thermostat_id,valid_equipment_type,None,None)
    assert thermostat.equipment_type == valid_equipment_type

def test_thermostat_attributes(valid_equipment_type, valid_thermostat_id,valid_temperature_in,valid_temperature_setpoint):
    thermostat = Thermostat(valid_thermostat_id,valid_equipment_type,valid_temperature_in,valid_temperature_setpoint)
    assert thermostat.equipment_type == valid_equipment_type
    assert type(thermostat.temperature_in.index) == pd.DatetimeIndex
    assert type(thermostat.temperature_setpoint.index) == pd.DatetimeIndex
