import logging
import json
import zipcodes
import warnings
from pkg_resources import resource_stream
from eeweather import (
        get_isd_file_metadata,
        rank_stations,
        select_station)
from eeweather.exceptions import (
        UnrecognizedUSAFIDError)


logging.getLogger(__name__)
warnings.simplefilter('module', Warning)

MAX_METERS = 100000

METHOD = [
        ['high', 40000],
        ['medium', 40000],
        ['high', MAX_METERS],
        ['medium', MAX_METERS],
        ]


def _zip_to_lat_long(zipcode):
    """ Returns the lat / long for a zip code, or None if none is found. """
    try:
        zip_location_list = zipcodes.matching(zipcode)
        first_location = zip_location_list.pop()
        lat = float(first_location.get('lat'))
        lon = float(first_location.get('long'))
    except ValueError:
        logging.warning(f'ZIP Code {zipcode} is invalid')
        return None, None
    except IndexError:
        logging.warning(f'No locations found for ZIP Code {zipcode}')
        return None, None
    return lat, lon


def _get_closest_station_by_zipcode_ranked(zipcode):
    """ Selects the nth ranked station from a list of ranked stations

    Parameters
    ----------
    zipcode : string
        ZIP Code

    Returns
    -------
    station : string
        Station that was found
    lat : float
        latitude for the search
    lon : float
        longitude for the search
    """

    zipcode = zipcode.zfill(5)  # Ensure that we have 5 characters, and if not left-pad it with zeroes.
    lat, lon = _zip_to_lat_long(zipcode)

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


def get_closest_station_by_zipcode(zipcode):
    """ Look up the station by ZIP Code from eeweather
    Searches for the closest station using ZIP Codes
    The algorithm is as follows:

    1. Get the location of the ZIP Code

    2. Select the station that is the closest with the highest quality using the following method:
        * high quality stations within 40,000 meters
        * medium quality stations within 40,000 meters
        * high quality stations within 100,000 meters
        * medium quality stations within 100,000 meters

    3. If no station is returned then we log a warning message. Nothing is returned.

    4. If the station is unrecognized (:code:`UnrecognizedUSAFIDError`) then we log a warning message. Nothing is returned.

    Parameters
    ----------
    zipcode : string
        ZIP code to look up

    Returns
    -------
    station : string or None
        Station that maps to the specified ZIP code
    """

    try:
        station, lat, lon = _get_closest_station_by_zipcode_ranked(zipcode)

        if station is None:
            warnings.warn(f"No station found for ZIP {zipcode}")
            return None

        isd_metadata = get_isd_file_metadata(str(station))
        if len(isd_metadata) == 0:
            logging.warning(f"ZIP code {zipcode} mapped to station {station}, but no ISD metadata was found.")
            return None

    except UnrecognizedUSAFIDError:
        logging.warning(f"Closest station {station} is not a recognized station for ZIP {zipcode}.")
        return None

    return str(station)
