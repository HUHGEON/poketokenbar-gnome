import json

from poketokenbar import config, state
from poketokenbar.models import DailyUsage


def _daily(total=40_930):
    return DailyUsage(
        date="2026-08-18",
        input_tokens=2,
        output_tokens=570,
        cache_creation_tokens=24_155,
        cache_read_tokens=16_203,
        total_tokens=total,
        total_cost=1.25,
    )


def test_build_totals_across_providers():
    payload = state.build({"claude_code": _daily(), "codex": _daily(10)}, config.DEFAULTS, [])
    assert payload["today"]["total_tokens"] == 40_940


def test_build_includes_panel_text():
    payload = state.build({"claude_code": _daily()}, config.DEFAULTS, [])
    assert payload["panel"]["tokens_text"] == "40.9K"


def test_panel_text_respects_show_tokens_setting():
    values = dict(config.DEFAULTS, show_tokens_in_menu=False)
    payload = state.build({"claude_code": _daily()}, values, [])
    assert payload["panel"]["tokens_text"] == ""


def test_panel_includes_cost_when_enabled():
    values = dict(config.DEFAULTS, show_cost_in_menu=True)
    payload = state.build({"claude_code": _daily()}, values, [])
    assert payload["panel"]["cost_text"] == "$1.2"


def test_build_carries_schema_version_and_errors():
    payload = state.build({}, config.DEFAULTS, ["claude_code: boom"])
    assert payload["schema_version"] == state.SCHEMA_VERSION
    assert payload["errors"] == ["claude_code: boom"]


def test_build_with_no_providers_is_zero_not_missing():
    payload = state.build({}, config.DEFAULTS, [])
    assert payload["today"]["total_tokens"] == 0
    assert payload["providers"] == {}


def test_write_is_atomic_and_leaves_no_temp_file(tmp_path):
    p = tmp_path / "state.json"
    state.write(p, state.build({"claude_code": _daily()}, config.DEFAULTS, []))
    assert json.loads(p.read_text(encoding="utf-8"))["today"]["total_tokens"] == 40_930
    assert list(tmp_path.iterdir()) == [p]


def test_write_replaces_previous_content(tmp_path):
    p = tmp_path / "state.json"
    state.write(p, state.build({"claude_code": _daily()}, config.DEFAULTS, []))
    state.write(p, state.build({"claude_code": _daily(1)}, config.DEFAULTS, []))
    assert json.loads(p.read_text(encoding="utf-8"))["today"]["total_tokens"] == 1
