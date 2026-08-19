"""state.json — the daemon's only output to the UI.

Written atomically (temp + rename) so the plasmoid, which polls, can never
read a torn file. Always parses: a failing poll produces errors[], never a
partial document.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from . import format as fmt
from . import limits
from .models import DailyUsage

SCHEMA_VERSION = 1


def default_path() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state")
    return Path(base) / "poketokenbar" / "state.json"


def _limits_payload(status) -> dict:
    """Serialise a limits.LimitStatus, or an empty dict when unavailable."""
    if status is None:
        return {}

    def window(w):
        if w is None:
            return None
        return {
            "utilization": w.utilization,
            "resets_at": w.resets_at,
            "severity": w.severity,
        }

    return {
        "session": window(status.session),
        "weekly": window(status.weekly),
        "plan": status.subscription_type,
    }


def build(
    daily_by_provider: dict[str, DailyUsage],
    config_values: dict,
    errors: list[str],
    scanning: bool = False,
    limit_status=None,
) -> dict:
    total_tokens = sum(d.total_tokens for d in daily_by_provider.values())
    total_cost = sum(d.total_cost for d in daily_by_provider.values())
    limit_mode = config_values.get("limit_display_mode", "both")

    return {
        "schema_version": SCHEMA_VERSION,
        "updated_at": time.time(),
        "scanning": scanning,
        "errors": errors,
        "today": {
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "tokens_grouped": fmt.grouped(total_tokens),
            "cost_text": fmt.cost(total_cost),
        },
        "providers": {
            pid: {
                "total_tokens": d.total_tokens,
                "total_cost": d.total_cost,
                "input_tokens": d.input_tokens,
                "output_tokens": d.output_tokens,
                "cache_creation_tokens": d.cache_creation_tokens,
                "cache_read_tokens": d.cache_read_tokens,
            }
            for pid, d in daily_by_provider.items()
        },
        "limits": _limits_payload(limit_status),
        "panel": {
            "tokens_text": fmt.compact(total_tokens)
            if config_values.get("show_tokens_in_menu")
            else "",
            "cost_text": fmt.cost_compact(total_cost)
            if config_values.get("show_cost_in_menu")
            else "",
            "limit_text": limits.panel_text(limit_status, limit_mode)
            if config_values.get("show_limit_in_menu")
            else "",
            # Structured form so the panel can colour each number on its own.
            "limit_windows": [
                {
                    "value": w.utilization,
                    "text": limits.format_percent(w.utilization),
                    "level": limits.level(
                        w.utilization,
                        config_values.get("warn_threshold", 80),
                        config_values.get("crit_threshold", 95),
                    ),
                }
                for w in limits.windows(limit_status, limit_mode)
            ]
            if config_values.get("show_limit_in_menu")
            else [],
            "sprite_path": "",  # populated in Plan 3
        },
    }


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)
