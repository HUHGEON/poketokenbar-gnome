"""Where things live, per platform.

Most of the twelve sources are dotfiles under the home directory and are the
same everywhere — `%USERPROFILE%\\.claude` on Windows is exactly `~/.claude`.
Three are not, because they use the platform's application-data directory
instead, and those three are the only reason this module exists:

                     macOS                          Linux                 Windows
    config/data      ~/Library/Application Support  $XDG_CONFIG_HOME      %APPDATA%
                                                    $XDG_DATA_HOME

`system` is injectable so the mapping can be exercised for every platform from
any one of them. Checking Windows behaviour only on Windows would mean checking
it nowhere, since this is developed on macOS and tested on Linux.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Mapping

WINDOWS = "win32"
MACOS = "darwin"


def _env(env: Mapping[str, str] | None) -> Mapping[str, str]:
    return os.environ if env is None else env


def _home(home: Path | None) -> Path:
    return home or Path.home()


def config_base(
    home: Path | None = None,
    env: Mapping[str, str] | None = None,
    system: str | None = None,
) -> Path:
    """Where an application keeps its user configuration.

    On Windows this is Roaming rather than Local: it is what Electron's
    `app.getPath("userData")` uses, which is what puts Cursor's store there.
    """
    env = _env(env)
    system = system or sys.platform
    if system == WINDOWS:
        appdata = (env.get("APPDATA") or "").strip()
        if appdata:
            return Path(appdata)
        return _home(home) / "AppData" / "Roaming"
    if system == MACOS:
        return _home(home) / "Library" / "Application Support"
    configured = (env.get("XDG_CONFIG_HOME") or "").strip()
    return Path(configured).expanduser() if configured else _home(home) / ".config"


def data_base(
    home: Path | None = None,
    env: Mapping[str, str] | None = None,
    system: str | None = None,
) -> Path:
    """Where an application keeps user data it is not configuration.

    macOS and Windows do not draw the distinction Linux does, so both collapse
    onto the same directory as `config_base`.
    """
    env = _env(env)
    system = system or sys.platform
    if system in (WINDOWS, MACOS):
        return config_base(home=home, env=env, system=system)
    configured = (env.get("XDG_DATA_HOME") or "").strip()
    return Path(configured).expanduser() if configured else _home(home) / ".local" / "share"


def state_base(
    home: Path | None = None,
    env: Mapping[str, str] | None = None,
    system: str | None = None,
) -> Path:
    """Where this project writes state.json.

    Linux has a directory for exactly this; the other two do not, so state sits
    beside the rest of the application's data.
    """
    env = _env(env)
    system = system or sys.platform
    if system in (WINDOWS, MACOS):
        return config_base(home=home, env=env, system=system)
    configured = (env.get("XDG_STATE_HOME") or "").strip()
    return Path(configured).expanduser() if configured else _home(home) / ".local" / "state"


def cache_base(
    home: Path | None = None,
    env: Mapping[str, str] | None = None,
    system: str | None = None,
) -> Path:
    """Where the scan cache goes.

    Windows keeps caches in Local rather than Roaming — a roaming profile
    should not carry a rebuildable index of someone's log files across
    machines.
    """
    env = _env(env)
    system = system or sys.platform
    if system == WINDOWS:
        local = (env.get("LOCALAPPDATA") or "").strip()
        if local:
            return Path(local)
        return _home(home) / "AppData" / "Local"
    if system == MACOS:
        return _home(home) / "Library" / "Caches"
    configured = (env.get("XDG_CACHE_HOME") or "").strip()
    return Path(configured).expanduser() if configured else _home(home) / ".cache"


def runtime_base(
    home: Path | None = None,
    env: Mapping[str, str] | None = None,
    system: str | None = None,
) -> Path:
    """Where the command spool goes.

    Linux has a per-session runtime directory that is cleared on logout, which
    is exactly right for a queue of one-shot commands. Elsewhere the temporary
    directory stands in — the spool is drained within seconds either way, and
    a leftover file is a command the daemon simply runs late.
    """
    env = _env(env)
    system = system or sys.platform
    if system == WINDOWS:
        for name in ("TEMP", "TMP"):
            value = (env.get(name) or "").strip()
            if value:
                return Path(value)
        return _home(home) / "AppData" / "Local" / "Temp"
    if system == MACOS:
        # TMPDIR is per-user on macOS, which is what matters for a spool.
        value = (env.get("TMPDIR") or "").strip()
        return Path(value) if value else Path("/tmp")
    configured = (env.get("XDG_RUNTIME_DIR") or "").strip()
    return Path(configured) if configured else Path("/tmp")
