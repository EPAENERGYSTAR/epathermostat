Some Common Issues with Data Files
==================================

.. _common-issues-data-files:

These are a list of common issues with the datafiles for the thermostat software.

Where to find errors
--------------------

- Thermostats that are rejected will be logged in the log file (default: `epathermostat.log`).
- This file should be in the same directory as the code that is calling the thermostat module.

.. _metadata-data:

Metadata File
-------------

- Missing / non-matching `interval_data_filename`: The interval data file name needs to match the name of the data file being loaded.
- Including a path in the metadata file for the `interval_data_filename`: The path isn't required. The location of the metadata file will provide the path for the interval data files.
- All columns in the metadata file must have data, even if that data is `none` or "". The software will try to elaborate if there is an entry that is missing a field, but your best results will be if you provide data for each field in the file.
- The `zipcode` field should use the ZCTA / ZIP Code of the thermostat. This will be turned into a latitude / longitude that will be used for station lookups.
- Data in UTC format ("+0") will give the best results. If you must include a UTC offset please ensure that your interval data is also using that UTC offset throughout the dataset.

Common Issues with Thermostat Interval Data CSV format
------------------------------------------------------

Missing data
############

- Missing days: The interval file must have all days represented from the beginning date to the end date, even if there is no data to report for that hour.
- All fields must be present: If there is no data for a field then it needs to still have a placeholder for that data.

Here is an example of how best to represent missing data:

Example of missing data
```````````````````````

In this example we have a thermostat that doesn't have a full day of data on 2021-01-02. The data file should look like the following

.. code-block:: console

   date,heat_runtime,cool_runtime,emergency_heat_runtime_00,emergency_heat_runtime_01,emergency_heat_runtime_02,emergency_heat_runtime_03,emergency_heat_runtime_04,emergency_heat_runtime_05,emergency_heat_runtime_06,emergency_heat_runtime_07,emergency_heat_runtime_08,emergency_heat_runtime_09,emergency_heat_runtime_10,emergency_heat_runtime_11,emergency_heat_runtime_12,emergency_heat_runtime_13,emergency_heat_runtime_14,emergency_heat_runtime_15,emergency_heat_runtime_16,emergency_heat_runtime_17,emergency_heat_runtime_18,emergency_heat_runtime_19,emergency_heat_runtime_20,emergency_heat_runtime_21,emergency_heat_runtime_22,emergency_heat_runtime_23,auxiliary_heat_runtime_00,auxiliary_heat_runtime_01,auxiliary_heat_runtime_02,auxiliary_heat_runtime_03,auxiliary_heat_runtime_04,auxiliary_heat_runtime_05,auxiliary_heat_runtime_06,auxiliary_heat_runtime_07,auxiliary_heat_runtime_08,auxiliary_heat_runtime_09,auxiliary_heat_runtime_10,auxiliary_heat_runtime_11,auxiliary_heat_runtime_12,auxiliary_heat_runtime_13,auxiliary_heat_runtime_14,auxiliary_heat_runtime_15,auxiliary_heat_runtime_16,auxiliary_heat_runtime_17,auxiliary_heat_runtime_18,auxiliary_heat_runtime_19,auxiliary_heat_runtime_20,auxiliary_heat_runtime_21,auxiliary_heat_runtime_22,auxiliary_heat_runtime_23,heating_setpoint_00,heating_setpoint_01,heating_setpoint_02,heating_setpoint_03,heating_setpoint_04,heating_setpoint_05,heating_setpoint_06,heating_setpoint_07,heating_setpoint_08,heating_setpoint_09,heating_setpoint_10,heating_setpoint_11,heating_setpoint_12,heating_setpoint_13,heating_setpoint_14,heating_setpoint_15,heating_setpoint_16,heating_setpoint_17,heating_setpoint_18,heating_setpoint_19,heating_setpoint_20,heating_setpoint_21,heating_setpoint_22,heating_setpoint_23,cooling_setpoint_00,cooling_setpoint_01,cooling_setpoint_02,cooling_setpoint_03,cooling_setpoint_04,cooling_setpoint_05,cooling_setpoint_06,cooling_setpoint_07,cooling_setpoint_08,cooling_setpoint_09,cooling_setpoint_10,cooling_setpoint_11,cooling_setpoint_12,cooling_setpoint_13,cooling_setpoint_14,cooling_setpoint_15,cooling_setpoint_16,cooling_setpoint_17,cooling_setpoint_18,cooling_setpoint_19,cooling_setpoint_20,cooling_setpoint_21,cooling_setpoint_22,cooling_setpoint_23,temp_in_00,temp_in_01,temp_in_02,temp_in_03,temp_in_04,temp_in_05,temp_in_06,temp_in_07,temp_in_08,temp_in_09,temp_in_10,temp_in_11,temp_in_12,temp_in_13,temp_in_14,temp_in_15,temp_in_16,temp_in_17,temp_in_18,temp_in_19,temp_in_20,temp_in_21,temp_in_22,temp_in_23
   2011-01-01,753.0,0.0,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,66.5,67.0,65.0,,65.0,69.5,65.5,69.0,67.0,66.5,65.0,64.0,65.5,,67.5,,68.0,65.0,68.0,64.5,65.0,,66.5,,81.0,,77.0,78.0,77.5,,76.0,79.0,75.5,,76.5,80.0,77.5,79.5,,,,71.5,79.5,73.0,78.5,74.5,79.5,79.0,66.5,67.0,,66.5,67.5,68.5,64.0,69.5,67.0,66.5,66.5,65.0,,65.0,67.5,66.5,,66.5,,63.5,65.0,63.0,66.5,
   2011-01-02,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
   2011-01-05,866.0,0.0,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,69.0,68.5,66.0,64.5,67.5,68.5,63.5,64.5,64.0,,,69.5,69.5,69.0,65.0,66.5,63.5,68.5,67.0,67.0,,62.5,66.5,68.5,75.0,,,75.5,77.0,77.5,73.5,75.5,74.5,77.5,78.0,78.0,,79.5,76.5,77.5,78.0,78.0,76.0,77.5,77.0,76.0,77.0,78.0,68.5,69.0,66.0,65.5,67.5,68.5,65.0,65.5,65.0,67.0,65.0,,67.5,71.0,66.0,67.5,,68.0,66.5,67.5,65.0,61.5,67.0,71.0
   ...

Note that all rows of data are still accounted for, even if there is no data. Also the date-series is contiguous. Even though the data is missing we denote it's absence by including a row for that date. This lets the software know that we are aware that the data is missing and that the data file isn't corrupt.

Missing Weather Station Data
----------------------------

Sometimes a ZIP Code / ZCTA will map to a weather station that doesn't have any data. That error will look like the following in the log file:

.. code-block:: console

   2021-08-09 11:26:44,208 - eeweather.connections - WARNING - Failed RETR /pub/data/noaa/2011/720516-99999-2011.gz:
   550 /pub/data/noaa/2011/720516-99999-2011.gz: No such file or directory

If the thermostat software cannot find data for a particular location to compare against it will throw out the thermostat.

Sometimes this error is temporary, but if it is consistently not finding data for a particular location please let us know the ZCTA / ZIP Code and the error message you are receiving.
