from thermostat.importers import from_csv, _load_outdoor_temperatures
from thermostat.importers import normalize_utc_offset
from thermostat.util.testing import get_data_path
import datetime

import numpy as np
import pandas as pd

import pytest

from .fixtures.thermostats import (
        thermostat_type_1,
        thermostat_type_1_utc,
        thermostat_type_1_utc_bad,)

def test_import_csv(thermostat_type_1):

    def assert_is_series_with_shape(series, shape):
        assert isinstance(series, pd.Series)
        assert series.shape == shape

    assert_is_series_with_shape(thermostat_type_1.cool_runtime, (1461,))
    assert_is_series_with_shape(thermostat_type_1.heat_runtime, (1461,))

    assert_is_series_with_shape(thermostat_type_1.auxiliary_heat_runtime, (35064,))
    assert_is_series_with_shape(thermostat_type_1.emergency_heat_runtime, (35064,))

    assert_is_series_with_shape(thermostat_type_1.cooling_setpoint, (35064,))
    assert_is_series_with_shape(thermostat_type_1.heating_setpoint, (35064,))

    assert_is_series_with_shape(thermostat_type_1.temperature_in, (35064,))
    assert_is_series_with_shape(thermostat_type_1.temperature_out, (35064,))

def test_utc_offset(thermostat_type_1_utc, thermostat_type_1_utc_bad):
    assert(normalize_utc_offset("+0") == datetime.timedelta(0))
    assert(normalize_utc_offset("-0") == datetime.timedelta(0))
    assert(normalize_utc_offset("0") == datetime.timedelta(0))
    assert(normalize_utc_offset(0) == datetime.timedelta(0))
    assert(normalize_utc_offset("+6") == datetime.timedelta(0, 21600))
    assert(normalize_utc_offset("-6") == datetime.timedelta(-1, 64800))
    assert(normalize_utc_offset(-6) == datetime.timedelta(-1, 64800))

    with pytest.raises(TypeError) as excinfo:
        normalize_utc_offset(6)
    assert "Invalid UTC" in str(excinfo)

    # Load a thermostat with utc offset == 0
    assert(isinstance(thermostat_type_1_utc.cool_runtime, pd.Series))
    # the bad utc_offset row is skipped, so no thermostat is imported
    assert thermostat_type_1_utc_bad == []


def constant_60F(station, index):
    """A weather_source stand-in: 60 F for every hour, no network."""
    return pd.Series(60.0, index=index, dtype=float)


def test_from_csv_accepts_a_weather_source():
    """from_csv can be handed temperatures instead of fetching them.

    Without this seam every fixture in the suite reaches NOAA during import,
    which is what made the regression tests depend on network availability.
    """
    thermostats = list(from_csv(
        # NB: get_data_path resolves relative to the *calling* file
        get_data_path("data/metadata_type_1_single.csv"),
        shuffle=False,
        weather_source=constant_60F,
    ))

    assert len(thermostats) == 1
    temp_out = thermostats[0].temperature_out
    assert isinstance(temp_out, pd.Series)
    assert (temp_out == 60.0).all()
    # the index is the thermostat's own local hourly index, not the fetch index
    assert temp_out.index.equals(thermostats[0].temperature_in.index)


def test_legacy_return_gives_the_pre_1_8_shape():
    """legacy_return=True yields the bare iterator 1.7.x returned, with no
    summary attached, while the default carries one."""
    args = (get_data_path("data/metadata_type_1_single.csv"),)
    kwargs = dict(shuffle=False, weather_source=constant_60F)

    default = from_csv(*args, **kwargs)
    legacy = from_csv(*args, legacy_return=True, **kwargs)

    # default keeps the drop-out accounting; legacy has no summary at all
    assert hasattr(default, "summary")
    assert not hasattr(legacy, "summary")

    # both iterate to the same loaded thermostats
    legacy_list = list(legacy)
    assert [t.thermostat_id for t in legacy_list] == \
        [t.thermostat_id for t in default]
    assert len(legacy_list) == 1


# choosing a station by what it actually delivers


def _hours(year=2011, n=8760):
    return pd.date_range("{}-01-01".format(year), periods=n, freq="h", tz="UTC")


def test_a_station_that_delivers_is_kept():
    index = _hours()
    served = []

    def source(station, idx):
        served.append(station)
        return pd.Series(60.0, index=idx, dtype=float)

    station, series = _load_outdoor_temperatures(
        ["NEAR", "FAR"], source, index, "91104")

    assert station == "NEAR"
    assert served == ["NEAR"]        # the second is never loaded
    assert series.notna().all()


def test_a_station_that_returns_nothing_is_stepped_over():
    """The Susanville case: the registry span says yes, every hour is NaN."""
    index = _hours()

    def source(station, idx):
        if station == "DEAD":
            return pd.Series(np.nan, index=idx, dtype=float)
        return pd.Series(60.0, index=idx, dtype=float)

    station, series = _load_outdoor_temperatures(
        ["DEAD", "ALIVE"], source, index, "96128")

    assert station == "ALIVE"
    assert series.notna().all()


def test_a_thin_station_is_stepped_over_too():
    """Not only the wholly dead ones. Sampled nationally, a station whose
    inventory says 0.83 delivers 67-80% of hours -- usable-looking, and well
    under the threshold."""
    index = _hours()

    def source(station, idx):
        series = pd.Series(60.0, index=idx, dtype=float)
        if station == "THIN":
            series.iloc[: int(0.25 * len(idx))] = np.nan   # 75% present
        return series

    station, _ = _load_outdoor_temperatures(["THIN", "FULL"], source, index, "91104")

    assert station == "FULL"


def test_a_station_just_over_the_bar_is_accepted():
    index = _hours()

    def source(station, idx):
        series = pd.Series(60.0, index=idx, dtype=float)
        series.iloc[: int(0.05 * len(idx))] = np.nan       # 95% present
        return series

    station, _ = _load_outdoor_temperatures(["NEAR", "FAR"], source, index, "91104")

    assert station == "NEAR"


def test_the_best_covered_is_used_when_nothing_clears_the_bar():
    """When no candidate is good enough, the best-covered one is returned --
    not the nearest. A thermostat is never dropped here for want of a better
    option; a station too thin to yield core days drops downstream instead."""
    index = _hours()
    coverage = {"NEAR": 0.50, "MID": 0.88, "FAR": 0.60}

    def source(station, idx):
        series = pd.Series(60.0, index=idx, dtype=float)
        series.iloc[: int((1 - coverage[station]) * len(idx))] = np.nan
        return series

    # all three are loaded (none clears 0.9), and the 0.88 wins over the
    # nearer 0.50 -- the old code returned NEAR and discarded MID.
    station, series = _load_outdoor_temperatures(
        ["NEAR", "MID", "FAR"], source, index, "91104")

    assert station == "MID"
    assert series.notna().mean() == pytest.approx(0.88, abs=1e-3)


def test_the_walk_stops_at_the_first_success():
    """Cost matters: this runs per thermostat, and every extra candidate is
    another year of weather over the network."""
    index = _hours()
    served = []

    def source(station, idx):
        served.append(station)
        if station == "DEAD":
            return pd.Series(np.nan, index=idx, dtype=float)
        return pd.Series(60.0, index=idx, dtype=float)

    _load_outdoor_temperatures(["DEAD", "ALIVE", "UNUSED"], source, index, "96128")

    assert served == ["DEAD", "ALIVE"]
