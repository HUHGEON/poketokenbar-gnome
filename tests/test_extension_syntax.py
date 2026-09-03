"""The extension's JavaScript parses, and its manifest is well formed.

GNOME Shell reports a syntax error only in the journal, after the extension has
already failed to load, so a stray character survives right up until someone
tries it on a real desktop. Node parses the same ESM grammar GJS does, which is
enough to catch that class without a Shell.

It is a parse check, not a run: nothing here proves an actor renders or that a
GNOME API exists. What it does mean is that a typo cannot reach a release.
"""

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

EXTENSION_DIR = (
    Path(__file__).resolve().parent.parent
    / "gnome-extension"
    / "poketokenbar@huhgeon.github.io"
)

NODE = shutil.which("node")


def js_files():
    return sorted(EXTENSION_DIR.rglob("*.js"))


@pytest.mark.skipif(NODE is None, reason="node is not installed")
@pytest.mark.parametrize("path", js_files(), ids=lambda p: p.name)
def test_each_file_parses(path):
    # Copied to .mjs so Node applies module grammar; the sources keep the .js
    # name GNOME Shell requires.
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / f"{path.stem}.mjs"
        target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        result = subprocess.run(
            [NODE, "--check", str(target)], capture_output=True, text=True
        )
    assert result.returncode == 0, f"{path.name} does not parse:\n{result.stderr}"


def test_the_manifest_is_valid_and_declares_what_shell_needs():
    metadata = json.loads((EXTENSION_DIR / "metadata.json").read_text(encoding="utf-8"))
    for key in ("uuid", "name", "description", "shell-version"):
        assert metadata.get(key), f"metadata.json has no {key}"
    assert metadata["uuid"] == EXTENSION_DIR.name, (
        "the uuid and the directory name must match or Shell will not load it"
    )
    assert all(v.isdigit() for v in metadata["shell-version"])


def test_the_manifest_declares_no_schema_it_does_not_ship():
    """Declaring settings-schema without installing the schema makes
    getSettings() throw the first time a preferences window opens."""
    metadata = json.loads((EXTENSION_DIR / "metadata.json").read_text(encoding="utf-8"))
    schema = metadata.get("settings-schema")
    if not schema:
        return
    schemas = list(EXTENSION_DIR.rglob("*.gschema.xml"))
    assert schemas, f"metadata declares {schema} but no schema is shipped"


def test_the_entry_point_default_exports_an_extension():
    source = (EXTENSION_DIR / "extension.js").read_text(encoding="utf-8")
    assert re.search(r"export\s+default\s+class\s+\w+\s+extends\s+Extension", source), (
        "GNOME 45+ loads the default export of extension.js"
    )
    assert "enable()" in source and "disable()" in source


def test_everything_enable_starts_is_torn_down_in_disable():
    """A timer or signal left connected leaks inside the compositor, where the
    only way out is a session restart."""
    source = (EXTENSION_DIR / "extension.js").read_text(encoding="utf-8")
    # Comments first: the file's own header describes this rule in prose, and
    # splitting on the word would cut the body at the sentence instead.
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    source = re.sub(r"//[^\n]*", "", source)
    enable = source.split("enable()")[1].split("disable()")[0]
    disable = source.split("disable()")[1]

    for handler in re.findall(r"this\.(_\w*[Hh]andler)\s*=", enable):
        assert f"disconnect(this.{handler})" in disable, f"{handler} is never disconnected"
    if "new StateReader" in enable:
        assert "stop()" in disable, "the state reader's timer is never stopped"
    assert "this._indicator?.destroy()" in disable, "_indicator is never destroyed"
    # The pet is in chrome, so it has to be removed from the layout manager as
    # well as destroyed; _removePet does both and disable() must call it.
    assert "_removePet()" in disable, "_pet is never torn down"
    assert "removeChrome" in source, "the pet is never taken out of chrome"


def test_the_stylesheet_is_present():
    """Shell loads stylesheet.css by name; without it every style_class here
    resolves to nothing and the popup renders unstyled.

    Its contents are not asserted: no check available from here can tell a
    valid St rule from one Shell will ignore, and a test that only restates the
    file would fail on every edit while catching nothing.
    """
    css = (EXTENSION_DIR / "stylesheet.css").read_text(encoding="utf-8")
    assert css.strip()
    assert ".poketokenbar-panel" in css


def test_no_source_file_is_empty():
    for path in js_files():
        assert path.read_text(encoding="utf-8").strip(), f"{path.name} is empty"
