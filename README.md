<div align="center">

# PokeTokenBar for GNOME

**Your AI coding tokens, hatched into Pokémon — in the GNOME panel.**

[![GNOME Shell](https://img.shields.io/badge/GNOME%20Shell-45%2B-4a86cf?logo=gnome&logoColor=white)](https://gnome.org)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-3fb950)](LICENSE)

**An unofficial GNOME port of [PokeTokenBar](https://github.com/chattymin/PokeTokenBar) by [chattymin](https://github.com/chattymin),**
**built on the Linux daemon from [poketokenbar-plasma](https://github.com/rubensanchezrivero/poketokenbar-plasma) by [rubensanchezrivero](https://github.com/rubensanchezrivero).**

</div>

The AI coding tokens you are already burning become a growing Pokémon companion
in your GNOME panel. Spend tokens, hatch an egg, evolve it along its real
evolution line, graduate it into your Pokédex, and start again. Underneath the
companion is a precise usage tracker — today's spend and cost, and the official
5-hour and weekly limits, read straight from your local logs.

> Usage is read directly from local files (`totalTokens` = input + output +
> cache, local date). No external usage CLI, no account, no network needed for
> the numbers. Unofficial, non-commercial Pokémon fan project — see
> [License & disclaimer](#license--disclaimer).

## Status

Feature-complete and under CI, but **not yet run on a real GNOME desktop.**

| | |
|---|---|
| Usage daemon (12 providers) | ✅ done |
| GNOME Shell extension | ✅ written |
| Test suite | ✅ 601 tests, green on CI |
| Install verified from a clean checkout | ✅ in CI |
| Verified on a real GNOME desktop | ❌ **not yet** |

That last row is the honest one. Every field the extension reads is compared
mechanically against a real daemon payload, and its JavaScript is parsed on
every push, so a wrong name or a stray character cannot reach you. What no
check here can tell you is whether an actor renders where it should. If you run
GNOME, that is exactly the report worth opening an issue for.

## Supported tools

All twelve of the upstream sources are read:

| Tool | Read from |
|---|---|
| **Claude Code** | `~/.claude/projects/**.jsonl` |
| **Codex** | `~/.codex/sessions/**.jsonl` |
| **Gemini CLI** | `~/.gemini/tmp/**` |
| **Antigravity** | `~/.gemini/antigravity*/conversations/*.db` |
| **OpenCode** | `~/.local/share/opencode` |
| **Hermes Agent** | `~/.hermes/state.db` |
| **Cursor** | `~/.config/Cursor/User/globalStorage/state.vscdb` |
| **Grok CLI** | `~/.grok/sessions/**/updates.jsonl` |
| **Copilot CLI** | `~/.copilot/session-store.db` |
| **Kiro CLI** | `~/.local/share/kiro-cli`, `~/.kiro/sessions` |
| **Pi Agent** | `~/.pi/agent/sessions` |
| **omp** (oh-my-pi) | `~/.omp/agent/sessions` |

Official 5-hour and weekly limits are read for Claude accounts.

Ten of the twelve read a dotfile path that is identical on macOS and Linux. Two
do not, and their Linux locations follow the platform convention rather than an
upstream test — **Cursor** and **Kiro**'s SQLite store. If either reports no
usage on your machine, `CURSOR_DATA_DIR` and `KIRO_CLI_HOME` override the
defaults, and a report of where your files actually live is welcome.

## How it fits together

```
poketokend (Python)  ──→  ~/.local/state/poketokenbar/state.json  ──→  GNOME Shell extension
                     ←──  $XDG_RUNTIME_DIR/poketokenbar/commands/  ←──
```

Plain files, not D-Bus. The daemon knows nothing about the UI, which is what
made a second front end possible at all — and what makes a third one easy.

## Install

Requirements: GNOME Shell 45+, Python 3.12+, `libnotify` for notifications
(optional), `python-orjson` for faster parsing (optional).

```bash
git clone https://github.com/HUHGEON/poketokenbar-gnome.git
cd poketokenbar-gnome
./install.sh
systemctl --user enable --now poketokend
```

Then enable **PokeTokenBar** in the Extensions app.

## Differences from the Plasma port

This started as a fork of the Plasma port and diverged in three ways.

**Ten more providers.** The Plasma port reads Claude Code and Codex; its author
had no data for the rest. The upstream Swift test suite turns out to carry the
schemas and sample records for most of them, so the parsers were ported
alongside their test cases and are verified without owning the tools.

**Three defects fixed in the shared core.** Codex reported zero for the week and
month, because it reimplemented the daily aggregation and never grew the period
one. Token parsing accepted `int` only, so a corrupt `1e30` became 0 and erased
a day rather than clamping. The provider registry built cacheless instances that
nothing used, while the daemon named its two providers by hand.

**Features the Plasma port left out:** per-provider extra scan folders, the
per-model breakdown of a day, French, Portuguese and German, and pinning a
caught species to the panel.

## Development

```bash
python -m pytest -q       # no network, and none of the twelve tools installed
```

The tests are the specification. Where a parser rule looks arbitrary, its test
says which upstream case pinned it and what went wrong without it.

[docs/TESTING.md](docs/TESTING.md) records exactly what is checked and what is
not — including the defects the checks have caught, so the claim that they earn
their keep is checkable rather than asserted.

## Credits

- [chattymin/PokeTokenBar](https://github.com/chattymin/PokeTokenBar) — the
  original macOS app, and the source of every parsing rule here.
- [rubensanchezrivero/poketokenbar-plasma](https://github.com/rubensanchezrivero/poketokenbar-plasma)
  — the Python daemon and the UI-agnostic file protocol this builds on.

## License & disclaimer

**MIT** — see [LICENSE](LICENSE). MIT applies to this project's own source code
only, and grants no rights over third-party trademarks, artwork, or data reached
through the app.

PokeTokenBar for GNOME is an **unofficial, non-commercial fan project**. It is
**not affiliated with, endorsed, sponsored, or approved by Nintendo, Game Freak,
Creatures Inc., or The Pokémon Company.** "Pokémon" and the related names,
characters and images are trademarks and copyrighted works of their respective
owners, and this project claims no ownership of or rights in any Pokémon
intellectual property.

- **No Pokémon assets are included in this repository or in any release.**
  Species data and sprites are fetched at **runtime** from the public
  [PokéAPI](https://pokeapi.co) and cached locally on your own machine; rights in
  the sprite images served through PokéAPI belong to their respective owners.
- This app is provided free of charge for **personal, non-commercial use only**.
- If you hold rights and have concerns about this project, please open an issue
  or contact the maintainer and it will be addressed promptly.

*Provided "as is", without warranty of any kind. This notice is not legal advice.*
