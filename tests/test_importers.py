from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path

import pandas as pd

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
