"""poketokenctl — the plasmoid's only way to talk to the daemon."""

from __future__ import annotations

import sys

from . import commands, config


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: poketokenctl {set <key> <value>|refresh}", file=sys.stderr)
        return 2

    action, rest = argv[0], argv[1:]
    if action == "set":
        if len(rest) != 2:
            print("usage: poketokenctl set <key> <value>", file=sys.stderr)
            return 2
        try:
            config.set_value(config.default_path(), rest[0], rest[1])
        except (KeyError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        commands.enqueue("reload_config", {})
        return 0

    if action == "refresh":
        commands.enqueue("refresh", {})
        return 0

    print(f"unknown command: {action}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
