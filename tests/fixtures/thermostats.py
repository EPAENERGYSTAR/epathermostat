from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path
from thermostat.regression import runtime_regression
from thermostat.core import Thermostat, CoreDaySet

import pandas as pd
import numpy as np
from numpy import nan

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

@pytest.fixture(scope="session", params=["../data/metadata_single_emg_aux_constant_on_outlier.csv"])
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

    # this data comes from a script in scripts/test_data_generation.ipynb
    data = [{
        'sw_version': '1.7.2',
        'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
        'equipment_type': 1,
        'heating_or_cooling': 'cooling_ALL',
        'zipcode': '62223',
        'station': '725314',
        'climate_zone': 'Mixed-Humid',
        'start_date': '2011-01-01T00:00:00',
        'end_date': '2014-12-31T00:00:00',
        'n_days_in_inputfile_date_range': 1460,
        'n_days_both_heating_and_cooling': 212,
        'n_days_insufficient_data': 13,
        'n_core_cooling_days': 296,
        'baseline_percentile_core_cooling_comfort_temperature': 69.5,
        'regional_average_baseline_cooling_comfort_temperature': 73.0,
        'percent_savings_baseline_percentile': 43.83576234744179,
        'avoided_daily_mean_core_day_runtime_baseline_percentile': 192.71571034192178,
        'avoided_total_core_day_runtime_baseline_percentile': 57043.85026120885,
        'baseline_daily_mean_core_day_runtime_baseline_percentile': 439.6312508824623,
        'baseline_total_core_day_runtime_baseline_percentile': 130130.85026120885,
        '_daily_mean_core_day_demand_baseline_baseline_percentile': 9.976082164677136,
        'percent_savings_baseline_regional': 21.403521446912517,
        'avoided_daily_mean_core_day_runtime_baseline_regional': 67.24044339932902,
        'avoided_total_core_day_runtime_baseline_regional': 19903.17124620139,
        'baseline_daily_mean_core_day_runtime_baseline_regional': 314.15598393986954,
        'baseline_total_core_day_runtime_baseline_regional': 92990.17124620138,
        '_daily_mean_core_day_demand_baseline_baseline_regional': 7.128806020996521,
        'mean_demand': 5.60299049538374,
        'tau': -0.8165326352929079,
        'alpha': 44.06852746653279,
        'mean_sq_err': 379.28224705229485,
        'root_mean_sq_err': 19.47517001343749,
        'cv_root_mean_sq_err': 0.07887381236030344,
        'mean_abs_pct_err': 0.050400459129042466,
        'mean_abs_err': 12.444656609338942,
        'total_core_cooling_runtime': 73087.0,
        'daily_mean_core_cooling_runtime': 246.91554054054055,
        'core_cooling_days_mean_indoor_temperature': 73.95971753003002,
        'core_cooling_days_mean_outdoor_temperature': 79.8426321875,
        'core_mean_indoor_temperature': 73.95971753003002,
        'core_mean_outdoor_temperature': 79.8426321875
        }, {
        'sw_version': '1.7.2',
        'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
        'equipment_type': 1,
        'heating_or_cooling': 'heating_ALL',
        'zipcode': '62223',
        'station': '725314',
        'climate_zone': 'Mixed-Humid',
        'start_date': '2011-01-01T00:00:00',
        'end_date': '2014-12-31T00:00:00',
        'n_days_in_inputfile_date_range': 1460,
        'n_days_both_heating_and_cooling': 212,
        'n_days_insufficient_data': 13,
        'n_core_heating_days': 895,
        'baseline_percentile_core_heating_comfort_temperature': 69.5,
        'regional_average_baseline_heating_comfort_temperature': 69,
        'percent_savings_baseline_percentile': 10.64692893106402,
        'avoided_daily_mean_core_day_runtime_baseline_percentile': 92.11668592857713,
        'avoided_total_core_day_runtime_baseline_percentile': 82444.43390607653,
        'baseline_daily_mean_core_day_runtime_baseline_percentile': 865.19489821908,
        'baseline_total_core_day_runtime_baseline_percentile': 774349.4339060766,
        '_daily_mean_core_day_demand_baseline_baseline_percentile': 27.292461874951055,
        'percent_savings_baseline_regional': 9.033255812379368,
        'avoided_daily_mean_core_day_runtime_baseline_regional': 76.76886005938185,
        'avoided_total_core_day_runtime_baseline_regional': 68708.12975314676,
        'baseline_daily_mean_core_day_runtime_baseline_regional': 849.8470723498847,
        'baseline_total_core_day_runtime_baseline_regional': 760613.1297531468,
        '_daily_mean_core_day_demand_baseline_baseline_regional': 26.808316680312686,
        'mean_demand': 24.386652855587275,
        'tau': -2.3486605751007135,
        'alpha': 31.700874116202517,
        'mean_sq_err': 6897.07048492154,
        'root_mean_sq_err': 83.04860314852706,
        'cv_root_mean_sq_err': 0.1074258746763381,
        'mean_abs_pct_err': 0.07192178838260584,
        'mean_abs_err': 55.60116758756078,
        'total_core_heating_runtime': 691905.0,
        'daily_mean_core_heating_runtime': 773.0782122905028,
        'core_heating_days_mean_indoor_temperature': 66.6958723285375,
        'core_heating_days_mean_outdoor_temperature': 44.679677289106145,
        'core_mean_indoor_temperature': 66.6958723285375,
        'core_mean_outdoor_temperature': 44.679677289106145,
        'total_auxiliary_heating_core_day_runtime': 144794.0,
        'total_emergency_heating_core_day_runtime': 2104.0,
        'rhu1_aux_duty_cycle': 0.06990582191780823,
        'rhu1_emg_duty_cycle': 0.0010435692541856925,
        'rhu1_compressor_duty_cycle': 0.3380902777777778,
        'rhu1_00F_to_05F': nan,
        'rhu1_05F_to_10F': 0.35810185185185184,
        'rhu1_10F_to_15F': 0.36336805555555557,
        'rhu1_15F_to_20F': 0.37900691389063484,
        'rhu1_20F_to_25F': 0.375673443706005,
        'rhu1_25F_to_30F': 0.3318400322150354,
        'rhu1_30F_to_35F': 0.28432496802364043,
        'rhu1_35F_to_40F': 0.19741898266605878,
        'rhu1_40F_to_45F': 0.15271363589013506,
        'rhu1_45F_to_50F': 0.09249776186213071,
        'rhu1_50F_to_55F': 0.052322643343051506,
        'rhu1_55F_to_60F': 0.028319891645631964,
        'rhu1_less10F': 0.3651785714285714,
        'rhu1_10F_to_20F': 0.3745206434583396,
        'rhu1_20F_to_30F': 0.3489457045517326,
        'rhu1_30F_to_40F': 0.24596842083649878,
        'rhu1_40F_to_50F': 0.12306960016924054,
        'rhu1_50F_to_60F': 0.0430327868852459,
        'rhu1_00F_to_05F_aux_duty_cycle': nan,
        'rhu1_05F_to_10F_aux_duty_cycle': 0.35810185185185184,
        'rhu1_10F_to_15F_aux_duty_cycle': 0.36336805555555557,
        'rhu1_15F_to_20F_aux_duty_cycle': 0.3760763888888889,
        'rhu1_20F_to_25F_aux_duty_cycle': 0.35656906906906904,
        'rhu1_25F_to_30F_aux_duty_cycle': 0.3082627118644068,
        'rhu1_30F_to_35F_aux_duty_cycle': 0.23578539823008848,
        'rhu1_35F_to_40F_aux_duty_cycle': 0.14188453159041395,
        'rhu1_40F_to_45F_aux_duty_cycle': 0.08783360566448802,
        'rhu1_45F_to_50F_aux_duty_cycle': 0.043188657407407405,
        'rhu1_50F_to_55F_aux_duty_cycle': 0.01672854785478548,
        'rhu1_55F_to_60F_aux_duty_cycle': 0.005432581018518519,
        'rhu1_less10F_aux_duty_cycle': 0.3651785714285714,
        'rhu1_10F_to_20F_aux_duty_cycle': 0.3724454365079365,
        'rhu1_20F_to_30F_aux_duty_cycle': 0.32688078703703705,
        'rhu1_30F_to_40F_aux_duty_cycle': 0.19123708010335919,
        'rhu1_40F_to_50F_aux_duty_cycle': 0.06370120120120121,
        'rhu1_50F_to_60F_aux_duty_cycle': 0.011223914269599549,
        'rhu1_00F_to_05F_emg_duty_cycle': nan,
        'rhu1_05F_to_10F_emg_duty_cycle': 0.0,
        'rhu1_10F_to_15F_emg_duty_cycle': 0.0,
        'rhu1_15F_to_20F_emg_duty_cycle': 0.0007986111111111112,
        'rhu1_20F_to_25F_emg_duty_cycle': 0.002027027027027027,
        'rhu1_25F_to_30F_emg_duty_cycle': 0.00211864406779661,
        'rhu1_30F_to_35F_emg_duty_cycle': 0.0019174041297935103,
        'rhu1_35F_to_40F_emg_duty_cycle': 0.002573529411764706,
        'rhu1_40F_to_45F_emg_duty_cycle': 0.001994825708061002,
        'rhu1_45F_to_50F_emg_duty_cycle': 0.0016550925925925926,
        'rhu1_50F_to_55F_emg_duty_cycle': 0.0017808030803080307,
        'rhu1_55F_to_60F_emg_duty_cycle': 0.001222511574074074,
        'rhu1_less10F_emg_duty_cycle': 0.0,
        'rhu1_10F_to_20F_emg_duty_cycle': 0.000570436507936508,
        'rhu1_20F_to_30F_emg_duty_cycle': 0.0020833333333333333,
        'rhu1_30F_to_40F_emg_duty_cycle': 0.0022286821705426356,
        'rhu1_40F_to_50F_emg_duty_cycle': 0.0018111861861861863,
        'rhu1_50F_to_60F_emg_duty_cycle': 0.001508742244782854,
        'rhu1_00F_to_05F_compressor_duty_cycle': nan,
        'rhu1_05F_to_10F_compressor_duty_cycle': 1.0,
        'rhu1_10F_to_15F_compressor_duty_cycle': 1.0,
        'rhu1_15F_to_20F_compressor_duty_cycle': 0.9935763888888889,
        'rhu1_20F_to_25F_compressor_duty_cycle': 0.952515015015015,
        'rhu1_25F_to_30F_compressor_duty_cycle': 0.9332156308851224,
        'rhu1_30F_to_35F_compressor_duty_cycle': 0.8341076696165192,
        'rhu1_35F_to_40F_compressor_duty_cycle': 0.7291598583877995,
        'rhu1_40F_to_45F_compressor_duty_cycle': 0.5862200435729847,
        'rhu1_45F_to_50F_compressor_duty_cycle': 0.4831539351851852,
        'rhu1_50F_to_55F_compressor_duty_cycle': 0.3519733223322332,
        'rhu1_55F_to_60F_compressor_duty_cycle': 0.2337745949074074,
        'rhu1_less10F_compressor_duty_cycle': 1.0,
        'rhu1_10F_to_20F_compressor_duty_cycle': 0.9954117063492064,
        'rhu1_20F_to_30F_compressor_duty_cycle': 0.9406539351851851,
        'rhu1_30F_to_40F_compressor_duty_cycle': 0.7843184754521964,
        'rhu1_40F_to_50F_compressor_duty_cycle': 0.5305086336336337,
        'rhu1_50F_to_60F_compressor_duty_cycle': 0.29437394247038917,
        'rhu2_aux_duty_cycle': 0.06990582191780823,
        'rhu2_emg_duty_cycle': 0.0010435692541856925,
        'rhu2_compressor_duty_cycle': 0.3380902777777778,
        'rhu2_00F_to_05F': nan,
        'rhu2_05F_to_10F': 0.35810185185185184,
        'rhu2_10F_to_15F': 0.36336805555555557,
        'rhu2_15F_to_20F': 0.37900691389063484,
        'rhu2_20F_to_25F': 0.375673443706005,
        'rhu2_25F_to_30F': 0.3318400322150354,
        'rhu2_30F_to_35F': 0.28432496802364043,
        'rhu2_35F_to_40F': 0.19741898266605878,
        'rhu2_40F_to_45F': 0.15271363589013506,
        'rhu2_45F_to_50F': 0.09249776186213071,
        'rhu2_50F_to_55F': 0.052322643343051506,
        'rhu2_55F_to_60F': 0.028319891645631964,
        'rhu2_less10F': 0.3651785714285714,
        'rhu2_10F_to_20F': 0.3745206434583396,
        'rhu2_20F_to_30F': 0.3489457045517326,
        'rhu2_30F_to_40F': 0.24596842083649878,
        'rhu2_40F_to_50F': 0.12306960016924054,
        'rhu2_50F_to_60F': 0.0430327868852459,
        'rhu2_00F_to_05F_aux_duty_cycle': nan,
        'rhu2_05F_to_10F_aux_duty_cycle': 0.35810185185185184,
        'rhu2_10F_to_15F_aux_duty_cycle': 0.36336805555555557,
        'rhu2_15F_to_20F_aux_duty_cycle': 0.3760763888888889,
        'rhu2_20F_to_25F_aux_duty_cycle': 0.35656906906906904,
        'rhu2_25F_to_30F_aux_duty_cycle': 0.3082627118644068,
        'rhu2_30F_to_35F_aux_duty_cycle': 0.23578539823008848,
        'rhu2_35F_to_40F_aux_duty_cycle': 0.14188453159041395,
        'rhu2_40F_to_45F_aux_duty_cycle': 0.08783360566448802,
        'rhu2_45F_to_50F_aux_duty_cycle': 0.043188657407407405,
        'rhu2_50F_to_55F_aux_duty_cycle': 0.01672854785478548,
        'rhu2_55F_to_60F_aux_duty_cycle': 0.005432581018518519,
        'rhu2_less10F_aux_duty_cycle': 0.3651785714285714,
        'rhu2_10F_to_20F_aux_duty_cycle': 0.3724454365079365,
        'rhu2_20F_to_30F_aux_duty_cycle': 0.32688078703703705,
        'rhu2_30F_to_40F_aux_duty_cycle': 0.19123708010335919,
        'rhu2_40F_to_50F_aux_duty_cycle': 0.06370120120120121,
        'rhu2_50F_to_60F_aux_duty_cycle': 0.011223914269599549,
        'rhu2_00F_to_05F_emg_duty_cycle': nan,
        'rhu2_05F_to_10F_emg_duty_cycle': 0.0,
        'rhu2_10F_to_15F_emg_duty_cycle': 0.0,
        'rhu2_15F_to_20F_emg_duty_cycle': 0.0007986111111111112,
        'rhu2_20F_to_25F_emg_duty_cycle': 0.002027027027027027,
        'rhu2_25F_to_30F_emg_duty_cycle': 0.00211864406779661,
        'rhu2_30F_to_35F_emg_duty_cycle': 0.0019174041297935103,
        'rhu2_35F_to_40F_emg_duty_cycle': 0.002573529411764706,
        'rhu2_40F_to_45F_emg_duty_cycle': 0.001994825708061002,
        'rhu2_45F_to_50F_emg_duty_cycle': 0.0016550925925925926,
        'rhu2_50F_to_55F_emg_duty_cycle': 0.0017808030803080307,
        'rhu2_55F_to_60F_emg_duty_cycle': 0.001222511574074074,
        'rhu2_less10F_emg_duty_cycle': 0.0,
        'rhu2_10F_to_20F_emg_duty_cycle': 0.000570436507936508,
        'rhu2_20F_to_30F_emg_duty_cycle': 0.0020833333333333333,
        'rhu2_30F_to_40F_emg_duty_cycle': 0.0022286821705426356,
        'rhu2_40F_to_50F_emg_duty_cycle': 0.0018111861861861863,
        'rhu2_50F_to_60F_emg_duty_cycle': 0.001508742244782854,
        'rhu2_00F_to_05F_compressor_duty_cycle': nan,
        'rhu2_05F_to_10F_compressor_duty_cycle': 1.0,
        'rhu2_10F_to_15F_compressor_duty_cycle': 1.0,
        'rhu2_15F_to_20F_compressor_duty_cycle': 0.9935763888888889,
        'rhu2_20F_to_25F_compressor_duty_cycle': 0.952515015015015,
        'rhu2_25F_to_30F_compressor_duty_cycle': 0.9332156308851224,
        'rhu2_30F_to_35F_compressor_duty_cycle': 0.8341076696165192,
        'rhu2_35F_to_40F_compressor_duty_cycle': 0.7291598583877995,
        'rhu2_40F_to_45F_compressor_duty_cycle': 0.5862200435729847,
        'rhu2_45F_to_50F_compressor_duty_cycle': 0.4831539351851852,
        'rhu2_50F_to_55F_compressor_duty_cycle': 0.3519733223322332,
        'rhu2_55F_to_60F_compressor_duty_cycle': 0.2337745949074074,
        'rhu2_less10F_compressor_duty_cycle': 1.0,
        'rhu2_10F_to_20F_compressor_duty_cycle': 0.9954117063492064,
        'rhu2_20F_to_30F_compressor_duty_cycle': 0.9406539351851851,
        'rhu2_30F_to_40F_compressor_duty_cycle': 0.7843184754521964,
        'rhu2_40F_to_50F_compressor_duty_cycle': 0.5305086336336337,
        'rhu2_50F_to_60F_compressor_duty_cycle': 0.29437394247038917}]
    return data
