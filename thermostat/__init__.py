import os

from ._version import __version__

# eeweather otherwise refreshes its station registry in the background from
# upstream's rolling release. thermostat pins one eeweather build and uses the
# registry that build shipped with, so station selection is reproducible run
# to run and a registry published later for newer eeweather code is never
# loaded into this one. Set EEWEATHER_AUTO_UPDATE=1 to opt back in.
os.environ.setdefault("EEWEATHER_AUTO_UPDATE", "0")

VERSION = tuple(int(part) for part in __version__.split("."))


def get_version():
    return __version__


from .core import Thermostat  # noqa: E402  (import shortcut, needs __version__ first)

__all__ = ("Thermostat", "VERSION", "__version__", "get_version")
