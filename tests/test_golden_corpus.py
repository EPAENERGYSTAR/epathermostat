"""The whole corpus, end to end, against a committed reference.

This is the check the project did not have: nothing ran the full 35-thermostat
corpus and compared the result to a stored answer, so a change that moved a
regulated number was only caught if it happened to move one of the handful of
values the unit tests assert on.

It is the oracle the 1.8.0/1.8.1 restructure was verified against by hand --
every commit was checked for a byte-identical corpus run. Committing it makes
CI do that instead of a person.

Regenerate deliberately, never casually::

    python scripts/regenerate_golden_corpus.py

A diff here means a regulated output moved. That is sometimes correct -- a
fixed bug, a better station -- but it is never routine, and the regeneration
should land in its own commit saying which cells moved and why.
"""
import os

import numpy as np
import pandas as pd
import pytest

from thermostat.importers import from_csv
from thermostat.exporters import metrics_to_csv
from thermostat.schema import COLUMNS

from .fixtures.weather import recorded_weather

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
GOLDEN = os.path.join(DATA, "golden_metrics.csv")

# The regulated tolerance. The suite's own golden assertions use the same
# figure, and the restructure was held to byte-identical, which is stricter.
RTOL = 1e-3

KEY = ["ct_identifier", "heating_or_cooling"]


@pytest.fixture(scope="module")
def corpus_metrics():
    thermostats = list(from_csv(
        os.path.join(DATA, "metadata.csv"),
        verbose=False, shuffle=False, weather_source=recorded_weather,
    ))
    metrics = []
    for thermostat in thermostats:
        metrics.extend(thermostat.calculate_epa_field_savings_metrics())

    frame = metrics_to_csv(metrics, os.devnull)

    return frame.sort_values(KEY).reset_index(drop=True)


@pytest.fixture(scope="module")
def golden():
    # zipcode is a string with meaningful leading zeros; left to pandas it
    # reads back as an integer and every ZIP east of Ohio loses a digit
    return (
        pd.read_csv(GOLDEN, dtype={"zipcode": str, "ct_identifier": str})
        .sort_values(KEY)
        .reset_index(drop=True)
    )


def test_the_corpus_produces_every_expected_record(corpus_metrics, golden):
    """Same thermostats, same seasons -- nothing silently dropped.

    A thermostat whose ZIP stops resolving, or whose station stops returning
    data, vanishes from the output with only a log line. This is what notices.
    """
    produced = set(map(tuple, corpus_metrics[KEY].values))
    expected = set(map(tuple, golden[KEY].values))

    assert produced == expected


def test_the_column_order_is_the_schema(corpus_metrics, golden):
    """Order, not just membership: the CSV is the deliverable."""
    assert list(corpus_metrics.columns) == COLUMNS
    assert list(golden.columns) == COLUMNS


def test_every_value_matches_the_golden_corpus(corpus_metrics, golden):
    """The regulated numbers, all 56 x 197 of them."""
    moved = []
    for column in COLUMNS:
        want, got = golden[column], corpus_metrics[column]
        if pd.api.types.is_numeric_dtype(want) and pd.api.types.is_numeric_dtype(got):
            a, b = want.to_numpy(dtype=float), got.to_numpy(dtype=float)
            if not np.array_equal(np.isnan(a), np.isnan(b)):
                moved.append("{}: NaN pattern differs".format(column))
                continue
            finite = ~np.isnan(a)
            if finite.any() and not np.allclose(a[finite], b[finite], rtol=RTOL,
                                                atol=0, equal_nan=True):
                worst = np.nanmax(
                    np.abs(a[finite] - b[finite])
                    / np.maximum(np.abs(a[finite]), 1e-12))
                moved.append("{}: max relative change {:.3e}".format(column, worst))
        else:
            # NaN is not equal to itself, and a missing climate zone is a
            # legitimate value here rather than a mismatch
            same = (want.isna() & got.isna()) | (want.astype(str) == got.astype(str))
            if not same.all():
                moved.append("{}: text differs".format(column))

    assert moved == [], (
        "{} columns moved against the golden corpus:\n  {}".format(
            len(moved), "\n  ".join(moved[:20]))
    )
