#!/usr/bin/env python
"""Rewrite tests/data/golden_metrics.csv from the current code.

Run this only when a regulated output is *meant* to move -- a fixed bug, a
better station, a changed methodology. A diff in the golden corpus is never
routine, and regenerating it should land in its own commit that says which
cells moved and why.

It prints a summary of what changed so that commit message can be written
from measurement rather than from memory.

Only ever run this against the committed public test corpus. It reads
whatever tests/data/metadata.csv points at; run against a real partner
submission it would write real fleet data (UUID + ZIP + service dates per
household) into the golden file, which is committed to a public repo.
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from thermostat.importers import from_csv  # noqa: E402
from thermostat.exporters import metrics_to_csv  # noqa: E402
from thermostat.schema import COLUMNS  # noqa: E402
from tests.fixtures.weather import recorded_weather  # noqa: E402

DATA = os.path.join(REPO, "tests", "data")
GOLDEN = os.path.join(DATA, "golden_metrics.csv")
KEY = ["ct_identifier", "heating_or_cooling"]

# Reading the old file back through CSV loses the last bits of a float, so a
# no-op regeneration still shows ~1e-14 movement. Below this is repr noise,
# not a changed answer.
NOISE_FLOOR = 1e-9


def main():
    thermostats = list(from_csv(
        os.path.join(DATA, "metadata.csv"),
        verbose=False, shuffle=False, weather_source=recorded_weather,
    ))
    metrics = []
    for thermostat in thermostats:
        metrics.extend(thermostat.calculate_epa_field_savings_metrics())
    fresh = metrics_to_csv(metrics, os.devnull).sort_values(KEY).reset_index(drop=True)

    if os.path.exists(GOLDEN):
        old = pd.read_csv(GOLDEN, dtype={"zipcode": str, "ct_identifier": str})
        old = old.sort_values(KEY).reset_index(drop=True)
        _report(old, fresh)

    fresh.to_csv(GOLDEN, index=False)
    print("\nwrote {} ({} rows x {} columns)".format(
        os.path.relpath(GOLDEN, REPO), len(fresh), len(fresh.columns)))


def _report(old, fresh):
    old_keys = set(map(tuple, old[KEY].values))
    new_keys = set(map(tuple, fresh[KEY].values))
    if old_keys != new_keys:
        print("records added:  ", sorted(new_keys - old_keys))
        print("records removed:", sorted(old_keys - new_keys))
        return

    moved = []
    for column in COLUMNS:
        a, b = old[column], fresh[column]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            x, y = a.to_numpy(dtype=float), b.to_numpy(dtype=float)
            if not np.array_equal(np.isnan(x), np.isnan(y)):
                moved.append((np.inf, column, int((np.isnan(x) ^ np.isnan(y)).sum())))
                continue
            finite = ~np.isnan(x)
            if not finite.any():
                continue
            rel = np.abs(x[finite] - y[finite]) / np.maximum(np.abs(x[finite]), 1e-12)
            if rel.max() > NOISE_FLOOR:
                moved.append((rel.max(), column, int((rel > NOISE_FLOOR).sum())))

    moved.sort(reverse=True)
    if not moved:
        print("no column moved by more than {:g} -- regeneration is a no-op"
              .format(NOISE_FLOOR))
        return
    print("columns changed: {} of {}".format(len(moved), len(COLUMNS)))
    for worst, column, count in moved[:25]:
        print("  {:>12}  {:<58} {} row(s)".format(
            "NaN-flip" if not np.isfinite(worst) else "{:.3e}".format(worst),
            column, count))


if __name__ == "__main__":
    main()
