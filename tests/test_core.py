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
def valid_temperature_out(valid_datetimeindex):
    return pd.Series(np.zeros((96,)),index=valid_datetimeindex)

@pytest.fixture
def thermostat_type_0(valid_thermostat_id, valid_equipment_type,
        valid_temperature_in,valid_temperature_setpoint,valid_temperature_out):
    thermostat = Thermostat(valid_thermostat_id,valid_equipment_type,
            valid_temperature_in,valid_temperature_setpoint,valid_temperature_out)
    return thermostat

@pytest.fixture
def heating_season_datetimeindex():
    return pd.DatetimeIndex(start="2012-01-01T00:00:00",freq='H',periods=96)

@pytest.fixture
def cooling_season_datetimeindex():
    return pd.DatetimeIndex(start="2012-06-01T00:00:00",freq='H',periods=96)

@pytest.fixture
def thermostat_type_1_with_heating_season(heating_season_datetimeindex,valid_temperature_in,valid_temperature_setpoint,valid_temperature_out):
    equipment_type = 1

    ss_heat_pump_heating = pd.Series(np.tile(3600,heating_season_datetimeindex.shape),index=heating_season_datetimeindex)
    ss_heat_pump_cooling = pd.Series(np.tile(0,heating_season_datetimeindex.shape),index=heating_season_datetimeindex)
    auxiliary_heat = pd.Series(np.tile(0,heating_season_datetimeindex.shape),index=heating_season_datetimeindex)
    emergency_heat = pd.Series(np.tile(0,heating_season_datetimeindex.shape),index=heating_season_datetimeindex)

    thermostat = Thermostat(valid_thermostat_id,
            equipment_type,
            valid_temperature_in,
            valid_temperature_setpoint,
            valid_temperature_out,
            ss_heat_pump_heating,
            ss_heat_pump_cooling,
            auxiliary_heat,
            emergency_heat)
    return thermostat

@pytest.fixture
def thermostat_type_1_with_cooling_season(cooling_season_datetimeindex,valid_temperature_in,valid_temperature_setpoint,valid_temperature_out):
    equipment_type = 1

    ss_heat_pump_heating = pd.Series(np.tile(0,cooling_season_datetimeindex.shape),index=cooling_season_datetimeindex)
    ss_heat_pump_cooling = pd.Series(np.tile(3600,cooling_season_datetimeindex.shape),index=cooling_season_datetimeindex)
    auxiliary_heat = pd.Series(np.tile(0,cooling_season_datetimeindex.shape),index=cooling_season_datetimeindex)
    emergency_heat = pd.Series(np.tile(0,cooling_season_datetimeindex.shape),index=cooling_season_datetimeindex)

    thermostat = Thermostat(valid_thermostat_id,
            equipment_type,
            valid_temperature_in,
            valid_temperature_setpoint,
            valid_temperature_out,
            ss_heat_pump_heating,
            ss_heat_pump_cooling,
            auxiliary_heat,
            emergency_heat)
    return thermostat

def test_thermostat_with_invalid_equipment_type(valid_thermostat_id,invalid_equipment_type):
    with pytest.raises(ValueError):
        thermostat = Thermostat(valid_thermostat_id,invalid_equipment_type,None,None,None)

def test_thermostat_with_valid_equipment_type(valid_thermostat_id,valid_equipment_type):
    thermostat = Thermostat(valid_thermostat_id,valid_equipment_type,None,None,None)
    assert thermostat.equipment_type == valid_equipment_type

def test_thermostat_attributes(thermostat_type_0):
    assert thermostat_type_0.equipment_type == 0
    assert type(thermostat_type_0.temperature_in.index) == pd.DatetimeIndex
    assert type(thermostat_type_0.temperature_setpoint.index) == pd.DatetimeIndex
    assert type(thermostat_type_0.temperature_out.index) == pd.DatetimeIndex

def test_thermostat_get_heating_columns(thermostat_type_1_with_heating_season,heating_season_datetimeindex):
    heating_columns = thermostat_type_1_with_heating_season.get_heating_columns()
    assert len(heating_columns) == 3
    for heating_column in heating_columns:
        assert heating_column.index.shape == heating_season_datetimeindex.shape
        assert type(heating_column.index) == pd.DatetimeIndex

def test_thermostat_get_cooling_columns(thermostat_type_1_with_cooling_season,cooling_season_datetimeindex):
    cooling_columns = thermostat_type_1_with_cooling_season.get_cooling_columns()
    assert len(cooling_columns) == 1
    for cooling_column in cooling_columns:
        assert cooling_column.index.shape == cooling_season_datetimeindex.shape
        assert type(cooling_column.index) == pd.DatetimeIndex

def test_thermostat_get_heating_seasons(thermostat_type_1_with_heating_season,heating_season_datetimeindex):
    heating_seasons = thermostat_type_1_with_heating_season.get_heating_seasons()
    assert len(heating_seasons) == 1
    assert heating_seasons[0][0].shape == heating_season_datetimeindex.shape
    assert heating_seasons[0][1] == "2011-2012 Heating Season"

def test_thermostat_get_cooling_seasons(thermostat_type_1_with_cooling_season,cooling_season_datetimeindex):
    cooling_seasons = thermostat_type_1_with_cooling_season.get_cooling_seasons()
    assert len(cooling_seasons) == 1
    assert cooling_seasons[0][0].shape == cooling_season_datetimeindex.shape
    assert cooling_seasons[0][1] == "2012 Cooling Season"
