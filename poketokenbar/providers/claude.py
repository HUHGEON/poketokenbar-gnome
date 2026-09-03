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

from .base import ScanningProvider, dedup_keep_max, loads as _loads, parse_iso, to_int as _int

# Re-exported under their original names: the tests and the Codex provider
# already import them from here.
_parse_timestamp = parse_iso


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


class ClaudeProvider(ScanningProvider):
    """Claude Code local usage."""

    id = "claude_code"
    display_name = "Claude Code"
    reports_cost = True
    # Bump when parse_line changes shape, to invalidate cached blobs.
    PARSER_VERSION = 1

    def curated_roots(self) -> list[Path]:
        return project_roots(home=self._home)

    def parse_file(self, path: Path) -> list[Entry]:
        return parse_file(path)
