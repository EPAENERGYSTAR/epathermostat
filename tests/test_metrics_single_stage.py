import pandas as pd
import numpy as np
from numpy.testing import assert_allclose

import tempfile

import pytest

from thermostat.exporters import metrics_to_csv
from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics

from .fixtures.single_stage import (
        thermostat_type_1,
        thermostat_type_2,
        thermostat_type_3,
        thermostat_type_4,
        thermostat_type_5,
        )

from .fixtures.metrics_data import (
        metrics_type_1_data,
        )
from thermostat.columns import EXPORT_COLUMNS
import six

@pytest.fixture(scope="session")
def metrics_type_1(thermostat_type_1):
    metrics_type_1 = thermostat_type_1.calculate_epa_field_savings_metrics()
    return metrics_type_1

@pytest.fixture(scope="session")
def metrics_type_1_multiple(thermostat_type_1):
    metrics_type_1 = multiple_thermostat_calculate_epa_field_savings_metrics([thermostat_type_1])
    return metrics_type_1

RTOL = 1e-3
ATOL = 1e-3

def test_calculate_epa_field_savings_metrics_type_1(metrics_type_1, metrics_type_1_data):
    assert len(metrics_type_1) == len(metrics_type_1_data)

    for key in metrics_type_1[0].keys():
        test_value = metrics_type_1[0][key]
        target_value = metrics_type_1_data[0][key]
        if isinstance(test_value, six.string_types):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

    for key in metrics_type_1[1].keys():
        test_value = metrics_type_1[1][key]
        target_value = metrics_type_1_data[1][key]
        if isinstance(test_value, six.string_types):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

def test_multiple_thermostat_calculate_epa_field_savings_metrics_type_1(metrics_type_1_multiple, metrics_type_1_data):
    # Test multiprocessing thermostat code
    assert len(metrics_type_1_multiple) == len(metrics_type_1_data)

    for key in metrics_type_1_multiple[0].keys():
        test_value = metrics_type_1_multiple[0][key]
        target_value = metrics_type_1_data[0][key]
        if isinstance(test_value, six.string_types):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

    for key in metrics_type_1_multiple[1].keys():
        test_value = metrics_type_1_multiple[1][key]
        target_value = metrics_type_1_data[1][key]
        if isinstance(test_value, six.string_types):
            assert test_value == target_value
        else:
            assert_allclose(test_value, target_value, rtol=RTOL, atol=ATOL)

def test_calculate_epa_field_savings_metrics_type_2(thermostat_type_2):
    metrics_type_2_entire = thermostat_type_2.calculate_epa_field_savings_metrics()
    assert len(metrics_type_2_entire) == 2

def test_calculate_epa_field_savings_metrics_type_3(thermostat_type_3):
    metrics_type_3 = thermostat_type_3.calculate_epa_field_savings_metrics()
    assert len(metrics_type_3) == 2

def test_calculate_epa_field_savings_metrics_type_4(thermostat_type_4):
    metrics_type_4 = thermostat_type_4.calculate_epa_field_savings_metrics()
    assert len(metrics_type_4) == 1

def test_calculate_epa_field_savings_metrics_type_5(thermostat_type_5):
    metrics_type_5 = thermostat_type_5.calculate_epa_field_savings_metrics()
    assert len(metrics_type_5) == 1

def test_metrics_to_csv(metrics_type_1):

    fd, fname = tempfile.mkstemp()
    df = metrics_to_csv(metrics_type_1, fname)

    assert isinstance(df, pd.DataFrame)
    assert df.columns[0] == "sw_version"
    assert df.columns[1] == "ct_identifier"

    with open(fname,'r') as f:
        lines = f.readlines()
        assert len(lines) == 3
        column_heads = lines[0].strip().split(',')
        assert column_heads == EXPORT_COLUMNS
