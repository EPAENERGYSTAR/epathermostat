import pandas as pd
from pkg_resources import resource_stream
from collections import namedtuple


def _load_mapping(filename_or_buffer):
    df = pd.read_csv(
        filename_or_buffer,
        usecols=["zipcode", "group"],
        dtype={"zipcode": str, "group": str},
    ).set_index('zipcode').drop('zipcode')
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
    if climate_zone_mapping is None:
        with resource_stream(
                'thermostat.resources',
                'Building America Climate Zone to Zipcode Database_Rev2_2016.09.08.csv') as f:
            mapping = _load_mapping(f)
    else:
        try:
            mapping = _load_mapping(climate_zone_mapping)
        except Exception as e:
            raise ValueError("Could not load climate zone mapping: %s" % e)

    with resource_stream('thermostat.resources', 'regional_baselines.csv') as f:
        df = pd.read_csv(
            f, usecols=[
                'EIA Climate Zone',
                'Baseline heating temp (F)',
                'Baseline cooling temp (F)'
            ])
        df = df.where((pd.notnull(df)), None)
        df = df.set_index('EIA Climate Zone')
        cooling_regional_baseline_temps = {k: v for k, v in df['Baseline cooling temp (F)'].iteritems()}
        heating_regional_baseline_temps = {k: v for k, v in df['Baseline heating temp (F)'].iteritems()}

    climate_zone = mapping.get(zipcode)
    baseline_regional_cooling_comfort_temperature = cooling_regional_baseline_temps.get(climate_zone, None)
    baseline_regional_heating_comfort_temperature = heating_regional_baseline_temps.get(climate_zone, None)

    climate_zone_nt = ClimateZone(climate_zone, baseline_regional_cooling_comfort_temperature, baseline_regional_heating_comfort_temperature)

    return climate_zone_nt
