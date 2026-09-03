"""Per-model breakdown — ports the Pi attribution cases from PiUsageTests.swift.

Upstream fills this for one opt-in provider. Here every source records a real
model id, so the breakdown is collected for all of them and the UI decides when
to show it — a per-provider opt-in would be the kind of id-keyed branch the
extension rules keep out of shared aggregation.
"""

import json

from poketokenbar import state
from poketokenbar.models import DailyUsage
from poketokenbar.providers import pi


def write_session(tmp_path, objects, sub=".pi/agent/sessions"):
    root = tmp_path / sub
    root.mkdir(parents=True, exist_ok=True)
    path = root / "session.jsonl"
    path.write_text("\n".join(json.dumps(o) for o in objects), encoding="utf-8")
    return path


def message(entry_id, model, input_tokens, timestamp="2026-08-17T10:00:00.000Z"):
    return {
        "type": "message",
        "id": entry_id,
        "timestamp": timestamp,
        "message": {
            "role": "assistant",
            "model": model,
            "usage": {"input": input_tokens, "output": 0, "cacheWrite": 0, "cacheRead": 0},
        },
    }


def test_one_session_log_is_broken_down_by_the_model_that_answered(tmp_path):
    """Pi and its forks route several models through a single session file."""
    write_session(
        tmp_path,
        [
            message("a", "claude-opus-5", 100),
            message("b", "gpt-5.5", 30),
            message("c", "claude-opus-5", 50),
        ],
    )
    provider = pi.PiProvider(home=tmp_path)
    entries = provider.scan_entries()
    daily = provider.aggregate_daily(entries[0].local_day, entries)

    assert daily.models == {"claude-opus-5": 150, "gpt-5.5": 30}
    assert daily.total_tokens == 180, "the breakdown must add up to the day"


def test_a_single_model_day_still_records_its_one_row(tmp_path):
    """The UI gates on the row count; the daemon does not decide for it."""
    write_session(tmp_path, [message("a", "claude-opus-5", 100)])
    provider = pi.PiProvider(home=tmp_path)
    entries = provider.scan_entries()
    daily = provider.aggregate_daily(entries[0].local_day, entries)
    assert daily.models == {"claude-opus-5": 100}


def test_rows_are_ordered_biggest_first():
    rows = state._model_rows({"small": 10, "big": 900, "middle": 100})
    assert [r["model"] for r in rows] == ["big", "middle", "small"]


def test_ties_break_on_the_model_name_so_the_order_is_stable():
    """Two equal models would otherwise swap places on every poll."""
    rows = state._model_rows({"b": 50, "a": 50})
    assert [r["model"] for r in rows] == ["a", "b"]
    assert rows == state._model_rows({"a": 50, "b": 50})


def test_zero_token_models_are_not_listed():
    assert state._model_rows({"unused": 0, "used": 5}) == [
        {
            "model": "used",
            "total_tokens": 5,
            "total_tokens_text": "5",
            "total_tokens_compact": "5",
        }
    ]


def test_state_exposes_the_breakdown_per_provider():
    daily = DailyUsage(date="2026-08-17", total_tokens=180, models={"m1": 150, "m2": 30})
    payload = state.build({"pi": daily}, {}, [])
    rows = payload["providers"]["pi"]["models"]
    assert [r["model"] for r in rows] == ["m1", "m2"]
    assert rows[0]["total_tokens"] == 150


def test_state_combines_the_same_model_across_providers():
    """A day spent on one model through two tools reads as one row."""
    payload = state.build(
        {
            "pi": DailyUsage(date="d", total_tokens=100, models={"claude-opus-5": 100}),
            "omp": DailyUsage(date="d", total_tokens=40, models={"claude-opus-5": 40}),
        },
        {},
        [],
    )
    assert payload["today"]["models"] == [
        {
            "model": "claude-opus-5",
            "total_tokens": 140,
            "total_tokens_text": "140",
            "total_tokens_compact": "140",
        }
    ]


def test_large_counts_are_preformatted():
    """QML renders large numbers as 8.55336e+07, so formatting stays in one place."""
    row = state._model_rows({"m": 85_533_600})[0]
    assert row["total_tokens_text"] == "85,533,600"
    assert "e+" not in row["total_tokens_compact"]


def test_a_day_with_no_usage_has_no_rows():
    assert state.build({}, {}, [])["today"]["models"] == []
