import pandas

HEAT_TYPE = [
    'non_heat_pump',  # Non heat pump heating (gas or oil furnace, electric resistance)
    'heat_pump_electric_backup',   # Heat pump with electric resistance heat (strip heat)
    'heat_pump_no_electric_backup',  # Heat pump without electric resistance heat
    'heat_pump_dual_fuel',  # Dual fuel heat pump (e.g. gas or oil fired)
    'other',  # Multi-zone, ?
    'none',  # No central heating system
    ]


HEAT_STAGE = [
    'single_stage',  # Single capacity heater or single stage compressor
    'two_stage',  # Dual capacity heater or dual stage compressor
    'modulating',  # Modulating or variable capacity unit
    ]

COOL_TYPE = [
    'central',  # Central AC
    'other',  # Mini-split, evaporative cooler, ?
    'none',  # No central cooling system
    ]

COOL_STAGE = [
    'single_speed',  # Single stage compressor
    'two_speed',  # Dual stage compressor
    'modulating',  # Modulating or variable capacity compressor
    ]


def has_heating(heat_type):
    if heat_type == 'none':
        return False
    if heat_type in HEAT_TYPE:
        return True
    return False


def has_cooling(cool_type):
    if cool_type == 'none':
        return False
    if pandas.isnull(cool_type):
        return True
    if cool_type in COOL_TYPE:
        return True
    return False


def has_auxiliary(heat_type):
    if heat_type == 'heat_pump_electric_backup':
        return True
    return False


def has_emergency(heat_type):
    if heat_type == 'heat_pump_electric_backup':
        return True
    return False


def has_two_stage_heating(heat_stage):
    if heat_stage == 'two_stage':
        return True
    return False


def has_two_stage_cooling(heat_stage):
    if heat_stage == 'two_speed':
        return True
    return False


def has_resistance_heat(heat_type):
    if heat_type == 'heat_pump_electric_backup':
        return True
    return False
