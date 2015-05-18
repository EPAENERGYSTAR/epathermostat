Tutorial
========

Input data should be specified using the following formats. One CSV should
specify thermostat summary metadata (e.g. unique identifiers, location, etc.).
Another CSV (or CSVs) should contain runtime information, linked to the
metadata csv by the :code:`thermostat_id` column.

Thermostat Summary Metadata CSV format
--------------------------------------

 - Each row should correspond to a single thermostat.
 - Nulls should be specified by leaving the field blank.

Columns
~~~~~~~

====================== ===========
Name                   Description
---------------------- -----------
:code:`thermostat_id`  A uniquely identifying marker for the thermostat.
:code:`zipcode`        The ZIP code in which the thermostat is installed [#]_.
:code:`equipment_type` The type of controlled HVAC heating and cooling equipment. (Details below)
====================== ===========

Options for :code:`equipment_type`:

- :code:`0`: Other – e.g. multi-zone multi-stage, modulating. Note: module will
   not output savings data for this type.
- :code:`1`: Single stage heat pump with aux and/or emergency heat
- :code:`2`: Single stage heat pump without aux or emergency heat
- :code:`3`: Single stage non heat pump with single-stage central air conditioning
- :code:`4`: Single stage non heat pump without central air conditioning
- :code:`5`: Single stage central air conditioning w/o central heating

Thermostat Interval Reading CSV format
--------------------------------------

 - Each row should correspond to a single reading from a thermostat.
 - Nulls should be specified by leaving the field blank.
 - All runtimes should be specified in seconds.
 - All date-times should be specified in the ISO 8601 combined date and time format.

Columns
~~~~~~~

============================ ===========
Name                         Description
---------------------------- -----------
:code:`thermostat_id`        A uniquely identifying marker for the thermostat.
:code:`start_datetime`       The start date and time of the reading.
:code:`end_datetime`         The end date and time of the reading.
:code:`temperature_in`       The average conditioned space temperature over the period of the reading.
:code:`temperature_setpoint` The average thermostat setpoint temperature over the period of the reading.
:code:`ss_heat_pump_heating` Runtime of single stage heat pump equipment in heating mode.
:code:`ss_heat_pump_cooling` Runtime of single stage heat pump equipment in cooling mode.
:code:`ss_heating`           Runtime of non-heat-pump single stage heating equipment.
:code:`auxiliary_heat`       Runtime of auxiliary heat equipment.
:code:`emergency_heat`       Runtime of emergency heat equipment.
:code:`central_ac`           Runtime of central air conditioning equipment.
============================ ===========

.. [#] Will be used for matching with a weather station that provides external
   dry-bulb temperature data.
