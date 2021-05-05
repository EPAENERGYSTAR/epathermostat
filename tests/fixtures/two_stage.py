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

    data = [{
        'sw_version': '2.0.0a3',
        'ct_identifier': 'c61badb0e0c0a7e06932de804af43111',
        'heat_type': 'heat_pump_electric_backup',
        'heat_stage': 'two_stage',
        'cool_type': 'heat_pump',
        'cool_stage': 'two_stage',
        'heating_or_cooling': 'cooling_ALL',
        'station': '723170',
        'climate_zone': 'Mixed-Humid',
        'start_date': '2018-01-01T00:00:00',
        'end_date': '2018-12-31T00:00:00',
        'n_days_in_inputfile_date_range': 364,
        'n_days_both_heating_and_cooling': 19,
        'n_days_insufficient_data': 14,
        'n_core_cooling_days': 177,
        'baseline_percentile_core_cooling_comfort_temperature': 70.8,
        'regional_average_baseline_cooling_comfort_temperature': 73.0,
        'percent_savings_baseline_percentile': 8.474979320768478,
        'avoided_daily_mean_core_day_runtime_baseline_percentile': 30.271169072136008,
        'avoided_total_core_day_runtime_baseline_percentile': 5357.996925768073,
        'baseline_daily_mean_core_day_runtime_baseline_percentile': 357.18280749021505,
        'baseline_total_core_day_runtime_baseline_percentile': 63221.356925768065,
        '_daily_mean_core_day_demand_baseline_baseline_percentile': 12.654947644324357,
        'percent_savings_baseline_regional': -9.176617797960848,
        'avoided_daily_mean_core_day_runtime_baseline_regional': -27.47789059576379,
        'avoided_total_core_day_runtime_baseline_regional': -4863.58663545019,
        'baseline_daily_mean_core_day_runtime_baseline_regional': 299.4337478223153,
        'baseline_total_core_day_runtime_baseline_regional': 52999.77336454981,
        '_daily_mean_core_day_demand_baseline_baseline_regional': 10.608904802169207,
        'mean_demand': 11.58244344841379,
        'tau': 8.678846357413157,
        'alpha': 28.224755844834235,
        'mean_sq_err': 2911.8653485099867,
        'root_mean_sq_err': 53.96170260944318,
        'cv_root_mean_sq_err': 0.16506510098742005,
        'mean_abs_pct_err': 0.12487596263133152,
        'mean_abs_err': 40.82340554284342,
        'total_core_cooling_runtime': 57863.36,
        'daily_mean_core_cooling_runtime': 326.9116384180791,
        'core_cooling_days_mean_indoor_temperature': 71.87485875706216,
        'core_cooling_days_mean_outdoor_temperature': 74.53503144067797,
        'core_mean_indoor_temperature': 71.87485875706216,
        'core_mean_outdoor_temperature': 74.53503144067797},
        {
        'sw_version': '2.0.0a3',
        'ct_identifier': 'c61badb0e0c0a7e06932de804af43111',
        'heat_type': 'heat_pump_electric_backup',
        'heat_stage': 'two_stage',
        'cool_type': 'heat_pump',
        'cool_stage': 'two_stage',
        'heating_or_cooling': 'heating_ALL',
        'station': '723170',
        'climate_zone': 'Mixed-Humid',
        'start_date': '2018-01-01T00:00:00',
        'end_date': '2018-12-31T00:00:00',
        'n_days_in_inputfile_date_range': 364,
        'n_days_both_heating_and_cooling': 19,
        'n_days_insufficient_data': 14,
        'n_core_heating_days': 133,
        'baseline_percentile_core_heating_comfort_temperature': 69.9,
        'regional_average_baseline_heating_comfort_temperature': 69,
        'percent_savings_baseline_percentile': 8.497564510061638,
        'avoided_daily_mean_core_day_runtime_baseline_percentile': 29.943342490990563,
        'avoided_total_core_day_runtime_baseline_percentile': 3982.464551301745,
        'baseline_daily_mean_core_day_runtime_baseline_percentile': 352.3755830924944,
        'baseline_total_core_day_runtime_baseline_percentile': 46865.95255130176,
        '_daily_mean_core_day_demand_baseline_baseline_percentile': 14.73165657978787,
        'percent_savings_baseline_regional': 3.0773167907368766,
        'avoided_daily_mean_core_day_runtime_baseline_regional': 10.237295491867794,
        'avoided_total_core_day_runtime_baseline_regional': 1361.5603004184165,
        'baseline_daily_mean_core_day_runtime_baseline_regional': 332.66953609337145,
        'baseline_total_core_day_runtime_baseline_regional': 44245.048300418406,
        '_daily_mean_core_day_demand_baseline_baseline_regional': 13.907811992179099,
        'mean_demand': 13.479824558519654,
        'tau': 12.130016008605418,
        'alpha': 23.919616995142334,
        'mean_sq_err': 6680.195824151183,
        'root_mean_sq_err': 81.73246493377759,
        'cv_root_mean_sq_err': 0.2534872591565411,
        'mean_abs_pct_err': 0.19445314201706065,
        'mean_abs_err': 62.69796227256328,
        'total_core_heating_runtime': 42883.488,
        'daily_mean_core_heating_runtime': 322.43224060150374,
        'core_heating_days_mean_indoor_temperature': 68.62462406015037,
        'core_heating_days_mean_outdoor_temperature': 43.35078979323308,
        'core_mean_indoor_temperature': 68.62462406015037,
        'core_mean_outdoor_temperature': 43.35078979323308,
        'total_auxiliary_heating_core_day_runtime': 1921.2,
        'total_emergency_heating_core_day_runtime': 110.0,
        'rhu1_00F_to_05F': nan,
        'rhu1_05F_to_10F': nan,
        'rhu1_10F_to_15F': nan,
        'rhu1_15F_to_20F': 0.8942762588010572,
        'rhu1_20F_to_25F': 0.5963729624072203,
        'rhu1_25F_to_30F': 0.11484128153249978,
        'rhu1_30F_to_35F': 0.061755889622692225,
        'rhu1_35F_to_40F': 0.03726613965499761,
        'rhu1_40F_to_45F': 0.03378050311337222,
        'rhu1_45F_to_50F': 0.010071854850694823,
        'rhu1_50F_to_55F': 0.0,
        'rhu1_55F_to_60F': 0.012756025498260699,
        'rhu1_30F_to_45F': 0.042893701102214736,
        'rhu2_00F_to_05F': nan,
        'rhu2_05F_to_10F': nan,
        'rhu2_10F_to_15F': nan,
        'rhu2_15F_to_20F': 0.8942762588010572,
        'rhu2_20F_to_25F': 0.5963729624072203,
        'rhu2_25F_to_30F': nan,
        'rhu2_30F_to_35F': 0.061755889622692225,
        'rhu2_35F_to_40F': 0.03726613965499761,
        'rhu2_40F_to_45F': 0.03378050311337222,
        'rhu2_45F_to_50F': 0.010071854850694823,
        'rhu2_50F_to_55F': 0.0,
        'rhu2_55F_to_60F': nan,
        'rhu2_30F_to_45F': 0.042893701102214736}]
    return data
