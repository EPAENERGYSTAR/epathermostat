"""Exceptions raised while importing thermostats.

These exist so that the import loop can tell *why* a thermostat was skipped.
Before, a missing weather station raised RuntimeError while the handler that
carried the ZIP-vs-ZCTA explanation caught ValueError, so that explanation
never reached the case it was written for and the real failure fell through to
a catch-all.
"""


class ThermostatImportError(Exception):
    """Base for every reason a single thermostat could not be imported."""


class StationNotFoundError(ThermostatImportError):
    """No weather station with data for the analysed years serves this ZIP."""


class InvalidIntervalDataError(ThermostatImportError):
    """The interval data file is missing, misshapen, or has bad dates."""


class InvalidUTCOffsetError(ThermostatImportError, TypeError):
    """The metadata row's utc_offset could not be parsed.

    Also a TypeError, which is what normalize_utc_offset raised before this
    type existed and what callers outside the import loop still catch.
    """
