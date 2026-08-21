from ._version import __version__

VERSION = tuple(int(part) for part in __version__.split("."))


def get_version():
    return __version__


from .core import Thermostat  # noqa: E402  (import shortcut, needs __version__ first)

__all__ = ("Thermostat", "VERSION", "__version__", "get_version")
