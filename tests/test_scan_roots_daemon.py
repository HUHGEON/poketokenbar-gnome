"""Extra scan folders, end to end through config, daemon, and state.json.

Each half is covered elsewhere; what these pin is the wiring between them,
which is where the setting can silently stop working while every unit test
still passes.
"""

import json

from poketokenbar import config, state
from poketokenbar.daemon import Daemon
from poketokenbar.providers.gemini import GeminiProvider


def write_session(root, name="session-a.jsonl", tokens=10):
    root.mkdir(parents=True, exist_ok=True)
    (root / name).write_text(
        json.dumps(
            {
                "id": name,
                "timestamp": "2026-06-30T10:00:00.000Z",
                "tokens": {"input": tokens},
            }
        ),
        encoding="utf-8",
    )


def make_daemon(tmp_path, home):
    daemon = Daemon(
        state_path=tmp_path / "state.json",
        config_path=tmp_path / "config.json",
        cache=None,
        providers=[],
    )
    daemon.providers = [
        GeminiProvider(home=home, custom_roots=daemon.custom_scan_roots)
    ]
    return daemon


def test_config_round_trips_one_providers_folders(tmp_path):
    path = tmp_path / "config.json"
    config.set_scan_roots(path, "gemini", "/tmp/a, /tmp/b")
    assert config.load(path)["custom_scan_roots"] == {"gemini": "/tmp/a, /tmp/b"}


def test_setting_one_provider_leaves_the_others_alone(tmp_path):
    path = tmp_path / "config.json"
    config.set_scan_roots(path, "gemini", "/tmp/a")
    config.set_scan_roots(path, "cursor", "/tmp/b")
    assert config.load(path)["custom_scan_roots"] == {"gemini": "/tmp/a", "cursor": "/tmp/b"}


def test_clearing_removes_the_entry_rather_than_storing_blank(tmp_path):
    path = tmp_path / "config.json"
    config.set_scan_roots(path, "gemini", "/tmp/a")
    config.set_scan_roots(path, "gemini", "   ")
    assert config.load(path)["custom_scan_roots"] == {}


def test_a_provider_id_with_a_separator_is_refused(tmp_path):
    import pytest

    with pytest.raises(ValueError):
        config.set_scan_roots(tmp_path / "config.json", "../evil", "/tmp/a")


def test_the_daemon_reads_the_folder_it_was_configured_with(tmp_path):
    home = tmp_path / "home"
    elsewhere = tmp_path / "elsewhere"
    write_session(elsewhere)

    daemon = make_daemon(tmp_path, home)
    assert daemon.providers[0].scan_entries() == [], "nothing configured yet"

    config.set_scan_roots(daemon.config_path, "gemini", str(elsewhere))
    daemon.config_values = config.load(daemon.config_path)
    assert len(daemon.providers[0].scan_entries()) == 1


def test_reload_config_takes_effect_without_restarting(tmp_path):
    """The providers hold a callable, not a snapshot, so a live reload lands."""
    home = tmp_path / "home"
    elsewhere = tmp_path / "elsewhere"
    write_session(elsewhere)

    daemon = make_daemon(tmp_path, home)
    provider = daemon.providers[0]
    assert provider.roots() == []

    config.set_scan_roots(daemon.config_path, "gemini", str(elsewhere))
    daemon.config_values = config.load(daemon.config_path)
    assert provider.roots() == [elsewhere]


def test_settings_payload_reports_the_surviving_count(tmp_path):
    home = tmp_path / "home"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    daemon = make_daemon(tmp_path, home)
    config.set_scan_roots(daemon.config_path, "gemini", str(elsewhere))
    daemon.config_values = config.load(daemon.config_path)

    row = daemon.settings_payload()["providers"][0]
    assert row["id"] == "gemini"
    assert row["display_name"] == "Gemini CLI"
    assert row["custom_scan_roots"] == str(elsewhere)
    assert row["matched_folders"] == 1


def test_settings_payload_reports_zero_for_a_folder_that_matched_nothing(tmp_path):
    daemon = make_daemon(tmp_path, tmp_path / "home")
    config.set_scan_roots(daemon.config_path, "gemini", str(tmp_path / "absent"))
    daemon.config_values = config.load(daemon.config_path)
    assert daemon.settings_payload()["providers"][0]["matched_folders"] == 0


def test_settings_payload_reaches_state_json(tmp_path):
    """The settings page has no other way to learn the match count."""
    daemon = make_daemon(tmp_path, tmp_path / "home")
    payload = state.build({}, daemon.config_values, [], settings=daemon.settings_payload())
    assert payload["settings"]["providers"][0]["id"] == "gemini"


def test_state_settings_block_defaults_to_empty():
    assert state.build({}, {}, [])["settings"] == {}
