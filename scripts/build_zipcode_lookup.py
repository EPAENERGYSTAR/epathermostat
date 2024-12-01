import pgeocode
import eeweather
import collections
from pprint import pprint
from thermostat.stations import get_closest_station_by_zipcode, USA_ISO_COUNTRY_CODES
from thermostat.climate_zone import retrieve_climate_zone
from multiprocessing import Pool, cpu_count
from functools import partial
from datetime import datetime


import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def get_station_climate_zone(zipcode_obj):
    try:
        zipcode = zipcode_obj
        station = get_closest_station_by_zipcode(zipcode)
        climate_zone_nt = retrieve_climate_zone(zipcode)
    except Exception as e:
        return None, None, None
    return zipcode, station, climate_zone_nt.climate_zone


def main(countries=USA_ISO_COUNTRY_CODES):
    """This code looks up all available zip codes and generates a data file with station and climate zone lookups"""
    zipcode_lookup = {}

    p = Pool()
    multiprocess_func_partial = partial(
        get_station_climate_zone,
        )
    us_zipcodes = sum((pgeocode.Nominatim(code)._data['postal_code'].tolist() for code in countries), [])
    result_list = p.imap(multiprocess_func_partial, us_zipcodes)
    p.close()
    p.join()

    for result in result_list:
        zipcode, station, climate_zone = result
        zipcode_lookup[zipcode] = {}
        zipcode_lookup[zipcode]['station'] = station
        zipcode_lookup[zipcode]['climate_zone'] = climate_zone

    sorted_zipcode_lookup = collections.OrderedDict(sorted(zipcode_lookup.items()))
    print('from collections import OrderedDict')
    print(f"# zipcodes version {pgeocode.__version__}")
    print(f"# eeweather version {eeweather.__version__}")
    print(f"# date {datetime.now()}")
    print()
    print("ZIPCODE_LOOKUP = \\")
    pprint(sorted_zipcode_lookup)


if __name__ == '__main__':
    main()
