from thermostat.stats import combine_output_dataframes
from thermostat.stats import compute_summary_statistics
from thermostat.stats import summary_statistics_to_csv
from .fixtures.thermostats import thermostat_emg_aux_constant_on_outlier
from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics
from thermostat.exporters import COLUMNS

from scipy.stats import norm, randint
import pandas as pd
import numpy as np
import json
from datetime import datetime

import tempfile
from itertools import islice, cycle

import pytest


def get_fake_output_df(n_columns):
    columns = [
        'sw_version',

        'ct_identifier',
        'equipment_type',
        'heating_or_cooling',
        'station',
        'zipcode',
        'climate_zone',

        'start_date',
        'end_date',

        'n_days_in_inputfile_date_range',
        'n_days_both_heating_and_cooling',
        'n_days_insufficient_data',
        'n_core_cooling_days',
        'n_core_heating_days',

        'baseline_percentile_core_cooling_comfort_temperature',
        'baseline_percentile_core_heating_comfort_temperature',
        'regional_average_baseline_cooling_comfort_temperature',
        'regional_average_baseline_heating_comfort_temperature',

        'percent_savings_baseline_percentile',
        'avoided_daily_mean_core_day_runtime_baseline_percentile',
        'avoided_total_core_day_runtime_baseline_percentile',
        'baseline_daily_mean_core_day_runtime_baseline_percentile',
        'baseline_total_core_day_runtime_baseline_percentile',
        '_daily_mean_core_day_demand_baseline_baseline_percentile',
        'percent_savings_baseline_regional',
        'avoided_daily_mean_core_day_runtime_baseline_regional',
        'avoided_total_core_day_runtime_baseline_regional',
        'baseline_daily_mean_core_day_runtime_baseline_regional',
        'baseline_total_core_day_runtime_baseline_regional',
        '_daily_mean_core_day_demand_baseline_baseline_regional',
        'mean_demand',
        'alpha',
        'tau',
        'mean_sq_err',
        'root_mean_sq_err',
        'cv_root_mean_sq_err',
        'mean_abs_err',
        'mean_abs_pct_err',

        'total_core_cooling_runtime',
        'total_core_heating_runtime',
        'total_auxiliary_heating_core_day_runtime',
        'total_emergency_heating_core_day_runtime',

        'daily_mean_core_cooling_runtime',
        'daily_mean_core_heating_runtime',

        'core_cooling_days_mean_indoor_temperature',
        'core_cooling_days_mean_outdoor_temperature',
        'core_heating_days_mean_indoor_temperature',
        'core_heating_days_mean_outdoor_temperature',
        'core_mean_indoor_temperature',
        'core_mean_outdoor_temperature',

        'rhu1_aux_duty_cycle',
        'rhu1_emg_duty_cycle',
        'rhu1_compressor_duty_cycle',

        'rhu1_00F_to_05F',
        'rhu1_05F_to_10F',
        'rhu1_10F_to_15F',
        'rhu1_15F_to_20F',
        'rhu1_20F_to_25F',
        'rhu1_25F_to_30F',
        'rhu1_30F_to_35F',
        'rhu1_35F_to_40F',
        'rhu1_40F_to_45F',
        'rhu1_45F_to_50F',
        'rhu1_50F_to_55F',
        'rhu1_55F_to_60F',

        'rhu1_less10F',
        'rhu1_10F_to_20F',
        'rhu1_20F_to_30F',
        'rhu1_30F_to_40F',
        'rhu1_40F_to_50F',
        'rhu1_50F_to_60F',

        'rhu1_00F_to_05F_aux_duty_cycle',
        'rhu1_05F_to_10F_aux_duty_cycle',
        'rhu1_10F_to_15F_aux_duty_cycle',
        'rhu1_15F_to_20F_aux_duty_cycle',
        'rhu1_20F_to_25F_aux_duty_cycle',
        'rhu1_25F_to_30F_aux_duty_cycle',
        'rhu1_30F_to_35F_aux_duty_cycle',
        'rhu1_35F_to_40F_aux_duty_cycle',
        'rhu1_40F_to_45F_aux_duty_cycle',
        'rhu1_45F_to_50F_aux_duty_cycle',
        'rhu1_50F_to_55F_aux_duty_cycle',
        'rhu1_55F_to_60F_aux_duty_cycle',

        'rhu1_less10F_aux_duty_cycle',
        'rhu1_10F_to_20F_aux_duty_cycle',
        'rhu1_20F_to_30F_aux_duty_cycle',
        'rhu1_30F_to_40F_aux_duty_cycle',
        'rhu1_40F_to_50F_aux_duty_cycle',
        'rhu1_50F_to_60F_aux_duty_cycle',

        'rhu1_00F_to_05F_emg_duty_cycle',
        'rhu1_05F_to_10F_emg_duty_cycle',
        'rhu1_10F_to_15F_emg_duty_cycle',
        'rhu1_15F_to_20F_emg_duty_cycle',
        'rhu1_20F_to_25F_emg_duty_cycle',
        'rhu1_25F_to_30F_emg_duty_cycle',
        'rhu1_30F_to_35F_emg_duty_cycle',
        'rhu1_35F_to_40F_emg_duty_cycle',
        'rhu1_40F_to_45F_emg_duty_cycle',
        'rhu1_45F_to_50F_emg_duty_cycle',
        'rhu1_50F_to_55F_emg_duty_cycle',
        'rhu1_55F_to_60F_emg_duty_cycle',

        'rhu1_less10F_emg_duty_cycle',
        'rhu1_10F_to_20F_emg_duty_cycle',
        'rhu1_20F_to_30F_emg_duty_cycle',
        'rhu1_30F_to_40F_emg_duty_cycle',
        'rhu1_40F_to_50F_emg_duty_cycle',
        'rhu1_50F_to_60F_emg_duty_cycle',

        'rhu1_00F_to_05F_compressor_duty_cycle',
        'rhu1_05F_to_10F_compressor_duty_cycle',
        'rhu1_10F_to_15F_compressor_duty_cycle',
        'rhu1_15F_to_20F_compressor_duty_cycle',
        'rhu1_20F_to_25F_compressor_duty_cycle',
        'rhu1_25F_to_30F_compressor_duty_cycle',
        'rhu1_30F_to_35F_compressor_duty_cycle',
        'rhu1_35F_to_40F_compressor_duty_cycle',
        'rhu1_40F_to_45F_compressor_duty_cycle',
        'rhu1_45F_to_50F_compressor_duty_cycle',
        'rhu1_50F_to_55F_compressor_duty_cycle',
        'rhu1_55F_to_60F_compressor_duty_cycle',

        'rhu1_less10F_compressor_duty_cycle',
        'rhu1_10F_to_20F_compressor_duty_cycle',
        'rhu1_20F_to_30F_compressor_duty_cycle',
        'rhu1_30F_to_40F_compressor_duty_cycle',
        'rhu1_40F_to_50F_compressor_duty_cycle',
        'rhu1_50F_to_60F_compressor_duty_cycle',

        'rhu2_aux_duty_cycle',
        'rhu2_emg_duty_cycle',
        'rhu2_compressor_duty_cycle',

        'rhu2_00F_to_05F',
        'rhu2_05F_to_10F',
        'rhu2_10F_to_15F',
        'rhu2_15F_to_20F',
        'rhu2_20F_to_25F',
        'rhu2_25F_to_30F',
        'rhu2_30F_to_35F',
        'rhu2_35F_to_40F',
        'rhu2_40F_to_45F',
        'rhu2_45F_to_50F',
        'rhu2_50F_to_55F',
        'rhu2_55F_to_60F',

        'rhu2_less10F',
        'rhu2_10F_to_20F',
        'rhu2_20F_to_30F',
        'rhu2_30F_to_40F',
        'rhu2_40F_to_50F',
        'rhu2_50F_to_60F',

        'rhu2_00F_to_05F_aux_duty_cycle',
        'rhu2_05F_to_10F_aux_duty_cycle',
        'rhu2_10F_to_15F_aux_duty_cycle',
        'rhu2_15F_to_20F_aux_duty_cycle',
        'rhu2_20F_to_25F_aux_duty_cycle',
        'rhu2_25F_to_30F_aux_duty_cycle',
        'rhu2_30F_to_35F_aux_duty_cycle',
        'rhu2_35F_to_40F_aux_duty_cycle',
        'rhu2_40F_to_45F_aux_duty_cycle',
        'rhu2_45F_to_50F_aux_duty_cycle',
        'rhu2_50F_to_55F_aux_duty_cycle',
        'rhu2_55F_to_60F_aux_duty_cycle',

        'rhu2_less10F_aux_duty_cycle',
        'rhu2_10F_to_20F_aux_duty_cycle',
        'rhu2_20F_to_30F_aux_duty_cycle',
        'rhu2_30F_to_40F_aux_duty_cycle',
        'rhu2_40F_to_50F_aux_duty_cycle',
        'rhu2_50F_to_60F_aux_duty_cycle',

        'rhu2_00F_to_05F_emg_duty_cycle',
        'rhu2_05F_to_10F_emg_duty_cycle',
        'rhu2_10F_to_15F_emg_duty_cycle',
        'rhu2_15F_to_20F_emg_duty_cycle',
        'rhu2_20F_to_25F_emg_duty_cycle',
        'rhu2_25F_to_30F_emg_duty_cycle',
        'rhu2_30F_to_35F_emg_duty_cycle',
        'rhu2_35F_to_40F_emg_duty_cycle',
        'rhu2_40F_to_45F_emg_duty_cycle',
        'rhu2_45F_to_50F_emg_duty_cycle',
        'rhu2_50F_to_55F_emg_duty_cycle',
        'rhu2_55F_to_60F_emg_duty_cycle',

        'rhu2_less10F_emg_duty_cycle',
        'rhu2_10F_to_20F_emg_duty_cycle',
        'rhu2_20F_to_30F_emg_duty_cycle',
        'rhu2_30F_to_40F_emg_duty_cycle',
        'rhu2_40F_to_50F_emg_duty_cycle',
        'rhu2_50F_to_60F_emg_duty_cycle',

        'rhu2_00F_to_05F_compressor_duty_cycle',
        'rhu2_05F_to_10F_compressor_duty_cycle',
        'rhu2_10F_to_15F_compressor_duty_cycle',
        'rhu2_15F_to_20F_compressor_duty_cycle',
        'rhu2_20F_to_25F_compressor_duty_cycle',
        'rhu2_25F_to_30F_compressor_duty_cycle',
        'rhu2_30F_to_35F_compressor_duty_cycle',
        'rhu2_35F_to_40F_compressor_duty_cycle',
        'rhu2_40F_to_45F_compressor_duty_cycle',
        'rhu2_45F_to_50F_compressor_duty_cycle',
        'rhu2_50F_to_55F_compressor_duty_cycle',
        'rhu2_55F_to_60F_compressor_duty_cycle',

        'rhu2_less10F_compressor_duty_cycle',
        'rhu2_10F_to_20F_compressor_duty_cycle',
        'rhu2_20F_to_30F_compressor_duty_cycle',
        'rhu2_30F_to_40F_compressor_duty_cycle',
        'rhu2_40F_to_50F_compressor_duty_cycle',
        'rhu2_50F_to_60F_compressor_duty_cycle',

    ]

    string_placeholder = ["PLACEHOLDER"] * n_columns
    zero_column = [0 if randint.rvs(0, 30) > 0 else  (None if randint.rvs(0, 2) > 0 else np.inf)
            for i in randint.rvs(0, 1, size=n_columns)]
    one_column = [1 if randint.rvs(0, 30) > 0 else  (None if randint.rvs(0, 2) > 0 else np.inf)
            for i in randint.rvs(0, 1, size=n_columns)]
    float_column = [i if randint.rvs(0, 30) > 0 else (None if randint.rvs(0, 2) > 0 else np.inf)
            for i in norm.rvs(size=n_columns)]
    zipcodes = ["01234", "12345", "23456", "34567", "43210", "54321", "65432", "76543"]
    zipcode_column = [i for i in islice(cycle(zipcodes), None, n_columns)]
    core_day_set_names = ["cooling_2012", "heating_2012-2013", "cooling_2013"]
    core_day_set_name_column = [i for i in islice(cycle(core_day_set_names), None, n_columns)]

    data = {
        'sw_version': string_placeholder,

        'ct_identifier': string_placeholder,
        'equipment_type': string_placeholder,
        'heating_or_cooling': core_day_set_name_column,
        'station': string_placeholder,
        'zipcode': zipcode_column,
        'climate_zone': string_placeholder,

        'start_date': datetime(2011, 1, 1),
        'end_date': datetime(2012, 1, 1),
        'n_days_both_heating_and_cooling': one_column,
        'n_days_in_inputfile_date_range': one_column,
        'n_days_insufficient_data': zero_column,
        'n_core_heating_days': one_column,

        'baseline_percentile_core_cooling_comfort_temperature': float_column,
        'baseline_percentile_core_heating_comfort_temperature': float_column,
        'regional_average_baseline_cooling_comfort_temperature': float_column,
        'regional_average_baseline_heating_comfort_temperature': float_column,

        'percent_savings_baseline_percentile': float_column,
        'avoided_daily_mean_core_day_runtime_baseline_percentile': float_column,
        'avoided_total_core_day_runtime_baseline_percentile': float_column,
        'baseline_daily_mean_core_day_runtime_baseline_percentile': float_column,
        'baseline_total_core_day_runtime_baseline_percentile': float_column,
        '_daily_mean_core_day_demand_baseline_baseline_percentile': float_column,
        'percent_savings_baseline_regional': float_column,
        'avoided_daily_mean_core_day_runtime_baseline_regional': float_column,
        'avoided_total_core_day_runtime_baseline_regional': float_column,
        'baseline_daily_mean_core_day_runtime_baseline_regional': float_column,
        'baseline_total_core_day_runtime_baseline_regional': float_column,
        '_daily_mean_core_day_demand_baseline_baseline_regional': float_column,
        'mean_demand': float_column,
        'alpha': float_column,
        'tau': float_column,
        'mean_sq_err': float_column,
        'root_mean_sq_err': float_column,
        'cv_root_mean_sq_err': float_column,
        'mean_abs_err': float_column,
        'mean_abs_pct_err': float_column,

        'total_core_cooling_runtime': float_column,
        'total_core_heating_runtime': float_column,
        'total_auxiliary_heating_core_day_runtime': float_column,
        'total_emergency_heating_core_day_runtime': float_column,

        'daily_mean_core_cooling_runtime': float_column,
        'daily_mean_core_heating_runtime': float_column,

        'core_cooling_days_mean_indoor_temperature': float_column,
        'core_cooling_days_mean_outdoor_temperature': float_column,
        'core_heating_days_mean_indoor_temperature': float_column,
        'core_heating_days_mean_outdoor_temperature': float_column,
        'core_mean_indoor_temperature': float_column,
        'core_mean_outdoor_temperature': float_column,

        'rhu1_aux_duty_cycle': float_column,
        'rhu1_emg_duty_cycle': float_column,
        'rhu1_compressor_duty_cycle': float_column,

        'rhu1_00F_to_05F': float_column,
        'rhu1_05F_to_10F': float_column,
        'rhu1_10F_to_15F': float_column,
        'rhu1_15F_to_20F': float_column,
        'rhu1_20F_to_25F': float_column,
        'rhu1_25F_to_30F': float_column,
        'rhu1_30F_to_35F': float_column,
        'rhu1_35F_to_40F': float_column,
        'rhu1_40F_to_45F': float_column,
        'rhu1_45F_to_50F': float_column,
        'rhu1_50F_to_55F': float_column,
        'rhu1_55F_to_60F': float_column,

        'rhu1_less10F': float_column,
        'rhu1_10F_to_20F': float_column,
        'rhu1_20F_to_30F': float_column,
        'rhu1_30F_to_40F': float_column,
        'rhu1_40F_to_50F': float_column,
        'rhu1_50F_to_60F': float_column,

        'rhu1_00F_to_05F_aux_duty_cycle': float_column,
        'rhu1_05F_to_10F_aux_duty_cycle': float_column,
        'rhu1_10F_to_15F_aux_duty_cycle': float_column,
        'rhu1_15F_to_20F_aux_duty_cycle': float_column,
        'rhu1_20F_to_25F_aux_duty_cycle': float_column,
        'rhu1_25F_to_30F_aux_duty_cycle': float_column,
        'rhu1_30F_to_35F_aux_duty_cycle': float_column,
        'rhu1_35F_to_40F_aux_duty_cycle': float_column,
        'rhu1_40F_to_45F_aux_duty_cycle': float_column,
        'rhu1_45F_to_50F_aux_duty_cycle': float_column,
        'rhu1_50F_to_55F_aux_duty_cycle': float_column,
        'rhu1_55F_to_60F_aux_duty_cycle': float_column,

        'rhu1_less10F_aux_duty_cycle': float_column,
        'rhu1_10F_to_20F_aux_duty_cycle': float_column,
        'rhu1_20F_to_30F_aux_duty_cycle': float_column,
        'rhu1_30F_to_40F_aux_duty_cycle': float_column,
        'rhu1_40F_to_50F_aux_duty_cycle': float_column,
        'rhu1_50F_to_60F_aux_duty_cycle': float_column,

        'rhu1_00F_to_05F_emg_duty_cycle': float_column,
        'rhu1_05F_to_10F_emg_duty_cycle': float_column,
        'rhu1_10F_to_15F_emg_duty_cycle': float_column,
        'rhu1_15F_to_20F_emg_duty_cycle': float_column,
        'rhu1_20F_to_25F_emg_duty_cycle': float_column,
        'rhu1_25F_to_30F_emg_duty_cycle': float_column,
        'rhu1_30F_to_35F_emg_duty_cycle': float_column,
        'rhu1_35F_to_40F_emg_duty_cycle': float_column,
        'rhu1_40F_to_45F_emg_duty_cycle': float_column,
        'rhu1_45F_to_50F_emg_duty_cycle': float_column,
        'rhu1_50F_to_55F_emg_duty_cycle': float_column,
        'rhu1_55F_to_60F_emg_duty_cycle': float_column,

        'rhu1_less10F_emg_duty_cycle': float_column,
        'rhu1_10F_to_20F_emg_duty_cycle': float_column,
        'rhu1_20F_to_30F_emg_duty_cycle': float_column,
        'rhu1_30F_to_40F_emg_duty_cycle': float_column,
        'rhu1_40F_to_50F_emg_duty_cycle': float_column,
        'rhu1_50F_to_60F_emg_duty_cycle': float_column,

        'rhu1_00F_to_05F_compressor_duty_cycle': float_column,
        'rhu1_05F_to_10F_compressor_duty_cycle': float_column,
        'rhu1_10F_to_15F_compressor_duty_cycle': float_column,
        'rhu1_15F_to_20F_compressor_duty_cycle': float_column,
        'rhu1_20F_to_25F_compressor_duty_cycle': float_column,
        'rhu1_25F_to_30F_compressor_duty_cycle': float_column,
        'rhu1_30F_to_35F_compressor_duty_cycle': float_column,
        'rhu1_35F_to_40F_compressor_duty_cycle': float_column,
        'rhu1_40F_to_45F_compressor_duty_cycle': float_column,
        'rhu1_45F_to_50F_compressor_duty_cycle': float_column,
        'rhu1_50F_to_55F_compressor_duty_cycle': float_column,
        'rhu1_55F_to_60F_compressor_duty_cycle': float_column,

        'rhu1_less10F_compressor_duty_cycle': float_column,
        'rhu1_10F_to_20F_compressor_duty_cycle': float_column,
        'rhu1_20F_to_30F_compressor_duty_cycle': float_column,
        'rhu1_30F_to_40F_compressor_duty_cycle': float_column,
        'rhu1_40F_to_50F_compressor_duty_cycle': float_column,
        'rhu1_50F_to_60F_compressor_duty_cycle': float_column,

        'rhu2_aux_duty_cycle': float_column,
        'rhu2_emg_duty_cycle': float_column,
        'rhu2_compressor_duty_cycle': float_column,

        'rhu2_00F_to_05F': float_column,
        'rhu2_05F_to_10F': float_column,
        'rhu2_10F_to_15F': float_column,
        'rhu2_15F_to_20F': float_column,
        'rhu2_20F_to_25F': float_column,
        'rhu2_25F_to_30F': float_column,
        'rhu2_30F_to_35F': float_column,
        'rhu2_35F_to_40F': float_column,
        'rhu2_40F_to_45F': float_column,
        'rhu2_45F_to_50F': float_column,
        'rhu2_50F_to_55F': float_column,
        'rhu2_55F_to_60F': float_column,

        'rhu2_less10F': float_column,
        'rhu2_10F_to_20F': float_column,
        'rhu2_20F_to_30F': float_column,
        'rhu2_30F_to_40F': float_column,
        'rhu2_40F_to_50F': float_column,
        'rhu2_50F_to_60F': float_column,

        'rhu2_00F_to_05F_aux_duty_cycle': float_column,
        'rhu2_05F_to_10F_aux_duty_cycle': float_column,
        'rhu2_10F_to_15F_aux_duty_cycle': float_column,
        'rhu2_15F_to_20F_aux_duty_cycle': float_column,
        'rhu2_20F_to_25F_aux_duty_cycle': float_column,
        'rhu2_25F_to_30F_aux_duty_cycle': float_column,
        'rhu2_30F_to_35F_aux_duty_cycle': float_column,
        'rhu2_35F_to_40F_aux_duty_cycle': float_column,
        'rhu2_40F_to_45F_aux_duty_cycle': float_column,
        'rhu2_45F_to_50F_aux_duty_cycle': float_column,
        'rhu2_50F_to_55F_aux_duty_cycle': float_column,
        'rhu2_55F_to_60F_aux_duty_cycle': float_column,

        'rhu2_less10F_aux_duty_cycle': float_column,
        'rhu2_10F_to_20F_aux_duty_cycle': float_column,
        'rhu2_20F_to_30F_aux_duty_cycle': float_column,
        'rhu2_30F_to_40F_aux_duty_cycle': float_column,
        'rhu2_40F_to_50F_aux_duty_cycle': float_column,
        'rhu2_50F_to_60F_aux_duty_cycle': float_column,

        'rhu2_00F_to_05F_emg_duty_cycle': float_column,
        'rhu2_05F_to_10F_emg_duty_cycle': float_column,
        'rhu2_10F_to_15F_emg_duty_cycle': float_column,
        'rhu2_15F_to_20F_emg_duty_cycle': float_column,
        'rhu2_20F_to_25F_emg_duty_cycle': float_column,
        'rhu2_25F_to_30F_emg_duty_cycle': float_column,
        'rhu2_30F_to_35F_emg_duty_cycle': float_column,
        'rhu2_35F_to_40F_emg_duty_cycle': float_column,
        'rhu2_40F_to_45F_emg_duty_cycle': float_column,
        'rhu2_45F_to_50F_emg_duty_cycle': float_column,
        'rhu2_50F_to_55F_emg_duty_cycle': float_column,
        'rhu2_55F_to_60F_emg_duty_cycle': float_column,

        'rhu2_less10F_emg_duty_cycle': float_column,
        'rhu2_10F_to_20F_emg_duty_cycle': float_column,
        'rhu2_20F_to_30F_emg_duty_cycle': float_column,
        'rhu2_30F_to_40F_emg_duty_cycle': float_column,
        'rhu2_40F_to_50F_emg_duty_cycle': float_column,
        'rhu2_50F_to_60F_emg_duty_cycle': float_column,

        'rhu2_00F_to_05F_compressor_duty_cycle': float_column,
        'rhu2_05F_to_10F_compressor_duty_cycle': float_column,
        'rhu2_10F_to_15F_compressor_duty_cycle': float_column,
        'rhu2_15F_to_20F_compressor_duty_cycle': float_column,
        'rhu2_20F_to_25F_compressor_duty_cycle': float_column,
        'rhu2_25F_to_30F_compressor_duty_cycle': float_column,
        'rhu2_30F_to_35F_compressor_duty_cycle': float_column,
        'rhu2_35F_to_40F_compressor_duty_cycle': float_column,
        'rhu2_40F_to_45F_compressor_duty_cycle': float_column,
        'rhu2_45F_to_50F_compressor_duty_cycle': float_column,
        'rhu2_50F_to_55F_compressor_duty_cycle': float_column,
        'rhu2_55F_to_60F_compressor_duty_cycle': float_column,

        'rhu2_less10F_compressor_duty_cycle': float_column,
        'rhu2_10F_to_20F_compressor_duty_cycle': float_column,
        'rhu2_20F_to_30F_compressor_duty_cycle': float_column,
        'rhu2_30F_to_40F_compressor_duty_cycle': float_column,
        'rhu2_40F_to_50F_compressor_duty_cycle': float_column,
        'rhu2_50F_to_60F_compressor_duty_cycle': float_column,
    }
    df = pd.DataFrame(data, columns=columns)
    return df


@pytest.fixture
def dataframes():
    df1 = get_fake_output_df(10)
    df2 = get_fake_output_df(10)
    dfs = [df1, df2]
    return dfs


@pytest.fixture
def combined_dataframe():
    df = get_fake_output_df(100)
    return df


def test_combine_output_dataframes(dataframes):
    combined = combine_output_dataframes(dataframes)
    assert combined.shape == (20, 200)


def test_compute_summary_statistics(combined_dataframe):
    summary_statistics = compute_summary_statistics(combined_dataframe)
    assert [len(s) for s in summary_statistics] == [
            49, 49, 49, 49,
            9105, 901, 9105, 901,
            ]

    def test_compute_summary_statistics_advanced(combined_dataframe):
        summary_statistics = compute_summary_statistics(combined_dataframe,
                advanced_filtering=True)
        assert [len(s) for s in summary_statistics] == [
                49, 49, 49, 49, 49, 49, 49, 49,
                9105, 901, 9105, 901, 9105, 901, 9105, 901,
                ]

        def test_summary_statistics_to_csv(combined_dataframe):
            summary_statistics = compute_summary_statistics(combined_dataframe)

    _, fname = tempfile.mkstemp()
    product_id = "FAKE"
    stats_df = summary_statistics_to_csv(summary_statistics, fname, product_id)
    assert isinstance(stats_df, pd.DataFrame)

    stats_df_reread = pd.read_csv(fname)
    assert stats_df_reread.shape == (9241, 9)


def test_iqr_filteringa(thermostat_emg_aux_constant_on_outlier):

    thermostats_iqflt = list(thermostat_emg_aux_constant_on_outlier)
    # Run the metrics / statistics with the outlier thermostat in place
    iqflt_metrics = multiple_thermostat_calculate_epa_field_savings_metrics(thermostats_iqflt)
    iqflt_output_dataframe = pd.DataFrame(iqflt_metrics, columns=COLUMNS)
    iqflt_summary_statistics = compute_summary_statistics(iqflt_output_dataframe)

    # Remove the outlier thermostat
    thermostats_noiq = []
    for thermostat in list(thermostats_iqflt):
        if thermostat.thermostat_id != 'thermostat_single_emg_aux_constant_on_outlier':
            thermostats_noiq.append(thermostat)

    if len(thermostats_noiq) == 5:
        raise ValueError("Try again")

    # Re-run the metrics / statistics with the outlier thermostat removed
    noiq_metrics = multiple_thermostat_calculate_epa_field_savings_metrics(thermostats_noiq)
    noiq_output_dataframe = pd.DataFrame(noiq_metrics, columns=COLUMNS)
    noiq_summary_statistics = compute_summary_statistics(noiq_output_dataframe)

    # Verify that the IQFLT removed the outliers by comparing this with the
    # metrics with the outlier thermostat already removed.
    for column in range(0, len(iqflt_summary_statistics)):
        fields_iqflt = [x for x in iqflt_summary_statistics[column] if '_IQFLT' in x]
        for field_iqflt in fields_iqflt:
            field_noiq = field_iqflt.replace('IQFLT', 'NOIQ')
            left_side = iqflt_summary_statistics[column][field_iqflt]
            right_side = noiq_summary_statistics[column][field_noiq]

            if np.isnan(left_side) or np.isnan(right_side):
                assert(np.isnan(left_side) and np.isnan(right_side))
            else:
                assert(left_side == right_side)
