import os
import logging
import logging.config
import json

from random import shuffle
from thermostat.importers import from_csv
from thermostat.exporters import metrics_to_csv
from thermostat.stats import compute_summary_statistics
from thermostat.stats import summary_statistics_to_csv
from thermostat.multiple import multiple_thermostat_calculate_epa_field_savings_metrics

def main():

    logging.basicConfig()
    with open("logging.json", "r") as logging_config:
        logging.config.dictConfig(json.load(logging_config))

    logger = logging.getLogger('epathermostat')  # Uses the 'epathermostat' logging
    logger.debug("Starting...")
    logging.captureWarnings(True)  # Set to True to log additional warning messages, False to only display on console

    data_dir = os.path.join("..", "tests", "data", "single_stage")
    metadata_filename = os.path.join(data_dir, "metadata.csv")

    # Verbose will override logging to display the imported thermostats. Set to "False" to use the logging level instead
    thermostats = list(from_csv(metadata_filename, verbose=True))

    # Figure out the random index for all of the thermostats based on the first one
    thermostat = thermostats[0]

    if thermostat.heat_runtime_daily is not None:
        thermostat_date_index = list(thermostat.heat_runtime_daily.index)
    if thermostat.cool_runtime_daily is not None:
        thermostat_date_index = list(thermostat.cool_runtime_daily.index)
    
    thermostat_index = list(range(0, len(thermostat_date_index)))
    for i in range(0, 500):
        shuffle(thermostat_index)

    output_dir = "."
    for thermostat in thermostats:
        thermostat_heat_index = []
        thermostat_heat = False
        thermostat_cool_index = []
        thermostat_cool = False

        if thermostat.heat_runtime_daily is not None:
            thermostat_date_index = list(thermostat.heat_runtime_daily.index)
            thermostat_heat = True
        if thermostat.cool_runtime_daily is not None:
            thermostat_date_index = list(thermostat.cool_runtime_daily.index)
            thermostat_cool = True
        
        # for i in range(0, len(thermostat_heat_index)):
        for offset, i in enumerate(thermostat_index):
            if thermostat_cool:
                thermostat.cool_runtime_daily[i] = None
            if thermostat_heat:
                thermostat.heat_runtime_daily[i] = None

            metrics = thermostat.calculate_epa_field_savings_metrics()

            for metric in metrics:
                logging_statement = f"{thermostat.thermostat_id} "
                logging_statement += f"mean demand: {metric['mean_demand']}, "
                logging_statement += f"tau: {metric['tau']}, "
                if 'n_core_heating_days' in metric:
                    logging_statement += f"n_core_heating_days: {metric['n_core_heating_days']}, "
                if 'n_core_cooling_days' in metric:
                    logging_statement += f"n_core_cooling_days: {metric['n_core_cooling_days']}, "
                logging_statement += f"days removed: {offset+1}, "
                logging_statement += f"day removed: {thermostat_date_index[i]}"
                logger.info(logging_statement)


if __name__ == "__main__":
    main()
