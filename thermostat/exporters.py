import pandas as pd
from thermostat.columns import EXPORT_COLUMNS


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
