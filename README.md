# PokeTokenBar — Linux / KDE Plasma port

A personal Linux build of PokeTokenBar for the KDE Plasma 6 panel: a Python
daemon reads your local AI-CLI logs and a QML plasmoid renders them.

**The macOS app is unaffected.** Nothing under `Sources/`, `Tests/`,
`Package.swift`, or `scripts/` is touched by anything in this directory.

## Status

Plan 1 of 6 is complete — the daemon, the Claude Code parser, and a working
panel with a popup. Still to come, in order:

| Plan | Scope |
|---|---|
| 2 | Limits (5-hour / weekly), burn rate, cost pricing, notifications |
| 3 | Companion engine, PokéAPI, sprites — the Pokémon appears in the panel |
| 4 | The remaining nine providers (Codex, Gemini, Cursor, …) |
| 5 | Shop, Bag, Pokédex tabs |
| 6 | Floating desktop pet, localisation, settings polish |

Until Plan 2 lands, cost always reads `$0.00` — `ModelPricing` is not ported
yet. Leave "Show cost" off.

Design and plans live in `docs/superpowers/` (untracked by repo policy —
`docs/*` is gitignored except `docs/reference/`).

## Install

```bash
./linux/install.sh
```

That installs, all under `$HOME`:

- the Python package → `~/.local/share/poketokenbar/app`
- a venv → `~/.local/share/poketokenbar/venv`
- `poketokenctl` → `~/.local/bin/`
- the plasmoid → `~/.local/share/plasma/plasmoids/org.kde.plasma.poketokenbar`
- a systemd user unit → `~/.config/systemd/user/poketokend.service` (enabled
  and started, so it comes back on login)

Then add the widget: right-click the panel → **Add Widgets** → search
**PokeTokenBar**. If it does not appear, restart the shell with
`systemctl --user restart plasma-plasmashell`.

## Where things live

| Path | Contents |
|---|---|
| `~/.local/state/poketokenbar/state.json` | what the panel renders; written atomically |
| `~/.config/poketokenbar/config.json` | settings, shared by both halves |
| `~/.cache/poketokenbar/scan.db` | incremental scan cache |
| `~/.local/share/poketokenbar/` | app, venv, and (from Plan 3) the save |
| `$XDG_RUNTIME_DIR/poketokenbar/commands/` | queued UI → daemon commands |

## Usage

```bash
poketokenctl set show_tokens_in_menu false   # change a setting
poketokenctl set refresh_interval 60
poketokenctl refresh                         # force a poll now
```

Settings are validated by the daemon, so an unknown key or a bad value exits
non-zero instead of writing garbage.

## Development

```bash
cd linux
python3 -m venv .venv && ./.venv/bin/pip install pytest
./.venv/bin/pytest -q
```

The Swift sources are the specification for every parser and balance
constant — port behaviour from them rather than re-deriving it, and check
`docs/reference/defect-log.md` before writing a subsystem so the port does not
re-introduce a bug class the macOS app already paid for.

Reinstall after changes with `./linux/install.sh` (it rsyncs and restarts the
service).

## Troubleshooting

```bash
systemctl --user status poketokend
journalctl --user -u poketokend -n 50 --no-pager
```

If the panel shows `…` forever, the daemon is not writing `state.json` — read
the journal before changing anything.

A cold first scan parses every log file; on a 559 MB corpus that took ~9 s,
after which warm scans are ~0.1 s. If it ever takes minutes, the incremental
cache is being invalidated — check that `PARSER_VERSION` is not changing and
that file mtimes are stable.
