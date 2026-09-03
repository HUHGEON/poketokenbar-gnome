"""The Qt front end, actually constructed and fed a real payload.

Qt runs offscreen, so unlike the GNOME extension this one can be built and
exercised here: every panel is instantiated, handed the output of a real
`state.build`, and asked to lay itself out. That does not prove it looks right,
but it does prove every widget constructs, every field it reads exists, and no
code path raises on the shapes the daemon actually emits.

The empty-state cases matter as much as the full ones. Most people install this
before the daemon has ever written a file, and a front end that raises on
`None` is one that never gets as far as showing anything.
"""

import os

import pytest

pytest.importorskip("PySide6", reason="the Qt front end is optional")

# Must be set before QApplication exists, and QApplication is process-wide.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from poketokenbar.ui import panels  # noqa: E402
from poketokenbar.ui.app import TrayApp, Window  # noqa: E402
from poketokenbar.ui.reader import StateReader  # noqa: E402
from poketokenbar.ui.widgets import Sprite, level_colour, meter  # noqa: E402

from test_extension_contract import full_payload  # noqa: E402


@pytest.fixture(scope="module")
def qt_app():
    """One QApplication for the module; Qt allows exactly one per process."""
    application = QApplication.instance() or QApplication([])
    yield application


@pytest.fixture(scope="module")
def payload():
    return full_payload()


@pytest.fixture
def reader(payload):
    subject = StateReader()
    subject.state = payload
    return subject


# MARK: panels


PANEL_NAMES = ("home", "shop", "bag", "collection", "settings")


@pytest.mark.parametrize("name", PANEL_NAMES)
def test_every_panel_renders_a_full_payload(qt_app, reader, payload, name):
    window = Window(reader)
    panel = window.panels[name]
    panel.update(payload)
    assert panel.layout_.count() > 0, f"{name} produced no widgets"


@pytest.mark.parametrize("name", PANEL_NAMES)
def test_every_panel_survives_an_empty_state(qt_app, name):
    """The state before the daemon has ever run, which is what a fresh install
    sees. A front end that raises here never shows anything at all."""
    empty = StateReader()
    window = Window(empty)
    window.panels[name].update(None)
    window.panels[name].update({})


@pytest.mark.parametrize("name", PANEL_NAMES)
def test_updating_twice_does_not_double_the_contents(qt_app, reader, payload, name):
    """A widget removed from a layout is still parented and still painted until
    Qt collects it, so a rebuild without an explicit delete shows both."""
    window = Window(reader)
    panel = window.panels[name]
    panel.update(payload)
    first = panel.layout_.count()
    panel.update(payload)
    assert panel.layout_.count() == first


def test_home_shows_the_companion_not_the_pinned_species(qt_app, payload):
    """Pinning changes the tray icon; hiding the companion in Home would make
    its progress unreachable.

    The two paths are set apart explicitly: the shared fixture has no sprite
    store, so both come back empty and the assertion would hold either way.
    """
    pinned = dict(
        payload,
        companion=dict(
            payload["companion"],
            sprite_path="/cache/5-a.gif",
            panel_sprite_path="/cache/3-sha.gif",
        ),
    )
    subject = StateReader()
    subject.state = pinned
    window = Window(subject)
    window.panels["home"].update(pinned)
    assert window.panels["home"].sprite._path == "/cache/5-a.gif"


# MARK: the window


def test_the_footer_reports_freshness(qt_app, reader, payload):
    window = Window(reader)
    window.refresh(payload)
    assert "Updated" in window.footer.text()


def test_the_footer_reports_daemon_errors_before_freshness(qt_app, payload):
    subject = StateReader()
    subject.state = dict(payload, errors=["claude_code: boom"])
    window = Window(subject)
    window.refresh(subject.state)
    assert "boom" in window.footer.text()


def test_the_footer_reports_a_stale_daemon(qt_app, payload):
    subject = StateReader()
    subject.state = dict(payload, updated_at=1.0)  # 1970
    window = Window(subject)
    window.refresh(subject.state)
    assert window.footer.text() == subject.text("stale_warning")


def test_only_the_visible_tab_is_rebuilt(qt_app, reader, payload):
    """The others would throw their children away again before anyone saw them."""
    window = Window(reader)
    window.tabs.setCurrentIndex(0)
    window.refresh(payload)
    assert window.panels["home"].layout_.count() > 0
    assert window.panels["shop"].layout_.count() == 0


# MARK: the tray


def test_the_tray_has_an_icon_before_the_first_sprite(qt_app):
    """Without one the tray entry is invisible and there is no way to open the
    window, which looks exactly like a crash."""
    tray = TrayApp(qt_app, StateReader())
    assert not tray.tray.icon().isNull()


def test_the_tooltip_carries_the_panel_numbers(qt_app, reader, payload):
    tray = TrayApp(qt_app, reader)
    tray._update_tray(payload)
    tooltip = tray.tray.toolTip()
    assert payload["panel"]["tokens_text"] in tooltip
    for window in payload["panel"]["limit_windows"]:
        assert window["text"] in tooltip


def test_the_tooltip_falls_back_to_the_app_name(qt_app):
    tray = TrayApp(qt_app, StateReader())
    tray._update_tray(None)
    assert tray.tray.toolTip() == "PokeTokenBar"


def test_the_tray_menu_offers_open_refresh_and_quit(qt_app):
    tray = TrayApp(qt_app, StateReader())
    labels = [action.text() for action in tray.tray.contextMenu().actions()]
    assert labels[0] == "Open"
    assert "Refresh" in labels
    assert "Quit" in labels


def test_polling_an_absent_state_file_does_not_raise(qt_app, tmp_path):
    """The normal state right after install."""
    subject = StateReader(path=tmp_path / "absent.json")
    tray = TrayApp(qt_app, subject)
    tray.poll()
    assert subject.error


# MARK: widgets


def test_a_sprite_does_not_rebuild_for_the_same_path(qt_app, tmp_path):
    """Rebuilding the QMovie every poll restarts the animation from frame one,
    so the companion would stutter rather than loop."""
    sprite = Sprite(32)
    sprite.set_path(None)
    assert sprite._path is None
    sprite.set_path(str(tmp_path / "missing.gif"))
    first = sprite._movie
    sprite.set_path(str(tmp_path / "missing.gif"))
    assert sprite._movie is first


def test_a_missing_sprite_file_leaves_the_label_blank(qt_app, tmp_path):
    sprite = Sprite(32)
    sprite.set_path(str(tmp_path / "nope.gif"))
    assert sprite.pixmap().isNull()


def test_a_meter_clamps_past_full(qt_app):
    """A limit over 100% must read as full rather than wrapping."""
    assert meter(1.5).value() == 100
    assert meter(-1).value() == 0
    assert meter(0.42).value() == 42


def test_level_colours_are_stated_not_themed():
    """"Close to your limit" has to read as a warning in any theme."""
    assert level_colour("crit") != level_colour("ok")
    assert level_colour(None) == level_colour("ok")
    assert level_colour("nonsense") == level_colour("ok")


# MARK: formatting shared with the other front ends


def test_resets_in_counts_down_rather_than_printing_a_timestamp():
    """The minute is floored, as it is in the other front ends, so a moment
    short of 2h15m reads as 2h 14m. Asserting the exact minute would make this
    fail on the microseconds between building the input and reading it."""
    from datetime import datetime, timedelta, timezone

    soon = (datetime.now(timezone.utc) + timedelta(hours=2, minutes=15)).isoformat()
    assert panels.resets_in(soon, lambda k: k) in ("2h 15m", "2h 14m")

    later = (datetime.now(timezone.utc) + timedelta(days=3, hours=4)).isoformat()
    assert panels.resets_in(later, lambda k: k).startswith("3d ")


def test_a_past_reset_says_so():
    assert panels.resets_in("2020-01-01T00:00:00Z", lambda k: k) == "resetting_now"


def test_an_unparseable_reset_is_blank_not_an_error():
    for value in (None, "", "not a date", 12345):
        assert panels.resets_in(value, lambda k: k) == ""


def test_ago_reads_as_english():
    assert panels.ago(5) == "just now"
    assert panels.ago(600) == "10 min ago"
    assert panels.ago(None) == ""


# MARK: settings coverage


def test_the_settings_panel_offers_every_daemon_setting():
    """A setting nobody can change may as well not exist."""
    from poketokenbar import config

    offered = {key for key, *_ in panels.SettingsPanel.TOGGLES}
    offered |= {key for key, *_ in panels.SettingsPanel.SPINS}
    offered |= {key for key, *_ in panels.SettingsPanel.CHOICES}
    not_for_a_form = {
        "floating_pet_x",       # set by dragging the pet
        "floating_pet_y",
        "custom_scan_roots",    # its own per-provider fields
    }
    missing = set(config.DEFAULTS) - offered - not_for_a_form
    assert not missing, f"settings with no control: {sorted(missing)}"


def test_every_settings_key_has_a_daemon_default():
    """config.load drops a key it has no default for, so a wrong name here is a
    control that changes nothing."""
    from poketokenbar import config

    offered = {key for key, *_ in panels.SettingsPanel.TOGGLES}
    offered |= {key for key, *_ in panels.SettingsPanel.SPINS}
    offered |= {key for key, *_ in panels.SettingsPanel.CHOICES}
    assert not offered - set(config.DEFAULTS)


def test_the_language_choice_matches_the_daemon_catalogue():
    from poketokenbar import l10n

    choices = dict((key, options) for key, _label, options in panels.SettingsPanel.CHOICES)
    assert list(choices["language"]) == list(l10n.LANGUAGES)
