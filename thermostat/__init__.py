VERSION = "2.0.0a5"


def get_version():
    return VERSION


# This try/except clause is a hack to make the get_version method work for the
# initial setup, which will fail with an ImportError because pandas hasn't yet
# been installed. Post-setup, this provides an import shortcut to Thermostat.
try:
    from .core import Thermostat  # noqa: F401
except ImportError:
    pass
