Data Files
==========


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
   "**Core mean temperatures**"
   ":code:`core_cooling_days_mean_indoor_temperature`","float","°F","Mean of core cooling days indoor temperature"
   ":code:`core_cooling_days_mean_outdoor_temperature`","float","°F","Mean of core cooling days outdoor temperature"
   ":code:`core_heating_days_mean_indoor_temperature`","float","°F","Mean of heating days indoor temperature"
   ":code:`core_heating_days_mean_outdoor_temperature`","float","°F","Mean of heating days outdoor temperature"
   ":code:`core_mean_indoor_temperature`","float","°F","Mean of indoor temperature"
   ":code:`core_mean_outdoor_temperature`","float","°F","Mean of outdoor temperature"
   "**Resistance heat outputs**"
   ":code:`rhu1_aux_duty_cycle`","float","minutes","Resistance heat utilization auxiliary duty cycle"
   ":code:`rhu1_emg_duty_cycle`","float","minutes","Resistance heat utilization emergency duty cycle"
   ":code:`rhu1_compressor_duty_cycle`","float","minutes","Resistance heat utilization compressor duty cycle"
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
   ":code:`rhu1_00F_to_05F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`0 \leq \frac{T_{aux}}{T_{out}} < 5`"
   ":code:`rhu1_05F_to_10F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`5 \leq \frac{T_{aux}}{T_{out}} < 10`"
   ":code:`rhu1_10F_to_15F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`10 \leq \frac{T_{aux}}{T_{out}} < 15`"
   ":code:`rhu1_15F_to_20F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`15 \leq \frac{T_{aux}}{T_{out}} < 20`"
   ":code:`rhu1_20F_to_25F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`20 \leq \frac{T_{aux}}{T_{out}} < 25`"
   ":code:`rhu1_25F_to_30F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`25 \leq \frac{T_{aux}}{T_{out}} < 30`"
   ":code:`rhu1_30F_to_35F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`30 \leq \frac{T_{aux}}{T_{out}} < 35`"
   ":code:`rhu1_35F_to_40F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`35 \leq \frac{T_{aux}}{T_{out}} < 40`"
   ":code:`rhu1_40F_to_45F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`40 \leq \frac{T_{aux}}{T_{out}}< 45`"
   ":code:`rhu1_45F_to_50F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`45 \leq \frac{T_{aux}}{T_{out}} < 50`"
   ":code:`rhu1_50F_to_55F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`50 \leq \frac{T_{aux}}{T_{out}} < 55`"
   ":code:`rhu1_55F_to_60F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`0 \leq \frac{T_{aux}}{T_{out}} < 5`"
   ":code:`rhu1_00F_to_05F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`0 \leq \frac{T_{emerg}}{T_{out}} < 5`"
   ":code:`rhu1_05F_to_10F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`5 \leq \frac{T_{emerg}}{T_{out}} < 10`"
   ":code:`rhu1_10F_to_15F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`10 \leq \frac{T_{emerg}}{T_{out}} < 15`"
   ":code:`rhu1_15F_to_20F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`15 \leq \frac{T_{emerg}}{T_{out}} < 20`"
   ":code:`rhu1_20F_to_25F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`20 \leq \frac{T_{emerg}}{T_{out}} < 25`"
   ":code:`rhu1_25F_to_30F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`25 \leq \frac{T_{emerg}}{T_{out}} < 30`"
   ":code:`rhu1_30F_to_35F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`30 \leq \frac{T_{emerg}}{T_{out}} < 35`"
   ":code:`rhu1_35F_to_40F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`35 \leq \frac{T_{emerg}}{T_{out}} < 40`"
   ":code:`rhu1_40F_to_45F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`40 \leq \frac{T_{emerg}}{T_{out}} < 45`"
   ":code:`rhu1_45F_to_50F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`45 \leq \frac{T_{emerg}}{T_{out}} < 50`"
   ":code:`rhu1_50F_to_55F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`50 \leq \frac{T_{emerg}}{T_{out}} < 55`"
   ":code:`rhu1_55F_to_60F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`55 \leq \frac{T_{emerg}}{T_{out}} < 60`"
   ":code:`rhu1_00F_to_05F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`0 \leq \frac{T_{comp}}{T_{out}} < 5`"
   ":code:`rhu1_05F_to_10F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`5 \leq \frac{T_{comp}}{T_{out}} < 10`"
   ":code:`rhu1_10F_to_15F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`10 \leq \frac{T_{comp}}{T_{out}} < 15`"
   ":code:`rhu1_15F_to_20F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`15 \leq \frac{T_{comp}}{T_{out}} < 20`"
   ":code:`rhu1_20F_to_25F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`20 \leq \frac{T_{comp}}{T_{out}} < 25`"
   ":code:`rhu1_25F_to_30F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`25 \leq \frac{T_{comp}}{T_{out}} < 30`"
   ":code:`rhu1_30F_to_35F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`30 \leq \frac{T_{comp}}{T_{out}} < 35`"
   ":code:`rhu1_35F_to_40F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`35 \leq \frac{T_{comp}}{T_{out}} < 40`"
   ":code:`rhu1_40F_to_45F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`40 \leq \frac{T_{comp}}{T_{out}} < 45`"
   ":code:`rhu1_45F_to_50F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`45 \leq \frac{T_{comp}}{T_{out}} < 50`"
   ":code:`rhu1_50F_to_55F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`50 \leq \frac{T_{comp}}{T_{out}} < 55`"
   ":code:`rhu1_55F_to_60F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`55 \leq \frac{T_{comp}}{T_{out}} < 60`"
   ":code:`rhu1_less10F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`0 \leq T_{out} < 10`"
   ":code:`rhu1_10F_to_20F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`10 \leq T_{out} < 20`"
   ":code:`rhu1_20F_to_30F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`20 \leq T_{out} < 30`"
   ":code:`rhu1_30F_to_40F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`30 \leq T_{out} < 40`"
   ":code:`rhu1_40F_to_50F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`40 \leq T_{out} < 50`"
   ":code:`rhu1_50F_to_60F`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`50 \leq T_{out} < 60`"
   ":code:`rhu1_less10F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`0 \leq \frac{T_{aux}}{T_{out}}  < 10`"
   ":code:`rhu1_10F_to_20F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`10 \leq \frac{T_{aux}}{T_{out}} < 20`"
   ":code:`rhu1_20F_to_30F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`20 \leq \frac{T_{aux}}{T_{out}} < 30`"
   ":code:`rhu1_30F_to_40F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`30 \leq \frac{T_{aux}}{T_{out}} < 40`"
   ":code:`rhu1_40F_to_50F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`40 \leq \frac{T_{aux}}{T_{out}} < 50`"
   ":code:`rhu1_50F_to_60F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`50 \leq \frac{T_{aux}}{T_{out}} < 60`"
   ":code:`rhu1_less10F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`0 \leq \frac{T_{emerg}}{T_{out}}  < 10`"
   ":code:`rhu1_10F_to_20F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`10 \leq \frac{T_{emerg}}{T_{out}} < 20`"
   ":code:`rhu1_20F_to_30F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`20 \leq \frac{T_{emerg}}{T_{out}} < 30`"
   ":code:`rhu1_30F_to_40F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`30 \leq \frac{T_{emerg}}{T_{out}} < 40`"
   ":code:`rhu1_40F_to_50F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`40 \leq \frac{T_{emerg}}{T_{out}} < 50`"
   ":code:`rhu1_50F_to_60F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`50 \leq \frac{T_{emerg}}{T_{out}} < 60`"
   ":code:`rhu1_less10F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`0 \leq \frac{T_{comp}}{T_{out}}  < 10`"
   ":code:`rhu1_10F_to_20F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`10 \leq \frac{T_{comp}}{T_{out}} < 20`"
   ":code:`rhu1_20F_to_30F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`20 \leq \frac{T_{comp}}{T_{out}} < 30`"
   ":code:`rhu1_30F_to_40F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`30 \leq \frac{T_{comp}}{T_{out}} < 40`"
   ":code:`rhu1_40F_to_50F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`40 \leq \frac{T_{comp}}{T_{out}} < 50`"
   ":code:`rhu1_50F_to_60F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","Resistance heat utilization for hourly temperature bin :math:`50 \leq \frac{T_{comp}}{T_{out}} < 60`"
   ":code:`rhu2_aux_duty_cycle`","float","minutes","Resistance heat utilization auxiliary duty cycle"
   ":code:`rhu2_emg_duty_cycle`","float","minutes","Resistance heat utilization emergency duty cycle"
   ":code:`rhu2_compressor_duty_cycle`","float","minutes","Resistance heat utilization compressor duty cycle"
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
   ":code:`rhu2_00F_to_05F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`0 \leq \frac{T_{aux}}{T_{out}} < 5`"
   ":code:`rhu2_05F_to_10F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`5 \leq \frac{T_{aux}}{T_{out}} < 10`"
   ":code:`rhu2_10F_to_15F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`10 \leq \frac{T_{aux}}{T_{out}} < 15`"
   ":code:`rhu2_15F_to_20F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`15 \leq \frac{T_{aux}}{T_{out}} < 20`"
   ":code:`rhu2_20F_to_25F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`20 \leq \frac{T_{aux}}{T_{out}} < 25`"
   ":code:`rhu2_25F_to_30F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`25 \leq \frac{T_{aux}}{T_{out}} < 30`"
   ":code:`rhu2_30F_to_35F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`30 \leq \frac{T_{aux}}{T_{out}} < 35`"
   ":code:`rhu2_35F_to_40F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`35 \leq \frac{T_{aux}}{T_{out}} < 40`"
   ":code:`rhu2_40F_to_45F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`40 \leq \frac{T_{aux}}{T_{out}}< 45`"
   ":code:`rhu2_45F_to_50F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`45 \leq \frac{T_{aux}}{T_{out}} < 50`"
   ":code:`rhu2_50F_to_55F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`50 \leq \frac{T_{aux}}{T_{out}} < 55`"
   ":code:`rhu2_55F_to_60F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`0 \leq \frac{T_{aux}}{T_{out}} < 5`"
   ":code:`rhu2_00F_to_05F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`0 \leq \frac{T_{emerg}}{T_{out}} < 5`"
   ":code:`rhu2_05F_to_10F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`5 \leq \frac{T_{emerg}}{T_{out}} < 10`"
   ":code:`rhu2_10F_to_15F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`10 \leq \frac{T_{emerg}}{T_{out}} < 15`"
   ":code:`rhu2_15F_to_20F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`15 \leq \frac{T_{emerg}}{T_{out}} < 20`"
   ":code:`rhu2_20F_to_25F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`20 \leq \frac{T_{emerg}}{T_{out}} < 25`"
   ":code:`rhu2_25F_to_30F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`25 \leq \frac{T_{emerg}}{T_{out}} < 30`"
   ":code:`rhu2_30F_to_35F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`30 \leq \frac{T_{emerg}}{T_{out}} < 35`"
   ":code:`rhu2_35F_to_40F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`35 \leq \frac{T_{emerg}}{T_{out}} < 40`"
   ":code:`rhu2_40F_to_45F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`40 \leq \frac{T_{emerg}}{T_{out}} < 45`"
   ":code:`rhu2_45F_to_50F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`45 \leq \frac{T_{emerg}}{T_{out}} < 50`"
   ":code:`rhu2_50F_to_55F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`50 \leq \frac{T_{emerg}}{T_{out}} < 55`"
   ":code:`rhu2_55F_to_60F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`55 \leq \frac{T_{emerg}}{T_{out}} < 60`"
   ":code:`rhu2_00F_to_05F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`0 \leq \frac{T_{comp}}{T_{out}} < 5`"
   ":code:`rhu2_05F_to_10F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`5 \leq \frac{T_{comp}}{T_{out}} < 10`"
   ":code:`rhu2_10F_to_15F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`10 \leq \frac{T_{comp}}{T_{out}} < 15`"
   ":code:`rhu2_15F_to_20F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`15 \leq \frac{T_{comp}}{T_{out}} < 20`"
   ":code:`rhu2_20F_to_25F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`20 \leq \frac{T_{comp}}{T_{out}} < 25`"
   ":code:`rhu2_25F_to_30F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`25 \leq \frac{T_{comp}}{T_{out}} < 30`"
   ":code:`rhu2_30F_to_35F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`30 \leq \frac{T_{comp}}{T_{out}} < 35`"
   ":code:`rhu2_35F_to_40F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`35 \leq \frac{T_{comp}}{T_{out}} < 40`"
   ":code:`rhu2_40F_to_45F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`40 \leq \frac{T_{comp}}{T_{out}} < 45`"
   ":code:`rhu2_45F_to_50F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`45 \leq \frac{T_{comp}}{T_{out}} < 50`"
   ":code:`rhu2_50F_to_55F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`50 \leq \frac{T_{comp}}{T_{out}} < 55`"
   ":code:`rhu2_55F_to_60F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`55 \leq \frac{T_{comp}}{T_{out}} < 60`"
   ":code:`rhu2_less10F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`0 \leq T_{out} < 10`"
   ":code:`rhu2_10F_to_20F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`10 \leq T_{out} < 20`"
   ":code:`rhu2_20F_to_30F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`20 \leq T_{out} < 30`"
   ":code:`rhu2_30F_to_40F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`30 \leq T_{out} < 40`"
   ":code:`rhu2_40F_to_50F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`40 \leq T_{out} < 50`"
   ":code:`rhu2_50F_to_60F`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`50 \leq T_{out} < 60`"
   ":code:`rhu2_less10F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`0 \leq \frac{T_{aux}}{T_{out}}  < 10`"
   ":code:`rhu2_10F_to_20F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`10 \leq \frac{T_{aux}}{T_{out}} < 20`"
   ":code:`rhu2_20F_to_30F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`20 \leq \frac{T_{aux}}{T_{out}} < 30`"
   ":code:`rhu2_30F_to_40F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`30 \leq \frac{T_{aux}}{T_{out}} < 40`"
   ":code:`rhu2_40F_to_50F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`40 \leq \frac{T_{aux}}{T_{out}} < 50`"
   ":code:`rhu2_50F_to_60F_aux_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`50 \leq \frac{T_{aux}}{T_{out}} < 60`"
   ":code:`rhu2_less10F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`0 \leq \frac{T_{emerg}}{T_{out}}  < 10`"
   ":code:`rhu2_10F_to_20F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`10 \leq \frac{T_{emerg}}{T_{out}} < 20`"
   ":code:`rhu2_20F_to_30F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`20 \leq \frac{T_{emerg}}{T_{out}} < 30`"
   ":code:`rhu2_30F_to_40F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`30 \leq \frac{T_{emerg}}{T_{out}} < 40`"
   ":code:`rhu2_40F_to_50F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`40 \leq \frac{T_{emerg}}{T_{out}} < 50`"
   ":code:`rhu2_50F_to_60F_emg_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`50 \leq \frac{T_{emerg}}{T_{out}} < 60`"
   ":code:`rhu2_less10F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`0 \leq \frac{T_{comp}}{T_{out}}  < 10`"
   ":code:`rhu2_10F_to_20F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`10 \leq \frac{T_{comp}}{T_{out}} < 20`"
   ":code:`rhu2_20F_to_30F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`20 \leq \frac{T_{comp}}{T_{out}} < 30`"
   ":code:`rhu2_30F_to_40F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`30 \leq \frac{T_{comp}}{T_{out}} < 40`"
   ":code:`rhu2_40F_to_50F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`40 \leq \frac{T_{comp}}{T_{out}} < 50`"
   ":code:`rhu2_50F_to_60F_compressor_duty_cycle`","decmial","0.0=0%, 1.0=100%","RHU2 filtered resistance heat utilization for hourly temperature bin :math:`50 \leq \frac{T_{comp}}{T_{out}} < 60`"


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
   ":code:`percent_savings_baseline_percentile_q1_national_weighted_mean`","National weighted 1st percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q2.5_national_weighted_mean`","National weighted 2.5th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q5_national_weighted_mean`","National weighted 5th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q10_national_weighted_mean`","National weighted 10th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q15_national_weighted_mean`","National weighted 15th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q20_national_weighted_mean`","National weighted 20th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q25_national_weighted_mean`","National weighted 25th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q30_national_weighted_mean`","National weighted 30th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q35_national_weighted_mean`","National weighted 35th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q40_national_weighted_mean`","National weighted 40th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q45_national_weighted_mean`","National weighted 45th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q50_national_weighted_mean`","National weighted 50th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q55_national_weighted_mean`","National weighted 55th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q60_national_weighted_mean`","National weighted 60th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q65_national_weighted_mean`","National weighted 65th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q70_national_weighted_mean`","National weighted 70th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q75_national_weighted_mean`","National weighted 75th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q80_national_weighted_mean`","National weighted 80th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q85_national_weighted_mean`","National weighted 85th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q90_national_weighted_mean`","National weighted 90th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q95_national_weighted_mean`","National weighted 95th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q98_national_weighted_mean`","National weighted 98th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_q99_national_weighted_mean`","National weighted 99th percentile percent savings as given by baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_lower_bound_95_perc_conf_national_weighted_mean`","National weighted mean percent savings lower bound as given by a 95% confidence interval and the baseline_percentile method."
   ":code:`percent_savings_baseline_percentile_upper_bound_95_perc_conf_national_weighted_mean`","National weighted mean percent savings upper bound as given by a 95% confidence interval and the baseline_percentile method."
   ":code:`percent_savings_baseline_regional_mean_national_weighted_mean`","National weighted mean percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q1_national_weighted_mean`","National weighted 1st percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q2.5_national_weighted_mean`","National weighted 2.5th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q5_national_weighted_mean`","National weighted 5th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q10_national_weighted_mean`","National weighted 10th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q15_national_weighted_mean`","National weighted 15th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q20_national_weighted_mean`","National weighted 20th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q25_national_weighted_mean`","National weighted 25th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q30_national_weighted_mean`","National weighted 30th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q35_national_weighted_mean`","National weighted 35th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q40_national_weighted_mean`","National weighted 40th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q45_national_weighted_mean`","National weighted 45th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q50_national_weighted_mean`","National weighted 50th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q55_national_weighted_mean`","National weighted 55th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q60_national_weighted_mean`","National weighted 60th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q65_national_weighted_mean`","National weighted 65th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q70_national_weighted_mean`","National weighted 70th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q75_national_weighted_mean`","National weighted 75th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q80_national_weighted_mean`","National weighted 80th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q85_national_weighted_mean`","National weighted 85th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q90_national_weighted_mean`","National weighted 90th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q95_national_weighted_mean`","National weighted 95th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q98_national_weighted_mean`","National weighted 98th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_q99_national_weighted_mean`","National weighted 99th percentile percent savings as given by baseline_regional method."
   ":code:`percent_savings_baseline_regional_lower_bound_95_perc_conf_national_weighted_mean`","National weighted mean percent savings lower bound as given by a 95% confidence interval and the baseline_regional method."
   ":code:`percent_savings_baseline_regional_upper_bound_95_perc_conf_national_weighted_mean`","National weighted mean percent savings upper bound as given by a 95% confidence interval and the baseline_regional method."
