# content of conftest.py

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    stats = getattr(config, "_zcta_coverage", None)
    if not stats:
        return
    valid = stats["ok"] + stats["no_core_days"]
    pct = valid / stats["total"] * 100
    terminalreporter.write_sep("=", "ZCTA coverage")
    terminalreporter.write_line(
        "  valid {:,}/{:,} ({:.2f}%)  load_error={:,}".format(
            valid, stats["total"], pct, stats["load_error"]
        )
    )
