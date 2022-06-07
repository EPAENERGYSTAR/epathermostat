#!/usr/bin/env python3
import uuid
import os

# Number of thermostat IDs to generate
NUM_THERMOSTATS = 1000
# Climate zones (also used as filenames)
CLIMATE_ZONES = [
    'very-cold_cold',
    'mixed-humid',
    'mixed-dry_hot-dry',
    'hot-humid',
    'marine',
]

# Change this file path to a different location if you wish to save the files
FILE_PATH = '/tmp'


def main():
    """ This script generates random UUIDs for each of the climate zones.
    This is used as an example for the thermostat_selection.py script

    :returns: None

    """
    for climate_zone in CLIMATE_ZONES:
        climate_zone_filename = climate_zone + '.csv'
        with open(os.path.join(FILE_PATH, climate_zone_filename), 'w') as thermostat_file:
            for _ in range(0, NUM_THERMOSTATS):
                thermostat_id = uuid.uuid4()
                thermostat_file.write(str(thermostat_id) + '\n')

    return


if __name__ == '__main__':
    main()
