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

    # this data comes from a script in scripts/test_data_generation.ipynb
    data = [{
        '_daily_mean_core_day_demand_baseline_dailyavgCTD_baseline10': 10.468759574679755,
        '_daily_mean_core_day_demand_baseline_dailyavgCTD_baseline_regional': 6.9995076265015452,
        '_daily_mean_core_day_demand_baseline_deltaT_cooling_baseline10': 10.35213142495174,
        '_daily_mean_core_day_demand_baseline_deltaT_cooling_baseline_regional': 6.8521314249517387,
        '_daily_mean_core_day_demand_baseline_hourlyavgCTD_baseline10': 10.037828533462667,
        '_daily_mean_core_day_demand_baseline_hourlyavgCTD_baseline_regional': 7.1915897136190141,
        'alpha_dailyavgCTD': 41.090666150420269,
        'alpha_deltaT_cooling': 41.090666272828457,
        'alpha_hourlyavgCTD': 43.763105264095309,
        'avoided_daily_mean_core_day_runtime_dailyavgCTD_baseline10': 183.25276415164092,
        'avoided_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional': 40.698890557354993,
        'avoided_daily_mean_core_day_runtime_deltaT_cooling_baseline10': 183.25276458586188,
        'avoided_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional': 40.69889060412104,
        'avoided_daily_mean_core_day_runtime_hourlyavgCTD_baseline10': 192.37100619232558,
        'avoided_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional': 67.81075711275345,
        'avoided_total_core_day_runtime_dailyavgCTD_baseline10': 54242.818188885714,
        'avoided_total_core_day_runtime_dailyavgCTD_baseline_regional': 12046.871604977077,
        'avoided_total_core_day_runtime_deltaT_cooling_baseline10': 54242.81831741512,
        'avoided_total_core_day_runtime_deltaT_cooling_baseline_regional': 12046.871618819827,
        'avoided_total_core_day_runtime_hourlyavgCTD_baseline10': 56941.817832928369,
        'avoided_total_core_day_runtime_hourlyavgCTD_baseline_regional': 20071.984105375021,
        'baseline10_core_cooling_comfort_temperature': 69.5,
        'baseline_daily_mean_core_day_runtime_dailyavgCTD_baseline10': 430.16830469218144,
        'baseline_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional': 287.61443109789553,
        'baseline_daily_mean_core_day_runtime_deltaT_cooling_baseline10': 430.1683051264024,
        'baseline_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional': 287.61443114466158,
        'baseline_daily_mean_core_day_runtime_hourlyavgCTD_baseline10': 439.28654673286616,
        'baseline_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional': 314.72629765329395,
        'baseline_total_core_day_runtime_dailyavgCTD_baseline10': 127329.81818888571,
        'baseline_total_core_day_runtime_dailyavgCTD_baseline_regional': 85133.871604977074,
        'baseline_total_core_day_runtime_deltaT_cooling_baseline10': 127329.81831741511,
        'baseline_total_core_day_runtime_deltaT_cooling_baseline_regional': 85133.87161881983,
        'baseline_total_core_day_runtime_hourlyavgCTD_baseline10': 130028.81783292838,
        'baseline_total_core_day_runtime_hourlyavgCTD_baseline_regional': 93158.984105375013,
        'climate_zone': 'Mixed-Humid',
        'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
        'cv_root_mean_sq_err_dailyavgCTD': 0.032453703894877235,
        'cv_root_mean_sq_err_deltaT_cooling': 0.032453703894877235,
        'cv_root_mean_sq_err_hourlyavgCTD': 0.076369208143191203,
        'daily_mean_core_cooling_runtime': 246.91554054054055,
        'end_date': '2014-12-31T00:00:00',
        'equipment_type': 1,
        'heating_or_cooling': 'cooling_ALL',
        'mean_abs_err_dailyavgCTD': 6.0097250289894051,
        'mean_abs_err_deltaT_cooling': 6.0097250021163369,
        'mean_abs_err_hourlyavgCTD': 11.86500967954804,
        'mean_abs_pct_err_dailyavgCTD': 0.024339193133948087,
        'mean_abs_pct_err_deltaT_cooling': 0.04118465892027369,
        'mean_abs_pct_err_hourlyavgCTD': 0.048052907701044228,
        'mean_demand_dailyavgCTD': 6.009042044649723,
        'mean_demand_deltaT_cooling': 5.8924138949217086,
        'mean_demand_hourlyavgCTD': 5.6420937008580641,
        'mean_sq_err_dailyavgCTD': 64.213358960645721,
        'mean_sq_err_deltaT_cooling': 64.213358960645706,
        'mean_sq_err_hourlyavgCTD': 355.57680594741566,
        'n_core_cooling_days': 296,
        'n_days_both_heating_and_cooling': 212,
        'n_days_in_inputfile_date_range': 1460,
        'n_days_insufficient_data': 13,
        'percent_savings_dailyavgCTD_baseline10': 42.600247891990179,
        'percent_savings_dailyavgCTD_baseline_regional': 14.150503645452437,
        'percent_savings_deltaT_cooling_baseline10': 42.600247949930704,
        'percent_savings_deltaT_cooling_baseline_regional': 14.150503659411548,
        'percent_savings_hourlyavgCTD_baseline10': 43.791690782032532,
        'percent_savings_hourlyavgCTD_baseline_regional': 21.545945673549831,
        'regional_average_baseline_cooling_comfort_temperature': 73.0,
        'root_mean_sq_err_dailyavgCTD': 8.0133238397462581,
        'root_mean_sq_err_deltaT_cooling': 8.0133238397462581,
        'root_mean_sq_err_hourlyavgCTD': 18.856744309329105,
        'start_date': '2011-01-01T00:00:00',
        'station': '725314',
        'sw_version': '0.4.1',
        'tau_dailyavgCTD': 0.11662814972801475,
        'tau_deltaT_cooling': 0.11662812910919834,
        'tau_hourlyavgCTD': -0.77340507831642546,
        'total_core_cooling_runtime': 73087.0,
        'zipcode': '62223'
    }, {
        '_daily_mean_core_day_demand_baseline_dailyavgHTD_baseline90': 27.151440137506324,
        '_daily_mean_core_day_demand_baseline_dailyavgHTD_baseline_regional': 26.651440137506324,
        '_daily_mean_core_day_demand_baseline_deltaT_heating_baseline90': 24.819205077379504,
        '_daily_mean_core_day_demand_baseline_deltaT_heating_baseline_regional': 24.319205077379504,
        '_daily_mean_core_day_demand_baseline_hourlyavgHTD_baseline90': 27.287371123657238,
        '_daily_mean_core_day_demand_baseline_hourlyavgHTD_baseline_regional': 26.803790817658069,
        'alpha_dailyavgHTD': 31.752492184412699,
        'alpha_deltaT_heating': 31.752492305778286,
        'alpha_hourlyavgHTD': 31.710213838562527,
        'avoided_daily_mean_core_day_runtime_dailyavgHTD_baseline90': 89.047678471216088,
        'avoided_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional': 73.17143237900973,
        'avoided_daily_mean_core_day_runtime_deltaT_heating_baseline90': 89.047677955482044,
        'avoided_daily_mean_core_day_runtime_deltaT_heating_baseline_regional': 73.171431802592892,
        'avoided_daily_mean_core_day_runtime_hourlyavgHTD_baseline90': 92.210161132884522,
        'avoided_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional': 76.87572622153327,
        'avoided_total_core_day_runtime_dailyavgHTD_baseline90': 79697.672231738397,
        'avoided_total_core_day_runtime_dailyavgHTD_baseline_regional': 65488.43197921371,
        'avoided_total_core_day_runtime_deltaT_heating_baseline90': 79697.671770156434,
        'avoided_total_core_day_runtime_deltaT_heating_baseline_regional': 65488.431463320638,
        'avoided_total_core_day_runtime_hourlyavgHTD_baseline90': 82528.094213931647,
        'avoided_total_core_day_runtime_hourlyavgHTD_baseline_regional': 68803.774968272279,
        'baseline90_core_heating_comfort_temperature': 69.5,
        'baseline_daily_mean_core_day_runtime_dailyavgHTD_baseline90': 862.12589076171889,
        'baseline_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional': 846.24964466951258,
        'baseline_daily_mean_core_day_runtime_deltaT_heating_baseline90': 862.12589024598481,
        'baseline_daily_mean_core_day_runtime_deltaT_heating_baseline_regional': 846.24964409309575,
        'baseline_daily_mean_core_day_runtime_hourlyavgHTD_baseline90': 865.28837342338727,
        'baseline_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional': 849.95393851203607,
        'baseline_total_core_day_runtime_dailyavgHTD_baseline90': 771602.67223173846,
        'baseline_total_core_day_runtime_dailyavgHTD_baseline_regional': 757393.43197921372,
        'baseline_total_core_day_runtime_deltaT_heating_baseline90': 771602.67177015636,
        'baseline_total_core_day_runtime_deltaT_heating_baseline_regional': 757393.43146332074,
        'baseline_total_core_day_runtime_hourlyavgHTD_baseline90': 774433.09421393159,
        'baseline_total_core_day_runtime_hourlyavgHTD_baseline_regional': 760708.77496827231,
        'climate_zone': 'Mixed-Humid',
        'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
        'cv_root_mean_sq_err_dailyavgHTD': 0.10577527836616675,
        'cv_root_mean_sq_err_deltaT_heating': 0.10577527836616675,
        'cv_root_mean_sq_err_hourlyavgHTD': 0.10688726642785656,
        'daily_mean_core_heating_runtime': 773.07821229050285,
        'end_date': '2014-12-31T00:00:00',
        'equipment_type': 1,
        'heating_or_cooling': 'heating_ALL',
        'mean_abs_err_dailyavgHTD': 53.987933696898082,
        'mean_abs_err_deltaT_heating': 53.98793310873058,
        'mean_abs_err_hourlyavgHTD': 55.118493568893847,
        'mean_abs_pct_err_dailyavgHTD': 0.069835021655753005,
        'mean_abs_pct_err_deltaT_heating': 0.13599730721793127,
        'mean_abs_pct_err_hourlyavgHTD': 0.071297434971795248,
        'mean_demand_dailyavgHTD': 24.347008978086041,
        'mean_demand_deltaT_heating': 22.014773917959218,
        'mean_demand_hourlyavgHTD': 24.379470167759287,
        'mean_sq_err_dailyavgHTD': 6686.7520765725567,
        'mean_sq_err_deltaT_heating': 6686.7520765725567,
        'mean_sq_err_hourlyavgHTD': 6828.0832609944391,
        'n_core_heating_days': 895,
        'n_days_both_heating_and_cooling': 212,
        'n_days_in_inputfile_date_range': 1460,
        'n_days_insufficient_data': 13,
        'percent_savings_dailyavgHTD_baseline90': 10.32884865486864,
        'percent_savings_dailyavgHTD_baseline_regional': 8.6465539855659852,
        'percent_savings_deltaT_heating_baseline90': 10.328848601226284,
        'percent_savings_deltaT_heating_baseline_regional': 8.6465539233412443,
        'percent_savings_hourlyavgHTD_baseline90': 10.656581547267123,
        'percent_savings_hourlyavgHTD_baseline_regional': 9.0446932166836049,
        'regional_average_baseline_heating_comfort_temperature': 69,
        'rhu_00F_to_05F': 0.0,
        'rhu_05F_to_10F': 0.35810185185185184,
        'rhu_10F_to_15F': 0.36336805555555557,
        'rhu_15F_to_20F': 0.38119557629422784,
        'rhu_20F_to_25F': 0.37248012562567473,
        'rhu_25F_to_30F': 0.33389851485148514,
        'rhu_30F_to_35F': 0.28564601161939751,
        'rhu_35F_to_40F': 0.19922959372824189,
        'rhu_40F_to_45F': 0.14960073815029559,
        'rhu_45F_to_50F': 0.091284920350038989,
        'rhu_50F_to_55F': 0.051777928495300843,
        'rhu_55F_to_60F': 0.029059252674493455,
        'root_mean_sq_err_dailyavgHTD': 81.772563103846494,
        'root_mean_sq_err_deltaT_heating': 81.772563103846494,
        'root_mean_sq_err_hourlyavgHTD': 82.63221684666604,
        'start_date': '2011-01-01T00:00:00',
        'station': '725314',
        'sw_version': '0.4.1',
        'tau_dailyavgHTD': -2.3322350601268216,
        'tau_deltaT_heating': -2.3322349401052329,
        'tau_hourlyavgHTD': -2.3424954770368576,
        'total_auxiliary_heating_core_day_runtime': 144794.0,
        'total_core_heating_runtime': 691905.0,
        'total_emergency_heating_core_day_runtime': 2104.0,
        'zipcode': '62223'
    }]
    return data
