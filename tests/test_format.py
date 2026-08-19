import pytest

from poketokenbar import format as fmt


@pytest.mark.parametrize(
    "value,expected",
    [
        (987, "987"),
        (0, "0"),
        (999, "999"),
        (1_000, "1K"),
        (12_345, "12.3K"),
        (190_612_940, "190.6M"),
        (1_240_000_000, "1.24B"),
        (-12_345, "-12.3K"),
    ],
)
def test_compact_matches_swift_formatter(value, expected):
    assert fmt.compact(value) == expected


def test_compact_trims_trailing_zeros():
    # 1_000_000 -> "1M", not "1.0M"
    assert fmt.compact(1_000_000) == "1M"


@pytest.mark.parametrize(
    "usd,expected",
    [(9.5, "$9.5"), (99.94, "$99.9"), (311.0, "$311"), (1_200.0, "$1200"), (12_000.0, "$12.0K")],
)
def test_cost_compact_matches_swift_thresholds(usd, expected):
    assert fmt.cost_compact(usd) == expected


def test_percent_drops_decimal_when_whole():
    assert fmt.percent(80.0) == "80%"
    assert fmt.percent(80.5) == "80.5%"
