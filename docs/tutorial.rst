Quickstart
==========

Load thermostat data (see input file format below).

.. code-block:: python

    import sys
    import os
    from os.path import expanduser
    from thermostat.importers import from_csv
    from thermostat.exporters import seasonal_metrics_to_csv

    data_dir = os.path.join(expanduser("~"),"Downloads")

    thermostats = from_csv(os.path.join(data_dir,"metadata_example.csv"),
                           os.path.join(data_dir,"interval_data_example.csv"))

Now you may iterate through thermostats and calculate savings metrics for each.

.. code-block:: python

    seasonal_metrics = []
    for thermostat in thermostats:
        outputs = thermostat.calculate_epa_draft_rccs_field_savings_metrics()
        seasonal_metrics.extend(outputs)

    filepath = os.path.join(data_dir, "thermostat_module_example_output.csv")
    seasonal_metrics_to_csv(seasonal_metrics, filepath)

**Note**: During the data loading step, you may see a warning that the weather cache is
disabled. You can safely ignore that warning, but if you wish to load a large
amount of data, it will load much more quickly if you use the weather cache.

To enable the weather cache, set the following environment variable to the
database of your choice (the example uses sqlite) by supplying a database url

.. code-block:: bash

    export EEMETER_WEATHER_CACHE_DATABASE_URL=sqlite:////path/to/db.sqlite

For more information, see `EE-Meter <http://eemeter.readthedocs.org/en/latest/tutorial.html#caching-weather-data>`_

Input data
==========

Input data should be specified using the following formats. One CSV should
specify thermostat summary metadata (e.g. unique identifiers, location, etc.).
Another CSV (or CSVs) should contain runtime information, linked to the
metadata csv by the :code:`thermostat_id` column.

Thermostat Summary Metadata CSV format
--------------------------------------

See :download:`example <./examples/metadata_example.csv>`.

Columns
~~~~~~~

====================== ===========
Name                   Description
---------------------- -----------
:code:`thermostat_id`  A uniquely identifying marker for the thermostat.
:code:`zipcode`        The ZIP code in which the thermostat is installed [#]_.
:code:`equipment_type` The type of controlled HVAC heating and cooling equipment. [#]_
:code:`utc_offset`     The UTC offset of the times in the corresponding interval data CSV. (e.g. "-0700")
====================== ===========

 - Each row should correspond to a single thermostat.
 - Nulls should be specified by leaving the field blank.
 - All data for a particular thermostat in the corresponding interval data
   CSV must use the SAME UTC offset provided here in the metadata.

Thermostat Interval Data CSV format
--------------------------------------

See :download:`example <./examples/interval_data_example.csv>`.

Columns
~~~~~~~

============================ ===========
Name                         Description
---------------------------- -----------
:code:`thermostat_id`        Uniquely identifying marker for the thermostat.
:code:`date`                 Date of this set of readings. (YYYY-MM-DD).
:code:`cool_runtime`         Runtime of cooling equipment (seconds, daily).
:code:`heat_runtime`         Runtime of heating equipment (seconds, daily).
:code:`auxiliary_heat`       Runtime of auxiliary heat equipment (seconds, daily).
:code:`emergency_heat`       Runtime of emergency heat equipment (seconds, daily).
:code:`temp_in_HH`           Hourly average conditioned space temperature over the period of the reading (HH=00-23).
:code:`heating_setpoint_HH`  Hourly average thermostat setpoint temperature over the period of the reading (HH=00-23).
:code:`cooling_setpoint_HH`  Hourly average thermostat setpoint temperature over the period of the reading (HH=00-23).
============================ ===========

- Each row should correspond to a single hourly reading from a thermostat.
- Nulls should be specified by leaving the field blank.
- Runtimes should be specified in seconds and should be less than or equal to
  86400 s (1 day).
- Dates should be specified in the ISO 8601 date format (e.g. :code:`2015-05-19`).
- All temperatures should be specified in °F (to the nearest 0.5°F).
- If no distinction is made between heating and cooling setpoint, set both
  equal to the single setpoint.
- All runtime data MUST have the same UTC offset, as provided in the
  corresponding metadata file.

.. [#] Will be used for matching with a weather station that provides external
   dry-bulb temperature data. This temperature data will be used to determine
   the bounds of the heating and cooling season over which metrics will be
   computed.

.. [#] Options for :code:`equipment_type`:

   - :code:`0`: Other – e.g. multi-zone multi-stage, modulating. Note: module will
     not output savings data for this type.
   - :code:`1`: Single stage heat pump with aux and/or emergency heat
   - :code:`2`: Single stage heat pump without aux or emergency heat
   - :code:`3`: Single stage non heat pump with single-stage central air conditioning
   - :code:`4`: Single stage non heat pump without central air conditioning
   - :code:`5`: Single stage central air conditioning without central heating

Output data
===========

See :download:`example <./examples/output_example.csv>`.

=============================================== =========================================
Name                                            Description
----------------------------------------------- -----------------------------------------
actual_daily_runtime
actual_seasonal_runtime
alpha_est_dailyavgCDD
alpha_est_dailyavgHDD
alpha_est_hourlysumCDD
alpha_est_hourlysumHDD
baseline_comfort_temperature
baseline_daily_runtime_dailyavgCDD
baseline_daily_runtime_dailyavgHDD
baseline_daily_runtime_deltaT
baseline_daily_runtime_hourlysumCDD
baseline_daily_runtime_hourlysumHDD
baseline_seasonal_runtime_dailyavgCDD
baseline_seasonal_runtime_dailyavgHDD
baseline_seasonal_runtime_deltaT
baseline_seasonal_runtime_hourlysumCDD
baseline_seasonal_runtime_hourlysumHDD
ct_identifier                                   Unique identifier for thermostat
deltaT_base_est_dailyavgCDD
deltaT_base_est_dailyavgHDD
deltaT_base_est_hourlysumCDD
deltaT_base_est_hourlysumHDD
equipment_type
mean_sq_err_dailyavgCDD
mean_sq_err_dailyavgHDD
mean_sq_err_hourlysumCDD
mean_sq_err_hourlysumHDD
mean_squared_error_deltaT
n_days_both_heating_and_cooling
n_days_both_heating_and_heating
n_days_incomplete
rhu_00F_to_05F
rhu_05F_to_10F
rhu_10F_to_15F
rhu_15F_to_20F
rhu_20F_to_25F
rhu_25F_to_30F
rhu_30F_to_35F
rhu_35F_to_40F
rhu_40F_to_45F
rhu_45F_to_50F
rhu_50F_to_55F
rhu_55F_to_60F
season_name
seasonal_avoided_runtime_dailyavgCDD
seasonal_avoided_runtime_dailyavgHDD
seasonal_avoided_runtime_deltaT
seasonal_avoided_runtime_hourlysumCDD
seasonal_avoided_runtime_hourlysumHDD
seasonal_savings_dailyavgCDD
seasonal_savings_dailyavgHDD
seasonal_savings_deltaT
seasonal_savings_hourlysumCDD
seasonal_savings_hourlysumHDD
slope_deltaT
zipcode
=============================================== =========================================
