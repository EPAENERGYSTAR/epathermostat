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
	'n_core_cooling_days': 159,
	'baseline_percentile_core_cooling_comfort_temperature': 70.9,
	'regional_average_baseline_cooling_comfort_temperature': 73.0,
	'percent_savings_baseline_percentile': 7.949942200976018,
	'avoided_daily_mean_core_day_runtime_baseline_percentile': 26.653401651166952,
	'avoided_total_core_day_runtime_baseline_percentile': 4237.890862535545,
	'baseline_daily_mean_core_day_runtime_baseline_percentile': 335.26535133670154,
	'baseline_total_core_day_runtime_baseline_percentile': 53307.19086253554,
	'_daily_mean_core_day_demand_baseline_baseline_percentile': 12.168302421738765,
	'percent_savings_baseline_regional': -9.462769099731771,
	'avoided_daily_mean_core_day_runtime_baseline_regional': -26.678693087249965,
	'avoided_total_core_day_runtime_baseline_regional': -4241.9122008727445,
	'baseline_daily_mean_core_day_runtime_baseline_regional': 281.93325659828463,
	'baseline_total_core_day_runtime_baseline_regional': 44827.38779912725,
	'_daily_mean_core_day_demand_baseline_baseline_regional': 10.232638461909708,
	'mean_demand': 11.200929412370568,
	'tau': 8.371282818608988,
	'alpha': 27.55235198113974,
	'mean_sq_err': 2714.7188218629863,
	'root_mean_sq_err': 52.10296365719503,
	'cv_root_mean_sq_err': 0.16883002654396964,
	'mean_abs_pct_err': 0.1270082906243978,
	'mean_abs_err': 39.19627619582243,
	'total_core_cooling_runtime': 49069.3,
	'daily_mean_core_cooling_runtime': 308.6119496855346,
	'core_cooling_days_mean_indoor_temperature': 71.87575995807128,
	'core_cooling_days_mean_outdoor_temperature': 74.44325500000001,
	'core_mean_indoor_temperature': 71.87575995807128,
	'core_mean_outdoor_temperature': 74.44325500000001},
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
	'percent_savings_baseline_percentile': 9.864301763590625,
	'avoided_daily_mean_core_day_runtime_baseline_percentile': 32.91716771902953,
	'avoided_total_core_day_runtime_baseline_percentile': 3818.391455407425,
	'baseline_daily_mean_core_day_runtime_baseline_percentile': 333.6999263397191,
	'baseline_total_core_day_runtime_baseline_percentile': 38709.19145540742,
	'_daily_mean_core_day_demand_baseline_baseline_percentile': 13.175487715848755,
	'percent_savings_baseline_regional': 3.31499473314762,
	'avoided_daily_mean_core_day_runtime_baseline_regional': 10.312801430761704,
	'avoided_total_core_day_runtime_baseline_regional': 1196.2849659683577,
	'baseline_daily_mean_core_day_runtime_baseline_regional': 311.09556005145134,
	'baseline_total_core_day_runtime_baseline_regional': 36087.08496596836,
	'_daily_mean_core_day_demand_baseline_baseline_regional': 12.2829986055802,
	'mean_demand': 11.875817848732618,
	'tau': 13.624549353183188,
	'alpha': 25.327330079653336,
	'mean_sq_err': 5950.806958626368,
	'root_mean_sq_err': 77.14147366123082,
	'cv_root_mean_sq_err': 0.25646906762535615,
	'mean_abs_pct_err': 0.1972712328788015,
	'mean_abs_err': 59.33578562179039,
	'total_core_heating_runtime': 34890.799999999996,
	'daily_mean_core_heating_runtime': 300.7827586206896,
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
	'rhu1_20F_to_25F': 0.6045587903407809,
	'rhu1_25F_to_30F': 0.12034338820193748,
	'rhu1_30F_to_35F': 0.0771375321534741,
	'rhu1_35F_to_40F': 0.04561882032049096,
	'rhu1_40F_to_45F': 0.03743520199479428,
	'rhu1_45F_to_50F': 0.014363535770523898,
	'rhu1_50F_to_55F': 0.0,
	'rhu1_55F_to_60F': 0.015546218487394958,
	'rhu1_30F_to_45F': 0.050930833104836905,
	'rhu2_00F_to_05F': nan,
	'rhu2_05F_to_10F': nan,
	'rhu2_10F_to_15F': nan,
	'rhu2_15F_to_20F': nan,
	'rhu2_20F_to_25F': 0.6045587903407809,
	'rhu2_25F_to_30F': nan,
	'rhu2_30F_to_35F': 0.0771375321534741,
	'rhu2_35F_to_40F': 0.04561882032049096,
	'rhu2_40F_to_45F': 0.03743520199479428,
	'rhu2_45F_to_50F': 0.014363535770523898,
	'rhu2_50F_to_55F': 0.0,
	'rhu2_55F_to_60F': nan,
	'rhu2_30F_to_45F': 0.050930833104836905}]


    return data
