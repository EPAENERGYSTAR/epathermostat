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

# Sort order for rough_quality (returned by eeweather).
QUALITY_SORT = {'high': 0, 'medium': 1, 'low': 2}


def _rank_stations_by_distance_and_quality(lat, lon):
    """ Ranks the stations by distance and quality based on latitude / longitude

    Parameters
    ----------
    lat : float
        latitude for the search
    lon : float
        longitude for the search

    Returns
    -------
    station_ranking : Pandas.DataFrame
    """

    station_ranking = rank_stations(lat, lon)
    station_ranking['enumerated_quality'] = station_ranking['rough_quality'].map(QUALITY_SORT)
    station_ranking = station_ranking.sort_values(by=['distance_meters', 'enumerated_quality'])
    return station_ranking


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

    lat, lon = zcta_to_lat_long(zcta)
    finding_station = True
    rank = 0
    while finding_station:
        rank = rank + 1
        station_ranking = _rank_stations_by_distance_and_quality(lat, lon)
        station, warnings = select_station(station_ranking, rank=rank)

        # Ignore stations that begin with A
        if str(station)[0] != 'A':
            finding_station = False

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

    7. If the station is over 50,000 meters from the ZCTA location then we log a warning message and revert to the backup method.

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
