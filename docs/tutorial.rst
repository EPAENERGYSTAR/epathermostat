Quickstart
==========

Load thermostat data (see input file format below).

.. code-block:: python

    import sys
    import os
    from os.path import expanduser
    from thermostat.importers import from_csv
    from thermostat.metrics import calculate_epa_draft_rccs_field_savings_metrics
    from thermostat.metrics import seasonal_metrics_to_csv

    data_dir = os.path.join(expanduser("~"),"Downloads/")

    thermostats = from_csv(os.path.join(data_dir,"thermostat_metadata.csv"),
                           os.path.join(data_dir,"thermostat_interval_data.csv"))

Now you may iterate through thermostats and calculate savings metrics for each.

.. code-block:: python

    for thermostat in thermostats:
        metrics = calculate_epa_draft_rccs_field_savings_metrics(thermostat)
        filepath = os.path.join(data_dir,"thermostat_{}_output.csv".format(thermostat.thermostat_id))
        seasonal_metrics_to_csv(metrics,filepath)

**Note**: During the data loading step, you may see a warning that the weather cache is
disabled. You can safely ignore that warning, but if you wish to load a large
amount of data, it will load much more quickly if you use the weather cache.

To enable the weather cache, set the following environment variable to the
database of your choice (the example uses sqlite) by supplying a database url

.. code-block:: bash

    export EEMETER_WEATHER_CACHE_DATABASE_URL=sqlite:////path/to/db.sqlite



Input data
==========

Input data should be specified using the following formats. One CSV should
specify thermostat summary metadata (e.g. unique identifiers, location, etc.).
Another CSV (or CSVs) should contain runtime information, linked to the
metadata csv by the :code:`thermostat_id` column.

Thermostat Summary Metadata CSV format
--------------------------------------

See :download:`example <./examples/thermostat_metadata_example.csv>`

Columns
~~~~~~~

====================== ===========
Name                   Description
---------------------- -----------
:code:`thermostat_id`  A uniquely identifying marker for the thermostat.
:code:`zipcode`        The ZIP code in which the thermostat is installed [#]_.
:code:`equipment_type` The type of controlled HVAC heating and cooling equipment. [#]_
====================== ===========

 - Each row should correspond to a single thermostat.
 - Nulls should be specified by leaving the field blank.

Thermostat Interval Reading CSV format
--------------------------------------

See :download:`example <./examples/thermostat_interval_reading_example.csv>`.

Columns
~~~~~~~

============================ ===========
Name                         Description
---------------------------- -----------
:code:`thermostat_id`        A uniquely identifying marker for the thermostat.
:code:`start_datetime`       The date and time at the start of the reading period.
:code:`end_datetime`         The date and time at the end of the reading period.
:code:`temperature_in`       The average conditioned space temperature over the period of the reading.
:code:`temperature_setpoint` The average thermostat setpoint temperature over the period of the reading.
:code:`ss_heat_pump_heating` Runtime of single stage heat pump equipment in heating mode.
:code:`ss_heat_pump_cooling` Runtime of single stage heat pump equipment in cooling mode.
:code:`auxiliary_heat`       Runtime of auxiliary heat equipment.
:code:`emergency_heat`       Runtime of emergency heat equipment.
:code:`ss_heating`           Runtime of single stage non-heat-pump heating equipment.
:code:`ss_central_ac`        Runtime of single stage central air conditioning equipment.
============================ ===========

- Each row should correspond to a single reading from a thermostat.
- Nulls should be specified by leaving the field blank.
- Runtimes should be specified in seconds.
- Datetimes should be specified in the ISO 8601 combined date and time format.
  (e.g. :code:`2015-05-19T07:31:23+00:00`)
- All temperatures should be specified in °F (to the nearest 0.5°F).


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

=============================================== =========================================
Name                                            Description
----------------------------------------------- -----------------------------------------
:code:`actual_daily_runtime`                    
:code:`actual_seasonal_runtime`                 
:code:`baseline_comfort_temperature`            
:code:`baseline_daily_runtime_dailyavgCDD`      
:code:`baseline_daily_runtime_dailyavgHDD`
:code:`baseline_daily_runtime_deltaT`
:code:`baseline_daily_runtime_hourlysumCDD`
:code:`baseline_daily_runtime_hourlysumHDD`
:code:`baseline_seasonal_runtime_dailyavgCDD`
:code:`baseline_seasonal_runtime_dailyavgHDD`
:code:`baseline_seasonal_runtime_deltaT`
:code:`baseline_seasonal_runtime_hourlysumCDD`
:code:`baseline_seasonal_runtime_hourlysumHDD`
:code:`ct_identifier`                           Unique identifier for thermostat
:code:`equipment_type`
:code:`intercept_dailyavgCDD`
:code:`intercept_dailyavgHDD`
:code:`intercept_deltaT`
:code:`intercept_hourlysumCDD`
:code:`intercept_hourlysumHDD`
:code:`mean_squared_error_dailyavgCDD`
:code:`mean_squared_error_dailyavgHDD`
:code:`mean_squared_error_deltaT`
:code:`mean_squared_error_hourlysumCDD`
:code:`mean_squared_error_hourlysumHDD`
:code:`n_days_both_heating_and_cooling`
:code:`n_days_incomplete`
:code:`rhu_00F_to_05F`
:code:`rhu_05F_to_10F`
:code:`rhu_10F_to_15F`
:code:`rhu_15F_to_20F`
:code:`rhu_20F_to_25F`
:code:`rhu_25F_to_30F`
:code:`rhu_30F_to_35F`
:code:`rhu_35F_to_40F`
:code:`rhu_40F_to_45F`
:code:`rhu_45F_to_50F`
:code:`rhu_50F_to_55F`
:code:`rhu_55F_to_60F`
:code:`season`                                  Name of the heating or cooling season
:code:`seasonal_avoided_runtime_dailyavgCDD`
:code:`seasonal_avoided_runtime_dailyavgHDD`
:code:`seasonal_avoided_runtime_deltaT`
:code:`seasonal_avoided_runtime_hourlysumCDD`
:code:`seasonal_avoided_runtime_hourlysumHDD`
:code:`seasonal_savings_dailyavgCDD`
:code:`seasonal_savings_dailyavgHDD`
:code:`seasonal_savings_deltaT`
:code:`seasonal_savings_hourlysumCDD`
:code:`seasonal_savings_hourlysumHDD`
:code:`slope_dailyavgCDD`
:code:`slope_dailyavgHDD`
:code:`slope_deltaT`
:code:`slope_hourlysumCDD`
:code:`slope_hourlysumHDD`
:code:`zipcode`
=============================================== =========================================
