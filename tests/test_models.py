from datetime import datetime, timezone

from poketokenbar.models import DailyUsage, Entry, ProviderEnrichment


def test_entry_total_sums_all_four_token_kinds():
    e = Entry(
        id="msg_1|req_1",
        date=datetime(2026, 8, 18, tzinfo=timezone.utc),
        local_day="2026-08-18",
        model="claude-opus-5",
        input=2,
        output=570,
        cache_write=24_155,
        cache_read=16_203,
    )
    assert e.total == 2 + 570 + 24_155 + 16_203


def test_daily_usage_defaults_are_zero():
    d = DailyUsage(date="2026-08-18")
    assert d.total_tokens == 0
    assert d.total_cost == 0.0


def test_enrichment_flags_default_to_not_ok():
    # A failed enrichment must not be mistaken for a successful empty one,
    # otherwise a transient error zeroes the popup's block/period sections.
    p = ProviderEnrichment()
    assert p.blocks_ok is False
    assert p.periods_ok is False
