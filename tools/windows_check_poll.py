"""One whole poll on Windows: real files, the same parsers, a real state.json.

This is the point of the port. Every parser has unit tests that pass on any
platform; what they cannot show is that the paths resolve, that the files are
found, and that the totals survive the round trip on the filesystem people will
actually run this on.
"""

import sys
from pathlib import Path

# Run as `python tools/x.py` from the repo root, which puts tools/ on the path
# and not the package beside it.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import datetime
import json
import os
import pathlib
import sys

from poketokenbar import config, providers, state
from poketokenbar.daemon import Daemon

EXPECTED = {
    # 1000 input + 200 output + 50 cache read
    "claude_code": 1250,
    # (500 - 100) input + (80 + 20) output + 100 cached
    "gemini": 600,
}


def seed(home: pathlib.Path) -> None:
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    claude = home / ".claude" / "projects" / "p"
    claude.mkdir(parents=True, exist_ok=True)
    (claude / "s.jsonl").write_text(
        json.dumps({
            "type": "assistant", "requestId": "r1", "timestamp": stamp,
            "message": {
                "id": "m1", "model": "claude-opus-5",
                "usage": {"input_tokens": 1000, "output_tokens": 200,
                          "cache_read_input_tokens": 50},
            },
        }),
        encoding="utf-8",
    )

    gemini = home / ".gemini" / "tmp" / "h" / "chats"
    gemini.mkdir(parents=True, exist_ok=True)
    (gemini / "session-a.jsonl").write_text(
        json.dumps({
            "id": "g1", "timestamp": stamp, "model": "gemini-2.5-pro",
            "tokens": {"input": 500, "cached": 100, "output": 80, "thoughts": 20},
        }),
        encoding="utf-8",
    )


def main() -> int:
    home = pathlib.Path(os.environ.get("USERPROFILE") or os.path.expanduser("~"))
    seed(home)

    daemon = Daemon(
        state_path=state.default_path(),
        config_path=config.default_path(),
        cache=None,
        providers=[],
    )
    daemon.providers = providers.build(custom_roots=daemon.custom_scan_roots)
    state.write(daemon.state_path, daemon.poll_once())

    written = json.loads(pathlib.Path(daemon.state_path).read_text(encoding="utf-8"))
    totals = {key: row["total_tokens"] for key, row in written["providers"].items()}
    print(f"  state.json : {daemon.state_path}")
    print(f"  providers  : {totals}")
    print(f"  errors     : {written['errors']}")

    if totals != EXPECTED:
        print(f"\nexpected {EXPECTED}", file=sys.stderr)
        return 1
    if written["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
