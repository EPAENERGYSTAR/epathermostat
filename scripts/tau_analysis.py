from write_stats import write_stats
from multi_thermostat_driver_func import mult_thermostat_driver
from analyze_tau_stats import analyze_tau_stats
from pathlib import Path
from datetime import date


if __name__ == '__main__':

    tau_save_path = Path('../datadir/attempt1')

    # This section finds the metadata files and data files for the thermostats.
    # These point to examples of the various styles of files
    # In most cases you will combine Single Stage, Two Stage, and Two Stage ERT
    # data in the same file.

    # Single Stage
    data_dir = Path('..') / '..' / 'datadir' / 'EPA_Tau'
    metadata_path = data_dir / '2019_epa_tau.csv'

    # path to the raw thermostat data in csv format
    # dir to save tau search stats to (multiple files per thermostat)
    output_dir = data_dir.parents[0] / 'Tau Results'
    metrics_filepath = output_dir / '2019_EPA_tau_2023_06_01_metrics_new.csv'

    # path to prior metrics file to use for comparison; should contain the same set of ct_identifiers
    results_old_path = output_dir / 'test_product_2023-10-26_metrics_base.csv'

    # path to directory of stats files output from running tau search code; called "tau_search_path" in core.py module
    stats_dir = Path('..') / '..' / 'datadir' / 'tau_search_stats'

    # path to directory where output plots and tables will be saved
    plots_dir = Path('..') / '..' / 'datadir' / 'tau_stats_plots'

    # The date of the run (defaults to today's date in YYYY-MM-DD format)
    RUN_DATE = date.today().strftime('%F')

    # The name of the product to be certified
    PRODUCT_ID = 'test_product'

    # This creates the base filename for the files that are created (e.g.
    # test_product_2022-03-28)
    BASE_FILENAME = f'{PRODUCT_ID}_{RUN_DATE}'

    # These are the filenames for the output files.
    METRICS_FILENAME = f'{BASE_FILENAME}_metrics.csv'
    CERTIFICATION_FILENAME = f'{BASE_FILENAME}_certification.csv'
    STATISTICS_FILENAME = f'{BASE_FILENAME}_stats.csv'
    ADVANCED_STATISTICS_FILENAME = f'{BASE_FILENAME}_stats_advanced.csv'
    IMPORT_ERRORS_FILENAME = f'{BASE_FILENAME}_import_errors.csv'
    SANITIZED_IMPORT_ERRORS_FILENAME = f'{BASE_FILENAME}_errors_sanitized.csv'
    CLIMATE_ZONE_INSUFFICIENT_FILENAME = f'{BASE_FILENAME}_climate_zone_insufficient.csv'
    ZIP_FILENAME = f'{BASE_FILENAME}.zip'

    # These are the locations of where these files will be stored.
    METRICS_FILEPATH = data_dir / METRICS_FILENAME
    STATS_FILEPATH = data_dir / STATISTICS_FILENAME
    CERTIFICATION_FILEPATH = data_dir / CERTIFICATION_FILENAME
    STATS_ADVANCED_FILEPATH = data_dir / ADVANCED_STATISTICS_FILENAME
    IMPORT_ERRORS_FILEPATH = data_dir / IMPORT_ERRORS_FILENAME
    SANITIZED_IMPORT_ERRORS_FILEPATH = data_dir / SANITIZED_IMPORT_ERRORS_FILENAME
    CLIMATE_ZONE_INSUFFICIENT_FILEPATH = data_dir / CLIMATE_ZONE_INSUFFICIENT_FILENAME
    ZIP_FILEPATH = data_dir / ZIP_FILENAME

    top_n = 30

    mult_thermostat_driver(
        advanced_stats=False,  # Whether to compute Advanced Statistics (in most cases this is NOT needed)
        product_id=PRODUCT_ID,  # The name of the product to be certified
        verbose=True,  # Verbose will override logging to display the imported thermostats.
        capture_warnings=True,  # Set to True to log additional warning messages,
        logging_config='logging.json',  # Example logging configuration for file and console output
        save_cache=False,  # Save cached weather data files? (Default: False)
        cache_path=None,
        tau_save_path=tau_save_path,
        metadata_filename=metadata_path,
        metrics_filepath=METRICS_FILEPATH,
        stats_filepath=STATS_FILEPATH,
        certification_filepath=CERTIFICATION_FILEPATH,
        stats_advanced_filepath=STATS_ADVANCED_FILEPATH,
        import_errors_filepath=IMPORT_ERRORS_FILEPATH,
        sanitized_import_errors_filepath=SANITIZED_IMPORT_ERRORS_FILEPATH,
        climate_zone_insufficient_filepath=CLIMATE_ZONE_INSUFFICIENT_FILEPATH,
        zip_filepath=ZIP_FILEPATH
    )

    write_stats(
        top_n=top_n,
        metadata_path=metadata_path,
        metrics_filepath=metrics_filepath
    )

    analyze_tau_stats(data_dir, results_old_path, metrics_filepath, stats_dir, plots_dir)
