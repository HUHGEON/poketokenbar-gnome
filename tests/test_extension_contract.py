"""The extension reads state.json; this checks it only reads what exists.

A GNOME Shell extension cannot be run from here, and a JavaScript typo in a
field name does not fail loudly — `state.companion.sprite_pat` is `undefined`,
which renders as a blank label rather than an error. That is the failure this
catches, and it is the one most likely to survive into a release.

The method is deliberately mechanical: the payload keys the daemon emits are
enumerated from a real `state.build`, the keys the extension reads are pulled
out of its source, and the difference is the test. It is not a substitute for
running the extension on a real desktop — nothing here proves an actor renders
— but it does mean every field name was compared rather than assumed.
"""

import re
from pathlib import Path

import pytest

from poketokenbar import limits, providers, state
from poketokenbar.balance import Rarity
from poketokenbar.companion import CompanionState, DexEntry, MonState
from poketokenbar.companion_store import CompanionStore
from poketokenbar.models import DailyUsage

class _StubSprites:
    """Enough of SpriteStore for the payload builders to fill their sprite rows."""

    def path(self, species_id, animated=True, shiny=False):
        return Path(f"/cache/{species_id}{'-sh' if shiny else ''}{'a' if animated else 's'}")

    def item_path(self, item_name):
        return Path(f"/cache/item-{item_name}.png")


EXTENSION_DIR = (
    Path(__file__).resolve().parent.parent
    / "gnome-extension"
    / "poketokenbar@huhgeon.github.io"
)


def full_payload() -> dict:
    """A payload with every optional block populated.

    Anything left empty here would let a missing key pass unnoticed, so the
    fixture is deliberately maximal rather than realistic.
    """
    store = CompanionStore(api=None, sprite_store=None)
    store.state = CompanionState(
        used_since_install=10**9,
        dex=[
            DexEntry(
                base_id=1, final_id=3, chain_order=[1, 2, 3], rarity=Rarity.COMMON,
                is_shiny=True, nature="brave", caught_at=1767312000.0,
                raised_seconds=3600,
            )
        ],
        active=MonState(
            base_id=4, path_ids=[4, 5, 6], planned_path_ids=[4, 5, 6], stage_index=1,
            rarity=Rarity.RARE, total_forms=3, nature="timid",
        ),
        inventory={"rareCandy": 2, "shinyCharm": 1},
    )
    return state.build(
        {"claude_code": DailyUsage(date="2026-09-03", total_tokens=10, models={"m": 10})},
        {"show_tokens_in_menu": True, "show_cost_in_menu": True, "show_limit_in_menu": True},
        [],
        companion_payload=store.payload(),
        shop_payload=store.shop_payload(),
        bag_payload=store.bag_payload(),
        dex_payload=store.dex_payload(),
        catch_log=store.catch_log_payload(),
        rarity_counts=store.rarity_counts(),
        catch_counts=store.catch_rarity_counts(),
        periods={"week": {"tokens": 1, "cost": 0.0}, "month": {"tokens": 2, "cost": 0.0}},
        burn={"session": {"rate_per_minute": 1.0, "minutes_to_full": 5, "eta_text": "x"}},
        limit_status=limits.LimitStatus(
            session=limits.LimitWindow(utilization=42.0, resets_at="2h", severity="warn"),
            weekly=limits.LimitWindow(utilization=10.0, resets_at="5d", severity="ok"),
            subscription_type="max",
            account={"email": "x@example.com"},
        ),
        provider_status={"anthropic": {"level": "operational"}},
        celebration={"kind": "hatch", "title": "t", "detail": "d"},
        settings={"providers": [{"id": "pi", "display_name": "Pi Agent",
                                 "custom_scan_roots": "", "matched_folders": 0}]},
    )


_LINE_COMMENT = re.compile(r"//[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
_STRING = re.compile(r"""'[^'\n]*'|"[^"\n]*"|`[^`]*`""", re.S)


def source_files() -> list[Path]:
    return sorted(EXTENSION_DIR.rglob("*.js"))


def source_code(strip_strings: bool = False) -> list[str]:
    """Each file with its comments stripped, and optionally its string literals.

    Prose mentions API names — "matching limits.level() in the daemon" — and a
    message like 'state.json is not valid JSON' reads as a property access, so
    scanning either would fail the build over a sentence. The catalogue scan
    needs the strings, hence the switch.
    """
    out = []
    for path in source_files():
        text = _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", path.read_text(encoding="utf-8")))
        out.append(_STRING.sub("''", text) if strip_strings else text)
    return out


@pytest.fixture(scope="module")
def payload():
    return full_payload()


@pytest.fixture(scope="module")
def companion_keys():
    """Both companion stages, unioned.

    The egg branch and the raising branch emit different keys — `egg_progress`
    exists only before the first hatch — so checking against one of them would
    fail every field belonging to the other.
    """
    store = CompanionStore(api=None, sprite_store=None)
    store.state = CompanionState()
    egg = set(store.payload())
    store.state = CompanionState(
        active=MonState(
            base_id=4, path_ids=[4, 5, 6], planned_path_ids=[4, 5, 6], stage_index=1,
            rarity=Rarity.RARE, total_forms=3, nature="timid",
        )
    )
    return egg | set(store.payload())


def test_the_extension_directory_is_where_the_tests_expect():
    assert EXTENSION_DIR.is_dir(), f"no extension at {EXTENSION_DIR}"
    assert (EXTENSION_DIR / "metadata.json").is_file()
    assert source_files(), "no JavaScript found"


# MARK: top-level blocks


# Every top-level key the extension may read off the parsed state.
def top_level_reads() -> set[str]:
    found: set[str] = set()
    pattern = re.compile(r"\bstate(?:\?)?\.(\w+)")
    for code in source_code(strip_strings=True):
        found.update(pattern.findall(code))
    return found


def test_every_top_level_block_the_extension_reads_exists(payload):
    # Reader methods and locals that share the name; they are not payload keys.
    not_payload = {"strings"}
    unknown = top_level_reads() - set(payload) - not_payload
    assert not unknown, f"extension reads state.{sorted(unknown)}, which the daemon never emits"


# MARK: per-block field names


BLOCK_ACCESSORS = {
    "companion": r"companion(?:\?)?\.(\w+)",
    "today": r"today(?:\?)?\.(\w+)",
    "panel": r"panel(?:\?)?\.(\w+)",
    "limits": r"limits(?:\?)?\.(\w+)",
}


def block_reads(expression: str) -> set[str]:
    pattern = re.compile(r"\b" + expression)
    found: set[str] = set()
    for code in source_code(strip_strings=True):
        found.update(pattern.findall(code))
    return found


@pytest.mark.parametrize("block,expression", sorted(BLOCK_ACCESSORS.items()))
def test_fields_read_out_of_each_block_exist(block, expression, payload, companion_keys):
    emitted = companion_keys if block == "companion" else set(payload[block])
    # Locals and helpers that happen to match the accessor shape.
    ignore = {"session", "weekly", "text", "forEach", "map", "filter", "length", "slice"}
    unknown = block_reads(expression) - emitted - ignore
    assert not unknown, (
        f"extension reads {block}.{sorted(unknown)}; "
        f"{block} actually carries {sorted(emitted)}"
    )


# MARK: list row fields, read through their own loop variable
#
# The sections deliberately name each loop variable after its block, so a field
# read off a shop row cannot be checked against a bag row's keys. Union-ing them
# would make every one of these assertions weaker than the bug it is for.


ROW_ACCESSORS = {
    "shopItem": "shop",
    "bagItem": "bag",
    "dexEntry": "dex",
    "catchRecord": "catch_log",
    "modelRow": "today_models",
    "evoStage": "evo_line",
    "chainStage": "catch_chain",
    "limitWindow": "limit_window",
}


def row_keys(name: str, payload: dict) -> set[str]:
    """The keys a row of that kind actually carries, taken from a real payload."""
    if name == "today_models":
        return set(payload["today"]["models"][0])
    if name == "limit_window":
        return set(payload["limits"]["session"])
    if name == "evo_line":
        # The evolution line is only built when a sprite store is present, so a
        # stub stands in — the field names are what is being checked, not the
        # paths.
        store = CompanionStore(api=None, sprite_store=_StubSprites())
        store.state = CompanionState(
            active=MonState(
                base_id=4, path_ids=[4, 5, 6], planned_path_ids=[4, 5, 6],
                stage_index=1, rarity=Rarity.RARE, total_forms=3,
            )
        )
        return set(store.payload()["evo_line"][0])
    if name == "catch_chain":
        return set(payload["catch_log"][0]["chain"][0])
    return set(payload[name][0])


@pytest.mark.parametrize("variable,block", sorted(ROW_ACCESSORS.items()))
def test_row_fields_read_in_the_extension_exist(variable, block, payload):
    pattern = rf"\b{variable}(?:\?)?\.(\w+)"
    unknown = block_reads(pattern) - row_keys(block, payload)
    assert not unknown, (
        f"extension reads {variable}.{sorted(unknown)}; "
        f"a {block} row carries {sorted(row_keys(block, payload))}"
    )


# MARK: list row shapes


LIST_ROW_FIELDS = {
    "shop": {"key", "kind", "price", "price_text", "label", "description", "badge",
             "sprite_path", "emoji", "owned", "owned_count", "affordable"},
    "bag": {"key", "label", "description", "effect", "sprite_path", "emoji", "count",
            "usable", "passive"},
    "dex": {"final_id", "species_id", "name", "rarity", "is_shiny", "is_raising",
            "sprite_path"},
}


@pytest.mark.parametrize("block", sorted(LIST_ROW_FIELDS))
def test_list_row_fields_match_what_the_daemon_emits(block, payload):
    """Pins the row shape itself, so a rename on either side is a failure here
    rather than a blank column in the popup."""
    rows = payload[block]
    assert rows, f"{block} fixture produced no rows"
    assert set(rows[0]) == LIST_ROW_FIELDS[block]


def test_catch_log_row_shape(payload):
    row = payload["catch_log"][0]
    assert set(row) == {
        "rarity", "nature", "is_shiny", "chain", "caught_at", "raised_text", "raising",
    }
    assert set(row["chain"][0]) == {"species_id", "name", "sprite_path"}


# MARK: strings


def test_every_string_key_the_extension_asks_for_is_in_the_catalogue(payload):
    """`text('foo')` falls back to the key itself, so a typo shows as raw text
    in the UI instead of failing."""
    # Both spellings: the reader method, and the `t` alias each section binds.
    pattern = re.compile(r"""(?:\.text|\bt)\(\s*['"]([a-z0-9_]+)['"]\s*\)""")
    asked: set[str] = set()
    for code in source_code():
        asked.update(pattern.findall(code))
    assert asked, "no catalogue lookups found; has the accessor been renamed?"
    unknown = asked - set(payload["strings"])
    assert not unknown, f"extension asks for strings {sorted(unknown)} that do not exist"


# MARK: commands


def test_every_command_the_extension_sends_is_one_the_daemon_drains():
    """A command name the daemon does not know is dropped in silence."""
    source = (EXTENSION_DIR / "lib" / "commands.js").read_text(encoding="utf-8")
    sent = set(re.findall(r"""enqueue\(\s*['"](\w+)['"]""", source))
    daemon = (
        Path(__file__).resolve().parent.parent / "poketokenbar" / "daemon.py"
    ).read_text(encoding="utf-8")
    handled = set(re.findall(r"""name\s*==\s*['"](\w+)['"]""", daemon))
    handled.update(re.findall(r"""name\s+in\s+\(([^)]*)\)""", daemon)[0].replace(
        '"', "").replace("'", "").replace(" ", "").split(",")
        if re.findall(r"""name\s+in\s+\(([^)]*)\)""", daemon) else [])
    for group in re.findall(r"""name\s+in\s+\(([^)]*)\)""", daemon):
        handled.update(part.strip().strip("\"'") for part in group.split(","))
    unknown = sent - handled
    assert not unknown, f"extension sends {sorted(unknown)}, which the daemon ignores"


def test_the_settings_block_lists_every_provider(payload):
    """The settings page has no other source for the provider list."""
    assert "providers" in payload["settings"]
    row = payload["settings"]["providers"][0]
    assert set(row) == {"id", "display_name", "custom_scan_roots", "matched_folders"}
    assert set(providers.registered_ids())  # registry is non-empty
