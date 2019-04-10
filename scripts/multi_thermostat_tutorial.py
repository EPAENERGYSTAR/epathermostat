import os
import logging
import logging.config
import json
from thermostat.importers import from_csv
from thermostat.exporters import metrics_to_csv
from thermostat.stats import compute_summary_statistics
from thermostat.stats import summary_statistics_to_csv
from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics


# This is an example of how to best use the new multi-processing functionality.
# It shows the proper format for wrapping the code under a main() function and
# shows how to use the multiple_thermostat_calculate_epa_field_savings_metrics
# function. Windows needs to have this code wrapped in a main() function in
# order to work.


def main():

    logging.basicConfig()
    # Example logging configuration for file and console output
    # logging.json: Normal logging example
    # logging_noisy.json: Turns on all debugging information
    # logging_quiet.json: Only logs error messages
    with open("logging.json", "r") as logging_config:
        logging.config.dictConfig(json.load(logging_config))

    logger = logging.getLogger('epathermostat')  # Uses the 'epathermostat' logging
    logger.debug("Starting...")
    logging.captureWarnings(True)  # Set to True to log additional warning messages, False to only display on console

    data_dir = os.path.join("..", "tests", "data")
    metadata_filename = os.path.join(data_dir, "metadata.csv")

    # Use this to save the weather cache to local disk files
    # thermostats = from_csv(metadata_filename, verbose=True, save_cache=True, cache_path='/tmp/epa_weather_files/')

    # Verbose will override logging to display the imported thermostats. Set to "False" to use the logging level instead
    thermostats = from_csv(metadata_filename, verbose=True)

    output_dir = "."
    metrics = multiple_thermostat_calculate_epa_field_savings_metrics(thermostats)

    output_filename = os.path.join(output_dir, "thermostat_example_output.csv")
    metrics_out = metrics_to_csv(metrics, output_filename)

    stats = compute_summary_statistics(metrics_out)
    stats_advanced = compute_summary_statistics(metrics_out, advanced_filtering=True)

    product_id = "test_product"
    stats_filepath = os.path.join(data_dir, "thermostat_example_stats.csv")
    summary_statistics_to_csv(stats, stats_filepath, product_id)

    stats_advanced_filepath = os.path.join(data_dir, "thermostat_example_stats_advanced.csv")
    summary_statistics_to_csv(stats_advanced, stats_advanced_filepath, product_id)


if __name__ == "__main__":
    main()
