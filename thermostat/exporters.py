import pandas as pd
import warnings
from thermostat.columns import EXPORT_COLUMNS, CERTIFICATION_HEADERS


warnings.simplefilter('module', Warning)


COLUMN_LOOKUP = {
        "percent_savings_baseline_percentile_lower_bound_95_perc_conf_national_weighted_mean": {
            "metric": "percent_savings_baseline_percentile",
            "statistic": "lower_bound_95",
            },
        "percent_savings_baseline_percentile_q20_national_weighted_mean": {
            "metric": "percent_savings_baseline_percentile",
            "statistic": "q20",
            },
        "rhu2IQFLT_30F_to_45F_upper_bound_95_perc_conf": {
            "metric": "rhu_30F_to_45F",
            "statistic": "upper_bound_95",
            }
        }
FILTER_LOOKUP = {
        "national_weighted_mean_heating_tau_cvrmse_savings_p01_filter": {
            "season": "heating",
            "region": "national_weighted_mean",
            "filter": "tau_cvrmse_savings_p01",
            },
        "national_weighted_mean_cooling_tau_cvrmse_savings_p01_filter": {
            "season": "cooling",
            "region": "national_weighted_mean",
            "filter": "tau_cvrmse_savings_p01",
            },
        "all_tau_cvrmse_savings_p01_filter_heating": {
            "season": "heating",
            "region": "all",
            "filter": "tau_cvrmse_savings_p01",
            },
        }

DATA_COLUMNS = [
        ['national_weighted_mean_heating_tau_cvrmse_savings_p01_filter', 'percent_savings_baseline_percentile_lower_bound_95_perc_conf_national_weighted_mean'],
        ['national_weighted_mean_cooling_tau_cvrmse_savings_p01_filter', 'percent_savings_baseline_percentile_lower_bound_95_perc_conf_national_weighted_mean'],
        ['national_weighted_mean_heating_tau_cvrmse_savings_p01_filter', 'percent_savings_baseline_percentile_q20_national_weighted_mean'],
        ['national_weighted_mean_cooling_tau_cvrmse_savings_p01_filter', 'percent_savings_baseline_percentile_q20_national_weighted_mean'],
        ['all_tau_cvrmse_savings_p01_filter_heating', 'rhu2IQFLT_30F_to_45F_upper_bound_95_perc_conf']]


def metrics_to_csv(metrics, filepath):
    """ Writes metrics outputs to the file specified.

    Parameters
    ----------
    metrics : list of dict
        list of outputs from the function
        `thermostat.calculate_epa_draft_rccs_field_savings_metrics()`
    filepath : str
        filepath specification for location of output CSV file.

    Returns
    -------
    df : pd.DataFrame
        DataFrame containing data output to CSV.
    """

    output_dataframe = pd.DataFrame(metrics, columns=EXPORT_COLUMNS)
    output_dataframe.to_csv(filepath, index=False, columns=EXPORT_COLUMNS)
    return output_dataframe


def certification_to_csv(stats, filepath, product_id):
    """ Writes certification outputs to the file specified.

    Parameters
    ----------
    stats : list of dict
        list of statistical outputs from the function
        `thermostat.compute_summary_statistics()`
    filepath : str
        filepath specification for location of output CSV file.

    Returns
    -------
    df : pd.DataFrame
        DataFrame containing data output to CSV.
    """
    if stats is None:
        warnings.warn("No certification data to export.")
        return None

    labels = [i.get('label') for i in stats]
    sw_version = stats[labels.index('all_tau_cvrmse_savings_p01_filter_heating')]['sw_version']

    certification_data = []

    for column_filter, column_data in DATA_COLUMNS:
        stats_column_number = labels.index(column_filter)
        value = stats[stats_column_number].get(column_data, None)
        row = [
                product_id,
                sw_version,
                COLUMN_LOOKUP[column_data]['metric'],
                FILTER_LOOKUP[column_filter]['filter'],
                FILTER_LOOKUP[column_filter]['region'],
                COLUMN_LOOKUP[column_data]['statistic'],
                FILTER_LOOKUP[column_filter]['season'],
                value,
                ]
        certification_data.append(row)

    output_dataframe = pd.DataFrame(certification_data, columns=CERTIFICATION_HEADERS)
    output_dataframe.to_csv(filepath, index=False, columns=CERTIFICATION_HEADERS, float_format='%.2f')
    return output_dataframe
