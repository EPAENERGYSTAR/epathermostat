import pandas as pd
import numpy as np
from numpy.testing import assert_allclose

import pytest

from .fixtures.single_stage import (
        thermostat_type_1,
        core_heating_day_set_type_1_entire as core_heating_day_set_type_1,
        core_cooling_day_set_type_1_entire as core_cooling_day_set_type_1,
        core_heating_day_set_type_1_empty,
        core_cooling_day_set_type_1_empty,
        )

from .fixtures.metrics_data import (
        metrics_type_1_data,
        )

RTOL = 1e-3
ATOL = 1e-3


def test_get_cooling_demand_dailyavgCTD_empty(thermostat_type_1, core_cooling_day_set_type_1_empty, metrics_type_1_data):
    thermostat_type_1.get_cooling_demand(core_cooling_day_set_type_1_empty)


def test_get_cooling_demand_dailyavgHTD_empty(thermostat_type_1, core_heating_day_set_type_1_empty, metrics_type_1_data):
    thermostat_type_1.get_heating_demand(core_heating_day_set_type_1_empty)


def test_get_cooling_demand(thermostat_type_1, core_cooling_day_set_type_1, metrics_type_1_data):
    demand, tau_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae = \
            thermostat_type_1.get_cooling_demand(core_cooling_day_set_type_1)
    assert_allclose(demand.mean(), metrics_type_1_data[0]["mean_demand"], rtol=RTOL, atol=ATOL)


def test_get_heating_demand(thermostat_type_1, core_heating_day_set_type_1, metrics_type_1_data):
    demand, tau_estimate, alpha_estimate, mse, rmse, cvrmse, mape, mae = \
            thermostat_type_1.get_heating_demand(core_heating_day_set_type_1)
    assert_allclose(demand.mean(), metrics_type_1_data[1]["mean_demand"], rtol=RTOL, atol=ATOL)
