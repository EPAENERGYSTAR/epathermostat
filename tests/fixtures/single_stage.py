from thermostat.importers import from_csv
from thermostat.importers import get_single_thermostat
from thermostat.util.testing import get_data_path
from thermostat.core import Thermostat, CoreDaySet
from tempfile import TemporaryDirectory

import pandas as pd
import numpy as np
from numpy import nan

import pytest

# Note:
# The following fixtures can be quite slow without a prebuilt weather cache
# they the from_csv command fetches weather data. (This happens with builds on
# travis.)
# To speed this up, spoof the weather source.

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_1_single_utc_offset_0.csv"])
def thermostat_type_1_utc(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_1_single_utc_offset_bad.csv"])
def thermostat_type_1_utc_bad(request):
    thermostats = from_csv(get_data_path(request.param))

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_1_single_bad_zip.csv"])
def thermostat_type_1_zip_bad(request):
    thermostats = from_csv(get_data_path(request.param))
    return list(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_multiple_same_key.csv"])
def thermostats_multiple_same_key(request):
    thermostats = from_csv(get_data_path(request.param))
    return thermostats

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_1_single_too_many_minutes.csv"])
def thermostat_type_1_too_many_minutes(request):
    thermostats = from_csv(get_data_path(request.param))
    return list(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_1_single_data_out_of_order.csv"])
def thermostat_type_1_data_out_of_order(request):
    thermostats = from_csv(get_data_path(request.param))
    return list(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_1_single_data_missing_header.csv"])
def thermostat_type_1_data_missing_header(request):
    thermostats = from_csv(get_data_path(request.param))
    return list(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_1_single.csv"])
def thermostat_type_1(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_1_single.csv"])
def thermostat_type_1_cache(request):
    with TemporaryDirectory() as tempdir:
        thermostats = from_csv(get_data_path(request.param), save_cache=True, cache_path=tempdir)
        return next(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_2_single.csv"])
def thermostat_type_2(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_3_single.csv"])
def thermostat_type_3(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_4_single.csv"])
def thermostat_type_4(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_5_single.csv"])
def thermostat_type_5(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_single_zero_days.csv"])
def thermostat_zero_days(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_1_single_missing_temperature.csv"])
def thermostat_missing_temperature(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_1_single_missing_hours.csv"])
def thermostat_missing_hours(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_1_single_missing_days.csv"])
def thermostat_missing_days(request):
    thermostats = from_csv(get_data_path(request.param))
    return list(thermostats)

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_single_emg_aux_constant_on_outlier.csv"])
def thermostat_emg_aux_constant_on_outlier(request):
    thermostats = from_csv(get_data_path(request.param))
    return thermostats

@pytest.fixture(scope="session")
def core_heating_day_set_type_1_mid_to_mid(thermostat_type_1):
    return thermostat_type_1.get_core_heating_days(method="year_mid_to_mid")[0]

@pytest.fixture(scope="session")
def core_heating_day_set_type_1_entire(thermostat_type_1):
    return thermostat_type_1.get_core_heating_days(method="entire_dataset")[0]

@pytest.fixture(scope="session")
def core_heating_day_set_type_2(thermostat_type_2):
    return thermostat_type_2.get_core_heating_days(method="year_mid_to_mid")[0]

@pytest.fixture(scope="session")
def core_heating_day_set_type_3(thermostat_type_3):
    return thermostat_type_3.get_core_heating_days(method="year_mid_to_mid")[0]

@pytest.fixture(scope="session")
def core_heating_day_set_type_4(thermostat_type_4):
    return thermostat_type_4.get_core_heating_days(method="year_mid_to_mid")[0]

@pytest.fixture(scope="session")
def core_cooling_day_set_type_1_end_to_end(thermostat_type_1):
    return thermostat_type_1.get_core_cooling_days(method="year_end_to_end")[0]

@pytest.fixture(scope="session")
def core_cooling_day_set_type_1_entire(thermostat_type_1):
    return thermostat_type_1.get_core_cooling_days(method="entire_dataset")[0]

@pytest.fixture(scope="session")
def core_cooling_day_set_type_1_empty(thermostat_type_1):
    core_cooling_day_set = thermostat_type_1.get_core_cooling_days(method="entire_dataset")[0]
    core_day_set = CoreDaySet(
        "empty",
        pd.Series(np.tile(False, core_cooling_day_set.daily.shape),
                  index=core_cooling_day_set.daily.index),
        pd.Series(np.tile(False, core_cooling_day_set.hourly.shape),
                  index=core_cooling_day_set.hourly.index),
        core_cooling_day_set.start_date,
        core_cooling_day_set.end_date
    )
    return core_day_set

@pytest.fixture(scope="session")
def core_heating_day_set_type_1_empty(thermostat_type_1):
    core_heating_day_set = thermostat_type_1.get_core_heating_days(method="entire_dataset")[0]
    core_day_set = CoreDaySet(
        "empty",
        pd.Series(np.tile(False, core_heating_day_set.daily.shape),
                  index=core_heating_day_set.daily.index),
        pd.Series(np.tile(False, core_heating_day_set.hourly.shape),
                  index=core_heating_day_set.hourly.index),
        core_heating_day_set.start_date,
        core_heating_day_set.end_date
    )
    return core_day_set

@pytest.fixture(scope="session")
def core_cooling_day_set_type_2(thermostat_type_2):
    return thermostat_type_2.get_core_cooling_days(method="year_end_to_end")[0]

@pytest.fixture(scope="session")
def core_cooling_day_set_type_3(thermostat_type_3):
    return thermostat_type_3.get_core_cooling_days(method="year_end_to_end")[0]

@pytest.fixture(scope="session")
def core_cooling_day_set_type_5(thermostat_type_5):
    return thermostat_type_5.get_core_cooling_days(method="year_end_to_end")[0]

@pytest.fixture(scope="session")
def metrics_type_1_data():
    data = \
    [{'_daily_mean_core_day_demand_baseline_baseline_percentile': 9.976082159783457,
    '_daily_mean_core_day_demand_baseline_baseline_regional': 7.12880601688671,
    'alpha': 44.06852749755634,
    'avoided_daily_mean_core_day_runtime_baseline_percentile': 192.715710435758,
    'avoided_daily_mean_core_day_runtime_baseline_regional': 67.2404434393765,
    'avoided_total_core_day_runtime_baseline_percentile': 57043.85028898437,
    'avoided_total_core_day_runtime_baseline_regional': 19903.171258055445,
    'baseline_daily_mean_core_day_runtime_baseline_percentile': 439.6312509762986,
    'baseline_daily_mean_core_day_runtime_baseline_regional': 314.155983979917,
    'baseline_percentile_core_cooling_comfort_temperature': 69.5,
    'baseline_total_core_day_runtime_baseline_percentile': 130130.85028898438,
    'baseline_total_core_day_runtime_baseline_regional': 92990.17125805543,
    'climate_zone': 'Mixed-Humid',
    'cool_stage': '',
    'cool_type': 'heat_pump',
    'core_cooling_days_mean_indoor_temperature': 73.95971753003002,
    'core_cooling_days_mean_outdoor_temperature': 79.8426321875,
    'core_mean_indoor_temperature': 73.95971753003002,
    'core_mean_outdoor_temperature': 79.8426321875,
    'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
    'cv_root_mean_sq_err': 0.07887381236030344,
    'daily_mean_core_cooling_runtime': 246.91554054054055,
    'end_date': '2014-12-31T00:00:00',
    'heat_stage': 'single_stage',
    'heat_type': 'heat_pump_electric_backup',
    'heating_or_cooling': 'cooling_ALL',
    'mean_abs_err': 12.444656615631587,
    'mean_abs_pct_err': 0.050400459154527476,
    'mean_demand': 5.602990491439324,
    'mean_sq_err': 379.28224705229485,
    'n_core_cooling_days': 296,
    'n_days_both_heating_and_cooling': 212,
    'n_days_in_inputfile_date_range': 1460,
    'n_days_insufficient_data': 13,
    'percent_savings_baseline_percentile': 43.83576235942965,
    'percent_savings_baseline_regional': 21.40352145693172,
    'regional_average_baseline_cooling_comfort_temperature': 73.0,
    'root_mean_sq_err': 19.47517001343749,
    'start_date': '2011-01-01T00:00:00',
    'station': '725314',
    'sw_version': '2.0.0a3',
    'tau': -0.8165326408614967,
    'total_core_cooling_runtime': 73087.0},
    {'_daily_mean_core_day_demand_baseline_baseline_percentile': 27.292462133995627,
    '_daily_mean_core_day_demand_baseline_baseline_regional': 26.808316938474633,
    'alpha': 31.700873772886364,
    'avoided_daily_mean_core_day_runtime_baseline_percentile': 92.11668477057343,
    'avoided_daily_mean_core_day_runtime_baseline_regional': 76.76885903961299,
    'avoided_total_core_day_runtime_baseline_percentile': 82444.43286966321,
    'avoided_total_core_day_runtime_baseline_regional': 68708.12884045363,
    'baseline_daily_mean_core_day_runtime_baseline_percentile': 865.194897061076,
    'baseline_daily_mean_core_day_runtime_baseline_regional': 849.8470713301159,
    'baseline_percentile_core_heating_comfort_temperature': 69.5,
    'baseline_total_core_day_runtime_baseline_percentile': 774349.432869663,
    'baseline_total_core_day_runtime_baseline_regional': 760613.1288404537,
    'climate_zone': 'Mixed-Humid',
    'cool_stage': '',
    'cool_type': 'heat_pump',
    'core_heating_days_mean_indoor_temperature': 66.6958723285375,
    'core_heating_days_mean_outdoor_temperature': 44.679677289106145,
    'core_mean_indoor_temperature': 66.6958723285375,
    'core_mean_outdoor_temperature': 44.679677289106145,
    'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
    'cv_root_mean_sq_err': 0.10742587467633809,
    'daily_mean_core_heating_runtime': 773.0782122905028,
    'end_date': '2014-12-31T00:00:00',
    'heat_stage': 'single_stage',
    'heat_type': 'heat_pump_electric_backup',
    'heating_or_cooling': 'heating_ALL',
    'mean_abs_err': 55.601169394930835,
    'mean_abs_pct_err': 0.07192179072049355,
    'mean_demand': 24.386653119691406,
    'mean_sq_err': 6897.070484921537,
    'n_core_heating_days': 895,
    'n_days_both_heating_and_cooling': 212,
    'n_days_in_inputfile_date_range': 1460,
    'n_days_insufficient_data': 13,
    'percent_savings_baseline_percentile': 10.646928811471101,
    'percent_savings_baseline_regional': 9.033255703224372,
    'regional_average_baseline_heating_comfort_temperature': 69,
    'rhu1_00F_to_05F': nan,
    'rhu1_05F_to_10F': 0.35810185185185184,
    'rhu1_10F_to_15F': 0.36336805555555557,
    'rhu1_15F_to_20F': 0.37900691389063484,
    'rhu1_20F_to_25F': 0.375673443706005,
    'rhu1_25F_to_30F': 0.3318400322150354,
    'rhu1_30F_to_35F': 0.28432496802364043,
    'rhu1_30F_to_45F': 0.22154695797667256,
    'rhu1_35F_to_40F': 0.19741898266605878,
    'rhu1_40F_to_45F': 0.15271363589013506,
    'rhu1_45F_to_50F': 0.09249776186213071,
    'rhu1_50F_to_55F': 0.052322643343051506,
    'rhu1_55F_to_60F': 0.028319891645631964,
    'rhu2_00F_to_05F': nan,
    'rhu2_05F_to_10F': 0.35810185185185184,
    'rhu2_10F_to_15F': 0.36336805555555557,
    'rhu2_15F_to_20F': 0.37900691389063484,
    'rhu2_20F_to_25F': 0.375673443706005,
    'rhu2_25F_to_30F': 0.3318400322150354,
    'rhu2_30F_to_35F': 0.28432496802364043,
    'rhu2_30F_to_45F': 0.22154695797667256,
    'rhu2_35F_to_40F': 0.19741898266605878,
    'rhu2_40F_to_45F': 0.15271363589013506,
    'rhu2_45F_to_50F': 0.09249776186213071,
    'rhu2_50F_to_55F': 0.052322643343051506,
    'rhu2_55F_to_60F': 0.028319891645631964,
    'root_mean_sq_err': 83.04860314852705,
    'start_date': '2011-01-01T00:00:00',
    'station': '725314',
    'sw_version': '2.0.0a3',
    'tau': -2.3486608421262156,
    'total_auxiliary_heating_core_day_runtime': 144794.0,
    'total_core_heating_runtime': 691905.0,
    'total_emergency_heating_core_day_runtime': 2104.0}]

    return data
