"""Every record that goes in is accounted for on the way out.

A thermostat can vanish at two points -- import, and the metrics calculation
-- and before these tests both losses were reported only as log lines. That
made a run that quietly lost three percent of its fleet to dead weather
stations indistinguishable from a clean one.
"""
import os

import pandas as pd

from thermostat.importers import ImportedThermostats, from_csv
from thermostat.multiple import (
    multiple_thermostat_calculate_epa_field_savings_metrics)
from thermostat.run_summary import (
    RunSummary,
    INVALID_UTC_OFFSET,
    NO_QUALIFYING_CORE_DAYS,
    UNSUPPORTED_EQUIPMENT_TYPE,
)
from thermostat.util.testing import get_data_path

from .fixtures.weather import recorded_weather


def load(name):
    return from_csv(get_data_path(os.path.join("data", name)),
                    shuffle=False, weather_source=recorded_weather)


def test_a_clean_run_accounts_for_every_record():
    imported = load("metadata_type_1_single.csv")
    thermostats = list(imported)

    assert imported.summary.requested == 1
    assert imported.summary.delivered == 1
    assert imported.summary.drop_outs == []
    assert imported.summary.completeness == 1.0
    assert len(thermostats) == 1


def test_an_unreadable_utc_offset_is_reported_as_data():
    imported = load("metadata_type_1_single_utc_offset_bad.csv")
    assert list(imported) == []

    summary = imported.summary
    assert summary.requested == 1
    assert summary.delivered == 0
    assert len(summary.drop_outs) == 1

    drop_out = summary.drop_outs[0]
    assert drop_out.stage == "import"
    assert drop_out.reason == INVALID_UTC_OFFSET
    assert drop_out.thermostat_id == "8465829e-df0d-449e-97bf-96317c24dec3"
    # the ZIP travels with the drop-out, so a geographic pattern in the
    # losses is visible without joining back to the input
    assert drop_out.zipcode == "62223"
    assert "Invalid UTC offset" in drop_out.detail


def test_an_unsupported_equipment_type_is_reported_as_data(tmp_path):
    metadata = tmp_path / "metadata.csv"
    metadata.write_text(
        "thermostat_id,equipment_type,zipcode,utc_offset,interval_data_filename\n"
        "unsupported,0,62223,-7,does_not_exist.csv\n")

    imported = from_csv(str(metadata), shuffle=False,
                        weather_source=recorded_weather)
    assert list(imported) == []

    drop_out = imported.summary.drop_outs[0]
    assert drop_out.reason == UNSUPPORTED_EQUIPMENT_TYPE
    assert drop_out.stage == "import"


class NoCoreDays(object):
    """Stands in for a thermostat that imports cleanly and yields no rows.

    Module-level and trivially picklable because multiple.py dispatches
    through a process Pool. Its real-world shape is a thermostat matched to a
    station that reported nothing over the analysed years: the file is fine,
    the import succeeds, and then no day qualifies as a core day.
    """
    thermostat_id = "no-core-days"
    zipcode = "96128"
    station = "725845"

    def calculate_epa_field_savings_metrics(self):
        return []


def test_a_thermostat_with_no_core_days_is_reported_as_data():
    """The loss that import alone cannot see."""
    imported = ImportedThermostats([NoCoreDays()], RunSummary(requested=1))

    metrics = multiple_thermostat_calculate_epa_field_savings_metrics(imported)

    assert metrics == []
    summary = imported.summary
    assert summary.requested == 1
    assert summary.delivered == 0

    drop_out = summary.drop_outs[0]
    assert drop_out.stage == "metrics"
    assert drop_out.reason == NO_QUALIFYING_CORE_DAYS
    assert drop_out.zipcode == "96128"
    assert drop_out.station == "725845"


def test_a_plain_list_of_thermostats_still_works():
    """multiple.py carries no requirement that it be handed a summary."""
    assert multiple_thermostat_calculate_epa_field_savings_metrics(
        [NoCoreDays()]) == []


def test_the_summary_survives_a_run_that_loses_nothing(tmp_path):
    """An empty drop-out file still has a header, so it can be read blindly."""
    path = tmp_path / "run_summary.csv"
    RunSummary(requested=4).to_csv(str(path))

    written = pd.read_csv(str(path))
    assert list(written.columns) == [
        "thermostat_id", "zipcode", "station", "stage", "reason", "detail"]
    assert len(written) == 0


def test_the_reason_counts_separate_the_two_stages():
    summary = RunSummary(requested=3)
    summary.record("a", "import", INVALID_UTC_OFFSET, "bad", zipcode="00001")
    summary.record("b", "import", INVALID_UTC_OFFSET, "bad", zipcode="00002")
    summary.record("c", "metrics", NO_QUALIFYING_CORE_DAYS, "none")

    assert summary.by_reason() == {
        ("import", INVALID_UTC_OFFSET): 2,
        ("metrics", NO_QUALIFYING_CORE_DAYS): 1,
    }
    assert summary.dropped == 3
    assert summary.delivered == 0
    assert "thermostats requested: 3" in summary.describe()


def test_an_empty_run_does_not_divide_by_zero():
    summary = RunSummary(requested=0)
    assert pd.isna(summary.completeness)
    assert "nan" in summary.describe().lower()


def test_the_registry_vintage_is_reported_when_known():
    summary = RunSummary(requested=1, registry_vintage="2026-07-23")

    assert "eeweather registry:    2026-07-23" in summary.describe()


def test_a_missing_registry_vintage_is_simply_omitted():
    summary = RunSummary(requested=1)

    assert "eeweather registry" not in summary.describe()
