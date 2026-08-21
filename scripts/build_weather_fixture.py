#!/usr/bin/env python
"""Capture the weather the test corpus needs, so the suite can run offline.

Every fixture in the suite called ``from_csv``, which fetched live from NOAA
during collection. That made the regulated golden values depend on the
network: an outage turned the build red for reasons unrelated to the code,
and a real regression looked exactly the same. It also meant the suite could
not be trusted as a diff oracle, because two runs need not agree.

``from_csv`` accepts a ``weather_source``; this records what it would have
fetched, once, into a fixture the suite reads instead.

Two things the capture has to respect:

* ``get_indexed_temperatures_eeweather`` derives its fetch window from the
  years present in the requested index, so a padded capture range fetches
  different years and eeweather's edge interpolation lands differently. The
  index has to be exactly the one the pipeline asks for.
* ``from_csv`` requests ``hourly_index_utc - utc_offset``, so the same station
  is asked for a differently-shifted window depending on the thermostat's
  offset. Entries are keyed by the request, not by the station -- merging the
  windows silently shifts the values.

Run it against a warm eeweather cache::

    EEWEATHER_CACHE_URL=sqlite:///path/to/cache.db \
        python scripts/build_weather_fixture.py

then confirm the golden test still passes.
"""
import io
import lzma
import os
import sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import thermostat.importers as importers  # noqa: E402
from thermostat.eeweather_wrapper import (  # noqa: E402
    get_indexed_temperatures_eeweather,
)

DATA = os.path.join(REPO, "tests", "data")
DEFAULT_OUT = os.path.join(DATA, "weather_fixture.npz.xz")

# every metadata file the suite loads a thermostat from
METADATA_FILES = [
    "metadata.csv",
    "metadata_type_1_single.csv",
    "metadata_type_2_single.csv",
    "metadata_type_3_single.csv",
    "metadata_type_4_single.csv",
    "metadata_type_5_single.csv",
    "metadata_single_zero_days.csv",
    "metadata_single_emg_aux_constant_on_outlier.csv",
    "metadata_type_1_single_utc_offset_0.csv",
    "metadata_type_1_single_utc_offset_bad.csv",
    "metadata_multiple_same_key.csv",
]


class _SerialPool:
    """Stand-in for multiprocessing.Pool, so captures reach this process."""

    def __init__(self, *args, **kwargs):
        pass

    def imap(self, func, iterable):
        return map(func, iterable)

    def close(self):
        pass

    def join(self):
        pass


def request_key(station, index):
    """Identifies one fetch: a station and the exact window asked for."""
    return "{}@{}@{}".format(station, index[0].value, len(index))


def capture(out_path):
    captured = {}

    def record(station, index):
        series = get_indexed_temperatures_eeweather(station, index)
        captured.setdefault(request_key(station, index), series)
        return series

    importers.Pool = _SerialPool
    for name in METADATA_FILES:
        path = os.path.join(DATA, name)
        if not os.path.exists(path):
            continue
        try:
            list(importers.from_csv(
                path, verbose=False, shuffle=False, weather_source=record))
        except Exception as error:  # a metadata file may be a bad-input fixture
            print("  {}: {}".format(name, error))

    payload = {}
    for key, series in sorted(captured.items()):
        step = np.diff(np.asarray(series.index.view("int64")))
        assert (step == 3_600 * 10 ** 9).all(), "index is not regular hourly"
        payload[key] = series.to_numpy(dtype="float64")

    buffer = io.BytesIO()
    # savez then lzma rather than savez_compressed: zlib gives 3.9 MB on this
    # data and lzma 2.3 MB, and the fixture is committed
    np.savez(buffer, **payload)
    data = lzma.compress(buffer.getvalue(), preset=9)
    with open(out_path, "wb") as handle:
        handle.write(data)

    stations = {key.split("@")[0] for key in payload}
    print("requests: {}   stations: {}   {:,} bytes".format(
        len(payload), len(stations), len(data)))


if __name__ == "__main__":
    capture(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT)
