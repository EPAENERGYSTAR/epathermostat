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
        'n_core_cooling_days': 176,
        'baseline_percentile_core_cooling_comfort_temperature': 70.9,
        'regional_average_baseline_cooling_comfort_temperature': 73.0,
        'percent_savings_baseline_percentile': 7.986050817651249,
        'avoided_daily_mean_core_day_runtime_baseline_percentile': 26.872153009996985,
        'avoided_total_core_day_runtime_baseline_percentile': 4729.498929759469,
        'baseline_daily_mean_core_day_runtime_baseline_percentile': 336.4886302827243,
        'baseline_total_core_day_runtime_baseline_percentile': 59221.99892975947,
        '_daily_mean_core_day_demand_baseline_baseline_percentile': 12.29985256021468,
        'percent_savings_baseline_regional': -9.264189796843251,
        'avoided_daily_mean_core_day_runtime_baseline_regional': -26.25147191424486,
        'avoided_total_core_day_runtime_baseline_regional': -4620.259056907095,
        'baseline_daily_mean_core_day_runtime_baseline_regional': 283.3650053584824,
        'baseline_total_core_day_runtime_baseline_regional': 49872.240943092904,
        '_daily_mean_core_day_demand_baseline_baseline_regional': 10.357995703169285,
        'mean_demand': 11.317580084259756,
        'tau': 8.35999604771793,
        'alpha': 27.357127139160706,
        'mean_sq_err': 2749.7065562832913,
        'root_mean_sq_err': 52.43764445780618,
        'cv_root_mean_sq_err': 0.16936322291276576,
        'mean_abs_pct_err': 0.1278259715930032,
        'mean_abs_err': 39.57702702858937,
        'total_core_cooling_runtime': 54492.5,
        'daily_mean_core_cooling_runtime': 309.61647727272725,
        'core_cooling_days_mean_indoor_temperature': 71.88806818181817,
        'core_cooling_days_mean_outdoor_temperature': 74.60005241477273,
        'core_mean_indoor_temperature': 71.88806818181817,
        'core_mean_outdoor_temperature': 74.60005241477273},
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
        'percent_savings_baseline_percentile': 8.854957643203448,
        'avoided_daily_mean_core_day_runtime_baseline_percentile': 29.399405403610444,
        'avoided_total_core_day_runtime_baseline_percentile': 3910.1209186801893,
        'baseline_daily_mean_core_day_runtime_baseline_percentile': 332.01068359909914,
        'baseline_total_core_day_runtime_baseline_percentile': 44157.42091868019,
        '_daily_mean_core_day_demand_baseline_baseline_percentile': 14.097762336112046,
        'percent_savings_baseline_regional': 3.259231164502472,
        'avoided_daily_mean_core_day_runtime_baseline_regional': 10.195082388706052,
        'avoided_total_core_day_runtime_baseline_regional': 1355.9459576979048,
        'baseline_daily_mean_core_day_runtime_baseline_regional': 312.80636058419475,
        'baseline_total_core_day_runtime_baseline_regional': 41603.2459576979,
        '_daily_mean_core_day_demand_baseline_baseline_regional': 13.28231272842122,
        'mean_demand': 12.849411452609838,
        'tau': 12.821237494206857,
        'alpha': 23.550594461976353,
        'mean_sq_err': 6282.739665533876,
        'root_mean_sq_err': 79.26373486995094,
        'cv_root_mean_sq_err': 0.26193252063376854,
        'mean_abs_pct_err': 0.20152856084124615,
        'mean_abs_err': 60.98481538906681,
        'total_core_heating_runtime': 40247.3,
        'daily_mean_core_heating_runtime': 302.61127819548875,
        'core_heating_days_mean_indoor_temperature': 68.62462406015037,
        'core_heating_days_mean_outdoor_temperature': 43.35078979323308,
        'core_mean_indoor_temperature': 68.62462406015037,
        'core_mean_outdoor_temperature': 43.35078979323308,
        'total_auxiliary_heating_core_day_runtime': 1921.2,
        'total_emergency_heating_core_day_runtime': 110.0,
        'rhu1_00F_to_05F': nan,
        'rhu1_05F_to_10F': nan,
        'rhu1_10F_to_15F': nan,
        'rhu1_15F_to_20F': 0.898346683326268,
        'rhu1_20F_to_25F': 0.6045587903407809,
        'rhu1_25F_to_30F': 0.12034338820193748,
        'rhu1_30F_to_35F': 0.06471454785103249,
        'rhu1_35F_to_40F': 0.03953822816729378,
        'rhu1_40F_to_45F': 0.03611635734408137,
        'rhu1_45F_to_50F': 0.01094695188206484,
        'rhu1_50F_to_55F': 0.0,
        'rhu1_55F_to_60F': 0.013987335790568002,
        'rhu1_30F_to_45F': 0.04547198421543015,
        'rhu2_00F_to_05F': nan,
        'rhu2_05F_to_10F': nan,
        'rhu2_10F_to_15F': nan,
        'rhu2_15F_to_20F': 0.898346683326268,
        'rhu2_20F_to_25F': 0.6045587903407809,
        'rhu2_25F_to_30F': nan,
        'rhu2_30F_to_35F': 0.06471454785103249,
        'rhu2_35F_to_40F': 0.03953822816729378,
        'rhu2_40F_to_45F': 0.03611635734408137,
        'rhu2_45F_to_50F': 0.01094695188206484,
        'rhu2_50F_to_55F': 0.0,
        'rhu2_55F_to_60F': nan,
        'rhu2_30F_to_45F': 0.04547198421543015}] 


    return data
