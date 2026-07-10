"""
full_zcta_run.py
================
Run the full epathermostat pipeline for all 33,791 Census ZCTAs.

Generates synthetic weather-proportional interval data for Jul 1, 2025 -
Jun 30, 2026, then runs from_csv + multiple_thermostat_calculate_epa_field_
savings_metrics in batches of 500.

Usage:
    python scripts/full_zcta_run.py [--batch-size N] [--output PATH]

Output: a CSV with one row per ZCTA containing assigned station, tau, cvrmse,
n_core_heating_days, n_core_cooling_days and status.

Estimated runtime: ~3-4 hours for all 33,791 ZCTAs.
"""

import argparse
import csv
import json
import logging
import os
import shutil
import struct
import tempfile
import warnings
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import eeweather

from thermostat.importers import from_csv
from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_SCRIPT_DIR = Path(__file__).parent
_JSON_PATH = _SCRIPT_DIR.parent / 'thermostat' / 'resources' / 'zipcode_usaf_station.json'
_DBF_PATH = _SCRIPT_DIR.parent.parent / 'US' / 'tl_2020_us_zcta520' / 'tl_2020_us_zcta520.dbf'

HEAT_START = date(2025, 7, 1)
HEAT_END = date(2026, 6, 30)
DATE_RANGE = pd.date_range(str(HEAT_START), str(HEAT_END), freq='D')

HEATING_SETPOINT = 68.0
COOLING_SETPOINT = 74.0
INDOOR_TEMP = 70.0
RUNTIME_ALPHA = 20.0

OUTPUT_COLS = [
    'zipcode', 'station', 'utc_offset',
    'n_core_heating_days', 'tau_h', 'cvrmse_h',
    'n_core_cooling_days', 'tau_c', 'cvrmse_c',
    'status',
]


def _patch_no_ftp():
    """Raise immediately on any FTP attempt — ensures offline-only operation."""
    import ftplib

    def _no_ftp(*a, **kw):
        raise RuntimeError("FTP disabled for full ZCTA run")

    ftplib.FTP.__init__ = _no_ftp


def read_census_dbf(dbf_path):
    """Return dict of zcta -> (lat, lon) from Census ZCTA shapefile DBF."""
    result = {}
    with open(dbf_path, 'rb') as f:
        header = f.read(32)
        nrecords = struct.unpack_from('<I', header, 4)[0]
        header_bytes = struct.unpack_from('<H', header, 8)[0]
        record_size = struct.unpack_from('<H', header, 10)[0]
        n_fields = (header_bytes - 32 - 1) // 32
        fields = []
        for _ in range(n_fields):
            fd = f.read(32)
            name = fd[:11].rstrip(b'\x00').decode('ascii')
            flen = fd[16]
            fields.append((name, flen))
        f.read(1)
        col_offsets = {}
        offset = 1
        for name, flen in fields:
            col_offsets[name] = (offset, flen)
            offset += flen
        zcta_off, zcta_len = col_offsets['ZCTA5CE20']
        lat_off, lat_len = col_offsets['INTPTLAT20']
        lon_off, lon_len = col_offsets['INTPTLON20']
        for _ in range(nrecords):
            rec = f.read(record_size)
            if rec[0:1] == b'*':
                continue
            zcta = rec[zcta_off:zcta_off + zcta_len].decode('ascii').strip()
            lat = float(rec[lat_off:lat_off + lat_len].decode('ascii').strip())
            lon = float(rec[lon_off:lon_off + lon_len].decode('ascii').strip())
            result[zcta] = (lat, lon)
    return result


def utc_offset_from_lon(lon):
    """Rough standard-time UTC offset from longitude."""
    if lon > -88:
        return -5
    elif lon > -104:
        return -6
    elif lon > -115:
        return -7
    else:
        return -8


def load_station_daily_temps(station_ids):
    """Load daily mean temperatures (°F) for heating year from eeweather cache.

    Uses cache only (fetch_from_web=False). Stations not in cache get NaN series.
    Returns dict: usaf_id -> pd.Series with daily date index.
    """
    start = pd.Timestamp('2025-01-01', tz='UTC')
    end = pd.Timestamp('2026-12-31 23:59', tz='UTC')
    result = {}
    for usaf_id in station_ids:
        try:
            tempC, _ = eeweather.load_isd_hourly_temp_data(
                usaf_id, start, end, fetch_from_web=False
            )
            tempF = 1.8 * tempC + 32
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                daily = tempF.resample('D').mean()
            daily = daily[str(HEAT_START):str(HEAT_END)]
        except Exception:
            daily = pd.Series(np.nan, index=DATE_RANGE.normalize(), dtype=float)
        result[usaf_id] = daily
    return result


def make_runtimes(daily_temps):
    """Return (heat_runtime, cool_runtime) numpy arrays for DATE_RANGE.

    heat_runtime[i] = clip(ALPHA * max(HEAT_SP - T[i], 0), 0, 1440)
    cool_runtime[i] = clip(ALPHA * max(T[i] - COOL_SP, 0), 0, 1440)
    NaN temperature days produce zero runtime (excluded from core days).
    """
    temps = daily_temps.reindex(DATE_RANGE.normalize()).values
    heat = np.clip(RUNTIME_ALPHA * np.maximum(HEATING_SETPOINT - temps, 0), 0, 1440)
    cool = np.clip(RUNTIME_ALPHA * np.maximum(temps - COOLING_SETPOINT, 0), 0, 1440)
    heat = np.where(np.isnan(heat), 0.0, heat)
    cool = np.where(np.isnan(cool), 0.0, cool)
    return heat, cool


def write_interval_csv(path, heat_runtime, cool_runtime):
    """Write a 365-day equipment_type=2 interval CSV (no aux/emergency columns)."""
    hourly_cols = []
    for h in range(24):
        hh = '{:02d}'.format(h)
        hourly_cols += [
            'temp_in_{}'.format(hh),
            'heating_setpoint_{}'.format(hh),
            'cooling_setpoint_{}'.format(hh),
        ]
    cols = ['date', 'heat_runtime', 'cool_runtime'] + hourly_cols
    rows = []
    for i, d in enumerate(DATE_RANGE):
        row = [d.strftime('%Y-%m-%d'), heat_runtime[i], cool_runtime[i]]
        for _ in range(24):
            row += [INDOOR_TEMP, HEATING_SETPOINT, COOLING_SETPOINT]
        rows.append(row)
    pd.DataFrame(rows, columns=cols).to_csv(path, index=False)


def process_batch(batch, station_daily_temps, tmpdir):
    """Generate interval CSVs, run pipeline for one batch.

    batch: list of (zcta, station, utc_offset) tuples
    Returns flat metrics list from multiple_thermostat_calculate_epa_field_savings_metrics.
    """
    meta_rows = []
    for zcta, station, utc_off in batch:
        daily = station_daily_temps.get(station, pd.Series(dtype=float))
        heat_rt, cool_rt = make_runtimes(daily)
        csv_name = '{}.csv'.format(zcta)
        write_interval_csv(os.path.join(tmpdir, csv_name), heat_rt, cool_rt)
        meta_rows.append({
            'thermostat_id': zcta,
            'zipcode': zcta,
            'utc_offset': str(utc_off),
            'equipment_type': 2,
            'interval_data_filename': csv_name,
        })

    meta_path = os.path.join(tmpdir, 'meta.csv')
    pd.DataFrame(meta_rows).to_csv(meta_path, index=False)

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        thermostats = list(from_csv(meta_path, shuffle=False))

    if not thermostats:
        return []

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        metrics = multiple_thermostat_calculate_epa_field_savings_metrics(thermostats)

    return metrics


def aggregate_metrics(metrics_list, batch):
    """Build per-ZCTA result rows from the flat metrics list.

    ZCTAs whose thermostat failed to load (not in metrics_list) get load_error.
    ZCTAs that loaded but had no core days get no_core_days.
    """
    by_zcta = {}
    for m in metrics_list:
        zcta = m['ct_identifier']
        if zcta not in by_zcta:
            by_zcta[zcta] = {}
        hot_or_cool = m.get('heating_or_cooling', '')
        if 'heating' in hot_or_cool:
            by_zcta[zcta]['n_core_heating_days'] = m.get('n_core_heating_days')
            by_zcta[zcta]['tau_h'] = m.get('tau')
            by_zcta[zcta]['cvrmse_h'] = m.get('cvrmse')
        elif 'cooling' in hot_or_cool:
            by_zcta[zcta]['n_core_cooling_days'] = m.get('n_core_cooling_days')
            by_zcta[zcta]['tau_c'] = m.get('tau')
            by_zcta[zcta]['cvrmse_c'] = m.get('cvrmse')

    loaded_zctas = set(by_zcta.keys())
    rows = []
    for zcta, station, utc_off in batch:
        if zcta not in loaded_zctas:
            rows.append({
                'zipcode': zcta, 'station': station, 'utc_offset': utc_off,
                'status': 'load_error',
            })
            continue
        d = by_zcta[zcta]
        status = 'ok' if d else 'no_core_days'
        rows.append({
            'zipcode': zcta,
            'station': station,
            'utc_offset': utc_off,
            'n_core_heating_days': d.get('n_core_heating_days'),
            'tau_h': d.get('tau_h'),
            'cvrmse_h': d.get('cvrmse_h'),
            'n_core_cooling_days': d.get('n_core_cooling_days'),
            'tau_c': d.get('tau_c'),
            'cvrmse_c': d.get('cvrmse_c'),
            'status': status,
        })
    return rows


def main(batch_size=500, output_path=None):
    _patch_no_ftp()

    if output_path is None:
        output_path = str(_SCRIPT_DIR.parent / 'full_zcta_results.csv')

    print("Loading ZCTA-to-station map...")
    with open(_JSON_PATH) as f:
        zcta_station = json.load(f)
    print("  {:,} ZCTAs with stations".format(len(zcta_station)))

    print("Loading Census centroids from DBF...")
    zcta_coords = read_census_dbf(_DBF_PATH)
    print("  {:,} Census ZCTAs".format(len(zcta_coords)))

    all_zctas = sorted(zcta_coords.keys())
    station_ids = sorted(set(v for v in zcta_station.values() if v))

    print("Pre-loading temperatures for {:,} stations from cache...".format(len(station_ids)))
    station_daily_temps = load_station_daily_temps(station_ids)
    print("  Done.")

    no_station_rows = []
    batches = []
    current_batch = []
    for zcta in all_zctas:
        station = zcta_station.get(zcta)
        lat, lon = zcta_coords.get(zcta, (0.0, -90.0))
        utc_off = utc_offset_from_lon(lon)
        if station is None:
            no_station_rows.append({
                'zipcode': zcta, 'station': None, 'utc_offset': utc_off,
                'status': 'no_station',
            })
        else:
            current_batch.append((zcta, station, utc_off))
            if len(current_batch) >= batch_size:
                batches.append(current_batch)
                current_batch = []
    if current_batch:
        batches.append(current_batch)

    print("  {:,} out-of-range ZCTAs (no_station)".format(len(no_station_rows)))
    print("  {:,} ZCTAs to run in {:,} batches of up to {:,}".format(
        len(zcta_station), len(batches), batch_size))

    with open(output_path, 'w', newline='') as outf:
        writer = csv.DictWriter(outf, fieldnames=OUTPUT_COLS, extrasaction='ignore')
        writer.writeheader()
        for row in no_station_rows:
            writer.writerow(row)

        for i, batch in enumerate(batches):
            tmpdir = tempfile.mkdtemp(prefix='zcta_batch_')
            try:
                try:
                    metrics_list = process_batch(batch, station_daily_temps, tmpdir)
                except Exception as exc:
                    logger.warning("Batch %d failed with exception: %s", i + 1, exc)
                    metrics_list = []
                rows = aggregate_metrics(metrics_list, batch)
                for row in rows:
                    writer.writerow(row)
                outf.flush()
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)

            n_processed = len(no_station_rows) + (i + 1) * batch_size
            print("Batch {:>4d}/{:>4d}  (~{:,}/{:,} ZCTAs)".format(
                i + 1, len(batches),
                min(n_processed, len(all_zctas)),
                len(all_zctas)))

    print("\nResults written to {}".format(output_path))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--batch-size', type=int, default=500,
                        help='ZCTAs per pipeline batch (default: 500)')
    parser.add_argument('--output', default=None,
                        help='Output CSV path (default: full_zcta_results.csv in repo root)')
    args = parser.parse_args()
    main(batch_size=args.batch_size, output_path=args.output)
