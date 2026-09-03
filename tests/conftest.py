import sys
from pathlib import Path

import pytest


def pytest_configure(config):
    """Register the one custom marker.

    Declared here as well as in pyproject: the ini registration is not picked
    up when pytest is invoked with a different rootdir, and an unregistered
    mark is a warning on every run.
    """
    config.addinivalue_line(
        "markers",
        "network: reaches the internet; skips itself when there is none")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Every variable that can move a path this project reads or writes.
_LOCATION_VARIABLES = (
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "XDG_STATE_HOME",
    "XDG_CACHE_HOME",
    "XDG_RUNTIME_DIR",
    "CLAUDE_CONFIG_DIR",
    "CODEX_HOME",
    "GROK_HOME",
    "COPILOT_HOME",
    "CURSOR_DATA_DIR",
    "KIRO_HOME",
    "KIRO_CLI_HOME",
    "HERMES_HOME",
    "OPENCODE_DATA_DIR",
    "ANTIGRAVITY_HOME",
    "PI_CODING_AGENT_DIR",
    "PI_CODING_AGENT_SESSION_DIR",
    "OMP_CODING_AGENT_DIR",
)


@pytest.fixture(autouse=True)
def isolated_locations(monkeypatch):
    """Clear every path override before each test.

    A provider given an explicit `home=` still reads the ambient environment for
    its XDG base, which is correct in production and poisonous in a test: on a
    machine with XDG_CONFIG_HOME set, the Cursor tests looked in that directory
    instead of the temporary home and found nothing.

    That passed locally and failed on CI, which is the worst version of it —
    the suite was quietly reporting on whoever's machine it ran on. Clearing the
    lot here fixes the whole class rather than the two tests that happened to
    show it.
    """
    for variable in _LOCATION_VARIABLES:
        monkeypatch.delenv(variable, raising=False)
