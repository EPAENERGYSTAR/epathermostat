import os
import logging
import logging.config
import json
import csv
from datetime import date
from zipfile import ZipFile
from thermostat.importers import from_csv
from thermostat.exporters import metrics_to_csv, certification_to_csv
from thermostat.stats import compute_summary_statistics
from thermostat.stats import summary_statistics_to_csv
from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics

# These are variables used in the example code. Please tailor these to your
# environment as needed.

# Whether to compute Advanced Statistics (in most cases this is NOT needed)
ADVANCED_STATS = False

# The name of the product to be certified
PRODUCT_ID = 'test_product'

# The date of the run (defaults to today's date in YYYY-MM-DD format)
RUN_DATE = date.today().strftime('%F')

# This creates the base filename for the files that are created (e.g.
# test_product_2022-03-28)
BASE_FILENAME = f'{PRODUCT_ID}_{RUN_DATE}'

# Verbose will override logging to display the imported thermostats. Set to
# 'False' to use the logging level instead
VERBOSE = True

# Set to True to log additional warning messages, False to only display on
# console
CAPTURE_WARNINGS = True

# Example logging configuration for file and console output
# logging.json: Normal logging example
# logging_noisy.json: Turns on all debugging information
# logging_quiet.json: Only logs error messages
LOGGING_CONFIG = 'logging.json'

# Save cached weather data files? (Default: False)
SAVE_CACHE = False
CACHE_PATH = None  # Replace with location to save the weather cache files (e.g. '/tmp/epathermosat')

# This section finds the metadata files and data files for the thermostats.
# These point to examples of the various styles of files
# In most cases you will combine Single Stage, Two Stage, and Two Stage ERT
# data in the same file.

# Single Stage
DATA_DIR = os.path.join('..', 'tests', 'data', 'single_stage')
METADATA_FILENAME = os.path.join(DATA_DIR, 'metadata.csv')

# Two Stage
# DATA_DIR = os.path.join('..', 'tests', 'data', 'two_stage')
# METADATA_FILENAME = os.path.join(DATA_DIR, 'epa_two_stage_metadata.csv')

# Two Stage ERT
# DATA_DIR = os.path.join('..', 'tests', 'data', 'two_stage_ert')
# METADATA_FILENAME = os.path.join(DATA_DIR, 'epa_two_stage_metadata.csv')

# Where to store the metrics file and import error log files. This will use
# the data directory. You may also use the current directory by setting
# OUTPUT_DIR = '.'
OUTPUT_DIR = DATA_DIR

# NOTE: The following parameters do not need to be changed. They are provided
# here as examples of the files that are generated by this script.

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
METRICS_FILEPATH = os.path.join(OUTPUT_DIR, METRICS_FILENAME)
STATS_FILEPATH = os.path.join(DATA_DIR, STATISTICS_FILENAME)
CERTIFICATION_FILEPATH = os.path.join(DATA_DIR, CERTIFICATION_FILENAME)
STATS_ADVANCED_FILEPATH = os.path.join(DATA_DIR, ADVANCED_STATISTICS_FILENAME)
IMPORT_ERRORS_FILEPATH = os.path.join(OUTPUT_DIR, IMPORT_ERRORS_FILENAME)
SANITIZED_IMPORT_ERRORS_FILEPATH = os.path.join(OUTPUT_DIR, SANITIZED_IMPORT_ERRORS_FILENAME)
CLIMATE_ZONE_INSUFFICIENT_FILEPATH = os.path.join(OUTPUT_DIR, CLIMATE_ZONE_INSUFFICIENT_FILENAME)
ZIP_FILEPATH = os.path.join(OUTPUT_DIR, ZIP_FILENAME)


def write_errors(filepath, fieldnames, errors, extrasaction=None):
    with open(filepath, 'w') as error_file:
        if extrasaction:
            writer = csv.DictWriter(
                error_file,
                fieldnames=fieldnames,
                dialect='excel',
                extrasaction=extrasaction)
        else:
            writer = csv.DictWriter(
                error_file,
                fieldnames=fieldnames,
                dialect='excel')
        writer.writeheader()
        for error in errors:
            writer.writerow(error)


def count_metadata(filepath):
    with open(filepath, 'r') as metadata_file:
        reader = csv.DictReader(metadata_file)
        return len(list(reader))


def main():
    '''
    This is an example of how to best use the new multi-processing functionality.
    It shows the proper format for wrapping the code under a main() function and
    shows how to use the multiple_thermostat_calculate_epa_field_savings_metrics
    function. Windows needs to have this code wrapped in a main() function in
    order to work.
    '''

    logging.basicConfig()
    with open(LOGGING_CONFIG, 'r') as logging_config:
        logging.config.dictConfig(json.load(logging_config))

    # Uses the 'epathermostat' logging
    logger = logging.getLogger('epathermostat')
    logger.debug('Starting...')
    logging.captureWarnings(CAPTURE_WARNINGS)

    thermostats, import_errors = from_csv(
        METADATA_FILENAME,
        verbose=VERBOSE,
        save_cache=SAVE_CACHE,
        cache_path=CACHE_PATH)

    # This logs any import errors that might have occurred.
    if import_errors:
        # This writes a file with the thermostat ID as part of the file. This
        # is for your own troubleshooting
        fieldnames = ['thermostat_id', 'error']
        write_errors(IMPORT_ERRORS_FILEPATH, fieldnames, import_errors)

        # This writes a file without the thermostat ID as part of the file.
        # This file is sent as part of the certification to help with
        # diagnosing issues with missing thermostats
        fieldnames = ['error']
        write_errors(SANITIZED_IMPORT_ERRORS_FILEPATH, fieldnames, import_errors, extrasaction='ignore')

    # Check to see how many thermostats we are importing and warn if less than 30%
    metadata_count = count_metadata(METADATA_FILENAME)
    thermostat_estimate_count = thermostats.__length_hint__()  # Get a rough estimate of the number of thermostats
    percent_thermostats_imported = (thermostat_estimate_count / metadata_count) * 100
    if percent_thermostats_imported < 30:
        logger.warning(f'Imported {percent_thermostats_imported}% of thermostats, which is less than 30%')
        logger.warning(f'Please check {IMPORT_ERRORS_FILEPATH} for more details')
    else:
        logger.debug(f'Imported {percent_thermostats_imported}% of thermostats')

    metrics = multiple_thermostat_calculate_epa_field_savings_metrics(thermostats)

    metrics_out = metrics_to_csv(metrics, METRICS_FILEPATH)

    stats, insufficient = compute_summary_statistics(metrics_out)

    if insufficient:
        fieldnames = ['climate_zone', 'count', 'error']
        write_errors(CLIMATE_ZONE_INSUFFICIENT_FILEPATH, fieldnames, insufficient)

    certification_to_csv(stats, CERTIFICATION_FILEPATH, PRODUCT_ID)

    summary_statistics_to_csv(
        stats,
        STATS_FILEPATH,
        PRODUCT_ID)

    if ADVANCED_STATS:
        stats_advanced = compute_summary_statistics(
            metrics_out,
            advanced_filtering=True)

        summary_statistics_to_csv(
            stats_advanced,
            STATS_ADVANCED_FILEPATH,
            PRODUCT_ID)

    # Compile the files together in a neat package
    files_to_zip = [
        CERTIFICATION_FILEPATH,
        STATS_FILEPATH,
        ]
    if ADVANCED_STATS:
        files_to_zip.append(STATS_ADVANCED_FILEPATH)

    if import_errors:
        files_to_zip.append(SANITIZED_IMPORT_ERRORS_FILEPATH)

    if insufficient:
        files_to_zip.append(CLIMATE_ZONE_INSUFFICIENT_FILEPATH)

    with ZipFile(ZIP_FILEPATH, 'w') as certification_zip:
        for filename in files_to_zip:
            if os.path.exists(filename):
                certification_zip.write(filename, arcname=os.path.basename(filename))


if __name__ == '__main__':
    main()
