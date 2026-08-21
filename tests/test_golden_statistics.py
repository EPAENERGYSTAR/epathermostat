"""The statistics module, end to end, against a committed reference.

The metrics corpus (test_golden_corpus.py) pins what the thermostat module
produces. This pins what the statistics module makes of it -- the per-zone
means, the quantiles, and the weighted national averages that are the numbers
actually reported to EPA. Before this existed, the whole statistics path
could be restructured with nothing to say whether a regulated figure moved.

Regenerate deliberately, never casually::

    python scripts/regenerate_golden_statistics.py
"""
import gzip
import os

import numpy as np
import pandas as pd
import pytest

from thermostat.stats import (
    CLIMATE_ZONES,
    NATIONAL,
    REPORTED_ZONES,
    FILTER_NAMES,
    BASIC_FILTER_NAMES,
    SEASONS,
    compute_summary_statistics,
    summary_statistics_to_csv,
)

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CORPUS = os.path.join(DATA, "golden_metrics.csv")
RTOL = 1e-3


def corpus():
    metrics = pd.read_csv(CORPUS, dtype={"zipcode": str, "ct_identifier": str})
    # The in-memory path carries None, not NaN, for a ZIP with no climate zone.
    metrics["climate_zone"] = metrics["climate_zone"].where(
        metrics["climate_zone"].notna(), None)
    return metrics


def golden(advanced):
    name = "golden_statistics_advanced.csv.gz" if advanced else "golden_statistics.csv.gz"
    with gzip.open(os.path.join(DATA, name), "rt") as f:
        return pd.read_csv(f)


@pytest.fixture(scope="module", params=[False, True], ids=["basic", "advanced"])
def computed(request, tmp_path_factory):
    """Write and read back, so both sides of the comparison have made the
    same CSV round trip. summary_statistics_to_csv writes the frame
    transposed with the statistic names as the index, and reading that back
    is what a reviewer would actually look at."""
    stats = compute_summary_statistics(corpus(), advanced_filtering=request.param)
    path = tmp_path_factory.mktemp("stats") / "out.csv.gz"
    summary_statistics_to_csv(stats, str(path), "golden")
    with gzip.open(str(path), "rt") as f:
        return request.param, pd.read_csv(f)


def test_the_shape_is_the_reference_shape(computed):
    advanced, got = computed
    want = golden(advanced)
    assert list(got.columns) == list(want.columns)
    assert len(got) == len(want)


def test_every_statistic_matches_the_golden_reference(computed):
    advanced, got = computed
    want = golden(advanced)

    mismatched = []
    for column in want.columns:
        a, b = want[column], got[column]
        if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
            x, y = a.to_numpy(dtype=float), b.to_numpy(dtype=float)
            if not np.allclose(x, y, rtol=RTOL, equal_nan=True):
                worst = np.nanmax(np.abs(x - y) / np.maximum(np.abs(x), 1e-12))
                mismatched.append("{} (worst rel {:.3e})".format(column, worst))
        else:
            same = (a.isna() & b.isna()) | (a.astype(str) == b.astype(str))
            if not same.all():
                mismatched.append("{} ({} rows)".format(column, int((~same).sum())))

    assert not mismatched, "statistics moved in {} column(s): {}".format(
        len(mismatched), mismatched[:8])


def test_every_emitted_label_is_one_the_generator_produces(computed):
    """The dispatch and the national weighting share one label vocabulary.

    They used to be built separately -- 48 hand-typed calls on one side, a
    format string against hardcoded zone and filter lists on the other. A
    disagreement made `stats_dict.get()` return None and drop that zone out
    of the weighted national average with no error at all.

    Note this is a *vocabulary* test, not a presence test: a combination with
    no rows behind it is legitimately absent (the corpus has no Marine
    cooling), and the weighting is built to tolerate that.
    """
    advanced, got = computed
    active = FILTER_NAMES if advanced else BASIC_FILTER_NAMES

    producible = {
        "{}_{}_{}".format(zone.slug, filter_name, season)
        for zone in REPORTED_ZONES
        for filter_name in active
        for season in SEASONS
    }
    emitted = set(got.columns) - {"Unnamed: 0"}
    national = {label for label in emitted
                if label.startswith("national_weighted_mean_")}

    unexplained = emitted - producible - national
    assert not unexplained, sorted(unexplained)[:8]


def test_the_national_weighting_looks_up_labels_the_dispatch_can_produce():
    """Pure code check -- no data needed, so it catches a rename immediately."""
    for zone in CLIMATE_ZONES:
        assert zone in REPORTED_ZONES
        assert zone.slug != NATIONAL.slug
    assert set(BASIC_FILTER_NAMES) <= set(FILTER_NAMES)
    assert SEASONS == ("heating", "cooling")


def test_a_nan_climate_zone_does_not_raise():
    """Re-reading a written metrics.csv yields NaN, not None, for a ZIP with
    no climate zone. The Python-loop subsetting this replaced raised
    TypeError on that input."""
    metrics = corpus()
    metrics["climate_zone"] = np.nan
    stats = compute_summary_statistics(metrics)
    labels = {s["label"] for s in stats}
    # every zone frame is empty, but the national ("all") frames still report
    assert "all_no_filter_heating" in labels
    assert "very-cold_cold_no_filter_heating" not in labels
