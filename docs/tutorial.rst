Quickstart
==========

Installation
------------

To install the thermostat package for the first time, we highly recommend that
you create a virtual environment or a conda environment in which to install it.
You may choose to skip this step, but do so at the risk of corrupting your
existing python environment. Isolating your python environment will also
make it easier to debug:

.. code-block:: bash

    # if using virtualenvwrapper (see https://virtualenvwrapper.readthedocs.org/en/latest/install.html)
    $ mkvirtualenv thermostat
    (thermostat)$ pip install thermostat

    # if using conda (see note below - conda is distributed with Anaconda)
    $ conda create --yes --name thermostat pandas
    (thermostat)$ pip install thermostat

If you already have an environment, use the following:

.. code-block:: bash

    # if using virtualenvwrapper
    $ workon thermostat
    (thermostat)$

    # if using conda
    $ source activate thermostat
    (thermostat)$

To deactivate the environment when you've finished, use the following:

.. code-block:: bash

    # if using virtualenvwrapper
    (thermostat)$ deactivate
    $

    # if using conda
    (thermostat)$ source deactivate
    $

Check to make sure you are on the most recent version of the package.

.. code-block:: python

    >>> import thermostat; thermostat.get_version()
    '0.3.2'

If you are not on the correct version, you should upgrade:

.. code-block:: bash

    $ pip install thermostat --upgrade

The command above will update dependencies as well. If you wish to skip this,
use the :code:`--no-deps` flag:

.. code-block:: bash

    $ pip install thermostat --upgrade --no-deps

.. note::

    If you experience issues installing python packages with C extensions, such
    as `numpy` or `scipy`, we recommend installing and using the free
    `Anaconda <https://www.continuum.io/downloads>`_ Python distribution by
    Continuum Analytics. It contains many of the numeric and scientific
    packages used by this package and has installers for Python 2.7 and 3.5 for
    Windows, Mac OS X and Linux.

Once you have verified a correct installation, import the necessary methods
and set a directory for finding and storing data.

Computing individual thermostat-season metrics
----------------------------------------------

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
    metrics_df = seasonal_metrics_to_csv(seasonal_metrics, output_filename)

The output CSV will be saved in your data directory and should very nearly
match the output CSV provided in the example data.

See :ref:`thermostat-output` for more detailed file format information.

.. note::

    The thermostat package depends on the eemeter package for weather data
    fetching. The eemeter package automatically creates its own cache directory
    in which it keeps cached versions of weather source data. This speeds up
    the (generally IO-bound) NOAA weather fetching routine on subsequent
    internal calls to fetch the same weather data (i.e. getting outdoor
    temperature data for thermostats that map to the same weather station).

    The weather cache is automtically created at :code:`~/.eemeter/cache/`.

    If you wish to change the location of this cache, you can set the
    environment variable as shown below to the path of the existing directory
    that you would like to set as the eemeter weather cache:

    .. code-block:: bash

        $ export EEMETER_WEATHER_CACHE_DIRECTORY=/path/to/directory

    If you are using virtualenvwrapper, you may find it convenient to put this
    in your postactivate hook script:

    .. code-block:: bash

        $ echo "export EEMETER_WEATHER_CACHE_DIRECTORY=/path/to/directory" >> $WORKON_HOME/thermostat/bin/postactivate

    You can also do this in python, but it must be done
    *before loading the package*.  For example:

    .. code-block:: python

        os.environ["EEMETER_WEATHER_CACHE_DIRECTORY"] = "/path/to/directory"

    For more information, see the `eemeter <http://eemeter.readthedocs.org/en/latest/tutorial.html#caching-weather-data>`_
    package.

.. note::

    US Census Bureau ZIP Code Tabulation Areas (ZCTA) are used to USPS ZIP
    codes to outdoor temperature data. If the automatic mapping is unsuccessful
    for one or more of the ZIP codes in your dataset, the reason is likely to
    be the discrepancy between "true" USPS ZIP codes and the US Census Bureau
    ZCTAs. "True" ZIP codes are not used because they do not always map well to
    location (e.g. P.O. boxes). You may need to first map ZIP codes to ZCTAs,
    or these thermostats will be skipped. (There are ~32,000 ZCTAs and ~42000
    ZIP codes).


Computing summary statistics
----------------------------

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

The Building America Climate Zone to ZIP code grouping used in this example
can be downloaded
:download:`here <./resources/Building America Climate Zone to Zipcode Database_Rev1_2015.12.18.csv>`.
The file maps ZIP codes to Climate Zones. This example computes summary
statistics for each climate zone using the provided mapping.

Should you wish to calculate a national average using a weighted climate zone
mapping as well, you should use the following weightings, also available for
download :download:`here <./resources/NationalAverageClimateZoneWeightings.json>`

.. code-block:: python

    from thermostat.stats import compute_summary_statistics_by_zipcode_group

    zipcode_mapping_path = os.path.join(data_dir,
            "Building America Climate Zone to Zipcode Database_Rev1_2015.12.18.csv")

    national_weighting_path = os.path.join(data_dir,
            "NationalAverageClimateZoneWeightings.json")

    summary_statistics = compute_summary_statistics_by_zipcode_group(metrics_df,
             filepath=zipcode_mapping_path, weights=national_weighting_path)

    stats.extend(summary_statistics)

Please see the :ref:`thermostat-api` docs for additional information
on computing summary statistics.

Batch Scheduling
----------------

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
----------------

For additional information on package usage, please see the
:ref:`thermostat-api` documentation.


.. _thermostat-input:

Input data
----------

Input data should be specified using the following formats. One CSV should
specify thermostat summary metadata (e.g. unique identifiers, location, etc.).
Another CSV (or CSVs) should contain runtime information, linked to the
metadata csv by the :code:`thermostat_id` column.

Example files :download:`here <./examples/examples.zip>`.

Thermostat Summary Metadata CSV format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Columns
```````

============================== ================ ===== ===========
Name                           Data Format      Units Description
------------------------------ ---------------- ----- -----------
:code:`thermostat_id`          string           N/A   A uniquely identifying marker for the thermostat.
:code:`equipment_type`         enum, {0..5}     N/A   The type of controlled HVAC heating and cooling equipment. [#]_
:code:`zipcode`                string, 5 digits N/A   The ZIP code in which the thermostat is installed [#]_.
:code:`utc_offset`             string           N/A   The UTC offset of the times in the corresponding interval data CSV. (e.g. "-0700")
:code:`interval_data_filename` string           N/A   The filename of the interval data file corresponding to this thermostat. Should be specified relative to the location of the metadata file.
============================== ================ ===== ===========

 - Each row should correspond to a single thermostat.
 - Nulls should be specified by leaving the field blank.
 - All interval data for a particular thermostat should use
   the *same, single* UTC offset provided in the metadata file.

Thermostat Interval Data CSV format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Columns
```````

============================ ======================= ======= ===========
Name                         Data Format             Units    Description
---------------------------- ----------------------- ------- -----------
:code:`thermostat_id`        string                  N/A     Uniquely identifying marker for the thermostat.
:code:`date`                 YYYY-MM-DD (ISO-8601)   N/A     Date of this set of readings.
:code:`cool_runtime`         decimal or integer      minutes Daily runtime of cooling equipment.
:code:`heat_runtime`         decimal or integer      minutes Daily runtime of heating equipment. [#]_
:code:`auxiliary_heat_HH`    decimal or integer      minutes Hourly runtime of auxiliary heat equipment (HH=00-23).
:code:`emergency_heat_HH`    decimal or integer      minutes Hourly runtime of emergency heat equipment (HH=00-23).
:code:`temp_in_HH`           decimal, to nearest 0.5 °F      Hourly average conditioned space temperature over the period of the reading (HH=00-23).
:code:`heating_setpoint_HH`  decimal, to nearest 0.5 °F      Hourly average thermostat setpoint temperature over the period of the reading (HH=00-23).
:code:`cooling_setpoint_HH`  decimal, to nearest 0.5 °F      Hourly average thermostat setpoint temperature over the period of the reading (HH=00-23).
============================ ======================= ======= ===========

- Each row should correspond to a single daily reading from a thermostat.
- Nulls should be specified by leaving the field blank.
- Zero values should be specified as 0, rather than as blank.
- If data is missing for a particular row of one column, data should still be
  provided for other columns in that row. For example, if runtime is missing
  for a particular date, please still provide indoor conditioned space
  temperature and setpoints for that date, if available.
- Runtimes should be less than or equal to 1440 min (1 day).
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
-----------

Individual thermostat-season
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following columns are a intermediate output generated for each thermostat-season.

Columns
```````

======================================================= ================ ======================== ===========
Name                                                    Data Format      Units                    Description
------------------------------------------------------- ---------------- ------------------------ -----------
:code:`ct_identifier`                                   string           N/A                      Identifier for thermostat as provided in the metadata file.
:code:`equipment_type`                                  enum, {0..5}     N/A                      Equipment type of this thermostat (1, 2, 3, 4, or 5).
:code:`season_name`                                     string           N/A                      Name of the season (e.g. "Heating 2012-2013").
:code:`station`                                         string, USAF ID  N/A                      USAF identifier for station used to fetch hourly temperature data.
:code:`zipcode`                                         string, 5 digits N/A                      ZIP code provided in the metadata file.
:code:`n_days_both_heating_and_cooling`                 integer          # days                   Number of days not included in this season's calculations due to presence of both heating and cooling.
:code:`n_days_insufficient_data`                        integer          # days                   Number of days not included in this season's calculations due to missing data.
:code:`n_days_in_season`                                integer          # days                   Number of days meeting criteria for season inclusion.
:code:`n_days_in_season_range`                          integer          # days                   Number of potential days in the season range (e.g. Jan 1 to Dec 31 = 365)
:code:`alpha_deltaT`                                    decimal          minutes/Δ°F              Slope found during a linear regression of a deltaT demand measure against runtime.
:code:`tau_deltaT`                                      decimal          minutes                  Intercept found during a linear regression of a deltaT demand measure against runtime.
:code:`alpha_dailyavgCDD`                               decimal          minutes/Δ°F              Estimate of alpha from the ratio estimation step of the dailyavgCDD demand measure.
:code:`alpha_dailyavgHDD`                               decimal          minutes/Δ°F              Estimate of alpha from the ratio estimation step of the dailyavgCDD demand measure.
:code:`alpha_hourlyavgCDD`                              decimal          minutes/Δ°F              Estimate of alpha from the ratio estimation step of the hourlyavgCDD demand measure.
:code:`alpha_hourlyavgHDD`                              decimal          minutes/Δ°F              Estimate of alpha from the ratio estimation step of the hourlyavgHDD demand measure.
:code:`mean_sq_err_dailyavgCDD`                         decimal          :math:`\text{minutes}^2` Mean squared error for the ratio estimation used during computation of the dailyavgCDD demand measure.
:code:`mean_sq_err_dailyavgHDD`                         decimal          :math:`\text{minutes}^2` Mean squared error for the ratio estimation used during computation of the dailyavgHDD demand measure.
:code:`mean_sq_err_hourlyavgCDD`                        decimal          :math:`\text{minutes}^2` Mean squared error for the ratio estimation used during computation of the hourlyavgCDD demand measure.
:code:`mean_sq_err_hourlyavgHDD`                        decimal          :math:`\text{minutes}^2` Mean squared error for the ratio estimation used during computation of the hourlyavgHDD demand measure.
:code:`mean_squared_error_deltaT`                       decimal          :math:`\text{minutes}^2` Mean squared error of the linear regression of the deltaT demand measure against runtime (see also slope_deltT).
:code:`tau_dailyavgCDD`                                 decimal          °F                       DeltaT base for the dailyavgCDD demand measure.
:code:`tau_dailyavgHDD`                                 decimal          °F                       DeltaT base for the dailyavgHDD demand measure.
:code:`tau_hourlyavgCDD`                                decimal          °F                       DeltaT base for the hourlyavgCDD demand measure.
:code:`tau_hourlyavgHDD`                                decimal          °F                       DeltaT base for the hourlyavgHDD demand measure.
:code:`baseline_daily_runtime_deltaT`                   decimal          minutes/day              Baseline daily runtime according to the deltaT demand measure.
:code:`baseline_daily_runtime_dailyavgCDD`              decimal          minutes/day              Baseline daily runtime according to the dailyavgCDD demand measure.
:code:`baseline_daily_runtime_dailyavgHDD`              decimal          minutes/day              Baseline daily runtime according to the dailyavgHDD demand measure.
:code:`baseline_daily_runtime_hourlyavgCDD`             decimal          minutes/day              Baseline daily runtime according to the hourlyavgCDD demand measure.
:code:`baseline_daily_runtime_hourlyavgHDD`             decimal          minutes/day              Baseline daily runtime according to the hourlyavgHDD demand measure.
:code:`baseline_seasonal_runtime_deltaT`                decimal          minutes/season           Baseline seasonal runtime according to the deltaT demand measure.
:code:`baseline_seasonal_runtime_dailyavgCDD`           decimal          minutes/season           Baseline seasonal runtime according to the dailyavgCDD demand measure.
:code:`baseline_seasonal_runtime_dailyavgHDD`           decimal          minutes/season           Baseline seasonal runtime according to the dailyavgHDD demand measure.
:code:`baseline_seasonal_runtime_hourlyavgCDD`          decimal          minutes/season           Baseline seasonal runtime according to the hourlyavgCDD demand measure.
:code:`baseline_seasonal_runtime_hourlyavgHDD`          decimal          minutes/season           Baseline seasonal runtime according to the hourlyavgHDD demand measure.
:code:`baseline_comfort_temperature`                    decimal          °F                       Baseline comfort temperature as determined by either the (10th percentile or 90th percentile of setpoints)
:code:`actual_daily_runtime`                            decimal          minutes/day              Observed average daily runtime for the season.
:code:`actual_seasonal_runtime`                         decimal          minutes/season           Observed total runtime for the season.
:code:`seasonal_avoided_runtime_deltaT`                 decimal          minutes/season           Seasonal avoided runtime according to the deltaT demand measure.
:code:`seasonal_avoided_runtime_dailyavgCDD`            decimal          minutes/season           Seasonal avoided runtime according to the dailyavgCDD demand measure (Cooling seasons only).
:code:`seasonal_avoided_runtime_dailyavgHDD`            decimal          minutes/season           Seasonal avoided runtime according to the dailyavgHDD demand measure (Heating seasons only).
:code:`seasonal_avoided_runtime_hourlyavgCDD`           decimal          minutes/season           Seasonal avoided runtime according to the hourlyavgCDD demand measure (Cooling seasons only).
:code:`seasonal_avoided_runtime_hourlyavgHDD`           decimal          minutes/season           Seasonal avoided runtime according to the hourlyavgHDD demand measure (Heating seasons only).
:code:`percent_savings_deltaT`                          decimal          0.0=0%, 1.0=100%         Seasonal savings according to the deltaT demand measure.
:code:`percent_savings_dailyavgCDD`                     decimal          0.0=0%, 1.0=100%         Seasonal savings according to the dailyavgCDD demand measure (Cooling seasons only).
:code:`percent_savings_dailyavgHDD`                     decimal          0.0=0%, 1.0=100%         Seasonal savings according to the dailyavgHDD demand measure (Heating seasons only).
:code:`percent_savings_hourlyavgCDD`                    decimal          0.0=0%, 1.0=100%         Seasonal savings according to the hourlyavgCDD demand measure (Cooling seasons only).
:code:`percent_savings_hourlyavgHDD`                    decimal          0.0=0%, 1.0=100%         Seasonal savings according to the hourlyavgHDD demand measure (Heating seasons only).
:code:`rhu_00F_to_05F`                                  decmial          0.0=0%, 1.0=100%         Resistance heat utilization for hourly temperature bin :math:`0 \leq T_{out} < 5`
:code:`rhu_05F_to_10F`                                  decmial          0.0=0%, 1.0=100%         Resistance heat utilization for hourly temperature bin :math:`5 \leq T_{out} < 10`
:code:`rhu_10F_to_15F`                                  decmial          0.0=0%, 1.0=100%         Resistance heat utilization for hourly temperature bin :math:`10 \leq T_{out} < 15`
:code:`rhu_15F_to_20F`                                  decmial          0.0=0%, 1.0=100%         Resistance heat utilization for hourly temperature bin :math:`15 \leq T_{out} < 20`
:code:`rhu_20F_to_25F`                                  decmial          0.0=0%, 1.0=100%         Resistance heat utilization for hourly temperature bin :math:`20 \leq T_{out} < 25`
:code:`rhu_25F_to_30F`                                  decmial          0.0=0%, 1.0=100%         Resistance heat utilization for hourly temperature bin :math:`25 \leq T_{out} < 30`
:code:`rhu_30F_to_35F`                                  decmial          0.0=0%, 1.0=100%         Resistance heat utilization for hourly temperature bin :math:`30 \leq T_{out} < 35`
:code:`rhu_35F_to_40F`                                  decmial          0.0=0%, 1.0=100%         Resistance heat utilization for hourly temperature bin :math:`35 \leq T_{out} < 40`
:code:`rhu_40F_to_45F`                                  decmial          0.0=0%, 1.0=100%         Resistance heat utilization for hourly temperature bin :math:`40 \leq T_{out} < 45`
:code:`rhu_45F_to_50F`                                  decmial          0.0=0%, 1.0=100%         Resistance heat utilization for hourly temperature bin :math:`45 \leq T_{out} < 50`
:code:`rhu_50F_to_55F`                                  decmial          0.0=0%, 1.0=100%         Resistance heat utilization for hourly temperature bin :math:`50 \leq T_{out} < 55`
:code:`rhu_55F_to_60F`                                  decmial          0.0=0%, 1.0=100%         Resistance heat utilization for hourly temperature bin :math:`55 \leq T_{out} < 60`
======================================================= ================ ======================== ===========

Summary Statistics
~~~~~~~~~~~~~~~~~~

For each real- or integer-valued column ("###") from the individual thermostat-season
output, the following summary statistics are generated.

Columns
```````

========================== ===========
Name                       Description
-------------------------- -----------
:code:`###_mean`           Mean
:code:`###_sem`            Standard Error of the Mean
:code:`###_10q`            1st decile (10th percentile, q=quantile)
:code:`###_20q`            2nd decile
:code:`###_30q`            3rd decile
:code:`###_40q`            4th decile
:code:`###_50q`            5th decile
:code:`###_60q`            6th decile
:code:`###_70q`            7th decile
:code:`###_80q`            8th decile
:code:`###_90q`            9th decile
========================== ===========


The following general columns are also output:

Columns
```````

=========================== ===========
Name                        Description
--------------------------- -----------
:code:`label`               Label for the summary
:code:`n_seasons_total`     Number of thermostat-seasons available for inclusion in summary. Should be the sum of :code:`n_seasons_kept` and :code:`n_seasons_discarded`.
:code:`n_seasons_kept`      Number of thermostat-seasons actually included in summary.
:code:`n_seasons_discarded` Number of thermostat-seasons not included in summary because of one or more failed inclusion tests.
=========================== ===========
