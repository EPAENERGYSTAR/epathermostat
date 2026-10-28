"""
smoke_test_2025.py
==================
End-to-end visual confirmation that live GHCNh weather is serving recent data.

This checked the GHCN-H *fallback* when outdoor temperatures came from ISD with
a second-source gap fill. That fallback is gone: weather now comes from a single
GHCNh source, so what this confirms is that the one source covers a recent year.

Usage (from epathermostat/ dir):
    python scripts/smoke_test_2025.py [zipcode]

Default zipcode: 62223 (Belleville IL - used in the standard test fixtures)

The script:
  1. Generates a synthetic 2025 interval CSV (indoor temps, setpoints, runtimes)
  2. Loads a Thermostat via the real importer, which fetches 2025 outdoor
     temperatures from NOAA
  3. Prints the first/last 30 hours of outdoor temperature data
  4. Prints a month-by-month coverage table
  5. Runs calculate_epa_field_savings_metrics() and prints key outputs
  6. Exits non-zero if overall coverage < 50%

Hours the station did not report are NaN; nothing fills them.
"""

import sys
import os
import logging
import warnings
import tempfile

import pandas as pd

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
logging.getLogger("thermostat").setLevel(logging.WARNING)


def generate_interval_csv(path):
    """Write a synthetic 2025 interval data CSV in epathermostat's expected format."""
    dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
    rows = []
    for d in dates:
        month = d.month
        heat_rt = 60.0 if month in (11, 12, 1, 2, 3) else 0.0
        cool_rt = 60.0 if month in (6, 7, 8, 9) else 0.0
        row = {
            "date": d.strftime("%Y-%m-%d"),
            "heat_runtime": heat_rt,
            "cool_runtime": cool_rt,
        }
        for h in range(24):
            hh = "{:02d}".format(h)
            row["temp_in_{}".format(hh)] = 70.0
            row["heating_setpoint_{}".format(hh)] = 68.0
            row["cooling_setpoint_{}".format(hh)] = 76.0
            row["auxiliary_heat_runtime_{}".format(hh)] = 0.0
            row["emergency_heat_runtime_{}".format(hh)] = 0.0
        rows.append(row)
    pd.DataFrame(rows).to_csv(path, index=False)


def load_thermostat(zipcode, csv_path, utc_offset="-6"):
    """Load a Thermostat using the real get_single_thermostat() importer path."""
    from thermostat.importers import get_single_thermostat
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return get_single_thermostat(
            thermostat_id="smoke-test-2025",
            equipment_type=1,
            zipcode=zipcode,
            utc_offset=utc_offset,
            interval_data_filename=str(csv_path),
        )


def print_sample_hours(temps, n=30):
    print("First {} hours:".format(n))
    print("{:<30} {:>10}".format("Timestamp", "Temp (F)"))
    print("-" * 42)
    for ts, val in temps.head(n).items():
        print("{:<30} {:>10}".format(str(ts), "{:.1f}".format(val) if pd.notna(val) else "NaN"))
    print()
    print("Last {} hours:".format(n))
    print("{:<30} {:>10}".format("Timestamp", "Temp (F)"))
    print("-" * 42)
    for ts, val in temps.tail(n).items():
        print("{:<30} {:>10}".format(str(ts), "{:.1f}".format(val) if pd.notna(val) else "NaN"))
    print()


def print_coverage_table(temps):
    print("{:<10} {:>10} {:>10} {:>10}".format("Month", "Non-NaN", "Total", "Coverage"))
    print("-" * 44)
    for month in range(1, 13):
        mask = temps.index.month == month
        total = mask.sum()
        non_nan = int(temps[mask].notna().sum())
        pct = non_nan / total * 100 if total else 0
        bar = "#" * int(pct / 5)
        print("{:<10} {:>10} {:>10}   {:>5.1f}%  {}".format(
            "2025-{:02d}".format(month), non_nan, total, pct, bar))
    print()
    total_all = len(temps)
    non_nan_all = int(temps.notna().sum())
    print("TOTAL:  {}/{} non-NaN hours ({:.1f}%)".format(
        non_nan_all, total_all, non_nan_all / total_all * 100))
    return non_nan_all / total_all


def run_pipeline(thermostat):
    print("\nRunning calculate_epa_field_savings_metrics() ...")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        results = thermostat.calculate_epa_field_savings_metrics()

    if not results:
        print("  No results returned (insufficient core days in synthetic data)")
        return

    print("\n  Pipeline output ({} result set(s)):".format(len(results)))
    for i, r in enumerate(results[:2]):
        print("\n  Result set {}:".format(i + 1))
        for key, val in sorted(r.items()):
            if isinstance(val, float):
                print("    {:50s} {:.4f}".format(key, val))
            else:
                print("    {:50s} {}".format(key, val))


def main():
    zipcode = sys.argv[1] if len(sys.argv) > 1 else "62223"
    print("=" * 60)
    print("Live GHCNh smoke test — 2025 data for zipcode {}".format(zipcode))
    print("=" * 60)
    print()

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    csv_path = tmp.name
    tmp.close()

    try:
        generate_interval_csv(csv_path)

        print("Loading thermostat via get_single_thermostat() importer (zipcode={}, utc_offset=-6) ...".format(zipcode))
        print("(single GHCNh source; unreported hours stay NaN)")
        print()

        try:
            thermostat = load_thermostat(zipcode, csv_path)
        except Exception as e:
            print("Import error: {}".format(e))
            import traceback
            traceback.print_exc()
            sys.exit(1)

        print("Station: {}".format(thermostat.station))
        print()

        temps_f = thermostat.temperature_out
        print_sample_hours(temps_f)
        coverage = print_coverage_table(temps_f)

        print()
        try:
            run_pipeline(thermostat)
        except Exception as e:
            print("Pipeline error: {}".format(e))
            import traceback
            traceback.print_exc()

        print()
        if coverage < 0.50:
            print("FAIL: coverage {:.1%} is below the 50% threshold.".format(coverage))
            sys.exit(1)
        else:
            print("PASS: {:.1%} of 2025 hourly temperatures are non-NaN.".format(coverage))

    finally:
        os.unlink(csv_path)


if __name__ == "__main__":
    main()
