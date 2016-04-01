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
    return thermostat_type_1.get_heating_seasons(method="year_mid_to_mid")[0]

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
def cooling_season_type_1(thermostat_type_1):
    return thermostat_type_1.get_cooling_seasons(method="year_end_to_end")[0]

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
def heating_season_type_1_data():
    data = {

        "baseline_setpoint": 69.0,
        "baseline_demand_deltaT_mean": 27.264,
        "baseline_demand_dailyavgHDD_mean": 27.264,
        "baseline_demand_hourlyavgHDD_mean": 27.353,

        "demand_deltaT_mean": 24.753,

        "demand_dailyavgHDD_mean": 27.747,
        "demand_dailyavgHDD_base": -2.994,
        "demand_dailyavgHDD_alpha": 1856.330,
        "demand_dailyavgHDD_error": 26069476.622,

        "demand_hourlyavgHDD_mean": 27.774,
        "demand_hourlyavgHDD_base": -3.017,
        "demand_hourlyavgHDD_alpha": 1854.556,
        "demand_hourlyavgHDD_error": 26213417.126,

        "regression_slope": 2028.269,
        "regression_mean_sq_error": 33507611.500,

        "total_baseline": 5776716.782,
    }
    return data

@pytest.fixture(scope="session")
def cooling_season_type_1_data():
    data = {
        "baseline_setpoint": 73.0,
        "baseline_demand_deltaT_mean": 7.917,
        "baseline_demand_dailyavgCDD_mean": 7.931,
        "baseline_demand_hourlyavgCDD_mean": 8.571,

        "demand_deltaT_mean": 6.615,

        "demand_dailyavgCDD_mean": 6.755,
        "demand_dailyavgCDD_base": 0.139,
        "demand_dailyavgCDD_alpha": 2451.223,
        "demand_dailyavgCDD_error": 313117.465,

        "demand_hourlyavgCDD_mean": 6.356,
        "demand_hourlyavgCDD_base": -0.614,
        "demand_hourlyavgCDD_alpha": 2604.821,
        "demand_hourlyavgCDD_error": 470205.068,

        "regression_slope": -2493.547,
        "regression_mean_sq_error": 499623.510,

        "total_baseline": 3805449.40,
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

            'slope_deltaT': 2451.22,
            'intercept_deltaT': 340.875,

            'alpha_est_dailyavgCDD': 2451.22,
            'alpha_est_hourlyavgCDD': 2604.821,
            'deltaT_base_est_dailyavgCDD': 0.139,
            'deltaT_base_est_hourlyavgCDD': -0.614,
            'mean_sq_err_deltaT': 313117.465,
            'mean_sq_err_dailyavgCDD': 313117.465,
            'mean_sq_err_hourlyavgCDD': 470205.068,
            'baseline_comfort_temperature': 73.0,

            'actual_seasonal_runtime': 1225295.0,
            'actual_daily_runtime': 16558.04054054054,

            'baseline_daily_runtime_deltaT': 13381.249,
            'baseline_daily_runtime_dailyavgCDD': 13353.393,
            'baseline_daily_runtime_hourlyavgCDD': 12054.887,
            'baseline_seasonal_runtime_deltaT': 990212.451,
            'baseline_seasonal_runtime_dailyavgCDD': 988151.127,
            'baseline_seasonal_runtime_hourlyavgCDD': 892061.698,

            'seasonal_avoided_runtime_deltaT': 235082.548,
            'seasonal_avoided_runtime_dailyavgCDD': 237143.872,
            'seasonal_avoided_runtime_hourlyavgCDD': 333233.301,
            'seasonal_savings_deltaT': 0.237,
            'seasonal_savings_dailyavgCDD': 0.239,
            'seasonal_savings_hourlyavgCDD': 0.373,

            'total_cooling_runtime': 1225295.0,
        },
        'heating': {
            'season_name': '2010-2011 Heating',

            'baseline_comfort_temperature': 69.0,

            'baseline_daily_runtime_deltaT': 46890.794,
            'baseline_daily_runtime_dailyavgHDD': 46890.794977101017,
            'baseline_daily_runtime_hourlyavgHDD': 46781.499,

            'baseline_seasonal_runtime_deltaT': 5955130.963,
            'baseline_seasonal_runtime_dailyavgHDD': 5955130.9620918296,
            'baseline_seasonal_runtime_hourlyavgHDD': 5941250.445,

            'actual_daily_runtime': 51509.393700787405,
            'actual_seasonal_runtime': 6541693.0,

            'seasonal_savings_deltaT': 0.098,
            'seasonal_savings_dailyavgHDD': 0.098496916632397943,
            'seasonal_savings_hourlyavgHDD': 0.16019121730023175,

            'seasonal_avoided_runtime_deltaT': 591686.950,
            'seasonal_avoided_runtime_dailyavgHDD': 586562.03790817072,
            'seasonal_avoided_runtime_hourlyavgHDD': 903231.94077690213,

            'mean_sq_err_deltaT': 26069476.622,
            'mean_sq_err_dailyavgHDD': 26069476.622,
            'mean_sq_err_hourlyavgHDD': 26213417.126,
            'slope_deltaT': 1856.330,
            'intercept_deltaT': 5376.836,
            'alpha_est_dailyavgHDD': 1856.330,
            'alpha_est_hourlyavgHDD': 1854.556,
            'deltaT_base_est_dailyavgHDD': -2.994,
            'deltaT_base_est_hourlyavgHDD': -3.017,
            'n_days_both_heating_and_cooling': 21,
            'n_days_insufficient_data': 1,

            'total_heating_runtime': 0,
            'total_emergency_heating_runtime': 0,
            'total_auxiliary_heating_runtime': 0,

            'rhu_00F_to_05F': 0.0,
            'rhu_05F_to_10F': 0.3171398454784492,
            'rhu_10F_to_15F': 0.18143782295208308,
            'rhu_15F_to_20F': 0.821,
            'rhu_20F_to_25F': 0.214,
            'rhu_25F_to_30F': 0.358,
            'rhu_30F_to_35F': 0.304,
            'rhu_35F_to_40F': 0.258,
            'rhu_40F_to_45F': 0.096,
            'rhu_45F_to_50F': 0.036,
            'rhu_50F_to_55F': 0.048,
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
