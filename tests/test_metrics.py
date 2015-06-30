from thermostat import Thermostat
from thermostat.metrics import calculate_epa_draft_rccs_field_savings_metrics

import pytest
from uuid import uuid4
import pandas as pd
import numpy as np

from numpy.testing import assert_allclose

def test_calculate_epa_draft_rccs_field_savings_metrics_type2():
    valid_thermostat_id = uuid4()
    valid_datetimeindex = pd.DatetimeIndex(start="2012-01-01T00:00:00",freq='H',periods=800)
    valid_zipcode = "01234"

    hourly_alpha = 20
    daily_alpha = hourly_alpha * 24

    #cooling season
    temp_in_cool = np.tile(70,(400,))
    temp_out_cool = np.linspace(80,90,num=400)
    setpoints_cool = np.tile(65,(400,))
    ss_heat_pump_cooling_cool = np.maximum((temp_out_cool - temp_in_cool) * hourly_alpha,0)
    ss_heat_pump_heating_cool = np.tile(0,(400,))

    # heating_season
    temp_in_heat = np.tile(70,(400,))
    temp_out_heat = np.linspace(60,50,num=400)
    setpoints_heat = np.tile(75,(400,))
    ss_heat_pump_cooling_heat = np.tile(0,(400,))
    ss_heat_pump_heating_heat = np.maximum((temp_in_heat - temp_out_heat) * hourly_alpha,0)

    # combine heating and cooling seasons.
    temp_in = pd.Series(np.concatenate((temp_in_cool,temp_in_heat)),index=valid_datetimeindex)
    temp_out = pd.Series(np.concatenate((temp_out_cool,temp_out_heat)),index=valid_datetimeindex)
    setpoints = pd.Series(np.concatenate((setpoints_cool,setpoints_heat)),index=valid_datetimeindex)
    ss_heat_pump_cooling = pd.Series(np.concatenate((ss_heat_pump_cooling_cool,ss_heat_pump_cooling_heat)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.concatenate((ss_heat_pump_heating_cool,ss_heat_pump_heating_heat)),index=valid_datetimeindex)

    thermostat_type_2 = Thermostat(valid_thermostat_id,2,valid_zipcode,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling)

    seasonal_metrics = calculate_epa_draft_rccs_field_savings_metrics(thermostat_type_2)

    cooling_2012 = seasonal_metrics["2012 Cooling Season"]
    heating_2011_12 = seasonal_metrics["2011-2012 Heating Season"]

    assert cooling_2012["ct_identifier"] is not None
    assert heating_2011_12["ct_identifier"] is not None

    assert cooling_2012["zipcode"] == valid_zipcode
    assert heating_2011_12["zipcode"] == valid_zipcode

    assert cooling_2012["equipment_type"] == 2
    assert heating_2011_12["equipment_type"] == 2

    assert_allclose(cooling_2012["baseline_comfort_temperature"],65,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["baseline_comfort_temperature"],75,rtol=1e-3,atol=1e-3)


    assert_allclose(cooling_2012["slope_deltaT"],-428.494,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["slope_dailyavgCDD"],428.494,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["slope_hourlysumCDD"],480.0,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["intercept_deltaT"],842.191,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["intercept_dailyavgCDD"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["intercept_hourlysumCDD"],0,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["mean_squared_error_deltaT"],121426.673,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["mean_squared_error_dailyavgCDD"],121426.673,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["mean_squared_error_hourlysumCDD"],0,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["baseline_seasonal_runtime_deltaT"],83577.981,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["baseline_seasonal_runtime_dailyavgCDD"],112212.498,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["baseline_seasonal_runtime_hourlysumCDD"],80000.0,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["actual_seasonal_runtime"],120000,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["baseline_daily_runtime_deltaT"],4916.351,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["baseline_daily_runtime_dailyavgCDD"],6600.735,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["baseline_daily_runtime_hourlysumCDD"],4705.882,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["actual_daily_runtime"],7058.823,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["seasonal_savings_deltaT"],0.435,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["seasonal_savings_dailyavgCDD"],0.069,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["seasonal_savings_hourlysumCDD"],0.5,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["seasonal_avoided_runtime_deltaT"],2142.471,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["seasonal_avoided_runtime_dailyavgCDD"],458.088,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["seasonal_avoided_runtime_hourlysumCDD"],2352.941,rtol=1e-3,atol=1e-3)
