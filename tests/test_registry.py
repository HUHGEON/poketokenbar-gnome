"""Registry integrity — ports the UsageStoreTests parity checks.

The extension rule is that a source is added in exactly two places: its own
module, and one REGISTRY entry. These tests are what makes that a rule rather
than a comment — the daemon builds from the registry, so anything the registry
gets wrong is wrong everywhere.
"""

import pytest

from poketokenbar import providers
from poketokenbar.providers.base import ScanningProvider


def test_every_registered_provider_has_an_identity():
    for cls in providers.REGISTRY:
        assert cls.id, f"{cls.__name__} has no id"
        assert cls.display_name, f"{cls.__name__} has no display_name"


def test_provider_ids_are_unique():
    """A duplicate id collapses two sources into one row and one cache bucket."""
    ids = providers.registered_ids()
    assert len(ids) == len(set(ids)), f"duplicate provider id in {ids}"


def test_build_returns_one_instance_per_entry():
    built = providers.build()
    assert len(built) == len(providers.REGISTRY)
    assert [p.id for p in built] == providers.registered_ids()


def test_build_shares_one_cache_with_every_provider():
    sentinel = object()
    for provider in providers.build(cache=sentinel):
        assert provider._cache is sentinel


@pytest.mark.parametrize("cls", providers.REGISTRY, ids=lambda c: c.id)
def test_scanning_providers_implement_the_subclass_contract(cls):
    """roots() and parse_file() are the only things a source must supply."""
    if not issubclass(cls, ScanningProvider):
        pytest.skip(f"{cls.__name__} is not file-scanning")
    assert cls.roots is not ScanningProvider.roots, "roots() not implemented"
    assert cls.parse_file is not ScanningProvider.parse_file, "parse_file() not implemented"


@pytest.mark.parametrize("cls", providers.REGISTRY, ids=lambda c: c.id)
def test_absent_source_is_silent_not_an_error(cls, tmp_path):
    """An empty home must read as 'this tool is not installed', never a crash.

    Most people run one or two of these tools, so the absent path is the
    common path — it is the one most likely to reach a user unexercised.
    """
    provider = cls(home=tmp_path)
    assert provider.scan_entries() == []
    assert provider.fetch_daily() is None
    periods = provider.fetch_periods()
    assert periods["week"]["tokens"] == 0
    assert periods["month"]["tokens"] == 0


@pytest.mark.parametrize("cls", providers.REGISTRY, ids=lambda c: c.id)
def test_period_totals_are_shared_not_reimplemented(cls):
    """Codex had reimplemented fetch_daily and never grew fetch_periods, so its
    week and month read zero while Claude's worked. Aggregation stays shared.
    """
    if not issubclass(cls, ScanningProvider):
        pytest.skip(f"{cls.__name__} is not file-scanning")
    assert cls.fetch_daily is ScanningProvider.fetch_daily
    assert cls.fetch_periods is ScanningProvider.fetch_periods
