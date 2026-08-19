"""Claude Code usage — ports the Claude half of LocalUsageReader.swift.

Rule: keep `type == "assistant"` rows, sum the four token fields of
`message.usage`, deduplicate on `(message.id, requestId)` keeping the entry
with the LARGEST total, and bucket by local date from `timestamp`.
"""

from __future__ import annotations

import os
from collections.abc import Iterator, Mapping
from datetime import date as _date
from datetime import datetime
from pathlib import Path

from .. import pricing
from ..cache import ScanCache
from ..models import DailyUsage, Entry, ProviderEnrichment

try:  # orjson is ~2x faster on this workload but must not be required
    import orjson

    def _loads(raw: str | bytes):
        return orjson.loads(raw)

except ModuleNotFoundError:  # pragma: no cover - exercised on hosts without orjson
    import json

    def _loads(raw: str | bytes):
        return json.loads(raw)


def _int(value) -> int:
    return value if isinstance(value, int) else 0


def _parse_timestamp(raw: str) -> datetime | None:
    """ISO-8601 with a trailing 'Z' and optional fractional seconds."""
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def parse_line(line: str) -> Entry | None:
    try:
        obj = _loads(line)
    except Exception:
        return None
    if not isinstance(obj, dict) or obj.get("type") != "assistant":
        return None
    msg = obj.get("message")
    if not isinstance(msg, dict):
        return None
    usage = msg.get("usage")
    if not isinstance(usage, dict):
        return None
    date = _parse_timestamp(obj.get("timestamp", ""))
    if date is None:
        return None
    return Entry(
        id=f"{msg.get('id') or ''}|{obj.get('requestId') or ''}",
        date=date,
        local_day=date.astimezone().strftime("%Y-%m-%d"),
        model=msg.get("model") or "unknown",
        # Only top-level fields. usage["iterations"] repeats these numbers.
        input=_int(usage.get("input_tokens")),
        output=_int(usage.get("output_tokens")),
        cache_write=_int(usage.get("cache_creation_input_tokens")),
        cache_read=_int(usage.get("cache_read_input_tokens")),
    )


def dedup_keep_max(entries: list[Entry]) -> list[Entry]:
    """Keep the largest-total entry per id — the completed one."""
    by_id: dict[str, Entry] = {}
    for e in entries:
        existing = by_id.get(e.id)
        if existing is None or e.total > existing.total:
            by_id[e.id] = e
    return list(by_id.values())


def parse_file(path: Path) -> list[Entry]:
    out: list[Entry] = []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                # Substring prefilter before JSON decode — the cold scan reads
                # hundreds of MB and most lines are not assistant turns.
                if '"usage"' not in line or '"assistant"' not in line:
                    continue
                entry = parse_line(line)
                if entry is not None:
                    out.append(entry)
    except OSError:
        return []
    return dedup_keep_max(out)


def project_roots(
    home: Path | None = None, env: Mapping[str, str] | None = None
) -> list[Path]:
    """Existing Claude project roots, symlink-deduplicated.

    macOS also probes ~/Library/Application Support/Claude for Claude Desktop
    embedded sessions. That path cannot exist on Linux, so it is omitted rather
    than branched on.
    """
    home = home or Path.home()
    env = os.environ if env is None else env

    candidates = [home / ".claude" / "projects", home / ".config" / "claude" / "projects"]
    configured = env.get("CLAUDE_CONFIG_DIR")
    if configured:
        candidates.append(Path(configured) / "projects")

    seen: set[Path] = set()
    roots: list[Path] = []
    for path in candidates:
        if not path.is_dir():
            continue
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        roots.append(path)
    return roots


def jsonl_files(root: Path) -> Iterator[Path]:
    """Every *.jsonl under root, including inside hidden directories."""
    yield from root.rglob("*.jsonl")


class ClaudeProvider:
    """Claude Code local usage."""

    id = "claude_code"
    display_name = "Claude Code"
    reports_cost = True
    # Bump when parse_line changes shape, to invalidate cached blobs.
    PARSER_VERSION = 1

    def __init__(self, cache: ScanCache | None = None, home: Path | None = None) -> None:
        self._cache = cache
        self._home = home

    def scan_entries(self) -> list[Entry]:
        """Every parsed entry across all roots, globally deduplicated."""
        all_entries: list[Entry] = []
        live: set[str] = set()
        for root in project_roots(home=self._home):
            for path in jsonl_files(root):
                try:
                    stat = path.stat()
                except OSError:
                    continue
                live.add(str(path))
                entries = None
                if self._cache is not None:
                    entries = self._cache.get(
                        self.id, path, stat.st_mtime, stat.st_size, self.PARSER_VERSION
                    )
                if entries is None:
                    entries = parse_file(path)
                    if self._cache is not None:
                        self._cache.put(
                            self.id,
                            path,
                            stat.st_mtime,
                            stat.st_size,
                            self.PARSER_VERSION,
                            entries,
                        )
                all_entries.extend(entries)
        if self._cache is not None:
            self._cache.prune(self.id, live)
        # Global dedup — the same turn may appear under overlapping roots.
        return dedup_keep_max(all_entries)

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
            # Priced per entry, because a day mixes models with different rates.
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

    def fetch_periods(self, today: str | None = None) -> dict:
        """Week-to-date and month-to-date totals.

        The week starts Monday, matching the Swift period grouping.
        """
        from datetime import datetime, timedelta

        day = today or _date.today().strftime("%Y-%m-%d")
        anchor = datetime.strptime(day, "%Y-%m-%d").date()
        week_start = anchor - timedelta(days=anchor.weekday())
        month_prefix = day[:7]

        week = {"tokens": 0, "cost": 0.0}
        month = {"tokens": 0, "cost": 0.0}
        for e in self.scan_entries():
            cost = pricing.cost(e.model, e.input, e.output, e.cache_write, e.cache_read)
            if e.local_day[:7] == month_prefix:
                month["tokens"] += e.total
                month["cost"] += cost
            try:
                entry_day = datetime.strptime(e.local_day, "%Y-%m-%d").date()
            except ValueError:
                continue
            if week_start <= entry_day <= anchor:
                week["tokens"] += e.total
                week["cost"] += cost
        return {"week": week, "month": month}

    def fetch_enrichment(self) -> ProviderEnrichment:
        # Blocks/burn-rate remain unported; the *_ok flags stay false so callers
        # keep their previous values rather than zeroing.
        return ProviderEnrichment()
