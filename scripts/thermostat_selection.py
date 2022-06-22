#!/usr/bin/env python3
import os
import pickle
import numpy as np


# NOTE: This sample file relies on UUIDs generated from the random_uuid_generation.py in this directory.
# You can use both of these files to get a sense of how thermostat selection
# works before modifying this script for your own process.

# Number of thermostats that will be selected
NUM_THERMOSTATS = 250

# Climate zones (also used as filenames for the selection process)
CLIMATE_ZONES = [
    'very-cold_cold',
    'mixed-humid',
    'mixed-dry_hot-dry',
    'hot-humid',
    'marine',
]

# Change this file path to a different location if you wish to save the files
FILE_PATH = '/tmp'

# NOTE: Replace these seeds with the ones provided per submission period
SEEDS = {
    'very-cold_cold': 101,
    'hot-humid': 102,
    'mixed-humid': 103,
    'mixed-dry_hot-dry': 104,
    'marine': 105,
}

# Output filenames
SAMPLE_OUTPUT_FILENAME = 'sample_output.csv'
SAMPLE_OUTPUT_VECTOR_FILENAME = 'sample_output_vector.csv'
PICKLE_RNG_STATE_FILENAME = 'prng_state.pickle'


def main():
    """ Example program for reading climate-zone-separated files and randomly
    selecting a sample from those files """

    # DEBUG: state caching
    prng_state_exact = np.random.get_state()

    # DEBUG: Save state via pickle
    with open(PICKLE_RNG_STATE_FILENAME, 'wb') as file:
        pickle.dump(prng_state_exact, file)

    # #DEBUG: Code to load old state and set PRNG to that state
    # with open('prng_state.pickle','rb') as f:
    #     reload_state = pickle.load(f)
    # np.random.set_state(reload_state)

    # NOTE: This uses a dictionary for loading each climate zone from a file.
    # This can be replaced with code that grabs this data from a database or
    # other means.
    climate_zone_dict = {}
    # Load sample target data; Note if 0:n index replaced with data/thermostat
    # id's, will sample unique id's instead of indices
    for climate_zone in CLIMATE_ZONES:
        climate_zone_filename = climate_zone + '.csv'
        with open(os.path.join(FILE_PATH, climate_zone_filename)) as thermostat_file:
            thermostats = thermostat_file.readlines()
            # Remove carriage return
            thermostats = [x.rstrip() for x in thermostats]
            # NOTE: You do not have to use Python sort here. If you database or
            # other system supports repeatable sorting you may use that instead
            thermostats = np.sort(thermostats)
            climate_zone_dict[climate_zone] = list(thermostats)

    # Sample target data, applying 1 seed per climate zone
    very_cold_rng = np.random.RandomState(seed=SEEDS['very-cold_cold'])
    sample_cold_very_cold = very_cold_rng.choice(
        climate_zone_dict['very-cold_cold'], NUM_THERMOSTATS, replace=False)
    hot_humid_rng = np.random.RandomState(seed=SEEDS['hot-humid'])
    sample_hot_humid = hot_humid_rng.choice(
        climate_zone_dict['hot-humid'], NUM_THERMOSTATS, replace=False)
    mixed_humid_rng = np.random.RandomState(seed=SEEDS['mixed-humid'])
    sample_mixed_humid = mixed_humid_rng.choice(
        climate_zone_dict['mixed-humid'], NUM_THERMOSTATS, replace=False)
    mixed_dry_hot_dry_rng = np.random.RandomState(seed=SEEDS['mixed-dry_hot-dry'])
    sample_mixed_dry_hot_dry = mixed_dry_hot_dry_rng.choice(
        climate_zone_dict['mixed-dry_hot-dry'], NUM_THERMOSTATS, replace=False)
    marine_rng = np.random.RandomState(seed=SEEDS['marine'])
    sample_marine = marine_rng.choice(
        climate_zone_dict['marine'], NUM_THERMOSTATS, replace=False)

    # Sort Sampled data by value
    sample_cold_very_cold = np.sort(sample_cold_very_cold)
    sample_hot_humid = np.sort(sample_hot_humid)
    sample_mixed_humid = np.sort(sample_mixed_humid)
    sample_mixed_dry_hot_dry = np.sort(sample_mixed_dry_hot_dry)
    sample_marine = np.sort(sample_marine)

    # Create matrix for all samples, Matrix format best for indices
    sorted_sample = np.vstack(
        (
            sample_cold_very_cold,
            sample_hot_humid,
            sample_mixed_humid,
            sample_mixed_dry_hot_dry,
            sample_marine
        )
    )

    # Create long format output, best for vector of thermostat id's
    results = sample_cold_very_cold
    outfile = np.append(results, [
                        sample_hot_humid, sample_mixed_humid, sample_mixed_dry_hot_dry, sample_marine])

    # Save Sample items to file
    np.savetxt(SAMPLE_OUTPUT_FILENAME, sorted_sample, fmt='%s', delimiter=',')
    np.savetxt(SAMPLE_OUTPUT_VECTOR_FILENAME,
               outfile, fmt='%s',  delimiter=',')


if __name__ == '__main__':
    main()
