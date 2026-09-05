"""What install.sh leaves behind.

It cannot be run here — it builds a venv and talks to systemd — but the parts
that decide behaviour are plain shell and can be run on their own.
"""

import os
from pathlib import Path

import pytest

from poketokenbar import config, platform_paths


# MARK: the pin default the front end picks


def test_the_installer_seeds_the_pin_setting_from_the_front_end():
    """Both readings of a pin are defensible and the pin lives in the save, so
    one daemon cannot behave one way for one front end and another for the
    other. The installer knows which UI it is putting down, so it picks the
    default — and only on a first install, or a later run would undo a choice
    someone has since made."""
    script = (Path(__file__).resolve().parent.parent / "install.sh").read_text(
        encoding="utf-8")
    assert "release_pin_on_graduation" in script
    assert "gnome|plasma) release_pin=true" in script
    assert "*)            release_pin=false" in script
    assert 'if [ ! -f "$config_file" ]' in script, (
        "a reinstall would overwrite a setting the user has changed"
    )


@pytest.mark.parametrize("ui,expected", [
    ("gnome", True), ("plasma", True), ("qt", False), ("none", False),
])
def test_the_seeded_default_is_what_the_daemon_reads(tmp_path, ui, expected):
    """Run the installer's own block, then read it back the way the daemon
    would on Linux — where install.sh runs. Resolving the path for the machine
    running the suite instead would compare an XDG path against macOS's
    Application Support and prove nothing."""
    import subprocess

    root = Path(__file__).resolve().parent.parent
    script = (root / "install.sh").read_text(encoding="utf-8")
    start = script.index('config_file="${XDG_CONFIG_HOME:-$HOME/.config}')
    end = script.index("fi", script.index("from POKETOKENBAR_UI=$ui")) + 2

    home = tmp_path / ui
    (home / ".config").mkdir(parents=True)
    subprocess.run(["bash", "-c", f"ui={ui}\n" + script[start:end]],
                   env={"HOME": str(home), "XDG_CONFIG_HOME": str(home / ".config"),
                        "PATH": os.environ.get("PATH", "")},
                   check=True, capture_output=True)

    path = (platform_paths.config_base(home, {"XDG_CONFIG_HOME": str(home / ".config")},
                                       "linux") / "poketokenbar" / "config.json")
    assert config.load(path)["release_pin_on_graduation"] is expected
