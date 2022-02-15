import zipcodes
from postalcodes_ca import postal_codes
import eeweather
import collections
from pprint import pprint
from thermostat.stations import get_closest_station_by_location_code
from thermostat.climate_zone import retrieve_climate_zone
from multiprocessing import Pool, cpu_count
from functools import partial


import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def get_station_climate_zone(location_code):
    try:
        station = get_closest_station_by_location_code(location_code)
        climate_zone_nt = retrieve_climate_zone(location_code)
    except Exception:
        return None, None, None
    return location_code, station, climate_zone_nt.climate_zone


def main():
    """This code looks up all available zip codes and generates a data file with station and climate zone lookups"""
    location_code_lookup = {}

    p = Pool()
    multiprocess_func_partial = partial(
        get_station_climate_zone,
        )

    postal_codes_list = list(postal_codes.keys())
    postal_codes_list = postal_codes_list[:100]
    zip_codes_list = [zipcode['zip_code'] for zipcode in zipcodes.list_all()]
    zip_codes_list = zip_codes_list[:100]
    location_codes_list = postal_codes_list + zip_codes_list
    result_list = p.imap(multiprocess_func_partial, location_codes_list)
    p.close()
    p.join()

    for result in result_list:
        location_code, station, climate_zone = result
        location_code_lookup[location_code] = {}
        location_code_lookup[location_code]['station'] = station
        location_code_lookup[location_code]['climate_zone'] = climate_zone

    sorted_location_code_lookup = collections.OrderedDict(sorted(location_code_lookup.items()))
    print('from collections import OrderedDict')
    print(f"# zipcodes version {zipcodes.__version__}")
    print(f"# postalcodes_ca version 0.8")
    print(f"# eeweather version {eeweather.__version__}")
    print()
    print("LOCATION_CODE_LOOKUP = \\")
    pprint(sorted_location_code_lookup)


if __name__ == '__main__':
    main()
