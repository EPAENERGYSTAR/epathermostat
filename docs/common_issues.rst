Some Common Issues with Data Files
==================================

.. _common-issues-data-files:

These are a list of common issues with the datafiles for the thermostat software.

Where to find errors
--------------------

- Thermostats that are rejected will be logged in the `thermostat_import_errors.csv` and in the log file (default: `epathermostat.log`).
- Both of these files should be in the same directory as the code that is calling the thermostat module.

.. _metadata-data

Metadata File
-------------

- Missing / non-matching `interval_data_filename`: The interval data file name needs to match the name of the data file being loaded.
- Including a path in the metadata file for the `interval_data_filename`: The path isn't required. The location of the metadata file will provide the path for the interval data files.
- All columns in the metadata file must have data, even if that data is `none` or "". The software will try to elaborate if there is an entry that is missing a field, but your best results will be if you provide data for each field in the file.
- The `zipcode` field should use the "ZIP Code Tabulation Area" code. This will allow for more accurate retrieval of weather station data. For more information on the mapping between ZIP / `ZCTA`_ codes and weather stations, please refer to `eeweather ZCTA to latitide / longitude conversion`_ and :ref:`thermostat.stations`.
- Data in UTC format ("+0") will give the best results. If you must include a UTC offset please ensure that your interval data is also using that UTC offset throughout the dataset.
- `heat_type`, `heat_stage`, `cool_type`, and `cool_stage` need to have appropriate values or placeholders for the data. A best practice is to fill any fields that don't have an appropriate type / stage with "none".

Common Issues with Thermostat Interval Data CSV format
------------------------------------------------------

Missing data
############

- Missing hours / days: The interval file must have all hours represented from the beginning timestamp to the end timestamp, even if there is no data to report for that hour.
- All fields must be present: If there is no data for a field then it needs to still have a placeholder for that data.

Here is an example of how best to represent missing data:

Example of missing data
```````````````````````

In this example we have a thermostat that doesn't have one hour of data on 2021-01-01 at 01:00 UTC. The data file should look like the following

.. code-block:: console

    datetime,cool_runtime_stg1,cool_runtime_stg2,cool_runtime_equiv,heat_runtime_stg1,heat_runtime_stg2,heat_runtime_equiv,emergency_heat_runtime,auxiliary_heat_runtime,temp_in
    2021-01-01 00:00:00,0.0,,,38.0,,,0.0,23.0,64.5
    2021-01-01 01:00:00,,,,,,,,,,
    2021-01-01 02:00:00,0.0,,,39.0,,,,4.0,65.5
   ...

Note that all rows of data are still accounted for, even if there is no data. Also the time-series is contiguous. Even though the data is missing we denote it's absence by including a row for that timestamp. This lets the software know that we are aware that the data is missing and that the data file isn't corrupt.

Missing Weather Station Data
----------------------------

Sometimes a ZCTA will map to a weather station that doesn't have any data. That error will look like the following in the log file:

.. code-block:: console

   2021-08-09 11:26:44,208 - eeweather.connections - WARNING - Failed RETR /pub/data/noaa/2011/720516-99999-2011.gz:
   550 /pub/data/noaa/2011/720516-99999-2011.gz: No such file or directory

If the thermostat software cannot find data for a particular location to compare against it will throw out the thermostat.

Sometimes this error is temporary, but if it is consistently not finding data for a particular location please let us know the ZCTA and the error message you are receiving.

.. _ZCTA: http://www.census.gov/programs-surveys/geography/guidance/geo-areas/zctas.html
.. _eeweather ZCTA to latitide / longitude conversion: http://eeweather.openee.io/en/latest/advanced.html#zcta-to-latitude-longitude-conversion
