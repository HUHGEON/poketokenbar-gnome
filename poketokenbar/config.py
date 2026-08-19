"""Settings shared by the daemon and the plasmoid.

Keys port from UsageStore's UserDefaults. Dropped deliberately:
disableKeychainAccess (no Keychain on Linux) and updateNotificationsEnabled
(no release channel for a personal build).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULTS: dict[str, object] = {
    "refresh_interval": 120,
    "warn_threshold": 80,
    "crit_threshold": 95,
    "show_tokens_in_menu": True,
    "show_cost_in_menu": False,
    "show_limit_in_menu": False,
    "limit_display_mode": "session",
    "limit_notifications": True,
    "companion_notifications": True,
    "status_checks_enabled": True,
    "floating_pet_enabled": False,
    "floating_pet_size": 96,
    "floating_pet_bubble_alerts": True,
    "language": "en",
}


def default_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")
    return Path(base) / "poketokenbar" / "config.json"


def load(path: Path) -> dict:
    values = dict(DEFAULTS)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return values
    if not isinstance(raw, dict):
        return values
    for key, value in raw.items():
        if key in DEFAULTS:
            values[key] = value
    return values


def save(path: Path, values: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(values, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _coerce(key: str, raw: str):
    default = DEFAULTS[key]
    if isinstance(default, bool):
        lowered = raw.strip().lower()
        if lowered in ("true", "1", "yes", "on"):
            return True
        if lowered in ("false", "0", "no", "off"):
            return False
        raise ValueError(f"{key} expects a boolean, got {raw!r}")
    if isinstance(default, int):
        return int(raw)
    return raw


def set_value(path: Path, key: str, raw: str) -> None:
    if key not in DEFAULTS:
        raise KeyError(f"unknown setting: {key}")
    values = load(path)
    values[key] = _coerce(key, raw)
    save(path, values)
