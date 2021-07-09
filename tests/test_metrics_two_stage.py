import pandas as pd
import numpy as np
from numpy.testing import assert_allclose

import tempfile

import pytest

from thermostat.exporters import metrics_to_csv
from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics

from .fixtures.two_stage import (
        thermostat_hpeb_2_hp_2,
        # thermostat_type_2,
        thermostat_fu_2_ce_2,
        thermostat_furnace_or_boiler_two_stage_none_single_stage,
        thermostat_na_2_hp_2,
        )

from .fixtures.metrics_data import (
        metrics_hpeb_2_hp_2_data,
        )
from thermostat.columns import EXPORT_COLUMNS
import six

@pytest.fixture(scope="session")
def metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage(thermostat_hpeb_2_hp_2):
    metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage = thermostat_hpeb_2_hp_2.calculate_epa_field_savings_metrics()
    return metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage

@pytest.fixture(scope="session")
def metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage_multiple(thermostat_hpeb_2_hp_2):
    metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage = multiple_thermostat_calculate_epa_field_savings_metrics([thermostat_hpeb_2_hp_2])
    return metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage

RTOL = 1e-3
ATOL = 1e-3

def test_calculate_epa_field_savings_metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage(metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage, metrics_hpeb_2_hp_2_data):
    assert len(metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage) == len(metrics_hpeb_2_hp_2_data)

    for key in metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage[0].keys():
        test_value = metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage[0][key]
        target_value = metrics_hpeb_2_hp_2_data[0][key]
        if isinstance(test_value, six.string_types):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

    for key in metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage[1].keys():
        test_value = metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage[1][key]
        target_value = metrics_hpeb_2_hp_2_data[1][key]
        if isinstance(test_value, six.string_types):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

def test_multiple_thermostat_calculate_epa_field_savings_metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage(metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage_multiple, metrics_hpeb_2_hp_2_data):
    # Test multiprocessing thermostat code
    assert len(metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage_multiple) == len(metrics_hpeb_2_hp_2_data)

    for key in metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage_multiple[0].keys():
        test_value = metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage_multiple[0][key]
        target_value = metrics_hpeb_2_hp_2_data[0][key]
        if isinstance(test_value, six.string_types):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

    for key in metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage_multiple[1].keys():
        test_value = metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage_multiple[1][key]
        target_value = metrics_hpeb_2_hp_2_data[1][key]
        if isinstance(test_value, six.string_types):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

def test_calculate_epa_field_savings_metrics_type_3(thermostat_fu_2_ce_2):
    metrics_type_3 = thermostat_fu_2_ce_2.calculate_epa_field_savings_metrics()
    assert len(metrics_type_3) == 2

def test_calculate_epa_field_savings_metrics_type_4(thermostat_furnace_or_boiler_two_stage_none_single_stage):
    metrics_type_4 = thermostat_furnace_or_boiler_two_stage_none_single_stage.calculate_epa_field_savings_metrics()
    assert len(metrics_type_4) == 1

def test_calculate_epa_field_savings_metrics_type_5(thermostat_na_2_hp_2):
    metrics_type_5 = thermostat_na_2_hp_2.calculate_epa_field_savings_metrics()
    assert len(metrics_type_5) == 1

def test_metrics_to_csv(metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage):

    fd, fname = tempfile.mkstemp()
    df = metrics_to_csv(metrics_heat_pump_electric_backup_two_stage_heat_pump_two_stage, fname)

    assert isinstance(df, pd.DataFrame)
    assert df.columns[0] == "sw_version"
    assert df.columns[1] == "ct_identifier"

    with open(fname,'r') as f:
        lines = f.readlines()
        assert len(lines) == 3
        column_heads = lines[0].strip().split(',')
        assert column_heads == EXPORT_COLUMNS
