import logging
import json
from datetime import date
from functools import lru_cache
from importlib.resources import files

from eeweather import WeatherLocation, WeatherStation
from eeweather.exceptions import UnrecognizedPlaceError

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

# Fraction of the analysed hours a station must actually deliver before it
# is accepted. Measured on the loaded series, not predicted from a summary:
# the packaged observation inventory lags NOAA by about six months and
# counts observations rather than hours, so it can only ever be a proxy.
MIN_HOURLY_COVERAGE = 0.9

# How many candidates to load before giving up and taking the nearest. A
# fleet run against an unresponsive NOAA must not turn one site into an
# unbounded search.
MAX_CANDIDATES_TRIED = 3


def get_candidate_stations_by_zipcode(zipcode, required_years=None):
    """Candidate weather stations for a ZIP code / ZCTA, nearest first.

    Returns a short list rather than one station because whether a station
    has usable data cannot be known until it is loaded. ``inventory_years``
    is only ``(first, last)`` -- a span that says nothing about the interior.
    USI0000KSVE (SUSANVILLE MUNI) reports (1973, 2026) and has no rows at all
    between 1997 and 2015, so a span test picks it for a 2011-2014 analysis
    and every hour comes back NaN.

    The caller loads these in order and keeps the first that delivers; see
    thermostat.importers.get_single_thermostat. Measured over every US ZCTA,
    23 have a nearest station that reported nothing in 2025, and all 23
    recover on the second candidate, a median 9 km further away.

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
    stations : list of string
        USAF station IDs, nearest first, at most MAX_CANDIDATES_TRIED of
        them. Empty when no station could be determined.
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
        fallback = lookup_usaf_station_by_zipcode(zipcode)

        return [fallback] if fallback else []

    # Distance-ranked GHCNh candidates within the cap. Ranking (distance, then
    # quality) and the distance cap are native to rank_stations now, so the
    # hand-rolled QUALITY_SORT/re-sort is gone.
    candidates = location.candidates(
        has_sources=("ghcnh",),
        max_distance_meters=_MAX_STATION_DISTANCE_KM * 1000.0,
    )

    usaf_ids = []
    for station_id, _row in candidates.iterrows():
        station = WeatherStation(station_id)
        usaf = _usaf_id(station)
        if usaf is not None and _spans_years(station, required_years):
            usaf_ids.append(usaf)
        if len(usaf_ids) >= MAX_CANDIDATES_TRIED:
            break

    if usaf_ids:
        return usaf_ids

    logger.warning(
        "No station with data for %s within %d km of zipcode %s — "
        "falling back to JSON map.",
        required_years, _MAX_STATION_DISTANCE_KM, zipcode,
    )
    fallback = lookup_usaf_station_by_zipcode(zipcode)

    return [fallback] if fallback else []


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
