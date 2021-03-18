import logging

HEAT_TYPE = [
    'furnace_or_boiler',  # Non heat pump heating (gas or oil furnace, electric resistance)
    'heat_pump_electric_backup',   # Heat pump with electric resistance heat (strip heat)
    'heat_pump_no_electric_backup',  # Heat pump without electric resistance heat
    'heat_pump_dual_fuel',  # Dual fuel heat pump (e.g. gas or oil fired)
    'other',  # Multi-zone, ?
    'none',  # No central heating system
    ]


HEAT_STAGE = [
    'single_stage',  # Single capacity heater or single stage compressor
    'single_speed',  # Single capacity heater or single stage compressor (synonym)
    'two_stage',  # Dual capacity heater or dual stage compressor
    'two_speed',  # Dual capacity heater or dual stage compressor (synonym)
    'modulating',  # Modulating or variable capacity unit
    'variable_speed',   # Modulating or variable capacity unit
    ]

COOL_TYPE = [
    'heat_pump',  # Heat pump w/ cooling
    'central',  # Central AC
    'other',  # Mini-split, evaporative cooler, ?
    'none',  # No central cooling system
    ]

COOL_STAGE = [
    'single_speed',  # Single stage compressor
    'single_stage',  # Single stage compressor (synonym)
    'two_speed',  # Dual stage compressor
    'two_stage',  # Dual stage compressor (synonym)
    'modulating',  # Modulating or variable capacity compressor
    'variable_speed',   # Modulating or variable capacity unit
    ]

#: This mapping is for old scripts that need to refer to the old mapping, but want to use the new functionality.
#:
#: Usage:
#:
#: ``equipment = EQUIPMENT_MAPPING[equipment_type]``
#:
#: ``heat_type = equipment['heat_type']``
#:
#: Note: Newer scripts should explicitly set the ``heat_type``, ``cool_type``, ``heat_stage``, and ``cool_stage``
#:
#:    ``equipment_type : { 0, 1, 2, 3, 4, 5 }``
#:        - :code:`0`: Other - e.g. multi-zone multi-stage, modulating. Note: module will
#:          not output savings data for this type.
#:        - :code:`1`: Single stage heat pump with aux and/or emergency heat
#:        - :code:`2`: Single stage heat pump without aux or emergency heat
#:        - :code:`3`: Single stage non heat pump with single-stage central air conditioning
#:        - :code:`4`: Single stage non heat pump without central air conditioning
#:        - :code:`5`: Single stage central air conditioning without central heating
EQUIPMENT_MAPPING = [
        {'heat_type': None, 'heat_stage': 'two_stage', 'cool_type': None, 'cool_stage': 'two_speed'},  # 0
        {'heat_type': 'heat_pump_electric_backup', 'heat_stage': 'single_stage', 'cool_type': 'heat_pump', 'cool_stage': None},  # 1
        {'heat_type': 'heat_pump_no_electric_backup', 'heat_stage': 'single_stage', 'cool_type': 'heat_pump', 'cool_stage': None},  # 2
        {'heat_type': 'furnace_or_boiler', 'heat_stage': 'single_stage', 'cool_type': 'central', 'cool_stage': 'single_speed'},  # 3
        {'heat_type': 'furnace_or_boiler', 'heat_stage': 'single_stage', 'cool_type': 'none', 'cool_stage': None},  # 4
        {'heat_type': 'none', 'heat_stage': None, 'cool_type': 'central', 'cool_stage': 'single_speed'},  # 5
        ]


def has_heating(heat_type):
    """ Determines of the heat type has heating capability

    Parameters
    ----------
    heat_type: str
        The name of the heat type

    Returns
    -------
    boolean
    """
    if heat_type is None:
        return False
    if heat_type == 'none':
        return False
    if heat_type == 'other':
        return False
    if heat_type == 'heat_pump_dual_fuel':
        return False
    if heat_type in HEAT_TYPE:
        return True
    return False


def has_cooling(cool_type):
    """ Determines if the cooling type has cooling capability

    Parameters
    ----------
    cool_type : str
        The name of the heat type


    Returns
    -------
    boolean
    """
    if cool_type is None:
        return False
    if cool_type == 'none':
        return False
    if cool_type == 'other':
        return False
    if cool_type in COOL_TYPE:
        return True
    return False


def has_auxiliary(heat_type):
    """ Determines if the heating type has aux capability

    Parameters
    ----------
    heat_type : str
        The name of the heat type


    Returns
    -------
    boolean
    """
    if heat_type == 'heat_pump_electric_backup':
        return True
    return False


def has_emergency(heat_type):
    """ Determines if the heating type has emergency capability

    Parameters
    ----------
    heat_type : str
        The name of the heat type


    Returns
    -------
    boolean
    """
    if heat_type == 'heat_pump_electric_backup':
        return True
    return False


def has_two_stage_heating(heat_stage):
    """ Determines if the heating stage has two-stage capability

    Parameters
    ----------
    heat_stage : str
        The name of the heat stage


    Returns
    -------
    boolean
    """
    if heat_stage == 'two_stage' or heat_stage == 'two_speed':
        return True
    return False


def has_two_stage_cooling(cool_stage):
    """ Determines if the cooling stage has two-stage capability

    Parameters
    ----------
    cool_stage : str
        The name of the cooling stage


    Returns
    -------
    boolean
    """
    if cool_stage == 'two_speed' or cool_stage == 'two_stage':
        return True
    return False


def has_multi_stage_cooling(cool_stage):
    """ Determines if the cooling stage has multi-stage capability

    Parameters
    ----------
    cool_stage : str
        The name of the cooling stage


    Returns
    -------
    boolean
    """
    if cool_stage == 'variable_speed' or cool_stage == 'modulating':
        return True
    return False


def has_multi_stage_heating(heat_stage):
    """ Determines if the heating stage has multi-stage capability

    Parameters
    ----------
    cool_stage : str
        The name of the cooling stage


    Returns
    -------
    boolean
    """
    if heat_stage == 'variable_speed' or heat_stage == 'modulating':
        return True
    return False


def has_resistance_heat(heat_type):
    """ Determines if the heat type has resistance heating capability

    Parameters
    ----------
    heat_type : str
        The name of the heating type


    Returns
    -------
    boolean
    """
    if heat_type == 'heat_pump_electric_backup':
        return True
    return False


def validate_heat_type(heat_type):
    if heat_type is None or heat_type == '' or heat_type in HEAT_TYPE:
        return True
    logging.warning("Heating type {heat_type} is not a recognized heating type.".format(heat_type=heat_type))
    return False


def validate_cool_type(cool_type):
    if cool_type is None or cool_type == '' or cool_type in COOL_TYPE:
        return True
    logging.warning("Cooling type {cool_type} is not a recognized cooling type.".format(cool_type=cool_type))
    return False


def validate_heat_stage(heat_stage):
    if heat_stage is None or heat_stage == '' or heat_stage in HEAT_STAGE:
        return True
    logging.warning("Heating stage {heat_stage} is not a recognized heating stage.".format(heat_stage=heat_stage))
    return False


def validate_cool_stage(cool_stage):
    if cool_stage is None or cool_stage == '' or cool_stage in COOL_STAGE:
        return True
    logging.warning("Cooling stage {cool_stage} is not a recognized cooling stage.".format(cool_stage=cool_stage))
    return False


def first_stage_capacity_ratio(heat_or_cool_type):
    if heat_or_cool_type == "furnace_or_boiler":
        return 0.65
    else:
        return 0.72
