from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path
from thermostat.regression import runtime_regression
from thermostat.savings import get_daily_avoided_runtime
from thermostat.core import Thermostat, Season

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
def heating_season_type_1_mid_to_mid(thermostat_type_1):
    return thermostat_type_1.get_heating_seasons(method="year_mid_to_mid")[0]

@pytest.fixture(scope="session")
def heating_season_type_1_entire(thermostat_type_1):
    return thermostat_type_1.get_heating_seasons(method="entire_dataset")[0]

@pytest.fixture(scope="session")
def heating_season_type_2(thermostat_type_2):
    return thermostat_type_2.get_heating_seasons(method="year_mid_to_mid")[0]

@pytest.fixture(scope="session")
def heating_season_type_3(thermostat_type_3):
    return thermostat_type_3.get_heating_seasons(method="year_mid_to_mid")[0]

@pytest.fixture(scope="session")
def heating_season_type_4(thermostat_type_4):
    return thermostat_type_4.get_heating_seasons(method="year_mid_to_mid")[0]

@pytest.fixture(scope="session")
def cooling_season_type_1_end_to_end(thermostat_type_1):
    return thermostat_type_1.get_cooling_seasons(method="year_end_to_end")[0]

@pytest.fixture(scope="session")
def cooling_season_type_1_entire(thermostat_type_1):
    return thermostat_type_1.get_cooling_seasons(method="entire_dataset")[0]

@pytest.fixture(scope="session")
def cooling_season_type_1_empty(thermostat_type_1):
    cooling_season = thermostat_type_1.get_cooling_seasons(method="entire_dataset")[0]
    season = Season(
        "empty",
        pd.Series(np.tile(False, cooling_season.daily.shape),
                  index=cooling_season.daily.index),
        pd.Series(np.tile(False, cooling_season.hourly.shape),
                  index=cooling_season.hourly.index),
        cooling_season.start_date,
        cooling_season.end_date
    )
    return season

@pytest.fixture(scope="session")
def heating_season_type_1_empty(thermostat_type_1):
    heating_season = thermostat_type_1.get_heating_seasons(method="entire_dataset")[0]
    season = Season(
        "empty",
        pd.Series(np.tile(False, heating_season.daily.shape),
                  index=heating_season.daily.index),
        pd.Series(np.tile(False, heating_season.hourly.shape),
                  index=heating_season.hourly.index),
        heating_season.start_date,
        heating_season.end_date
    )
    return season

@pytest.fixture(scope="session")
def cooling_season_type_2(thermostat_type_2):
    return thermostat_type_2.get_cooling_seasons(method="year_end_to_end")[0]

@pytest.fixture(scope="session")
def cooling_season_type_3(thermostat_type_3):
    return thermostat_type_3.get_cooling_seasons(method="year_end_to_end")[0]

@pytest.fixture(scope="session")
def cooling_season_type_5(thermostat_type_5):
    return thermostat_type_5.get_cooling_seasons(method="year_end_to_end")[0]

@pytest.fixture(scope="session")
def seasonal_metrics_type_1_data():

    data = [{
        'actual_daily_runtime': 259.18279569892474,
        'actual_seasonal_runtime': 72312.0,
        'alpha_dailyavgCDD': 41.036967918237124,
        'alpha_deltaT': 41.036967982606093,
        'alpha_hourlyavgCDD': 43.197061671334374,
        'avoided_daily_runtime_dailyavgCDD': 45.038053651730685,
        'avoided_daily_runtime_deltaT': 45.038053640613533,
        'avoided_daily_runtime_hourlyavgCDD': 68.957398341402126,
        'avoided_seasonal_runtime_dailyavgCDD': 12565.616968832861,
        'avoided_seasonal_runtime_deltaT': 12565.616965731177,
        'avoided_seasonal_runtime_hourlyavgCDD': 19239.114137251192,
        'baseline_comfort_temperature': 73.0,
        'baseline_daily_runtime_dailyavgCDD': 304.22084935065539,
        'baseline_daily_runtime_deltaT': 304.22084933953829,
        'baseline_daily_runtime_hourlyavgCDD': 328.14019404032683,
        'baseline_seasonal_runtime_dailyavgCDD': 84877.616968832852,
        'baseline_seasonal_runtime_deltaT': 84877.616965731184,
        'baseline_seasonal_runtime_hourlyavgCDD': 91551.114137251192,
        'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
        'cv_root_mean_sq_err_dailyavgCDD': 0.035622600852994589,
        'cv_root_mean_sq_err_deltaT': 0.035622600852994589,
        'cv_root_mean_sq_err_hourlyavgCDD': 0.059215432670233249,
        'equipment_type': 1,
        'mean_abs_err_dailyavgCDD': 6.7245506618977666,
        'mean_abs_err_deltaT': 6.7245506557544878,
        'mean_abs_err_hourlyavgCDD': 9.6841574264109198,
        'mean_abs_pct_err_dailyavgCDD': 0.025945204594942428,
        'mean_abs_pct_err_deltaT': 0.039751319303639385,
        'mean_abs_pct_err_hourlyavgCDD': 0.037364198500506783,
        'mean_demand_baseline_dailyavgCDD': 7.4133364325744315,
        'mean_demand_baseline_deltaT': 7.2757930107526905,
        'mean_demand_baseline_hourlyavgCDD': 7.5963545052436077,
        'mean_demand_dailyavgCDD': 6.3158368867633135,
        'mean_demand_deltaT': 6.1833746515332546,
        'mean_demand_hourlyavgCDD': 6.0000098541637321,
        'mean_sq_err_dailyavgCDD': 85.243954699804632,
        'mean_sq_err_deltaT': 85.243954699804632,
        'mean_sq_err_hourlyavgCDD': 235.54948226916471,
        'n_days_both_heating_and_cooling': 212,
        'n_days_in_season': 279,
        'n_days_in_season_range': 1460,
        'n_days_insufficient_data': 13,
        'percent_savings_dailyavgCDD': 14.804394159000681,
        'percent_savings_deltaT': 14.804394155887371,
        'percent_savings_hourlyavgCDD': 21.014614970614538,
        'root_mean_sq_err_dailyavgCDD': 9.2327652791460384,
        'root_mean_sq_err_deltaT': 9.2327652791460384,
        'root_mean_sq_err_hourlyavgCDD': 15.347621387992497,
        'season_name': 'All Cooling',
        'station': '725314',
        'tau_dailyavgCDD': 0.13246223523005834,
        'tau_deltaT': 0.1324622231578064,
        'tau_hourlyavgCDD': -0.59772643108680812,
        'total_cooling_runtime': 72312.0,
        'zipcode': '62223'
    },
    {
        'actual_daily_runtime': 783.77551020408168,
        'actual_seasonal_runtime': 691290.0,
        'alpha_dailyavgHDD': 31.616543138550465,
        'alpha_deltaT': 31.616543261864294,
        'alpha_hourlyavgHDD': 31.581695733213213,
        'avoided_daily_runtime_dailyavgHDD': 74.507011604492305,
        'avoided_daily_runtime_deltaT': 74.507011815832016,
        'avoided_daily_runtime_hourlyavgHDD': 77.355750177198516,
        'avoided_seasonal_runtime_dailyavgHDD': 65715.184235162218,
        'avoided_seasonal_runtime_deltaT': 65715.184421563841,
        'avoided_seasonal_runtime_hourlyavgHDD': 68227.771656289086,
        'baseline_comfort_temperature': 69.0,
        'baseline_daily_runtime_dailyavgHDD': 858.28252180857396,
        'baseline_daily_runtime_deltaT': 858.28252201991359,
        'baseline_daily_runtime_hourlyavgHDD': 861.13126038128019,
        'baseline_seasonal_runtime_dailyavgHDD': 757005.18423516222,
        'baseline_seasonal_runtime_deltaT': 757005.18442156375,
        'baseline_seasonal_runtime_hourlyavgHDD': 759517.77165628911,
        'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
        'cv_root_mean_sq_err_dailyavgHDD': 0.10463571541123799,
        'cv_root_mean_sq_err_deltaT': 0.10463571541123795,
        'cv_root_mean_sq_err_hourlyavgHDD': 0.10546367026360252,
        'equipment_type': 1,
        'mean_abs_err_dailyavgHDD': 54.422121420106983,
        'mean_abs_err_deltaT': 54.422120753917241,
        'mean_abs_err_hourlyavgHDD': 55.254760591329067,
        'mean_abs_pct_err_dailyavgHDD': 0.069435853393705046,
        'mean_abs_pct_err_deltaT': 0.12004353179248572,
        'mean_abs_pct_err_hourlyavgHDD': 0.070498197343448088,
        'mean_demand_baseline_dailyavgHDD': 27.146627575551069,
        'mean_demand_baseline_deltaT': 24.683145519077197,
        'mean_demand_baseline_hourlyavgHDD': 27.266783508260538,
        'mean_demand_dailyavgHDD': 24.790044464045593,
        'mean_demand_deltaT': 22.326562407571725,
        'mean_demand_hourlyavgHDD': 24.81739792647727,
        'mean_sq_err_dailyavgHDD': 6725.7895611049762,
        'mean_sq_err_deltaT': 6725.7895611049726,
        'mean_sq_err_hourlyavgHDD': 6832.6494743152734,
        'n_days_both_heating_and_cooling': 212,
        'n_days_in_season': 882,
        'n_days_in_season_range': 1460,
        'n_days_insufficient_data': 13,
        'percent_savings_dailyavgHDD': 8.6809424299461497,
        'percent_savings_deltaT': 8.6809424524321521,
        'percent_savings_hourlyavgHDD': 8.9830382121940353,
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
        'root_mean_sq_err_dailyavgHDD': 82.010911232012148,
        'root_mean_sq_err_deltaT': 82.01091123201212,
        'root_mean_sq_err_hourlyavgHDD': 82.659841968850102,
        'season_name': 'All Heating',
        'station': '725314',
        'tau_dailyavgHDD': -2.46348205647387,
        'tau_deltaT': -2.4634819572784949,
        'tau_hourlyavgHDD': -2.4755774760841209,
        'total_auxiliary_heating_runtime': 144794.0,
        'total_emergency_heating_runtime': 2084.0,
        'total_heating_runtime': 691290.0,
        'zipcode': '62223'
    }]
    return data
