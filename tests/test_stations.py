import pytest
from thermostat.stations import get_closest_station_by_zipcode


def test_non_a_station():
    assert('A' not in get_closest_station_by_zipcode('77975'))
