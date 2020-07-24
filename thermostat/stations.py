import logging
import json
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

# This is a JSON file with the zipcode to usaf_station mapping that were previously in eemeter.
zipcode_usaf_json = resource_stream('thermostat.resources', 'zipcode_usaf_station.json').read().decode()
zipcode_usaf = json.loads(zipcode_usaf_json)

MAX_METERS = 100000

METHOD = [
        ['high', 40000],
        ['medium', 40000],
        ['high', MAX_METERS],
        ['medium', MAX_METERS],
        ]


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
    warnings : list
        List of warnings for the returned station (includes distance warnings)
    lat : float
        latitude for the search
    lon : float
        longitude for the search
    """

    zcta = zcta.zfill(5)  # Ensure that we have 5 characters, and if not left-pad it with zeroes.
    lat, lon = zcta_to_lat_long(zcta)

    station = None
    warnings = []

    for min_quality, max_distance_meters in METHOD:
        station_ranking = rank_stations(lat, lon, minimum_quality=min_quality, max_distance_meters=max_distance_meters)
        # Remove airport stations like A00008
        if len(station_ranking) > 0:
            station_ranking = station_ranking[station_ranking.index.str.contains('^[0-9]')]

            station, warnings = select_station(station_ranking, distance_warnings=(max_distance_meters, MAX_METERS))
            if station and len(warnings) == 0:
                break

    return station, warnings, lat, lon


def get_closest_station_by_zipcode(zipcode):
    """ Look up the station by ZCTA / Zip Code from eeweather
    Searches for a particular station using the ZCTA lookup for a particular zip code (from eeweather).
    The algorithm is as follows:

    1. Get a ranking of stations by distance and rough quality (quality is defined as high, medium, or low).

    2. Select the station that is the closest with the highest quality.

    3. Check to see if there are any ISD files associated with the station. If not revert to the backup method.

    4. If the station is unrecognized (:code:`UnrecognizedUSAFIDError`) then revert to the backup method.

    5. If the ZCTA is unrecognized (:code:`UnrecognizedZCTAError`) then return `None`. No station will be selected.

    6. If the station selected is not the station that would be selected via
       the zip code method then we log a debug message for what we would have previously returned

    Parameters
    ----------
    zipcode : string
        zipcode / ZCTA to look up (referred to as zipcode because this is also used for the backup method)

    Returns
    -------
    station : string or None
        Station that maps to the specified zipcode / ZCTA
    """

    station_lookup_method_by_zipcode = lookup_usaf_station_by_zipcode(zipcode)
    try:
        station, warnings, lat, lon = _get_closest_station_by_zcta_ranked(zipcode)

        isd_metadata = get_isd_file_metadata(str(station))
        if len(isd_metadata) == 0:
            logging.warning("Zipcode %s mapped to station %s, but no ISD metadata was found." % (zipcode, station))
            return station_lookup_method_by_zipcode

    except UnrecognizedUSAFIDError as e:
        logging.warning("Closest station %s is not a recognized station. Using backup-method station %s for zipcode %s instead." % (
            str(station),
            station_lookup_method_by_zipcode,
            zipcode))
        return station_lookup_method_by_zipcode

    except UnrecognizedZCTAError as e:
        logging.warning("Unrecognized ZCTA %s" % e)
        return None

    if str(station) != station_lookup_method_by_zipcode:
        logging.debug("Previously would have selected station %s instead of %s for zip code %s" % (
            station_lookup_method_by_zipcode,
            str(station),
            zipcode))

    if warnings:
        logging.warning("Station %s is %d meters over maximum %d meters (%d meters) (zip code %s is at lat/lon %f, %f)" % (
            str(station),
            int(warnings[0].data['distance_meters'] - warnings[0].data['max_distance_meters']),
            int(warnings[0].data['max_distance_meters']),
            int(warnings[0].data['distance_meters']),
            zipcode,
            lat,
            lon,
            ))
        logging.warning("Closest station %s is too far. Using backup-method station %s instead." % (
            str(station),
            station_lookup_method_by_zipcode))
        return station_lookup_method_by_zipcode

    return str(station)


def lookup_usaf_station_by_zipcode(zipcode):
    """ Backup method for determining which station matches which zipcode

    Parameters
    ----------

    zipcode : string
        zipcode to search

    Returns
    -------

    station : string or None
       Station that matches the zipcode
    """

    usaf = zipcode_usaf.get(zipcode, None)
    return usaf
