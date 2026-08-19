"""Codex usage — ports the Codex half of LocalUsageReader.swift.

Rollout files at ~/.codex/sessions/**/rollout-*.jsonl carry
`payload.type == "token_count"` events. Each event's `info.last_token_usage`
is the delta for that turn, so entries are summed rather than max-reduced.

Turn identity is `(file, turn index)`. A forked or resumed session copies its
parent's events verbatim, so the same turn can appear in several files; the
provider deduplicates on the session id it finds in the file metadata.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date as _date
from pathlib import Path

from .. import pricing
from ..cache import ScanCache
from ..models import DailyUsage, Entry, ProviderEnrichment
from .claude import _parse_timestamp, jsonl_files

PARSER_VERSION = 1


def _int(value) -> int:
    return value if isinstance(value, int) else 0


@dataclass(slots=True)
class ParsedRollout:
    entries: list[Entry]
    session_id: str | None


def parse_rollout(path: Path) -> ParsedRollout:
    """Parse one rollout file into per-turn entries."""
    entries: list[Entry] = []
    session_id: str | None = None
    model = "gpt-5.5"
    turn = 0
    name = path.name

    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"session_id"' in line or '"model"' in line:
                    obj = _load(line)
                    if isinstance(obj, dict):
                        found = _find_session_id(obj)
                        if found and session_id is None:
                            session_id = found
                        found_model = _find_model(obj)
                        if found_model:
                            model = found_model
                if "token_count" not in line:
                    continue
                obj = _load(line)
                if not isinstance(obj, dict):
                    continue
                payload = obj.get("payload")
                if not isinstance(payload, dict) or payload.get("type") != "token_count":
                    continue
                info = payload.get("info")
                if not isinstance(info, dict):
                    continue
                last = info.get("last_token_usage")
                if not isinstance(last, dict):
                    continue
                date = _parse_timestamp(obj.get("timestamp", ""))
                if date is None:
                    continue

                input_total = _int(last.get("input_tokens"))
                cached = _int(last.get("cached_input_tokens"))
                entries.append(
                    Entry(
                        # Keyed by (cumulative, delta), not by file position or
                        # timestamp. A fork replays the parent's turns with
                        # fresh timestamps but an identical cumulative
                        # sequence, so this collapses the copies while keeping
                        # the fork's own turns. The delta is part of the key
                        # because a fork emits a zero-delta turn that repeats
                        # the parent's final cumulative value.
                        id=f"codex|{_cumulative(info)}|{_last_total(last)}",
                        date=date,
                        local_day=date.astimezone().strftime("%Y-%m-%d"),
                        model=model,
                        input=max(0, input_total - cached),
                        output=_int(last.get("output_tokens")),
                        cache_write=0,
                        cache_read=cached,
                    )
                )
                turn += 1
    except OSError:
        return ParsedRollout([], None)

    return ParsedRollout(entries, session_id)


def _cumulative(info: dict) -> int:
    total = info.get("total_token_usage")
    return _int(total.get("total_tokens")) if isinstance(total, dict) else 0


def _last_total(last: dict) -> int:
    return _int(last.get("total_tokens"))


def _load(line: str):
    try:
        return json.loads(line)
    except ValueError:
        return None


def _find_session_id(obj: dict) -> str | None:
    for key in ("session_id", "sessionId", "id"):
        value = obj.get(key)
        if isinstance(value, str) and value:
            return value
    payload = obj.get("payload")
    if isinstance(payload, dict):
        return _find_session_id(payload)
    return None


def _find_model(obj: dict) -> str | None:
    value = obj.get("model")
    if isinstance(value, str) and value:
        return value
    payload = obj.get("payload")
    if isinstance(payload, dict):
        return _find_model(payload)
    return None


def session_roots(home: Path | None = None) -> list[Path]:
    home = home or Path.home()
    root = home / ".codex" / "sessions"
    return [root] if root.is_dir() else []


class CodexProvider:
    id = "codex"
    display_name = "Codex"
    reports_cost = True
    PARSER_VERSION = PARSER_VERSION

    def __init__(self, cache: ScanCache | None = None, home: Path | None = None) -> None:
        self._cache = cache
        self._home = home

    def scan_entries(self) -> list[Entry]:
        by_id: dict[str, Entry] = {}
        for root in session_roots(self._home):
            for path in sorted(jsonl_files(root)):
                for entry in parse_rollout(path).entries:
                    by_id.setdefault(entry.id, entry)
        return list(by_id.values())

    @staticmethod
    def dedup(entries: list[Entry]) -> list[Entry]:
        by_id: dict[str, Entry] = {}
        for e in entries:
            by_id.setdefault(e.id, e)
        return list(by_id.values())

    def fetch_daily(self, today: str | None = None) -> DailyUsage | None:
        day = today or _date.today().strftime("%Y-%m-%d")
        entries = [e for e in self.scan_entries() if e.local_day == day]
        if not entries:
            return None
        daily = DailyUsage(date=day)
        for e in entries:
            daily.input_tokens += e.input
            daily.output_tokens += e.output
            daily.cache_creation_tokens += e.cache_write
            daily.cache_read_tokens += e.cache_read
            daily.total_cost += pricing.cost(
                e.model, e.input, e.output, e.cache_write, e.cache_read
            )
        daily.total_tokens = (
            daily.input_tokens
            + daily.output_tokens
            + daily.cache_creation_tokens
            + daily.cache_read_tokens
        )
        return daily

    def fetch_enrichment(self) -> ProviderEnrichment:
        return ProviderEnrichment()
