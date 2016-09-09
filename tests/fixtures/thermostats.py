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
        '_daily_mean_core_day_demand_baseline_dailyavgCTD_baseline10': 10.408255245982748,
        '_daily_mean_core_day_demand_baseline_dailyavgCTD_baseline_regional': 7.4133364325744315,
        '_daily_mean_core_day_demand_baseline_deltaT_cooling_baseline10': 10.275793010752691,
        '_daily_mean_core_day_demand_baseline_deltaT_cooling_baseline_regional': 7.2757930107526905,
        '_daily_mean_core_day_demand_baseline_hourlyavgCTD_baseline10': 10.076189648529365,
        '_daily_mean_core_day_demand_baseline_hourlyavgCTD_baseline_regional': 7.5963545052436077,
        'alpha_dailyavgCTD': 41.036967918237124,
        'alpha_deltaT_cooling': 41.036967982606093,
        'alpha_hourlyavgCTD': 43.197061671334374,
        'avoided_daily_mean_core_day_runtime_dailyavgCTD_baseline10': 167.94044091529256,
        'avoided_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional': 45.038053651730685,
        'avoided_daily_mean_core_day_runtime_deltaT_cooling_baseline10': 167.94044108985264,
        'avoided_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional': 45.038053640613533,
        'avoided_daily_mean_core_day_runtime_hourlyavgCTD_baseline10': 176.07898996065927,
        'avoided_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional': 68.957398341402126,
        'avoided_total_core_day_runtime_dailyavgCTD_baseline10': 46855.38301536662,
        'avoided_total_core_day_runtime_dailyavgCTD_baseline_regional': 12565.616968832861,
        'avoided_total_core_day_runtime_deltaT_cooling_baseline10': 46855.383064068883,
        'avoided_total_core_day_runtime_deltaT_cooling_baseline_regional': 12565.616965731177,
        'avoided_total_core_day_runtime_hourlyavgCTD_baseline10': 49126.038199023933,
        'avoided_total_core_day_runtime_hourlyavgCTD_baseline_regional': 19239.114137251192,
        'baseline10_core_cooling_comfort_temperature': 70.0,
        'baseline_daily_mean_core_day_runtime_dailyavgCTD_baseline10': 427.12323661421726,
        'baseline_daily_mean_core_day_runtime_dailyavgCTD_baseline_regional': 304.22084935065539,
        'baseline_daily_mean_core_day_runtime_deltaT_cooling_baseline10': 427.12323678877738,
        'baseline_daily_mean_core_day_runtime_deltaT_cooling_baseline_regional': 304.22084933953829,
        'baseline_daily_mean_core_day_runtime_hourlyavgCTD_baseline10': 435.26178565958395,
        'baseline_daily_mean_core_day_runtime_hourlyavgCTD_baseline_regional': 328.14019404032683,
        'baseline_total_core_day_runtime_dailyavgCTD_baseline10': 119167.38301536662,
        'baseline_total_core_day_runtime_dailyavgCTD_baseline_regional': 84877.616968832852,
        'baseline_total_core_day_runtime_deltaT_cooling_baseline10': 119167.38306406888,
        'baseline_total_core_day_runtime_deltaT_cooling_baseline_regional': 84877.616965731184,
        'baseline_total_core_day_runtime_hourlyavgCTD_baseline10': 121438.03819902393,
        'baseline_total_core_day_runtime_hourlyavgCTD_baseline_regional': 91551.114137251192,
        'climate_zone': 'Mixed-Humid',
        'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
        'cv_root_mean_sq_err_dailyavgCTD': 0.035622600852994589,
        'cv_root_mean_sq_err_deltaT_cooling': 0.035622600852994589,
        'cv_root_mean_sq_err_hourlyavgCTD': 0.059215432670233249,
        'daily_mean_core_cooling_runtime': 259.18279569892474,
        'end_date': '2014-12-31T00:00:00',
        'equipment_type': 1,
        'heating_or_cooling': 'cooling_ALL',
        'mean_abs_err_dailyavgCTD': 6.7245506618977666,
        'mean_abs_err_deltaT_cooling': 6.7245506557544878,
        'mean_abs_err_hourlyavgCTD': 9.6841574264109198,
        'mean_abs_pct_err_dailyavgCTD': 0.025945204594942428,
        'mean_abs_pct_err_deltaT_cooling': 0.039751319303639385,
        'mean_abs_pct_err_hourlyavgCTD': 0.037364198500506783,
        'mean_demand_dailyavgCTD': 6.3158368867633135,
        'mean_demand_deltaT_cooling': 6.1833746515332546,
        'mean_demand_hourlyavgCTD': 6.0000098541637321,
        'mean_sq_err_dailyavgCTD': 85.243954699804632,
        'mean_sq_err_deltaT_cooling': 85.243954699804632,
        'mean_sq_err_hourlyavgCTD': 235.54948226916471,
        'n_core_cooling_days': 279,
        'n_days_both_heating_and_cooling': 212,
        'n_days_in_inputfile_date_range': 1460,
        'n_days_insufficient_data': 13,
        'percent_savings_dailyavgCTD_baseline10': 39.318966171577863,
        'percent_savings_dailyavgCTD_baseline_regional': 14.804394159000681,
        'percent_savings_deltaT_cooling_baseline10': 39.318966196377467,
        'percent_savings_deltaT_cooling_baseline_regional': 14.804394155887371,
        'percent_savings_hourlyavgCTD_baseline10': 40.453583512697747,
        'percent_savings_hourlyavgCTD_baseline_regional': 21.014614970614538,
        'regional_average_baseline_cooling_comfort_temperature': 73.0,
        'root_mean_sq_err_dailyavgCTD': 9.2327652791460384,
        'root_mean_sq_err_deltaT_cooling': 9.2327652791460384,
        'root_mean_sq_err_hourlyavgCTD': 15.347621387992497,
        'start_date': '2011-01-01T00:00:00',
        'station': '725314',
        'sw_version': '0.3.4',
        'tau_dailyavgCTD': 0.13246223523005834,
        'tau_deltaT_cooling': 0.1324622231578064,
        'tau_hourlyavgCTD': -0.59772643108680812,
        'total_core_cooling_runtime': 72312.0,
        'zipcode': '62223'
    }, {
        '_daily_mean_core_day_demand_baseline_dailyavgHTD_baseline90': 27.646627575551069,
        '_daily_mean_core_day_demand_baseline_dailyavgHTD_baseline_regional': 27.146627575551069,
        '_daily_mean_core_day_demand_baseline_deltaT_heating_baseline90': 25.183145519077197,
        '_daily_mean_core_day_demand_baseline_deltaT_heating_baseline_regional': 24.683145519077197,
        '_daily_mean_core_day_demand_baseline_hourlyavgHTD_baseline90': 27.75294901325627,
        '_daily_mean_core_day_demand_baseline_hourlyavgHTD_baseline_regional': 27.266783508260538,
        'alpha_dailyavgHTD': 31.616543138550465,
        'alpha_deltaT_heating': 31.616543261864294,
        'alpha_hourlyavgHTD': 31.581695733213213,
        'avoided_daily_mean_core_day_runtime_dailyavgHTD_baseline90': 90.315283173767568,
        'avoided_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional': 74.507011604492305,
        'avoided_daily_mean_core_day_runtime_deltaT_heating_baseline90': 90.31528344676417,
        'avoided_daily_mean_core_day_runtime_deltaT_heating_baseline_regional': 74.507011815832016,
        'avoided_daily_mean_core_day_runtime_hourlyavgHTD_baseline90': 92.709681231957688,
        'avoided_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional': 77.355750177198516,
        'avoided_total_core_day_runtime_dailyavgHTD_baseline90': 79658.079759262997,
        'avoided_total_core_day_runtime_dailyavgHTD_baseline_regional': 65715.184235162218,
        'avoided_total_core_day_runtime_deltaT_heating_baseline90': 79658.080000046,
        'avoided_total_core_day_runtime_deltaT_heating_baseline_regional': 65715.184421563841,
        'avoided_total_core_day_runtime_hourlyavgHTD_baseline90': 81769.93884658668,
        'avoided_total_core_day_runtime_hourlyavgHTD_baseline_regional': 68227.771656289086,
        'baseline90_core_heating_comfort_temperature': 69.5,
        'baseline_daily_mean_core_day_runtime_dailyavgHTD_baseline90': 874.0907933778492,
        'baseline_daily_mean_core_day_runtime_dailyavgHTD_baseline_regional': 858.28252180857396,
        'baseline_daily_mean_core_day_runtime_deltaT_heating_baseline90': 874.09079365084574,
        'baseline_daily_mean_core_day_runtime_deltaT_heating_baseline_regional': 858.28252201991359,
        'baseline_daily_mean_core_day_runtime_hourlyavgHTD_baseline90': 876.48519143603937,
        'baseline_daily_mean_core_day_runtime_hourlyavgHTD_baseline_regional': 861.13126038128019,
        'baseline_total_core_day_runtime_dailyavgHTD_baseline90': 770948.07975926297,
        'baseline_total_core_day_runtime_dailyavgHTD_baseline_regional': 757005.18423516222,
        'baseline_total_core_day_runtime_deltaT_heating_baseline90': 770948.08000004594,
        'baseline_total_core_day_runtime_deltaT_heating_baseline_regional': 757005.18442156375,
        'baseline_total_core_day_runtime_hourlyavgHTD_baseline90': 773059.93884658674,
        'baseline_total_core_day_runtime_hourlyavgHTD_baseline_regional': 759517.77165628911,
        'climate_zone': 'Mixed-Humid',
        'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
        'cv_root_mean_sq_err_dailyavgHTD': 0.10463571541123799,
        'cv_root_mean_sq_err_deltaT_heating': 0.10463571541123795,
        'cv_root_mean_sq_err_hourlyavgHTD': 0.10546367026360252,
        'daily_mean_core_heating_runtime': 783.77551020408168,
        'end_date': '2014-12-31T00:00:00',
        'equipment_type': 1,
        'heating_or_cooling': 'heating_ALL',
        'mean_abs_err_dailyavgHTD': 54.422121420106983,
        'mean_abs_err_deltaT_heating': 54.422120753917241,
        'mean_abs_err_hourlyavgHTD': 55.254760591329067,
        'mean_abs_pct_err_dailyavgHTD': 0.069435853393705046,
        'mean_abs_pct_err_deltaT_heating': 0.12004353179248572,
        'mean_abs_pct_err_hourlyavgHTD': 0.070498197343448088,
        'mean_demand_dailyavgHTD': 24.790044464045593,
        'mean_demand_deltaT_heating': 22.326562407571725,
        'mean_demand_hourlyavgHTD': 24.81739792647727,
        'mean_sq_err_dailyavgHTD': 6725.7895611049762,
        'mean_sq_err_deltaT_heating': 6725.7895611049726,
        'mean_sq_err_hourlyavgHTD': 6832.6494743152734,
        'n_core_heating_days': 882,
        'n_days_both_heating_and_cooling': 212,
        'n_days_in_inputfile_date_range': 1460,
        'n_days_insufficient_data': 13,
        'percent_savings_dailyavgHTD_baseline90': 10.332483062171594,
        'percent_savings_dailyavgHTD_baseline_regional': 8.6809424299461497,
        'percent_savings_deltaT_heating_baseline90': 10.332483090176611,
        'percent_savings_deltaT_heating_baseline_regional': 8.6809424524321521,
        'percent_savings_hourlyavgHTD_baseline90': 10.577438402588584,
        'percent_savings_hourlyavgHTD_baseline_regional': 8.9830382121940353,
        'regional_average_baseline_heating_comfort_temperature': 69,
        'rhu_00F_to_05F': 0.13811230585424134,
        'rhu_05F_to_10F': 0.21504112808460635,
        'rhu_10F_to_15F': 0.25189433583120524,
        'rhu_15F_to_20F': 0.34905586867873561,
        'rhu_20F_to_25F': 0.2565088069329351,
        'rhu_25F_to_30F': 0.30574378831881249,
        'rhu_30F_to_35F': 0.268709491472999,
        'rhu_35F_to_40F': 0.24520583502050564,
        'rhu_40F_to_45F': 0.12015639518746908,
        'rhu_45F_to_50F': 0.069261820071140248,
        'rhu_50F_to_55F': 0.04768494913443562,
        'rhu_55F_to_60F': 0.026319839926119748,
        'root_mean_sq_err_dailyavgHTD': 82.010911232012148,
        'root_mean_sq_err_deltaT_heating': 82.01091123201212,
        'root_mean_sq_err_hourlyavgHTD': 82.659841968850102,
        'start_date': '2011-01-01T00:00:00',
        'station': '725314',
        'sw_version': '0.3.4',
        'tau_dailyavgHTD': -2.46348205647387,
        'tau_deltaT_heating': -2.4634819572784949,
        'tau_hourlyavgHTD': -2.4755774760841209,
        'total_auxiliary_heating_core_day_runtime': 144794.0,
        'total_core_heating_runtime': 691290.0,
        'total_emergency_heating_core_day_runtime': 2084.0,
        'zipcode': '62223'
    }]
    return data
