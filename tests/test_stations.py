import pytest
from thermostat.stations import get_closest_station_by_location_code, _zip_to_lat_long


def test_non_a_station():
    assert('A' not in get_closest_station_by_location_code('77975'))


def test_bad_location_code():
    assert(get_closest_station_by_location_code('99999') is None)


def test_station_retrieval():
    assert('725370' in get_closest_station_by_location_code('48242')) 


def test_no_station():
    assert(get_closest_station_by_location_code('00602') is None)


def test_invalid_zcta():
    with pytest.warns(Warning):
        get_closest_station_by_location_code('AAAAA')

def test_zip_to_lat_long():
    assert(_zip_to_lat_long('48242')) is not None, None
