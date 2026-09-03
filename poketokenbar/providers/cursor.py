"""Cursor usage — ports the local half of Cursor's reader in
LocalAdditionalUsageProvider.swift.

Cursor keeps its chat history in the VS Code-style key/value store
`state.vscdb`, where every `bubbleId:*` row is one chat bubble carrying
`tokenCount.{inputTokens, outputTokens}`, a `createdAt`, and a nullable
`modelType`.

Costs are not reported: an included-plan Cursor account is billed by request,
not per token, and the dashboard shows tokens only.

**Path remapping.** This is one of only two sources whose location actually
differs from macOS. Cursor is an Electron app, so its user-data directory is
`app.getPath("userData")`:

    macOS    ~/Library/Application Support/Cursor/User/globalStorage
    Linux    $XDG_CONFIG_HOME/Cursor/User/globalStorage  (~/.config/Cursor/...)

The Linux path follows the Electron convention that VS Code itself uses
(`~/.config/Code`), but unlike every other reader here it is not pinned by an
upstream test — nothing in the Swift suite exercises a Linux layout. Treat it as
the one place a first Linux user is most likely to find nothing, and prefer a
report over a guess if that happens: `$CURSOR_DATA_DIR` overrides it meanwhile.

Not yet ported: the signed-in dashboard API, which upstream prefers over this
local scan when a Cursor login is present. The local store is what that path
falls back to, so this reads usage offline; it can undercount against the
dashboard for usage that never touched this machine.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Mapping

from ..models import Entry
from .base import loads, parse_iso, to_int
from .sqlite_source import SQLiteProvider, date_value, make_entry, query

_SQL = "SELECT rowid, key, value FROM cursorDiskKV WHERE key GLOB 'bubbleId:*'"


def flexible_date(raw) -> datetime | None:
    """`createdAt` is an ISO-8601 string in some rows and an epoch number in others."""
    if isinstance(raw, str):
        return parse_iso(raw)
    return date_value(raw)


def parse_bubble(obj: dict, key: str) -> Entry | None:
    token_count = obj.get("tokenCount")
    if not isinstance(token_count, dict):
        return None
    input_tokens = to_int(token_count.get("inputTokens"))
    output = to_int(token_count.get("outputTokens"))
    if input_tokens + output <= 0:
        return None
    date = flexible_date(obj.get("createdAt"))
    if date is None:
        return None
    model = obj.get("modelType")
    return make_entry(
        f"cursor|{key}",
        date,
        model if isinstance(model, str) and model else "unknown",
        input=input_tokens,
        output=output,
    )


def parse_database(path: Path) -> list[Entry]:
    rows = query(path, _SQL)
    if not rows:
        return []
    out: list[Entry] = []
    for _rowid, key, payload in rows:
        if not isinstance(key, str):
            continue
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8", "replace")
        if not isinstance(payload, str):
            continue
        try:
            obj = loads(payload)
        except Exception:
            continue
        if not isinstance(obj, dict):
            continue
        entry = parse_bubble(obj, key)
        if entry is not None:
            out.append(entry)
    return out


def user_data_dirs(home: Path | None = None, env: Mapping[str, str] | None = None) -> list[Path]:
    """Electron user-data directories for Cursor and Cursor Nightly."""
    env = os.environ if env is None else env
    home = home or Path.home()
    configured = (env.get("CURSOR_DATA_DIR") or "").strip()
    if configured:
        return [Path(configured).expanduser()]
    config_home = (env.get("XDG_CONFIG_HOME") or "").strip()
    base = Path(config_home).expanduser() if config_home else home / ".config"
    return [
        base / "Cursor" / "User" / "globalStorage",
        base / "Cursor Nightly" / "User" / "globalStorage",
    ]


class CursorProvider(SQLiteProvider):
    """Cursor local usage, read from its chat store."""

    id = "cursor"
    display_name = "Cursor"
    # Included-plan usage is billed by request, and the dashboard is token-only.
    reports_cost = False
    PARSER_VERSION = 1
    database_names = ("state.vscdb",)

    def curated_roots(self) -> list[Path]:
        return user_data_dirs(self._home)

    def parse_file(self, path: Path) -> list[Entry]:
        return parse_database(path)
