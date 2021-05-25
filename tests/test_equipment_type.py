import pytest
from thermostat.equipment_type import (
    has_heating,
    has_cooling,
    has_auxiliary,
    has_emergency,
    has_two_stage_heating,
    has_two_stage_cooling,
    has_resistance_heat,
    validate_heat_type,
    validate_cool_type,
    validate_heat_stage,
    validate_cool_stage,
    first_stage_capacity_ratio,
    )



def test_missing_or_blank_heat_type():
    assert(has_heating(None) is False)
    assert(has_heating('') is False)


def test_missing_or_blank_cool_type():
    assert(has_cooling(None) is False)
    assert(has_cooling('') is False)


def test_missing_or_blank_heat_stage():
    assert(has_two_stage_heating(None) is False)
    assert(has_two_stage_heating('') is False)


def test_missing_or_blank_cool_stage():
    assert(has_two_stage_cooling(None) is False)
    assert(has_two_stage_cooling('') is False)


def test_has_heating():
    for i in [
        'furnace_or_boiler',  # Non heat pump heating (gas or oil furnace, electric resistance)
        'heat_pump_electric_backup',   # Heat pump with electric resistance heat (strip heat)
        'heat_pump_no_electric_backup',  # Heat pump without electric resistance heat
    ]:
        assert(has_heating(i) is True)
    for i in [
        'heat_pump_dual_fuel',  # Dual fuel heat pump (e.g. gas or oil fired)
        'other',  # Multi-zone, ?
        'none',  # None
    ]:
        assert(has_heating(i) is False)
    assert(has_heating(None) is False)
    assert(validate_heat_type('furnace_or_boiler') is True)
    assert(validate_heat_type('bogus_heat_pump') is False)


def test_has_cooling():
    for i in [
        'heat_pump',  # Heat pump w/ cooling
        'central',  # Central AC
    ]:
        assert(has_cooling(i) is True)
    assert(has_cooling('none') is False)
    assert(has_cooling('other') is False)
    assert(has_cooling(None) is False)
    assert(validate_cool_type('heat_pump') is True)
    assert(validate_cool_type('bogus_pump') is False)


def test_has_two_stage_cooling():
    assert(has_two_stage_cooling('two_speed') is True)
    assert(has_two_stage_cooling('two_stage') is True)
    assert(has_two_stage_cooling('single_speed') is False)
    assert(has_two_stage_cooling('single_stage') is False)
    assert(has_two_stage_cooling('modulating') is False)
    assert(has_two_stage_cooling(None) is False)
    assert(has_two_stage_cooling('none') is False)
    assert(has_two_stage_cooling('') is False)
    assert(validate_cool_stage('two_speed') is True)
    assert(validate_cool_stage('ten_speed') is False)


def test_has_two_stage_heating():
    assert(has_two_stage_heating('two_stage') is True)
    assert(has_two_stage_heating('single_stage') is False)
    assert(has_two_stage_heating('two_speed') is True)
    assert(has_two_stage_heating('single_speed') is False)
    assert(has_two_stage_heating('modulating') is False)
    assert(has_two_stage_heating(None) is False)
    assert(has_two_stage_heating('none') is False)
    assert(has_two_stage_heating('') is False)
    assert(validate_heat_stage('two_stage') is True)
    assert(validate_heat_stage('two_speed') is True)
    assert(validate_heat_stage('2_stage') is False)


def test_has_emergency():
    assert(has_emergency('heat_pump_electric_backup') is True)
    assert(has_emergency('heat_pump_no_electric_backup') is False)
    assert(has_emergency('heat_pump_dual_fuel') is False)


def test_has_auxiliary():
    assert(has_auxiliary('heat_pump_electric_backup') is True)
    assert(has_auxiliary('heat_pump_no_electric_backup') is False)
    assert(has_auxiliary('heat_pump_dual_fuel') is False)


def test_has_resistance_heat():
    assert(has_resistance_heat('heat_pump_electric_backup') is True)
    assert(has_resistance_heat('heat_pump_no_electric_backup') is False)
    assert(has_resistance_heat('heat_pump_dual_fuel') is False)


def test_ratio():
    assert(first_stage_capacity_ratio('furnace_or_boiler') == .65)
    assert(first_stage_capacity_ratio('heat_pump') == .72)
