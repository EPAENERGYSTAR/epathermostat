import pytest
import warnings
import numpy as np
from numpy.testing import assert_allclose
from numpy import isnan
import pandas as pd

from datetime import datetime

from thermostat.core import (
        __pandas_warnings,
        percent_savings,
        RESISTANCE_HEAT_USE_BIN_PAIRS,
        )
from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path

from .fixtures.single_stage import (
        thermostat_type_1,
        thermostat_type_2,
        thermostat_type_3,
        thermostat_type_4,
        thermostat_type_5,
        core_heating_day_set_type_1_entire,
        core_heating_day_set_type_2,
        core_heating_day_set_type_3,
        core_heating_day_set_type_4,
        core_cooling_day_set_type_1_entire,
        core_cooling_day_set_type_2,
        core_cooling_day_set_type_3,
        core_cooling_day_set_type_5,
        thermostat_zero_days,
        thermostats_multiple_same_key,
        )

from .fixtures.metrics_data import(
        metrics_type_1_data,
        )

BASELINE_REGIONAL_COMFORT_CHECK_NONE = [
        'baseline_regional_demand',
        'baseline_regional_runtime',
        'avoided_runtime_baseline_regional',
        'percent_savings_baseline_regional',
        'avoided_daily_mean_core_day_runtime_baseline_regional',
        'avoided_total_core_day_runtime_baseline_regional',
        'baseline_daily_mean_core_day_runtime_baseline_regional',
        'baseline_total_core_day_runtime_baseline_regional',
        '_daily_mean_core_day_demand_baseline_baseline_regional',
        ]


def test_rhu_formatting(thermostat_type_1):
    assert('rhu1_less05F' == thermostat_type_1._format_rhu('rhu1', -np.inf, 5, None))
    assert('rhu1_greater55F' == thermostat_type_1._format_rhu('rhu1', 55, np.inf, None))
    assert('rhu1_30F_to_45F' == thermostat_type_1._format_rhu('rhu1', 30, 45, None))
    assert('rhu2_05F_to_10F_aux_duty_cycle' == thermostat_type_1._format_rhu('rhu2', 5, 10, 'aux_duty_cycle'))

def test_pandas_warnings(thermostat_type_1):
    with pytest.warns(Warning):
        __pandas_warnings('0.21.0')

    with pytest.warns(None) as pytest_warnings:
        __pandas_warnings('1.2.0')
    assert not pytest_warnings

    assert __pandas_warnings(None) is None


def test_perecent_saings(thermostat_type_1):
    avoided = pd.Series([4, 5,6])
    baseline = pd.Series([0, 0, 0])
    result = percent_savings(avoided, baseline, 'thermostat_test')
    assert result == np.inf


def test_zero_days_warning(thermostat_zero_days):
    output = thermostat_zero_days.calculate_epa_field_savings_metrics()
    assert isnan(output[0]['daily_mean_core_cooling_runtime'])
    assert isnan(output[1]['daily_mean_core_heating_runtime'])


def test_multiple_same_key(thermostats_multiple_same_key):
    metrics = []
    for thermostat in thermostats_multiple_same_key:
        outputs = thermostat.calculate_epa_field_savings_metrics()
        metrics.extend(outputs)
    assert len(metrics) == 4

    for key in metrics[0]:
        assert(metrics[0][key] == metrics[2][key])

    for key in metrics[1]:
        # nan can never be equal, so skip nan
        if not (isinstance(metrics[1][key], float) and np.isnan(metrics[1][key])):
            assert(metrics[1][key] == metrics[3][key])


def test_interpolate_empty(thermostat_type_1):
    s1 = pd.Series([])
    s1_intp = thermostat_type_1._interpolate(s1)
    np.testing.assert_allclose(s1_intp, [])


def test_interpolate_full(thermostat_type_1):
    s2 = pd.Series([1])
    s2_intp = thermostat_type_1._interpolate(s2)
    np.testing.assert_allclose(s2_intp, [1])
    np.testing.assert_allclose(s2_intp, [1])


def test_interpolate_forward(thermostat_type_1):
    s3 = pd.Series([1, np.nan])
    s3_intp = thermostat_type_1._interpolate(s3)
    np.testing.assert_allclose(s3_intp, [1, 1])


def test_interpolate_backward(thermostat_type_1):
    s4 = pd.Series([np.nan, 1])
    s4_intp = thermostat_type_1._interpolate(s4)
    np.testing.assert_allclose(s4_intp, [1, 1])


def test_interpolate_one_missing_bad_method(thermostat_type_1):
    s5 = pd.Series([8, 3, np.nan, 1, 7])
    s5_intp = thermostat_type_1._interpolate(s5, method="none")
    np.testing.assert_allclose(s5_intp, [8,3,np.nan,1,7])


def test_interpolate_one_missing(thermostat_type_1):
    s5 = pd.Series([8, 3, np.nan, 1, 7])
    s5_intp = thermostat_type_1._interpolate(s5)
    np.testing.assert_allclose(s5_intp, [8,3,2,1,7])


def test_interpolate_two_missing(thermostat_type_1):
    s6 = pd.Series([8, np.nan, np.nan, 1, 7])
    s6_intp = thermostat_type_1._interpolate(s6)
    np.testing.assert_allclose(s6_intp, [8,5.666,3.333,1,7], rtol=1e-3)


def test_interpolate_three_missing(thermostat_type_1):
    s = pd.Series([8, np.nan, np.nan, np.nan, 1, 7])
    s_intp = thermostat_type_1._interpolate(s)
    np.testing.assert_allclose(s_intp, [8,6.25,np.nan,2.75,1,7])


def test_thermostat_type_1_get_core_heating_days(thermostat_type_1):
    core_heating_day_sets = thermostat_type_1.get_core_heating_days()
    assert len(core_heating_day_sets) == 1

def test_thermostat_type_1_get_core_heating_days_bad_methods(thermostat_type_1):
    with pytest.raises(NotImplementedError) as record:
        core_heating_day_sets = thermostat_type_1.get_core_heating_days(
                method="bad_method")

def test_thermostat_type_1_get_core_cooling_days(thermostat_type_1):
    core_cooling_day_sets = thermostat_type_1.get_core_cooling_days()
    assert len(core_cooling_day_sets) == 1

def test_thermostat_type_1_get_core_cooling_days_bad_methods(thermostat_type_1):
    with pytest.raises(NotImplementedError) as record:
        core_cooling_day_sets = thermostat_type_1.get_core_cooling_days(
                method="bad_method")

def test_thermostat_type_1_no_data(thermostat_type_1):
    heat_runtime_daily = thermostat_type_1.heat_runtime_daily
    thermostat_type_1.heat_runtime_daily = None
    with pytest.raises(ValueError) as record:
        thermostat_type_1.validate()
    thermostat_type_1.heat_runtime_daily = heat_runtime_daily

    cool_runtime_daily = thermostat_type_1.cool_runtime_daily
    thermostat_type_1.cool_runtime_daily = None
    with pytest.raises(ValueError) as record:
        thermostat_type_1.validate()
    thermostat_type_1.cool_runtime_daily = cool_runtime_daily

    aux_heat_runtime = thermostat_type_1.auxiliary_heat_runtime
    emg_heat_runtime = thermostat_type_1.emergency_heat_runtime
    thermostat_type_1.auxiliary_heat_runtime = None
    thermostat_type_1.emergency_heat_runtime = None
    with pytest.raises(ValueError) as record:
        thermostat_type_1.validate()
    thermostat_type_1.auxiliary_heat_runtime = aux_heat_runtime
    thermostat_type_1.emergency_heat_runtime = emg_heat_runtime


def test_thermostat_type_1_baseline_regional_comfort_temperature_none(thermostat_type_1,
        core_heating_day_set_type_1_entire, core_cooling_day_set_type_1_entire):
    climate_zone='Mixed-Humid'
    core_heating_day_set_method='entire_dataset'
    core_cooling_day_set_method='entire_dataset'
    baseline_regional_cooling_comfort_temperature=None
    baseline_regional_heating_comfort_temperature=None
    result = thermostat_type_1._calculate_cooling_epa_field_savings_metrics(
            climate_zone,
            core_cooling_day_set_type_1_entire,
            core_cooling_day_set_method,
            baseline_regional_cooling_comfort_temperature)

    for baseline_key in BASELINE_REGIONAL_COMFORT_CHECK_NONE:
        assert result.get(baseline_key, None) is None

    result = thermostat_type_1._calculate_heating_epa_field_savings_metrics(
            climate_zone,
            core_heating_day_set_type_1_entire,
            core_heating_day_set_method,
            baseline_regional_heating_comfort_temperature)

    for baseline_key in BASELINE_REGIONAL_COMFORT_CHECK_NONE:
        assert result.get(baseline_key, None) is None


def test_thermostat_type_2_get_core_heating_days(thermostat_type_2):
    core_heating_day_sets = thermostat_type_2.get_core_heating_days()
    assert len(core_heating_day_sets) == 1


def test_thermostat_type_2_get_core_cooling_days(thermostat_type_2):
    core_cooling_day_sets = thermostat_type_2.get_core_cooling_days()
    assert len(core_cooling_day_sets) == 1


def test_thermostat_type_3_get_core_heating_days(thermostat_type_3):
    core_heating_day_sets = thermostat_type_3.get_core_heating_days()
    assert len(core_heating_day_sets) == 1


def test_thermostat_type_3_get_core_cooling_days(thermostat_type_3):
    core_cooling_day_sets = thermostat_type_3.get_core_cooling_days()
    assert len(core_cooling_day_sets) == 1


def test_thermostat_type_4_get_core_heating_days(thermostat_type_4):
    core_heating_day_sets = thermostat_type_4.get_core_heating_days()
    assert len(core_heating_day_sets) == 1


def test_thermostat_type_4_get_core_cooling_days(thermostat_type_4):
    with pytest.raises(ValueError):
        core_cooling_day_sets = thermostat_type_4.get_core_cooling_days()


def test_thermostat_type_5_get_core_heating_days(thermostat_type_5):
    with pytest.raises(ValueError):
        core_heating_day_sets = thermostat_type_5.get_core_heating_days()


def test_thermostat_type_5_get_core_cooling_days(thermostat_type_5):
    core_cooling_day_sets = thermostat_type_5.get_core_cooling_days()
    assert len(core_cooling_day_sets) == 1


def test_thermostat_type_1_get_core_heating_days_with_params(thermostat_type_1):
    core_heating_day_sets = thermostat_type_1.get_core_heating_days(
            min_minutes_heating=0, max_minutes_cooling=0)
    assert len(core_heating_day_sets) == 1


def test_thermostat_type_1_get_core_cooling_days_with_params(thermostat_type_1):
    core_heating_day_sets = thermostat_type_1.get_core_cooling_days(
            min_minutes_cooling=0, max_minutes_heating=0)
    assert len(core_heating_day_sets) == 1


def test_get_core_cooling_day_baseline_setpoint_not_implemented(thermostat_type_1, core_cooling_day_set_type_1_entire):
    with pytest.raises(NotImplementedError):
        thermostat_type_1.get_core_cooling_day_baseline_setpoint(core_cooling_day_set_type_1_entire, method="bad")
    with pytest.raises(NotImplementedError):
        thermostat_type_1.get_core_cooling_day_baseline_setpoint(core_cooling_day_set_type_1_entire, source="bad")
    with pytest.raises(NotImplementedError):
        thermostat_type_1.get_core_cooling_day_baseline_setpoint(core_cooling_day_set_type_1_entire, source="cooling_setpoint")


def test_get_core_heating_day_baseline_setpoint_not_implemented(thermostat_type_1, core_heating_day_set_type_1_entire):
    with pytest.raises(NotImplementedError):
        thermostat_type_1.get_core_heating_day_baseline_setpoint(core_heating_day_set_type_1_entire, method="bad")
    with pytest.raises(NotImplementedError):
        thermostat_type_1.get_core_heating_day_baseline_setpoint(core_heating_day_set_type_1_entire, source="bad")
    with pytest.raises(NotImplementedError):
        thermostat_type_1.get_core_heating_day_baseline_setpoint(core_cooling_day_set_type_1_entire, source="heating_setpoint")


def test_rhu_bins_none(thermostat_type_1):
    rhu = thermostat_type_1._rhu_outputs(
            rhu_type='rhu1',
            rhu_bins=None,
            rhu_usage_bins=RESISTANCE_HEAT_USE_BIN_PAIRS,
            duty_cycle=None)
    unique_rhu = set(rhu.values()).pop()
    assert unique_rhu is None

def test_thermostat_core_heating_day_set_attributes(core_heating_day_set_type_1_entire):

    assert isinstance(core_heating_day_set_type_1_entire.name, str)
    assert isinstance(core_heating_day_set_type_1_entire.daily, pd.Series)
    assert isinstance(core_heating_day_set_type_1_entire.hourly, pd.Series)
    assert core_heating_day_set_type_1_entire.daily.shape == (1461,)
    assert core_heating_day_set_type_1_entire.hourly.shape == (35064,)
    assert (
        isinstance(core_heating_day_set_type_1_entire.start_date, datetime)
        or isinstance(core_heating_day_set_type_1_entire.start_date, np.datetime64)
    )
    assert (
        isinstance(core_heating_day_set_type_1_entire.end_date, datetime)
        or isinstance(core_heating_day_set_type_1_entire.end_date, np.datetime64)
    )


def test_thermostat_core_cooling_day_set_attributes(core_cooling_day_set_type_1_entire):

    assert isinstance(core_cooling_day_set_type_1_entire.name, str)
    assert isinstance(core_cooling_day_set_type_1_entire.daily, pd.Series)
    assert isinstance(core_cooling_day_set_type_1_entire.hourly, pd.Series)
    assert core_cooling_day_set_type_1_entire.daily.shape == (1461,)
    assert core_cooling_day_set_type_1_entire.hourly.shape == (35064,)
    assert (
        isinstance(core_cooling_day_set_type_1_entire.start_date, datetime)
        or isinstance(core_cooling_day_set_type_1_entire.start_date, np.datetime64)
    )
    assert (
        isinstance(core_cooling_day_set_type_1_entire.end_date, datetime)
        or isinstance(core_cooling_day_set_type_1_entire.end_date, np.datetime64)
    )


def test_thermostat_equipment_protect_cooling(thermostat_type_4, thermostat_type_5):
    assert thermostat_type_5._protect_cooling() is None
    with pytest.raises(ValueError):
        assert thermostat_type_4._protect_cooling()


def test_thermostat_equipment_protect_heating(thermostat_type_4, thermostat_type_5):
    assert thermostat_type_4._protect_heating() is None
    with pytest.raises(ValueError):
        assert thermostat_type_5._protect_heating()


def test_thermostat_equipment_protect_resistance_heat(thermostat_type_1, thermostat_type_2):
    assert thermostat_type_1._protect_resistance_heat() is None
    with pytest.raises(ValueError):
        assert thermostat_type_2._protect_resistance_heat()


def test_thermostat_equipment_protect_aux_emerg(thermostat_type_1, thermostat_type_2):
    assert thermostat_type_1._protect_aux_emerg() is None
    with pytest.raises(ValueError):
        assert thermostat_type_2._protect_aux_emerg()


def test_thermostat_type_1_total_heating_runtime(thermostat_type_1,
        core_heating_day_set_type_1_entire, metrics_type_1_data):

    total_runtime = thermostat_type_1.total_heating_runtime(core_heating_day_set_type_1_entire)
    assert_allclose(total_runtime, metrics_type_1_data[1]["total_core_heating_runtime"], rtol=1e-3)


def test_thermostat_type_1_total_emergency_heating_runtime(thermostat_type_1,
        core_heating_day_set_type_1_entire, metrics_type_1_data):

    total_runtime = thermostat_type_1.total_emergency_heating_runtime(core_heating_day_set_type_1_entire)
    assert_allclose(total_runtime, metrics_type_1_data[1]["total_emergency_heating_core_day_runtime"], rtol=1e-3)


def test_thermostat_type_1_total_auxiliary_heating_runtime(thermostat_type_1,
        core_heating_day_set_type_1_entire, metrics_type_1_data):

    total_runtime = thermostat_type_1.total_auxiliary_heating_runtime(core_heating_day_set_type_1_entire)
    assert_allclose(total_runtime, metrics_type_1_data[1]["total_auxiliary_heating_core_day_runtime"], rtol=1e-3)


def test_thermostat_type_1_total_cooling_runtime(thermostat_type_1,
        core_cooling_day_set_type_1_entire, metrics_type_1_data):

    total_runtime = thermostat_type_1.total_cooling_runtime(core_cooling_day_set_type_1_entire)
    assert_allclose(total_runtime, metrics_type_1_data[0]["total_core_cooling_runtime"], rtol=1e-3)


def test_thermostat_type_1_get_resistance_heat_utilization_bins_rhu1(thermostat_type_1,
        core_heating_day_set_type_1_entire, metrics_type_1_data):

    start = 0
    stop = 60
    step = 5
    temperature_bins = list(t for t in range(start, stop+step, step))
    rhu_runtime = thermostat_type_1.get_resistance_heat_utilization_runtime(
            core_heating_day_set_type_1_entire)
    rhu = thermostat_type_1.get_resistance_heat_utilization_bins(
            rhu_runtime,
            temperature_bins,
            core_heating_day_set_type_1_entire)

    assert len(rhu) == 12

    for item in rhu.itertuples():
        bin_name = thermostat_type_1._format_rhu('rhu1', item.Index.left, item.Index.right, duty_cycle=None)
        bin_value = item.rhu
        assert_allclose(bin_value, metrics_type_1_data[1][bin_name], rtol=1e-3)

    rhu = thermostat_type_1.get_resistance_heat_utilization_bins(
            None,
            temperature_bins,
            core_heating_day_set_type_1_entire)

    assert rhu is None

def test_thermostat_type_1_get_resistance_heat_utilization_bins_rhu2(thermostat_type_1,
        core_heating_day_set_type_1_entire, metrics_type_1_data):

    start = 0
    stop = 60
    step = 5
    VAR_MIN_RHU_RUNTIME = 30 * 60  # Unit is in minutes (30 hours * 60 minutes)
    temperature_bins = list(t for t in range(start, stop+step, step))
    rhu_runtime = thermostat_type_1.get_resistance_heat_utilization_runtime(
            core_heating_day_set_type_1_entire)
    rhu = thermostat_type_1.get_resistance_heat_utilization_bins(
            rhu_runtime,
            temperature_bins,
            core_heating_day_set_type_1_entire,
            VAR_MIN_RHU_RUNTIME)

    assert len(rhu) == 12

    for item in rhu.itertuples():
        bin_name = thermostat_type_1._format_rhu('rhu2', item.Index.left, item.Index.right, duty_cycle=None)
        bin_value = item.rhu
        assert_allclose(bin_value, metrics_type_1_data[1][bin_name], rtol=1e-3)

    rhu = thermostat_type_1.get_resistance_heat_utilization_bins(
            None,
            temperature_bins,
            core_heating_day_set_type_1_entire,
            VAR_MIN_RHU_RUNTIME)

    assert rhu is None


def test_thermostat_types_2_get_resistance_heat_utilization_runtime_rhu(
        core_heating_day_set_type_1_entire, thermostat_type_2):

    with pytest.raises(ValueError):
        thermostat_type_2.get_resistance_heat_utilization_runtime(
            core_heating_day_set_type_1_entire)


@pytest.fixture(params=range(2))
def core_days(request, thermostat_type_1, core_heating_day_set_type_1_entire,
        core_cooling_day_set_type_1_entire):

    tests = [
        (thermostat_type_1, core_cooling_day_set_type_1_entire, 0, "cooling"),
        (thermostat_type_1, core_heating_day_set_type_1_entire, 1, "heating"),
    ]

    return tests[request.param]


def test_day_counts(core_days, metrics_type_1_data):
    thermostat, core_day_set, i, heating_or_cooling = core_days
    n_both, n_days_insufficient = thermostat.get_ignored_days(core_day_set)
    n_core_days = thermostat.get_core_day_set_n_days(core_day_set)
    n_days_in_inputfile_date_range = thermostat.get_inputfile_date_range(core_day_set)
    assert n_both == metrics_type_1_data[i]["n_days_both_heating_and_cooling"]
    assert n_days_insufficient == metrics_type_1_data[i]["n_days_insufficient_data"]
    assert n_core_days == metrics_type_1_data[i]["n_core_{}_days".format(heating_or_cooling)]
    assert n_days_in_inputfile_date_range == metrics_type_1_data[i]["n_days_in_inputfile_date_range"]
