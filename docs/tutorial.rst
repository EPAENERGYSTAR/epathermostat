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

