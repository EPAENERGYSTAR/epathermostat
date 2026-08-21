#!/usr/bin/env python
"""Rewrite tests/data/golden_statistics*.csv from the current code.

Same contract as regenerate_golden_corpus.py: a diff here means a regulated
statistic moved, which is never routine. Run deliberately, and land the
result in its own commit that says which cells moved and why.
"""
import os
import sys

import numpy as np
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from thermostat.stats import compute_summary_statistics  # noqa: E402
from thermostat.stats import summary_statistics_to_csv  # noqa: E402

DATA = os.path.join(REPO, "tests", "data")
CORPUS = os.path.join(DATA, "golden_metrics.csv")
NOISE_FLOOR = 1e-9
PRODUCT_ID = "golden"


def build(advanced):
    metrics = pd.read_csv(CORPUS, dtype={"zipcode": str, "ct_identifier": str})
    # The in-memory path carries None, not NaN, for a ZIP with no climate
    # zone. Match it so this file is comparable across versions.
    metrics["climate_zone"] = metrics["climate_zone"].where(
        metrics["climate_zone"].notna(), None)
    stats = compute_summary_statistics(metrics, advanced_filtering=advanced)
    name = "golden_statistics_advanced.csv.gz" if advanced else "golden_statistics.csv.gz"
    path = os.path.join(DATA, name)
    # gzip: the pair is 4.5 MB as text and compresses about 12x.
    # pandas reads and writes .csv.gz transparently.
    summary_statistics_to_csv(stats, path, PRODUCT_ID)
    return path


def report(path, before):
    if before is None:
        print("  (new file)")
        return
    after = pd.read_csv(path)
    if list(before.columns) != list(after.columns):
        print("  COLUMNS CHANGED: {} -> {}".format(
            len(before.columns), len(after.columns)))
        print("   added:   ", sorted(set(after.columns) - set(before.columns))[:8])
        print("   removed: ", sorted(set(before.columns) - set(after.columns))[:8])
        return
    if len(before) != len(after):
        print("  ROWS CHANGED: {} -> {}".format(len(before), len(after)))
        return
    moved = 0
    worst = (0.0, None)
    for column in before.columns:
        a, b = before[column], after[column]
        if not (pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b)):
            if not (a.astype(str) == b.astype(str)).all():
                print("  text column changed:", column)
            continue
        x, y = a.to_numpy(dtype=float), b.to_numpy(dtype=float)
        if not np.array_equal(np.isnan(x), np.isnan(y)):
            print("  NaN pattern changed:", column)
            moved += 1
            continue
        finite = ~np.isnan(x)
        if not finite.any():
            continue
        rel = np.abs(x[finite] - y[finite]) / np.maximum(np.abs(x[finite]), 1e-12)
        if rel.max() > NOISE_FLOOR:
            moved += 1
            if rel.max() > worst[0]:
                worst = (rel.max(), column)
    if moved:
        print("  {} of {} columns moved; worst {:.3e} ({})".format(
            moved, len(before.columns), worst[0], worst[1]))
    else:
        print("  no column moved by more than {:g} -- regeneration is a no-op"
              .format(NOISE_FLOOR))


def main():
    for advanced in (False, True):
        name = "golden_statistics_advanced.csv.gz" if advanced else "golden_statistics.csv.gz"
        path = os.path.join(DATA, name)
        before = pd.read_csv(path) if os.path.exists(path) else None
        print("{}:".format(name))
        build(advanced)
        report(path, before)
        after = pd.read_csv(path)
        print("  wrote {} rows x {} columns\n".format(len(after), len(after.columns)))


if __name__ == "__main__":
    main()
