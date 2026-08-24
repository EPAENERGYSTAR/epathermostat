"""The recorded weather the corpus needs, so the suite never hits the network.

Every thermostat fixture used to call ``from_csv``, which fetched live from
NOAA during collection. That made the regulated golden values depend on the
network: an outage turned the build red for reasons unrelated to the code, and
a real regression was indistinguishable from weather. The comment those
fixtures carried -- "to speed this up, spoof the weather source" -- is what
this closes.

Rebuild with ``scripts/build_weather_fixture.py`` after anything that changes
which station a ZIP resolves to, or which hours are requested.
"""
import io
import lzma
import os

import numpy as np
import pandas as pd

FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "weather_fixture.npz.xz",
)


def _load():
    with lzma.open(FIXTURE_PATH) as handle:
        # np.load needs a seekable stream; the archive is a couple of MB
        with np.load(io.BytesIO(handle.read())) as archive:
            return {key: archive[key] for key in archive.files}


_RECORDED = _load()


def request_key(station, index):
    """Identifies one fetch: a station and the exact window asked for.

    Keyed by the request rather than by the station because ``from_csv`` asks
    for ``hourly_index_utc - utc_offset``, so the same station is asked for a
    differently-shifted window depending on the thermostat's offset.
    """
    return "{}@{}@{}".format(station, index[0].value, len(index))


def recorded_weather(station, index):
    """A ``weather_source`` for ``from_csv``, answered from the fixture.

    Raises rather than falling back to the network: a missing entry means the
    fixture is stale, and silently fetching would hide that while making the
    goldens depend on the network again.
    """
    if len(index) == 0:
        return pd.Series([], index=index, dtype=float)

    key = request_key(station, index)
    if key not in _RECORDED:
        raise KeyError(
            "no recorded weather for {}; the fixture is stale -- rebuild it "
            "with scripts/build_weather_fixture.py".format(key)
        )

    return pd.Series(_RECORDED[key], index=index)
