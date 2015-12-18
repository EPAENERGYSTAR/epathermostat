Quickstart
==========

First, check to make sure you are on the most recent version of the package.

.. code-block:: python

    >>> import thermostat; thermostat.get_version()
    '0.2.12'

Import the necessary methods and set a directory for finding and storing data.

.. code-block:: python

    import sys
    import os
    from os.path import expanduser
    from thermostat.importers import from_csv
    from thermostat.exporters import seasonal_metrics_to_csv

    data_dir = os.path.join(expanduser("~"), "Downloads")

After importing the package methods, load the example thermostat data.

See :ref:`thermostat-input` for more detailed file format information.

This line will take more than a few minutes, even if the weather cache
is enabled (more information below). This is because loading thermostat data
involves downloading hourly weather data from a remote source - in this case,
the NCDC.

There is fabricated data from 35 thermostats in the example file, including one
from each Building America, IECC, and CEC climate zone.

The data for this step can be downloaded :download:`here <./examples/examples.zip>`.

.. code-block:: python

    metadata_filename = os.path.join(data_dir, "examples/metadata.csv")
    thermostats = from_csv(metadata_filename, verbose=True)

To calculate savings metrics, iterate through thermostats and save the results.

.. code-block:: python

    seasonal_metrics = []
    for thermostat in thermostats:
        outputs = thermostat.calculate_epa_draft_rccs_field_savings_metrics()
        seasonal_metrics.extend(outputs)

    output_filename = os.path.join(data_dir, "thermostat_example_output.csv")
    metrics_df = seasonal_metrics_to_csv(seasonal_metrics, filepath)

The output CSV will be saved in your data directory and should very nearly
match the output CSV provided in the example data.

See :ref:`thermostat-output` for more detailed file format information.

**Note**: During the data loading step, you may see a warning that the weather
cache is disabled. You can safely ignore that warning, but if you wish to load
a large amount of data, it will load much more quickly upon repeated execution
if you use the weather cache.

To enable the weather cache, set the following environment variable to the
database of your choice (the example uses sqlite) by supplying a database url.

The weather cache stores weather locally so that it need only be downloaded
once.

To create a new sqlite database, specify a fully-qualified path to valid
location for new database file, and the database will be created for you in the
location you specify.

.. code-block:: bash

    $ export EEMETER_WEATHER_CACHE_DATABASE_URL=sqlite:////path/to/db.sqlite

You can also do this in python, but it must be done *before loading the package*.
For example:

.. code-block:: python

    os.environ["EEMETER_WEATHER_CACHE_DATABASE_URL"] = "sqlite:///{}".format(os.path.join(data_dir,"weather_cache.db"))

For more information, see the `eemeter <http://eemeter.readthedocs.org/en/latest/tutorial.html#caching-weather-data>`_
package.


Computing summary statistics
============================

Once you have obtained output for each individual thermostat in your dataset,
use the stats module to compute summary statistics, which are formatted for
submission to the EPA. The example below works with the output file from the
tutorial above and can be modified to use your data.

(Some additional imports.)

.. code-block:: python

    from thermostat.stats import compute_summary_statistics
    from thermostat.stats import compute_summary_statistics_by_zipcode
    from thermostat.stats import compute_summary_statistics_by_weather_station

    from thermostat.stats import summary_statistics_to_csv

Compute statistics across all thermostats and save to file. CSV will have 2 rows
and 584 columns (One row each for heating/cooling, one column for each
summary statistic).

.. code-block:: python

    # uses the metrics_df created in the Quickstart above.
    stats = compute_summary_statistics(metrics_df, "all_thermostats")
    stats.extend(compute_summary_statistics_by_zipcode(metrics_df))
    stats.extend(compute_summary_statistics_by_weather_station(metrics_df))

    stats_filepath = os.path.join(data_dir, "thermostat_example_stats.csv")
    stats_df = summary_statistics_to_csv(stats, stats_filepath)

If you need to run compute summary statistics for a custom grouping of
zipcodes, use the following and provide as a parameter the path to the
file describing the zipcode groupings. The name of the file can be anything,
but the format should be CSV as described in the API docs.

.. code-block:: python

    from thermostat.stats import compute_summary_statistics_by_zipcode_group

    stats.extend(compute_summary_statistics_by_zipcode_group(metrics_df,
             filepath="/path/to/grouping.csv"))

Please see the :ref:`thermostat-api` docs for additional information
on computing summary statistics.

Batch Scheduling
================

As some vendors have large numbers of thermostats, the following fuctions
assist in batch scheduling. For example, to create 10 batches, do the following:

(More imports.)

.. code-block:: python

    from thermostat.parallel import schedule_batches

Create a directory in which to save zipped batches, then save them there and
keep track of the filenames.

.. code-block:: python

    directory = os.path.join(data_dir, "thermostat_batches")
    batch_zipfile_names = schedule_batches(metadata_filename, n_batches=10,
            zip_files=True, batches_dir=directory)

More information
================

For additional information on package usage, please see the
:ref:`thermostat-api` documentation.


.. _thermostat-input:

Input data
==========

Input data should be specified using the following formats. One CSV should
specify thermostat summary metadata (e.g. unique identifiers, location, etc.).
Another CSV (or CSVs) should contain runtime information, linked to the
metadata csv by the :code:`thermostat_id` column.

Example files :download:`here <./examples/examples.zip>`.

Thermostat Summary Metadata CSV format
--------------------------------------

Columns
~~~~~~~

============================== ===========
Name                           Description
------------------------------ -----------
:code:`thermostat_id`          A uniquely identifying marker for the thermostat.
:code:`equipment_type`         The type of controlled HVAC heating and cooling equipment. [#]_
:code:`zipcode`                The ZIP code in which the thermostat is installed [#]_.
:code:`utc_offset`             The UTC offset of the times in the corresponding interval data CSV. (e.g. "-0700")
:code:`interval_data_filename` The filename of the interval data file corresponding to this thermostat. Should be specified relative to the location of the metadata file.
============================== ===========

 - Each row should correspond to a single thermostat.
 - Nulls should be specified by leaving the field blank.
 - All interval data for a particular thermostat should use
   the *same, single* UTC offset provided in the metadata file.

Thermostat Interval Data CSV format
--------------------------------------

Columns
~~~~~~~

============================ ===========
Name                         Description
---------------------------- -----------
:code:`thermostat_id`        Uniquely identifying marker for the thermostat.
:code:`date`                 Date of this set of readings. (YYYY-MM-DD).
:code:`cool_runtime`         Daily runtime of cooling equipment (seconds).
:code:`heat_runtime`         Daily runtime of heating equipment (seconds). [#]_
:code:`auxiliary_heat_HH`    Hourly runtime of auxiliary heat equipment (seconds; HH=00-23).
:code:`emergency_heat_HH`    Hourly runtime of emergency heat equipment (seconds; HH=00-23).
:code:`temp_in_HH`           Hourly average conditioned space temperature over the period of the reading (seconds; HH=00-23).
:code:`heating_setpoint_HH`  Hourly average thermostat setpoint temperature over the period of the reading (seconds; HH=00-23).
:code:`cooling_setpoint_HH`  Hourly average thermostat setpoint temperature over the period of the reading (seconds; HH=00-23).
============================ ===========

- Each row should correspond to a single hourly reading from a thermostat.
- Nulls should be specified by leaving the field blank.
- Zero values should be specified as 0, rather than as blank.
- If data is missing for a particular row of one column, data should still be
  provided for other columns in that row. For example, if runtime is missing
  for a particular date, please still provide indoor conditioned space
  temperature and setpoints for that date, if available.
- Runtimes should be specified in seconds and should be less than or equal to
  86400 s (1 day).
- Dates should be specified in the ISO 8601 date format (e.g. :code:`2015-05-19`).
- All temperatures should be specified in °F (to the nearest 0.5°F).
- If no distinction is made between heating and cooling setpoint, set both
  equal to the single setpoint.
- All runtime data MUST have the same UTC offset, as provided in the
  corresponding metadata file.
- If only a single setpoint is used for the thermostat, please copy the same
  setpoint data in to the heating and cooling setpoint columns.
- Outdoor temperature data need not be provided - it will be fetched
  automatically from NCDC using the `eemeter <http://eemeter.readthedocs.org/en/latest/>`_ package.

.. [#] Options for :code:`equipment_type`:

   - :code:`0`: Other – e.g. multi-zone multi-stage, modulating. Note: module will
     not output savings data for this type.
   - :code:`1`: Single stage heat pump with aux and/or emergency heat
   - :code:`2`: Single stage heat pump without aux or emergency heat
   - :code:`3`: Single stage non heat pump with single-stage central air conditioning
   - :code:`4`: Single stage non heat pump without central air conditioning
   - :code:`5`: Single stage central air conditioning without central heating

.. [#] Will be used for matching with a weather station that provides external
   dry-bulb temperature data. This temperature data will be used to determine
   the bounds of the heating and cooling season over which metrics will be
   computed. For more information on the mapping between ZIP codes and
   weather stations, please see the `eemeter.location <http://eemeter.readthedocs.org/en/latest/eemeter.html#module-eemeter.location>`_ package.

.. [#] Should not include runtime for auxiliary or emergency heat - this should
   be provided separately in the columns `emergency_heat_HH` and
   `auxiliary_heat_HH`.


.. _thermostat-output:

Output data
===========

======================================================= =========================================
Name                                                    Description
------------------------------------------------------- -----------------------------------------
:code:`ct_identifier`                                   Identifier for thermostat as provided in the metadata file.
:code:`equipment_type`                                  Equipment type of this thermostat (1, 2, 3, 4, or 5).
:code:`season_name`                                     Name of the season (e.g. "Heating 2012-2013").
:code:`station`                                         USAF identifier for station used to fetch hourly temperature data.
:code:`zipcode`                                         ZIP code provided in the metadata file.
:code:`n_days_both_heating_and_cooling`                 Number of days not included in this season's calculations due to presence of both heating and cooling.
:code:`n_days_insufficient_data`                        Number of days not included in this season's calculations due to missing data.
:code:`slope_deltaT`                                    Slope found during a linear regression of a deltaT demand measure against runtime.
:code:`intercept_deltaT`                                Intercept found during a linear regression of a deltaT demand measure against runtime.
:code:`alpha_est_dailyavgCDD`                           Estimate of alpha from the ratio estimation step of the dailyavgCDD demand measure.
:code:`alpha_est_dailyavgHDD`                           Estimate of alpha from the ratio estimation step of the dailyavgCDD demand measure.
:code:`alpha_est_hourlyavgCDD`                          Estimate of alpha from the ratio estimation step of the hourlyavgCDD demand measure.
:code:`alpha_est_hourlyavgHDD`                          Estimate of alpha from the ratio estimation step of the hourlyavgHDD demand measure.
:code:`mean_sq_err_dailyavgCDD`                         Mean squared error for the ratio estimation used during computation of the dailyavgCDD demand measure.
:code:`mean_sq_err_dailyavgHDD`                         Mean squared error for the ratio estimation used during computation of the dailyavgHDD demand measure.
:code:`mean_sq_err_hourlyavgCDD`                        Mean squared error for the ratio estimation used during computation of the hourlyavgCDD demand measure.
:code:`mean_sq_err_hourlyavgHDD`                        Mean squared error for the ratio estimation used during computation of the hourlyavgHDD demand measure.
:code:`mean_squared_error_deltaT`                       Mean squared error of the linear regression of the deltaT demand measure against runtime (see also slope_deltT).
:code:`deltaT_base_est_dailyavgCDD`                     DeltaT base for the dailyavgCDD demand measure.
:code:`deltaT_base_est_dailyavgHDD`                     DeltaT base for the dailyavgHDD demand measure.
:code:`deltaT_base_est_hourlyavgCDD`                    DeltaT base for the hourlyavgCDD demand measure.
:code:`deltaT_base_est_hourlyavgHDD`                    DeltaT base for the hourlyavgHDD demand measure.
:code:`baseline_daily_runtime_deltaT`                   Baseline daily runtime according to the deltaT demand measure.
:code:`baseline_daily_runtime_dailyavgCDD`              Baseline daily runtime according to the dailyavgCDD demand measure.
:code:`baseline_daily_runtime_dailyavgHDD`              Baseline daily runtime according to the dailyavgHDD demand measure.
:code:`baseline_daily_runtime_hourlyavgCDD`             Baseline daily runtime according to the hourlyavgCDD demand measure.
:code:`baseline_daily_runtime_hourlyavgHDD`             Baseline daily runtime according to the hourlyavgHDD demand measure.
:code:`baseline_seasonal_runtime_deltaT`                Baseline seasonal runtime according to the deltaT demand measure.
:code:`baseline_seasonal_runtime_dailyavgCDD`           Baseline seasonal runtime according to the dailyavgCDD demand measure.
:code:`baseline_seasonal_runtime_dailyavgHDD`           Baseline seasonal runtime according to the dailyavgHDD demand measure.
:code:`baseline_seasonal_runtime_hourlyavgCDD`          Baseline seasonal runtime according to the hourlyavgCDD demand measure.
:code:`baseline_seasonal_runtime_hourlyavgHDD`          Baseline seasonal runtime according to the hourlyavgHDD demand measure.
:code:`baseline_comfort_temperature`                    Baseline comfort temperature as determined by either the (10th percentile or 90th percentile of setpoints)
:code:`actual_daily_runtime`                            Observed average daily runtime for the season.
:code:`actual_seasonal_runtime`                         Observed total runtime for the season.
:code:`seasonal_avoided_runtime_deltaT`                 Seasonal avoided runtime according to the deltaT demand measure.
:code:`seasonal_avoided_runtime_dailyavgCDD`            Seasonal avoided runtime according to the dailyavgCDD demand measure (Cooling seasons only).
:code:`seasonal_avoided_runtime_dailyavgHDD`            Seasonal avoided runtime according to the dailyavgHDD demand measure (Heating seasons only).
:code:`seasonal_avoided_runtime_hourlyavgCDD`           Seasonal avoided runtime according to the hourlyavgCDD demand measure (Cooling seasons only).
:code:`seasonal_avoided_runtime_hourlyavgHDD`           Seasonal avoided runtime according to the hourlyavgHDD demand measure (Heating seasons only).
:code:`seasonal_savings_deltaT`                         Seasonal savings according to the deltaT demand measure.
:code:`seasonal_savings_dailyavgCDD`                    Seasonal savings according to the dailyavgCDD demand measure (Cooling seasons only).
:code:`seasonal_savings_dailyavgHDD`                    Seasonal savings according to the dailyavgHDD demand measure (Heating seasons only).
:code:`seasonal_savings_hourlyavgCDD`                   Seasonal savings according to the hourlyavgCDD demand measure (Cooling seasons only).
:code:`seasonal_savings_hourlyavgHDD`                   Seasonal savings according to the hourlyavgHDD demand measure (Heating seasons only).
:code:`rhu_00F_to_05F`                                  Resistance heat utilization for hourly temperature bin :math:`0 \leq T < 5`
:code:`rhu_05F_to_10F`                                  Resistance heat utilization for hourly temperature bin :math:`5 \leq T < 10`
:code:`rhu_10F_to_15F`                                  Resistance heat utilization for hourly temperature bin :math:`10 \leq T < 15`
:code:`rhu_15F_to_20F`                                  Resistance heat utilization for hourly temperature bin :math:`15 \leq T < 20`
:code:`rhu_20F_to_25F`                                  Resistance heat utilization for hourly temperature bin :math:`20 \leq T < 25`
:code:`rhu_25F_to_30F`                                  Resistance heat utilization for hourly temperature bin :math:`25 \leq T < 30`
:code:`rhu_30F_to_35F`                                  Resistance heat utilization for hourly temperature bin :math:`30 \leq T < 35`
:code:`rhu_35F_to_40F`                                  Resistance heat utilization for hourly temperature bin :math:`35 \leq T < 40`
:code:`rhu_40F_to_45F`                                  Resistance heat utilization for hourly temperature bin :math:`40 \leq T < 45`
:code:`rhu_45F_to_50F`                                  Resistance heat utilization for hourly temperature bin :math:`45 \leq T < 50`
:code:`rhu_50F_to_55F`                                  Resistance heat utilization for hourly temperature bin :math:`50 \leq T < 55`
:code:`rhu_55F_to_60F`                                  Resistance heat utilization for hourly temperature bin :math:`55 \leq T < 60`
======================================================= =========================================


