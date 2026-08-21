import os
from collections import namedtuple
from functools import lru_cache
from importlib.resources import files

import pandas as pd

CLIMATE_ZONE_CSV = (
    'Building America Climate Zone to Zipcode Database_Rev2_2016.09.08.csv')
REGIONAL_BASELINES_CSV = 'regional_baselines.csv'

ClimateZone = namedtuple('ClimateZone', [
    'climate_zone',
    'baseline_regional_cooling_comfort_temperature',
    'baseline_regional_heating_comfort_temperature',
])


def _load_mapping(filename_or_buffer):
    df = pd.read_csv(
        filename_or_buffer,
        usecols=["zipcode", "group"],
        dtype={"zipcode": str, "group": str},
    ).set_index('zipcode').drop('zipcode', errors='ignore')
    df = df.where((pd.notnull(df)), None)

    return dict(df.to_records('index'))


@lru_cache(maxsize=None)
def _default_mapping():
    """The packaged zipcode -> climate zone mapping.

    Cached because it is ~730 kB of CSV and retrieve_climate_zone is called
    once per thermostat; it used to be re-parsed on every one of those calls.
    """
    with (files('thermostat.resources') / CLIMATE_ZONE_CSV).open('rb') as f:
        return _load_mapping(f)


@lru_cache(maxsize=None)
def _mapping_from_path(path):
    return _load_mapping(path)


@lru_cache(maxsize=None)
def _regional_baselines():
    """(cooling, heating) baseline comfort temperatures by climate zone."""
    with (files('thermostat.resources') / REGIONAL_BASELINES_CSV).open('rb') as f:
        df = pd.read_csv(
            f, usecols=[
                'EIA Climate Zone',
                'Baseline heating temp (F)',
                'Baseline cooling temp (F)'
            ])
    df = df.where((pd.notnull(df)), None)
    df = df.set_index('EIA Climate Zone')

    cooling = {k: v for k, v in df['Baseline cooling temp (F)'].items()}
    heating = {k: v for k, v in df['Baseline heating temp (F)'].items()}
    return cooling, heating


def retrieve_climate_zone(climate_zone_mapping, zipcode):
    """ Loads the Climate Zone to Zipcode database
    and returns the climate zone and baseline regional comfort temperatures.

    Parameters
    ----------

    climate_zone_mapping : filename, file-like object, or None

        A mapping from climate zone to zipcode. If None is provided, uses
        default zipcode to climate zone mapping provided in tutorial.

        :download:`default mapping <./resources/Building America Climate Zone to Zipcode Database_Rev2_2016.09.08.csv>`

    zipcode : str

        The 5-digit zipcode to look up. An unrecognized zipcode yields a
        ClimateZone whose fields are all None.

    Returns
    -------

    climate_zone_nt : named tuple
       Named Tuple consisting of the Climate Zone, baseline_regional_cooling_comfort_temperature, and baseline_regional_heating_comfort_temperature
    """
    if climate_zone_mapping is None:
        mapping = _default_mapping()
    else:
        try:
            # Paths are cached; file-like objects cannot be (they are
            # consumed by the read), so those are parsed every call.
            if isinstance(climate_zone_mapping, (str, os.PathLike)):
                mapping = _mapping_from_path(os.fspath(climate_zone_mapping))
            else:
                mapping = _load_mapping(climate_zone_mapping)
        except Exception as e:
            raise ValueError("Could not load climate zone mapping: %s" % e)

    cooling_regional_baseline_temps, heating_regional_baseline_temps = \
        _regional_baselines()

    climate_zone = mapping.get(zipcode)

    return ClimateZone(
        climate_zone,
        cooling_regional_baseline_temps.get(climate_zone, None),
        heating_regional_baseline_temps.get(climate_zone, None),
    )
