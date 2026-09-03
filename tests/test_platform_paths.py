"""Per-platform base directories, exercised for all three from any one of them.

`system` is injected rather than read, so Windows behaviour is checked here
rather than only on Windows — which, developing on macOS and testing on Linux,
would mean checked nowhere.
"""

from pathlib import Path

import pytest

from poketokenbar import platform_paths as paths

HOME = Path("/home/u")
WIN_HOME = Path("C:/Users/u")


# MARK: Linux


def test_linux_uses_the_xdg_directories():
    assert paths.config_base(HOME, {}, "linux") == HOME / ".config"
    assert paths.data_base(HOME, {}, "linux") == HOME / ".local" / "share"
    assert paths.state_base(HOME, {}, "linux") == HOME / ".local" / "state"
    assert paths.cache_base(HOME, {}, "linux") == HOME / ".cache"


@pytest.mark.parametrize(
    "function,variable",
    [
        (paths.config_base, "XDG_CONFIG_HOME"),
        (paths.data_base, "XDG_DATA_HOME"),
        (paths.state_base, "XDG_STATE_HOME"),
        (paths.cache_base, "XDG_CACHE_HOME"),
    ],
)
def test_each_xdg_override_is_honoured(function, variable):
    assert function(HOME, {variable: "/elsewhere"}, "linux") == Path("/elsewhere")


def test_linux_runtime_prefers_the_session_directory():
    """It is cleared on logout, which is what a queue of one-shot commands wants."""
    assert paths.runtime_base(HOME, {"XDG_RUNTIME_DIR": "/run/user/1000"}, "linux") == Path(
        "/run/user/1000"
    )
    assert paths.runtime_base(HOME, {}, "linux") == Path("/tmp")


# MARK: macOS


def test_macos_collapses_config_data_and_state_onto_application_support():
    """macOS draws no distinction between them, so neither does this."""
    support = HOME / "Library" / "Application Support"
    assert paths.config_base(HOME, {}, "darwin") == support
    assert paths.data_base(HOME, {}, "darwin") == support
    assert paths.state_base(HOME, {}, "darwin") == support


def test_macos_caches_are_separate():
    assert paths.cache_base(HOME, {}, "darwin") == HOME / "Library" / "Caches"


def test_macos_ignores_the_xdg_variables():
    """A stray XDG_CONFIG_HOME must not move a macOS app off Application Support."""
    env = {"XDG_CONFIG_HOME": "/elsewhere", "XDG_CACHE_HOME": "/elsewhere"}
    assert paths.config_base(HOME, env, "darwin") == HOME / "Library" / "Application Support"
    assert paths.cache_base(HOME, env, "darwin") == HOME / "Library" / "Caches"


def test_macos_runtime_uses_the_per_user_tmpdir():
    assert paths.runtime_base(HOME, {"TMPDIR": "/var/folders/x/T/"}, "darwin") == Path(
        "/var/folders/x/T"
    )


# MARK: Windows


def test_windows_uses_roaming_for_config_and_data():
    """Roaming is what Electron's userData resolves to, which is where Cursor
    puts the store this project reads."""
    env = {"APPDATA": "C:/Users/u/AppData/Roaming"}
    roaming = Path("C:/Users/u/AppData/Roaming")
    assert paths.config_base(WIN_HOME, env, "win32") == roaming
    assert paths.data_base(WIN_HOME, env, "win32") == roaming
    assert paths.state_base(WIN_HOME, env, "win32") == roaming


def test_windows_caches_go_to_local_not_roaming():
    """A roaming profile should not carry a rebuildable index of someone's logs
    between machines."""
    env = {"LOCALAPPDATA": "C:/Users/u/AppData/Local"}
    assert paths.cache_base(WIN_HOME, env, "win32") == Path("C:/Users/u/AppData/Local")


def test_windows_falls_back_to_the_conventional_layout():
    """A service account can start without APPDATA set; guessing beats crashing,
    and this is the layout it would have had."""
    assert paths.config_base(WIN_HOME, {}, "win32") == WIN_HOME / "AppData" / "Roaming"
    assert paths.cache_base(WIN_HOME, {}, "win32") == WIN_HOME / "AppData" / "Local"


def test_windows_runtime_uses_temp():
    assert paths.runtime_base(WIN_HOME, {"TEMP": "C:/Temp"}, "win32") == Path("C:/Temp")
    assert paths.runtime_base(WIN_HOME, {"TMP": "C:/Tmp"}, "win32") == Path("C:/Tmp")
    assert paths.runtime_base(WIN_HOME, {}, "win32") == (
        WIN_HOME / "AppData" / "Local" / "Temp"
    )


def test_windows_ignores_the_xdg_variables():
    """WSL and Git Bash both export these into a native Python's environment."""
    env = {"APPDATA": "C:/Roaming", "XDG_CONFIG_HOME": "/home/u/.config"}
    assert paths.config_base(WIN_HOME, env, "win32") == Path("C:/Roaming")


# MARK: the shape of the thing


@pytest.mark.parametrize("system", ["linux", "darwin", "win32"])
@pytest.mark.parametrize(
    "function",
    [paths.config_base, paths.data_base, paths.state_base, paths.cache_base,
     paths.runtime_base],
)
def test_every_base_resolves_on_every_platform(function, system):
    """No combination may return None or an empty path.

    Absoluteness is deliberately not asserted: `Path` means the *running*
    platform's flavour, so a POSIX-shaped result is not absolute when this test
    runs on Windows, and a C: path is not absolute when it runs on Linux. The
    property that holds everywhere is that the result is rooted at something
    that was given to it.
    """
    result = function(HOME, {}, system)
    assert isinstance(result, Path)
    # Compared as posix: `str()` on a Windows Path renders "/tmp" as "\\tmp",
    # so the separator has to be normalised before any prefix check.
    text = result.as_posix()
    assert text and text not in (".", "")
    assert text.startswith(HOME.as_posix()) or text.startswith("/"), result


def test_an_empty_override_is_ignored_not_obeyed():
    """An exported-but-empty variable would otherwise resolve to the filesystem
    root, and the daemon would try to write there."""
    for variable in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME"):
        assert paths.config_base(HOME, {variable: "   "}, "linux") == HOME / ".config"
    assert paths.config_base(WIN_HOME, {"APPDATA": ""}, "win32") == (
        WIN_HOME / "AppData" / "Roaming"
    )
