import struct
import json
import collections
from multiprocessing import Pool
from datetime import datetime
from pathlib import Path

import eeweather
from thermostat.stations import _get_both_year_station

import logging
logger = logging.getLogger(__name__)

# Census ZCTA shapefile lives one directory above the epathermostat package root.
_DBF_PATH = (
    Path(__file__).parent.parent.parent
    / 'US' / 'tl_2020_us_zcta520' / 'tl_2020_us_zcta520.dbf'
)
_OUT_PATH = (
    Path(__file__).parent.parent
    / 'thermostat' / 'resources' / 'zipcode_usaf_station.json'
)


def read_census_dbf(dbf_path):
    """Return list of (zcta, lat, lon) from a Census ZCTA shapefile DBF.

    Reads ZCTA5CE20, INTPTLAT20, INTPTLON20 columns only.
    """
    result = []
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

        f.read(1)  # header terminator byte

        col_offsets = {}
        offset = 1  # byte 0 is the deletion flag
        for name, flen in fields:
            col_offsets[name] = (offset, flen)
            offset += flen

        zcta_off, zcta_len = col_offsets['ZCTA5CE20']
        lat_off, lat_len = col_offsets['INTPTLAT20']
        lon_off, lon_len = col_offsets['INTPTLON20']

        for _ in range(nrecords):
            rec = f.read(record_size)
            if rec[0:1] == b'*':  # deleted record
                continue
            zcta = rec[zcta_off:zcta_off + zcta_len].decode('ascii').strip()
            lat = float(rec[lat_off:lat_off + lat_len].decode('ascii').strip())
            lon = float(rec[lon_off:lon_off + lon_len].decode('ascii').strip())
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


def main():
    """Regenerate zipcode_usaf_station.json with all 33,791 Census ZCTAs."""
    print("Reading Census ZCTA shapefile DBF...")
    zcta_records = read_census_dbf(_DBF_PATH)
    print(f"  {len(zcta_records):,} Census ZCTAs found")

    print("Resolving stations via eeweather cache (this may take a few minutes)...")
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

    with open(_OUT_PATH, 'w') as f:
        json.dump(sorted_lookup, f, indent=2)

    print(f"\n# eeweather version {eeweather.__version__}")
    print(f"# date {datetime.now()}")
    print(f"Written {len(sorted_lookup):,} entries to {_OUT_PATH}")
    print(f"Out of range / no qualifying station (island territories): {no_station:,}")


if __name__ == '__main__':
    main()
