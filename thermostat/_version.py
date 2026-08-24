"""Single source of the package version.

Kept import-free so packaging metadata can read the literal without importing
thermostat (which pulls in pandas, numpy and eeweather).
"""
__version__ = "1.8.1"
