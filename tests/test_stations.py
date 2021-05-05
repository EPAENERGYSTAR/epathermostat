import pytest
from thermostat.stations import get_closest_station_by_zipcode, _zip_to_lat_long


def test_non_a_station():
    assert('A' not in get_closest_station_by_zipcode('77975'))


def test_bad_zipcode():
    assert(get_closest_station_by_zipcode('99999') is None)


def test_station_retrieval():
    assert('725370' in get_closest_station_by_zipcode('48242')) 


def test_no_station():
    assert(get_closest_station_by_zipcode('00602') is None)


def test_invalid_zcta():
    with pytest.warns(Warning):
        get_closest_station_by_zipcode('AAAAA')

def test_zip_to_lat_long():
    assert(_zip_to_lat_long('48242')) is not None, None

