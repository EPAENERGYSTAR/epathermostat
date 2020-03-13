# This is for old scripts that might still refer to the old mapping.
# Usage: equipment = EQUIPMENT_MAPPING[equipment_type]
# heat_type = equipment['heat_type']
EQUIPMENT_MAPPING = [
        {'heat_type': None, 'heat_stage': 'two_stage', 'cool_type': None, 'cool_stage': 'two_stage'},  # 0
        {'heat_type': 'heat_pump_electric_backup', 'heat_stage': 'single_stage', 'cool_type': 'heat_pump', 'cool_stage': None},  # 1
        {'heat_type': 'heat_pump_no_electric_backup', 'heat_stage': 'single_stage', 'cool_type': 'heat_pump', 'cool_stage': None},  # 2
        {'heat_type': 'non_heat_pump', 'heat_stage': 'single_stage', 'cool_type': 'central', 'cool_stage': 'single_stage'},  # 3
        {'heat_type': 'non_heat_pump', 'heat_stage': 'single_stage', 'cool_type': 'none', 'cool_stage': None},  # 4
        {'heat_type': 'none', 'heat_stage': None, 'cool_type': 'central', 'cool_stage': 'single_stage'},  # 5
        ]

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
    'heat_pump',  # Heat pump w/ cooling
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


def has_two_stage_cooling(cool_stage):
    if cool_stage == 'two_speed':
        return True
    return False


def has_resistance_heat(heat_type):
    if heat_type == 'heat_pump_electric_backup':
        return True
    return False
