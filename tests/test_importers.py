from thermostat.importers import from_csv
from thermostat.importers import get_hourly_outdoor_temperature
from thermostat.util.testing import get_data_path


import pandas as pd
from eemeter.weather import ISDWeatherSource
from datetime import datetime

import pytest

@pytest.fixture(params=["metadata_equipment_type_0.csv"])
def metadata_type_0_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["metadata_equipment_type_1.csv"])
def metadata_type_1_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["metadata_equipment_type_2.csv"])
def metadata_type_2_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["metadata_equipment_type_3.csv"])
def metadata_type_3_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["metadata_equipment_type_4.csv"])
def metadata_type_4_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["metadata_equipment_type_5.csv"])
def metadata_type_5_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["hourly_data_equipment_type_0.csv"])
def interval_data_type_0_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["hourly_data_equipment_type_1_both.csv",
                        "hourly_data_equipment_type_1_emergency.csv",
                        "hourly_data_equipment_type_1_auxiliary.csv"])
def interval_data_type_1_valid_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["hourly_data_equipment_type_2.csv"])
def interval_data_type_2_valid_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["hourly_data_equipment_type_3.csv"])
def interval_data_type_3_valid_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["hourly_data_equipment_type_4.csv"])
def interval_data_type_4_valid_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["hourly_data_equipment_type_5.csv"])
def interval_data_type_5_valid_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["hourly_data_equipment_type_0.csv",
                        "hourly_data_equipment_type_2.csv",
                        "hourly_data_equipment_type_3.csv",
                        "hourly_data_equipment_type_4.csv",
                        "hourly_data_equipment_type_5.csv"])
def interval_data_type_1_invalid_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["hourly_data_equipment_type_0.csv",
                        "hourly_data_equipment_type_1_both.csv",
                        "hourly_data_equipment_type_1_emergency.csv",
                        "hourly_data_equipment_type_1_auxiliary.csv",
                        "hourly_data_equipment_type_3.csv",
                        "hourly_data_equipment_type_4.csv",
                        "hourly_data_equipment_type_5.csv"])
def interval_data_type_2_invalid_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["hourly_data_equipment_type_0.csv",
                        "hourly_data_equipment_type_1_both.csv",
                        "hourly_data_equipment_type_1_emergency.csv",
                        "hourly_data_equipment_type_1_auxiliary.csv",
                        "hourly_data_equipment_type_2.csv",
                        "hourly_data_equipment_type_4.csv",
                        "hourly_data_equipment_type_5.csv"])
def interval_data_type_3_invalid_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["hourly_data_equipment_type_0.csv",
                        "hourly_data_equipment_type_1_both.csv",
                        "hourly_data_equipment_type_1_emergency.csv",
                        "hourly_data_equipment_type_1_auxiliary.csv",
                        "hourly_data_equipment_type_2.csv",
                        "hourly_data_equipment_type_3.csv",
                        "hourly_data_equipment_type_5.csv"])
def interval_data_type_4_invalid_filename(request):
    return get_data_path(request.param)

@pytest.fixture(params=["hourly_data_equipment_type_0.csv",
                        "hourly_data_equipment_type_1_both.csv",
                        "hourly_data_equipment_type_1_emergency.csv",
                        "hourly_data_equipment_type_1_auxiliary.csv",
                        "hourly_data_equipment_type_2.csv",
                        "hourly_data_equipment_type_3.csv",
                        "hourly_data_equipment_type_4.csv"])
def interval_data_type_5_invalid_filename(request):
    return get_data_path(request.param)

def test_import_csv_type_0_skips_import(metadata_type_0_filename,interval_data_type_0_filename):
    thermostats = from_csv(metadata_type_0_filename,interval_data_type_0_filename)
    assert len(thermostats) == 0


def test_import_csv_type_1_with_valid_columns(metadata_type_1_filename,interval_data_type_1_valid_filename):
    thermostats = from_csv(metadata_type_1_filename,interval_data_type_1_valid_filename)
    assert len(thermostats) == 1

def test_import_csv_type_2_with_valid_columns(metadata_type_2_filename,interval_data_type_2_valid_filename):
    thermostats = from_csv(metadata_type_2_filename,interval_data_type_2_valid_filename)
    assert len(thermostats) == 1

def test_import_csv_type_3_with_valid_columns(metadata_type_3_filename,interval_data_type_3_valid_filename):
    thermostats = from_csv(metadata_type_3_filename,interval_data_type_3_valid_filename)
    assert len(thermostats) == 1

def test_import_csv_type_4_with_valid_columns(metadata_type_4_filename,interval_data_type_4_valid_filename):
    thermostats = from_csv(metadata_type_4_filename,interval_data_type_4_valid_filename)
    assert len(thermostats) == 1

def test_import_csv_type_1_with_valid_columns(metadata_type_5_filename,interval_data_type_5_valid_filename):
    thermostats = from_csv(metadata_type_5_filename,interval_data_type_5_valid_filename)
    assert len(thermostats) == 1


def test_import_csv_type_1_with_invalid_columns(metadata_type_1_filename,interval_data_type_1_invalid_filename):
    with pytest.raises(ValueError):
        thermostats = from_csv(metadata_type_1_filename,interval_data_type_1_invalid_filename)

def test_import_csv_type_2_with_invalid_columns(metadata_type_2_filename,interval_data_type_2_invalid_filename):
    with pytest.raises(ValueError):
        thermostats = from_csv(metadata_type_2_filename,interval_data_type_2_invalid_filename)

def test_import_csv_type_3_with_invalid_columns(metadata_type_3_filename,interval_data_type_3_invalid_filename):
    with pytest.raises(ValueError):
        thermostats = from_csv(metadata_type_3_filename,interval_data_type_3_invalid_filename)

def test_import_csv_type_4_with_invalid_columns(metadata_type_4_filename,interval_data_type_4_invalid_filename):
    with pytest.raises(ValueError):
        thermostats = from_csv(metadata_type_4_filename,interval_data_type_4_invalid_filename)

def test_import_csv_type_5_with_invalid_columns(metadata_type_5_filename,interval_data_type_5_invalid_filename):
    with pytest.raises(ValueError):
        thermostats = from_csv(metadata_type_5_filename,interval_data_type_5_invalid_filename)

def test_import_csv_imports_attributes_correctly(metadata_type_2_filename,interval_data_type_2_valid_filename):
    thermostats = from_csv(metadata_type_2_filename,interval_data_type_2_valid_filename)
    thermostat = thermostats[0]
    assert type(thermostat.temperature_in.index) == pd.DatetimeIndex
    assert type(thermostat.temperature_setpoint.index) == pd.DatetimeIndex
    assert type(thermostat.ss_heat_pump_heating.index) == pd.DatetimeIndex
    assert type(thermostat.ss_heat_pump_cooling.index) == pd.DatetimeIndex
    with pytest.raises(AttributeError):
        thermostat.auxiliary_heat
    with pytest.raises(AttributeError):
        thermostat.emergency_heat
    with pytest.raises(AttributeError):
        thermostat.ss_heating
    with pytest.raises(AttributeError):
        thermostat.ss_central_ac

##################### Outdoor temperature #########################

@pytest.fixture(params=[(datetime(2014,1,1),datetime(2014,1,2)),
                        (datetime(2014,1,1),datetime(2014,2,1))])
def hourly_datetime_index(request):
    start,end = request.param
    return pd.DatetimeIndex(start=start,end=end,freq="H")

@pytest.fixture(params=["722660"])
def hourly_weather_source(request):
    station = request.param
    return ISDWeatherSource(station,2010,2015)

def test_get_hourly_outdoor_temperature(hourly_datetime_index,hourly_weather_source):
    outdoor_temperatures = get_hourly_outdoor_temperature(hourly_datetime_index,hourly_weather_source)
    assert type(outdoor_temperatures.index) == pd.DatetimeIndex
    assert outdoor_temperatures.index[0] == hourly_datetime_index[0]
    assert len(outdoor_temperatures.index) + 1  == len(hourly_datetime_index)
    assert sum(pd.isnull(outdoor_temperatures)) < 2 * (len(hourly_datetime_index) / 24.)
    for temp in outdoor_temperatures:
        if not pd.isnull(temp):
            assert -60 < temp < 140
