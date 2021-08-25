import pytest
import numpy as np
from numpy.testing import assert_allclose
from numpy import isnan
import pandas as pd

from datetime import datetime

from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path

from .fixtures.two_stage import (
        thermostat_na_2_hp_2,
        thermostat_fu_2_ce_2,
        thermostat_furnace_or_boiler_two_stage_none_single_stage,
        thermostat_hpeb_2_hp_2,
        core_heating_day_set_hpeb_2_hp_2_entire,
        core_cooling_day_set_hpeb_2_hp_2_entire,
        )

from .fixtures.metrics_data import (
        metrics_hpeb_2_hp_2_data,
        )


def test_thermostat_hpeb_2_hp_2_get_core_heating_days(thermostat_hpeb_2_hp_2):
    core_heating_day_sets = thermostat_hpeb_2_hp_2.get_core_heating_days()
    assert len(core_heating_day_sets) == 1


def test_thermostat_hpeb_2_hp_2_get_core_cooling_days(thermostat_hpeb_2_hp_2):
    core_cooling_day_sets = thermostat_hpeb_2_hp_2.get_core_cooling_days()
    assert len(core_cooling_day_sets) == 1


def test_thermostat_fu_2_ce_2_get_core_heating_days(thermostat_fu_2_ce_2):
    core_heating_day_sets = thermostat_fu_2_ce_2.get_core_heating_days()
    assert len(core_heating_day_sets) == 1


def test_thermostat_fu_2_ce_2_get_core_cooling_days(thermostat_fu_2_ce_2):
    core_cooling_day_sets = thermostat_fu_2_ce_2.get_core_cooling_days()
    assert len(core_cooling_day_sets) == 1


def test_thermostat_na_2_hp_2(thermostat_na_2_hp_2):
    with pytest.raises(ValueError):
        core_heating_day_sets = thermostat_na_2_hp_2.get_core_heating_days()


def test_thermostat_na_2_hp_2(thermostat_na_2_hp_2):
    core_cooling_day_sets = thermostat_na_2_hp_2.get_core_cooling_days()
    assert len(core_cooling_day_sets) == 1


def test_thermostat_furnace_or_boiler_two_stage_none_single_stage(thermostat_furnace_or_boiler_two_stage_none_single_stage):
    with pytest.raises(ValueError):
        core_cooling_day_sets = thermostat_furnace_or_boiler_two_stage_none_single_stage.get_core_cooling_days()


def test_thermostat_furnace_or_boiler_two_stage_none_single_stage(thermostat_furnace_or_boiler_two_stage_none_single_stage):
    core_heating_day_sets = thermostat_furnace_or_boiler_two_stage_none_single_stage.get_core_heating_days()
    assert len(core_heating_day_sets) == 1


def test_thermostat_core_heating_day_set_attributes(core_heating_day_set_hpeb_2_hp_2_entire):

    assert isinstance(core_heating_day_set_hpeb_2_hp_2_entire.name, str)
    assert isinstance(core_heating_day_set_hpeb_2_hp_2_entire.daily, pd.Series)
    assert isinstance(core_heating_day_set_hpeb_2_hp_2_entire.hourly, pd.Series)
    assert core_heating_day_set_hpeb_2_hp_2_entire.daily.shape == (365,)
    assert core_heating_day_set_hpeb_2_hp_2_entire.hourly.shape == (8760,)
    assert (
        isinstance(core_heating_day_set_hpeb_2_hp_2_entire.start_date, datetime)
        or isinstance(core_heating_day_set_hpeb_2_hp_2_entire.start_date, np.datetime64)
    )
    assert (
        isinstance(core_heating_day_set_hpeb_2_hp_2_entire.end_date, datetime)
        or isinstance(core_heating_day_set_hpeb_2_hp_2_entire.end_date, np.datetime64)
    )


def test_thermostat_core_cooling_day_set_attributes(core_cooling_day_set_hpeb_2_hp_2_entire):

    assert isinstance(core_cooling_day_set_hpeb_2_hp_2_entire.name, str)
    assert isinstance(core_cooling_day_set_hpeb_2_hp_2_entire.daily, pd.Series)
    assert isinstance(core_cooling_day_set_hpeb_2_hp_2_entire.hourly, pd.Series)
    assert core_cooling_day_set_hpeb_2_hp_2_entire.daily.shape == (365,)
    assert core_cooling_day_set_hpeb_2_hp_2_entire.hourly.shape == (8760,)
    assert (
        isinstance(core_cooling_day_set_hpeb_2_hp_2_entire.start_date, datetime)
        or isinstance(core_cooling_day_set_hpeb_2_hp_2_entire.start_date, np.datetime64)
    )
    assert (
        isinstance(core_cooling_day_set_hpeb_2_hp_2_entire.end_date, datetime)
        or isinstance(core_cooling_day_set_hpeb_2_hp_2_entire.end_date, np.datetime64)
    )


def test_thermostat_hpeb_2_hp_2_total_heating_runtime(thermostat_hpeb_2_hp_2,
        core_heating_day_set_hpeb_2_hp_2_entire, metrics_hpeb_2_hp_2_data):

    total_runtime = thermostat_hpeb_2_hp_2.total_heating_runtime(core_heating_day_set_hpeb_2_hp_2_entire)
    assert_allclose(total_runtime, metrics_hpeb_2_hp_2_data[1]["total_core_heating_runtime"], rtol=1e-3)


def test_thermostat_hpeb_2_hp_2_total_emergency_heating_runtime(thermostat_hpeb_2_hp_2,
        core_heating_day_set_hpeb_2_hp_2_entire, metrics_hpeb_2_hp_2_data):

    total_runtime = thermostat_hpeb_2_hp_2.total_emergency_heating_runtime(core_heating_day_set_hpeb_2_hp_2_entire)
    assert_allclose(total_runtime, metrics_hpeb_2_hp_2_data[1]["total_emergency_heating_core_day_runtime"], rtol=1e-3)


def test_thermostat_hpeb_2_hp_2_total_auxiliary_heating_runtime(thermostat_hpeb_2_hp_2,
        core_heating_day_set_hpeb_2_hp_2_entire, metrics_hpeb_2_hp_2_data):

    total_runtime = thermostat_hpeb_2_hp_2.total_auxiliary_heating_runtime(core_heating_day_set_hpeb_2_hp_2_entire)
    assert_allclose(total_runtime, metrics_hpeb_2_hp_2_data[1]["total_auxiliary_heating_core_day_runtime"], rtol=1e-3)


def test_thermostat_hpeb_2_hp_2_total_cooling_runtime(thermostat_hpeb_2_hp_2,
        core_cooling_day_set_hpeb_2_hp_2_entire, metrics_hpeb_2_hp_2_data):

    total_runtime = thermostat_hpeb_2_hp_2.total_cooling_runtime(core_cooling_day_set_hpeb_2_hp_2_entire)
    assert_allclose(total_runtime, metrics_hpeb_2_hp_2_data[0]["total_core_cooling_runtime"], rtol=1e-3)


def test_thermostat_hpeb_2_hp_2_get_resistance_heat_utilization_bins_rhu1(thermostat_hpeb_2_hp_2,
        core_heating_day_set_hpeb_2_hp_2_entire, metrics_hpeb_2_hp_2_data):

    start = 0
    stop = 60
    step = 5
    temperature_bins = list(t for t in range(start, stop+step, step))
    rhu_runtime = thermostat_hpeb_2_hp_2.get_resistance_heat_utilization_runtime(
            core_heating_day_set_hpeb_2_hp_2_entire)
    rhu = thermostat_hpeb_2_hp_2.get_resistance_heat_utilization_bins(
            rhu_runtime,
            temperature_bins,
            core_heating_day_set_hpeb_2_hp_2_entire)

    assert len(rhu) == 12

    for item in rhu.itertuples():
        bin_name = thermostat_hpeb_2_hp_2._format_rhu('rhu1', item.Index.left, item.Index.right, duty_cycle=None)
        bin_value = item.rhu
        assert_allclose(bin_value, metrics_hpeb_2_hp_2_data[1][bin_name], rtol=1e-3)


def test_thermostat_hpeb_2_hp_2_get_resistance_heat_utilization_bins_rhu2(thermostat_hpeb_2_hp_2,
        core_heating_day_set_hpeb_2_hp_2_entire, metrics_hpeb_2_hp_2_data):

    start = 0
    stop = 60
    step = 5
    VAR_MIN_RHU_RUNTIME = 30 * 60  # Unit is in minutes (30 hours * 60 minutes)
    temperature_bins = list(t for t in range(start, stop+step, step))
    rhu_runtime = thermostat_hpeb_2_hp_2.get_resistance_heat_utilization_runtime(
            core_heating_day_set_hpeb_2_hp_2_entire)
    rhu = thermostat_hpeb_2_hp_2.get_resistance_heat_utilization_bins(
            rhu_runtime,
            temperature_bins,
            core_heating_day_set_hpeb_2_hp_2_entire,
            VAR_MIN_RHU_RUNTIME)

    assert len(rhu) == 12

    for item in rhu.itertuples():
        bin_name = thermostat_hpeb_2_hp_2._format_rhu('rhu2', item.Index.left, item.Index.right, duty_cycle=None)
        bin_value = item.rhu
        assert_allclose(bin_value, metrics_hpeb_2_hp_2_data[1][bin_name], rtol=1e-3)



@pytest.fixture(params=range(2))
def core_days(request, thermostat_hpeb_2_hp_2,
        core_heating_day_set_hpeb_2_hp_2_entire,
        core_cooling_day_set_hpeb_2_hp_2_entire):

    tests = [
        (
            thermostat_hpeb_2_hp_2,
            core_cooling_day_set_hpeb_2_hp_2_entire,
            0,
            "cooling"
        ),
        (
            thermostat_hpeb_2_hp_2,
            core_heating_day_set_hpeb_2_hp_2_entire,
            1,
            "heating"
        ),
    ]

    return tests[request.param]


def test_day_counts(core_days, metrics_hpeb_2_hp_2_data):
    thermostat, core_day_set, i, heating_or_cooling = core_days
    n_both, n_days_insufficient = thermostat.get_ignored_days(core_day_set)
    n_core_days = thermostat.get_core_day_set_n_days(core_day_set)
    n_days_in_inputfile_date_range = thermostat.get_inputfile_date_range(core_day_set)
    assert n_both == metrics_hpeb_2_hp_2_data[i]["n_days_both_heating_and_cooling"]
    assert n_days_insufficient == metrics_hpeb_2_hp_2_data[i]["n_days_insufficient_data"]
    assert n_core_days == metrics_hpeb_2_hp_2_data[i]["n_core_{}_days".format(heating_or_cooling)]
    assert n_days_in_inputfile_date_range == metrics_hpeb_2_hp_2_data[i]["n_days_in_inputfile_date_range"]
