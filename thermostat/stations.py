import logging
import json
import zipcodes
import warnings
from pkg_resources import resource_stream
from eeweather import (
        get_isd_file_metadata,
        zcta_to_lat_long,
        rank_stations,
        select_station)
from eeweather.exceptions import (
        UnrecognizedZCTAError,
        UnrecognizedUSAFIDError)


logging.getLogger(__name__)
warnings.simplefilter('module', Warning)

# This is a JSON file with the zipcode to usaf_station mapping that were previously in eemeter.
with resource_stream('thermostat.resources', 'zipcode_usaf_station.json') as zipcode_usaf_stream:
    zipcode_usaf_json = zipcode_usaf_stream.read().decode()
    zipcode_usaf = json.loads(zipcode_usaf_json)

MAX_METERS = 100000

METHOD = [
        ['high', 40000],
        ['medium', 40000],
        ['high', MAX_METERS],
        ['medium', MAX_METERS],
        ]


def _zip_to_lat_long(zipcode):
    """ Returns the lat / long for a zip code, or None if none is found. """
    zip_location_list = zipcodes.matching(zipcode)
    try:
        first_location = zip_location_list.pop()
        lat = float(first_location.get('lat'))
        lon = float(first_location.get('long'))
    except Exception:
        return None, None
    return lat, lon


def _get_closest_station_by_zcta_ranked(zcta):
    """ Selects the nth ranked station from a list of ranked stations

    Parameters
    ----------
    zcta : string
        ZIP Code Tabulation Area (ZCTA)

    Returns
    -------
    station : string
        Station that was found
    lat : float
        latitude for the search
    lon : float
        longitude for the search
    """

    zcta = zcta.zfill(5)  # Ensure that we have 5 characters, and if not left-pad it with zeroes.
    try:
        lat, lon = zcta_to_lat_long(zcta)
    except UnrecognizedZCTAError:
        warnings.warn("%s is not recognized as a ZCTA. Treating as a ZIP Code instead." % zcta)
        lat, lon = _zip_to_lat_long(zcta)

    station = None

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
    """ Look up the station by ZCTA / Zip Code from eeweather
    Searches for the closest station using ZCTA or Zip Codes
    The algorithm is as follows:

    1. Get the location of the ZCTA, and fall back to ZIP if the ZCTA isn't recognized

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
        ZCTA / ZIP code to look up (referred to as zipcode in the code)

    Returns
    -------
    station : string or None
        Station that maps to the specified ZCTA / ZIP code
    """

    try:
        station, lat, lon = _get_closest_station_by_zcta_ranked(zipcode)

        if station is None:
            zipcode_mapping = zipcodes.matching(zipcode)
            warnings.warn("No station found for ZCTA / ZIP %s (%s, %s)." % (
                zipcode,
                zipcode_mapping[0].get('city'),
                zipcode_mapping[0].get('state')
                ))
            return None

        isd_metadata = get_isd_file_metadata(str(station))
        if len(isd_metadata) == 0:
            logging.warning("Zipcode %s mapped to station %s, but no ISD metadata was found." % (zipcode, station))
            return None

    except UnrecognizedUSAFIDError:
        zipcode_mapping = zipcodes.matching(zipcode)
        logging.warning("Closest station %s is not a recognized station for ZCTA / ZIP %s (%s, %s)." % (
            str(station),
            zipcode,
            zipcode_mapping[0].get('city'),
            zipcode_mapping[0].get('state')
            ))
        return None

    except TypeError as e:
        logging.warning("Unable to perform look-up for ZCTA / ZIP %s. Skipping." % zipcode)
        logging.warning(e)
        return None

    return str(station)
