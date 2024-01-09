from pathlib import Path
from thermostat.importers import from_csv
from thermostat.exporters import metrics_to_csv
from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics


def write_stats(
        top_n: int,
        metadata_path: Path,
        metrics_filepath: Path
         ):

    thermostats, tstat_errors = from_csv(metadata_path, top_n=top_n)
    metrics = multiple_thermostat_calculate_epa_field_savings_metrics(thermostats)

    metrics_to_csv(metrics, metrics_filepath)


if __name__ == '__main__':
    # for testing purposes; only run the first n thermostat files
    # set to None to run all
    top_n = 30

    # path to the raw thermostat data in csv format
    data_dir = Path('..') / '..' / 'datadir' / 'EPA_Tau'
    metadata_path = data_dir / '2019_epa_tau.csv'
    # dir to save tau search stats to (multiple files per thermostat)
    output_dir = data_dir.parents[0] / 'Tau Results'
    metrics_filepath = output_dir / '2019_EPA_tau_2023_06_01_metrics_new.csv'

    write_stats(
        top_n=top_n,
        metadata_path=metadata_path,
        metrics_filepath=metrics_filepath
    )
