"""Gemini CLI parsing — ports the Gemini cases from LocalUsageReaderTests.swift.

Verified against the Swift reader's rules rather than against a live install:
the token mapping, the update-wins ordering, and the clamp are all pinned by
the upstream suite, so the parser can be checked without owning Gemini CLI.
"""

import json

from poketokenbar.providers import gemini
from poketokenbar.providers.base import MAX_PARSED_TOKEN_VALUE


def write_session(tmp_path, lines, name="session-x.jsonl", sub="hash/chats"):
    directory = tmp_path / sub
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_token_mapping_preserves_usage_metadata(tmp_path):
    """input−cached+tool, output+thoughts, cached as a cache read."""
    line = json.dumps(
        {
            "id": "g1",
            "timestamp": "2026-06-30T10:00:00.000Z",
            "model": "gemini-2.5-pro",
            "tokens": {"input": 100, "cached": 30, "tool": 5, "output": 40, "thoughts": 7},
        }
    )
    entries = gemini.parse_file(write_session(tmp_path, [line]))
    assert len(entries) == 1
    entry = entries[0]
    assert entry.input == 75  # (100 - 30) + 5
    assert entry.output == 47  # 40 + 7
    assert entry.cache_read == 30
    assert entry.cache_write == 0
    assert entry.model == "gemini-2.5-pro"
    # total stays equal to the log's own totalTokenCount
    assert entry.total == 100 + 5 + 40 + 7


def test_message_update_replaces_the_earlier_value(tmp_path):
    """A turn is restated as it completes; the last record is the final one."""
    lines = [
        json.dumps(
            {
                "id": "g1",
                "timestamp": "2026-06-30T10:00:00.000Z",
                "tokens": {"input": 10, "output": 1},
            }
        ),
        json.dumps(
            {
                "type": "message_update",
                "id": "g1",
                "timestamp": "2026-06-30T10:00:05.000Z",
                "tokens": {"input": 10, "output": 90},
            }
        ),
    ]
    entries = gemini.parse_file(write_session(tmp_path, lines))
    assert len(entries) == 1
    assert entries[0].output == 90


def test_record_without_timestamp_inherits_the_last_one_seen(tmp_path):
    lines = [
        json.dumps({"timestamp": "2026-06-30T10:00:00.000Z", "type": "start"}),
        json.dumps({"id": "g2", "tokens": {"input": 4, "output": 2}}),
    ]
    entries = gemini.parse_file(write_session(tmp_path, lines))
    assert len(entries) == 1
    assert entries[0].local_day != ""


def test_record_with_no_timestamp_at_all_is_dropped(tmp_path):
    """No date means no day to bucket it into — dropping beats guessing today."""
    line = json.dumps({"id": "g3", "tokens": {"input": 4, "output": 2}})
    assert gemini.parse_file(write_session(tmp_path, [line])) == []


def test_parsing_clamps_and_its_additions_stay_in_range(tmp_path):
    """Ports testGeminiParsingClampsAndItsAdditionsStayInRange.

    Gemini adds two parsed fields immediately, so the clamp has to survive
    being summed with itself.
    """
    line = json.dumps(
        {
            "id": "g1",
            "timestamp": "2026-06-30T10:00:00.000Z",
            "model": "gemini-2.5-pro",
            "tokens": {
                "input": 1e30,
                "cached": 0,
                "tool": 1e30,
                "output": 1e30,
                "thoughts": 1e30,
            },
        }
    )
    entries = gemini.parse_file(write_session(tmp_path, [line]))
    assert len(entries) == 1
    assert entries[0].input == MAX_PARSED_TOKEN_VALUE * 2
    assert entries[0].output == MAX_PARSED_TOKEN_VALUE * 2


def test_legacy_json_conversation_record(tmp_path):
    """Older installs keep one .json document with a messages array."""
    document = {
        "startTime": "2026-06-30T09:00:00.000Z",
        "messages": [
            {"id": "m1", "tokens": {"input": 10, "output": 5}},
            {"id": "m2", "tokens": {"input": 20, "output": 6}},
        ],
    }
    directory = tmp_path / "hash" / "chats"
    directory.mkdir(parents=True)
    path = directory / "session-legacy.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    entries = gemini.parse_file(path)
    assert len(entries) == 2
    assert sum(e.total for e in entries) == 41


def test_lines_without_tokens_contribute_nothing(tmp_path):
    lines = [
        json.dumps({"timestamp": "2026-06-30T10:00:00.000Z", "type": "user"}),
        json.dumps({"id": "x", "timestamp": "2026-06-30T10:00:01.000Z"}),
        "not json at all",
    ]
    assert gemini.parse_file(write_session(tmp_path, lines)) == []


def test_provider_scans_both_file_shapes(tmp_path):
    """The provider must pick up .jsonl and legacy .json under one root."""
    chats = tmp_path / ".gemini" / "tmp" / "hash" / "chats"
    chats.mkdir(parents=True)
    (chats / "session-a.jsonl").write_text(
        json.dumps(
            {"id": "a", "timestamp": "2026-06-30T10:00:00.000Z", "tokens": {"input": 10}}
        ),
        encoding="utf-8",
    )
    (chats / "session-b.json").write_text(
        json.dumps(
            {
                "startTime": "2026-06-30T10:00:00.000Z",
                "messages": [{"id": "b", "tokens": {"output": 7}}],
            }
        ),
        encoding="utf-8",
    )

    provider = gemini.GeminiProvider(home=tmp_path)
    entries = provider.scan_entries()
    assert sorted(e.total for e in entries) == [7, 10]


def test_absent_root_yields_nothing(tmp_path):
    """No Gemini install must be silence, not an error."""
    provider = gemini.GeminiProvider(home=tmp_path)
    assert provider.scan_entries() == []
    assert provider.fetch_daily() is None
