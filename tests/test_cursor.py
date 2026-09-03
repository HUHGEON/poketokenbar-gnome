"""Cursor parsing — ports CursorUsageTests.swift (the local-store half).

The dashboard API path is not ported yet, so the cases here are the ones that
exercise `state.vscdb` directly.
"""

import json
import sqlite3

from poketokenbar.providers import cursor


def write_store(path, rows):
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "CREATE TABLE cursorDiskKV (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB)"
        )
        connection.executemany("INSERT INTO cursorDiskKV VALUES (?,?)", rows)
        connection.commit()
    finally:
        connection.close()
    return path


def bubble(input=1500, output=800, created_at="2026-01-04T10:34:54.766Z", model="claude-3.5-sonnet"):
    doc = {"tokenCount": {"inputTokens": input, "outputTokens": output}, "createdAt": created_at}
    if model is not None:
        doc["modelType"] = model
    return json.dumps(doc)


def test_reads_bubble_tokens_and_ignores_other_keys(tmp_path):
    path = write_store(
        tmp_path / "state.vscdb",
        [
            ("bubbleId:tab-1:msg-1", bubble()),
            ("composerData:other", json.dumps({"unrelated": True})),
            ("bubbleId:tab-1:msg-zero", bubble(input=0, output=0, model="gpt-4o")),
            # GLOB is case-sensitive: lowercase must not match.
            ("bubbleid:tab-1:wrong-case", bubble(input=999, output=1, model="gpt-4o")),
        ],
    )
    entries = cursor.parse_database(path)
    assert len(entries) == 1, "only case-exact bubbleId:* rows with tokens count"
    e = entries[0]
    assert e.input == 1500
    assert e.output == 800
    assert e.model == "claude-3.5-sonnet"
    assert e.id == "cursor|bubbleId:tab-1:msg-1"


def test_zero_token_bubbles_are_ignored():
    assert cursor.parse_bubble(json.loads(bubble(input=0, output=0)), "k") is None


def test_missing_token_count_is_ignored():
    assert cursor.parse_bubble({"createdAt": "2026-01-04T10:00:00Z"}, "k") is None


def test_missing_model_falls_back_to_unknown():
    entry = cursor.parse_bubble(json.loads(bubble(model=None)), "k")
    assert entry.model == "unknown"


def test_missing_or_invalid_created_at_is_ignored():
    assert cursor.parse_bubble({"tokenCount": {"inputTokens": 5}}, "k") is None
    assert (
        cursor.parse_bubble(json.loads(bubble(created_at="not a date")), "k") is None
    )


def test_numeric_created_at_in_milliseconds_and_seconds():
    ms = cursor.parse_bubble(json.loads(bubble(created_at=1767522894766)), "k")
    seconds = cursor.parse_bubble(json.loads(bubble(created_at=1767522894)), "k")
    assert abs(ms.date.timestamp() - 1767522894.766) < 0.01
    assert abs(seconds.date.timestamp() - 1767522894) < 0.01


def test_fractional_seconds_are_accepted():
    entry = cursor.parse_bubble(json.loads(bubble(created_at="2026-01-04T10:34:54.766Z")), "k")
    assert abs(entry.date.timestamp() - 1767522894.766) < 0.01


def test_blob_payloads_are_decoded(tmp_path):
    """The column is declared BLOB, so a row can come back as bytes."""
    path = write_store(tmp_path / "state.vscdb", [("bubbleId:b", bubble().encode("utf-8"))])
    assert len(cursor.parse_database(path)) == 1


def test_nonexistent_store_is_silent(tmp_path):
    assert cursor.parse_database(tmp_path / "absent.vscdb") == []


def test_cursor_reports_no_cost(tmp_path):
    """Included-plan usage is billed by request; the dashboard is token-only."""
    root = tmp_path / ".config" / "Cursor" / "User" / "globalStorage"
    root.mkdir(parents=True)
    write_store(root / "state.vscdb", [("bubbleId:b", bubble(input=1_000_000, output=1_000_000))])
    provider = cursor.CursorProvider(home=tmp_path)
    entries = provider.scan_entries()
    daily = provider.aggregate_daily(entries[0].local_day, entries)
    assert provider.reports_cost is False
    assert daily.total_cost == 0
    assert daily.total_tokens == 2_000_000


# MARK: paths — the one source whose location really moves


def test_linux_user_data_dirs_follow_the_electron_convention(tmp_path):
    """macOS keeps this under Library/Application Support; Linux under XDG config.

    Unlike the parsers, this path is not pinned by any upstream test — it
    follows the Electron/VS Code convention and wants a real-world confirmation.
    """
    assert cursor.user_data_dirs(home=tmp_path, env={}) == [
        tmp_path / ".config" / "Cursor" / "User" / "globalStorage",
        tmp_path / ".config" / "Cursor Nightly" / "User" / "globalStorage",
    ]


def test_xdg_config_home_is_honoured(tmp_path):
    elsewhere = tmp_path / "xdg"
    dirs = cursor.user_data_dirs(home=tmp_path, env={"XDG_CONFIG_HOME": str(elsewhere)})
    assert dirs[0] == elsewhere / "Cursor" / "User" / "globalStorage"


def test_cursor_data_dir_overrides_everything(tmp_path):
    """The escape hatch while the Linux default is still unconfirmed."""
    custom = tmp_path / "elsewhere"
    assert cursor.user_data_dirs(home=tmp_path, env={"CURSOR_DATA_DIR": str(custom)}) == [
        custom
    ]


def test_nightly_is_scanned_alongside_stable(tmp_path):
    base = tmp_path / ".config"
    for flavour in ("Cursor", "Cursor Nightly"):
        root = base / flavour / "User" / "globalStorage"
        root.mkdir(parents=True)
        write_store(root / "state.vscdb", [(f"bubbleId:{flavour}", bubble())])
    assert len(cursor.CursorProvider(home=tmp_path).scan_entries()) == 2


def test_provider_identity():
    provider = cursor.CursorProvider()
    assert provider.id == "cursor"
    assert provider.display_name == "Cursor"
