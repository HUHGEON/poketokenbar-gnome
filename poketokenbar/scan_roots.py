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

    Walked through `Path.parts` rather than by splitting on "/". An earlier
    version tested for an absolute path with `startswith("/")` and split on the
    same character, which rejected every Windows path outright — the whole
    setting silently did nothing there, and a real Windows runner is what caught
    it. `Path` knows both separators and both shapes of root.
    """
    out: list[Path] = []
    for part in _SPLIT.split(raw or ""):
        pattern = part.strip()
        if not pattern:
            continue
        candidate = Path(os.path.expanduser(pattern))
        # Relative patterns are refused rather than resolved against whatever
        # directory the daemon happens to have been started in.
        if not candidate.is_absolute():
            continue

        segments = candidate.parts
        bases = [Path(segments[0])]  # "/" on POSIX, "C:\\" on Windows
        for segment in segments[1:]:
            if _GLOB.search(segment):
                matched: list[Path] = []
                for base in bases:
                    try:
                        names = sorted(entry.name for entry in base.iterdir())
                    except OSError:
                        continue
                    # `fnmatch`, not `fnmatchcase`: it normalises case the way
                    # the platform does, which is what a user typing a pattern
                    # into a Windows path expects. On POSIX the two are the same.
                    matched.extend(
                        base / name for name in names if fnmatch.fnmatch(name, segment)
                    )
                bases = matched
            else:
                bases = [base / segment for base in bases]
        out.extend(base for base in bases if base.is_dir())
    return out


def _normalized(path: Path) -> str:
    """Symlinks resolved, case folded, and separators made uniform.

    `~/.config/claude` being a link to `~/.claude` is a common XDG setup, and
    comparing the literal paths would scan that tree twice.

    The separator matters as much as the case. Every nesting test below is a
    string prefix check, and they were written against "/" — on Windows, where
    a resolved path comes back with backslashes, that made both of them answer
    "not nested" for everything. Nested roots would have doubled the scan, and
    worse, the guard that stops an extra folder swallowing a curated default
    would never have fired.
    """
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path
    return resolved.as_posix().lower()


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
        stem = key.rstrip("/")
        if not any(stem == k.rstrip("/") or stem.startswith(k.rstrip("/") + "/")
                   for k in kept):
            kept.append(key)
    return [root for key, root in unique if key in kept]


def _would_evict(extra: Path, protected: list[Path]) -> bool:
    """Whether this extra is an ancestor of a curated default.

    Adding `~` as an extra used to fold every curated root away, and the scan
    then never descended into the dotted directories underneath, so the usage
    silently read as zero. An extra that swallows a default is dropped instead.
    """
    key = _normalized(extra).rstrip("/")
    for default in protected:
        other = _normalized(default).rstrip("/")
        # A filesystem root swallows everything. Written as "is there anything
        # left" rather than a literal "/", because a Windows root is "c:".
        if not key:
            if other:
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
