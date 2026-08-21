import logging
import json
from datetime import date, datetime, timezone
from functools import lru_cache
from importlib.resources import files

from eeweather import WeatherLocation, WeatherStation
from eeweather.exceptions import UnrecognizedPlaceError

try:
    # Added by an eeweather pull request; until it lands upstream, station
    # selection falls back to the inventory-span test it has always used.
    from eeweather.registry.coverage import get_station_coverage
except ImportError:  # pragma: no cover - depends on the installed eeweather
    get_station_coverage = None

logger = logging.getLogger(__name__)


@lru_cache(maxsize=None)
def _zipcode_usaf():
    """Static JSON fallback map (committed resource), used only when the
    reshaped eeweather registry can't resolve a ZCTA to a station.

    Loaded on first use rather than at import: it is ~700 kB, every worker
    process paid for it, and the fallback is rarely reached. The parsed dict
    is kept; the raw text is not.
    """
    with (files('thermostat.resources') / 'zipcode_usaf_station.json').open('rb') as f:
        return json.load(f)

# Maximum distance (km) from ZCTA centroid to assigned station.
_MAX_STATION_DISTANCE_KM = 500

# Fraction of the analysed months a station must have reported through.
_MIN_COVERAGE = 0.9


def get_closest_station_by_zipcode(zipcode, required_years=None):
    """Return the nearest weather station for a ZIP code / ZCTA whose GHCNh
    record covers the years being analysed.

    Ranks the ZCTA's candidate GHCNh stations by distance (within 500 km of the
    ZCTA centroid) and selects the nearest whose registry inventory covers every
    year in *required_years*. Falls back to the static JSON map when eeweather
    does not recognise the ZCTA or no qualifying station is found in range.

    Parameters
    ----------
    zipcode : string
        5-digit ZIP code or ZCTA.
    required_years : list of int, optional
        Calendar years the station must have data for. Callers running
        historical data should pass the years spanned by that data so station
        selection matches the analysed period rather than the current calendar
        year. Defaults to [today.year-1, today.year] when not supplied.

    Returns
    -------
    station : string or None
        USAF station ID, or None if no station could be determined.
    """
    if required_years is None:
        today = date.today()
        required_years = [today.year - 1, today.year]

    try:
        location = WeatherLocation.from_place(
            "zcta", zipcode.zfill(5), sources=("ghcnh",)
        )
    except UnrecognizedPlaceError:
        logger.warning("Unrecognized ZCTA %s — falling back to JSON map.", zipcode)
        return lookup_usaf_station_by_zipcode(zipcode)

    # Distance-ranked GHCNh candidates within the cap. Ranking (distance, then
    # quality) and the distance cap are native to rank_stations now, so the
    # hand-rolled QUALITY_SORT/re-sort is gone.
    candidates = location.candidates(
        has_sources=("ghcnh",),
        max_distance_meters=_MAX_STATION_DISTANCE_KM * 1000.0,
    )

    # Two passes over the same distance-ranked list. The first requires the
    # station to have actually reported during the analysed years; the second
    # accepts a span match, which is what this used to do on its own.
    fallback = None
    for station_id, _row in candidates.iterrows():
        station = WeatherStation(station_id)
        usaf = _usaf_id(station)
        if usaf is None or not _spans_years(station, required_years):
            continue
        if fallback is None:
            fallback = usaf
        if _reported_during(station, required_years):
            return usaf

    if fallback is not None:
        logger.warning(
            "No station within %d km of zipcode %s reported during %s; using "
            "the nearest station whose inventory spans those years.",
            _MAX_STATION_DISTANCE_KM, zipcode, required_years,
        )
        return fallback

    logger.warning(
        "No station with data for %s within %d km of zipcode %s — "
        "falling back to JSON map.",
        required_years, _MAX_STATION_DISTANCE_KM, zipcode,
    )
    return lookup_usaf_station_by_zipcode(zipcode)


def _usaf_id(station):
    """The station's USAF id, or None if it has none or is Canadian."""
    usaf_ids = station.ids.get("usaf") or ()
    usaf = usaf_ids[0] if usaf_ids else None
    if usaf is None or str(usaf).startswith("A"):  # skip Canadian airport codes
        return None

    return str(usaf)


def _spans_years(station, required_years):
    """Whether the station's inventory span encloses every required year.

    A span is (first, last) and says nothing about what lies between, so this
    is a cheap necessary condition, not a sufficient one.
    """
    inventory = station.inventory_years.get("ghcnh")
    if not inventory:
        return False
    first, last = inventory

    return all(first <= year <= last for year in required_years)


def _reported_during(station, required_years):
    """Whether the station actually reported through the analysed years.

    Answered from eeweather's packaged observation inventory when that
    version exposes it. ``inventory_years`` is only ``(first, last)`` -- a
    span, which says nothing about what lies between. USI0000KSVE
    (SUSANVILLE MUNI) reports a span of (1973, 2026) and has no rows at all
    between 1997 and 2015, so the span test picks it for a 2011-2014
    analysis and every hour comes back NaN.

    Deliberately not answered from ``get_quality``: 'low' rates
    *reliability*, not presence. Of four stations this rejects on quality in
    the test corpus, three carry 90-99% of the hours -- swapping them for
    more distant ones would change a regulated result for no coverage
    reason.

    Returns True when the running eeweather cannot answer, so behavior is
    unchanged until the coverage API is available.
    """
    if get_station_coverage is None:
        return True

    start = datetime(min(required_years), 1, 1, tzinfo=timezone.utc)
    end = datetime(max(required_years), 12, 31, tzinfo=timezone.utc)

    return get_station_coverage(station.id, start, end) >= _MIN_COVERAGE


def lookup_usaf_station_by_zipcode(zipcode):
    """Static JSON map lookup (fallback method).

    Parameters
    ----------
    zipcode : string

    Returns
    -------
    station : string or None
    """
    return _zipcode_usaf().get(zipcode, None)
