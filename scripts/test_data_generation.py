#!/usr/bin/env python

from pprint import pprint

from thermostat.importers import from_csv
from thermostat.util.testing import get_data_path
import thermostat
import os


thermostat_path = os.path.join(os.path.join("/", *thermostat.__file__.split('/')[:5]), "tests", "data", "single_stage", "metadata_type_1_single.csv")
thermostat_type_1 = list(from_csv(thermostat_path))[0]
metrics = thermostat_type_1.calculate_epa_field_savings_metrics()
print(
"""
@pytest.fixture(scope="session")
def metrics_type_1_data():
    data = \\
"""
, end='')
pprint(metrics)
print(
"""
    return data
"""
)

thermostat_path = os.path.join(os.path.join("/", *thermostat.__file__.split('/')[:5]), "tests", "data", "two_stage", "metadata_heat_pump_electric_backup_two_stage_heat_pump_two_stage.csv")
thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage = list(from_csv(thermostat_path))[0]
metrics = thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage.calculate_epa_field_savings_metrics()
print(
"""
@pytest.fixture(scope="session")
def metrics_hpeb_2_hp_2_data():
    data = \\
"""
, end='')
pprint(metrics)
print(
"""
    return data
"""
)


thermostat_path = os.path.join(os.path.join("/", *thermostat.__file__.split('/')[:5]), "tests", "data", "two_stage_ert", "metadata_heat_pump_electric_backup_two_stage_heat_pump_two_stage.csv")
thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage = list(from_csv(thermostat_path))[0]
metrics = thermostat_heat_pump_electric_backup_two_stage_heat_pump_two_stage.calculate_epa_field_savings_metrics()
print(
"""
@pytest.fixture(scope="session")
def metrics_ert_hpeb_2_hp_2_data():
    data = \\
"""
, end='')
pprint(metrics)
print(
"""
    return data
"""
)
