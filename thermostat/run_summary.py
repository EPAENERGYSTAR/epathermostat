""" Accounting for the thermostats that do not make it into the output.

A run drops records at two points: during import, when the interval data or
the weather cannot be loaded at all, and during the metrics calculation, when
a thermostat loads cleanly but qualifies for no core days. Both used to be
reported only as log lines, so a fleet that lost three percent of its records
to dead weather stations produced the same output file as one that lost none.

This module makes those drop-outs a data product: one row per lost
thermostat, with the stage, a stable machine-readable reason, and the detail
needed to act on it.
"""
from collections import Counter, namedtuple

import pandas as pd


# One lost thermostat. stage is 'import' or 'metrics'; reason is a stable slug.
DropOut = namedtuple(
    "DropOut", ["thermostat_id", "zipcode", "station", "stage", "reason", "detail"])

COLUMNS = list(DropOut._fields)

# Stable reason slugs. Names, not free text, so a run-over-run comparison can
# tell "we lost 40 more to dead stations" from "we lost 40 more to bad files".
UNSUPPORTED_EQUIPMENT_TYPE = "unsupported_equipment_type"
STATION_NOT_FOUND = "station_not_found"
WEATHER_DATA_NOT_AVAILABLE = "weather_data_not_available"
INVALID_INTERVAL_DATA = "invalid_interval_data"
INVALID_UTC_OFFSET = "invalid_utc_offset"
UNEXPECTED_ERROR = "unexpected_error"
NO_QUALIFYING_CORE_DAYS = "no_qualifying_core_days"


class RunSummary(object):
    """ What a run was asked to do and what it actually did.

    Attributes
    ----------
    requested : int
        Rows read from the metadata file.
    drop_outs : list of DropOut
        One entry per thermostat that produced no output, in the order the
        loss was detected.
    """

    def __init__(self, requested=0, shuffle=None, seed=None):
        self.requested = requested
        self.shuffle = shuffle
        #: The seed the row order was produced with. Recorded even when the
        #: caller supplied none, so the order can be reproduced after the fact.
        self.seed = seed
        self.drop_outs = []

    @property
    def dropped(self):
        return len(self.drop_outs)

    @property
    def delivered(self):
        """ Thermostats that contributed at least one row to the output. """
        return self.requested - self.dropped

    @property
    def completeness(self):
        """ Delivered as a fraction of requested, or NaN for an empty run. """
        if self.requested == 0:
            return float("nan")
        return self.delivered / self.requested

    def record(self, thermostat_id, stage, reason, detail,
               zipcode=None, station=None):
        self.drop_outs.append(DropOut(
            thermostat_id=thermostat_id, zipcode=zipcode, station=station,
            stage=stage, reason=reason, detail=detail))

    def extend(self, drop_outs):
        self.drop_outs.extend(drop_outs)

    def by_reason(self):
        """ Counter of drop-outs keyed on ``(stage, reason)``. """
        return Counter((d.stage, d.reason) for d in self.drop_outs)

    def to_dataframe(self):
        return pd.DataFrame(self.drop_outs, columns=COLUMNS)

    def to_csv(self, filepath):
        """ Write one row per drop-out, with the header even when there are none. """
        df = self.to_dataframe()
        df.to_csv(filepath, index=False)
        return df

    def describe(self):
        """ A short block suitable for logging at the end of a run. """
        lines = ["thermostats requested: {}".format(self.requested),
                 "thermostats delivered: {} ({:.1%})".format(
                     self.delivered, self.completeness),
                 "thermostats dropped:   {}".format(self.dropped)]
        if self.shuffle:
            lines.append("row order seed:        {} (pass seed={} to reproduce)"
                         .format(self.seed, self.seed))
        elif self.shuffle is False:
            lines.append("row order:             input order (not shuffled)")
        for (stage, reason), count in sorted(self.by_reason().items()):
            lines.append("  {:<8} {:<28} {}".format(stage, reason, count))
        return "\n".join(lines)

    def __repr__(self):
        return "RunSummary(requested={}, delivered={}, dropped={}, seed={})".format(
            self.requested, self.delivered, self.dropped, self.seed)
