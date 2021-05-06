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

@pytest.fixture(scope="session", params=["../data/two_stage_ert/metadata_furnace_or_boiler_two_stage_central_two_stage.csv"])
def thermostat_ert_fu_2_ce_2(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/two_stage_ert/metadata_furnace_or_boiler_two_stage_none_single_stage.csv"])
def thermostat_ert_fu_2_na_1(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/two_stage_ert/metadata_heat_pump_electric_backup_two_stage_heat_pump_two_stage.csv"])
def thermostat_ert_hpeb_2_hp_2(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/two_stage_ert/metadata_none_two_stage_heat_pump_two_stage.csv"])
def thermostat_ert_na_2_hp_2(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session")
def core_heating_day_set_ert_hpeb_2_hp_2_entire(thermostat_ert_hpeb_2_hp_2):
    return thermostat_ert_hpeb_2_hp_2.get_core_heating_days(method="entire_dataset")[0]

@pytest.fixture(scope="session")
def core_cooling_day_set_ert_hpeb_2_hp_2_entire(thermostat_ert_hpeb_2_hp_2):
    return thermostat_ert_hpeb_2_hp_2.get_core_cooling_days(method="entire_dataset")[0]


@pytest.fixture(scope="session")
def metrics_ert_hpeb_2_hp_2_data():
    data = \
    [{'_daily_mean_core_day_demand_baseline_baseline_percentile': 12.25281033824587,
    '_daily_mean_core_day_demand_baseline_baseline_regional': 10.312943007859884,
    'alpha': 27.60856756116322,
    'avoided_daily_mean_core_day_runtime_baseline_percentile': 27.102996583034777,
    'avoided_daily_mean_core_day_runtime_baseline_regional': -26.45396166762003,
    'avoided_total_core_day_runtime_baseline_percentile': 4770.1273986141205,
    'avoided_total_core_day_runtime_baseline_regional': -4655.897253501125,
    'baseline_daily_mean_core_day_runtime_baseline_percentile': 338.28254203758024,
    'baseline_daily_mean_core_day_runtime_baseline_regional': 284.7255837869254,
    'baseline_percentile_core_cooling_comfort_temperature': 70.9,
    'baseline_total_core_day_runtime_baseline_percentile': 59537.72739861412,
    'baseline_total_core_day_runtime_baseline_regional': 50111.70274649888,
    'climate_zone': 'Mixed-Humid',
    'cool_stage': 'two_stage',
    'cool_type': 'heat_pump',
    'core_cooling_days_mean_indoor_temperature': 71.88806818181817,
    'core_cooling_days_mean_outdoor_temperature': 74.60005241477273,
    'core_mean_indoor_temperature': 71.88806818181817,
    'core_mean_outdoor_temperature': 74.60005241477273,
    'ct_identifier': 'c61badb0e0c0a7e06932de804af43111',
    'cv_root_mean_sq_err': 0.16788677782925684,
    'daily_mean_core_cooling_runtime': 311.17954545454546,
    'end_date': '2018-12-31T00:00:00',
    'heat_stage': 'two_stage',
    'heat_type': 'heat_pump_electric_backup',
    'heating_or_cooling': 'cooling_ALL',
    'mean_abs_err': 39.55504086253661,
    'mean_abs_pct_err': 0.12711324198625543,
    'mean_demand': 11.27112244288543,
    'mean_sq_err': 2729.323861698708,
    'n_core_cooling_days': 176,
    'n_days_both_heating_and_cooling': 19,
    'n_days_in_inputfile_date_range': 364,
    'n_days_insufficient_data': 14,
    'percent_savings_baseline_percentile': 8.011940675325738,
    'percent_savings_baseline_regional': -9.291037818159984,
    'regional_average_baseline_cooling_comfort_temperature': 73.0,
    'root_mean_sq_err': 52.24293121273641,
    'start_date': '2018-01-01T00:00:00',
    'station': '723170',
    'sw_version': '2.0.0a3',
    'tau': 8.310141458385782,
    'total_core_cooling_runtime': 54767.6},
    {'_daily_mean_core_day_demand_baseline_baseline_percentile': 14.0775234005962,
    '_daily_mean_core_day_demand_baseline_baseline_regional': 13.262372650813058,
    'alpha': 23.730080239253436,
    'avoided_daily_mean_core_day_runtime_baseline_percentile': 29.61940648265708,
    'avoided_daily_mean_core_day_runtime_baseline_regional': 10.275813783215527,
    'avoided_total_core_day_runtime_baseline_percentile': 3939.3810621933917,
    'avoided_total_core_day_runtime_baseline_regional': 1366.683233167665,
    'baseline_daily_mean_core_day_runtime_baseline_percentile': 334.06075986611575,
    'baseline_daily_mean_core_day_runtime_baseline_regional': 314.7171671666742,
    'baseline_percentile_core_heating_comfort_temperature': 69.9,
    'baseline_total_core_day_runtime_baseline_percentile': 44430.08106219339,
    'baseline_total_core_day_runtime_baseline_regional': 41857.38323316767,
    'climate_zone': 'Mixed-Humid',
    'cool_stage': 'two_stage',
    'cool_type': 'heat_pump',
    'core_heating_days_mean_indoor_temperature': 68.62462406015037,
    'core_heating_days_mean_outdoor_temperature': 43.35078979323308,
    'core_mean_indoor_temperature': 68.62462406015037,
    'core_mean_outdoor_temperature': 43.35078979323308,
    'ct_identifier': 'c61badb0e0c0a7e06932de804af43111',
    'cv_root_mean_sq_err': 0.258345382172041,
    'daily_mean_core_heating_runtime': 304.44135338345876,
    'end_date': '2018-12-31T00:00:00',
    'heat_stage': 'two_stage',
    'heat_type': 'heat_pump_electric_backup',
    'heating_or_cooling': 'heating_ALL',
    'mean_abs_err': 60.50847476858618,
    'mean_abs_pct_err': 0.1987524825261593,
    'mean_demand': 12.829343614264856,
    'mean_sq_err': 6185.982599217759,
    'n_core_heating_days': 133,
    'n_days_both_heating_and_cooling': 19,
    'n_days_in_inputfile_date_range': 364,
    'n_days_insufficient_data': 14,
    'percent_savings_baseline_percentile': 8.866472822048268,
    'percent_savings_baseline_regional': 3.265094775644526,
    'regional_average_baseline_heating_comfort_temperature': 69,
    'rhu1_00F_to_05F': nan,
    'rhu1_05F_to_10F': nan,
    'rhu1_10F_to_15F': nan,
    'rhu1_15F_to_20F': 0.8979559976359601,
    'rhu1_20F_to_25F': 0.6045587903407809,
    'rhu1_25F_to_30F': 0.12034338820193748,
    'rhu1_30F_to_35F': 0.06371785003148994,
    'rhu1_30F_to_45F': 0.045160693322785564,
    'rhu1_35F_to_40F': 0.039343105400120544,
    'rhu1_40F_to_45F': 0.03605074276325836,
    'rhu1_45F_to_50F': 0.010863180256371055,
    'rhu1_50F_to_55F': 0.0,
    'rhu1_55F_to_60F': 0.013987335790568002,
    'rhu2_00F_to_05F': nan,
    'rhu2_05F_to_10F': nan,
    'rhu2_10F_to_15F': nan,
    'rhu2_15F_to_20F': 0.8979559976359601,
    'rhu2_20F_to_25F': 0.6045587903407809,
    'rhu2_25F_to_30F': nan,
    'rhu2_30F_to_35F': 0.06371785003148994,
    'rhu2_30F_to_45F': 0.045160693322785564,
    'rhu2_35F_to_40F': 0.039343105400120544,
    'rhu2_40F_to_45F': 0.03605074276325836,
    'rhu2_45F_to_50F': 0.010863180256371055,
    'rhu2_50F_to_55F': 0.0,
    'rhu2_55F_to_60F': nan,
    'root_mean_sq_err': 78.65101778882304,
    'start_date': '2018-01-01T00:00:00',
    'station': '723170',
    'sw_version': '2.0.0a3',
    'tau': 12.84342248121461,
    'total_auxiliary_heating_core_day_runtime': 1921.2,
    'total_core_heating_runtime': 40490.70000000001,
    'total_emergency_heating_core_day_runtime': 110.0}]

    return data
