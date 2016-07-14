VERSION = (0, 3, 4)

def get_version():
    return '{}.{}.{}'.format(VERSION[0], VERSION[1], VERSION[2])

# This try/except clause is a hack to make the get_version method work for the
# initial setup, which will fail with an ImportError because pandas hasn't yet
# been installed. Post-setup, this provides an import shortcut to Thermostat.
try:
    from .core import Thermostat
except ImportError:
    pass
