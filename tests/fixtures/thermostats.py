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

    data = [{
        '_daily_mean_core_day_demand_baseline_dailyavgCTD_baseline10': 10.40137740398669,
        '_daily_mean_core_day_demand_baseline_dailyavgCTD_baseline_regional': 7.4060378635912354,
        '_daily_mean_core_day_demand_baseline_deltaT_cooling_baseline10': 10.282300147209424,
        '_daily_mean_core_day_demand_baseline_deltaT_cooling_baseline_regional': 7.2823001472094226,
        '_daily_mean_core_day_demand_baseline_hourlyavgCTD_baseline10': 10.112308877401233,
        '_daily_mean_core_day_demand_baseline_hourlyavgCTD_baseline_regional': 7.6260316015295659,
        'alpha_dailyavgCTD': 41.08170521631375,
        'alpha_deltaT_cooling': 41.081705064809377,
        'alpha_hourlyavgCTD': 43.033765878987062,
        'avoided_daily_mean_core_day_runtime_dailyavgCTD_baseline10': 168.12352465528323,
        'avoided_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional': 45.069868633988456,
        'avoided_daily_mean_core_day_runtime_deltaT_cooling_baseline10': 168.12352408820755,
        'avoided_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional': 45.069868509872734,
        'avoided_daily_mean_core_day_runtime_hourlyavgCTD_baseline10': 175.98793702716242,
        'avoided_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional': 68.99406282705533,
        'avoided_total_core_day_runtime_dailyavgCTD_baseline10': 46906.463378824024,
        'avoided_total_core_day_runtime_dailyavgCTD_baseline_regional': 12574.493348882779,
        'avoided_total_core_day_runtime_deltaT_cooling_baseline10': 46906.463220609905,
        'avoided_total_core_day_runtime_deltaT_cooling_baseline_regional': 12574.493314254492,
        'avoided_total_core_day_runtime_hourlyavgCTD_baseline10': 49100.634430578313,
        'avoided_total_core_day_runtime_hourlyavgCTD_baseline_regional': 19249.343528748439,
        'baseline10_core_cooling_comfort_temperature': 70.0,
        'baseline_daily_mean_core_day_runtime_dailyavgCTD_baseline10': 427.30632035420803,
        'baseline_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional': 304.25266433291313,
        'baseline_daily_mean_core_day_runtime_deltaT_cooling_baseline10': 427.30631978713228,
        'baseline_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional': 304.25266420879746,
        'baseline_daily_mean_core_day_runtime_hourlyavgCTD_baseline10': 435.17073272608712,
        'baseline_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional': 328.17685852598004,
        'baseline_total_core_day_runtime_dailyavgCTD_baseline10': 119218.46337882403,
        'baseline_total_core_day_runtime_dailyavgCTD_baseline_regional': 84886.493348882766,
        'baseline_total_core_day_runtime_deltaT_cooling_baseline10': 119218.4632206099,
        'baseline_total_core_day_runtime_deltaT_cooling_baseline_regional': 84886.493314254491,
        'baseline_total_core_day_runtime_hourlyavgCTD_baseline10': 121412.63443057831,
        'baseline_total_core_day_runtime_hourlyavgCTD_baseline_regional': 91561.343528748432,
        'climate_zone': 'Mixed-Humid',
        'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
        'cv_root_mean_sq_err_dailyavgCTD': 0.030778007884826493,
        'cv_root_mean_sq_err_deltaT_cooling': 0.030778007884826448,
        'cv_root_mean_sq_err_hourlyavgCTD': 0.057880694291325828,
        'daily_mean_core_cooling_runtime': 259.18279569892474,
        'end_date': '2014-12-31T00:00:00',
        'equipment_type': 1,
        'heating_or_cooling': 'cooling_ALL',
        'mean_abs_err_dailyavgCTD': 5.9830279846068768,
        'mean_abs_err_deltaT_cooling': 5.983028010851724,
        'mean_abs_err_hourlyavgCTD': 9.2369538508651221,
        'mean_abs_pct_err_dailyavgCTD': 0.023084201898790225,
        'mean_abs_pct_err_deltaT_cooling': 0.034981404736391102,
        'mean_abs_pct_err_hourlyavgCTD': 0.035638761538767688,
        'mean_demand_dailyavgCTD': 6.3089590447672546,
        'mean_demand_deltaT_cooling': 6.1898817879899877,
        'mean_demand_hourlyavgCTD': 6.0227774726422671,
        'mean_sq_err_dailyavgCTD': 63.634605105096682,
        'mean_sq_err_deltaT_cooling': 63.634605105096497,
        'mean_sq_err_hourlyavgCTD': 225.05040772556777,
        'n_core_cooling_days': 279,
        'n_days_both_heating_and_cooling': 212,
        'n_days_in_inputfile_date_range': 1460,
        'n_days_insufficient_data': 13,
        'percent_savings_dailyavgCTD_baseline10': 39.344965577836575,
        'percent_savings_dailyavgCTD_baseline_regional': 14.813302862213568,
        'percent_savings_deltaT_cooling_baseline10': 39.344965497341647,
        'percent_savings_deltaT_cooling_baseline_regional': 14.813302827462813,
        'percent_savings_hourlyavgCTD_baseline10': 40.4411243202644,
        'percent_savings_hourlyavgCTD_baseline_regional': 21.023439354299697,
        'regional_average_baseline_cooling_comfort_temperature': 73.0,
        'root_mean_sq_err_dailyavgCTD': 7.9771301296328794,
        'root_mean_sq_err_deltaT_cooling': 7.9771301296328678,
        'root_mean_sq_err_hourlyavgCTD': 15.001680163420621,
        'start_date': '2011-01-01T00:00:00',
        'station': '725314',
        'sw_version': '0.4.0',
        'tau_dailyavgCTD': 0.1190772567772668,
        'tau_deltaT_cooling': 0.11907728133268593,
        'tau_hourlyavgCTD': -0.56229016615414917,
        'total_core_cooling_runtime': 72312.0,
        'zipcode': '62223'
    }, {
        '_daily_mean_core_day_demand_baseline_dailyavgHTD_baseline90': 27.640829239441153,
        '_daily_mean_core_day_demand_baseline_dailyavgHTD_baseline_regional': 27.140829239441153,
        '_daily_mean_core_day_demand_baseline_deltaT_heating_baseline90': 25.174951580787596,
        '_daily_mean_core_day_demand_baseline_deltaT_heating_baseline_regional': 24.674951580787596,
        '_daily_mean_core_day_demand_baseline_hourlyavgHTD_baseline90': 27.745267202451704,
        '_daily_mean_core_day_demand_baseline_hourlyavgHTD_baseline_regional': 27.258963721731487,
        'alpha_dailyavgHTD': 31.623941715909474,
        'alpha_deltaT_heating': 31.623941538912561,
        'alpha_hourlyavgHTD': 31.591623495230735,
        'avoided_daily_mean_core_day_runtime_dailyavgHTD_baseline90': 90.336462643411849,
        'avoided_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional': 74.52449178545713,
        'avoided_daily_mean_core_day_runtime_deltaT_heating_baseline90': 90.336462409188613,
        'avoided_daily_mean_core_day_runtime_deltaT_heating_baseline_regional': 74.524491639732332,
        'avoided_daily_mean_core_day_runtime_hourlyavgHTD_baseline90': 92.742525030346357,
        'avoided_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional': 77.379408563012987,
        'avoided_total_core_day_runtime_dailyavgHTD_baseline90': 79676.760051489255,
        'avoided_total_core_day_runtime_dailyavgHTD_baseline_regional': 65730.60175477319,
        'avoided_total_core_day_runtime_deltaT_heating_baseline90': 79676.759844904358,
        'avoided_total_core_day_runtime_deltaT_heating_baseline_regional': 65730.601626243923,
        'avoided_total_core_day_runtime_hourlyavgHTD_baseline90': 81798.907076765492,
        'avoided_total_core_day_runtime_hourlyavgHTD_baseline_regional': 68248.638352577458,
        'baseline90_core_heating_comfort_temperature': 69.5,
        'baseline_daily_mean_core_day_runtime_dailyavgHTD_baseline90': 874.11197284749358,
        'baseline_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional': 858.30000198953871,
        'baseline_daily_mean_core_day_runtime_deltaT_heating_baseline90': 874.11197261327015,
        'baseline_daily_mean_core_day_runtime_deltaT_heating_baseline_regional': 858.3000018438139,
        'baseline_daily_mean_core_day_runtime_hourlyavgHTD_baseline90': 876.51803523442811,
        'baseline_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional': 861.15491876709461,
        'baseline_total_core_day_runtime_dailyavgHTD_baseline90': 770966.76005148934,
        'baseline_total_core_day_runtime_dailyavgHTD_baseline_regional': 757020.60175477318,
        'baseline_total_core_day_runtime_deltaT_heating_baseline90': 770966.7598449043,
        'baseline_total_core_day_runtime_deltaT_heating_baseline_regional': 757020.60162624391,
        'baseline_total_core_day_runtime_hourlyavgHTD_baseline90': 773088.90707676555,
        'baseline_total_core_day_runtime_hourlyavgHTD_baseline_regional': 759538.63835257746,
        'climate_zone': 'Mixed-Humid',
        'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
        'cv_root_mean_sq_err_dailyavgHTD': 0.10447207148899268,
        'cv_root_mean_sq_err_deltaT_heating': 0.10447207148899268,
        'cv_root_mean_sq_err_hourlyavgHTD': 0.10529247201990428,
        'daily_mean_core_heating_runtime': 783.77551020408168,
        'end_date': '2014-12-31T00:00:00',
        'equipment_type': 1,
        'heating_or_cooling': 'heating_ALL',
        'mean_abs_err_dailyavgHTD': 54.30059894064167,
        'mean_abs_err_deltaT_heating': 54.300599891142141,
        'mean_abs_err_hourlyavgHTD': 55.117371177544747,
        'mean_abs_pct_err_dailyavgHTD': 0.069280805834954856,
        'mean_abs_pct_err_deltaT_heating': 0.11977124943613111,
        'mean_abs_pct_err_hourlyavgHTD': 0.070322905551352483,
        'mean_demand_dailyavgHTD': 24.784244710702126,
        'mean_demand_deltaT_heating': 22.318367052048565,
        'mean_demand_hourlyavgHTD': 24.809598985072899,
        'mean_sq_err_dailyavgHTD': 6704.768556627957,
        'mean_sq_err_deltaT_heating': 6704.7685566279561,
        'mean_sq_err_hourlyavgHTD': 6810.4847198639573,
        'n_core_heating_days': 882,
        'n_days_both_heating_and_cooling': 212,
        'n_days_in_inputfile_date_range': 1460,
        'n_days_insufficient_data': 13,
        'percent_savings_dailyavgHTD_baseline90': 10.334655679081159,
        'percent_savings_dailyavgHTD_baseline_regional': 8.6828022384608428,
        'percent_savings_deltaT_heating_baseline90': 10.334655655054824,
        'percent_savings_deltaT_heating_baseline_regional': 8.6828022229567292,
        'percent_savings_hourlyavgHTD_baseline90': 10.580789134081197,
        'percent_savings_hourlyavgHTD_baseline_regional': 8.9855387081567351,
        'regional_average_baseline_heating_comfort_temperature': 69,
        'rhu_00F_to_05F': 0.10293333333333334,
        'rhu_05F_to_10F': 0.21504112808460635,
        'rhu_10F_to_15F': 0.25222924603340729,
        'rhu_15F_to_20F': 0.3481727747331238,
        'rhu_20F_to_25F': 0.25228588565063587,
        'rhu_25F_to_30F': 0.31253169225095651,
        'rhu_30F_to_35F': 0.26873058051091708,
        'rhu_35F_to_40F': 0.24271985569297436,
        'rhu_40F_to_45F': 0.11955851597538715,
        'rhu_45F_to_50F': 0.071810573586446214,
        'rhu_50F_to_55F': 0.048272807794508411,
        'rhu_55F_to_60F': 0.024797882753870137,
        'root_mean_sq_err_dailyavgHTD': 81.882651133362529,
        'root_mean_sq_err_deltaT_heating': 81.882651133362529,
        'root_mean_sq_err_hourlyavgHTD': 82.525660978049473,
        'start_date': '2011-01-01T00:00:00',
        'station': '725314',
        'sw_version': '0.4.0',
        'tau_dailyavgHTD': -2.4658776586535609,
        'tau_deltaT_heating': -2.4658778059507656,
        'tau_hourlyavgHTD': -2.4762007262329404,
        'total_auxiliary_heating_core_day_runtime': 144794.0,
        'total_core_heating_runtime': 691290.0,
        'total_emergency_heating_core_day_runtime': 2084.0,
        'zipcode': '62223'
    }]
    return data
