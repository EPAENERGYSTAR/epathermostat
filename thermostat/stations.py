import logging
from datetime import date

from eeweather import WeatherLocation, WeatherStation
from eeweather.exceptions import UnrecognizedPlaceError

logger = logging.getLogger(__name__)


# Maximum distance (km) from ZCTA centroid to assigned station.
_MAX_STATION_DISTANCE_KM = 500

# Coverage that makes a station good enough to stop looking -- a search
# short-circuit, not an exclusion gate. The importer keeps the best-covered
# candidate regardless; the per-day core-day rule is the real gate.
MIN_HOURLY_COVERAGE = 0.9

# Bound on candidates loaded, so an unresponsive NOAA can't make one site an
# unbounded search. A network-cost knob, not a correctness gate: the importer
# keeps the best of whatever it loads, and the per-day core-day rule backstops
# a too-thin result. Offline over every US ZCTA, 96% clear the bar on the first
# candidate and 99.9% within three; five covers the deepest observed with
# margin (the inventory proxy understates real depth, so headroom is deliberate).
MAX_CANDIDATES_TRIED = 5


def get_candidate_stations_by_zipcode(zipcode, required_years=None):
    """Candidate weather stations for a ZIP code / ZCTA, nearest first.

    Returns a short list rather than one station because whether a station
    has usable data cannot be known until it is loaded. ``inventory_years``
    is only ``(first, last)`` -- a span that says nothing about the interior.
    USI0000KSVE (SUSANVILLE MUNI) reports (1973, 2026) and has no rows at all
    between 1997 and 2015, so a span test picks it for a 2011-2014 analysis
    and every hour comes back NaN.

    The caller loads these in order and keeps the best-covered; see
    thermostat.importers._load_outdoor_temperatures.

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
        logger.warning("No ZCTA %s in the registry; no station.", zipcode)
        return []

    # Distance-ranked GHCNh candidates within the cap; ranking and cap are native to rank_stations.
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
        "No station with data for %s within %d km of zipcode %s.",
        required_years, _MAX_STATION_DISTANCE_KM, zipcode,
    )
    return []


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

