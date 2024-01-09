from pathlib import Path
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


def mult_thermostat_driver(
        advanced_stats: bool,
        product_id: str,
        verbose: bool,
        capture_warnings: bool,
        logging_config: str,
        save_cache: Path,
        cache_path: Path,
        tau_save_path: Path,
        metadata_filename: Path,
        metrics_filepath: Path,
        stats_filepath: Path,
        certification_filepath: Path,
        stats_advanced_filepath: Path,
        import_errors_filepath: Path,
        sanitized_import_errors_filepath: Path,
        climate_zone_insufficient_filepath: Path,
        zip_filepath: Path
):
    '''
    This script processes the thermostat metadata and data files to generate
    the certification files for submission to EPA.
    '''

    logging.basicConfig()
    with open(logging_config, 'r') as logging_config:
        logging.config.dictConfig(json.load(logging_config))

    # Uses the 'epathermostat' logging
    logger = logging.getLogger('epathermostat')
    logger.debug('Starting...')
    logging.captureWarnings(capture_warnings)

    thermostats, import_errors = from_csv(
        metadata_filename,
        verbose=verbose,
        save_cache=save_cache,
        cache_path=cache_path,
        tau_search_path=tau_save_path)

    # This logs any import errors that might have occurred.
    if import_errors:
        # This writes a file with the thermostat ID as part of the file. This
        # is for your own troubleshooting
        fieldnames = ['thermostat_id', 'error']
        write_errors(import_errors_filepath, fieldnames, import_errors)

        # This writes a file without the thermostat ID as part of the file.
        # This file is sent as part of the certification to help with
        # diagnosing issues with missing thermostats
        fieldnames = ['error']
        write_errors(sanitized_import_errors_filepath, fieldnames, import_errors, extrasaction='ignore')

    # Check to see how many thermostats we are importing and warn if less than 30%
    metadata_count = count_metadata(metadata_filename)
    thermostat_estimate_count = thermostats.__length_hint__()  # Get a rough estimate of the number of thermostats
    percent_thermostats_imported = (thermostat_estimate_count / metadata_count) * 100
    if percent_thermostats_imported < 30:
        logger.warning(f'Imported {percent_thermostats_imported}% of thermostats, which is less than 30%')
        logger.warning(f'Please check {import_errors_filepath} for more details')
    else:
        logger.debug(f'Imported {percent_thermostats_imported}% of thermostats')

    metrics = multiple_thermostat_calculate_epa_field_savings_metrics(thermostats)

    metrics_out = metrics_to_csv(metrics, metrics_filepath)

    stats, insufficient = compute_summary_statistics(metrics_out)

    if insufficient:
        fieldnames = ['climate_zone', 'count', 'error']
        write_errors(climate_zone_insufficient_filepath, fieldnames, insufficient)

    certification_to_csv(stats, certification_filepath, product_id)

    summary_statistics_to_csv(
        stats,
        stats_filepath,
        product_id)

    if advanced_stats:
        stats_advanced = compute_summary_statistics(
            metrics_out,
            advanced_filtering=True)

        summary_statistics_to_csv(
            stats_advanced,
            stats_advanced_filepath,
            product_id)

    # Compile the files together in a neat package
    files_to_zip = [
        certification_filepath,
        stats_filepath,
        ]
    if advanced_stats:
        files_to_zip.append(stats_advanced_filepath)

    if import_errors:
        files_to_zip.append(sanitized_import_errors_filepath)

    if insufficient:
        files_to_zip.append(climate_zone_insufficient_filepath)

    with ZipFile(zip_filepath, 'w') as certification_zip:
        for filename in files_to_zip:
            if filename.exists():
                certification_zip.write(filename, arcname=filename.name)
