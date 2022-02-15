import logging
import zipcodes
from postalcodes_ca import postal_codes, parse_postal_code


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


def _postal_code_to_lat_long(postal_code):
    """ Returns the lat / long for a postal code or None if none is found """
    try:
        postal_code = parse_postal_code(postal_code)  # Do some rudimentary cleaning
        location = postal_codes[postal_code]
        lat = float(location.latitude)
        lon = float(location.longitude)
    except ValueError:
        logging.warning(f'Postal Code {postal_code} is invalid')
        return None, None
    return lat, lon


def location_lookup(location_code):
    """TODO: Docstring for location_lookup.
    :returns: TODO

    """

    lat = None
    lon = None

    if len(location_code) > 5:
        # Looks like a Canadian Postal Code
        lat, lon = _postal_code_to_lat_long(location_code)
    else:
        # Assume that we have a ZIP Code
        location_code = location_code.zfill(5)  # Ensure that we have 5 characters, and if not left-pad it with zeroes.
        lat, lon = _zip_to_lat_long(location_code)
    return lat, lon
