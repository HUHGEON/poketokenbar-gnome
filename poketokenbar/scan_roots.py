"""Extra scan folders — ports CustomScanRoots.swift.

One list per provider, so a folder added for Gemini is never handed to Claude's
parser. Extras only *add* to a provider's curated defaults; they never replace
them.

Upstream keeps a second registry mapping provider id to curated roots, and its
own docs warn that forgetting an entry there silently reports zero matches. Here
the provider already knows its own roots, so that registry does not exist —
`ScanningProvider.curated_roots()` is the single source both the scan and the
settings count read.
"""

from __future__ import annotations

import fnmatch
import os
import re
from pathlib import Path

_SPLIT = re.compile(r"[,\n\r]")
_GLOB = re.compile(r"[*?\[]")


def expand(raw: str) -> list[Path]:
    """Comma/newline separated patterns into existing directories.

    Tilde is expanded and each path segment may glob. Entries point at the log
    root itself, with no suffix appended. A pattern matching nothing is not an
    error: it can legitimately be registered before the tool that fills it runs.
    """
    out: list[Path] = []
    for part in _SPLIT.split(raw or ""):
        pattern = part.strip()
        if not pattern:
            continue
        absolute = os.path.expanduser(pattern)
        # Relative patterns are refused rather than resolved against whatever
        # directory the daemon happens to have been started in.
        if not absolute.startswith("/"):
            continue

        bases = [""]
        for segment in absolute.split("/"):
            if not segment:
                continue
            if _GLOB.search(segment):
                matched: list[str] = []
                for base in bases:
                    try:
                        names = sorted(os.listdir(base or "/"))
                    except OSError:
                        continue
                    matched.extend(
                        f"{base}/{name}"
                        for name in names
                        if fnmatch.fnmatchcase(name, segment)
                    )
                bases = matched
            else:
                bases = [f"{base}/{segment}" for base in bases]
        if bases == [""]:
            bases = ["/"]
        out.extend(Path(p) for p in bases if os.path.isdir(p))
    return out


def _normalized(path: Path) -> str:
    """Symlinks resolved and case folded, for comparing two roots.

    `~/.config/claude` being a link to `~/.claude` is a common XDG setup, and
    comparing the literal paths would scan that tree twice.
    """
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    return str(resolved).lower()


def fold(roots: list[Path]) -> list[Path]:
    """Drop duplicate and nested roots, keeping the original priority order.

    Overlapping roots do not corrupt the totals — the global dedup fixes those —
    but they double the scan cost for nothing.
    """
    seen: set[str] = set()
    unique: list[tuple[str, Path]] = []
    for root in roots:
        key = _normalized(root)
        if key not in seen:
            seen.add(key)
            unique.append((key, root))

    kept: list[str] = []
    # Shortest first, so a parent settles before its children are considered.
    for key, _root in sorted(unique, key=lambda pair: len(pair[0])):
        if not any(key == k or key.startswith(k + "/") for k in kept):
            kept.append(key)
    return [root for key, root in unique if key in kept]


def _would_evict(extra: Path, protected: list[Path]) -> bool:
    """Whether this extra is an ancestor of a curated default.

    Adding `~` as an extra used to fold every curated root away, and the scan
    then never descended into the dotted directories underneath, so the usage
    silently read as zero. An extra that swallows a default is dropped instead.
    """
    key = _normalized(extra)
    for default in protected:
        other = _normalized(default)
        if key == "/":
            if other != key:
                return True
        elif other != key and other.startswith(key + "/"):
            return True
    return False


def union(defaults: list[Path], extra_raw: str | None) -> list[Path]:
    """Curated defaults, plus any extra that does not swallow one of them."""
    protected = fold(defaults)
    if not extra_raw or not extra_raw.strip():
        return protected
    added = [e for e in expand(extra_raw) if not _would_evict(e, protected)]
    return fold(protected + added)


def surviving_extra_count(defaults: list[Path], extra_raw: str) -> int:
    """How many extras actually made it — the number settings shows.

    Counting the raw patterns instead would tell someone their folder was
    accepted when it had been dropped for swallowing a default.
    """
    protected = {_normalized(p) for p in fold(defaults)}
    return sum(
        1 for root in union(defaults, extra_raw) if _normalized(root) not in protected
    )
