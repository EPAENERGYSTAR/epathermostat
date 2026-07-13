"""
build_station_data.py
======================
Build the two committed station-data resources used by epathermostat's
weather-station fallback, in the order they depend on each other:

1. ``populate-cache`` -- fetch NOAA GHCN-H hourly temperature data for the
   relevant stations into the local eeweather SQLite cache and export it to
   ``thermostat/resources/cache.sql.gz``.
2. ``build-lookup``   -- read the Census ZCTA shapefile DBF and resolve every
   ZCTA to its nearest station that has data for both required years (using the
   cache just populated), writing ``thermostat/resources/zipcode_usaf_station.json``.

Run from the epathermostat repo root:

    # Stage 1: (re)build the cache. Use --all-stations before rebuilding the
    # lookup so nearest-station matching can choose from every station.
    python scripts/build_station_data.py populate-cache --all-stations

    # Stage 2: rebuild the ZCTA -> station JSON from the populated cache.
    python scripts/build_station_data.py build-lookup

    # Or do both in order:
    python scripts/build_station_data.py all

populate-cache is resumable: station-years already present in the cache are
skipped. 2025 cache entries are stored with an ``updated`` timestamp in the
current year so eeweather treats them as non-expiring
(``updated_during_data_year`` is False).
"""

import argparse
import collections
import gzip
import json
import logging
import os
import sqlite3
import struct
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from multiprocessing import Pool
from pathlib import Path

import pandas as pd
import pytz
import eeweather
from thermostat.stations import _get_both_year_station
from thermostat.weather_fallback import fetch_ghcnh_hourly_temp_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# First year affected by the NOAA outage; fetch through the current year.
OUTAGE_YEAR = 2025
CURRENT_YEAR = date.today().year

CACHE_PATH = os.path.expanduser("~/.eeweather/cache.db")

_RESOURCES = Path(__file__).parent.parent / "thermostat" / "resources"
_CACHE_SQL_PATH = _RESOURCES / "cache.sql.gz"
_ZIPCODE_STATION_JSON = _RESOURCES / "zipcode_usaf_station.json"

# Census ZCTA shapefile lives one directory above the epathermostat package root.
_DBF_PATH = (
    Path(__file__).parent.parent.parent
    / "US" / "tl_2020_us_zcta520" / "tl_2020_us_zcta520.dbf"
)


# ===========================================================================
# Stage 1: populate the eeweather cache from GHCN-H
# ===========================================================================

def _load_station_ids():
    with open(_ZIPCODE_STATION_JSON) as f:
        mapping = json.load(f)
    return sorted(set(v for v in mapping.values() if v))


def _load_all_station_ids(min_quality=None):
    """Return non-Canadian USAF IDs from the eeweather metadata DB.

    min_quality: None (all), 'high' (high only), or 'high,medium' (both).
    """
    root = os.path.dirname(os.path.dirname(os.path.abspath(eeweather.__file__)))
    db_path = os.path.join(root, "eeweather", "resources", "metadata.db")
    conn = sqlite3.connect(db_path)
    if min_quality:
        allowed = tuple(q.strip() for q in min_quality.split(","))
        placeholders = ",".join("?" * len(allowed))
        rows = conn.execute(
            "SELECT usaf_id FROM isd_station_metadata "
            "WHERE usaf_id NOT LIKE 'A%' AND quality IN ({})".format(placeholders),
            allowed,
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT usaf_id FROM isd_station_metadata WHERE usaf_id NOT LIKE 'A%'"
        ).fetchall()
    conn.close()
    return sorted(r[0] for r in rows)


def _get_wban_id(usaf_id):
    try:
        meta = eeweather.get_isd_station_metadata(usaf_id)
        wban = meta.get("recent_wban_id")
        if wban and wban != "99999":
            return wban
        # recent_wban_id is a sentinel -- fall back to the first valid WBAN in wban_ids.
        for candidate in (meta.get("wban_ids") or "").split(","):
            candidate = candidate.strip()
            if candidate and candidate != "99999":
                return candidate
        return None
    except Exception:
        return None


def _cache_key(usaf_id, year):
    return "isd-hourly-{}-{}".format(usaf_id, year)


def _load_cached_keys():
    """Return the set of all isd-hourly-* keys already in the cache."""
    conn = sqlite3.connect(CACHE_PATH)
    try:
        rows = conn.execute(
            "SELECT key FROM items WHERE key LIKE 'isd-hourly-%'"
        ).fetchall()
        return {r[0] for r in rows}
    except Exception:
        return set()
    finally:
        conn.close()


def _fetch_year(usaf_id, wban_id, year):
    """Fetch one station-year from GHCN-H. Returns (usaf_id, year, series_or_None)."""
    start = pd.Timestamp(datetime(year, 1, 1), tz=pytz.UTC)
    # Cap end at today to avoid requesting future dates.
    end_date = min(date(year, 12, 31), date.today())
    end = pd.Timestamp(
        datetime(end_date.year, end_date.month, end_date.day, 23, 59), tz=pytz.UTC
    )

    ts = fetch_ghcnh_hourly_temp_data(wban_id, start, end)
    if ts.empty:
        return usaf_id, year, None

    # Reindex to the full hourly range so the series length is consistent.
    full_index = pd.date_range(start, end, freq="h", tz=pytz.UTC)
    ts = ts.reindex(full_index)
    return usaf_id, year, ts


def _write_to_cache(usaf_id, year, ts):
    """Write a series to the eeweather cache using eeweather's own serializer."""
    eeweather.write_isd_hourly_temp_data_to_cache(usaf_id, year, ts)


def _export_cache(output_path):
    """Dump the SQLite cache to a gzipped SQL file."""
    logger.info("Exporting cache to %s ...", output_path)
    conn = sqlite3.connect(CACHE_PATH)
    with gzip.open(output_path, "wt", encoding="utf-8") as f:
        for line in conn.iterdump():
            f.write(line + "\n")
    conn.close()
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info("Export complete: %.1f MB", size_mb)


def populate_cache(workers=8, no_export=False, all_stations=False, min_quality=None):
    if all_stations:
        station_ids = _load_all_station_ids(min_quality=min_quality)
        logger.info(
            "Found %d stations in eeweather metadata DB (quality filter: %s)",
            len(station_ids), min_quality or "none",
        )
    else:
        station_ids = _load_station_ids()
        logger.info("Found %d unique stations in zipcode JSON", len(station_ids))

    years = list(range(OUTAGE_YEAR, CURRENT_YEAR + 1))
    logger.info("Populating years: %s", years)

    # Load all already-cached keys in a single query (faster than per-item lookups).
    cached_keys = _load_cached_keys()
    logger.info("Loaded %d cached keys from %s", len(cached_keys), CACHE_PATH)

    # Build work list, skipping already-cached entries.
    work = []
    for usaf_id in station_ids:
        wban_id = _get_wban_id(usaf_id)
        if not wban_id:
            continue
        for year in years:
            if _cache_key(usaf_id, year) in cached_keys:
                continue
            work.append((usaf_id, wban_id, year))
    logger.info(
        "%d station-years to fetch (%d already cached)", len(work), len(cached_keys)
    )

    if not work:
        logger.info("Nothing to do.")
    else:
        fetched = written = failed = 0
        t_start = time.monotonic()
        last_log = t_start

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(_fetch_year, usaf_id, wban_id, year): (usaf_id, year)
                for usaf_id, wban_id, year in work
            }
            for future in as_completed(futures):
                usaf_id, year = futures[future]
                try:
                    _, _, ts = future.result()
                    fetched += 1
                    if ts is not None:
                        _write_to_cache(usaf_id, year, ts)
                        written += 1
                    else:
                        logger.debug("No GHCN-H data for %s %d", usaf_id, year)
                        failed += 1
                except Exception as exc:
                    logger.warning("Error for %s %d: %s", usaf_id, year, exc)
                    failed += 1

                now = time.monotonic()
                if now - last_log >= 60 or fetched == len(work):
                    elapsed = now - t_start
                    rate = fetched / elapsed if elapsed > 0 else 0
                    eta = int((len(work) - fetched) / rate) if rate > 0 else 0
                    logger.info(
                        "Progress: %d/%d fetched, %d written, %d no-data, eta %dmin",
                        fetched, len(work), written, failed, eta // 60,
                    )
                    last_log = now

        logger.info(
            "Done: %d fetched, %d written to cache, %d with no GHCN-H data",
            fetched, written, failed,
        )

    if not no_export:
        _export_cache(str(_CACHE_SQL_PATH))
        logger.info("Updated cache.sql.gz is ready to commit.")
    else:
        logger.info("Skipping export (--no-export).")


# ===========================================================================
# Stage 2: build the ZCTA -> station lookup JSON
# ===========================================================================

def read_census_dbf(dbf_path):
    """Return list of (zcta, lat, lon) from a Census ZCTA shapefile DBF.

    Reads ZCTA5CE20, INTPTLAT20, INTPTLON20 columns only.
    """
    result = []
    with open(dbf_path, "rb") as f:
        header = f.read(32)
        nrecords = struct.unpack_from("<I", header, 4)[0]
        header_bytes = struct.unpack_from("<H", header, 8)[0]
        record_size = struct.unpack_from("<H", header, 10)[0]
        n_fields = (header_bytes - 32 - 1) // 32

        fields = []
        for _ in range(n_fields):
            fd = f.read(32)
            name = fd[:11].rstrip(b"\x00").decode("ascii")
            flen = fd[16]
            fields.append((name, flen))

        f.read(1)  # header terminator byte

        col_offsets = {}
        offset = 1  # byte 0 is the deletion flag
        for name, flen in fields:
            col_offsets[name] = (offset, flen)
            offset += flen

        zcta_off, zcta_len = col_offsets["ZCTA5CE20"]
        lat_off, lat_len = col_offsets["INTPTLAT20"]
        lon_off, lon_len = col_offsets["INTPTLON20"]

        for _ in range(nrecords):
            rec = f.read(record_size)
            if rec[0:1] == b"*":  # deleted record
                continue
            zcta = rec[zcta_off:zcta_off + zcta_len].decode("ascii").strip()
            lat = float(rec[lat_off:lat_off + lat_len].decode("ascii").strip())
            lon = float(rec[lon_off:lon_off + lon_len].decode("ascii").strip())
            result.append((zcta, lat, lon))

    return result


def lookup_station(args):
    """Resolve a single ZCTA to its nearest both-year station.

    Top-level function so multiprocessing can pickle it.
    """
    zcta, lat, lon = args
    try:
        station = _get_both_year_station(lat, lon)
    except Exception:
        station = None
    return zcta, station


def build_lookup():
    """Regenerate zipcode_usaf_station.json with all Census ZCTAs."""
    logger.info("Reading Census ZCTA shapefile DBF...")
    zcta_records = read_census_dbf(_DBF_PATH)
    logger.info("  %d Census ZCTAs found", len(zcta_records))

    logger.info("Resolving stations via eeweather cache (this may take a few minutes)...")
    with Pool() as p:
        results = p.imap(lookup_station, zcta_records, chunksize=100)
        zipcode_lookup = {}
        no_station = 0
        for zcta, station in results:
            if station is not None:
                zipcode_lookup[zcta] = station
            else:
                no_station += 1

    sorted_lookup = collections.OrderedDict(sorted(zipcode_lookup.items()))

    with open(_ZIPCODE_STATION_JSON, "w") as f:
        json.dump(sorted_lookup, f, indent=2)

    logger.info("# eeweather version %s", eeweather.__version__)
    logger.info("# date %s", datetime.now())
    logger.info("Written %d entries to %s", len(sorted_lookup), _ZIPCODE_STATION_JSON)
    logger.info(
        "Out of range / no qualifying station (island territories): %d", no_station
    )


# ===========================================================================
# CLI
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_pop = sub.add_parser(
        "populate-cache", help="Fetch GHCN-H into the cache and export cache.sql.gz"
    )
    p_pop.add_argument("--workers", type=int, default=8,
                       help="Parallel fetch threads (default: 8)")
    p_pop.add_argument("--no-export", action="store_true",
                       help="Skip writing cache.sql.gz")
    p_pop.add_argument("--all-stations", action="store_true",
                       help="Fetch all non-Canadian eeweather stations instead of "
                            "just those in the JSON")
    p_pop.add_argument("--min-quality", default=None,
                       help="Comma-separated quality tiers to include with "
                            "--all-stations (e.g. 'high' or 'high,medium'). "
                            "Default: all qualities.")

    sub.add_parser(
        "build-lookup", help="Rebuild zipcode_usaf_station.json from the cache"
    )

    p_all = sub.add_parser(
        "all", help="Run populate-cache --all-stations, then build-lookup"
    )
    p_all.add_argument("--workers", type=int, default=8,
                       help="Parallel fetch threads (default: 8)")
    p_all.add_argument("--min-quality", default=None,
                       help="Comma-separated quality tiers for the cache fetch")

    args = parser.parse_args()

    if args.command == "populate-cache":
        populate_cache(workers=args.workers, no_export=args.no_export,
                       all_stations=args.all_stations, min_quality=args.min_quality)
    elif args.command == "build-lookup":
        build_lookup()
    elif args.command == "all":
        populate_cache(workers=args.workers, all_stations=True,
                       min_quality=args.min_quality)
        build_lookup()


if __name__ == "__main__":
    main()
