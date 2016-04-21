from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path
from thermostat.regression import runtime_regression
from thermostat.savings import get_daily_avoided_runtime

import pytest

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

    data = [
        {
            'actual_daily_runtime': 258.50714285714287,
            'actual_seasonal_runtime': 72382.0,
            'alpha_est_dailyavgCDD': 41.063986872312697,
            'alpha_est_hourlyavgCDD': 43.205603632243765,
            'baseline_comfort_temperature': 73.0,
            'baseline_daily_runtime_dailyavgCDD': 213.33281565792521,
            'baseline_daily_runtime_deltaT': 213.54431770100112,
            'baseline_daily_runtime_hourlyavgCDD': 189.50001944152106,
            'baseline_seasonal_runtime_dailyavgCDD': 59733.188384219058,
            'baseline_seasonal_runtime_deltaT': 59792.408956280313,
            'baseline_seasonal_runtime_hourlyavgCDD': 53060.005443625894,
            'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
            'cv_root_mean_sq_err_dailyavgCDD': 0.036034915711021194,
            'cv_root_mean_sq_err_deltaT': 0.036034915711021208,
            'cv_root_mean_sq_err_hourlyavgCDD': 0.059274915677335706,
            'deltaT_base_est_dailyavgCDD': 0.12633641311050195,
            'deltaT_base_est_hourlyavgCDD': -0.59985285737455418,
            'equipment_type': 1,
            'intercept_deltaT': 5.1878759238044738,
            'mean_abs_err_dailyavgCDD': 6.7779239378443563,
            'mean_abs_err_deltaT': 6.7779239261487616,
            'mean_abs_err_hourlyavgCDD': 9.6688889545539443,
            'mean_abs_pct_err_dailyavgCDD': 0.026219484161758722,
            'mean_abs_pct_err_deltaT': 0.040743414247220312,
            'mean_abs_pct_err_hourlyavgCDD': 0.037402792231150069,
            'mean_demand_baseline_dailyavgCDD': 7.3953235714946395,
            'mean_demand_baseline_deltaT': 7.2638366071428582,
            'mean_demand_baseline_hourlyavgCDD': 7.5803654789895161,
            'mean_demand_dailyavgCDD': 6.2952275837454241,
            'mean_demand_deltaT': 6.1688911706349217,
            'mean_demand_hourlyavgCDD': 5.9831855390216662,
            'mean_sq_err_dailyavgCDD': 86.774499299359718,
            'mean_sq_err_deltaT': 86.774499299359817,
            'mean_sq_err_hourlyavgCDD': 234.79399480077305,
            'n_days_both_heating_and_cooling': 212,
            'n_days_in_season': 280,
            'n_days_in_season_range': 1460,
            'n_days_insufficient_data': 13,
            'root_mean_sq_err_dailyavgCDD': 9.3152831035540569,
            'root_mean_sq_err_deltaT': 9.3152831035540622,
            'root_mean_sq_err_hourlyavgCDD': 15.322989094846118,
            'season_name': 'All Cooling',
            'seasonal_avoided_runtime_dailyavgCDD': 12648.811615780945,
            'seasonal_avoided_runtime_deltaT': 12589.591043719691,
            'seasonal_avoided_runtime_hourlyavgCDD': 19321.994556374106,
            'seasonal_savings_dailyavgCDD': 0.21175517259217058,
            'seasonal_savings_deltaT': 0.21055500628725446,
            'seasonal_savings_hourlyavgCDD': 0.36415364821066487,
            'slope_deltaT': 41.063986986913051,
            'station': '725314',
            'total_cooling_runtime': 72382.0,
            'zipcode': '62223'
        },
        {
            'actual_daily_runtime': 783.77551020408168,
            'actual_seasonal_runtime': 691290.0,
            'alpha_est_dailyavgHDD': 31.616543138550465,
            'alpha_est_hourlyavgHDD': 31.581695733213213,
            'baseline_comfort_temperature': 69.0,
            'baseline_daily_runtime_dailyavgHDD': 709.26849859958929,
            'baseline_daily_runtime_deltaT': 709.26849833140921,
            'baseline_daily_runtime_hourlyavgHDD': 706.41976002688307,
            'baseline_seasonal_runtime_dailyavgHDD': 625574.81576483778,
            'baseline_seasonal_runtime_deltaT': 625574.81552830292,
            'baseline_seasonal_runtime_hourlyavgHDD': 623062.22834371089,
            'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
            'cv_root_mean_sq_err_dailyavgHDD': 0.10463571541123799,
            'cv_root_mean_sq_err_deltaT': 0.10463571541123799,
            'cv_root_mean_sq_err_hourlyavgHDD': 0.10546367026360252,
            'deltaT_base_est_dailyavgHDD': -2.46348205647387,
            'deltaT_base_est_hourlyavgHDD': -2.4755774760841209,
            'equipment_type': 1,
            'intercept_deltaT': 77.886784168778192,
            'mean_abs_err_dailyavgHDD': 54.422121420106983,
            'mean_abs_err_deltaT': 54.422120797019211,
            'mean_abs_err_hourlyavgHDD': 55.254760591329067,
            'mean_abs_pct_err_dailyavgHDD': 0.069435853393705046,
            'mean_abs_pct_err_deltaT': 0.12004353214631101,
            'mean_abs_pct_err_hourlyavgHDD': 0.070498197343448088,
            'mean_demand_baseline_dailyavgHDD': 27.146627575551069,
            'mean_demand_baseline_deltaT': 24.683145519077197,
            'mean_demand_baseline_hourlyavgHDD': 27.266783508260538,
            'mean_demand_dailyavgHDD': 24.790044464045593,
            'mean_demand_deltaT': 22.326562407571725,
            'mean_demand_hourlyavgHDD': 24.81739792647727,
            'mean_sq_err_dailyavgHDD': 6725.7895611049762,
            'mean_sq_err_deltaT': 6725.7895611049753,
            'mean_sq_err_hourlyavgHDD': 6832.6494743152734,
            'n_days_both_heating_and_cooling': 212,
            'n_days_in_season': 882,
            'n_days_in_season_range': 1460,
            'n_days_insufficient_data': 13,
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
            'root_mean_sq_err_deltaT': 82.010911232012148,
            'root_mean_sq_err_hourlyavgHDD': 82.659841968850102,
            'season_name': 'All Heating',
            'seasonal_avoided_runtime_dailyavgHDD': 65715.184235162174,
            'seasonal_avoided_runtime_deltaT': 65715.184471697095,
            'seasonal_avoided_runtime_hourlyavgHDD': 68227.771656289086,
            'seasonal_savings_dailyavgHDD': 0.10504768187449767,
            'seasonal_savings_deltaT': 0.10504768229232518,
            'seasonal_savings_hourlyavgHDD': 0.10950394447382772,
            'slope_deltaT': 31.616543252350915,
            'station': '725314',
            'total_auxiliary_heating_runtime': 144794.0,
            'total_emergency_heating_runtime': 2084.0,
            'total_heating_runtime': 691290.0,
            'zipcode': '62223'
        }
    ]
    return data

# @pytest.fixture(scope="session")
# def heating_demand_deltaT_type_1(thermostat_type_1, heating_season_type_1):
#     return thermostat_type_1.get_heating_demand(heating_season_type_1, method="deltaT")
#
# @pytest.fixture(scope="session")
# def cooling_demand_deltaT_type_1(thermostat_type_1, cooling_season_type_1):
#     return thermostat_type_1.get_cooling_demand(cooling_season_type_1, method="deltaT")
#
# @pytest.fixture(scope="session")
# def baseline_heating_demand_deltaT_type_1(thermostat_type_1, heating_season_type_1):
#     return thermostat_type_1.get_baseline_heating_demand(heating_season_type_1,
#             70, method="deltaT")
#
# @pytest.fixture(scope="session")
# def baseline_cooling_demand_deltaT_type_1(thermostat_type_1, cooling_season_type_1):
#     return thermostat_type_1.get_baseline_cooling_demand(cooling_season_type_1,
#             70, method="deltaT")
#
# @pytest.fixture(scope="session")
# def heating_daily_runtime_type_1(thermostat_type_1, heating_season_type_1):
#     return thermostat_type_1.heat_runtime[heating_season_type_1.daily].values
#
# @pytest.fixture(scope="session")
# def cooling_daily_runtime_type_1(thermostat_type_1, cooling_season_type_1):
#     return thermostat_type_1.cool_runtime[cooling_season_type_1.daily].values
#
# @pytest.fixture(scope="session")
# def daily_avoided_cooling_runtime_deltaT_type_1(thermostat_type_1, cooling_demand_deltaT_type_1,
#         baseline_cooling_demand_deltaT_type_1):
#     return get_daily_avoided_runtime(-2400,
#             -cooling_demand_deltaT_type_1, baseline_cooling_demand_deltaT_type_1)
#
# @pytest.fixture(scope="session")
# def daily_avoided_heating_runtime_deltaT_type_1(thermostat_type_1, heating_demand_deltaT_type_1,
#         baseline_heating_demand_deltaT_type_1):
#     return get_daily_avoided_runtime(2400,
#             heating_demand_deltaT_type_1, baseline_heating_demand_deltaT_type_1)
