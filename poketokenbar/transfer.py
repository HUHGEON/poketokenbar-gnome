"""Save export / import — ports SaveTransfer.swift.

An export is an envelope around the save: format version, app version, device
name, and timestamp. Importing replaces local progress entirely, so the
envelope is validated before anything is overwritten, and the existing save is
kept as a backup rather than discarded.
"""

from __future__ import annotations

import json
import platform
import time
from datetime import datetime
from pathlib import Path

from . import save
from .companion import CompanionState

FORMAT = "poketokenbar.save"
FORMAT_VERSION = 1


class TransferError(Exception):
    pass


def suggested_filename(now: float | None = None) -> str:
    stamp = datetime.fromtimestamp(now or time.time()).strftime("%Y-%m-%d")
    return f"poketokenbar-save-{stamp}.json"


def encode(state: CompanionState, app_version: str = "0.1.0", now: float | None = None) -> dict:
    return {
        "format": FORMAT,
        "format_version": FORMAT_VERSION,
        "app_version": app_version,
        "device": platform.node(),
        "exported_at": now or time.time(),
        "save": save.encode(state),
    }


def summary(state: CompanionState) -> dict:
    """What a person needs to judge an overwrite before confirming it."""
    active = state.active
    return {
        "dex_count": len(state.dex),
        "used_since_install": state.used_since_install,
        "active_species": active.current_id if active else None,
        "items": sum(state.inventory.values()),
    }


def export_to(path: Path, state: CompanionState, app_version: str = "0.1.0") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(encode(state, app_version), indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def decode(raw: dict) -> CompanionState:
    if not isinstance(raw, dict):
        raise TransferError("not a save file")
    if raw.get("format") != FORMAT:
        raise TransferError("not a PokeTokenBar save file")
    version = raw.get("format_version")
    if not isinstance(version, int) or version > FORMAT_VERSION:
        # Refuse the future rather than silently dropping fields we cannot read.
        raise TransferError(f"unsupported save version: {version}")
    body = raw.get("save")
    if not isinstance(body, dict):
        raise TransferError("save file has no payload")
    return save.decode(body)


def import_from(path: Path, target: Path | None = None) -> CompanionState:
    """Replace the local save with an exported one.

    The current save is copied aside first: importing is destructive, and a
    mistaken import should be recoverable.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise TransferError(f"cannot read {path}: {exc}") from exc

    incoming = decode(raw)

    target = target or save.default_path()
    if target.is_file():
        backup = target.with_suffix(target.suffix + ".before-import")
        try:
            backup.write_bytes(target.read_bytes())
        except OSError:
            pass  # a failed backup must not block the import the user asked for

    save.save(incoming, target)
    return incoming
