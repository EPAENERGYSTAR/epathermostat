import socket

import pytest

from thermostat import _network


@pytest.fixture
def reset_pin(monkeypatch):
    """Give each test a dual-stack starting point, then restore.

    Importing thermostat already applies the pin, so the resolver has to be put
    back to its dual-stack behaviour before a test can observe force_ipv4 doing
    anything.
    """
    urllib3_connection = pytest.importorskip("urllib3.util.connection")
    original = urllib3_connection.allowed_gai_family
    urllib3_connection.allowed_gai_family = lambda: socket.AF_UNSPEC
    monkeypatch.setattr(_network, "_applied", False)
    yield urllib3_connection
    urllib3_connection.allowed_gai_family = original
    _network._applied = True


def test_force_ipv4_pins_address_family(reset_pin, monkeypatch):
    monkeypatch.delenv(_network.ALLOW_IPV6_ENV_VAR, raising=False)

    assert _network.force_ipv4() is True
    assert reset_pin.allowed_gai_family() == socket.AF_INET


def test_force_ipv4_is_idempotent(reset_pin, monkeypatch):
    monkeypatch.delenv(_network.ALLOW_IPV6_ENV_VAR, raising=False)

    assert _network.force_ipv4() is True
    assert _network.force_ipv4() is True
    assert reset_pin.allowed_gai_family() == socket.AF_INET


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_env_var_opts_out(reset_pin, monkeypatch, value):
    monkeypatch.setenv(_network.ALLOW_IPV6_ENV_VAR, value)

    assert _network.force_ipv4() is False
    assert reset_pin.allowed_gai_family() == socket.AF_UNSPEC


@pytest.mark.parametrize("value", ["0", "false", "no", ""])
def test_env_var_other_values_do_not_opt_out(reset_pin, monkeypatch, value):
    monkeypatch.setenv(_network.ALLOW_IPV6_ENV_VAR, value)

    assert _network.force_ipv4() is True
    assert reset_pin.allowed_gai_family() == socket.AF_INET


def test_importing_thermostat_applies_the_pin():
    """The pin must not require any action from the caller.

    Manufacturers run this package unmodified, so importing it has to be enough.
    """
    urllib3_connection = pytest.importorskip("urllib3.util.connection")

    import thermostat  # noqa: F401  (import is the assertion)

    assert urllib3_connection.allowed_gai_family() == socket.AF_INET
