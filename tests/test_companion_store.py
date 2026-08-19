import random

from poketokenbar import balance
from poketokenbar.balance import Rarity
from poketokenbar.companion import EvoLine
from poketokenbar.companion_store import CompanionStore


class FakeAPI:
    def __init__(self, forms=3, rarity=Rarity.COMMON, broken=False):
        self.forms, self.rarity, self.broken = forms, rarity, broken
        self.rolls = 0

    def roll_base_species(self, rng, tier=None):
        if self.broken:
            from poketokenbar.pokeapi import PokeAPIError

            raise PokeAPIError("offline")
        self.rolls += 1
        return 1

    def line(self, base_id):
        if self.broken:
            from poketokenbar.pokeapi import PokeAPIError

            raise PokeAPIError("offline")
        return EvoLine(base_id=1, path_ids=list(range(1, self.forms + 1)), rarity=self.rarity)


def _store(tmp_path, api=None, seeded=True):
    s = CompanionStore(
        save_path=tmp_path / "companion.json", api=api or FakeAPI(), rng=random.Random(3)
    )
    if seeded:
        # First update only seeds the baseline; start from a known point.
        s.update({}, today="2026-08-18")
    return s


def test_first_update_seeds_the_baseline_without_granting(tmp_path):
    # Installing must not retroactively credit a day's existing usage.
    s = CompanionStore(save_path=tmp_path / "c.json", api=FakeAPI())
    s.update({"claude_code": 50_000_000}, today="2026-08-18")
    assert s.state.used_since_install == 0
    assert s.state.active is None


def test_second_update_credits_only_the_delta(tmp_path):
    s = CompanionStore(save_path=tmp_path / "c.json", api=FakeAPI())
    s.update({"claude_code": 1_000}, today="2026-08-18")
    s.update({"claude_code": 1_500}, today="2026-08-18")
    assert s.state.used_since_install == 500


def test_a_provider_total_going_backwards_does_not_credit_negative(tmp_path):
    s = _store(tmp_path)
    s.update({"claude_code": 1_000}, today="2026-08-18")
    s.update({"claude_code": 400}, today="2026-08-18")
    assert s.state.used_since_install == 1_000


def test_new_day_counts_the_new_days_usage_not_the_old_total(tmp_path):
    s = _store(tmp_path)
    s.update({"claude_code": 900}, today="2026-08-18")
    before = s.state.used_since_install
    # Next day the provider reports today's total from zero again. That 100 is
    # genuinely new usage, so it counts; what must NOT happen is re-crediting
    # yesterday's 900.
    s.update({"claude_code": 100}, today="2026-08-19")
    assert s.state.used_since_install == before + 100


def test_providers_are_tracked_independently(tmp_path):
    s = _store(tmp_path)
    s.update({"a": 100, "b": 100}, today="2026-08-18")
    s.update({"a": 150, "b": 100}, today="2026-08-18")
    assert s.state.used_since_install == 250


def test_enough_usage_hatches_a_companion(tmp_path):
    s = _store(tmp_path)
    s.update({"claude_code": balance.EGG_HATCH_THRESHOLD}, today="2026-08-18")
    assert s.state.active is not None
    assert s.payload()["stage"] == "mon"


def test_offline_holds_progress_in_the_egg(tmp_path):
    s = _store(tmp_path, api=FakeAPI(broken=True))
    s.update({"claude_code": balance.EGG_HATCH_THRESHOLD * 2}, today="2026-08-18")
    assert s.state.active is None
    assert s.state.egg_usage == balance.EGG_HATCH_THRESHOLD * 2
    assert s.payload()["stage"] == "egg"


def test_state_survives_a_restart(tmp_path):
    s = _store(tmp_path)
    s.update({"claude_code": balance.EGG_HATCH_THRESHOLD}, today="2026-08-18")
    species = s.state.active.current_id

    reopened = CompanionStore(save_path=tmp_path / "companion.json", api=FakeAPI())
    assert reopened.state.active is not None
    assert reopened.state.active.current_id == species


def test_egg_payload_reports_progress(tmp_path):
    s = _store(tmp_path)
    s.update({"claude_code": balance.EGG_HATCH_THRESHOLD // 2}, today="2026-08-18")
    payload = s.payload()
    assert payload["stage"] == "egg"
    assert 0.4 < payload["egg_progress"] < 0.6


def test_mon_payload_reports_stage_progress(tmp_path):
    s = _store(tmp_path)
    s.update({"claude_code": balance.EGG_HATCH_THRESHOLD}, today="2026-08-18")
    payload = s.payload()
    assert payload["stage_index"] == 0
    assert payload["stage_threshold"] > 0
    assert payload["species_id"] >= 1
