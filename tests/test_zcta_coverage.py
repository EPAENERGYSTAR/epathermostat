"""
tests/test_zcta_coverage.py
===========================
Slow integration test that runs every ZCTA from zipcode_usaf_station.json
through the Jul 2025-Jun 2026 heating year pipeline and asserts >=99% coverage.

Run with:
    pytest --runslow tests/test_zcta_coverage.py -s -v
"""

import json
import os
import shutil
import sqlite3
import tempfile
import time
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import eeweather

from thermostat.importers import from_csv
from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_RESOURCES_DIR = Path(__file__).parent.parent / "thermostat" / "resources"
_JSON_PATH = _RESOURCES_DIR / "zipcode_usaf_station.json"

HEAT_START = date(2025, 7, 1)
HEAT_END = date(2026, 6, 30)
DATE_RANGE = pd.date_range(str(HEAT_START), str(HEAT_END), freq="D")

HEATING_SETPOINT = 68.0
COOLING_SETPOINT = 74.0
INDOOR_TEMP = 70.0
RUNTIME_ALPHA = 20.0

# Total 2020 Census ZCTA count.  ZCTAs absent from zipcode_usaf_station.json
# (island territories + remote Alaska with no both-year station in range) make
# up the difference between this and the map size; they count as no_station.
TOTAL_ZCTA_COUNT = 33791

BATCH_SIZE = 500

# A station qualifies only if the local cache actually holds this many valid
# daily temperatures in EACH half of the heating year (Jul-Dec 2025 and
# Jan-Jun 2026).  Checking real data — not just eeweather key existence — keeps
# assignment deterministic and guarantees the pipeline never has to reach the
# (dead) NOAA network mid-run, which would raise and drop the ZCTA.
MIN_VALID_DAYS_PER_HALF = 30
_HALF_SPLIT = "2025-12-31"


# ---------------------------------------------------------------------------
# Network safety
# ---------------------------------------------------------------------------

def _patch_block_noaa_network():
    """Block DNS lookups for NOAA hostnames so data comes only from local cache.

    Forces NOAA hostname resolution to fail immediately, keeping this coverage
    test offline and deterministic regardless of network reachability.
    """
    import socket as _socket

    _orig_getaddrinfo = _socket.getaddrinfo
    _NOAA_HOSTS = frozenset({
        "www.ncei.noaa.gov",
        "ncei.noaa.gov",
        "www.ncdc.noaa.gov",
        "ncdc.noaa.gov",
        "nomads.ncep.noaa.gov",
        "tidesandcurrents.noaa.gov",
    })

    def _patched(host, port, *args, **kwargs):
        if isinstance(host, str) and host in _NOAA_HOSTS:
            raise _socket.gaierror("NOAA network blocked: {}".format(host))
        return _orig_getaddrinfo(host, port, *args, **kwargs)

    _socket.getaddrinfo = _patched


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_offset_from_lon(lon):
    """Rough standard-time UTC offset from station longitude."""
    if lon > -88:
        return -5
    elif lon > -104:
        return -6
    elif lon > -115:
        return -7
    else:
        return -8


def _load_station_lons(station_ids):
    """Return {usaf_id: longitude_float} from eeweather's bundled metadata.db."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(eeweather.__file__)))
    db_path = os.path.join(root, "eeweather", "resources", "metadata.db")
    conn = sqlite3.connect(db_path)
    ids = sorted(station_ids)
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        "SELECT usaf_id, longitude FROM isd_station_metadata WHERE usaf_id IN ({})".format(
            placeholders
        ),
        ids,
    ).fetchall()
    conn.close()
    result = {}
    for usaf_id, lon_str in rows:
        try:
            result[usaf_id] = float(lon_str)
        except (TypeError, ValueError):
            result[usaf_id] = -90.0
    return result


def _load_station_daily_temps(station_ids):
    """Load daily mean temps (F) for heating year from eeweather cache only."""
    start = pd.Timestamp("2025-01-01", tz="UTC")
    end = pd.Timestamp("2026-12-31 23:59", tz="UTC")
    result = {}
    for usaf_id in station_ids:
        try:
            tempC, _ = eeweather.load_isd_hourly_temp_data(
                usaf_id, start, end, fetch_from_web=False
            )
            tempF = 1.8 * tempC + 32
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                daily = tempF.resample("D").mean()
            daily = daily[str(HEAT_START):str(HEAT_END)]
            # Drop the UTC tz and normalize to midnight so the index aligns
            # with the tz-naive DATE_RANGE used in _make_runtimes; otherwise the
            # reindex matches nothing and every day's temperature becomes NaN.
            daily.index = daily.index.tz_localize(None).normalize()
        except Exception:
            daily = pd.Series(np.nan, index=DATE_RANGE.normalize(), dtype=float)
        result[usaf_id] = daily
    return result


def _station_has_both_year_data(daily):
    """True if the cached daily series has real data in both halves of the year.

    Guards against stations whose eeweather key exists but whose current-year
    data is missing/empty — feeding those to the pipeline triggers a live NOAA
    fetch that fails and drops the ZCTA.
    """
    if daily is None or len(daily) == 0:
        return False
    first_half = daily[str(HEAT_START):_HALF_SPLIT]
    second_half = daily["2026-01-01":str(HEAT_END)]
    return (
        int(first_half.notna().sum()) >= MIN_VALID_DAYS_PER_HALF
        and int(second_half.notna().sum()) >= MIN_VALID_DAYS_PER_HALF
    )


def _make_runtimes(daily_temps):
    """Return (heat_runtime, cool_runtime) arrays, minutes per day, clipped to [0,1440]."""
    temps = daily_temps.reindex(DATE_RANGE.normalize()).values
    heat = np.clip(RUNTIME_ALPHA * np.maximum(HEATING_SETPOINT - temps, 0), 0, 1440)
    cool = np.clip(RUNTIME_ALPHA * np.maximum(temps - COOLING_SETPOINT, 0), 0, 1440)
    heat = np.where(np.isnan(heat), 0.0, heat)
    cool = np.where(np.isnan(cool), 0.0, cool)
    return heat, cool


def _write_interval_csv(path, heat_runtime, cool_runtime):
    """Write a 365-day equipment_type=2 interval CSV."""
    hourly_cols = []
    for h in range(24):
        hh = "{:02d}".format(h)
        hourly_cols += [
            "temp_in_{}".format(hh),
            "heating_setpoint_{}".format(hh),
            "cooling_setpoint_{}".format(hh),
        ]
    cols = ["date", "heat_runtime", "cool_runtime"] + hourly_cols
    rows = []
    for i, d in enumerate(DATE_RANGE):
        row = [d.strftime("%Y-%m-%d"), heat_runtime[i], cool_runtime[i]]
        for _ in range(24):
            row += [INDOOR_TEMP, HEATING_SETPOINT, COOLING_SETPOINT]
        rows.append(row)
    pd.DataFrame(rows, columns=cols).to_csv(path, index=False)


def _process_batch(batch, station_daily_temps, tmpdir):
    """Generate interval CSVs and run the thermostat pipeline for one batch.

    batch: list of (zcta, station, utc_offset) tuples
    Returns the flat metrics list from multiple_thermostat_calculate_epa_field_savings_metrics.
    """
    meta_rows = []
    for zcta, station, utc_off in batch:
        daily = station_daily_temps.get(station, pd.Series(dtype=float))
        heat_rt, cool_rt = _make_runtimes(daily)
        csv_name = "{}.csv".format(zcta)
        _write_interval_csv(os.path.join(tmpdir, csv_name), heat_rt, cool_rt)
        meta_rows.append({
            "thermostat_id": zcta,
            "zipcode": zcta,
            "utc_offset": str(utc_off),
            "equipment_type": 2,
            "interval_data_filename": csv_name,
        })
    meta_path = os.path.join(tmpdir, "meta.csv")
    pd.DataFrame(meta_rows).to_csv(meta_path, index=False)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        thermostats = list(from_csv(meta_path, shuffle=False))
    if not thermostats:
        return []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return multiple_thermostat_calculate_epa_field_savings_metrics(thermostats)


def _aggregate_metrics(metrics_list, batch):
    """Return per-ZCTA status dicts (ok / no_core_days / load_error)."""
    by_zcta = {}
    for m in metrics_list:
        zcta = m["ct_identifier"]
        if zcta not in by_zcta:
            by_zcta[zcta] = {}
        hc = m.get("heating_or_cooling", "")
        if "heating" in hc:
            by_zcta[zcta]["n_heat"] = m.get("n_core_heating_days")
        elif "cooling" in hc:
            by_zcta[zcta]["n_cool"] = m.get("n_core_cooling_days")
    rows = []
    for zcta, station, utc_off in batch:
        if zcta not in by_zcta:
            rows.append({"zipcode": zcta, "status": "load_error"})
        else:
            d = by_zcta[zcta]
            n_heat = d.get("n_heat") or 0
            n_cool = d.get("n_cool") or 0
            status = "ok" if (n_heat > 0 or n_cool > 0) else "no_core_days"
            rows.append({"zipcode": zcta, "status": status})
    return rows


def _run_batch_once(batch, station_daily_temps):
    """Run one batch through the pipeline and return per-ZCTA status rows."""
    tmpdir = tempfile.mkdtemp(prefix="zcta_cov_")
    try:
        try:
            metrics_list = _process_batch(batch, station_daily_temps, tmpdir)
        except Exception:
            metrics_list = []
        return _aggregate_metrics(metrics_list, batch)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _run_batch_with_retry(batch, station_daily_temps):
    """Run a batch, then re-run any dropped ZCTA on its own.

    multiprocessing.Pool sporadically drops a result under concurrent eeweather
    cache access, so a ZCTA with perfectly good data can go missing from a large
    batch.  Re-running each dropped ZCTA solo (no concurrency) recovers it; only
    a ZCTA that still fails alone is a genuine load_error.
    """
    rows = _run_batch_once(batch, station_daily_temps)
    by_id = {t[0]: t for t in batch}
    dropped = [by_id[r["zipcode"]] for r in rows if r["status"] == "load_error"]
    if dropped:
        recovered = {}
        for t in dropped:
            solo = _run_batch_once([t], station_daily_temps)
            recovered[t[0]] = solo[0]["status"] if solo else "load_error"
        for r in rows:
            if r["status"] == "load_error":
                r["status"] = recovered.get(r["zipcode"], "load_error")
    return rows


def _fmt_eta(seconds):
    if seconds is None or seconds <= 0:
        return "--:--"
    h, rem = divmod(int(seconds), 3600)
    return "{:d}h{:02d}m".format(h, rem // 60)


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_zcta_coverage_rate(pytestconfig, tmp_path):
    """
    Runs all 33,791 Census ZCTAs through the Jul 2025-Jun 2026 heating year
    pipeline. Asserts >=99% receive valid weather data and 0 pipeline crashes.

    Run with:  pytest --runslow tests/test_zcta_coverage.py -s
    """
    _patch_block_noaa_network()

    print("\nLoading both-year station map...")
    with open(_JSON_PATH) as f:
        zcta_station = json.load(f)
    # zipcode_usaf_station.json is a committed static fallback map: each value is
    # the nearest station with coverage for the relevant window.
    # ZCTAs absent from the map (island territories + remote Alaska) have no
    # station in range — a documented coverage gap.
    no_station_base = TOTAL_ZCTA_COUNT - len(zcta_station)
    station_ids = sorted(set(zcta_station.values()))
    print("  {:,} ZCTAs mapped to {:,} both-year stations; {:,} ZCTAs have no "
          "both-year station (gap)".format(
              len(zcta_station), len(station_ids), no_station_base))

    print("Loading station longitudes...")
    station_lons = _load_station_lons(set(station_ids))

    print("Pre-loading daily temperatures for {:,} stations from cache...".format(
        len(station_ids)))
    station_daily_temps = _load_station_daily_temps(station_ids)

    # Deterministic data-adequacy gate: the map is a key-existence snapshot and
    # the eeweather cache drifts, so a mapped station can still lack real
    # current-year data.  Require actual both-year data; ZCTAs whose station
    # fails join the no_station gap rather than crashing the pipeline on a live
    # fetch to the dead NOAA host.
    good_stations = {
        s for s in station_ids if _station_has_both_year_data(station_daily_temps[s])
    }
    rerouted = [z for z, s in zcta_station.items() if s not in good_stations]
    if rerouted:
        print("  {:,} ZCTAs rerouted to no_station (station lacks cached "
              "both-year data)".format(len(rerouted)))
    zcta_station = {z: s for z, s in zcta_station.items() if s in good_stations}
    station_ids = sorted(good_stations)
    no_station = no_station_base + len(rerouted)

    batches = []
    current = []
    for zcta in sorted(zcta_station.keys()):
        station = zcta_station[zcta]
        lon = station_lons.get(station, -90.0)
        current.append((zcta, station, _utc_offset_from_lon(lon)))
        if len(current) >= BATCH_SIZE:
            batches.append(current)
            current = []
    if current:
        batches.append(current)

    n_batches = len(batches)
    print("Running {:,} batches of up to {:,} ZCTAs...".format(n_batches, BATCH_SIZE))

    ok = no_core_days = load_error = 0
    batch_times = []

    for i, batch in enumerate(batches):
        t0 = time.monotonic()
        for row in _run_batch_with_retry(batch, station_daily_temps):
            s = row["status"]
            if s == "ok":
                ok += 1
            elif s == "no_core_days":
                no_core_days += 1
            else:
                load_error += 1

        batch_times.append(time.monotonic() - t0)
        avg = sum(batch_times) / len(batch_times)
        eta = _fmt_eta(avg * (n_batches - i - 1))
        print(
            "BATCH {:d}/{:d}  ok={:,}  load_error={:,}  eta={}".format(
                i + 1, n_batches, ok, load_error, eta
            ),
            flush=True,
        )

    total = TOTAL_ZCTA_COUNT
    valid = ok + no_core_days
    pct_valid = valid / total * 100

    print("\nZCTA coverage ({:,} total):".format(total))
    print("  ok:            {:>8,}  ({:5.2f}%)".format(ok, ok / total * 100))
    print(
        "  no_core_days:  {:>8,}  ({:5.2f}%)  [Hawaii — tropical, expected]".format(
            no_core_days, no_core_days / total * 100
        )
    )
    print(
        "  no_station:    {:>8,}  ({:5.2f}%)  [territories + remote AK — no both-year data]".format(
            no_station, no_station / total * 100
        )
    )
    print("  load_error:    {:>8,}  ({:5.2f}%)".format(load_error, load_error / total * 100))
    print("  VALID:         {:>8,}  ({:5.2f}%)".format(valid, pct_valid))

    pytestconfig._zcta_coverage = {
        "total": total,
        "ok": ok,
        "no_core_days": no_core_days,
        "no_station": no_station,
        "load_error": load_error,
    }

    assert load_error == 0, "{:,} ZCTAs had pipeline load errors".format(load_error)
    assert pct_valid >= 99.0, (
        "ZCTA valid-data rate {:.2f}% < 99.0% threshold "
        "(ok={:,}, no_core_days={:,}, load_error={:,})".format(
            pct_valid, ok, no_core_days, load_error
        )
    )
