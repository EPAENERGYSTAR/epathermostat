"""The output schema, in one place.

Every metric name the package emits, and the population-statistics subsets
of it, were previously written out by hand five times: exporters.COLUMNS
(197), three lists in stats (181/32/184), a partial copy in the test suite,
and again in docs/data_files.rst. Nothing checked that any two agreed, and
metrics_to_csv builds its frame with ``columns=COLUMNS``, so a metric added
in core.py and missed here vanished from the CSV with no error.

147 of the 197 names are mechanical: the resistance-heat-utilization bins
crossed with the duty cycles. Those are generated from the bin definitions
in :mod:`thermostat.core`, so a change to the bins changes the schema. The
remaining names are genuine distinct metrics and are listed once.
"""
from thermostat.core import (
    RESISTANCE_HEAT_USE_BIN_FIRST_TUPLE,
    RESISTANCE_HEAT_USE_BIN_SECOND_TUPLE,
    Thermostat,
)


RHU_TYPES = ("rhu1", "rhu2")

# None is the bin's own rhu value; the rest are its duty cycles
DUTY_CYCLES = (None, "aux_duty_cycle", "emg_duty_cycle", "compressor_duty_cycle")

# thermostat-level duty cycles, emitted once rather than per bin
THERMOSTAT_DUTY_CYCLE_COLUMNS = (
    "rhu1_aux_duty_cycle",
    "rhu1_emg_duty_cycle",
    "rhu1_compressor_duty_cycle",
)

# rhu1_00F_to_05F_aux_duty_cycle has always sat at the end of the rhu1
# second-bin-set block rather than with its eleven siblings -- a
# copy-paste slip that stats.py faithfully reproduces. Column order is
# part of the CSV contract, so it is preserved here deliberately rather
# than silently corrected. Drop this when a column-order change is
# acceptable.
_LEGACY_MISPLACED_COLUMN = "rhu1_00F_to_05F_aux_duty_cycle"
_LEGACY_MISPLACED_AFTER = "rhu1_50F_to_60F"


def _bin_columns(rhu_type, bins, duty_cycle):
    return [
        Thermostat._format_rhu(
            None, rhu_type=rhu_type, low=low, high=high, duty_cycle=duty_cycle
        )
        for low, high in bins
    ]


def rhu_columns():
    """Every resistance-heat-utilization column, in output order."""
    columns = []
    for rhu_type in RHU_TYPES:
        if rhu_type == "rhu1":
            columns.extend(THERMOSTAT_DUTY_CYCLE_COLUMNS)
        for bins in (
            RESISTANCE_HEAT_USE_BIN_FIRST_TUPLE,
            RESISTANCE_HEAT_USE_BIN_SECOND_TUPLE,
        ):
            for duty_cycle in DUTY_CYCLES:
                columns.extend(_bin_columns(rhu_type, bins, duty_cycle))

    columns.remove(_LEGACY_MISPLACED_COLUMN)
    columns.insert(
        columns.index(_LEGACY_MISPLACED_AFTER) + 1, _LEGACY_MISPLACED_COLUMN
    )

    return columns


RHU_COLUMNS = tuple(rhu_columns())

# every non-rhu metric, in output order
NON_RHU_COLUMNS = (
    "sw_version",
    "ct_identifier",
    "equipment_type",
    "heating_or_cooling",
    "zipcode",
    "station",
    "climate_zone",
    "start_date",
    "end_date",
    "n_days_in_inputfile_date_range",
    "n_days_both_heating_and_cooling",
    "n_days_insufficient_data",
    "n_core_cooling_days",
    "n_core_heating_days",
    "baseline_percentile_core_cooling_comfort_temperature",
    "baseline_percentile_core_heating_comfort_temperature",
    "regional_average_baseline_cooling_comfort_temperature",
    "regional_average_baseline_heating_comfort_temperature",
    "percent_savings_baseline_percentile",
    "avoided_daily_mean_core_day_runtime_baseline_percentile",
    "avoided_total_core_day_runtime_baseline_percentile",
    "baseline_daily_mean_core_day_runtime_baseline_percentile",
    "baseline_total_core_day_runtime_baseline_percentile",
    "_daily_mean_core_day_demand_baseline_baseline_percentile",
    "percent_savings_baseline_regional",
    "avoided_daily_mean_core_day_runtime_baseline_regional",
    "avoided_total_core_day_runtime_baseline_regional",
    "baseline_daily_mean_core_day_runtime_baseline_regional",
    "baseline_total_core_day_runtime_baseline_regional",
    "_daily_mean_core_day_demand_baseline_baseline_regional",
    "mean_demand",
    "alpha",
    "tau",
    "mean_sq_err",
    "root_mean_sq_err",
    "cv_root_mean_sq_err",
    "mean_abs_err",
    "mean_abs_pct_err",
    "total_core_cooling_runtime",
    "total_core_heating_runtime",
    "total_auxiliary_heating_core_day_runtime",
    "total_emergency_heating_core_day_runtime",
    "daily_mean_core_cooling_runtime",
    "daily_mean_core_heating_runtime",
    "core_cooling_days_mean_indoor_temperature",
    "core_cooling_days_mean_outdoor_temperature",
    "core_heating_days_mean_indoor_temperature",
    "core_heating_days_mean_outdoor_temperature",
    "core_mean_indoor_temperature",
    "core_mean_outdoor_temperature",
)

# the CSV schema: metrics_to_csv writes exactly these, in this order
COLUMNS = list(NON_RHU_COLUMNS) + list(RHU_COLUMNS)

# population-statistics subsets, as non-rhu selections; each is emitted
# in COLUMNS order with the rhu block appended where it applies
_HEATING_NON_RHU = (
    "n_days_in_inputfile_date_range",
    "n_days_both_heating_and_cooling",
    "n_days_insufficient_data",
    "n_core_heating_days",
    "baseline_percentile_core_heating_comfort_temperature",
    "regional_average_baseline_heating_comfort_temperature",
    "percent_savings_baseline_percentile",
    "avoided_daily_mean_core_day_runtime_baseline_percentile",
    "avoided_total_core_day_runtime_baseline_percentile",
    "baseline_daily_mean_core_day_runtime_baseline_percentile",
    "baseline_total_core_day_runtime_baseline_percentile",
    "_daily_mean_core_day_demand_baseline_baseline_percentile",
    "percent_savings_baseline_regional",
    "avoided_daily_mean_core_day_runtime_baseline_regional",
    "avoided_total_core_day_runtime_baseline_regional",
    "baseline_daily_mean_core_day_runtime_baseline_regional",
    "baseline_total_core_day_runtime_baseline_regional",
    "_daily_mean_core_day_demand_baseline_baseline_regional",
    "mean_demand",
    "alpha",
    "tau",
    "mean_sq_err",
    "root_mean_sq_err",
    "cv_root_mean_sq_err",
    "mean_abs_err",
    "mean_abs_pct_err",
    "total_core_heating_runtime",
    "total_auxiliary_heating_core_day_runtime",
    "total_emergency_heating_core_day_runtime",
    "daily_mean_core_heating_runtime",
    "core_heating_days_mean_indoor_temperature",
    "core_heating_days_mean_outdoor_temperature",
    "core_mean_indoor_temperature",
    "core_mean_outdoor_temperature",
)

_COOLING_NON_RHU = (
    "n_days_in_inputfile_date_range",
    "n_days_both_heating_and_cooling",
    "n_days_insufficient_data",
    "n_core_cooling_days",
    "baseline_percentile_core_cooling_comfort_temperature",
    "regional_average_baseline_cooling_comfort_temperature",
    "percent_savings_baseline_percentile",
    "avoided_daily_mean_core_day_runtime_baseline_percentile",
    "avoided_total_core_day_runtime_baseline_percentile",
    "baseline_daily_mean_core_day_runtime_baseline_percentile",
    "baseline_total_core_day_runtime_baseline_percentile",
    "_daily_mean_core_day_demand_baseline_baseline_percentile",
    "percent_savings_baseline_regional",
    "avoided_daily_mean_core_day_runtime_baseline_regional",
    "avoided_total_core_day_runtime_baseline_regional",
    "baseline_daily_mean_core_day_runtime_baseline_regional",
    "baseline_total_core_day_runtime_baseline_regional",
    "_daily_mean_core_day_demand_baseline_baseline_regional",
    "mean_demand",
    "alpha",
    "tau",
    "mean_sq_err",
    "root_mean_sq_err",
    "cv_root_mean_sq_err",
    "mean_abs_err",
    "mean_abs_pct_err",
    "total_core_cooling_runtime",
    "daily_mean_core_cooling_runtime",
    "core_cooling_days_mean_indoor_temperature",
    "core_cooling_days_mean_outdoor_temperature",
    "core_mean_indoor_temperature",
    "core_mean_outdoor_temperature",
)

_ALL_NON_RHU = (
    "n_days_in_inputfile_date_range",
    "n_days_both_heating_and_cooling",
    "n_days_insufficient_data",
    "n_core_cooling_days",
    "n_core_heating_days",
    "baseline_percentile_core_cooling_comfort_temperature",
    "baseline_percentile_core_heating_comfort_temperature",
    "regional_average_baseline_cooling_comfort_temperature",
    "regional_average_baseline_heating_comfort_temperature",
    "percent_savings_baseline_percentile",
    "avoided_daily_mean_core_day_runtime_baseline_percentile",
    "avoided_total_core_day_runtime_baseline_percentile",
    "baseline_daily_mean_core_day_runtime_baseline_percentile",
    "baseline_total_core_day_runtime_baseline_percentile",
    "_daily_mean_core_day_demand_baseline_baseline_percentile",
    "percent_savings_baseline_regional",
    "avoided_daily_mean_core_day_runtime_baseline_regional",
    "avoided_total_core_day_runtime_baseline_regional",
    "baseline_daily_mean_core_day_runtime_baseline_regional",
    "baseline_total_core_day_runtime_baseline_regional",
    "_daily_mean_core_day_demand_baseline_baseline_regional",
    "mean_demand",
    "alpha",
    "tau",
    "mean_sq_err",
    "root_mean_sq_err",
    "cv_root_mean_sq_err",
    "mean_abs_err",
    "mean_abs_pct_err",
    "total_core_cooling_runtime",
    "total_core_heating_runtime",
    "total_auxiliary_heating_core_day_runtime",
    "total_emergency_heating_core_day_runtime",
    "daily_mean_core_cooling_runtime",
    "daily_mean_core_heating_runtime",
    "core_mean_indoor_temperature",
    "core_mean_outdoor_temperature",
)

REAL_OR_INTEGER_VALUED_COLUMNS_HEATING = (
    list(_HEATING_NON_RHU) + list(RHU_COLUMNS)
)
REAL_OR_INTEGER_VALUED_COLUMNS_COOLING = list(_COOLING_NON_RHU)
REAL_OR_INTEGER_VALUED_COLUMNS_ALL = list(_ALL_NON_RHU) + list(RHU_COLUMNS)
