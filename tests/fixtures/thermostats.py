from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path
from thermostat.regression import runtime_regression
from thermostat.core import Thermostat, CoreDaySet

import pandas as pd
import numpy as np

import pytest

# will be modified, recreate every time by scoping to function
@pytest.fixture(scope='function')
def thermostat_template():
    thermostat_id = "FAKE"
    equipment_type = 0
    zipcode = "FAKE"
    station = "FAKE"
    temperature_in = pd.Series([])
    temperature_out = pd.Series([])
    cooling_setpoint = pd.Series([])
    heating_setpoint = pd.Series([])
    cool_runtime = pd.Series([])
    heat_runtime = pd.Series([])
    auxiliary_heat_runtime = pd.Series([])
    emergency_heat_runtime = pd.Series([])

    thermostat = Thermostat(
        thermostat_id,
        equipment_type,
        zipcode,
        station,
        temperature_in,
        temperature_out,
        cooling_setpoint,
        heating_setpoint,
        cool_runtime,
        heat_runtime,
        auxiliary_heat_runtime,
        emergency_heat_runtime
    )
    return thermostat

# Note:
# The following fixtures can be quite slow without a prebuilt weather cache
# they the from_csv command fetches weather data. (This happens with builds on
# travis.)
# To speed this up, spoof the weather source.

@pytest.fixture(scope="session", params=["../data/metadata_type_1_single_utc_offset_0.csv"])
def thermostat_type_1_utc(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/metadata_type_1_single_utc_offset_bad.csv"])
def thermostat_type_1_utc_bad(request):
    thermostats = from_csv(get_data_path(request.param))

@pytest.fixture(scope="session", params=["../data/metadata_multiple_same_key.csv"])
def thermostats_multiple_same_key(request):
    thermostats = from_csv(get_data_path(request.param))
    return thermostats

@pytest.fixture(scope="session", params=["../data/metadata_type_1_single.csv"])
def thermostat_type_1(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/metadata_type_2_single.csv"])
def thermostat_type_2(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/metadata_type_3_single.csv"])
def thermostat_type_3(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/metadata_type_4_single.csv"])
def thermostat_type_4(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/metadata_type_5_single.csv"])
def thermostat_type_5(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

@pytest.fixture(scope="session", params=["../data/metadata_single_zero_days.csv"])
def thermostat_zero_days(request):
    thermostats = from_csv(get_data_path(request.param))
    return next(thermostats)

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

    # this data comes from a script in scripts/test_data_generation.ipynb
    data = [{
	'_daily_mean_core_day_demand_baseline_baseline_percentile': 9.976082164677136,
	'_daily_mean_core_day_demand_baseline_baseline_regional': 7.128806020996521,
	'alpha': 44.06852746653279,
	'avoided_daily_mean_core_day_runtime_baseline_percentile': 192.71571034192178,
	'avoided_daily_mean_core_day_runtime_baseline_regional': 67.24044339932902,
	'avoided_total_core_day_runtime_baseline_percentile': 57043.85026120885,
	'avoided_total_core_day_runtime_baseline_regional': 19903.17124620139,
	'baseline_daily_mean_core_day_runtime_baseline_percentile': 439.6312508824623,
	'baseline_daily_mean_core_day_runtime_baseline_regional': 314.15598393986954,
	'baseline_percentile_core_cooling_comfort_temperature': 69.5,
	'baseline_total_core_day_runtime_baseline_percentile': 130130.85026120885,
	'baseline_total_core_day_runtime_baseline_regional': 92990.17124620138,
	'climate_zone': 'Mixed-Humid',
	'core_cooling_days_mean_indoor_temperature': 73.95971753003002,
	'core_cooling_days_mean_outdoor_temperature': 79.8426321875,
	'core_mean_indoor_temperature': 73.95971753003002,
	'core_mean_outdoor_temperature': 79.8426321875,
	'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
	'cv_root_mean_sq_err': 0.07887381236030344,
	'daily_mean_core_cooling_runtime': 246.91554054054055,
	'end_date': '2014-12-31T00:00:00',
	'equipment_type': 1,
	'heating_or_cooling': 'cooling_ALL',
	'mean_abs_err': 12.444656609338942,
	'mean_abs_pct_err': 0.050400459129042466,
	'mean_demand': 5.60299049538374,
	'mean_sq_err': 379.28224705229485,
	'n_core_cooling_days': 296,
	'n_days_both_heating_and_cooling': 212,
	'n_days_in_inputfile_date_range': 1460,
	'n_days_insufficient_data': 13,
	'percent_savings_baseline_percentile': 43.83576234744179,
	'percent_savings_baseline_regional': 21.403521446912517,
	'regional_average_baseline_cooling_comfort_temperature': 73.0,
	'root_mean_sq_err': 19.47517001343749,
	'start_date': '2011-01-01T00:00:00',
	'station': '725314',
	'sw_version': '1.5.2',
	'tau': -0.8165326352929079,
	'total_core_cooling_runtime': 73087.0,
	'zipcode': '62223'
	}, {
	'_daily_mean_core_day_demand_baseline_baseline_percentile': 27.292461874951055,
	'_daily_mean_core_day_demand_baseline_baseline_regional': 26.808316680312686,
	'alpha': 31.700874116202517,
	'avoided_daily_mean_core_day_runtime_baseline_percentile': 92.11668592857713,
	'avoided_daily_mean_core_day_runtime_baseline_regional': 76.76886005938185,
	'avoided_total_core_day_runtime_baseline_percentile': 82444.43390607653,
	'avoided_total_core_day_runtime_baseline_regional': 68708.12975314676,
	'baseline_daily_mean_core_day_runtime_baseline_percentile': 865.19489821908,
	'baseline_daily_mean_core_day_runtime_baseline_regional': 849.8470723498847,
	'baseline_percentile_core_heating_comfort_temperature': 69.5,
	'baseline_total_core_day_runtime_baseline_percentile': 774349.4339060766,
	'baseline_total_core_day_runtime_baseline_regional': 760613.1297531468,
	'climate_zone': 'Mixed-Humid',
	'core_heating_days_mean_indoor_temperature': 66.6958723285375,
	'core_heating_days_mean_outdoor_temperature': 44.679677289106145,
	'core_mean_indoor_temperature': 66.6958723285375,
	'core_mean_outdoor_temperature': 44.679677289106145,
	'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
	'cv_root_mean_sq_err': 0.1074258746763381,
	'daily_mean_core_heating_runtime': 773.0782122905028,
	'end_date': '2014-12-31T00:00:00',
	'equipment_type': 1,
	'heating_or_cooling': 'heating_ALL',
	'mean_abs_err': 55.60116758756078,
	'mean_abs_pct_err': 0.07192178838260584,
	'mean_demand': 24.386652855587275,
	'mean_sq_err': 6897.07048492154,
	'n_core_heating_days': 895,
	'n_days_both_heating_and_cooling': 212,
	'n_days_in_inputfile_date_range': 1460,
	'n_days_insufficient_data': 13,
	'percent_savings_baseline_percentile': 10.64692893106402,
	'percent_savings_baseline_regional': 9.033255812379368,
	'regional_average_baseline_heating_comfort_temperature': 69,
	'rhu_00F_to_05F': float('nan'),
	'rhu_05F_to_10F': 0.35810185185185184,
	'rhu_10F_to_15F': 0.36336805555555557,
	'rhu_15F_to_20F': 0.37900691389063484,
	'rhu_20F_to_25F': 0.375673443706005,
	'rhu_25F_to_30F': 0.3318400322150354,
	'rhu_30F_to_35F': 0.28432496802364043,
	'rhu_35F_to_40F': 0.19741898266605878,
	'rhu_40F_to_45F': 0.15271363589013506,
	'rhu_45F_to_50F': 0.09249776186213071,
	'rhu_50F_to_55F': 0.052322643343051506,
	'rhu_55F_to_60F': 0.028319891645631964,
	'root_mean_sq_err': 83.04860314852706,
	'start_date': '2011-01-01T00:00:00',
	'station': '725314',
	'sw_version': '1.5.2',
	'tau': -2.3486605751007135,
	'total_auxiliary_heating_core_day_runtime': 144794.0,
	'total_core_heating_runtime': 691905.0,
	'total_emergency_heating_core_day_runtime': 2104.0,
	'zipcode': '62223'
    }]
    return data
