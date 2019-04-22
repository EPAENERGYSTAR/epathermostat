Quickstart
==========

Installation
------------

To install the thermostat package for the first time, we highly recommend that
you create a virtual environment or a conda environment in which to install it.
You may choose to skip this step, but do so at the risk of corrupting your
existing python environment. Isolating your python environment will also
make it easier to debug.

.. code-block:: bash

    # if using virtualenvwrapper (see https://virtualenvwrapper.readthedocs.org/en/latest/install.html)
    $ mkvirtualenv thermostat
    (thermostat)$ pip install thermostat

    # if using conda (see note below - conda is distributed with Anaconda)
    $ conda create --yes --name thermostat pandas
    $ source activate thermostat
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

    '1.5.0'

If you are not on the correct version, you should upgrade:

.. code-block:: bash

    $ pip install thermostat --upgrade

The command above will update dependencies as well. If you wish to skip this,
use the :code:`--no-deps` flag:

.. code-block:: bash

    $ pip install thermostat --upgrade --no-deps

Previous versions of the package are available on `github <https://github.com/openeemeter/thermostat/releases>`_.

.. note::

    If you experience issues installing python packages with C extensions, such
    as `numpy` or `scipy`, we recommend installing and using the free
    `Anaconda <https://www.continuum.io/downloads>`_ Python distribution by
    Continuum Analytics. It contains many of the numeric and scientific
    packages used by this package and has installers for Python 2.7 and 3.5 for
    Windows, Mac OS X and Linux.

Once you have verified a correct installation, import the necessary methods
and set a directory for finding and storing data.

.. note::

    If you suspect a package version conflict or error, you can verify the
    versions of the packages you have installed against the package
    versions in :download:`thermostatreqnotes.txt <../thermostatreqnotes.txt>`.

    To list your package versions, use:

    .. code-block:: bash

        $ pip freeze

    or (if you're using Anaconda):

    .. code-block:: bash

        $ conda list

Script setup and imports
------------------------

Import the few built-in python packages and methods we will be using in
this tutorial as follows.

.. code-block:: python

    import sys
    import os
    import warnings
    from os.path import expanduser

Also make sure to import the methods we will be using from the thermostat
package.

.. code-block:: python

    from thermostat.importers import from_csv
    from thermostat.exporters import metrics_to_csv
    from thermostat.stats import compute_summary_statistics
    from thermostat.stats import summary_statistics_to_csv


If you wish to use multiple processors for your thermostat calculations you'll
need some additional modules:

.. code-block:: python

    from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics


Set the data_dir variable as a convenience. We will refer to this directory
and save our results in it. You should also move all downloaded and extracted
files used in this tutorial into this directory before using them. You may, of
course, choose to use a different directory, which you can set here, or
override it entirely by replacing it where it appears in the tutorial.

.. code-block:: python

    data_dir = os.path.join(expanduser("~"), "thermostat_tutorial")
    # or data_dir = "/full/path/to/custom/directory/"

Optional Setup
--------------

If you wish to follow the progress of downloading and caching external
weather files, which will be the most time-consuming portion of this
tutorial, you may wish at this point to configure logging. The example
here will work within most ipython or script environments. If you have a
more complicated logging setup, you may need to use something other than
the root logger, which this uses.

.. code-block:: python

    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

.. note::

    The thermostat package depends on the eemeter package for weather data
    fetching. The eemeter package automatically creates its own cache directory
    in which it keeps cached versions of weather source data. This speeds up
    the (generally I/O bound) NOAA weather fetching routine on subsequent
    internal calls to fetch the same weather data (i.e. getting outdoor
    temperature data for thermostats that map to the same weather station).

    For more information, see the `eemeter package <https://eemeter.readthedocs.io/en/release-v0.4.8-alpha/weather.html#isdweathersource>`_.

.. note::

    US Census Bureau ZIP Code Tabulation Areas (ZCTA) are used to map USPS ZIP
    codes to outdoor temperature data. If the automatic mapping is unsuccessful
    for one or more of the ZIP codes in your dataset, the reason is likely to
    be the discrepancy between "true" USPS ZIP codes and the US Census Bureau
    ZCTAs. "True" ZIP codes are not used because they do not always map well to
    location (for example, ZIP codes for P.O. boxes). You may need to first map
    ZIP codes to ZCTAs, or these thermostats will be skipped. There are roughly
    32,000 ZCTAs and roughly 42000 ZIP codes - many fewer ZCTAs than ZIP codes.

Computing individual thermostat-season metrics
----------------------------------------------

After importing the package methods, load the example thermostat data, or
provide data of your own. See :ref:`thermostat-input` for more detailed file
format information.

Fabricated example data from 35 thermostats in various climate zones, is
available for download :download:`here <./examples/examples.zip>`.

Loading the thermostat data below will take more than a few minutes, even if
the weather cache is enabled (see note above). This is because loading
thermostat data involves downloading hourly weather data from a remote
source - in this case, the NCDC.

The following loads an lazy iterator over the thermostats. The thermostats
will be loaded into memory as necessary in the following steps.

.. code-block:: python

    metadata_filename = os.path.join(data_dir, "examples/metadata.csv")
    thermostats = from_csv(metadata_filename, verbose=True)

To calculate savings metrics, iterate through thermostats and save the results.
Uncomment the commented lines if you would like to store the thermostats in
memory for inspection. Note that this could eat up your application memory and
is only recommended for debugging purposes.

.. code-block:: python

    metrics = []
    # saved_thermostats = []
    for thermostat in thermostats:
        outputs = thermostat.calculate_epa_field_savings_metrics()
        metrics.extend(outputs)
        # saved_thermostats.append(thermostat)


If you are looking to use multiple thermostats for the calculation you may
replace the above code with the following method call:

.. code-block:: python

    metrics = multiple_thermostat_calculate_epa_field_savings_metrics(thermostats)

This will use all of the available CPUs on the machine in order to calculate
the savings metrics. 

.. note::

    You will need to have imported the
    ``multiple_thermostat_calculate_epa_field_savings_metrics`` method from
    ``thermostat.multiple`` prior to using this method.

    If you're running under Windows please see the "Notes for Windows Users" below.


The single-thermostat metrics should be output to CSV and converted to dataframe format.

.. code-block:: python

    output_filename = os.path.join(data_dir, "thermostat_example_output.csv")
    metrics_df = metrics_to_csv(metrics, output_filename)

The output CSV will be saved in your data directory and should very nearly
match the output CSV provided in the example data.

See :ref:`thermostat-output` for more detailed file format information.


Computing summary statistics
----------------------------

Once you have obtained output for each individual thermostat in your dataset,
use the stats module to compute summary statistics, which are formatted for
submission to the EPA. The example below works with the output file from the
tutorial above and can be modified to use your data.

Compute statistics across all thermostats.

.. code-block:: python

    # uses the metrics_df created in the Quickstart above.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        # uses the metrics_df created in the quickstart above.
        stats = compute_summary_statistics(metrics_df)

        # If you want to have advanced filter outputs, use this instead
        # stats_advanced = compute_summary_statistics(metrics_df, advanced_filtering=True)

Save these results to file.

Each row of the saved CSV will represent one type of output, with one row per
statistic per output. Each column in the CSV will represent one subset of
thermostats, as determined by grouping by EIC climate zone and applying
various filtering methods. National weighted averages will be available near
the top of the file.

At this point, you will also need to provide an alphanumeric product identifier
for the connected thermostat; e.g. a combination of the connected thermostat
service plus one or more connected thermostat device models that comprises the
data set.

.. code-block:: python

    product_id = "INSERT ALPHANUMERIC PRODUCT ID HERE"
    stats_filepath = os.path.join(data_dir, "thermostat_example_stats.csv")
    stats_df = summary_statistics_to_csv(stats, stats_filepath, product_id)

    # or with advanced filter outputs
    # stats_advanced_filepath = os.path.join(data_dir, "thermostat_example_stats_advanced.csv")
    # stats_advanced_df = summary_statistics_to_csv(stats_advanced, stats_advanced_filepath, product_id)

National savings are computed by weighted average of percent savings results
grouped by climate zone. Heavier weights are applied to results in climate
zones which, regionally, tend to have longer runtimes. Weightings used are
available :download:`for download <../thermostat/resources/NationalAverageClimateZoneWeightings.csv>`.

Notes for Windows Users
-----------------------

Python under Windows requires that all multiprocessing code needs to be run under a sub module. If you are under Windows you will need to wrap your code using the following:

.. code-block:: python
    
    def main():
        # Code goes here

    if __name__ == "__main__":
        main()

Not having this wrapper will cause a Runtime Error "Attempt to start a new process before the current process has finished its bootstrapping phase.".

Other platforms should not be affected by this.

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
  automatically from NCDC using the `eemeter package <https://eemeter.readthedocs.io/en/release-v0.4.8-alpha/weather.html#isdweathersource>`_ package.
- Dates should be consecutive.

.. [#] Options for :code:`equipment_type`:

   - :code:`0`: Other – e.g. multi-zone multi-stage, modulating. Note: module will
     not output savings data for this type.
   - :code:`1`: Single stage heat pump with electric resistance aux and/or emergency heat (i.e., strip heat)
   - :code:`2`: Single stage heat pump without additional and/or supplemental heating sources (excludes aux/emergency heat as well as dual fuel systems, i.e., heat pump plus gas- or oil-fired furnace)
   - :code:`3`: Single stage non heat pump with single-stage central air conditioning
   - :code:`4`: Single stage non heat pump without central air conditioning
   - :code:`5`: Single stage central air conditioning without central heating

.. [#] Will be used for matching with a weather station that provides external
   dry-bulb temperature data. This temperature data will be used to determine
   the bounds of the heating and cooling season over which metrics will be
   computed. For more information on the mapping between ZIP codes and
   weather stations, please see `eemeter.weather.location <https://eemeter.readthedocs.io/en/release-v0.4.8-alpha/weather.html#eemeter.weather.location.zipcode_to_climate_zone>`_.

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

.. csv-table::
   :header: "Name", "Data Format", "Units", "Description"

   "**General outputs**"
   ":code:`sw_version`","string","N/A","Software version."
   ":code:`ct_identifier`","string","N/A","Identifier for thermostat as provided in the metadata file."
   ":code:`equipment_type`","enum {0..5}","N/A","Equipment type of this thermostat (1, 2, 3, 4, or 5)."
   ":code:`heating_or_cooling`","string","N/A","Label for the core day set (e.g. 'heating_2012-2013')."
   ":code:`zipcode`","string, 5 digits ","N/A","ZIP code provided in the metadata file."
   ":code:`station`","string, USAF ID","N/A","USAF identifier for station used to fetch hourly temperature data."
   ":code:`climate_zone`","string","N/A","EIC climate zone (consolidated)."
   ":code:`start_date`","date","ISO-8601","Earliest date in input file."
   ":code:`end_zone`","date","ISO-8601","Latest date in input file."
   ":code:`n_days_both_heating_and_cooling`","integer","# days","Number of days not included as core days due to presence of both heating and cooling."
   ":code:`n_days_insufficient_data`","integer","# days","Number of days not included as core days due to missing data."
   ":code:`n_core_cooling_days`","integer","# days","Number of days meeting criteria for inclusion in core cooling day set."
   ":code:`n_core_heating_days`","integer","# days","Number of days meeting criteria for inclusion in core heating day set."
   ":code:`n_days_in_inputfile_date_range`","integer","# days","Number of potential days in inputfile date range."
   ":code:`baseline10_core_cooling_comfort_temperature`","float","°F","Baseline comfort temperature as determined by 10th percentile of indoor temperatures."
   ":code:`baseline90_core_cooling_comfort_temperature`","float","°F","Baseline comfort temperature as determined by 90th percentile of indoor temperatures."
   ":code:`regional_average_baseline_cooling_comfort_temperature`","float","°F","Baseline comfort temperature as determined by regional average."
   ":code:`regional_average_baseline_heating_comfort_temperature`","float","°F","Baseline comfort temperature as determined by regional average."
   "**Model outputs**"
   ":code:`percent_savings_baseline_percentile`","float","percent","Percent savings as given by hourly average CTD or HTD method with 10th or 90th percentile baseline"
   ":code:`avoided_daily_mean_core_day_runtime_baseline_percentile`","float","minutes","Avoided average daily runtime for core cooling days"
   ":code:`avoided_total_core_day_runtime_baseline_percentile`","float","minutes","Avoided total runtime for core cooling days"
   ":code:`baseline_daily_mean_core_day_runtime_baseline_percentile`","float","minutes","Baseline average daily runtime for core cooling days"
   ":code:`baseline_total_core_day_runtime_baseline_percentile`","float","minutes","Baseline total runtime for core cooling days"
   ":code:`percent_savings_baseline_regional`","float","percent","Percent savings as given by hourly average CTD or HTD method with 10th or 90th percentile regional baseline"
   ":code:`avoided_daily_mean_core_day_runtime_baseline_regional`","float","minutes","Avoided average daily runtime for core cooling days"
   ":code:`avoided_total_core_day_runtime_baseline_regional`","float","minutes","Avoided total runtime for core cooling days"
   ":code:`baseline_daily_mean_core_day_runtime_baseline_regional`","float","minutes","Baseline average daily runtime for core cooling days"
   ":code:`baseline_total_core_day_runtime_baseline_regional`","float","minutes","Baseline total runtime for core cooling days"
   ":code:`mean_demand`","float","°F","Average cooling demand"
   ":code:`alpha`","float","minutes/Δ°F","The fitted slope of cooling runtime to demand regression"
   ":code:`tau`","float","°F","The fitted intercept of cooling runtime to demand regression"
   ":code:`mean_sq_err`","float","N/A","Mean squared error of regression"
   ":code:`root_mean_sq_err`","float","N/A","Root mean squared error of regression"
   ":code:`cv_root_mean_sq_err`","float","N/A","Coefficient of variation of root mean squared error of regression"
   ":code:`mean_abs_err`","float","N/A","Mean absolute error"
   ":code:`mean_abs_pct_err`","float","N/A","Mean absolute percent error"
   "**Runtime outputs**"
   ":code:`total_core_cooling_runtime`","float","minutes","Total core cooling equipment runtime"
   ":code:`total_core_heating_runtime`","float","minutes","Total core heating equipment runtime"
   ":code:`total_auxiliary_heating_core_day_runtime`","float","minutes","Total core auxiliary heating equipment runtime"
   ":code:`total_emergency_heating_core_day_runtime`","float","minutes","Total core emergency heating equipment runtime"
   ":code:`daily_mean_core_cooling_runtime`","float","minutes","Average daily core cooling runtime"
   ":code:`daily_mean_core_heating_runtime`","float","minutes","Average daily core cooling runtime"
   "**Resistance heat outputs**"
   ":code:`rhu1_00F_to_05F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`0 \leq T_{out} < 5`"
   ":code:`rhu1_05F_to_10F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`5 \leq T_{out} < 10`"
   ":code:`rhu1_10F_to_15F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`10 \leq T_{out} < 15`"
   ":code:`rhu1_15F_to_20F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`15 \leq T_{out} < 20`"
   ":code:`rhu1_20F_to_25F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`20 \leq T_{out} < 25`"
   ":code:`rhu1_25F_to_30F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`25 \leq T_{out} < 30`"
   ":code:`rhu1_30F_to_35F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`30 \leq T_{out} < 35`"
   ":code:`rhu1_35F_to_40F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`35 \leq T_{out} < 40`"
   ":code:`rhu1_40F_to_45F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`40 \leq T_{out} < 45`"
   ":code:`rhu1_45F_to_50F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`45 \leq T_{out} < 50`"
   ":code:`rhu1_50F_to_55F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`50 \leq T_{out} < 55`"
   ":code:`rhu1_55F_to_60F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`55 \leq T_{out} < 60`"

Summary Statistics
~~~~~~~~~~~~~~~~~~

For each real- or integer-valued column ("###") from the individual thermostat-season
output, the following summary statistics are generated.

(For readability, these columns are actually rows.)

Columns
```````

.. csv-table::
   :header: "Name", "Description"

   ":code:`###_n`","Number of samples"
   ":code:`###_upper_bound_95_perc_conf`","95% confidence upper bound on mean value"
   ":code:`###_mean`","Mean value"
   ":code:`###_lower_bound_95_perc_conf`","95% confidence lower bound on mean value"
   ":code:`###_sem`","Standard error of the mean"
   ":code:`###_10q`","1st decile (10th percentile, q=quantile)"
   ":code:`###_20q`","2nd decile"
   ":code:`###_30q`","3rd decile"
   ":code:`###_40q`","4th decile"
   ":code:`###_50q`","5th decile"
   ":code:`###_60q`","6th decile"
   ":code:`###_70q`","7th decile"
   ":code:`###_80q`","8th decile"
   ":code:`###_90q`","9th decile"

The following general columns are also output:

Columns
```````

.. csv-table::
   :header: "Name", "Description"

   ":code:`sw_version`","Software version"
   ":code:`product_id`","Alphanumeric product identifier"
   ":code:`n_thermostat_core_day_sets_total`","Number of relevant rows from thermostat module output before filtering"
   ":code:`n_thermostat_core_day_sets_kept`","Number of relevant rows from thermostat module not filtered out"
   ":code:`n_thermostat_core_day_sets_discarded`","Number of relevant rows from thermostat module filtered out"

The following national weighted percent savings columns are also available.

National savings are computed by weighted average of percent savings results
grouped by climate zone. Heavier weights are applied to results in climate
zones which, regionally, tend to have longer runtimes. Weightings used are
available :download:`for download <../thermostat/resources/NationalAverageClimateZoneWeightings.csv>`.

Columns
```````
.. csv-table::
   :header: "Name", "Description"

   ":code:`percent_savings_baseline_percentile_mean_national_weighted_mean`","National weighted mean percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q10_national_weighted_mean`","National weighted 10th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q20_national_weighted_mean`","National weighted 20th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q30_national_weighted_mean`","National weighted 30th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q40_national_weighted_mean`","National weighted 40th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q50_national_weighted_mean`","National weighted 50th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q60_national_weighted_mean`","National weighted 60th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q70_national_weighted_mean`","National weighted 70th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q80_national_weighted_mean`","National weighted 80th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q90_national_weighted_mean`","National weighted 90th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_lower_bound_95_perc_conf_national_weighted_mean`","National weighted mean percent savings lower bound as given by a 95% confidence interval and the baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_upper_bound_95_perc_conf_national_weighted_mean`","National weighted mean percent savings upper bound as given by a 95% confidence interval and the baseline_percentile method."
   ":code:`percent_savings_baseline_regional_mean_national_weighted_mean`","National weighted mean percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q10_national_weighted_mean`","National weighted 10th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q20_national_weighted_mean`","National weighted 20th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q30_national_weighted_mean`","National weighted 30th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q40_national_weighted_mean`","National weighted 40th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q50_national_weighted_mean`","National weighted 50th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q60_national_weighted_mean`","National weighted 60th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q70_national_weighted_mean`","National weighted 70th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q80_national_weighted_mean`","National weighted 80th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q90_national_weighted_mean`","National weighted 90th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_lower_bound_95_perc_conf_national_weighted_mean`","National weighted mean percent savings lower bound as given by a 95% confidence interval and the baseline_regional method."
   ":code:`percent_savings_baseline_regional_upper_bound_95_perc_conf_national_weighted_mean`","National weighted mean percent savings upper bound as given by a 95% confidence interval and the baseline_regional method."
