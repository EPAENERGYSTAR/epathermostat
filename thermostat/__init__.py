VERSION = (0, 2, 13)

def get_version():
    return '{}.{}.{}'.format(VERSION[0], VERSION[1], VERSION[2])

from .core import Thermostat
