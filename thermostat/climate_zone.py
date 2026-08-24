import os
from collections import namedtuple
from functools import lru_cache
from importlib.resources import files

import pandas as pd
from eeweather import WeatherLocation
from eeweather.exceptions import UnrecognizedPlaceError

REGIONAL_BASELINES_CSV = 'regional_baselines.csv'

ClimateZone = namedtuple('ClimateZone', [
    'climate_zone',
    'baseline_regional_cooling_comfort_temperature',
    'baseline_regional_heating_comfort_temperature',
])

# eeweather's eight Building America zones collapsed onto the EPA five-group
# scheme the regional baselines and statistics are keyed on.
_BA_COLLAPSE = {
    'Very Cold': 'Very-Cold/Cold',
    'Cold': 'Very-Cold/Cold',
    'Subarctic': 'Very-Cold/Cold',
    'Mixed-Dry': 'Mixed-Dry/Hot-Dry',
    'Hot-Dry': 'Mixed-Dry/Hot-Dry',
    'Mixed-Humid': 'Mixed-Humid',
    'Hot-Humid': 'Hot-Humid',
    'Marine': 'Marine',
}


@lru_cache(maxsize=None)
def _ba_climate_zone(zipcode):
    """The EPA five-group climate zone for a ZIP/ZCTA.

    From eeweather's packaged Building America geometry -- no network, no
    vendored copy. None for a ZCTA eeweather does not recognise.
    """
    try:
        zones = WeatherLocation.from_place("zcta", zipcode.zfill(5)).zones or {}
    except UnrecognizedPlaceError:
        return None

    return _BA_COLLAPSE.get(zones.get('ba_climate_zone'))


def _load_mapping(filename_or_buffer):
    df = pd.read_csv(
        filename_or_buffer,
        usecols=["zipcode", "group"],
        dtype={"zipcode": str, "group": str},
    ).set_index('zipcode').drop('zipcode', errors='ignore')
    df = df.where((pd.notnull(df)), None)

    return dict(df.to_records('index'))


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
    """ Return the climate zone and baseline regional comfort temperatures.

    Parameters
    ----------

    climate_zone_mapping : filename, file-like object, or None

        A caller-supplied zipcode -> climate zone mapping. When None (the
        default), the zone comes from eeweather's Building America geometry
        rather than a vendored table.

    zipcode : str

        The 5-digit zipcode to look up. An unrecognized zipcode yields a
        ClimateZone whose fields are all None.

    Returns
    -------

    climate_zone_nt : named tuple
       Named Tuple consisting of the Climate Zone, baseline_regional_cooling_comfort_temperature, and baseline_regional_heating_comfort_temperature
    """
    if climate_zone_mapping is None:
        climate_zone = _ba_climate_zone(zipcode)
    else:
        try:
            if isinstance(climate_zone_mapping, (str, os.PathLike)):
                mapping = _mapping_from_path(os.fspath(climate_zone_mapping))
            else:
                mapping = _load_mapping(climate_zone_mapping)
        except Exception as e:
            raise ValueError("Could not load climate zone mapping: %s" % e)
        climate_zone = mapping.get(zipcode)

    cooling_regional_baseline_temps, heating_regional_baseline_temps = \
        _regional_baselines()

    return ClimateZone(
        climate_zone,
        cooling_regional_baseline_temps.get(climate_zone, None),
        heating_regional_baseline_temps.get(climate_zone, None),
    )
