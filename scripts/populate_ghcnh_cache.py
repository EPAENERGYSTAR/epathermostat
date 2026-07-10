"""
populate_ghcnh_cache.py
=======================
Pre-populate the eeweather SQLite cache with NOAA GHCN-H data for all
stations referenced in zipcode_usaf_station.json, then export the result
as thermostat/resources/cache.sql.gz.

Run from the epathermostat repo root:

    python scripts/populate_ghcnh_cache.py

The script is resumable: stations already cached for a given year are skipped.
2025 cache entries are stored with an updated timestamp of the current year
so eeweather treats them as non-expiring (updated_during_data_year is False).

Usage:
    python scripts/populate_ghcnh_cache.py [--workers N] [--no-export]

Options:
    --workers N       Number of parallel fetch threads (default: 8)
    --no-export       Skip re-writing cache.sql.gz (useful for incremental runs)
    --all-stations    Fetch all 4,804 non-Canadian eeweather stations instead of
                      just those in zipcode_usaf_station.json. Use this before
                      rebuilding the JSON for optimal nearest-station matching.
"""

import argparse
import gzip
import json
import logging
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime

import pandas as pd
import pytz
import eeweather
from thermostat.weather_fallback import fetch_ghcnh_hourly_temp_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# First year affected by the NOAA outage.
OUTAGE_YEAR = 2025
# Fetch through current year.
CURRENT_YEAR = date.today().year

CACHE_PATH = os.path.expanduser("~/.eeweather/cache.db")
RESOURCE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "thermostat", "resources", "cache.sql.gz"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ZIPCODE_STATION_JSON = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "thermostat", "resources", "zipcode_usaf_station.json")
)


def _load_station_ids():
    with open(_ZIPCODE_STATION_JSON) as f:
        mapping = json.load(f)
    return sorted(set(v for v in mapping.values() if v))


def _load_all_station_ids():
    """Return all non-Canadian USAF IDs from the eeweather metadata DB."""
    import os as _os
    root = _os.path.dirname(_os.path.dirname(_os.path.abspath(eeweather.__file__)))
    db_path = _os.path.join(root, 'eeweather', 'resources', 'metadata.db')
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT usaf_id FROM isd_station_metadata WHERE usaf_id NOT LIKE 'A%'"
    ).fetchall()
    conn.close()
    return sorted(r[0] for r in rows)


def _get_wban_id(usaf_id):
    try:
        meta = eeweather.get_isd_station_metadata(usaf_id)
        return meta.get("recent_wban_id")
    except Exception:
        return None


def _cache_key(usaf_id, year):
    return "isd-hourly-{}-{}".format(usaf_id, year)


def _already_cached(usaf_id, year):
    """Return True if a non-empty cache entry exists for this station+year."""
    conn = sqlite3.connect(CACHE_PATH)
    try:
        cur = conn.execute(
            "SELECT data FROM items WHERE key = ?", (_cache_key(usaf_id, year),)
        )
        row = cur.fetchone()
        if row is None:
            return False
        data = json.loads(row[0])
        # Consider it cached if at least 10% of hours have values
        non_null = sum(1 for _, v in data if v is not None)
        return non_null > (365 * 24 * 0.10)
    except Exception:
        return False
    finally:
        conn.close()


def _fetch_year(usaf_id, wban_id, year):
    """Fetch one station-year from GHCN-H. Returns (usaf_id, year, series_or_None)."""
    start = pd.Timestamp(datetime(year, 1, 1), tz=pytz.UTC)
    # Cap end at today to avoid requesting future dates.
    end_date = min(date(year, 12, 31), date.today())
    end = pd.Timestamp(datetime(end_date.year, end_date.month, end_date.day, 23, 59), tz=pytz.UTC)

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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(workers=8, no_export=False, all_stations=False):
    if all_stations:
        station_ids = _load_all_station_ids()
        logger.info("Found %d stations in eeweather metadata DB", len(station_ids))
    else:
        station_ids = _load_station_ids()
        logger.info("Found %d unique stations in zipcode JSON", len(station_ids))

    years = list(range(OUTAGE_YEAR, CURRENT_YEAR + 1))
    logger.info("Populating years: %s", years)

    # Build work list, skipping already-cached entries.
    # WBAN "99999" is a sentinel for "unknown station" — no real data exists.
    SENTINEL_WBANS = {"99999"}
    work = []
    skipped_sentinel = 0
    for usaf_id in station_ids:
        wban_id = _get_wban_id(usaf_id)
        if not wban_id:
            continue
        if wban_id in SENTINEL_WBANS:
            skipped_sentinel += 1
            continue
        for year in years:
            if _already_cached(usaf_id, year):
                continue
            work.append((usaf_id, wban_id, year))

    if skipped_sentinel:
        logger.info("Skipped %d stations with sentinel WBAN (no real data)", skipped_sentinel)
    logger.info("%d station-years to fetch (%d already cached)", len(work), len(station_ids) * len(years) - len(work))

    if not work:
        logger.info("Nothing to do.")
    else:
        fetched = 0
        written = 0
        failed = 0

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

                if fetched % 50 == 0:
                    logger.info(
                        "Progress: %d/%d fetched, %d written, %d no-data",
                        fetched, len(work), written, failed,
                    )

        logger.info(
            "Done: %d fetched, %d written to cache, %d with no GHCN-H data",
            fetched, written, failed,
        )

    if not no_export:
        out = os.path.normpath(os.path.join(os.path.dirname(__file__), RESOURCE_PATH))
        _export_cache(out)
        logger.info("Updated cache.sql.gz is ready to commit.")
    else:
        logger.info("Skipping export (--no-export).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workers", type=int, default=8, help="Parallel fetch threads (default: 8)")
    parser.add_argument("--no-export", action="store_true", help="Skip writing cache.sql.gz")
    parser.add_argument("--all-stations", action="store_true",
                        help="Fetch all 4,804 non-Canadian eeweather stations instead of just those in the JSON")
    args = parser.parse_args()
    main(workers=args.workers, no_export=args.no_export, all_stations=args.all_stations)
