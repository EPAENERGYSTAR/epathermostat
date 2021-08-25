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

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_1_single_metadata_missing_header.csv"])
def thermostat_type_1_metadata_missing_header(request):
    with pytest.raises(ValueError) as excinfo: 
        thermostats = from_csv(get_data_path(request.param))
        return list(thermostats)
    assert "thermostat_id" in str(excinfo)
    return []

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

@pytest.fixture(scope="session", params=["../data/single_stage/metadata_type_1_single_missing_over_18_days_temperature.csv"])
def thermostat_missing_over_18_days_temperature(request):
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
def core_heating_day_set_type_1_entire(thermostat_type_1):
    return thermostat_type_1.get_core_heating_days()[0]

@pytest.fixture(scope="session")
def core_heating_day_set_type_2(thermostat_type_2):
    return thermostat_type_2.get_core_heating_days()[0]

@pytest.fixture(scope="session")
def core_heating_day_set_type_3(thermostat_type_3):
    return thermostat_type_3.get_core_heating_days()[0]

@pytest.fixture(scope="session")
def core_heating_day_set_type_4(thermostat_type_4):
    return thermostat_type_4.get_core_heating_days()[0]

@pytest.fixture(scope="session")
def core_cooling_day_set_type_1_entire(thermostat_type_1):
    return thermostat_type_1.get_core_cooling_days()[0]

@pytest.fixture(scope="session")
def core_cooling_day_set_type_1_empty(thermostat_type_1):
    core_cooling_day_set = thermostat_type_1.get_core_cooling_days()[0]
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
    core_heating_day_set = thermostat_type_1.get_core_heating_days()[0]
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
    return thermostat_type_2.get_core_cooling_days()[0]

@pytest.fixture(scope="session")
def core_cooling_day_set_type_3(thermostat_type_3):
    return thermostat_type_3.get_core_cooling_days()[0]

@pytest.fixture(scope="session")
def core_cooling_day_set_type_5(thermostat_type_5):
    return thermostat_type_5.get_core_cooling_days()[0]
