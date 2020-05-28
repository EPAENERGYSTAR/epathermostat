import pandas as pd
import numpy as np

from numpy.testing import assert_allclose

import pytest

from .fixtures.thermostats import thermostat_type_1
from .fixtures.thermostats import core_heating_day_set_type_1_entire
from .fixtures.thermostats import core_cooling_day_set_type_1_entire
from .fixtures.thermostats import metrics_type_1_data
from .fixtures.thermostats import thermostat_template

from thermostat.core import CoreDaySet
from datetime import datetime

RTOL = 1e-3
ATOL = 1e-3


@pytest.mark.slow
def test_get_core_cooling_day_baseline_setpoint(thermostat_type_1, core_cooling_day_set_type_1_entire, metrics_type_1_data):

    baseline = thermostat_type_1.get_core_cooling_day_baseline_setpoint(core_cooling_day_set_type_1_entire)
    assert_allclose(baseline, metrics_type_1_data[0]["baseline_percentile_core_cooling_comfort_temperature"], rtol=RTOL, atol=ATOL)

@pytest.mark.slow
def test_get_core_heating_day_baseline_setpoint(thermostat_type_1, core_heating_day_set_type_1_entire, metrics_type_1_data):

    baseline = thermostat_type_1.get_core_heating_day_baseline_setpoint(core_heating_day_set_type_1_entire)
    assert_allclose(baseline, metrics_type_1_data[1]["baseline_percentile_core_heating_comfort_temperature"], rtol=RTOL, atol=ATOL)

def test_get_core_heating_day_baseline_setpoint_null_temperature_in(thermostat_template):

    index = pd.date_range(start=datetime(2011, 1, 1), periods=3, freq='D')
    thermostat_template.temperature_in = pd.Series([0, 1, 2], index=index)
    thermostat_template.equipment_type = 1

    season_selector = pd.Series([True, True, True], index=index)
    core_day_set = CoreDaySet("FAKE", season_selector, season_selector, None, None)

    sp = thermostat_template.get_core_heating_day_baseline_setpoint(core_day_set, source='heating_setpoint')
    assert pd.isnull(sp)

    sp = thermostat_template.get_core_heating_day_baseline_setpoint(core_day_set, source='temperature_in')
    assert_allclose(sp, 1.8)

    thermostat_template.temperature_in = pd.Series([np.nan, 1, 2], index=index)
    sp = thermostat_template.get_core_heating_day_baseline_setpoint(core_day_set, source='temperature_in')
    assert_allclose(sp, 1.9)

    thermostat_template.temperature_in = pd.Series([0, 1, np.nan], index=index)
    sp = thermostat_template.get_core_heating_day_baseline_setpoint(core_day_set, source='temperature_in')
    assert_allclose(sp, 0.9)

    thermostat_template.temperature_in = pd.Series([np.nan, np.nan, np.nan], index=index)
    sp = thermostat_template.get_core_heating_day_baseline_setpoint(core_day_set, source='temperature_in')
    assert pd.isnull(sp)

def test_get_core_cooling_day_baseline_setpoint_null_temperature_in(thermostat_template):

    index = pd.date_range(start=datetime(2011, 1, 1), periods=3, freq='D')
    thermostat_template.temperature_in = pd.Series([0, 1, 2], index=index)
    thermostat_template.equipment_type = 1

    season_selector = pd.Series([True, True, True], index=index)
    core_day_set = CoreDaySet("FAKE", season_selector, season_selector, None, None)

    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(core_day_set, source='cooling_setpoint')
    assert pd.isnull(sp)

    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(core_day_set, source='temperature_in')
    assert_allclose(sp, 0.2)

    thermostat_template.temperature_in = pd.Series([np.nan, 1, 2], index=index)
    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(core_day_set, source='temperature_in')
    assert_allclose(sp, 1.1)

    thermostat_template.temperature_in = pd.Series([0, 1, np.nan], index=index)
    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(core_day_set, source='temperature_in')
    assert_allclose(sp, 0.1)

    thermostat_template.temperature_in = pd.Series([np.nan, np.nan, np.nan], index=index)
    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(core_day_set, source='temperature_in')
    assert pd.isnull(sp)

def test_get_core_heating_day_baseline_setpoint_null_heating_setpoint(thermostat_template):

    index = pd.date_range(start=datetime(2011, 1, 1), periods=3, freq='D')
    thermostat_template.heating_setpoint = pd.Series([0, 1, 2], index=index)
    thermostat_template.equipment_type = 1

    season_selector = pd.Series([True, True, True], index=index)
    core_day_set = CoreDaySet("FAKE", season_selector, season_selector, None, None)

    sp = thermostat_template.get_core_heating_day_baseline_setpoint(core_day_set, source='temperature_in')
    assert pd.isnull(sp)

    sp = thermostat_template.get_core_heating_day_baseline_setpoint(core_day_set, source='heating_setpoint')
    assert_allclose(sp, 1.8)

    thermostat_template.heating_setpoint = pd.Series([np.nan, 1, 2], index=index)
    sp = thermostat_template.get_core_heating_day_baseline_setpoint(core_day_set, source='heating_setpoint')
    assert_allclose(sp, 1.9)

    thermostat_template.heating_setpoint = pd.Series([0, 1, np.nan], index=index)
    sp = thermostat_template.get_core_heating_day_baseline_setpoint(core_day_set, source='heating_setpoint')
    assert_allclose(sp, 0.9)

    thermostat_template.heating_setpoint = pd.Series([np.nan, np.nan, np.nan], index=index)
    sp = thermostat_template.get_core_heating_day_baseline_setpoint(core_day_set, source='heating_setpoint')
    assert pd.isnull(sp)

def test_get_core_cooling_day_baseline_setpoint_null_cooling_setpoint(thermostat_template):

    index = pd.date_range(start=datetime(2011, 1, 1), periods=3, freq='D')
    thermostat_template.cooling_setpoint = pd.Series([0, 1, 2], index=index)
    thermostat_template.equipment_type = 1

    season_selector = pd.Series([True, True, True], index=index)
    core_day_set = CoreDaySet("FAKE", season_selector, season_selector, None, None)

    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(core_day_set, source='temperature_in')
    assert pd.isnull(sp)

    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(core_day_set, source='cooling_setpoint')
    assert_allclose(sp, 0.2)

    thermostat_template.cooling_setpoint = pd.Series([np.nan, 1, 2], index=index)
    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(core_day_set, source='cooling_setpoint')
    assert_allclose(sp, 1.1)

    thermostat_template.cooling_setpoint = pd.Series([0, 1, np.nan], index=index)
    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(core_day_set, source='cooling_setpoint')
    assert_allclose(sp, 0.1)

    thermostat_template.cooling_setpoint = pd.Series([np.nan, np.nan, np.nan], index=index)
    sp = thermostat_template.get_core_cooling_day_baseline_setpoint(core_day_set, source='cooling_setpoint')
    assert pd.isnull(sp)
