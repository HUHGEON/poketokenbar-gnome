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

from . import balance, companion, pokeapi, save, sprites
from .companion import CompanionState


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
        self._persist()

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

    def payload(self) -> dict:
        """Companion section of state.json."""
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
            }

        threshold = balance.phase_threshold(mon.rarity, mon.total_forms, mon.stage_index)
        return {
            "stage": "mon",
            "label": "",
            "species_id": mon.current_id,
            "name": self.species_name(mon.current_id, self.state.language),
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
        }

    def _persist(self) -> None:
        save.save(self.state, self.save_path)
