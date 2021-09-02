#!/usr/bin/env python
import os
import logging
import logging.config
import json
import sqlite3

from random import shuffle
from thermostat.importers import from_csv
from thermostat.exporters import metrics_to_csv
from thermostat.stats import compute_summary_statistics
from thermostat.stats import summary_statistics_to_csv
from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics

# Set this variable to the location of the data files (Default: ../tests/data/single_stage)
# NOTE: You'll want to set this to the location of the dataset that you wish to remove missing days.
DATA_DIR = os.path.join("..", "tests", "data", "single_stage")

# Set this variable for the location to create the metrics database file (default: current directory, metrics.db)
METRICS_DATABASE_FILE = os.path.join('.', 'metrics.db')


def main():

    metrics_db = sqlite3.connect(METRICS_DATABASE_FILE)
    n_remove = 5
    logging.basicConfig()
    with open("logging.json", "r") as logging_config:
        logging.config.dictConfig(json.load(logging_config))

    logger = logging.getLogger('epathermostat')  # Uses the 'epathermostat' logging
    logger.debug("Starting...")
    logging.captureWarnings(True)  # Set to True to log additional warning messages, False to only display on console

    metadata_filename = os.path.join(DATA_DIR, "metadata.csv")

    # Verbose will override logging to display the imported thermostats.
    # Set to "False" to use the logging level instead
    thermostats = list(from_csv(metadata_filename, verbose=True))

    for thermostat in thermostats:
        thermostat_heat = False
        thermostat_cool = False

        if thermostat.heat_runtime_daily is not None:
            thermostat_date_index = list(thermostat.heat_runtime_daily.index)
            thermostat_heat = True
        if thermostat.cool_runtime_daily is not None:
            thermostat_date_index = list(thermostat.cool_runtime_daily.index)
            thermostat_cool = True

        thermostat_index = list(range(0, len(thermostat_date_index)))
        for i in range(0, 500):
            shuffle(thermostat_index)

        thermostat_index_list = list(enumerate(thermostat_index))

        for offset in range(0, len(thermostat_index_list), n_remove):
            days_removed = []
            for _, i in thermostat_index_list[offset:offset+n_remove]:
                if thermostat_cool:
                    thermostat.cool_runtime_daily[i] = None
                if thermostat_heat:
                    thermostat.heat_runtime_daily[i] = None
                days_removed.append(thermostat_date_index[thermostat_index_list[i][1]])

            metrics = thermostat.calculate_epa_field_savings_metrics()
            metrics_out = metrics_to_csv(metrics, 'metrics_temp.csv')
            metrics_out['days_removed'] = offset + n_remove

            logging_statement = f"{thermostat.thermostat_id} "
            logging_statement += f"days removed: {offset+n_remove}, "
            logging_statement += f"(removed: {days_removed})"
            logger.info(logging_statement)

            metrics_out.to_sql(
                name='metric',
                con=metrics_db,
                if_exists='append')


if __name__ == "__main__":
    main()
