"""Every path the daemon writes stays under the user's profile.

Run by CI on a real Windows runner. `platform_paths` injects the system so all
three mappings are checked from anywhere, but this is the one place the real
one is exercised — and the one thing an injected mapping cannot tell you is
whether the environment actually looks the way it was assumed to.
"""

import sys
from pathlib import Path

# Run as `python tools/x.py` from the repo root, which puts tools/ on the path
# and not the package beside it.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import sys

from poketokenbar import config, platform_paths, state


def main() -> int:
    profile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    # These hold a person's settings, their save and their cache, and every one
    # of them has to be writable without an administrator.
    owned = {
        "config": config.default_path(),
        "state": state.default_path(),
        "save": platform_paths.data_base() / "poketokenbar" / "companion.json",
        "cache": platform_paths.cache_base() / "poketokenbar",
    }
    failed = False
    for name, path in owned.items():
        inside = str(path).lower().startswith(profile.lower())
        print(f"  {name:8} {path}{'' if inside else '   <-- OUTSIDE THE PROFILE'}")
        failed = failed or not inside

    # The spool is deliberately not on that list. It is a temporary directory by
    # design — cleared on logout, which is exactly right for a queue of one-shot
    # commands — and a temporary directory is not required to sit under the
    # profile. What matters is that it can be created and written.
    spool = platform_paths.runtime_base() / "poketokenbar" / "commands"
    try:
        spool.mkdir(parents=True, exist_ok=True)
        probe = spool / ".writable"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        print(f"  spool    {spool}  (writable)")
    except OSError as error:
        print(f"  spool    {spool}   <-- NOT WRITABLE: {error}")
        failed = True

    if failed:
        print("\nnothing here should need an administrator", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
