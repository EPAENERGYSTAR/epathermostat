"""The output schema is generated, and it agrees with what core.py emits.

Neither of these was checked before. The 197 output names were written out
by hand in five places, and metrics_to_csv builds its frame with
``columns=COLUMNS``, which silently discards keys that are not in the list --
so a metric added in core.py could vanish from the CSV with no error, and
three of them had.
"""
import re
from pathlib import Path

import pytest

from thermostat.core import (
    RESISTANCE_HEAT_USE_BIN_FIRST_TUPLE,
    RESISTANCE_HEAT_USE_BIN_SECOND_TUPLE,
)
from thermostat.schema import (
    COLUMNS,
    NON_RHU_COLUMNS,
    REAL_OR_INTEGER_VALUED_COLUMNS_ALL,
    REAL_OR_INTEGER_VALUED_COLUMNS_COOLING,
    REAL_OR_INTEGER_VALUED_COLUMNS_HEATING,
    RHU_COLUMNS,
    rhu_columns,
)

from .fixtures.thermostats import thermostat_type_1  # noqa: F401


def test_columns_have_no_duplicates():
    assert len(COLUMNS) == len(set(COLUMNS))


def test_columns_is_the_two_blocks():
    assert COLUMNS == list(NON_RHU_COLUMNS) + list(RHU_COLUMNS)
    assert len(COLUMNS) == 197


def test_rhu_columns_are_generated_from_the_bin_definitions():
    """4 duty-cycle variants x 2 bin sets x 2 rhu types, plus 3 thermostat-level."""
    bins = len(RESISTANCE_HEAT_USE_BIN_FIRST_TUPLE) + len(
        RESISTANCE_HEAT_USE_BIN_SECOND_TUPLE
    )

    assert len(rhu_columns()) == bins * 4 * 2 + 3


def test_stats_subsets_are_ordered_selections_of_columns():
    order = {name: i for i, name in enumerate(COLUMNS)}
    for subset in (
        REAL_OR_INTEGER_VALUED_COLUMNS_HEATING,
        REAL_OR_INTEGER_VALUED_COLUMNS_COOLING,
        REAL_OR_INTEGER_VALUED_COLUMNS_ALL,
    ):
        assert set(subset) <= set(COLUMNS)
        positions = [order[name] for name in subset]
        assert positions == sorted(positions)


def test_cooling_subset_has_no_resistance_heat_columns():
    assert not any(
        name.startswith("rhu") for name in REAL_OR_INTEGER_VALUED_COLUMNS_COOLING
    )


def test_every_emitted_metric_is_in_the_schema(thermostat_type_1):  # noqa: F811
    """The check that did not exist: nothing core.py emits is dropped.

    A type 1 thermostat exercises every branch -- heating, cooling and
    auxiliary/emergency -- so it emits the widest set of keys.
    """
    emitted = set()
    for record in thermostat_type_1.calculate_epa_field_savings_metrics():
        emitted |= set(record.keys())

    assert emitted - set(COLUMNS) == set()


def test_schema_names_every_emitted_metric(thermostat_type_1):  # noqa: F811
    """And the converse: no column is declared that nothing ever fills."""
    emitted = set()
    for record in thermostat_type_1.calculate_epa_field_savings_metrics():
        emitted |= set(record.keys())

    assert set(COLUMNS) - emitted == set()


def test_the_documented_columns_are_the_schema_columns():
    """docs/data_files.rst is the fifth hand-typed copy of the schema.

    It had drifted three ways: three ``rhu2_*_duty_cycle`` rows for columns
    the CSV never carried, two comfort-temperature rows still using the
    internal ``baseline10``/``baseline90`` variable names instead of the
    emitted ones, and two demand columns missing entirely.
    """
    docs = (
        Path(__file__).resolve().parent.parent / "docs" / "data_files.rst"
    ).read_text(encoding="utf-8")

    # The output table is the only one whose rows carry the leading-underscore
    # and rhu names, but other tables in the file document input columns and
    # summary statistics -- so check containment in that direction only.
    documented = set(re.findall(r":code:`([A-Za-z0-9_]+)`", docs))

    assert [name for name in COLUMNS if name not in documented] == []
