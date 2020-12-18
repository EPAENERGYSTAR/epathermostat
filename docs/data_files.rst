Data Files
==========


.. _thermostat-input:

Input data
----------

Input data should be specified using the following formats. The metadata CSV file 
specifies unique values for each thermostat such as equipment type and location.
Each thermostat interval data CSV file contains hourly runtime information and is linked
to the metadata CSV file by the :code:`interval_data_filename` column.

Example files :download:`here <./examples/examples.zip>`.

Thermostat Summary Metadata CSV format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Columns
```````

============================== ================ ===== ===========
Name                           Data Format      Units Description
------------------------------ ---------------- ----- -----------
:code:`thermostat_id`          string           N/A   A uniquely identifying marker for the thermostat.
:code:`heat_type`              string           N/A   The type of controlled HVAC heating equipment. [#]_ 
:code:`heat_stage`             string           N/A   The stages of controlled HVAC heating equipment. [#]_
:code:`cool_type`              string           N/A   The type of controlled HVAC cooling equipment. [#]_
:code:`cool_stage`             string           N/A   The stages of controlled HVAC cooling equipment. [#]_
:code:`zipcode`                string, 5 digits N/A   The `ZCTA`_ code in which the thermostat is installed. [#]_
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

============================ ================================ ======= ===========
Name                         Data Format                      Units   Description
---------------------------- -------------------------------- ------- -----------
:code:`thermostat_id`        string                           N/A     Uniquely identifying marker for the thermostat.
:code:`datetime`             YYYY-MM-DD hh:mm:ss (ISO-8601)   N/A     Date and time of this set of readings.
:code:`cool_runtime_stg1`    decimal or integer               minutes Hourly runtime of cooling equipment (all units).
:code:`cool_runtime_stg2`    decimal or integer               minutes Hourly runtime of cooling equipment second stage (two-stage units only).
:code:`cool_runtime_equiv`   decimal or integer               minutes Hourly full load equivalent runtime of cooling equipment (multi-stage units only).
:code:`heat_runtime_stg1`    decimal or integer               minutes Hourly runtime of heating equipment (all units).
:code:`heat_runtime_stg2`    decimal or integer               minutes Hourly runtime of heating equipment second stage (two-stage units only).
:code:`heat_runtime_equiv`   decimal or integer               minutes Hourly full load equivalent runtime of heating equipment (multi-stage units only).
:code:`auxiliary_heat`       decimal or integer               minutes Hourly runtime of auxiliary heat equipment.
:code:`emergency_heat`       decimal or integer               minutes Hourly runtime of emergency heat equipment.
:code:`temp_in`              decimal, to nearest 0.5 °F       °F      Hourly average conditioned space temperature over the period of the reading.
============================ ================================ ======= ===========

- Dates should be specified in the ISO 8601 date format (e.g. :code:`2015-05-19 01:00:00`, :code:`2020-01-01 23:00:00`).
- Dates and times must be consecutive. (e.g.: :code:`2020-01-01 23:00:00`
  should have :code:`2020-01-02 00:00:00` on the next line and :code:`2020-01-02 01:00:00` after that.)
- All dates for the period must be represented and consecutive. (i.e. each date for a period must have a line in the data file.)
- Each row should correspond to a single hourly reading from a thermostat. [#]_
- `NULL` should be specified by leaving the field blank.
- Zero values should be specified as 0, rather than as blank.
- If data is missing for a particular row of one column, data should still be
  provided for other columns in that row. For example, if runtime is missing
  for a particular hour, please still provide indoor conditioned space
  temperature for that hour, if available.
- Runtimes should be less than or equal to 60 minutes (1 hour).
- All temperatures should be specified in °F (to the nearest 0.5°F).
- All runtime data MUST have the same UTC offset, as provided in the
  corresponding metadata file.
- Outdoor temperature data need not be provided - it will be fetched
  automatically from NCDC using the `eeweather`_ package.
- If a heating or cooling type or stage is not present or not applicable a
  value of :code:`none` or blank is sufficient.
- All headers must be present in the file, even if there is no data for that
  column (use :code:`none` or blank for missing data.)

.. [#] Possible values for :code:`heat_type` are:

    - :code:`furnace_or_boiler`: Forced air furnace (any fuel)
    - :code:`heat_pump_electric_backup`: Heat pump with electric resistance heat (strip heat)
    - :code:`heat_pump_no_electric_backup`: Heat pump without electric resistance heat
    - :code:`heat_pump_dual_fuel`: Dual fuel heat pump (e.g. gas or oil fired)
    - :code:`other`: Multi-zone, etc.
    - :code:`none`: No central heating system
    - :code:`(blank)`: No central heating system

.. [#] Possible values for :code:`heat_stage` are:

    - :code:`single_stage`: Single capacity heater or single stage compressor
    - :code:`single_speed`: Synonym for single capacity heater or single stage compressor
    - :code:`two_stage`: Dual capacity heater or dual stage compressor
    - :code:`two_speed`: Synonym for dual capacity heater or dual stage compressor
    - :code:`modulating`: Modulating or variable capacity unit
    - :code:`variable_speed`: Modulating or variable capacity unit
    - :code:`none`: No central heating system
    - :code:`(blank)`: No central heating system

.. [#] Possible values for :code:`cool_type` are:

    - :code:`heat_pump`: Heat pump w/ cooling
    - :code:`central`: Central AC
    - :code:`other`: Mini-split, evaporative cooler, etc.
    - :code:`none`: No central cooling system
    - :code:`(blank)`: No central cooling system

.. [#] Possible values for :code:`cool_stage` are:

    - :code:`single_stage`: Single stage compressor
    - :code:`two_stage`: Dual stage compressor
    - :code:`single_speed`: Single stage compressor (synonym for single_stage)
    - :code:`two_speed`: Dual stage compressor (synonym for two_stage)
    - :code:`modulating`: Modulating or variable capacity compressor
    - :code:`none`: No central cooling system
    - :code:`(blank)`: No central cooling system

.. [#] Will be used for matching with a weather station that provides external
   dry-bulb temperature data. This temperature data will be used to determine
   the bounds of the heating and cooling season over which metrics will be
   computed. For more information on the mapping between ZIP / `ZCTA`_ codes and
   weather stations, please refer to `eeweather ZCTA to latitide / longitude conversion`_
   and :ref:`thermostat.stations`.

.. [#] Previous versions of this software had each row as one daily result. This version changes this to use hourly rows instead.

.. _thermostat-output:

Output data
-----------

Individual thermostat-season
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following columns are an intermediate output generated for each thermostat-season.

Columns
```````

.. csv-table::
   :header: "Name", "Data Format", "Units", "Description"

   "**General outputs**"
   ":code:`sw_version`","string","N/A","Software version."
   ":code:`ct_identifier`","string","N/A","Identifier for thermostat as provided in the metadata file."
   ":code:`heat_type`","string","N/A","Heating type for the thermostat"
   ":code:`heat_stage`","string","N/A","Heating stage for the thermostat"
   ":code:`cool_type`","string","N/A","Cooling type for the thermostat"
   ":code:`cool_stage`","string","N/A","Cooling stage for the thermostat"
   ":code:`heating_or_cooling`","string","N/A","Label for the core day set (e.g. 'heating_2012-2013')."
   ":code:`zipcode`","string, 5 digits ","N/A","ZIP code provided in the metadata file."
   ":code:`station`","string, USAF ID","N/A","USAF identifier for station used to fetch hourly temperature data."
   ":code:`climate_zone`","string","N/A","EIC climate zone (consolidated)."
   ":code:`start_date`","date","ISO-8601","Earliest date in input file."
   ":code:`end_date`","date","ISO-8601","Latest date in input file."
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
   "**Core mean temperatures**"
   ":code:`core_cooling_days_mean_indoor_temperature`","float","°F","Mean of core cooling days indoor temperature"
   ":code:`core_cooling_days_mean_outdoor_temperature`","float","°F","Mean of core cooling days outdoor temperature"
   ":code:`core_heating_days_mean_indoor_temperature`","float","°F","Mean of heating days indoor temperature"
   ":code:`core_heating_days_mean_outdoor_temperature`","float","°F","Mean of heating days outdoor temperature"
   ":code:`core_mean_indoor_temperature`","float","°F","Mean of indoor temperature"
   ":code:`core_mean_outdoor_temperature`","float","°F","Mean of outdoor temperature"
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
   ":code:`rhu1_30F_to_45F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`30 \leq T_{out} < 45`"
   ":code:`rhu2_00F_to_05F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`0 \leq T_{out} < 5`"
   ":code:`rhu2_05F_to_10F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`5 \leq T_{out} < 10`"
   ":code:`rhu2_10F_to_15F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`10 \leq T_{out} < 15`"
   ":code:`rhu2_15F_to_20F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`15 \leq T_{out} < 20`"
   ":code:`rhu2_20F_to_25F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`20 \leq T_{out} < 25`"
   ":code:`rhu2_25F_to_30F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`25 \leq T_{out} < 30`"
   ":code:`rhu2_30F_to_35F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`30 \leq T_{out} < 35`"
   ":code:`rhu2_35F_to_40F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`35 \leq T_{out} < 40`"
   ":code:`rhu2_40F_to_45F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`40 \leq T_{out} < 45`"
   ":code:`rhu2_45F_to_50F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`45 \leq T_{out} < 50`"
   ":code:`rhu2_50F_to_55F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`50 \leq T_{out} < 55`"
   ":code:`rhu2_55F_to_60F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`55 \leq T_{out} < 60`"
   ":code:`rhu2_30F_to_45F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`30 \leq T_{out} < 45`"
   ":code:`rhu2IQFLT_00F_to_05F`","decmial","0.0=0%, 1.0=100%","RHU2 IQR filtered resistance heat utilization for hourly temperature bin :math:`0 \leq T_{out} < 5`"
   ":code:`rhu2IQFLT_05F_to_10F`","decmial","0.0=0%, 1.0=100%","RHU2 IQR filtered resistance heat utilization for hourly temperature bin :math:`5 \leq T_{out} < 10`"
   ":code:`rhu2IQFLT_10F_to_15F`","decmial","0.0=0%, 1.0=100%","RHU2 IQR filtered resistance heat utilization for hourly temperature bin :math:`10 \leq T_{out} < 15`"
   ":code:`rhu2IQFLT_15F_to_20F`","decmial","0.0=0%, 1.0=100%","RHU2 IQR filtered resistance heat utilization for hourly temperature bin :math:`15 \leq T_{out} < 20`"
   ":code:`rhu2IQFLT_20F_to_25F`","decmial","0.0=0%, 1.0=100%","RHU2 IQR filtered resistance heat utilization for hourly temperature bin :math:`20 \leq T_{out} < 25`"
   ":code:`rhu2IQFLT_25F_to_30F`","decmial","0.0=0%, 1.0=100%","RHU2 IQR filtered resistance heat utilization for hourly temperature bin :math:`25 \leq T_{out} < 30`"
   ":code:`rhu2IQFLT_30F_to_35F`","decmial","0.0=0%, 1.0=100%","RHU2 IQR filtered resistance heat utilization for hourly temperature bin :math:`30 \leq T_{out} < 35`"
   ":code:`rhu2IQFLT_35F_to_40F`","decmial","0.0=0%, 1.0=100%","RHU2 IQR filtered resistance heat utilization for hourly temperature bin :math:`35 \leq T_{out} < 40`"
   ":code:`rhu2IQFLT_40F_to_45F`","decmial","0.0=0%, 1.0=100%","RHU2 IQR filtered resistance heat utilization for hourly temperature bin :math:`40 \leq T_{out} < 45`"
   ":code:`rhu2IQFLT_45F_to_50F`","decmial","0.0=0%, 1.0=100%","RHU2 IQR filtered resistance heat utilization for hourly temperature bin :math:`45 \leq T_{out} < 50`"
   ":code:`rhu2IQFLT_50F_to_55F`","decmial","0.0=0%, 1.0=100%","RHU2 IQR filtered resistance heat utilization for hourly temperature bin :math:`50 \leq T_{out} < 55`"
   ":code:`rhu2IQFLT_55F_to_60F`","decmial","0.0=0%, 1.0=100%","RHU2 IQR filtered resistance heat utilization for hourly temperature bin :math:`55 \leq T_{out} < 60`"
   ":code:`rhu2IQFLT_30F_to_45F`","decmial","0.0=0%, 1.0=100%","RHU2 IQR filtered resistance heat utilization for hourly temperature bin :math:`30 \leq T_{out} < 45`"


.. _thermostat-output-statistics:

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
   ":code:`###_1q`","q1 (q=quantile)"
   ":code:`###_2.5q`","q2.5"
   ":code:`###_5q`","q5"
   ":code:`###_10q`","q10"
   ":code:`###_15q`","q15"
   ":code:`###_20q`","q20"
   ":code:`###_25q`","q25"
   ":code:`###_30q`","q30"
   ":code:`###_35q`","q35"
   ":code:`###_40q`","q40"
   ":code:`###_45q`","q45"
   ":code:`###_50q`","q50"
   ":code:`###_55q`","q55"
   ":code:`###_60q`","q60"
   ":code:`###_65q`","q65"
   ":code:`###_70q`","q70"
   ":code:`###_75q`","q75"
   ":code:`###_80q`","q80"
   ":code:`###_85q`","q85"
   ":code:`###_90q`","q90"
   ":code:`###_95q`","q95"
   ":code:`###_98q`","q98"
   ":code:`###_99q`","q99"

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


.. _thermostat-output-certification:

Certification File
~~~~~~~~~~~~~~~~~~

The following file is output for certification:

Columns
```````

.. csv-table::
   :header: "Name", "Description"

    ":code:`product_id`","Product ID"
    ":code:`sw_version`","Software Version"
    ":code:`metric`","Metric (:code:`percent_savings_baseline_percentile` or :code:`rhu_30F_to_45F`)"
    ":code:`filter`","Filter Used (:code:`tau_cvrmse_savings_p01`)"
    ":code:`region`","Region (:code:`national_weighted_mean` or :code:`all`)"
    ":code:`statistic`","Statistic (:code:`lower_bound_95` (95% confidence lower bound on mean value), :code:`q20` (20th percentile) or :code:`upper_bound_95` (95% confidence upper bound on mean value))"
    ":code:`season`","Season (:code:`heating` or :code:`cooling`)"
    ":code:`value`","Value"

National weighted percent savings are computed by weighted average of percent savings results
grouped by climate zone. Heavier weights are applied to results in climate
zones which tend to have longer runtimes. Weightings used are
available :download:`for download <../thermostat/resources/NationalAverageClimateZoneWeightings.csv>`.

.. _ZCTA: http://www.census.gov/programs-surveys/geography/guidance/geo-areas/zctas.html
.. _eeweather ZCTA to latitide / longitude conversion: http://eeweather.openee.io/en/latest/advanced.html#zcta-to-latitude-longitude-conversion
.. _eeweather: http://eeweather.openee.io/en/latest/index.html 
