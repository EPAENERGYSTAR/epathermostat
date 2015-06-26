from thermostat.baseline import get_cooling_season_baseline_setpoints
from thermostat.baseline import get_heating_season_baseline_setpoints
from thermostat.baseline import get_cooling_season_baseline_cdd
from thermostat.baseline import get_heating_season_baseline_hdd
from thermostat import Thermostat
import pytest
import pandas as pd
import numpy as np
from numpy.testing import assert_allclose

@pytest.fixture
def valid_thermostat_id():
    return "10912098123"

@pytest.fixture
def valid_datetimeindex():
    return pd.DatetimeIndex(start="2012-01-01T00:00:00",freq='H',periods=400)

@pytest.fixture
def valid_temperature_in(valid_datetimeindex):
    return pd.Series(np.zeros((400,)),index=valid_datetimeindex)

@pytest.fixture
def valid_temperature_out(valid_datetimeindex):
    return pd.Series(np.zeros((400,)),index=valid_datetimeindex)

RTOL = 1e-6
ATOL = 1e-6

def test_get_cooling_season_baseline_setpoints(valid_thermostat_id,valid_temperature_in,valid_temperature_out,valid_datetimeindex):

    setpoints = pd.Series(np.arange(0,100,.25),index=valid_datetimeindex)
    ss_heat_pump_cooling = pd.Series(np.tile(3600,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    thermostat_type_2 = Thermostat(valid_thermostat_id,2,valid_temperature_in,setpoints,valid_temperature_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)

    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    baseline = get_cooling_season_baseline_setpoints(thermostat_type_2,cooling_season)

    assert_allclose(baseline.values, np.tile(9.575,(400,)),rtol=RTOL,atol=ATOL)
    assert all(baseline.index == valid_datetimeindex)

def test_get_heating_season_baseline_setpoints(valid_thermostat_id,valid_temperature_in,valid_temperature_out,valid_datetimeindex):

    setpoints = pd.Series(np.arange(0,100,.25),index=valid_datetimeindex)
    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(3600,(400,)),index=valid_datetimeindex)
    thermostat_type_2 = Thermostat(valid_thermostat_id,2,valid_temperature_in,setpoints,valid_temperature_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)

    heating_season, name = thermostat_type_2.get_heating_seasons()[0]
    baseline = get_heating_season_baseline_setpoints(thermostat_type_2,heating_season)

    assert_allclose(baseline.values, np.tile(86.175,(400,)),rtol=RTOL,atol=ATOL)
    assert all(baseline.index == valid_datetimeindex)

def test_get_cooling_season_baseline_cdd_dailyavg(valid_thermostat_id,valid_temperature_in,valid_datetimeindex):
    setpoints = pd.Series(np.arange(0,100,.25),index=valid_datetimeindex)

    ss_heat_pump_cooling = pd.Series(np.tile(3600,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    temp_out = pd.Series(np.tile(100,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,valid_temperature_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)
    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    baseline_setpoints = get_cooling_season_baseline_setpoints(thermostat_type_2,cooling_season)
    baseline_cdd = get_cooling_season_baseline_cdd(thermostat_type_2,cooling_season,baseline_setpoints,method="dailyavgCDD")

    assert_allclose(baseline_cdd.values, np.tile(90.425,(16,)))

def test_get_heating_season_baseline_hdd_dailyavg(valid_thermostat_id,valid_temperature_in,valid_datetimeindex):
    setpoints = pd.Series(np.arange(0,100,.25),index=valid_datetimeindex)

    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(3600,(400,)),index=valid_datetimeindex)

    temp_out = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,valid_temperature_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)
    heating_season, name = thermostat_type_2.get_heating_seasons()[0]
    baseline_setpoints = get_heating_season_baseline_setpoints(thermostat_type_2,heating_season)
    baseline_hdd = get_heating_season_baseline_hdd(thermostat_type_2,heating_season,baseline_setpoints,method="dailyavgHDD")

    assert_allclose(baseline_hdd.values, np.tile(86.175,(16,)))

def test_get_cooling_season_baseline_cdd_hourlysum(valid_thermostat_id,valid_temperature_in,valid_datetimeindex):
    setpoints = pd.Series(np.arange(0,100,.25),index=valid_datetimeindex)

    ss_heat_pump_cooling = pd.Series(np.tile(3600,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    temp_out = pd.Series(np.tile(100,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,valid_temperature_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)
    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    baseline_setpoints = get_cooling_season_baseline_setpoints(thermostat_type_2,cooling_season)
    baseline_cdd = get_cooling_season_baseline_cdd(thermostat_type_2,cooling_season,baseline_setpoints,method="hourlysumCDD")

    assert_allclose(baseline_cdd.values, np.tile(90.425,(16,)))

def test_get_heating_season_baseline_hdd_hourlysum(valid_thermostat_id,valid_temperature_in,valid_datetimeindex):
    setpoints = pd.Series(np.arange(0,100,.25),index=valid_datetimeindex)

    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(3600,(400,)),index=valid_datetimeindex)

    temp_out = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,valid_temperature_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)
    heating_season, name = thermostat_type_2.get_heating_seasons()[0]
    baseline_setpoints = get_heating_season_baseline_setpoints(thermostat_type_2,heating_season)
    baseline_hdd = get_heating_season_baseline_hdd(thermostat_type_2,heating_season,baseline_setpoints,method="hourlysumHDD")

    assert_allclose(baseline_hdd.values, np.tile(86.175,(16,)))
