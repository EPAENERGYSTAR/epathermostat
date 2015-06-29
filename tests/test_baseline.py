from thermostat.baseline import get_cooling_season_baseline_setpoints
from thermostat.baseline import get_heating_season_baseline_setpoints
from thermostat.baseline import get_cooling_season_baseline_cooling_demand
from thermostat.baseline import get_heating_season_baseline_heating_demand
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

def test_get_cooling_season_baseline_deltaT(valid_thermostat_id,valid_temperature_in,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(80,90,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(65,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.maximum((temp_out - temp_in) * hourly_alpha,0),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,
            ss_heat_pump_cooling=ss_heat_pump_cooling)

    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    baseline_setpoints = get_cooling_season_baseline_setpoints(thermostat_type_2,cooling_season)
    baseline_deltaT = get_cooling_season_baseline_cooling_demand(thermostat_type_2,cooling_season,baseline_setpoints,method="deltaT")

    assert_allclose(baseline_deltaT.values, [15.288, 15.889, 16.491, 17.092,
                                             17.694, 18.295, 18.897, 19.498,
                                             20.100, 20.701, 21.303, 21.904,
                                             22.506, 23.107, 23.709, 24.310],rtol=1e-3, atol=1e-3)

def test_get_heating_season_baseline_deltaT(valid_thermostat_id,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(60,50,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(75,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.maximum((temp_in - temp_out) * hourly_alpha,0),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,
            ss_heat_pump_cooling=ss_heat_pump_cooling)

    heating_season, name = thermostat_type_2.get_heating_seasons()[0]
    baseline_setpoints = get_heating_season_baseline_setpoints(thermostat_type_2,heating_season)
    baseline_deltaT = get_heating_season_baseline_heating_demand(thermostat_type_2,heating_season,baseline_setpoints,method="deltaT")

    assert_allclose(baseline_deltaT.values, [15.288, 15.889, 16.491, 17.092,
                                             17.694, 18.295, 18.897, 19.498,
                                             20.100, 20.701, 21.303, 21.904,
                                             22.506, 23.107, 23.709, 24.310],rtol=1e-3, atol=1e-3)

def test_get_cooling_season_baseline_cdd_dailyavg(valid_thermostat_id,valid_temperature_in,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(80,90,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(65,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.maximum((temp_out - temp_in) * hourly_alpha,0),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,
            ss_heat_pump_cooling=ss_heat_pump_cooling)

    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    baseline_setpoints = get_cooling_season_baseline_setpoints(thermostat_type_2,cooling_season)
    deltaT_base_fake = 0
    baseline_cdd = get_cooling_season_baseline_cooling_demand(thermostat_type_2,cooling_season,baseline_setpoints,deltaT_base_fake,method="dailyavgCDD")

    assert_allclose(baseline_cdd.values, [15.288, 15.889, 16.491, 17.092,
                                          17.694, 18.295, 18.897, 19.498,
                                          20.100, 20.701, 21.303, 21.904,
                                          22.506, 23.107, 23.709, 24.310],rtol=1e-3, atol=1e-3)

def test_get_heating_season_baseline_hdd_dailyavg(valid_thermostat_id,valid_temperature_in,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(60,50,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(75,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.maximum((temp_in - temp_out) * hourly_alpha,0),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,
            ss_heat_pump_cooling=ss_heat_pump_cooling)

    heating_season, name = thermostat_type_2.get_heating_seasons()[0]
    baseline_setpoints = get_heating_season_baseline_setpoints(thermostat_type_2,heating_season)
    deltaT_base_fake = 0
    baseline_hdd = get_heating_season_baseline_heating_demand(thermostat_type_2,heating_season,baseline_setpoints,deltaT_base_fake,method="dailyavgHDD")

    assert_allclose(baseline_hdd.values, [15.288, 15.889, 16.491, 17.092,
                                          17.694, 18.295, 18.897, 19.498,
                                          20.100, 20.701, 21.303, 21.904,
                                          22.506, 23.107, 23.709, 24.310],rtol=1e-3, atol=1e-3)

def test_get_cooling_season_baseline_cdd_dailyavg(valid_thermostat_id,valid_temperature_in,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(80,90,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(65,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.maximum((temp_out - temp_in) * hourly_alpha,0),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,
            ss_heat_pump_cooling=ss_heat_pump_cooling)

    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    baseline_setpoints = get_cooling_season_baseline_setpoints(thermostat_type_2,cooling_season)
    deltaT_base_fake = 0
    baseline_cdd = get_cooling_season_baseline_cooling_demand(thermostat_type_2,cooling_season,baseline_setpoints,deltaT_base_fake,method="hourlysumCDD")

    assert_allclose(baseline_cdd.values, [15.288, 15.889, 16.491, 17.092,
                                          17.694, 18.295, 18.897, 19.498,
                                          20.100, 20.701, 21.303, 21.904,
                                          22.506, 23.107, 23.709, 24.310],rtol=1e-3, atol=1e-3)

def test_get_heating_season_baseline_hdd_dailyavg(valid_thermostat_id,valid_temperature_in,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(60,50,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(75,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.maximum((temp_in - temp_out) * hourly_alpha,0),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,
            ss_heat_pump_cooling=ss_heat_pump_cooling)

    heating_season, name = thermostat_type_2.get_heating_seasons()[0]
    baseline_setpoints = get_heating_season_baseline_setpoints(thermostat_type_2,heating_season)
    deltaT_base_fake = 0
    baseline_hdd = get_heating_season_baseline_heating_demand(thermostat_type_2,heating_season,baseline_setpoints,deltaT_base_fake,method="hourlysumHDD")

    assert_allclose(baseline_hdd.values, [15.288, 15.889, 16.491, 17.092,
                                          17.694, 18.295, 18.897, 19.498,
                                          20.100, 20.701, 21.303, 21.904,
                                          22.506, 23.107, 23.709, 24.310],rtol=1e-3, atol=1e-3)

