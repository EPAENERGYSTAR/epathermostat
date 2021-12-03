import pandas as pd
import zipcodes
from pkg_resources import resource_stream
from collections import namedtuple
from eeweather.geo import get_lat_long_climate_zones
import numpy as np


BASELINE_TEMPERATURE = {
    'Very-Cold/Cold': {
        'heating': 68,
        'cooling': 73,
        },
    'Mixed-Humid': {
        'heating': 69,
        'cooling': 73,
        },
    'Mixed-Dry/Hot-Dry': {
        'heating': 69,
        'cooling': 75,
        },
    'Hot-Humid': {
        'heating': 70,
        'cooling': 75,
        },
    'Marine': {
        'heating': 67,
        'cooling': np.nan,
        }
    }

CLIMATE_ZONE_MAPPING = {
    'Cold': 'Very-Cold/Cold',
    'Very Cold': 'Very-Cold/Cold',
    'Hot-Dry': 'Mixed-Dry/Hot-Dry',
    'Mixed-Dry': 'Mixed-Dry/Hot-Dry',
    }


def _load_mapping(filename_or_buffer):
    df = pd.read_csv(
        filename_or_buffer,
        usecols=["zipcode", "group"],
        dtype={"zipcode": str, "group": str},
    ).set_index('zipcode').drop('zipcode', errors='ignore')
    df = df.where((pd.notnull(df)), None)

    return dict(df.to_records('index'))


def retrieve_climate_zone(climate_zone_mapping, zipcode):
    """ Loads the Climate Zone to Zipcode database
    and returns the climate zone and baseline regional comfort temperatures.

    Parameters
    ----------

    climate_zone_mapping : filename, default: None

        A mapping from climate zone to zipcode. If None is provided, uses
        default zipcode to climate zone mapping provided in tutorial.

        :download:`default mapping <./resources/Building America Climate Zone to Zipcode Database_Rev2_2016.09.08.csv>`

    Returns
    -------

    climate_zone_nt : named tuple
       Named Tuple consisting of the Climate Zone, baseline_regional_cooling_comfort_temperature, and baseline_regional_heating_comfort_temperature
    """
    ClimateZone = namedtuple('ClimateZone', ['climate_zone', 'baseline_regional_cooling_comfort_temperature', 'baseline_regional_heating_comfort_temperature'])
    zipcode_details = zipcodes.matching(zipcode).pop()
    latitude = float(zipcode_details['lat'])
    longitude = float(zipcode_details['long'])
    ee_climate_zones = get_lat_long_climate_zones(latitude, longitude)
    ba_climate_zone = ee_climate_zones['ba_climate_zone']
    climate_zone = CLIMATE_ZONE_MAPPING.get(ba_climate_zone, ba_climate_zone)
    baseline_regional_cooling_comfort_temperature = BASELINE_TEMPERATURE.get(climate_zone, {}).get('cooling', None)
    baseline_regional_heating_comfort_temperature = BASELINE_TEMPERATURE.get(climate_zone, {}).get('heating', None)

    climate_zone_nt = ClimateZone(climate_zone, baseline_regional_cooling_comfort_temperature, baseline_regional_heating_comfort_temperature)
    return climate_zone_nt
