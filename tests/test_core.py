from thermostat.core import Thermostat

import pandas as pd
import numpy as np

import pytest

from numpy.testing import assert_allclose

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
def valid_zipcode():
    return "01234"

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
def full_year_datetimeindex():
    return pd.DatetimeIndex(start="2012-01-01T00:00:00",freq='H',periods=365*24)

@pytest.fixture
def full_year_temperature_in(full_year_datetimeindex):
    return pd.Series(np.zeros(full_year_datetimeindex.shape),index=full_year_datetimeindex)

@pytest.fixture
def full_year_temperature_setpoint(full_year_datetimeindex):
    return pd.Series(np.zeros(full_year_datetimeindex.shape),index=full_year_datetimeindex)

@pytest.fixture
def full_year_temperature_out(full_year_datetimeindex):
    return pd.Series(np.zeros(full_year_datetimeindex.shape),index=full_year_datetimeindex)

@pytest.fixture
def thermostat_type_0(valid_thermostat_id, valid_equipment_type, valid_zipcode,
        valid_temperature_in,valid_temperature_setpoint,valid_temperature_out):
    thermostat = Thermostat(valid_thermostat_id,valid_equipment_type, valid_zipcode,
            valid_temperature_in,valid_temperature_setpoint,valid_temperature_out)
    return thermostat

@pytest.fixture
def heating_season_datetimeindex():
    return pd.DatetimeIndex(start="2012-01-01T00:00:00",freq='H',periods=96)

@pytest.fixture
def cooling_season_datetimeindex():
    return pd.DatetimeIndex(start="2012-06-01T00:00:00",freq='H',periods=96)

@pytest.fixture
def thermostat_type_1_with_heating_season(valid_thermostat_id,valid_zipcode,heating_season_datetimeindex,valid_temperature_in,valid_temperature_setpoint,valid_temperature_out):
    equipment_type = 1

    ss_heat_pump_heating = pd.Series(np.tile(3600,heating_season_datetimeindex.shape),index=heating_season_datetimeindex)
    ss_heat_pump_cooling = pd.Series(np.tile(0,heating_season_datetimeindex.shape),index=heating_season_datetimeindex)
    auxiliary_heat = pd.Series(np.tile(0,heating_season_datetimeindex.shape),index=heating_season_datetimeindex)
    emergency_heat = pd.Series(np.tile(0,heating_season_datetimeindex.shape),index=heating_season_datetimeindex)

    thermostat = Thermostat(valid_thermostat_id,
            equipment_type,
            valid_zipcode,
            valid_temperature_in,
            valid_temperature_setpoint,
            valid_temperature_out,
            ss_heat_pump_heating,
            ss_heat_pump_cooling,
            auxiliary_heat,
            emergency_heat)
    return thermostat

@pytest.fixture
def thermostat_type_1_with_heating_season_emg_aux(valid_thermostat_id,valid_zipcode,heating_season_datetimeindex,valid_temperature_in,valid_temperature_setpoint,valid_temperature_out):
    equipment_type = 1

    ss_heat_pump_heating = pd.Series(np.tile(3600,heating_season_datetimeindex.shape),index=heating_season_datetimeindex)
    ss_heat_pump_cooling = pd.Series(np.tile(0,heating_season_datetimeindex.shape),index=heating_season_datetimeindex)
    auxiliary_heat = pd.Series(np.tile(10,heating_season_datetimeindex.shape),index=heating_season_datetimeindex)
    emergency_heat = pd.Series(np.tile(20,heating_season_datetimeindex.shape),index=heating_season_datetimeindex)
    temp_in = pd.Series(np.linspace(0,60,num=heating_season_datetimeindex.shape[0]),index=heating_season_datetimeindex)

    thermostat = Thermostat(valid_thermostat_id,
            equipment_type,
            valid_zipcode,
            valid_temperature_in,
            valid_temperature_setpoint,
            temp_in,
            ss_heat_pump_heating,
            ss_heat_pump_cooling,
            auxiliary_heat,
            emergency_heat)
    return thermostat

@pytest.fixture
def thermostat_type_1_with_cooling_season(valid_thermostat_id,valid_zipcode,cooling_season_datetimeindex,valid_temperature_in,valid_temperature_setpoint,valid_temperature_out):
    equipment_type = 1

    ss_heat_pump_heating = pd.Series(np.tile(0,cooling_season_datetimeindex.shape),index=cooling_season_datetimeindex)
    ss_heat_pump_cooling = pd.Series(np.tile(3600,cooling_season_datetimeindex.shape),index=cooling_season_datetimeindex)
    auxiliary_heat = pd.Series(np.tile(0,cooling_season_datetimeindex.shape),index=cooling_season_datetimeindex)
    emergency_heat = pd.Series(np.tile(0,cooling_season_datetimeindex.shape),index=cooling_season_datetimeindex)

    thermostat = Thermostat(valid_thermostat_id,
            equipment_type,
            valid_zipcode,
            valid_temperature_in,
            valid_temperature_setpoint,
            valid_temperature_out,
            ss_heat_pump_heating,
            ss_heat_pump_cooling,
            auxiliary_heat,
            emergency_heat)
    return thermostat

@pytest.fixture
def thermostat_type_2_with_heating_and_cooling_season(valid_thermostat_id,valid_zipcode,full_year_datetimeindex,
        full_year_temperature_in,full_year_temperature_setpoint,full_year_temperature_out):
    equipment_type = 2

    ss_heat_pump_heating = pd.Series(np.tile(3600,full_year_datetimeindex.shape),index=full_year_datetimeindex)
    ss_heat_pump_cooling = pd.Series(np.tile(3600,full_year_datetimeindex.shape),index=full_year_datetimeindex)

    thermostat = Thermostat(valid_thermostat_id,
            equipment_type,
            valid_zipcode,
            full_year_temperature_in,
            full_year_temperature_setpoint,
            full_year_temperature_out,
            ss_heat_pump_heating,
            ss_heat_pump_cooling)
    return thermostat

@pytest.fixture
def thermostat_type_4_with_heating_season(valid_zipcode,cooling_season_datetimeindex,valid_temperature_in,valid_temperature_setpoint,valid_temperature_out):
    equipment_type = 4

    ss_heating = pd.Series(np.tile(3600,cooling_season_datetimeindex.shape),index=cooling_season_datetimeindex)

    thermostat = Thermostat(valid_thermostat_id,
            equipment_type,
            valid_zipcode,
            valid_temperature_in,
            valid_temperature_setpoint,
            valid_temperature_out,
            ss_heating=ss_heating)
    return thermostat

@pytest.fixture
def thermostat_type_5_with_cooling_season(valid_zipcode,cooling_season_datetimeindex,valid_temperature_in,valid_temperature_setpoint,valid_temperature_out):
    equipment_type = 5

    ss_central_ac = pd.Series(np.tile(3600,cooling_season_datetimeindex.shape),index=cooling_season_datetimeindex)

    thermostat = Thermostat(valid_thermostat_id,
            equipment_type,
            valid_zipcode,
            valid_temperature_in,
            valid_temperature_setpoint,
            valid_temperature_out,
            ss_central_ac=ss_central_ac)
    return thermostat

def test_thermostat_with_invalid_equipment_type(valid_thermostat_id,invalid_equipment_type):
    with pytest.raises(ValueError):
        thermostat = Thermostat(valid_thermostat_id,invalid_equipment_type,None,None,None,None)

def test_thermostat_with_valid_equipment_type(valid_thermostat_id,valid_equipment_type):
    thermostat = Thermostat(valid_thermostat_id,valid_equipment_type,None,None,None,None)
    assert thermostat.equipment_type == valid_equipment_type

def test_thermostat_attributes(thermostat_type_0):
    assert thermostat_type_0.equipment_type == 0
    assert type(thermostat_type_0.temperature_in.index) == pd.DatetimeIndex
    assert type(thermostat_type_0.temperature_setpoint.index) == pd.DatetimeIndex
    assert type(thermostat_type_0.temperature_out.index) == pd.DatetimeIndex

def test_thermostat_get_heating_columns(thermostat_type_1_with_heating_season,heating_season_datetimeindex):
    heating_columns = thermostat_type_1_with_heating_season.get_heating_columns()
    assert len(heating_columns) == 1
    for heating_column in heating_columns:
        assert heating_column.index.shape == heating_season_datetimeindex.shape
        assert type(heating_column.index) == pd.DatetimeIndex

def test_thermostat_get_cooling_columns(thermostat_type_1_with_cooling_season,cooling_season_datetimeindex):
    cooling_columns = thermostat_type_1_with_cooling_season.get_cooling_columns()
    assert len(cooling_columns) == 1
    for cooling_column in cooling_columns:
        assert cooling_column.index.shape == cooling_season_datetimeindex.shape
        assert type(cooling_column.index) == pd.DatetimeIndex

def test_thermostat_get_resistance_heat_columns(thermostat_type_1_with_heating_season,heating_season_datetimeindex):
    rh_columns = thermostat_type_1_with_heating_season.get_resistance_heat_columns()
    assert len(rh_columns) == 2
    for rh_column in rh_columns:
        assert rh_column.index.shape == heating_season_datetimeindex.shape
        assert type(rh_column.index) == pd.DatetimeIndex

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

def test_thermostat_get_cooling_columns_with_no_cooling_columns(thermostat_type_4_with_heating_season):
    cooling_columns = thermostat_type_4_with_heating_season.get_cooling_columns()
    assert cooling_columns == []

def test_thermostat_get_cooling_seasons_with_no_cooling_columns(thermostat_type_4_with_heating_season):
    cooling_seasons = thermostat_type_4_with_heating_season.get_cooling_seasons()
    assert cooling_seasons == []

def test_thermostat_get_heating_columns_with_no_heating_columns(thermostat_type_5_with_cooling_season):
    heating_columns = thermostat_type_5_with_cooling_season.get_heating_columns()
    assert heating_columns == []

def test_thermostat_get_heating_seasons_with_no_heating_columns(thermostat_type_5_with_cooling_season):
    heating_seasons = thermostat_type_5_with_cooling_season.get_heating_seasons()
    assert heating_seasons == []

def test_thermostat_get_cooling_seasons_ignores_simultaneous_heating_cooling(thermostat_type_2_with_heating_and_cooling_season):
    cooling_seasons = thermostat_type_2_with_heating_and_cooling_season.get_cooling_seasons()
    assert cooling_seasons == []

def test_thermostat_get_heating_seasons_ignores_simultaneous_heating_cooling(thermostat_type_2_with_heating_and_cooling_season):
    heating_seasons = thermostat_type_2_with_heating_and_cooling_season.get_heating_seasons()
    assert heating_seasons == []

def test_thermostat_get_heating_season_total_runtime(thermostat_type_1_with_heating_season):
    heating_season,_ = thermostat_type_1_with_heating_season.get_heating_seasons()[0]
    heating_runtime = thermostat_type_1_with_heating_season.get_heating_season_total_runtime(heating_season)
    assert_allclose(heating_runtime,345600,rtol=1e-3,atol=1e-3)

def test_thermostat_get_cooling_season_total_runtime(thermostat_type_1_with_cooling_season):
    cooling_season,_ = thermostat_type_1_with_cooling_season.get_cooling_seasons()[0]
    cooling_runtime = thermostat_type_1_with_cooling_season.get_cooling_season_total_runtime(cooling_season)
    assert_allclose(cooling_runtime,345600,rtol=1e-3,atol=1e-3)

def test_thermostat_get_resistance_heat_utilization(thermostat_type_1_with_heating_season_emg_aux):
    heating_season,_ = thermostat_type_1_with_heating_season_emg_aux.get_heating_seasons()[0]
    rhus = thermostat_type_1_with_heating_season_emg_aux.get_resistance_heat_utilization(heating_season)
    assert_allclose(rhus,np.tile(0.008287,(12,)),rtol=1e-3,atol=1e-3)

def test_get_season_ignored_days(thermostat_type_1_with_heating_season):
    _,season_name = thermostat_type_1_with_heating_season.get_heating_seasons()[0]
    n_days_both, n_days_incomplete = thermostat_type_1_with_heating_season.get_season_ignored_days(season_name)
    assert n_days_both == 0
    assert n_days_incomplete == 0
