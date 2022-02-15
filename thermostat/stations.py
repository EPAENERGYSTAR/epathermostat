import logging
import json
import warnings
from pkg_resources import resource_stream
from eeweather import (
        get_isd_file_metadata,
        rank_stations,
        select_station)
from eeweather.exceptions import (
        UnrecognizedUSAFIDError)
from .location_code import location_lookup


logging.getLogger(__name__)
warnings.simplefilter('module', Warning)

MAX_METERS = 100000

METHOD = [
        ['high', 40000],
        ['medium', 40000],
        ['high', MAX_METERS],
        ['medium', MAX_METERS],
        ]



def _get_closest_station_by_location_code_ranked(location_code):
    """ Selects the nth ranked station from a list of ranked stations

    Parameters
    ----------
    location_code : string
        ZIP Code / Postal Code

    Returns
    -------
    station : string
        Station that was found
    lat : float
        latitude for the search
    lon : float
        longitude for the search
    """

    lat, lon = location_lookup(location_code)
    station = None

    if lat and lon:
        for min_quality, max_distance_meters in METHOD:
            station_ranking = rank_stations(lat, lon, minimum_quality=min_quality, max_distance_meters=max_distance_meters)
            # Remove airport stations like A00008
            if len(station_ranking) > 0:
                station_ranking = station_ranking[station_ranking.index.str.contains('^[0-9]')]

                station, _ = select_station(station_ranking)
                if station:
                    break

    return station, lat, lon


def get_closest_station_by_location_code(location_code):
    """ Look up the station by ZIP Code / Postal Code from eeweather
    Searches for the closest station using ZIP Code / Postal Code
    The algorithm is as follows:

    1. Get the location of the ZIP Code / Postal Code

    2. Select the station that is the closest with the highest quality using the following method:
        * high quality stations within 40,000 meters
        * medium quality stations within 40,000 meters
        * high quality stations within 100,000 meters
        * medium quality stations within 100,000 meters

    3. If no station is returned then we log a warning message. Nothing is returned.

    4. If the station is unrecognized (:code:`UnrecognizedUSAFIDError`) then we log a warning message. Nothing is returned.

    Parameters
    ----------
    location_code : string
        ZIP Code / Postal Code to look up

    Returns
    -------
    station : string or None
        Station that maps to the specified location code
    """

    try:
        station, lat, lon = _get_closest_station_by_location_code_ranked(location_code)

        logging.debug(f'Station: {station}, Latitude: {lat}, Longitude: {lon}')

        if station is None:
            warnings.warn(f"No station found for location code {location_code}")
            return None

        isd_metadata = get_isd_file_metadata(str(station))
        if len(isd_metadata) == 0:
            logging.warning(f"Location code {location_code} mapped to station {station}, but no ISD metadata was found.")
            return None

    except UnrecognizedUSAFIDError:
        logging.warning(f"Closest station {station} is not a recognized station for Location Code {location_code}.")
        return None

    return str(station)
