from thermostat.importers import from_csv
from thermostat.importers import get_single_thermostat
from thermostat.util.testing import get_data_path
from thermostat.core import Thermostat, CoreDaySet
from tempfile import TemporaryDirectory

import pandas as pd
import numpy as np
from numpy import nan

import pytest

''' Abbreviations used in this file:

    XX - Heating system type: fu (furnace), hp (heat pump),  er (electric resistance), ot (other)
    XX - Cooling system type: ce (central), hp (heat pump), 

    YY - backup: eb (electric backup), ne (non electric backup, df (dual fuel), na (N/A)

    Z - speed: 1 (single stage), 2 (two stage), v (variable)
'''

@pytest.fixture(scope="session", params=["../data/two_stage/metadata_furnace_or_boiler_two_stage_central_two_stage.csv"])
def thermostat_fu_2_ce_2(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/two_stage/metadata_furnace_or_boiler_two_stage_none_single_stage.csv"])
def thermostat_furnace_or_boiler_two_stage_none_single_stage(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/two_stage/metadata_heat_pump_electric_backup_two_stage_heat_pump_two_stage.csv"])
def thermostat_hpeb_2_hp_2(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/two_stage/metadata_none_two_stage_heat_pump_two_stage.csv"])
def thermostat_na_2_hp_2(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session")
def core_heating_day_set_hpeb_2_hp_2_entire(thermostat_hpeb_2_hp_2):
    return thermostat_hpeb_2_hp_2.get_core_heating_days(method="entire_dataset")[0]

@pytest.fixture(scope="session")
def core_cooling_day_set_hpeb_2_hp_2_entire(thermostat_hpeb_2_hp_2):
    return thermostat_hpeb_2_hp_2.get_core_cooling_days(method="entire_dataset")[0]


@pytest.fixture(scope="session")
def metrics_hpeb_2_hp_2_data():
    data = \
    [{'_daily_mean_core_day_demand_baseline_baseline_percentile': 12.606760008550685,
    '_daily_mean_core_day_demand_baseline_baseline_regional': 10.562788562873564,
    'alpha': 28.48315881979677,
    'avoided_daily_mean_core_day_runtime_baseline_percentile': 30.53061871305234,
    'avoided_daily_mean_core_day_runtime_baseline_regional': -27.68814459729872,
    'avoided_total_core_day_runtime_baseline_percentile': 5403.919512210265,
    'avoided_total_core_day_runtime_baseline_regional': -4900.801593721873,
    'baseline_daily_mean_core_day_runtime_baseline_percentile': 359.08034752661166,
    'baseline_daily_mean_core_day_runtime_baseline_regional': 300.86158421626055,
    'baseline_percentile_core_cooling_comfort_temperature': 70.8,
    'baseline_total_core_day_runtime_baseline_percentile': 63557.221512210264,
    'baseline_total_core_day_runtime_baseline_regional': 53252.50040627812,
    'climate_zone': 'Mixed-Humid',
    'cool_stage': 'two_stage',
    'cool_type': 'heat_pump',
    'core_cooling_days_mean_indoor_temperature': 71.87485875706216,
    'core_cooling_days_mean_outdoor_temperature': 74.53503144067797,
    'core_mean_indoor_temperature': 71.87485875706216,
    'core_mean_outdoor_temperature': 74.53503144067797,
    'ct_identifier': 'c61badb0e0c0a7e06932de804af43111',
    'cv_root_mean_sq_err': 0.16357602780022015,
    'daily_mean_core_cooling_runtime': 328.5497288135593,
    'end_date': '2018-12-31T00:00:00',
    'heat_stage': 'two_stage',
    'heat_type': 'heat_pump_electric_backup',
    'heating_or_cooling': 'cooling_ALL',
    'mean_abs_err': 40.78334959625454,
    'mean_abs_pct_err': 0.12413143588195652,
    'mean_demand': 11.534876833436256,
    'mean_sq_err': 2888.294955208049,
    'n_core_cooling_days': 177,
    'n_days_both_heating_and_cooling': 19,
    'n_days_in_inputfile_date_range': 364,
    'n_days_insufficient_data': 14,
    'percent_savings_baseline_percentile': 8.50244768986966,
    'percent_savings_baseline_regional': -9.202951140946054,
    'regional_average_baseline_cooling_comfort_temperature': 73.0,
    'root_mean_sq_err': 53.742859574161564,
    'start_date': '2018-01-01T00:00:00',
    'station': '723170',
    'sw_version': '2.0.0a3',
    'tau': 8.628075151655493,
    'total_core_cooling_runtime': 58153.301999999996},
    {'_daily_mean_core_day_demand_baseline_baseline_percentile': 14.695315526664897,
    '_daily_mean_core_day_demand_baseline_baseline_regional': 13.87197893888318,
    'alpha': 24.12888815088287,
    'avoided_daily_mean_core_day_runtime_baseline_percentile': 30.20112844422813,
    'avoided_daily_mean_core_day_runtime_baseline_regional': 10.334932007113602,
    'avoided_total_core_day_runtime_baseline_percentile': 4016.750083082341,
    'avoided_total_core_day_runtime_baseline_regional': 1374.545956946109,
    'baseline_daily_mean_core_day_runtime_baseline_percentile': 354.58162468482965,
    'baseline_daily_mean_core_day_runtime_baseline_regional': 334.7154282477151,
    'baseline_percentile_core_heating_comfort_temperature': 69.9,
    'baseline_total_core_day_runtime_baseline_percentile': 47159.35608308234,
    'baseline_total_core_day_runtime_baseline_regional': 44517.15195694611,
    'climate_zone': 'Mixed-Humid',
    'cool_stage': 'two_stage',
    'cool_type': 'heat_pump',
    'core_heating_days_mean_indoor_temperature': 68.62462406015037,
    'core_heating_days_mean_outdoor_temperature': 43.35078979323308,
    'core_mean_indoor_temperature': 68.62462406015037,
    'core_mean_outdoor_temperature': 43.35078979323308,
    'ct_identifier': 'c61badb0e0c0a7e06932de804af43111',
    'cv_root_mean_sq_err': 0.2499173059502313,
    'daily_mean_core_heating_runtime': 324.3804962406015,
    'end_date': '2018-12-31T00:00:00',
    'heat_stage': 'two_stage',
    'heat_type': 'heat_pump_electric_backup',
    'heating_or_cooling': 'heating_ALL',
    'mean_abs_err': 62.13151151808365,
    'mean_abs_pct_err': 0.19153898658567647,
    'mean_demand': 13.443657006165555,
    'mean_sq_err': 6572.069220018736,
    'n_core_heating_days': 133,
    'n_days_both_heating_and_cooling': 19,
    'n_days_in_inputfile_date_range': 364,
    'n_days_insufficient_data': 14,
    'percent_savings_baseline_percentile': 8.517398066262583,
    'percent_savings_baseline_regional': 3.0876772132131776,
    'regional_average_baseline_heating_comfort_temperature': 69,
    'rhu1_00F_to_05F': nan,
    'rhu1_05F_to_10F': nan,
    'rhu1_10F_to_15F': nan,
    'rhu1_15F_to_20F': 0.8938117141436386,
    'rhu1_20F_to_25F': 0.5963729624072203,
    'rhu1_25F_to_30F': 0.11484128153249978,
    'rhu1_30F_to_35F': 0.06079135092511376,
    'rhu1_30F_to_45F': 0.042601115604947795,
    'rhu1_35F_to_40F': 0.03708658025696731,
    'rhu1_40F_to_45F': 0.033719108302466015,
    'rhu1_45F_to_50F': 0.009995474641406793,
    'rhu1_50F_to_55F': 0.0,
    'rhu1_55F_to_60F': 0.012756025498260699,
    'rhu2_00F_to_05F': nan,
    'rhu2_05F_to_10F': nan,
    'rhu2_10F_to_15F': nan,
    'rhu2_15F_to_20F': 0.8938117141436386,
    'rhu2_20F_to_25F': 0.5963729624072203,
    'rhu2_25F_to_30F': nan,
    'rhu2_30F_to_35F': 0.06079135092511376,
    'rhu2_30F_to_45F': 0.042601115604947795,
    'rhu2_35F_to_40F': 0.03708658025696731,
    'rhu2_40F_to_45F': 0.033719108302466015,
    'rhu2_45F_to_50F': 0.009995474641406793,
    'rhu2_50F_to_55F': 0.0,
    'rhu2_55F_to_60F': nan,
    'root_mean_sq_err': 81.06829972325025,
    'start_date': '2018-01-01T00:00:00',
    'station': '723170',
    'sw_version': '2.0.0a3',
    'tau': 12.16945589758016,
    'total_auxiliary_heating_core_day_runtime': 1921.2,
    'total_core_heating_runtime': 43142.606,
    'total_emergency_heating_core_day_runtime': 110.0}]

    return data
