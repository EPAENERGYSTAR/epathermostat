from thermostat.baseline import get_cooling_season_baseline_setpoints
from thermostat.baseline import get_heating_season_baseline_setpoints
from thermostat.baseline import get_cooling_season_baseline_cooling_demand
from thermostat.baseline import get_heating_season_baseline_heating_demand
from thermostat.demand import get_cooling_demand
from thermostat.demand import get_heating_demand
from thermostat.regression import runtime_regression
from thermostat.savings import get_daily_avoided_runtime
from thermostat.savings import get_total_baseline_cooling_runtime
from thermostat.savings import get_total_baseline_heating_runtime
from thermostat.savings import get_seasonal_percent_savings

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

def test_get_daily_avoided_runtime_cooling_deltaT(valid_thermostat_id,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(80,90,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(65,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.maximum((temp_out - temp_in) * hourly_alpha,0),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)

    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    baseline_setpoints = get_cooling_season_baseline_setpoints(thermostat_type_2,cooling_season)
    baseline_deltaT = get_cooling_season_baseline_cooling_demand(thermostat_type_2,cooling_season,baseline_setpoints,method="deltaT")
    deltaT = get_cooling_demand(thermostat_type_2,cooling_season,method="deltaT")
    deltaT = -deltaT

    hourly_runtime = ss_heat_pump_cooling[cooling_season]
    slope,intercept, mean_sq_err = runtime_regression(hourly_runtime,deltaT)

    avoided_runtime = get_daily_avoided_runtime(slope,deltaT,baseline_deltaT)

    assert_allclose(avoided_runtime,np.tile(2400,(16,)),rtol=1e-3,atol=1e-3)


def test_get_daily_avoided_runtime_heating_deltaT(valid_thermostat_id,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(60,50,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(75,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.maximum((temp_in - temp_out) * hourly_alpha,0),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)

    heating_season, name = thermostat_type_2.get_heating_seasons()[0]
    baseline_setpoints = get_heating_season_baseline_setpoints(thermostat_type_2,heating_season)
    baseline_deltaT = get_heating_season_baseline_heating_demand(thermostat_type_2,heating_season,baseline_setpoints,method="deltaT")
    deltaT = get_heating_demand(thermostat_type_2,heating_season,method="deltaT")

    hourly_runtime = ss_heat_pump_heating[heating_season]
    slope, intercept, mean_sq_err = runtime_regression(hourly_runtime,deltaT)

    avoided_runtime = get_daily_avoided_runtime(slope,deltaT,baseline_deltaT)

    assert_allclose(avoided_runtime,np.tile(2400,(16,)),rtol=1e-3,atol=1e-3)

def test_get_daily_avoided_runtime_dailyavgCDD(valid_thermostat_id,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(80,90,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(65,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.maximum((temp_out - temp_in) * hourly_alpha,0),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)

    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    dailyavgCDD,deltaT_base_est,alpha_est,mean_sq_err = get_cooling_demand(thermostat_type_2,cooling_season,method="dailyavgCDD")

    baseline_setpoints = get_cooling_season_baseline_setpoints(thermostat_type_2,cooling_season)
    baseline_dailyavgCDD = get_cooling_season_baseline_cooling_demand(thermostat_type_2,cooling_season,baseline_setpoints,deltaT_base_est,method="dailyavgCDD")

    hourly_runtime = ss_heat_pump_cooling[cooling_season]
    slope,intercept, mean_sq_err = runtime_regression(hourly_runtime,dailyavgCDD)

    avoided_runtime = get_daily_avoided_runtime(slope,dailyavgCDD,baseline_dailyavgCDD)

    assert_allclose(avoided_runtime,np.tile(2400,(16,)),rtol=1e-3,atol=1e-3)

def test_get_daily_avoided_runtime_dailyavgHDD(valid_thermostat_id,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(60,50,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(75,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.maximum((temp_in - temp_out) * hourly_alpha,0),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)

    heating_season, name = thermostat_type_2.get_heating_seasons()[0]
    dailyavgHDD,deltaT_base_est,alpha_est,mean_sq_err = get_heating_demand(thermostat_type_2,heating_season,method="dailyavgHDD")

    baseline_setpoints = get_heating_season_baseline_setpoints(thermostat_type_2,heating_season)
    baseline_dailyavgHDD = get_heating_season_baseline_heating_demand(thermostat_type_2,heating_season,baseline_setpoints,deltaT_base_est,method="dailyavgHDD")

    hourly_runtime = ss_heat_pump_heating[heating_season]
    slope, intercept, mean_sq_err = runtime_regression(hourly_runtime,dailyavgHDD)

    avoided_runtime = get_daily_avoided_runtime(slope,dailyavgHDD,baseline_dailyavgHDD)

    assert_allclose(avoided_runtime,np.tile(2400,(16,)),rtol=1e-3,atol=1e-3)

def test_get_daily_avoided_runtime_hourlysumCDD(valid_thermostat_id,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(80,90,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(65,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.maximum((temp_out - temp_in) * hourly_alpha,0),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)

    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    hourlysumCDD,deltaT_base_est,alpha_est,mean_sq_err = get_cooling_demand(thermostat_type_2,cooling_season,method="hourlysumCDD")

    baseline_setpoints = get_cooling_season_baseline_setpoints(thermostat_type_2,cooling_season)
    baseline_hourlysumCDD = get_cooling_season_baseline_cooling_demand(thermostat_type_2,cooling_season,baseline_setpoints,deltaT_base_est,method="hourlysumCDD")

    hourly_runtime = ss_heat_pump_cooling[cooling_season]
    slope,intercept, mean_sq_err = runtime_regression(hourly_runtime,hourlysumCDD)

    avoided_runtime = get_daily_avoided_runtime(slope,hourlysumCDD,baseline_hourlysumCDD)

    assert_allclose(avoided_runtime,np.tile(2400,(16,)),rtol=1e-3,atol=1e-3)

def test_get_daily_avoided_runtime_hourlysumHDD(valid_thermostat_id,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(60,50,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(75,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.maximum((temp_in - temp_out) * hourly_alpha,0),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)

    heating_season, name = thermostat_type_2.get_heating_seasons()[0]
    hourlysumHDD,deltaT_base_est,alpha_est,mean_sq_err = get_heating_demand(thermostat_type_2,heating_season,method="hourlysumHDD")

    baseline_setpoints = get_heating_season_baseline_setpoints(thermostat_type_2,heating_season)
    baseline_hourlysumHDD = get_heating_season_baseline_heating_demand(thermostat_type_2,heating_season,baseline_setpoints,deltaT_base_est,method="hourlysumHDD")

    hourly_runtime = ss_heat_pump_heating[heating_season]
    slope, intercept, mean_sq_err = runtime_regression(hourly_runtime,hourlysumHDD)

    avoided_runtime = get_daily_avoided_runtime(slope,hourlysumHDD,baseline_hourlysumHDD)

    assert_allclose(avoided_runtime,np.tile(2400,(16,)),rtol=1e-3,atol=1e-3)

def test_get_total_baseline_runtime_dailyavgCDD(valid_thermostat_id,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(80,90,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(65,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.maximum((temp_out - temp_in) * hourly_alpha,0),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)

    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    dailyavgCDD,deltaT_base_est,alpha_est,mean_sq_err = get_cooling_demand(thermostat_type_2,cooling_season,method="dailyavgCDD")

    baseline_setpoints = get_cooling_season_baseline_setpoints(thermostat_type_2,cooling_season)
    baseline_dailyavgCDD = get_cooling_season_baseline_cooling_demand(thermostat_type_2,cooling_season,baseline_setpoints,deltaT_base_est,method="dailyavgCDD")

    hourly_runtime = ss_heat_pump_cooling[cooling_season]
    slope,intercept, mean_sq_err = runtime_regression(hourly_runtime,dailyavgCDD)

    avoided_runtime = get_daily_avoided_runtime(slope,dailyavgCDD,baseline_dailyavgCDD)

    total_baseline_cooling_runtime = \
            get_total_baseline_cooling_runtime(thermostat_type_2,cooling_season,avoided_runtime)

    assert_allclose(total_baseline_cooling_runtime,75260.150,rtol=1e-3,atol=1e-3)

def test_get_total_baseline_runtime_dailyavgHDD(valid_thermostat_id,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(60,50,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(75,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.maximum((temp_in - temp_out) * hourly_alpha,0),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)

    heating_season, name = thermostat_type_2.get_heating_seasons()[0]
    dailyavgHDD,deltaT_base_est,alpha_est,mean_sq_err = get_heating_demand(thermostat_type_2,heating_season,method="dailyavgHDD")

    baseline_setpoints = get_heating_season_baseline_setpoints(thermostat_type_2,heating_season)
    baseline_dailyavgHDD = get_heating_season_baseline_heating_demand(thermostat_type_2,heating_season,baseline_setpoints,deltaT_base_est,method="dailyavgHDD")

    hourly_runtime = ss_heat_pump_heating[heating_season]
    slope, intercept, mean_sq_err = runtime_regression(hourly_runtime,dailyavgHDD)

    avoided_runtime = get_daily_avoided_runtime(slope,dailyavgHDD,baseline_dailyavgHDD)

    total_baseline_heating_runtime = \
            get_total_baseline_heating_runtime(thermostat_type_2,heating_season,avoided_runtime)

    assert_allclose(total_baseline_heating_runtime,75260.150,rtol=1e-3,atol=1e-3)

def test_get_seasonal_percent_savings_dailyavgCDD(valid_thermostat_id,valid_datetimeindex):
    temp_in = pd.Series(np.tile(70,(400,)),index=valid_datetimeindex)
    temp_out = pd.Series(np.linspace(80,90,num=400),index=valid_datetimeindex)
    setpoints = pd.Series(np.tile(65,(400,)),index=valid_datetimeindex)

    hourly_alpha = 20

    ss_heat_pump_cooling = pd.Series(np.maximum((temp_out - temp_in) * hourly_alpha,0),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.tile(0,(400,)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)

    cooling_season, name = thermostat_type_2.get_cooling_seasons()[0]
    dailyavgCDD,deltaT_base_est,alpha_est,mean_sq_err = get_cooling_demand(thermostat_type_2,cooling_season,method="dailyavgCDD")

    baseline_setpoints = get_cooling_season_baseline_setpoints(thermostat_type_2,cooling_season)
    baseline_dailyavgCDD = get_cooling_season_baseline_cooling_demand(thermostat_type_2,cooling_season,baseline_setpoints,deltaT_base_est,method="dailyavgCDD")

    hourly_runtime = ss_heat_pump_cooling[cooling_season]
    slope,intercept, mean_sq_err = runtime_regression(hourly_runtime,dailyavgCDD)

    avoided_runtime = get_daily_avoided_runtime(slope,dailyavgCDD,baseline_dailyavgCDD)

    total_baseline_cooling_runtime = \
            get_total_baseline_cooling_runtime(thermostat_type_2,cooling_season,avoided_runtime)

    seasonal_percent_savings = get_seasonal_percent_savings(total_baseline_cooling_runtime,avoided_runtime)

    assert_allclose(seasonal_percent_savings,0.510,rtol=1e-3,atol=1e-3)

