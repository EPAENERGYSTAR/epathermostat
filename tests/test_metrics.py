from thermostat import Thermostat
from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path
from thermostat.exporters import seasonal_metrics_to_csv

import pandas as pd
import numpy as np
from numpy.testing import assert_allclose

import tempfile

import pytest

RTOL = 1e-3
ATOL = 1e-3

@pytest.fixture(params=["metadata.csv"])
def metadata_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["interval_data.csv"])
def interval_data_filename(request):
    return get_data_path(request.param)

@pytest.fixture
def thermostat(metadata_filename, interval_data_filename):
    thermostats = from_csv(metadata_filename, interval_data_filename)
    return thermostats[0]

def test_calculate_epa_draft_rccs_field_savings_metrics(thermostat):
    seasonal_metrics = thermostat.calculate_epa_draft_rccs_field_savings_metrics()

    assert len(seasonal_metrics) == 9

    cooling_season_outputs = seasonal_metrics[0]
    assert cooling_season_outputs['season_name'] == '2011 Cooling'
    assert cooling_season_outputs['ct_identifier'] == 'test'
    assert cooling_season_outputs['zipcode'] =='91104'

    assert_allclose(cooling_season_outputs['equipment_type'], 1, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['n_days_both_heating_and_cooling'], 65, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['n_days_insufficient_data'], 4, rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['slope_deltaT'], -2405.618, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['alpha_est_dailyavgCDD'], 2306.649, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['alpha_est_hourlysumCDD'], 2635.493, rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['deltaT_base_est_dailyavgCDD'], 0.243, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['deltaT_base_est_hourlysumCDD'], -0.770, rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['mean_squared_error_deltaT'], 1058435.360, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['mean_sq_err_dailyavgCDD'], 985500.273, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['mean_sq_err_hourlysumCDD'], 1220265.285, rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['baseline_comfort_temperature'], 75.0, rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['actual_daily_runtime'], 10599.225, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['baseline_daily_runtime_deltaT'], 7082.037, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['baseline_daily_runtime_dailyavgCDD'], 12989.397, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['baseline_daily_runtime_hourlysumCDD'], 7029.208, rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['actual_seasonal_runtime'], 423969.0, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['baseline_seasonal_runtime_deltaT'], 283281.489, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['baseline_seasonal_runtime_dailyavgCDD'], 519575.897, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['baseline_seasonal_runtime_hourlysumCDD'], 281168.351, rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['seasonal_avoided_runtime_deltaT'], 140687.510, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['seasonal_avoided_runtime_dailyavgCDD'], -95606.897, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['seasonal_avoided_runtime_hourlysumCDD'], 142800.648, rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['seasonal_savings_deltaT'], 0.496, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['seasonal_savings_dailyavgCDD'], -0.184, rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['seasonal_savings_hourlysumCDD'], 0.507, rtol=RTOL, atol=ATOL)

    heating_season_outputs = seasonal_metrics[4]

    assert heating_season_outputs['season_name'] == '2010-2011 Heating'
    assert heating_season_outputs['ct_identifier'] == 'test'
    assert heating_season_outputs['zipcode'] == '91104'
    assert_allclose(heating_season_outputs['seasonal_avoided_runtime_dailyavgHDD'], 412533.647, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['seasonal_savings_hourlysumHDD'], 0.437, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['baseline_seasonal_runtime_hourlysumHDD'], 1797180.271, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_30F_to_35F'], 0.0, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_20F_to_25F'], 0.0, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['seasonal_savings_dailyavgHDD'], 0.189, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_25F_to_30F'], 0.0, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['baseline_daily_runtime_deltaT'], 15513.253, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['baseline_seasonal_runtime_deltaT'], 2171855.459, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['mean_sq_err_hourlysumHDD'], 882030.507, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['mean_squared_error_deltaT'], 369356.647, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_00F_to_05F'], 0.0, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['seasonal_avoided_runtime_deltaT'], 412250.540, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['baseline_daily_runtime_dailyavgHDD'], 15511.231, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_45F_to_50F'], 0.032, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['seasonal_avoided_runtime_hourlysumHDD'], 786925.728, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_40F_to_45F'], 0.0, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['slope_deltaT'], 2400.482, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['actual_seasonal_runtime'], 2584106.0, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_35F_to_40F'], 0.0, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['alpha_est_hourlysumHDD'], 2582.295, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['deltaT_base_est_dailyavgHDD'], -0.001, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['mean_sq_err_dailyavgHDD'], 369354.946, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_05F_to_10F'], 0.0, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['seasonal_savings_deltaT'], 0.189, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_50F_to_55F'], 0.032, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['alpha_est_dailyavgHDD'], 2400.238, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_55F_to_60F'], 0.0214, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_10F_to_15F'], 0.0, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['equipment_type'], 1, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['n_days_insufficient_data'], 2, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['baseline_seasonal_runtime_dailyavgHDD'], 2171572.352, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['baseline_comfort_temperature'], 66.0, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['deltaT_base_est_hourlysumHDD'], 0.428, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['baseline_daily_runtime_hourlysumHDD'], 12837.002, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['n_days_both_heating_and_cooling'], 22, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['actual_daily_runtime'], 18457.900, rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_15F_to_20F'], 0.0, rtol=RTOL, atol=ATOL)

def test_seasonal_metrics_to_csv(thermostat):
    fd, fname = tempfile.mkstemp()
    seasonal_metrics = thermostat.calculate_epa_draft_rccs_field_savings_metrics()
    seasonal_metrics_to_csv(seasonal_metrics, fname)
    with open(fname,'r') as f:
        lines = f.readlines()
        assert len(lines) == 10
        for line in lines:
            assert len(line.split(',')) == 55
