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
from fixtures.thermostats import seasonal_metrics_type_1_data

@pytest.fixture(scope="session")
def seasonal_metrics_type_1(thermostat_type_1):
    seasonal_metrics_type_1 = thermostat_type_1.calculate_epa_draft_rccs_field_savings_metrics()
    return seasonal_metrics_type_1

RTOL = 1e-3
ATOL = 1e-3

def test_calculate_epa_draft_rccs_field_savings_metrics_type_1(seasonal_metrics_type_1, seasonal_metrics_type_1_data):
    assert len(seasonal_metrics_type_1) == len(seasonal_metrics_type_1_data)

    for key in seasonal_metrics_type_1[0].keys():
        test_value = seasonal_metrics_type_1[0][key]
        target_value = seasonal_metrics_type_1_data[0][key]
        assert test_value == target_value

    for key in seasonal_metrics_type_1[1].keys():
        test_value = seasonal_metrics_type_1[1][key]
        target_value = seasonal_metrics_type_1_data[1][key]
        assert test_value == target_value

def test_calculate_epa_draft_rccs_field_savings_metrics_type_2(thermostat_type_2):
    seasonal_metrics_type_2_entire = thermostat_type_2.calculate_epa_draft_rccs_field_savings_metrics()
    assert len(seasonal_metrics_type_2_entire) == 2

    seasonal_metrics_type_2_yearly = thermostat_type_2.calculate_epa_draft_rccs_field_savings_metrics(
            cooling_season_method="year_end_to_end",
            heating_season_method="year_mid_to_mid")
    assert len(seasonal_metrics_type_2_yearly) == 9

def test_calculate_epa_draft_rccs_field_savings_metrics_type_3(thermostat_type_3):
    seasonal_metrics_type_3 = thermostat_type_3.calculate_epa_draft_rccs_field_savings_metrics()
    assert len(seasonal_metrics_type_3) == 2

def test_calculate_epa_draft_rccs_field_savings_metrics_type_4(thermostat_type_4):
    seasonal_metrics_type_4 = thermostat_type_4.calculate_epa_draft_rccs_field_savings_metrics()
    assert len(seasonal_metrics_type_4) == 1

def test_calculate_epa_draft_rccs_field_savings_metrics_type_5(thermostat_type_5):
    seasonal_metrics_type_5 = thermostat_type_5.calculate_epa_draft_rccs_field_savings_metrics()
    assert len(seasonal_metrics_type_5) == 1

def test_seasonal_metrics_to_csv(seasonal_metrics_type_1):

    fd, fname = tempfile.mkstemp()
    df = seasonal_metrics_to_csv(seasonal_metrics_type_1, fname)

    assert isinstance(df, pd.DataFrame)
    assert df.columns[0] == "ct_identifier"
    assert df.columns[1] == "equipment_type"

    with open(fname,'r') as f:
        lines = f.readlines()
        assert len(lines) == 3
        column_heads = lines[0].split(',')
        assert column_heads[0] == "ct_identifier"
        assert column_heads[1] == "equipment_type"
        assert column_heads[2] == "season_name"
        assert column_heads[3] == "station"
        assert column_heads[4] == "zipcode"
        assert column_heads[62].strip() == "rhu_55F_to_60F"
        for line in lines:
            assert len(line.split(',')) == 63
