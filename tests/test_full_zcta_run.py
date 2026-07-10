"""Tests for scripts/full_zcta_run.py helper functions."""

import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from scripts.full_zcta_run import (
    utc_offset_from_lon,
    make_runtimes,
    write_interval_csv,
    aggregate_metrics,
    DATE_RANGE,
    HEATING_SETPOINT,
    COOLING_SETPOINT,
    RUNTIME_ALPHA,
)


# ---------------------------------------------------------------------------
# utc_offset_from_lon
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lon,expected", [
    (-74.0, -5),    # New York (Eastern)
    (-87.6, -5),    # Chicago just east of -88 boundary (Eastern)
    (-90.0, -6),    # Central
    (-100.0, -6),   # Kansas (Central)
    (-105.0, -7),   # Denver (Mountain)
    (-118.0, -8),   # Los Angeles (Pacific)
    (-157.0, -8),   # Honolulu — west of -115 (Pacific)
])
def test_utc_offset_from_lon(lon, expected):
    assert utc_offset_from_lon(lon) == expected


# ---------------------------------------------------------------------------
# make_runtimes
# ---------------------------------------------------------------------------

def test_make_runtimes_heating_day():
    """A cold day (T=20°F) should produce heat_runtime and zero cool_runtime."""
    cold_temps = pd.Series(20.0, index=DATE_RANGE.normalize())
    heat, cool = make_runtimes(cold_temps)
    expected_heat = min(RUNTIME_ALPHA * (HEATING_SETPOINT - 20.0), 1440)
    assert np.allclose(heat, expected_heat)
    assert np.all(cool == 0.0)


def test_make_runtimes_cooling_day():
    """A hot day (T=90°F) should produce cool_runtime and zero heat_runtime."""
    hot_temps = pd.Series(90.0, index=DATE_RANGE.normalize())
    heat, cool = make_runtimes(hot_temps)
    expected_cool = min(RUNTIME_ALPHA * (90.0 - COOLING_SETPOINT), 1440)
    assert np.allclose(cool, expected_cool)
    assert np.all(heat == 0.0)


def test_make_runtimes_nan_becomes_zero():
    """NaN temperatures should produce zero runtime (not NaN)."""
    nan_temps = pd.Series(np.nan, index=DATE_RANGE.normalize())
    heat, cool = make_runtimes(nan_temps)
    assert not np.any(np.isnan(heat))
    assert not np.any(np.isnan(cool))
    assert np.all(heat == 0.0)
    assert np.all(cool == 0.0)


def test_make_runtimes_clipped_at_1440():
    """Extremely cold temperature should be clipped to 1440 min/day."""
    arctic_temps = pd.Series(-100.0, index=DATE_RANGE.normalize())
    heat, _ = make_runtimes(arctic_temps)
    assert np.all(heat == 1440.0)


def test_make_runtimes_neutral_temperature():
    """A temperature between setpoints (71°F) should give zero runtime on both."""
    neutral_temps = pd.Series(71.0, index=DATE_RANGE.normalize())
    heat, cool = make_runtimes(neutral_temps)
    assert np.all(heat == 0.0)
    assert np.all(cool == 0.0)


# ---------------------------------------------------------------------------
# write_interval_csv
# ---------------------------------------------------------------------------

def test_write_interval_csv_columns_and_rows():
    """Interval CSV must have exactly 365 rows and the expected column set."""
    heat_rt = np.zeros(len(DATE_RANGE))
    cool_rt = np.zeros(len(DATE_RANGE))
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        path = f.name
    try:
        write_interval_csv(path, heat_rt, cool_rt)
        df = pd.read_csv(path)
        assert len(df) == len(DATE_RANGE)
        assert 'date' in df.columns
        assert 'heat_runtime' in df.columns
        assert 'cool_runtime' in df.columns
        # Spot-check hourly columns
        assert 'temp_in_00' in df.columns
        assert 'heating_setpoint_23' in df.columns
        assert 'cooling_setpoint_12' in df.columns
        # No aux/emergency columns (equipment_type=2)
        assert not any('auxiliary' in c for c in df.columns)
        assert not any('emergency' in c for c in df.columns)
    finally:
        os.unlink(path)


def test_write_interval_csv_runtime_values():
    """Heat/cool runtime values must round-trip correctly."""
    heat_rt = np.array([60.0] * len(DATE_RANGE))
    cool_rt = np.array([30.0] * len(DATE_RANGE))
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        path = f.name
    try:
        write_interval_csv(path, heat_rt, cool_rt)
        df = pd.read_csv(path)
        assert (df['heat_runtime'] == 60.0).all()
        assert (df['cool_runtime'] == 30.0).all()
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# aggregate_metrics
# ---------------------------------------------------------------------------

def _make_metric(zcta, mode, tau, cvrmse, n_days):
    """Build a minimal metric dict like calculate_epa_field_savings_metrics returns."""
    m = {'ct_identifier': zcta, 'heating_or_cooling': mode, 'tau': tau, 'cvrmse': cvrmse}
    if 'heating' in mode:
        m['n_core_heating_days'] = n_days
    else:
        m['n_core_cooling_days'] = n_days
    return m


def test_aggregate_metrics_ok_heating_and_cooling():
    """Both heating and cooling results are extracted correctly."""
    batch = [('60601', '725300', -6)]
    metrics_list = [
        _make_metric('60601', 'heating_2025_2026', tau=5.2, cvrmse=0.25, n_days=120),
        _make_metric('60601', 'cooling_2025', tau=3.1, cvrmse=0.30, n_days=80),
    ]
    rows = aggregate_metrics(metrics_list, batch)
    assert len(rows) == 1
    r = rows[0]
    assert r['status'] == 'ok'
    assert r['tau_h'] == pytest.approx(5.2)
    assert r['cvrmse_h'] == pytest.approx(0.25)
    assert r['n_core_heating_days'] == 120
    assert r['tau_c'] == pytest.approx(3.1)
    assert r['cvrmse_c'] == pytest.approx(0.30)
    assert r['n_core_cooling_days'] == 80


def test_aggregate_metrics_load_error():
    """ZCTA not appearing in metrics_list is recorded as load_error."""
    batch = [('99999', '725300', -6)]
    metrics_list = []  # nothing loaded
    rows = aggregate_metrics(metrics_list, batch)
    assert len(rows) == 1
    assert rows[0]['status'] == 'load_error'


def test_aggregate_metrics_no_core_days():
    """ZCTA that appears in metrics but with no heating_or_cooling rows → no_core_days."""
    batch = [('60601', '725300', -6)]
    # An empty dict in by_zcta: zcta present but no heating/cooling row
    # Simulate by sending a metric with unknown mode
    metrics_list = [{'ct_identifier': '60601', 'heating_or_cooling': 'unknown'}]
    rows = aggregate_metrics(metrics_list, batch)
    assert len(rows) == 1
    assert rows[0]['status'] == 'no_core_days'


def test_aggregate_metrics_multiple_zctas():
    """Multiple ZCTAs in a batch are each aggregated independently."""
    batch = [
        ('60601', '725300', -6),
        ('10001', '725053', -5),
    ]
    metrics_list = [
        _make_metric('60601', 'heating_2025_2026', tau=5.0, cvrmse=0.2, n_days=100),
        _make_metric('10001', 'heating_2025_2026', tau=6.0, cvrmse=0.3, n_days=110),
    ]
    rows = aggregate_metrics(metrics_list, batch)
    assert len(rows) == 2
    assert rows[0]['zipcode'] == '60601'
    assert rows[1]['zipcode'] == '10001'
    assert rows[0]['tau_h'] == pytest.approx(5.0)
    assert rows[1]['tau_h'] == pytest.approx(6.0)
