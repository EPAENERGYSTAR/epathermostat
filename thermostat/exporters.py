import pandas as pd

def seasonal_metrics_to_csv(seasonal_metrics, filepath):
    """ Writes seasonal metrics outputs to the file specified.

    Parameters
    ----------
    seaonal_metrics : list of dict
        list of outputs from the function
        `thermostat.calculate_epa_draft_rccs_field_savings_metrics()`
    filepath : str
        filepath specification for location of output CSV file.

    Returns
    -------
    df : pd.DataFrame
        DataFrame containing data output to CSV.

    """

    columns = [
        'ct_identifier',
        'equipment_type',
        'season_name',
        'station',
        'zipcode',

        'n_days_in_season_range',
        'n_days_in_season',
        'n_days_both_heating_and_cooling',
        'n_days_insufficient_data',

        'percent_savings_deltaT',
        'avoided_daily_runtime_deltaT',
        'avoided_seasonal_runtime_deltaT',
        'baseline_daily_runtime_deltaT',
        'baseline_seasonal_runtime_deltaT',
        'mean_demand_deltaT',
        'mean_demand_baseline_deltaT',
        'alpha_deltaT',
        'tau_deltaT',
        'mean_sq_err_deltaT',
        'root_mean_sq_err_deltaT',
        'cv_root_mean_sq_err_deltaT',
        'mean_abs_err_deltaT',
        'mean_abs_pct_err_deltaT',

        'percent_savings_dailyavgCDD',
        'avoided_daily_runtime_dailyavgCDD',
        'avoided_seasonal_runtime_dailyavgCDD',
        'baseline_daily_runtime_dailyavgCDD',
        'baseline_seasonal_runtime_dailyavgCDD',
        'mean_demand_dailyavgCDD',
        'mean_demand_baseline_dailyavgCDD',
        'alpha_dailyavgCDD',
        'tau_dailyavgCDD',
        'mean_sq_err_dailyavgCDD',
        'root_mean_sq_err_dailyavgCDD',
        'cv_root_mean_sq_err_dailyavgCDD',
        'mean_abs_err_dailyavgCDD',
        'mean_abs_pct_err_dailyavgCDD',

        'percent_savings_hourlyavgCDD',
        'avoided_daily_runtime_hourlyavgCDD',
        'avoided_seasonal_runtime_hourlyavgCDD',
        'baseline_daily_runtime_hourlyavgCDD',
        'baseline_seasonal_runtime_hourlyavgCDD',
        'mean_demand_hourlyavgCDD',
        'mean_demand_baseline_hourlyavgCDD',
        'alpha_hourlyavgCDD',
        'tau_hourlyavgCDD',
        'mean_sq_err_hourlyavgCDD',
        'root_mean_sq_err_hourlyavgCDD',
        'cv_root_mean_sq_err_hourlyavgCDD',
        'mean_abs_err_hourlyavgCDD',
        'mean_abs_pct_err_hourlyavgCDD',

        'percent_savings_dailyavgHDD',
        'avoided_daily_runtime_dailyavgHDD',
        'avoided_seasonal_runtime_dailyavgHDD',
        'baseline_daily_runtime_dailyavgHDD',
        'baseline_seasonal_runtime_dailyavgHDD',
        'mean_demand_dailyavgHDD',
        'mean_demand_baseline_dailyavgHDD',
        'alpha_dailyavgHDD',
        'tau_dailyavgHDD',
        'mean_sq_err_dailyavgHDD',
        'root_mean_sq_err_dailyavgHDD',
        'cv_root_mean_sq_err_dailyavgHDD',
        'mean_abs_err_dailyavgHDD',
        'mean_abs_pct_err_dailyavgHDD',

        'percent_savings_hourlyavgHDD',
        'avoided_daily_runtime_hourlyavgHDD',
        'avoided_seasonal_runtime_hourlyavgHDD',
        'baseline_daily_runtime_hourlyavgHDD',
        'baseline_seasonal_runtime_hourlyavgHDD',
        'mean_demand_hourlyavgHDD',
        'mean_demand_baseline_hourlyavgHDD',
        'alpha_hourlyavgHDD',
        'tau_hourlyavgHDD',
        'mean_sq_err_hourlyavgHDD',
        'root_mean_sq_err_hourlyavgHDD',
        'cv_root_mean_sq_err_hourlyavgHDD',
        'mean_abs_err_hourlyavgHDD',
        'mean_abs_pct_err_hourlyavgHDD',

        'total_auxiliary_heating_runtime',
        'total_emergency_heating_runtime',
        'total_heating_runtime',
        'total_cooling_runtime',

        'actual_daily_runtime',
        'actual_seasonal_runtime',

        'baseline_comfort_temperature',

        'rhu_00F_to_05F',
        'rhu_05F_to_10F',
        'rhu_10F_to_15F',
        'rhu_15F_to_20F',
        'rhu_20F_to_25F',
        'rhu_25F_to_30F',
        'rhu_30F_to_35F',
        'rhu_35F_to_40F',
        'rhu_40F_to_45F',
        'rhu_45F_to_50F',
        'rhu_50F_to_55F',
        'rhu_55F_to_60F',
    ]

    output_dataframe = pd.DataFrame(seasonal_metrics, columns=columns)
    output_dataframe.to_csv(filepath, index=False, columns=columns)
    return output_dataframe
