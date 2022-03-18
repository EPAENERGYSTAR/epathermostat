import os
import logging
import logging.config
import json
import csv
from zipfile import ZipFile
from thermostat.importers import from_csv
from thermostat.exporters import metrics_to_csv, certification_to_csv
from thermostat.stats import compute_summary_statistics
from thermostat.stats import summary_statistics_to_csv
from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics

# These are variables used in the example code. Please tailor these to your
# environment as needed.

# Whether to compute Advanced Statistics (in most cases this is NOT needed)
ADVANCED_STATS = True

# The name of the product to be certified
PRODUCT_ID = "test_product"

# Verbose will override logging to display the imported thermostats. Set to
# "False" to use the logging level instead
VERBOSE = True

# Example logging configuration for file and console output
# logging.json: Normal logging example
# logging_noisy.json: Turns on all debugging information
# logging_quiet.json: Only logs error messages
LOGGING_CONFIG = "logging.json"

# This section finds the metadata files and data files for the thermostats.
# These point to examples of the various styles of files
# In most cases you will combine Single Stage, Two Stage, and Two Stage ERT
# data in the same file.

# Single Stage
DATA_DIR = os.path.join("..", "tests", "data", "single_stage")
METADATA_FILENAME = os.path.join(DATA_DIR, "metadata.csv")

# Two Stage
# DATA_DIR = os.path.join("..", "tests", "data", "two_stage")
# METADATA_FILENAME = os.path.join(DATA_DIR, "epa_two_stage_metadata.csv")

# Two Stage ERT
# DATA_DIR = os.path.join("..", "tests", "data", "two_stage_ert")
# METADATA_FILENAME = os.path.join(DATA_DIR, "epa_two_stage_metadata.csv")

# Where to store the metrics file and import error log files. This will use
# the data directory. You may also use the current directory by setting
# OUTPUT_DIR = "."
OUTPUT_DIR = DATA_DIR

# These are the filenames for the output files.
METRICS_FILENAME = 'thermostat_example_metrics.csv'
CERTIFICATION_FILENAME = 'thermostat_example_certification.csv'
STATISTICS_FILENAME = 'thermostat_example_stats.csv'
ADVANCED_STATISTICS_FILENAME = 'thermostat_example_stats_advanced.csv'
IMPORT_ERRORS_FILENAME = 'thermostat_import_errors.csv'
ZIP_FILENAME = 'thermostat_example.zip'

# These are the locations of where these files will be stored.
METRICS_FILEPATH = os.path.join(OUTPUT_DIR, METRICS_FILENAME)
STATS_FILEPATH = os.path.join(DATA_DIR, STATISTICS_FILENAME)
CERTIFICATION_FILEPATH = os.path.join(DATA_DIR, CERTIFICATION_FILENAME)
STATS_ADVANCED_FILEPATH = os.path.join(DATA_DIR, ADVANCED_STATISTICS_FILENAME)
IMPORT_ERRORS_FILEPATH = os.path.join(OUTPUT_DIR, IMPORT_ERRORS_FILENAME)
ZIP_FILEPATH = os.path.join(OUTPUT_DIR, ZIP_FILENAME)

# This is an example of how to best use the new multi-processing functionality.
# It shows the proper format for wrapping the code under a main() function and
# shows how to use the multiple_thermostat_calculate_epa_field_savings_metrics
# function. Windows needs to have this code wrapped in a main() function in
# order to work.


def main():

    logging.basicConfig()
    with open(LOGGING_CONFIG, "r") as logging_config:
        logging.config.dictConfig(json.load(logging_config))

    # Uses the 'epathermostat' logging
    logger = logging.getLogger('epathermostat')
    logger.debug("Starting...")
    # Set to True to log additional warning messages, False to only display on
    # console
    logging.captureWarnings(True)

    thermostats, import_errors = from_csv(METADATA_FILENAME, verbose=VERBOSE)
    # Use this instead to save the weather cache to local disk files
    # thermostats, errors = from_csv(METADATA_FILENAME, verbose=VERBOSE, save_cache=True,
    #                        cache_path='/tmp/epa_weather_files/')

    # This logs any import errors that might have occurred.
    if import_errors:
        fieldnames = ['thermostat_id', 'error']
        with open(IMPORT_ERRORS_FILEPATH, 'w') as error_file:
            writer = csv.DictWriter(error_file, fieldnames=fieldnames, dialect='excel')
            writer.writeheader()
            for thermostat_error in import_errors:
                writer.writerow(thermostat_error)

    metrics = multiple_thermostat_calculate_epa_field_savings_metrics(thermostats)

    metrics_out = metrics_to_csv(metrics, METRICS_FILEPATH)

    stats = compute_summary_statistics(metrics_out)

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

    files_to_zip = [
        CERTIFICATION_FILEPATH,
        STATS_FILEPATH,
        ]
    if ADVANCED_STATS:
        files_to_zip.append(STATS_ADVANCED_FILEPATH)
    with ZipFile(ZIP_FILEPATH, 'w') as certification_zip:
        for filename in files_to_zip:
            certification_zip.write(filename, arcname=os.path.basename(filename))


if __name__ == "__main__":
    main()
