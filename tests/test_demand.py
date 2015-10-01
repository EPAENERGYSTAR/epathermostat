from thermostat.core import Thermostat
from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path

import numpy as np
import pandas as pd

from numpy.testing import assert_allclose

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

@pytest.fixture
def heating_season(thermostat):
    return thermostat.get_heating_seasons()[0]

@pytest.fixture
def cooling_season(thermostat):
    return thermostat.get_cooling_seasons()[0]

def test_get_cooling_demand_deltaT(thermostat, cooling_season):

    deltaT = thermostat.get_cooling_demand(cooling_season, method="deltaT")
    assert_allclose(deltaT.mean(), -4.352, rtol=RTOL, atol=ATOL)

def test_get_cooling_demand_dailyavgCDD(thermostat, cooling_season):

    dailyavgCDD, deltaT_base_estimate, alpha_estimate, error = \
            thermostat.get_cooling_demand(cooling_season, method="dailyavgCDD")
    assert_allclose(dailyavgCDD.mean(), 4.595, rtol=RTOL, atol=ATOL)
    assert_allclose(deltaT_base_estimate, 0.243, rtol=RTOL, atol=ATOL)
    assert_allclose(alpha_estimate, 2306.649, rtol=RTOL, atol=ATOL)
    assert_allclose(error, 985500.273, rtol=RTOL, atol=ATOL)

def test_get_cooling_demand_hourlysumCDD(thermostat, cooling_season):

    hourlysumCDD, deltaT_base_estimate, alpha_estimate, error = \
            thermostat.get_cooling_demand(cooling_season, method="hourlysumCDD")
    assert_allclose(hourlysumCDD.mean(), 4.021, rtol=RTOL, atol=ATOL)
    assert_allclose(deltaT_base_estimate, -0.770, rtol=RTOL, atol=ATOL)
    assert_allclose(alpha_estimate, 2635.493, rtol=RTOL, atol=ATOL)
    assert_allclose(error, 1220265.285, rtol=RTOL, atol=ATOL)

def test_get_heating_demand_deltaT(thermostat, heating_season):

    deltaT = thermostat.get_heating_demand(heating_season, method="deltaT")
    assert_allclose(deltaT.mean(), 7.689, rtol=RTOL, atol=ATOL)

def test_get_heating_demand_dailyavgHDD(thermostat, heating_season):

    dailyavgHDD, deltaT_base_estimate, alpha_estimate, error = \
            thermostat.get_heating_demand(heating_season, method="dailyavgHDD")
    assert_allclose(dailyavgHDD.mean(), 7.690, rtol=RTOL, atol=ATOL)
    assert_allclose(deltaT_base_estimate, -0.001, rtol=RTOL, atol=ATOL)
    assert_allclose(alpha_estimate, 2400.239, rtol=RTOL, atol=ATOL)
    assert_allclose(error, 369354.946, rtol=RTOL, atol=ATOL)

def test_get_heating_demand_hourlysumHDD(thermostat, heating_season):

    hourlysumHDD, deltaT_base_estimate, alpha_estimate, error = \
            thermostat.get_heating_demand(heating_season, method="hourlysumHDD")
    assert_allclose(hourlysumHDD.mean(), 7.148, rtol=RTOL, atol=ATOL)
    assert_allclose(deltaT_base_estimate, 0.428, rtol=RTOL, atol=ATOL)
    assert_allclose(alpha_estimate, 2582.295, rtol=RTOL, atol=ATOL)
    assert_allclose(error, 882030.507, rtol=RTOL, atol=ATOL)
