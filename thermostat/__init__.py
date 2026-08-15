VERSION = (1, 7, 10)

def get_version():
    return '{}.{}.{}'.format(VERSION[0], VERSION[1], VERSION[2])

# NOAA's NCEI hostnames resolve to IPv6 addresses that do not accept
# connections, which makes every weather request fail or hang on dual-stack
# hosts. Pin outbound HTTP to IPv4 before anything can open a connection. See
# thermostat/_network.py for the full rationale and the opt-out env var.
from ._network import force_ipv4
force_ipv4()

# This try/except clause is a hack to make the get_version method work for the
# initial setup, which will fail with an ImportError because pandas hasn't yet
# been installed. Post-setup, this provides an import shortcut to Thermostat.
try:
    from .core import Thermostat
except ImportError:
    pass
