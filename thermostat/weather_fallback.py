import logging
from datetime import datetime

import pandas as pd
import pytz
import requests

logger = logging.getLogger(__name__)

_NCEI_URL = "https://www.ncei.noaa.gov/access/services/data/v1"


def fetch_ghcnh_hourly_temp_data(wban_id, start, end):
    """Fetch hourly temperature data from NOAA GHCN-H for a WBAN station.

    Parameters
    ----------
    wban_id : str
        WBAN station identifier (will be zero-padded to construct GHCN-H ID).
    start : pd.Timestamp
        UTC start of the date range (date component used).
    end : pd.Timestamp
        UTC end of the date range (date component used).

    Returns
    -------
    pd.Series
        UTC-indexed hourly temperature in Celsius.
        Returns an empty Series (never raises) on any network or parse failure.
    """
    _empty = pd.Series([], index=pd.DatetimeIndex([], tz=pytz.UTC), dtype=float)

    ghcnh_id = "USW{}".format(str(wban_id).zfill(8))
    params = {
        "dataset": "global-historical-climatology-network-hourly",
        "stations": ghcnh_id,
        "startDate": start.strftime("%Y-%m-%d"),
        "endDate": end.strftime("%Y-%m-%d"),
        "dataTypes": "DATE,temperature",
        "format": "json",
    }

    try:
        resp = requests.get(_NCEI_URL, params=params, timeout=60)
        resp.raise_for_status()
        records = resp.json()
    except Exception as exc:
        logger.warning("GHCN-H request failed for station %s: %s", ghcnh_id, exc)
        return _empty

    if not records:
        return _empty

    try:
        dates = []
        temps = []
        for record in records:
            try:
                temp = float(record["temperature"])
            except (KeyError, ValueError, TypeError):
                continue
            dt = pytz.UTC.localize(
                datetime.strptime(record["DATE"], "%Y-%m-%dT%H:%M:%S")
            )
            dates.append(dt)
            temps.append(temp)

        if not dates:
            return _empty

        ts = pd.Series(temps, index=dates, dtype=float)
        ts = ts.groupby(ts.index).mean()
        return ts.resample("H").mean()

    except Exception as exc:
        logger.warning("GHCN-H response parsing failed for station %s: %s", ghcnh_id, exc)
        return _empty
