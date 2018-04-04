from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path

import numpy as np
import pandas as pd

from datetime import datetime

import pytest

from fixtures.thermostats import thermostat_type_1
from fixtures.thermostats import thermostat_type_2
from fixtures.thermostats import thermostat_type_3
from fixtures.thermostats import thermostat_type_4
from fixtures.thermostats import thermostat_type_5
from fixtures.thermostats import core_heating_day_set_type_1_entire
from fixtures.thermostats import core_heating_day_set_type_2
from fixtures.thermostats import core_heating_day_set_type_3
from fixtures.thermostats import core_heating_day_set_type_4
from fixtures.thermostats import core_cooling_day_set_type_1_entire
from fixtures.thermostats import core_cooling_day_set_type_2
from fixtures.thermostats import core_cooling_day_set_type_3
from fixtures.thermostats import core_cooling_day_set_type_5
from fixtures.thermostats import metrics_type_1_data
from fixtures.thermostats import thermostat_zero_days

from numpy.testing import assert_allclose
from numpy import isnan


def test_zero_days_warning(thermostat_zero_days):
    output = thermostat_zero_days.calculate_epa_field_savings_metrics()
    assert isnan(output[0]['daily_mean_core_cooling_runtime'])


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
    core_heating_day_sets = thermostat_type_1.get_core_heating_days(
            method="year_mid_to_mid")
    assert len(core_heating_day_sets) == 5


def test_thermostat_type_1_get_core_cooling_days(thermostat_type_1):
    core_cooling_day_sets = thermostat_type_1.get_core_cooling_days(
            method="year_end_to_end")
    assert len(core_cooling_day_sets) == 4


def test_thermostat_type_2_get_core_heating_days(thermostat_type_2):
    core_heating_day_sets = thermostat_type_2.get_core_heating_days(
            method="year_mid_to_mid")
    assert len(core_heating_day_sets) == 5


def test_thermostat_type_2_get_core_cooling_days(thermostat_type_2):
    core_cooling_day_sets = thermostat_type_2.get_core_cooling_days(
            method="year_end_to_end")
    assert len(core_cooling_day_sets) == 4


def test_thermostat_type_3_get_core_heating_days(thermostat_type_3):
    core_heating_day_sets = thermostat_type_3.get_core_heating_days(
            method="year_mid_to_mid")
    assert len(core_heating_day_sets) == 5


def test_thermostat_type_3_get_core_cooling_days(thermostat_type_3):
    core_cooling_day_sets = thermostat_type_3.get_core_cooling_days(
            method="year_end_to_end")
    assert len(core_cooling_day_sets) == 4


def test_thermostat_type_4_get_core_heating_days(thermostat_type_4):
    core_heating_day_sets = thermostat_type_4.get_core_heating_days(
            method="year_mid_to_mid")
    assert len(core_heating_day_sets) == 5


def test_thermostat_type_4_get_core_cooling_days(thermostat_type_4):
    with pytest.raises(ValueError):
        core_cooling_day_sets = thermostat_type_4.get_core_cooling_days(
                method="year_end_to_end")


def test_thermostat_type_5_get_core_heating_days(thermostat_type_5):
    with pytest.raises(ValueError):
        core_heating_day_sets = thermostat_type_5.get_core_heating_days(
                method="year_mid_to_mid")


def test_thermostat_type_5_get_core_cooling_days(thermostat_type_5):
    core_cooling_day_sets = thermostat_type_5.get_core_cooling_days(
            method="year_end_to_end")
    assert len(core_cooling_day_sets) == 4


def test_thermostat_type_1_get_core_heating_days_with_params(thermostat_type_1):
    core_heating_day_sets = thermostat_type_1.get_core_heating_days(
            min_minutes_heating=0, max_minutes_cooling=0,
            method="year_mid_to_mid")
    assert len(core_heating_day_sets) == 5


def test_thermostat_type_1_get_core_cooling_days_with_params(thermostat_type_1):
    core_heating_day_sets = thermostat_type_1.get_core_cooling_days(
            min_minutes_cooling=0, max_minutes_heating=0,
            method="year_end_to_end")
    assert len(core_heating_day_sets) == 4


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


def test_thermostat_type_1_get_resistance_heat_utilization_bins(thermostat_type_1,
        core_heating_day_set_type_1_entire, metrics_type_1_data):

    bins = thermostat_type_1.get_resistance_heat_utilization_bins(core_heating_day_set_type_1_entire)

    bin_names = [
        'rhu_00F_to_05F',
        'rhu_05F_to_10F',
        'rhu_10F_to_15F',
        'rhu_15F_to_20F',
        'rhu_20F_to_25F',
        'rhu_25F_to_30F',
        'rhu_30F_to_35F',
        'rhu_35F_to_40F',
        'rhu_40F_to_45F',
        'rhu_45F_to_50F',
        'rhu_50F_to_55F',
        'rhu_55F_to_60F',
    ]

    assert len(bins) == 12

    for i, (bin_value, bin_name) in enumerate(zip(bins, bin_names)):
        assert_allclose(bin_value, metrics_type_1_data[1][bin_name], rtol=1e-3)


def test_thermostat_types_2_get_resistance_heat_utilization_bins(
        core_heating_day_set_type_1_entire, thermostat_type_2):

    with pytest.raises(ValueError):
        thermostat_type_2.get_resistance_heat_utilization_bins(
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
