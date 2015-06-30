from thermostat import Thermostat
from thermostat.metrics import calculate_epa_draft_rccs_field_savings_metrics
from thermostat.metrics import seasonal_metrics_to_csv

import pytest
from uuid import uuid4
import pandas as pd
import numpy as np
import tempfile

from numpy.testing import assert_allclose

@pytest.fixture
def thermostat_type_1():
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
    emergency_heat_cool = np.tile(0,(400,))
    auxiliary_heat_cool = np.tile(0,(400,))

    # heating_season
    temp_in_heat = np.tile(70,(400,))
    temp_out_heat = np.linspace(60,50,num=400)
    setpoints_heat = np.tile(75,(400,))
    ss_heat_pump_cooling_heat = np.tile(0,(400,))
    ss_heat_pump_heating_heat = np.maximum((temp_in_heat - temp_out_heat) * hourly_alpha,0)
    emergency_heat_heat = np.tile(20,(400,))
    auxiliary_heat_heat = np.tile(10,(400,))

    # combine heating and cooling seasons.
    temp_in = pd.Series(np.concatenate((temp_in_cool,temp_in_heat)),index=valid_datetimeindex)
    temp_out = pd.Series(np.concatenate((temp_out_cool,temp_out_heat)),index=valid_datetimeindex)
    setpoints = pd.Series(np.concatenate((setpoints_cool,setpoints_heat)),index=valid_datetimeindex)
    ss_heat_pump_cooling = pd.Series(np.concatenate((ss_heat_pump_cooling_cool,ss_heat_pump_cooling_heat)),index=valid_datetimeindex)
    ss_heat_pump_heating = pd.Series(np.concatenate((ss_heat_pump_heating_cool,ss_heat_pump_heating_heat)),index=valid_datetimeindex)
    emergency_heat = pd.Series(np.concatenate((emergency_heat_cool,emergency_heat_heat)),index=valid_datetimeindex)
    auxiliary_heat = pd.Series(np.concatenate((auxiliary_heat_cool,auxiliary_heat_heat)),index=valid_datetimeindex)

    thermostat_type_1 = Thermostat(valid_thermostat_id,1,valid_zipcode,temp_in,setpoints,temp_out,
            ss_heat_pump_heating=ss_heat_pump_heating,ss_heat_pump_cooling=ss_heat_pump_cooling,
            emergency_heat=emergency_heat,auxiliary_heat=auxiliary_heat)
    return thermostat_type_1


def test_calculate_epa_draft_rccs_field_savings_metrics_type1(thermostat_type_1):
    seasonal_metrics = calculate_epa_draft_rccs_field_savings_metrics(thermostat_type_1)

    cooling_2012 = seasonal_metrics["2012 Cooling Season"]
    heating_2011_12 = seasonal_metrics["2011-2012 Heating Season"]

    assert cooling_2012["ct_identifier"] is not None
    assert heating_2011_12["ct_identifier"] is not None

    assert cooling_2012["zipcode"] == thermostat_type_1.zipcode
    assert heating_2011_12["zipcode"] == thermostat_type_1.zipcode

    assert cooling_2012["equipment_type"] == 1
    assert heating_2011_12["equipment_type"] == 1

    assert_allclose(cooling_2012["baseline_comfort_temperature"],65,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["baseline_comfort_temperature"],75,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["slope_deltaT"],-480,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["slope_dailyavgCDD"],480,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["slope_hourlysumCDD"],480.0,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["intercept_deltaT"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["intercept_dailyavgCDD"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["intercept_hourlysumCDD"],0,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["mean_squared_error_deltaT"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["mean_squared_error_dailyavgCDD"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["mean_squared_error_hourlysumCDD"],0,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["baseline_seasonal_runtime_deltaT"],75260.150,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["baseline_seasonal_runtime_dailyavgCDD"],75260.150,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["baseline_seasonal_runtime_hourlysumCDD"],75260.150,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["actual_seasonal_runtime"],113660.150,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["baseline_daily_runtime_deltaT"],4703.759,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["baseline_daily_runtime_dailyavgCDD"],4703.759,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["baseline_daily_runtime_hourlysumCDD"],4703.759,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["actual_daily_runtime"],7103.759,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["seasonal_savings_deltaT"],0.510,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["seasonal_savings_dailyavgCDD"],0.510,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["seasonal_savings_hourlysumCDD"],0.510,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["seasonal_avoided_runtime_deltaT"],38400,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["seasonal_avoided_runtime_dailyavgCDD"],38400,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["seasonal_avoided_runtime_hourlysumCDD"],38400,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["slope_deltaT"],480.0,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["slope_dailyavgHDD"],480.0,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["slope_hourlysumHDD"],480.0,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["intercept_deltaT"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["intercept_dailyavgHDD"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["intercept_hourlysumHDD"],0,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["mean_squared_error_deltaT"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["mean_squared_error_dailyavgHDD"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["mean_squared_error_hourlysumHDD"],0,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["baseline_seasonal_runtime_deltaT"],76800,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["baseline_seasonal_runtime_dailyavgHDD"],76800,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["baseline_seasonal_runtime_hourlysumHDD"],76800,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["actual_seasonal_runtime"],115200.0,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["baseline_daily_runtime_deltaT"],4800,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["baseline_daily_runtime_dailyavgHDD"],4800,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["baseline_daily_runtime_hourlysumHDD"],4800,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["actual_daily_runtime"],7200.0,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["seasonal_savings_deltaT"],0.5,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["seasonal_savings_dailyavgHDD"],0.5,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["seasonal_savings_hourlysumHDD"],0.5,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["seasonal_avoided_runtime_deltaT"],38400,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["seasonal_avoided_runtime_dailyavgHDD"],38400,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["seasonal_avoided_runtime_hourlysumHDD"],38400,rtol=1e-3,atol=1e-3)

    for low,high in [(i,i+5) for i in range(0,60,5)]:
        label = "rhu_{:02d}F_to_{:02d}F".format(low,high)
        assert_allclose(heating_2011_12[label],0.0937,rtol=1e-3,atol=1e-3)

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

    assert_allclose(cooling_2012["slope_deltaT"],-480,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["slope_dailyavgCDD"],480,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["slope_hourlysumCDD"],480.0,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["intercept_deltaT"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["intercept_dailyavgCDD"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["intercept_hourlysumCDD"],0,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["mean_squared_error_deltaT"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["mean_squared_error_dailyavgCDD"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["mean_squared_error_hourlysumCDD"],0,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["baseline_seasonal_runtime_deltaT"],75260.150,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["baseline_seasonal_runtime_dailyavgCDD"],75260.150,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["baseline_seasonal_runtime_hourlysumCDD"],75260.150,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["actual_seasonal_runtime"],113660.150,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["baseline_daily_runtime_deltaT"],4703.759,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["baseline_daily_runtime_dailyavgCDD"],4703.759,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["baseline_daily_runtime_hourlysumCDD"],4703.759,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["actual_daily_runtime"],7103.759,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["seasonal_savings_deltaT"],0.510,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["seasonal_savings_dailyavgCDD"],0.510,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["seasonal_savings_hourlysumCDD"],0.510,rtol=1e-3,atol=1e-3)

    assert_allclose(cooling_2012["seasonal_avoided_runtime_deltaT"],38400,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["seasonal_avoided_runtime_dailyavgCDD"],38400,rtol=1e-3,atol=1e-3)
    assert_allclose(cooling_2012["seasonal_avoided_runtime_hourlysumCDD"],38400,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["slope_deltaT"],480.0,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["slope_dailyavgHDD"],480.0,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["slope_hourlysumHDD"],480.0,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["intercept_deltaT"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["intercept_dailyavgHDD"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["intercept_hourlysumHDD"],0,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["mean_squared_error_deltaT"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["mean_squared_error_dailyavgHDD"],0,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["mean_squared_error_hourlysumHDD"],0,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["baseline_seasonal_runtime_deltaT"],76800,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["baseline_seasonal_runtime_dailyavgHDD"],76800,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["baseline_seasonal_runtime_hourlysumHDD"],76800,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["actual_seasonal_runtime"],115200.0,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["baseline_daily_runtime_deltaT"],4800,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["baseline_daily_runtime_dailyavgHDD"],4800,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["baseline_daily_runtime_hourlysumHDD"],4800,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["actual_daily_runtime"],7200.0,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["seasonal_savings_deltaT"],0.5,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["seasonal_savings_dailyavgHDD"],0.5,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["seasonal_savings_hourlysumHDD"],0.5,rtol=1e-3,atol=1e-3)

    assert_allclose(heating_2011_12["seasonal_avoided_runtime_deltaT"],38400,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["seasonal_avoided_runtime_dailyavgHDD"],38400,rtol=1e-3,atol=1e-3)
    assert_allclose(heating_2011_12["seasonal_avoided_runtime_hourlysumHDD"],38400,rtol=1e-3,atol=1e-3)

    for low,high in [(i,i+5) for i in range(0,60,5)]:
        label = "rhu_{:02d}F_to_{:02d}F".format(low,high)
        assert heating_2011_12[label] is None

def test_seasonal_metrics_to_csv(thermostat_type_1):
    fd, fname = tempfile.mkstemp()
    seasonal_metrics = calculate_epa_draft_rccs_field_savings_metrics(thermostat_type_1)
    seasonal_metrics_to_csv(seasonal_metrics,fname)
    with open(fname,'r') as f:
        lines = f.readlines()
        assert len(lines) == 3
        for line in lines:
            assert len(line.split(',')) == 54
