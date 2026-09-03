"""The Windows installer scripts.

They cannot be run from here, but they can be parsed — PowerShell's own parser
runs on Linux — and the paths and module names they name can be checked against
the code they are supposed to start. Those are the two ways a script like this
fails: a syntax error, or a rename on the Python side that nothing tells it
about.
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from poketokenbar import config, platform_paths, state

WINDOWS_DIR = Path(__file__).resolve().parent.parent / "packaging" / "windows"
INSTALL = WINDOWS_DIR / "install.ps1"
UNINSTALL = WINDOWS_DIR / "uninstall.ps1"

PWSH = shutil.which("pwsh") or shutil.which("powershell")

PARSE = (
    "$errs = $null;"
    "[System.Management.Automation.Language.Parser]::ParseFile("
    "'{path}', [ref]$null, [ref]$errs) | Out-Null;"
    "if ($errs.Count) {{ $errs | ForEach-Object {{ Write-Output $_ }}; exit 1 }}"
)


def both_scripts():
    return [INSTALL, UNINSTALL]


@pytest.mark.parametrize("path", both_scripts(), ids=lambda p: p.name)
def test_the_scripts_exist(path):
    assert path.is_file(), f"missing {path}"
    assert path.read_text(encoding="utf-8").strip()


@pytest.mark.skipif(PWSH is None, reason="PowerShell is not installed")
@pytest.mark.parametrize("path", both_scripts(), ids=lambda p: p.name)
def test_each_script_parses(path):
    result = subprocess.run(
        [PWSH, "-NoProfile", "-Command", PARSE.format(path=path)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"{path.name} does not parse:\n{result.stdout}"


# MARK: what it starts


def test_it_launches_the_modules_that_actually_exist():
    """A rename on the Python side is invisible to a script that hardcodes the
    old module name — the shortcut still exists and simply does nothing."""
    script = INSTALL.read_text(encoding="utf-8")
    for module in re.findall(r"-m (poketokenbar[\w.]*)", script):
        parts = module.split(".")
        target = Path(__file__).resolve().parent.parent.joinpath(*parts)
        assert target.with_suffix(".py").is_file() or (target / "__init__.py").is_file(), (
            f"install.ps1 starts {module}, which does not exist"
        )


def test_it_starts_both_halves():
    """The daemon produces the numbers and the tray shows them; one without the
    other is an install that looks broken."""
    script = INSTALL.read_text(encoding="utf-8")
    assert "poketokenbar.daemon" in script
    assert "poketokenbar.ui.app" in script


def test_it_uses_pythonw_so_no_console_window_appears():
    """python.exe brings a console host with it, so a tray app started at login
    would flash a black window on every boot."""
    script = INSTALL.read_text(encoding="utf-8")
    assert "pythonw.exe" in script
    assert "Scripts\\python.exe" in script, "the plain interpreter is still needed for pip"


def test_it_installs_the_qt_front_end():
    """Without PySide6 the tray app cannot start at all, and the failure is
    silent because nothing has a console."""
    assert "PySide6" in INSTALL.read_text(encoding="utf-8")


# MARK: where it puts things


def test_the_install_root_is_under_the_user_profile():
    """No step here needs an administrator; a path outside the profile would
    mean one does."""
    script = INSTALL.read_text(encoding="utf-8")
    assert "$env:LOCALAPPDATA" in script
    assert "C:\\Program Files" not in script


def test_it_names_the_state_file_where_the_daemon_writes_it():
    """The closing message tells someone where to look; if it names the wrong
    directory the first thing they check will be empty."""
    script = INSTALL.read_text(encoding="utf-8")
    windows_state = platform_paths.state_base(
        home=Path("C:/Users/u"), env={"APPDATA": "C:/Users/u/AppData/Roaming"},
        system="win32")
    assert windows_state.name == "Roaming"
    assert "APPDATA" in script and "poketokenbar" in script


def test_the_uninstaller_leaves_the_save_alone():
    """A Pokedex should not vanish because someone removed the viewer."""
    script = UNINSTALL.read_text(encoding="utf-8")
    assert "LOCALAPPDATA" in script, "it removes the install root"
    # The save lives in APPDATA, and the script must say so rather than delete it.
    assert "delete it by hand" in script.lower() or "by hand" in script.lower()
    assert "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $env:APPDATA" not in script


def test_the_daemon_and_the_tray_agree_on_the_state_path():
    """Both are started by the same script and must read and write one file."""
    from poketokenbar.ui.reader import StateReader

    assert StateReader().path == state.default_path()


def test_config_and_state_share_a_root_on_windows():
    """Windows has no equivalent of the XDG split, so both sit in Roaming; a
    mismatch would leave the tray editing settings the daemon never reads."""
    home, env = Path("C:/Users/u"), {"APPDATA": "C:/Users/u/AppData/Roaming"}
    assert (
        platform_paths.config_base(home, env, "win32")
        == platform_paths.state_base(home, env, "win32")
    )
    assert config.DEFAULTS  # the module the tray writes through


# MARK: the generated VBScript


def test_the_launcher_is_built_by_substitution_not_interpolation():
    """The first release shipped a .vbs one quote short.

    VBScript escapes a quote inside a string by doubling it, so the Run line
    needs three quotes then two. Interpolating a path into that is how one got
    lost, and the result parses fine as PowerShell while every launch dies with
    "Expected end of statement" — which no amount of parsing the installer
    would have caught.
    """
    script = INSTALL.read_text(encoding="utf-8")
    assert "@'" in script, "the template must be a single-quoted here-string"
    assert '"""__PYW__"" -m __MODULE__"' in script, (
        "the Run line no longer has the doubled quotes VBScript needs"
    )
    # The call is split across lines for readability, so the dot is not adjacent.
    assert "Replace('__PYW__'" in script


def test_the_template_has_balanced_vbscript_quoting():
    """Counted rather than eyeballed: every line of the template must have an
    even number of quotes, or the string never closes."""
    script = INSTALL.read_text(encoding="utf-8")
    template = script.split("$vbsTemplate = @'")[1].split("'@")[0]
    for line in template.strip().splitlines():
        assert line.count('"') % 2 == 0, f"unbalanced quotes: {line}"


def test_the_launcher_starts_both_halves():
    script = INSTALL.read_text(encoding="utf-8")
    assert "'poketokenbar.daemon'" in script
    assert "'poketokenbar.ui.app'" in script


def test_ci_actually_runs_the_installer():
    """Parsing it is not running it, and the quoting bug lived entirely in the
    gap between the two."""
    workflow = (
        Path(__file__).resolve().parent.parent / ".github" / "workflows" / "ci.yml"
    ).read_text(encoding="utf-8")
    assert "./packaging/windows/install.ps1" in workflow, (
        "CI parses the installer but never executes it"
    )
    assert "cscript" in workflow, "the generated VBScript is never compiled"
    assert "./packaging/windows/uninstall.ps1" in workflow
