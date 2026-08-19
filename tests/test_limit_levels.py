from poketokenbar import config, limits, state
from poketokenbar.models import DailyUsage


def _status(session=96.0, weekly=18.0):
    return limits.parse(
        {
            "limits": [
                {"kind": "session", "percent": session, "resets_at": "2026-08-19T01:49:59Z"},
                {"kind": "weekly_all", "percent": weekly, "resets_at": "2026-08-25T12:59:59Z"},
            ]
        }
    )


# --- level thresholds ------------------------------------------------------


def test_level_is_ok_below_warn():
    assert limits.level(50.0, warn=80, crit=95) == "ok"


def test_level_is_warn_at_the_warn_threshold():
    # Boundary belongs to the more severe band — 80 with warn=80 is a warning,
    # not still-fine.
    assert limits.level(80.0, warn=80, crit=95) == "warn"


def test_level_is_crit_at_the_crit_threshold():
    assert limits.level(95.0, warn=80, crit=95) == "crit"


def test_level_is_crit_above_crit():
    assert limits.level(96.0, warn=80, crit=95) == "crit"


# --- panel windows ---------------------------------------------------------


def _panel(cfg=None, status=None):
    values = dict(config.DEFAULTS, show_limit_in_menu=True, show_tokens_in_menu=False)
    values.update(cfg or {})
    payload = state.build(
        {"claude_code": DailyUsage(date="2026-08-18", total_tokens=1)},
        values,
        [],
        limit_status=status if status is not None else _status(),
    )
    return payload["panel"]


def test_panel_exposes_one_window_per_limit():
    windows = _panel()["limit_windows"]
    assert [w["text"] for w in windows] == ["96%", "18%"]


def test_panel_windows_carry_levels_for_colouring():
    windows = _panel()["limit_windows"]
    assert [w["level"] for w in windows] == ["crit", "ok"]


def test_panel_windows_respect_configured_thresholds():
    windows = _panel(cfg={"warn_threshold": 10, "crit_threshold": 20})["limit_windows"]
    assert [w["level"] for w in windows] == ["crit", "warn"]


def test_panel_windows_follow_display_mode():
    windows = _panel(cfg={"limit_display_mode": "session"})["limit_windows"]
    assert [w["text"] for w in windows] == ["96%"]


def test_panel_windows_empty_when_limits_hidden():
    assert _panel(cfg={"show_limit_in_menu": False})["limit_windows"] == []


def test_panel_windows_omit_a_missing_window():
    status = limits.parse({"limits": [{"kind": "session", "percent": 96}]})
    assert [w["text"] for w in _panel(status=status)["limit_windows"]] == ["96%"]


def test_tokens_text_can_be_switched_off_independently():
    assert _panel()["tokens_text"] == ""
