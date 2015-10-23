from thermostat.exporters import seasonal_metrics_to_csv

import pandas as pd
import numpy as np
from numpy.testing import assert_allclose

import tempfile

import pytest

from fixtures.thermostats import thermostat_type_1
from fixtures.thermostats import thermostat_type_2
from fixtures.thermostats import thermostat_type_3
from fixtures.thermostats import thermostat_type_4
from fixtures.thermostats import thermostat_type_5
from fixtures.thermostats import seasonal_metrics_type_1
from fixtures.thermostats import seasonal_metrics_type_1_data

RTOL = 1e-3
ATOL = 1e-3


def test_calculate_epa_draft_rccs_field_savings_metrics_type_1(seasonal_metrics_type_1, seasonal_metrics_type_1_data):
    assert len(seasonal_metrics_type_1) == seasonal_metrics_type_1_data["n_seasons"]

    cooling_season_outputs = seasonal_metrics_type_1[0]
    assert cooling_season_outputs['ct_identifier'] == seasonal_metrics_type_1_data['ct_identifier']
    assert cooling_season_outputs['equipment_type'] == seasonal_metrics_type_1_data['equipment_type']
    assert cooling_season_outputs['zipcode'] == seasonal_metrics_type_1_data['zipcode']
    assert cooling_season_outputs['station'] == seasonal_metrics_type_1_data['station']

    assert cooling_season_outputs['season_name'] == seasonal_metrics_type_1_data['cooling']['season_name']
    assert_allclose(cooling_season_outputs['n_days_both_heating_and_cooling'],
            seasonal_metrics_type_1_data['cooling']['n_days_both_heating_and_cooling'], rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['n_days_insufficient_data'],
            seasonal_metrics_type_1_data['cooling']['n_days_insufficient_data'], rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['slope_deltaT'],
            seasonal_metrics_type_1_data['cooling']['slope_deltaT'], rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['alpha_est_dailyavgCDD'],
            seasonal_metrics_type_1_data['cooling']['alpha_est_dailyavgCDD'], rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['alpha_est_hourlyavgCDD'],
            seasonal_metrics_type_1_data['cooling']['alpha_est_hourlyavgCDD'], rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['deltaT_base_est_dailyavgCDD'],
            seasonal_metrics_type_1_data['cooling']['deltaT_base_est_dailyavgCDD'], rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['deltaT_base_est_hourlyavgCDD'],
            seasonal_metrics_type_1_data['cooling']['deltaT_base_est_hourlyavgCDD'], rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['mean_squared_error_deltaT'],
            seasonal_metrics_type_1_data['cooling']['mean_squared_error_deltaT'], rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['mean_sq_err_dailyavgCDD'],
            seasonal_metrics_type_1_data['cooling']['mean_sq_err_dailyavgCDD'], rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['mean_sq_err_hourlyavgCDD'],
            seasonal_metrics_type_1_data['cooling']['mean_sq_err_hourlyavgCDD'], rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['baseline_comfort_temperature'],
            seasonal_metrics_type_1_data['cooling']['baseline_comfort_temperature'], rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['actual_daily_runtime'],
            seasonal_metrics_type_1_data['cooling']['actual_daily_runtime'], rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['actual_seasonal_runtime'],
            seasonal_metrics_type_1_data['cooling']['actual_seasonal_runtime'], rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['baseline_daily_runtime_deltaT'],
            seasonal_metrics_type_1_data['cooling']['baseline_daily_runtime_deltaT'], rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['baseline_daily_runtime_dailyavgCDD'],
            seasonal_metrics_type_1_data['cooling']['baseline_daily_runtime_dailyavgCDD'], rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['baseline_daily_runtime_hourlyavgCDD'],
            seasonal_metrics_type_1_data['cooling']['baseline_daily_runtime_hourlyavgCDD'], rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['baseline_seasonal_runtime_deltaT'],
            seasonal_metrics_type_1_data['cooling']['baseline_seasonal_runtime_deltaT'], rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['baseline_seasonal_runtime_dailyavgCDD'],
            seasonal_metrics_type_1_data['cooling']['baseline_seasonal_runtime_dailyavgCDD'], rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['baseline_seasonal_runtime_hourlyavgCDD'],
            seasonal_metrics_type_1_data['cooling']['baseline_seasonal_runtime_hourlyavgCDD'], rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['seasonal_avoided_runtime_deltaT'],
            seasonal_metrics_type_1_data['cooling']['seasonal_avoided_runtime_deltaT'], rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['seasonal_avoided_runtime_dailyavgCDD'],
            seasonal_metrics_type_1_data['cooling']['seasonal_avoided_runtime_dailyavgCDD'], rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['seasonal_avoided_runtime_hourlyavgCDD'],
            seasonal_metrics_type_1_data['cooling']['seasonal_avoided_runtime_hourlyavgCDD'], rtol=RTOL, atol=ATOL)

    assert_allclose(cooling_season_outputs['seasonal_savings_deltaT'],
            seasonal_metrics_type_1_data['cooling']['seasonal_savings_deltaT'], rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['seasonal_savings_dailyavgCDD'],
            seasonal_metrics_type_1_data['cooling']['seasonal_savings_dailyavgCDD'], rtol=RTOL, atol=ATOL)
    assert_allclose(cooling_season_outputs['seasonal_savings_hourlyavgCDD'],
            seasonal_metrics_type_1_data['cooling']['seasonal_savings_hourlyavgCDD'], rtol=RTOL, atol=ATOL)

    heating_season_outputs = seasonal_metrics_type_1[4]

    assert heating_season_outputs['ct_identifier'] == seasonal_metrics_type_1_data['ct_identifier']
    assert heating_season_outputs['equipment_type'] == seasonal_metrics_type_1_data['equipment_type']
    assert heating_season_outputs['zipcode'] == seasonal_metrics_type_1_data['zipcode']
    assert heating_season_outputs['station'] == seasonal_metrics_type_1_data['station']

    assert heating_season_outputs['season_name'] == seasonal_metrics_type_1_data['heating']['season_name']
    assert_allclose(heating_season_outputs['baseline_comfort_temperature'],
            seasonal_metrics_type_1_data['heating']['baseline_comfort_temperature'], rtol=RTOL, atol=ATOL)

    assert_allclose(heating_season_outputs['baseline_seasonal_runtime_deltaT'],
            seasonal_metrics_type_1_data['heating']['baseline_seasonal_runtime_deltaT'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['baseline_seasonal_runtime_dailyavgHDD'],
            seasonal_metrics_type_1_data['heating']['baseline_seasonal_runtime_dailyavgHDD'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['baseline_seasonal_runtime_hourlyavgHDD'],
            seasonal_metrics_type_1_data['heating']['baseline_seasonal_runtime_hourlyavgHDD'], rtol=RTOL, atol=ATOL)

    assert_allclose(heating_season_outputs['baseline_daily_runtime_deltaT'],
            seasonal_metrics_type_1_data['heating']['baseline_daily_runtime_deltaT'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['baseline_daily_runtime_dailyavgHDD'],
            seasonal_metrics_type_1_data['heating']['baseline_daily_runtime_dailyavgHDD'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['baseline_daily_runtime_hourlyavgHDD'],
            seasonal_metrics_type_1_data['heating']['baseline_daily_runtime_hourlyavgHDD'], rtol=RTOL, atol=ATOL)

    assert_allclose(heating_season_outputs['actual_daily_runtime'],
            seasonal_metrics_type_1_data['heating']['actual_daily_runtime'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['actual_seasonal_runtime'],
            seasonal_metrics_type_1_data['heating']['actual_seasonal_runtime'], rtol=RTOL, atol=ATOL)

    assert_allclose(heating_season_outputs['seasonal_avoided_runtime_deltaT'],
            seasonal_metrics_type_1_data['heating']['seasonal_avoided_runtime_deltaT'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['seasonal_avoided_runtime_dailyavgHDD'],
            seasonal_metrics_type_1_data['heating']['seasonal_avoided_runtime_dailyavgHDD'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['seasonal_avoided_runtime_hourlyavgHDD'],
            seasonal_metrics_type_1_data['heating']['seasonal_avoided_runtime_hourlyavgHDD'], rtol=RTOL, atol=ATOL)

    assert_allclose(heating_season_outputs['seasonal_savings_deltaT'],
            seasonal_metrics_type_1_data['heating']['seasonal_savings_deltaT'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['seasonal_savings_dailyavgHDD'],
            seasonal_metrics_type_1_data['heating']['seasonal_savings_dailyavgHDD'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['seasonal_savings_hourlyavgHDD'],
            seasonal_metrics_type_1_data['heating']['seasonal_savings_hourlyavgHDD'], rtol=RTOL, atol=ATOL)

    assert_allclose(heating_season_outputs['mean_squared_error_deltaT'],
            seasonal_metrics_type_1_data['heating']['mean_squared_error_deltaT'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['mean_sq_err_dailyavgHDD'],
            seasonal_metrics_type_1_data['heating']['mean_sq_err_dailyavgHDD'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['mean_sq_err_hourlyavgHDD'],
            seasonal_metrics_type_1_data['heating']['mean_sq_err_hourlyavgHDD'], rtol=RTOL, atol=ATOL)

    assert_allclose(heating_season_outputs['slope_deltaT'],
            seasonal_metrics_type_1_data['heating']['slope_deltaT'], rtol=RTOL, atol=ATOL)

    assert_allclose(heating_season_outputs['alpha_est_dailyavgHDD'],
            seasonal_metrics_type_1_data['heating']['alpha_est_dailyavgHDD'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['alpha_est_hourlyavgHDD'],
            seasonal_metrics_type_1_data['heating']['alpha_est_hourlyavgHDD'], rtol=RTOL, atol=ATOL)

    assert_allclose(heating_season_outputs['deltaT_base_est_dailyavgHDD'],
            seasonal_metrics_type_1_data['heating']['deltaT_base_est_dailyavgHDD'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['deltaT_base_est_hourlyavgHDD'],
            seasonal_metrics_type_1_data['heating']['deltaT_base_est_hourlyavgHDD'], rtol=RTOL, atol=ATOL)

    assert_allclose(heating_season_outputs['n_days_insufficient_data'],
            seasonal_metrics_type_1_data['heating']['n_days_insufficient_data'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['n_days_both_heating_and_cooling'],
            seasonal_metrics_type_1_data['heating']['n_days_both_heating_and_cooling'], rtol=RTOL, atol=ATOL)

    assert_allclose(heating_season_outputs['rhu_00F_to_05F'],
            seasonal_metrics_type_1_data['heating']['rhu_00F_to_05F'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_05F_to_10F'],
            seasonal_metrics_type_1_data['heating']['rhu_05F_to_10F'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_10F_to_15F'],
            seasonal_metrics_type_1_data['heating']['rhu_10F_to_15F'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_15F_to_20F'],
            seasonal_metrics_type_1_data['heating']['rhu_15F_to_20F'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_20F_to_25F'],
            seasonal_metrics_type_1_data['heating']['rhu_20F_to_25F'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_25F_to_30F'],
            seasonal_metrics_type_1_data['heating']['rhu_25F_to_30F'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_30F_to_35F'],
            seasonal_metrics_type_1_data['heating']['rhu_30F_to_35F'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_35F_to_40F'],
            seasonal_metrics_type_1_data['heating']['rhu_35F_to_40F'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_40F_to_45F'],
            seasonal_metrics_type_1_data['heating']['rhu_40F_to_45F'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_45F_to_50F'],
            seasonal_metrics_type_1_data['heating']['rhu_45F_to_50F'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_50F_to_55F'],
            seasonal_metrics_type_1_data['heating']['rhu_50F_to_55F'], rtol=RTOL, atol=ATOL)
    assert_allclose(heating_season_outputs['rhu_55F_to_60F'],
            seasonal_metrics_type_1_data['heating']['rhu_55F_to_60F'], rtol=RTOL, atol=ATOL)

def test_calculate_epa_draft_rccs_field_savings_metrics_type_2(thermostat_type_2):
    seasonal_metrics_type_2 = thermostat_type_2.calculate_epa_draft_rccs_field_savings_metrics()
    assert len(seasonal_metrics_type_2) == 9

def test_calculate_epa_draft_rccs_field_savings_metrics_type_3(thermostat_type_3):
    seasonal_metrics_type_3 = thermostat_type_3.calculate_epa_draft_rccs_field_savings_metrics()
    assert len(seasonal_metrics_type_3) == 9

def test_calculate_epa_draft_rccs_field_savings_metrics_type_4(thermostat_type_4):
    seasonal_metrics_type_4 = thermostat_type_4.calculate_epa_draft_rccs_field_savings_metrics()
    assert len(seasonal_metrics_type_4) == 5

def test_calculate_epa_draft_rccs_field_savings_metrics_type_5(thermostat_type_5):
    seasonal_metrics_type_5 = thermostat_type_5.calculate_epa_draft_rccs_field_savings_metrics()
    assert len(seasonal_metrics_type_5) == 4

def test_seasonal_metrics_to_csv(seasonal_metrics_type_1):
    fd, fname = tempfile.mkstemp()
    seasonal_metrics_to_csv(seasonal_metrics_type_1, fname)
    with open(fname,'r') as f:
        lines = f.readlines()
        assert len(lines) == 10
        for line in lines:
            assert len(line.split(',')) == 56
