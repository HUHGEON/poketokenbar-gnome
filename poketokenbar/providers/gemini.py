"""Gemini CLI usage — ports the Gemini half of LocalUsageReader.swift.

Sessions live at `~/.gemini/tmp/<hash>/chats/session-*.jsonl`, with older
installs keeping a single `.json` conversation record instead.

Token mapping preserves what `usageMetadata` means, so that `Entry.total`
equals the log's own `totalTokenCount`:

    input  = (input - cached) + tool   # toolUsePrompt is charged as input
    output = output + thoughts         # thoughts are reasoning output
    cache_read  = cached
    cache_write = 0                    # Gemini never reports a cache write

Within one file the last record for an id wins: `message_update` lines restate a
turn as it completes, so the final value is the one that counts. Across files
the largest total wins, the same as every other JSONL source.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Iterator

from ..models import Entry
from .base import ScanningProvider, loads, local_day, parse_iso, to_int


def _absorb(
    obj: dict,
    file_name: str,
    fallback: datetime | None,
    by_id: dict[str, Entry],
    order: list[str],
) -> None:
    """Fold one record carrying `tokens` into the per-id table."""
    tokens = obj.get("tokens")
    if not isinstance(tokens, dict):
        return
    raw_id = obj.get("id")
    entry_id = raw_id if isinstance(raw_id, str) and raw_id else str(uuid.uuid4())

    date = None
    raw_ts = obj.get("timestamp")
    if isinstance(raw_ts, str):
        date = parse_iso(raw_ts)
    if date is None:
        date = fallback
    if date is None:
        return

    model = obj.get("model")
    cached = to_int(tokens.get("cached"))
    entry = Entry(
        id=f"gemini|{file_name}|{entry_id}",
        date=date,
        local_day=local_day(date),
        model=model if isinstance(model, str) and model else "gemini",
        input=max(0, to_int(tokens.get("input")) - cached) + to_int(tokens.get("tool")),
        output=to_int(tokens.get("output")) + to_int(tokens.get("thoughts")),
        cache_write=0,
        cache_read=cached,
    )
    if entry_id not in by_id:
        order.append(entry_id)
    by_id[entry_id] = entry  # a later message_update carries the final value


def parse_file(path: Path) -> list[Entry]:
    by_id: dict[str, Entry] = {}
    order: list[str] = []
    file_name = path.name

    if path.suffix == ".jsonl":
        last_timestamp: datetime | None = None
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    # Substring prefilter before the JSON decode — a cold scan
                    # reads far more lines than it keeps.
                    if '"tokens"' not in line and '"timestamp"' not in line:
                        continue
                    try:
                        obj = loads(line)
                    except Exception:
                        continue
                    if not isinstance(obj, dict):
                        continue
                    raw_ts = obj.get("timestamp")
                    if isinstance(raw_ts, str):
                        parsed = parse_iso(raw_ts)
                        if parsed is not None:
                            # Records without their own timestamp inherit the
                            # most recent one seen above them in the file.
                            last_timestamp = parsed
                    _absorb(obj, file_name, last_timestamp, by_id, order)
        except OSError:
            return []
        return [by_id[i] for i in order]

    # Legacy single-document conversation record.
    try:
        obj = loads(path.read_bytes())
    except (OSError, Exception):
        return []
    if not isinstance(obj, dict):
        return []
    messages = obj.get("messages")
    if not isinstance(messages, list):
        return []
    raw_start = obj.get("startTime")
    session_start = parse_iso(raw_start) if isinstance(raw_start, str) else None
    for message in messages:
        if isinstance(message, dict):
            _absorb(message, file_name, session_start, by_id, order)
    return [by_id[i] for i in order]


def scan_roots(home: Path | None = None) -> list[Path]:
    """`~/.gemini/tmp` — identical on Linux and macOS."""
    return [(home or Path.home()) / ".gemini" / "tmp"]


class GeminiProvider(ScanningProvider):
    """Gemini CLI local usage."""

    id = "gemini"
    display_name = "Gemini CLI"
    reports_cost = True
    PARSER_VERSION = 1

    def curated_roots(self) -> list[Path]:
        return scan_roots(self._home)

    def files(self, root: Path) -> Iterator[Path]:
        # Both shapes coexist: .jsonl for current installs, .json for older ones.
        yield from root.rglob("*.jsonl")
        yield from root.rglob("*.json")

    def parse_file(self, path: Path) -> list[Entry]:
        return parse_file(path)
