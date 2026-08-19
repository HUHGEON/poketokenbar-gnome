"""Ties the companion engine to live usage — ports CompanionStore.swift.

Providers report cumulative totals for *today*, not deltas. This converts them
into deltas by remembering what has already been credited per provider, which
is why the baseline is tracked per provider id rather than in aggregate: a
single total cannot be decomposed when one provider resets and another does not.
"""

from __future__ import annotations

import random
from datetime import date as _date
from pathlib import Path

from . import balance, companion, l10n, pokeapi, save, shop, sprites
from .companion import CompanionState
from .format import compact as _compact


def _duration(seconds: float | None) -> str:
    if not seconds or seconds <= 0:
        return ""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    if days > 0:
        return f"{days} days, {hours} hr"
    minutes = int((seconds % 3600) // 60)
    return f"{hours} hr, {minutes} min" if hours else f"{minutes} min"


class CompanionStore:
    def __init__(
        self,
        save_path: Path | None = None,
        api: pokeapi.PokeAPI | None = None,
        sprite_store: sprites.SpriteStore | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self.save_path = save_path
        self.state: CompanionState = save.load(save_path)
        self.api = api
        self.sprites = sprite_store
        self.rng = rng or random.Random()
        # Held for one poll so the popup can show a celebration banner; the
        # notification fires immediately but the banner needs a render pass.
        self.celebration: dict | None = None
        self.last_events: companion.GrowthEvents | None = None

    # --- usage -------------------------------------------------------------

    def update(self, totals_by_provider: dict[str, int], today: str | None = None) -> None:
        """Credit the growth of today's usage since the last update."""
        today = today or _date.today().strftime("%Y-%m-%d")

        # The None sentinel must be checked BEFORE the day rollover, or a
        # fresh save (last_date == "") takes the rollover branch, loses the
        # sentinel, and credits the whole existing day retroactively.
        if self.state.claimed_today_tokens_by_provider is None:
            # First run: seed the baseline, granting nothing for past usage.
            self.state.claimed_today_tokens_by_provider = dict(totals_by_provider)
            self.state.install_baseline_set = True
            self.state.last_date = today
            self._persist()
            return

        # A new day restarts every provider's "today" total at zero, so the
        # old baselines would make every delta negative. Clearing them lets the
        # new day's usage count from zero, which is real usage, not a re-count.
        if self.state.last_date != today:
            self.state.last_date = today
            self.state.claimed_today_tokens_by_provider = {}

        claimed = self.state.claimed_today_tokens_by_provider

        delta = 0
        for provider_id, total in totals_by_provider.items():
            previous = claimed.get(provider_id, 0)
            # A total going backwards (log rotation, cache rebuild) must not
            # produce a negative delta.
            if total > previous:
                delta += total - previous
            claimed[provider_id] = total

        if delta <= 0:
            self._persist()
            return

        line = self._line_for_egg() if self.state.active is None else None
        self.last_events = companion.apply_usage(
            self.state, delta, line_for_egg=line, rng=self.rng
        )
        self._note_celebration(self.last_events)
        self._persist()

    def _note_celebration(self, events) -> None:
        if events is None:
            return
        mon = self.state.active
        name = self.species_name(mon.current_id, self.state.language) if mon else ""
        if events.ditto_revealed:
            self.celebration = {
                "kind": "ditto",
                "title": "Huh? It's Ditto!",
                "detail": "Your companion was a Ditto all along.",
            }
        elif events.graduated is not None:
            self.celebration = {
                "kind": "graduated",
                "title": "Graduated!",
                "detail": f"{name or 'It'} joined your Pokedex.",
            }
        elif events.evolved_to is not None:
            self.celebration = {
                "kind": "evolved",
                "title": "Evolved!",
                "detail": f"It became {name}." if name else "It evolved.",
            }
        elif events.hatched is not None:
            shiny = mon is not None and mon.is_shiny
            self.celebration = {
                "kind": "shiny" if shiny else "hatched",
                "title": "A shiny hatched!" if shiny else "It hatched!",
                "detail": (
                    f"A shiny {name} — 1 in {balance.SHINY_DENOMINATOR}!"
                    if shiny
                    else f"{name} came out of the egg."
                ),
            }

    def _line_for_egg(self):
        """Species data for a hatch, or None when offline."""
        if self.api is None:
            return None
        try:
            species_id = self.state.pending_hatch_id
            if species_id is None:
                species_id = self.api.roll_base_species(self.rng, self.state.egg_tier)
            return self.api.line(species_id)
        except pokeapi.PokeAPIError:
            return None  # hold progress in the egg; hatch on a later poll

    # --- presentation ------------------------------------------------------

    def species_name(self, species_id: int, language: str = "en") -> str:
        """Localised species name, or "" when unknown.

        Reads the on-disk species cache the line lookup already populated, so
        this costs nothing after the hatch and stays silent when offline.
        """
        if self.api is None:
            return ""
        try:
            entry = self.api.species(species_id)
        except Exception:
            return ""
        names = {
            n["language"]["name"]: n["name"]
            for n in entry.get("names", [])
            if n.get("language", {}).get("name")
        }
        # ja-Hrkt is the kana form PokeAPI uses for Japanese.
        for code in ({"ja": ["ja-Hrkt", "ja"]}.get(language, [language])):
            if names.get(code):
                return names[code]
        return names.get("en", "")

    def sprite_path(self) -> str:
        mon = self.state.active
        if mon is None or self.sprites is None:
            return ""
        path = self.sprites.path(mon.current_id, animated=True, shiny=mon.is_shiny)
        return str(path) if path else ""

    def payload(self, today_tokens: int = 0, limit_warning: bool = False) -> dict:
        """Companion section of state.json."""
        kind = companion.display_state(self.state, today_tokens, limit_warning)
        mon = self.state.active
        if mon is None:
            progress = min(1.0, self.state.egg_usage / balance.EGG_HATCH_THRESHOLD)
            return {
                "stage": "egg",
                "label": f"\N{EGG}{round(progress * 100)}%",
                "egg_usage": self.state.egg_usage,
                "egg_progress": round(progress, 4),
                "egg_tier": str(self.state.egg_tier) if self.state.egg_tier else None,
                "sprite_path": "",
                "dex_count": len(self.state.dex),
                "spendable_tokens": self.state.spendable_tokens,
                "spendable_text": _compact(self.state.spendable_tokens),
                "display_state": kind,
                "status_message": l10n.t(f"status_{kind.lower()}", self.state.language),
            }

        threshold = balance.phase_threshold(mon.rarity, mon.total_forms, mon.stage_index)
        # Remaining to the NEXT step: an evolution mid-line, graduation at the end.
        remaining = max(0, threshold - mon.used_at_stage)
        evo_line = []
        if self.sprites is not None:
            for index, species_id in enumerate(mon.path_ids):
                path = self.sprites.path(species_id, animated=False, shiny=mon.is_shiny)
                evo_line.append(
                    {
                        "species_id": species_id,
                        "name": self.species_name(species_id, self.state.language),
                        "sprite_path": str(path) if path else "",
                        "current": index == mon.stage_index,
                        "reached": index <= mon.stage_index,
                    }
                )
        return {
            "stage": "mon",
            "label": "",
            "species_id": mon.current_id,
            "name": self.species_name(mon.current_id, self.state.language),
            "is_final_form": mon.is_final_form,
            "remaining_tokens": remaining,
            "remaining_text": _compact(remaining),
            "goal": "graduation" if mon.is_final_form else "next evolution",
            "evo_line": evo_line,
            "is_shiny": mon.is_shiny,
            "nature": mon.nature,
            "rarity": str(mon.rarity),
            "stage_index": mon.stage_index,
            "total_forms": mon.total_forms,
            "used_at_stage": mon.used_at_stage,
            "stage_threshold": threshold,
            "stage_progress": round(min(1.0, mon.used_at_stage / threshold), 4)
            if threshold
            else 0.0,
            "sprite_path": self.sprite_path(),
            "dex_count": len(self.state.dex),
            "spendable_tokens": self.state.spendable_tokens,
            "spendable_text": _compact(self.state.spendable_tokens),
            "display_state": kind,
            "status_message": l10n.t(f"status_{kind.lower()}", self.state.language),
        }

    # --- economy -----------------------------------------------------------

    def grant_candy(self, windows: dict[str, float]) -> int:
        granted = shop.grant_candy(self.state, windows)
        self._persist()
        return granted

    def buy(self, key: str) -> str:
        message = shop.buy(self.state, key)
        self._persist()
        return message

    def use_item(self, key: str) -> str:
        message = shop.use_item(self.state, key, rng=self.rng)
        self._persist()
        return message

    def _item_sprite(self, key: str) -> str:
        name = balance.ITEM_SPRITE.get(key)
        if not name or self.sprites is None:
            return ""
        path = self.sprites.item_path(name)
        return str(path) if path else ""

    def shop_payload(self) -> list[dict]:
        spendable = self.state.spendable_tokens
        out = []
        for e in shop.entries(self.state):
            if e.kind == "item":
                sprite = self._item_sprite(e.key)
                description = balance.ITEM_DESCRIPTION.get(e.key, "")
                badge = ""
            else:
                sprite = self._item_sprite("egg")
                tier = e.key.split(":")[1] if ":" in e.key else None
                description = balance.EGG_DESCRIPTION.get(tier, "")
                badge = (tier or "").upper()
            out.append(
                {
                    "key": e.key,
                    "kind": e.kind,
                    "price": e.price,
                    "price_text": _compact(e.price),
                    "label": e.label,
                    "description": description,
                    "badge": badge,
                    "sprite_path": sprite,
                    "emoji": {"rareCandy": "\N{CANDY}", "mint": "\N{HERB}",
                              "shinyCharm": "\N{SPARKLES}"}.get(e.key, "\N{EGG}"),
                    "owned": e.owned,
                    "owned_count": self.state.inventory.get(e.key, 0),
                    "affordable": spendable >= e.price and not e.owned,
                }
            )
        return out

    def bag_payload(self) -> list[dict]:
        emoji = {"rareCandy": "\N{CANDY}", "mint": "\N{HERB}", "shinyCharm": "\N{SPARKLES}"}
        return [
            {
                "key": key,
                "label": balance.ITEM_LABEL.get(key, key),
                "description": balance.ITEM_DESCRIPTION.get(key, ""),
                "effect": balance.ITEM_EFFECT.get(key, ""),
                "sprite_path": self._item_sprite(key),
                "emoji": emoji.get(key, "?"),
                "count": count,
                # Passive items are held, not consumed.
                "usable": key in ("rareCandy", "mint") and self.state.active is not None,
                "passive": key == "shinyCharm",
            }
            for key, count in sorted(self.state.inventory.items())
            if count > 0
        ]

    def dex_payload(self) -> list[dict]:
        """Species-level collection — ports dexSpecies.

        Includes every species in a graduated chain, plus the CURRENT
        companion's reached forms only (path_ids up to stage_index). The
        planned path is never used: it contains stages not yet evolved into,
        which would list species that have never been owned.

        A species backed only by the current companion is flagged is_raising —
        buying an egg discards that companion and the entry disappears, so it
        is not yet permanent.
        """
        acc: dict[int, dict] = {}

        for entry in self.state.dex:
            for species_id in entry.chain_order:
                slot = acc.setdefault(
                    species_id,
                    {"rarity": str(entry.rarity), "is_shiny": False, "graduated": False},
                )
                if entry.is_shiny:
                    slot["is_shiny"] = True
                slot["graduated"] = True

        mon = self.state.active
        if mon is not None:
            for species_id in mon.path_ids[: mon.stage_index + 1]:
                slot = acc.setdefault(
                    species_id,
                    {"rarity": str(mon.rarity), "is_shiny": False, "graduated": False},
                )
                if mon.is_shiny:
                    slot["is_shiny"] = True

        out = []
        for species_id in sorted(acc):
            slot = acc[species_id]
            sprite = ""
            if self.sprites is not None:
                path = self.sprites.path(
                    species_id, animated=False, shiny=slot["is_shiny"]
                )
                sprite = str(path) if path else ""
            out.append(
                {
                    "final_id": species_id,
                    "species_id": species_id,
                    "name": self.species_name(species_id, self.state.language),
                    "rarity": slot["rarity"],
                    "is_shiny": slot["is_shiny"],
                    "is_raising": not slot["graduated"],
                    "sprite_path": sprite,
                }
            )
        return out

    def _chain(self, species_ids, shiny: bool) -> list[dict]:
        out = []
        for species_id in species_ids:
            sprite = ""
            if self.sprites is not None:
                path = self.sprites.path(species_id, animated=False, shiny=shiny)
                sprite = str(path) if path else ""
            out.append(
                {
                    "species_id": species_id,
                    "name": self.species_name(species_id, self.state.language),
                    "sprite_path": sprite,
                }
            )
        return out

    def catch_log_payload(self) -> list[dict]:
        """Every catch, newest first, with its full evolution chain.

        Entries predating caught_at sort last rather than pretending to be
        ancient; ordering among them is unspecified.
        """
        out = [
            {
                "rarity": str(e.rarity),
                "nature": e.nature,
                "is_shiny": e.is_shiny,
                "chain": self._chain(e.chain_order, e.is_shiny),
                "caught_at": e.caught_at,
                "raised_text": _duration(e.raised_seconds),
                "raising": False,
            }
            for e in self.state.dex
        ]
        out.sort(key=lambda d: d["caught_at"] or 0, reverse=True)

        # The companion still being raised leads the log, as in the macOS app.
        mon = self.state.active
        if mon is not None:
            out.insert(
                0,
                {
                    "rarity": str(mon.rarity),
                    "nature": mon.nature,
                    "is_shiny": mon.is_shiny,
                    "chain": self._chain(mon.path_ids[: mon.stage_index + 1], mon.is_shiny),
                    "caught_at": mon.hatched_at,
                    "raised_text": "",
                    "raising": True,
                },
            )
        return out

    def rarity_counts(self) -> dict:
        """Species counts for the Pokedex filters.

        The catch log counts individuals instead — 14 catches can be 28
        species — so the two tabs cannot share one tally.
        """
        counts = {"legendary": 0, "rare": 0, "uncommon": 0, "common": 0}
        for row in self.dex_payload():
            key = row["rarity"]
            if key in counts:
                counts[key] += 1
        return counts

    def catch_rarity_counts(self) -> dict:
        """Individual counts for the catch log, including the one being raised."""
        counts = {"legendary": 0, "rare": 0, "uncommon": 0, "common": 0}
        for entry in self.state.dex:
            key = str(entry.rarity)
            if key in counts:
                counts[key] += 1
        if self.state.active is not None:
            key = str(self.state.active.rarity)
            if key in counts:
                counts[key] += 1
        return counts

    def _persist(self) -> None:
        save.save(self.state, self.save_path)
