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

    data = [{'sw_version': '2.0.0a3',
	'ct_identifier': 'c61badb0e0c0a7e06932de804af43111',
	'heat_type': 'heat_pump_electric_backup',
	'heat_stage': 'two_stage',
	'cool_type': 'heat_pump',
	'cool_stage': 'two_stage',
	'heating_or_cooling': 'cooling_ALL',
	'zipcode': '27313',
	'station': '723170',
	'climate_zone': 'Mixed-Humid',
	'start_date': '2018-01-01T00:00:00',
	'end_date': '2018-12-31T00:00:00',
	'n_days_in_inputfile_date_range': 364,
	'n_days_both_heating_and_cooling': 17,
	'n_days_insufficient_data': 51,
	'n_core_cooling_days': 160,
	'baseline_percentile_core_cooling_comfort_temperature': 70.8,
	'regional_average_baseline_cooling_comfort_temperature': 73.0,
	'percent_savings_baseline_percentile': 8.463791321979913,
	'avoided_daily_mean_core_day_runtime_baseline_percentile': 30.115655373809567,
	'avoided_total_core_day_runtime_baseline_percentile': 4818.504859809531,
	'baseline_daily_mean_core_day_runtime_baseline_percentile': 355.81755537380957,
	'baseline_total_core_day_runtime_baseline_percentile': 56930.808859809535,
	'_daily_mean_core_day_demand_baseline_baseline_percentile': 12.482315175044594,
	'percent_savings_baseline_regional': -9.403622697474983,
	'avoided_daily_mean_core_day_runtime_baseline_regional': -27.99521353986586,
	'avoided_total_core_day_runtime_baseline_regional': -4479.234166378537,
	'baseline_daily_mean_core_day_runtime_baseline_regional': 297.70668646013416,
	'baseline_total_core_day_runtime_baseline_regional': 47633.06983362146,
	'_daily_mean_core_day_demand_baseline_baseline_regional': 10.443747459873368,
	'mean_demand': 11.425838066476988,
	'tau': 8.651198370580325,
	'alpha': 28.505733943105504,
	'mean_sq_err': 2864.5864690277967,
	'root_mean_sq_err': 53.521831704714636,
	'cv_root_mean_sq_err': 0.16432766190407436,
	'mean_abs_pct_err': 0.12404402189116978,
	'mean_abs_err': 40.4013736135956,
	'total_core_cooling_runtime': 52112.304000000004,
	'daily_mean_core_cooling_runtime': 325.7019,
	'core_cooling_days_mean_indoor_temperature': 71.86122395833334,
	'core_cooling_days_mean_outdoor_temperature': 74.37230553125,
	'core_mean_indoor_temperature': 71.86122395833334,
	'core_mean_outdoor_temperature': 74.37230553125},
	{'sw_version': '2.0.0a3',
	'ct_identifier': 'c61badb0e0c0a7e06932de804af43111',
	'heat_type': 'heat_pump_electric_backup',
	'heat_stage': 'two_stage',
	'cool_type': 'heat_pump',
	'cool_stage': 'two_stage',
	'heating_or_cooling': 'heating_ALL',
	'zipcode': '27313',
	'station': '723170',
	'climate_zone': 'Mixed-Humid',
	'start_date': '2018-01-01T00:00:00',
	'end_date': '2018-12-31T00:00:00',
	'n_days_in_inputfile_date_range': 364,
	'n_days_both_heating_and_cooling': 17,
	'n_days_insufficient_data': 51,
	'n_core_heating_days': 116,
	'baseline_percentile_core_heating_comfort_temperature': 70.0,
	'regional_average_baseline_heating_comfort_temperature': 69,
	'percent_savings_baseline_percentile': 9.514796083459109,
	'avoided_daily_mean_core_day_runtime_baseline_percentile': 33.699673877299716,
	'avoided_total_core_day_runtime_baseline_percentile': 3909.162169766767,
	'baseline_daily_mean_core_day_runtime_baseline_percentile': 354.18177732557547,
	'baseline_total_core_day_runtime_baseline_percentile': 41085.08616976676,
	'_daily_mean_core_day_demand_baseline_baseline_percentile': 13.718239201708988,
	'percent_savings_baseline_regional': 3.147418518670501,
	'avoided_daily_mean_core_day_runtime_baseline_regional': 10.414707505654109,
	'avoided_total_core_day_runtime_baseline_regional': 1208.1060706558767,
	'baseline_daily_mean_core_day_runtime_baseline_regional': 330.89681095392996,
	'baseline_total_core_day_runtime_baseline_regional': 38384.03007065588,
	'_daily_mean_core_day_demand_baseline_baseline_regional': 12.816361242594352,
	'mean_demand': 12.412976715425232,
	'tau': 13.024456363883589,
	'alpha': 25.81831181959944,
	'mean_sq_err': 6287.119332008238,
	'root_mean_sq_err': 79.29135723399013,
	'cv_root_mean_sq_err': 0.2474127459251007,
	'mean_abs_pct_err': 0.18942391878742224,
	'mean_abs_err': 60.70697593640847,
	'total_core_heating_runtime': 37175.924000000006,
	'daily_mean_core_heating_runtime': 320.4821034482759,
	'core_heating_days_mean_indoor_temperature': 68.65607040229885,
	'core_heating_days_mean_outdoor_temperature': 43.64093413793104,
	'core_mean_indoor_temperature': 68.65607040229885,
	'core_mean_outdoor_temperature': 43.64093413793104,
	'total_auxiliary_heating_core_day_runtime': 1512.6000000000001,
	'total_emergency_heating_core_day_runtime': 0.0,
	'rhu1_00F_to_05F': nan,
	'rhu1_05F_to_10F': nan,
	'rhu1_10F_to_15F': nan,
	'rhu1_15F_to_20F': nan,
	'rhu1_20F_to_25F': 0.5963729624072203,
	'rhu1_25F_to_30F': 0.11484128153249978,
	'rhu1_30F_to_35F': 0.07377455861954366,
	'rhu1_35F_to_40F': 0.04290403220944863,
	'rhu1_40F_to_45F': 0.03502547046482063,
	'rhu1_45F_to_50F': 0.013218695583036512,
	'rhu1_50F_to_55F': 0.0,
	'rhu1_55F_to_60F': 0.014154065085746858,
	'rhu1_30F_to_45F': 0.048018860280357595,
	'rhu2_00F_to_05F': nan,
	'rhu2_05F_to_10F': nan,
	'rhu2_10F_to_15F': nan,
	'rhu2_15F_to_20F': nan,
	'rhu2_20F_to_25F': 0.5963729624072203,
	'rhu2_25F_to_30F': nan,
	'rhu2_30F_to_35F': 0.07377455861954366,
	'rhu2_35F_to_40F': 0.04290403220944863,
	'rhu2_40F_to_45F': 0.03502547046482063,
	'rhu2_45F_to_50F': 0.013218695583036512,
	'rhu2_50F_to_55F': 0.0,
	'rhu2_55F_to_60F': nan,
	'rhu2_30F_to_45F': 0.048018860280357595}]

    return data
