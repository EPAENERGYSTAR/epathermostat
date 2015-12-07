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
def heating_season_type_1(thermostat_type_1):
    return thermostat_type_1.get_heating_seasons()[0]

@pytest.fixture(scope="session")
def heating_season_type_2(thermostat_type_2):
    return thermostat_type_2.get_heating_seasons()[0]

@pytest.fixture(scope="session")
def heating_season_type_3(thermostat_type_3):
    return thermostat_type_3.get_heating_seasons()[0]

@pytest.fixture(scope="session")
def heating_season_type_4(thermostat_type_4):
    return thermostat_type_4.get_heating_seasons()[0]

@pytest.fixture(scope="session")
def cooling_season_type_1(thermostat_type_1):
    return thermostat_type_1.get_cooling_seasons()[0]

@pytest.fixture(scope="session")
def cooling_season_type_2(thermostat_type_2):
    return thermostat_type_2.get_cooling_seasons()[0]

@pytest.fixture(scope="session")
def cooling_season_type_3(thermostat_type_3):
    return thermostat_type_3.get_cooling_seasons()[0]

@pytest.fixture(scope="session")
def cooling_season_type_5(thermostat_type_5):
    return thermostat_type_5.get_cooling_seasons()[0]

@pytest.fixture(scope="session")
def heating_season_type_1_data():
    data = {

        "baseline_setpoint": 69.0,
        "baseline_demand_deltaT_mean": 27.231,
        "baseline_demand_dailyavgHDD_mean": 27.231,
        "baseline_demand_hourlyavgHDD_mean": 27.319,

        "demand_deltaT_mean": 24.748,

        "demand_dailyavgHDD_mean": 27.692,
        "demand_dailyavgHDD_base": -2.943,
        "demand_dailyavgHDD_alpha": 1860.052,
        "demand_dailyavgHDD_error": 26320361.186,

        "demand_hourlyavgHDD_mean": 26.742,
        "demand_hourlyavgHDD_base": -3.176,
        "demand_hourlyavgHDD_alpha": 1926.148,
        "demand_hourlyavgHDD_error": 37740348.357,

        "regression_slope": 2028.269,
        "regression_mean_sq_error": 33507611.500,

        "total_baseline": 5784859.915,
    }
    return data

@pytest.fixture(scope="session")
def cooling_season_type_1_data():
    data = {
        "baseline_setpoint": 73.0,
        "baseline_demand_deltaT_mean": 7.954,
        "baseline_demand_dailyavgCDD_mean": 7.967,
        "baseline_demand_hourlyavgCDD_mean": 8.581,

        "demand_deltaT_mean": -6.601,

        "demand_dailyavgCDD_mean": 6.788,
        "demand_dailyavgCDD_base": 0.186,
        "demand_dailyavgCDD_alpha": 2439.255,
        "demand_dailyavgCDD_error": 455238.968,

        "demand_hourlyavgCDD_mean": 6.402,
        "demand_hourlyavgCDD_base": -0.227,
        "demand_hourlyavgCDD_alpha": 2586.019,
        "demand_hourlyavgCDD_error": 967272.695,

        "regression_slope": -2493.547,
        "regression_mean_sq_error": 499623.510,

        "total_baseline": 1465638.294,
    }
    return data

@pytest.fixture(scope="session")
def seasonal_metrics_type_1(thermostat_type_1):
    seasonal_metrics_type_1 = thermostat_type_1.calculate_epa_draft_rccs_field_savings_metrics()
    return seasonal_metrics_type_1

@pytest.fixture(scope="session")
def seasonal_metrics_type_1_data():
    data = {
        'n_seasons': 9,
        'ct_identifier': '8465829e-df0d-449e-97bf-96317c24dec3',
        'equipment_type': 1,
        'zipcode': '62223',
        'station': '725314',
        'cooling': {
            'season_name': '2011 Cooling',

            'n_days_both_heating_and_cooling': 50,
            'n_days_insufficient_data': 3,

            'slope_deltaT': -2439.25,
            'intercept_deltaT': 455.782,

            'alpha_est_dailyavgCDD': 2439.2550734667493,
            'alpha_est_hourlyavgCDD': 2586.0199377023241,
            'deltaT_base_est_dailyavgCDD': 0.18685313192145378,
            'deltaT_base_est_hourlyavgCDD': -0.22766268959342667,
            'mean_squared_error_deltaT': 455238.968,
            'mean_sq_err_dailyavgCDD': 455238.96824238711,
            'mean_sq_err_hourlyavgCDD': 967272.69587867765,
            'baseline_comfort_temperature': 73.0,

            'actual_seasonal_runtime': 1225295.0,
            'actual_daily_runtime': 16558.04054054054,

            'baseline_daily_runtime_deltaT': 19859.046,
            'baseline_daily_runtime_dailyavgCDD': 13230.890480387623,
            'baseline_daily_runtime_hourlyavgCDD': 11392.382352886532,
            'baseline_seasonal_runtime_deltaT': 1469569.417,
            'baseline_seasonal_runtime_dailyavgCDD': 979085.89554868406,
            'baseline_seasonal_runtime_hourlyavgCDD': 843036.29411360342,

            'seasonal_avoided_runtime_deltaT': -244274.417,
            'seasonal_avoided_runtime_dailyavgCDD': 246209.10445131591,
            'seasonal_avoided_runtime_hourlyavgCDD': 382258.70588639658,
            'seasonal_savings_deltaT': -0.166,
            'seasonal_savings_dailyavgCDD': 0.25146833957130926,
            'seasonal_savings_hourlyavgCDD': 0.45343090037222678,
        },
        'heating': {
            'season_name': '2010-2011 Heating',

            'baseline_comfort_temperature': 69.0,

            'baseline_daily_runtime_deltaT': 46890.794,
            'baseline_daily_runtime_dailyavgHDD': 46890.794977101017,
            'baseline_daily_runtime_hourlyavgHDD': 44397.331174985018,

            'baseline_seasonal_runtime_deltaT': 5955130.963,
            'baseline_seasonal_runtime_dailyavgHDD': 5955130.9620918296,
            'baseline_seasonal_runtime_hourlyavgHDD': 5638461.0592230977,

            'actual_daily_runtime': 51509.393700787405,
            'actual_seasonal_runtime': 6541693.0,

            'seasonal_savings_deltaT': 0.098,
            'seasonal_savings_dailyavgHDD': 0.098496916632397943,
            'seasonal_savings_hourlyavgHDD': 0.16019121730023175,

            'seasonal_avoided_runtime_deltaT': 586562.03,
            'seasonal_avoided_runtime_dailyavgHDD': 586562.03790817072,
            'seasonal_avoided_runtime_hourlyavgHDD': 903231.94077690213,

            'mean_squared_error_deltaT': 26320361.186,
            'mean_sq_err_dailyavgHDD': 26320361.186872497,
            'mean_sq_err_hourlyavgHDD': 37740348.35749115,
            'slope_deltaT': 1860.051,
            'intercept_deltaT': 5475.708,
            'alpha_est_dailyavgHDD': 1860.0519991680801,
            'alpha_est_hourlyavgHDD': 1926.1484535747609,
            'deltaT_base_est_dailyavgHDD': -2.9438471466751173,
            'deltaT_base_est_hourlyavgHDD': -3.1766280839181986,
            'n_days_both_heating_and_cooling': 21,
            'n_days_insufficient_data': 1,

            'rhu_00F_to_05F': 0.0,
            'rhu_05F_to_10F': 0.3171398454784492,
            'rhu_10F_to_15F': 0.18143782295208308,
            'rhu_15F_to_20F': 0.82927887715121762,
            'rhu_20F_to_25F': 0.21074775309785052,
            'rhu_25F_to_30F': 0.36166978777239517,
            'rhu_30F_to_35F': 0.30197430104742429,
            'rhu_35F_to_40F': 0.25799949609473422,
            'rhu_40F_to_45F': 0.094300198855303843,
            'rhu_45F_to_50F': 0.048254439290994391,
            'rhu_50F_to_55F': 0.035075942295116048,
            'rhu_55F_to_60F': 0.02697922716979162,
        },
    }
    return data

@pytest.fixture(scope="session")
def heating_demand_deltaT_type_1(thermostat_type_1, heating_season_type_1):
    return thermostat_type_1.get_heating_demand(heating_season_type_1, method="deltaT")

@pytest.fixture(scope="session")
def cooling_demand_deltaT_type_1(thermostat_type_1, cooling_season_type_1):
    return thermostat_type_1.get_cooling_demand(cooling_season_type_1, method="deltaT")

@pytest.fixture(scope="session")
def baseline_heating_demand_deltaT_type_1(thermostat_type_1, heating_season_type_1):
    return thermostat_type_1.get_baseline_heating_demand(heating_season_type_1,
            70, method="deltaT")

@pytest.fixture(scope="session")
def baseline_cooling_demand_deltaT_type_1(thermostat_type_1, cooling_season_type_1):
    return thermostat_type_1.get_baseline_cooling_demand(cooling_season_type_1,
            70, method="deltaT")

@pytest.fixture(scope="session")
def heating_daily_runtime_type_1(thermostat_type_1, heating_season_type_1):
    return thermostat_type_1.heat_runtime[heating_season_type_1.daily].values

@pytest.fixture(scope="session")
def cooling_daily_runtime_type_1(thermostat_type_1, cooling_season_type_1):
    return thermostat_type_1.cool_runtime[cooling_season_type_1.daily].values

@pytest.fixture(scope="session")
def daily_avoided_cooling_runtime_deltaT_type_1(thermostat_type_1, cooling_demand_deltaT_type_1,
        baseline_cooling_demand_deltaT_type_1):
    return get_daily_avoided_runtime(-2400,
            -cooling_demand_deltaT_type_1, baseline_cooling_demand_deltaT_type_1)

@pytest.fixture(scope="session")
def daily_avoided_heating_runtime_deltaT_type_1(thermostat_type_1, heating_demand_deltaT_type_1,
        baseline_heating_demand_deltaT_type_1):
    return get_daily_avoided_runtime(2400,
            heating_demand_deltaT_type_1, baseline_heating_demand_deltaT_type_1)
