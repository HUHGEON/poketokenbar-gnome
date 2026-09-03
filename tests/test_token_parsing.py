"""Token-number parsing — ports the clamp cases from LocalUsageReaderTests.swift.

The Swift reader accepts any JSON number and clamps it; the first Python port
accepted `int` only, so a corrupt `1e30` silently became 0 instead of the
ceiling. Both directions are wrong in the same place, so both are pinned here.
"""

from poketokenbar.providers.base import MAX_PARSED_TOKEN_VALUE, to_int


def test_plain_integers_pass_through():
    assert to_int(0) == 0
    assert to_int(1234) == 1234


def test_floats_count_as_numbers():
    """A log carrying 1.0 or 1e30 is still reporting tokens, not nothing."""
    assert to_int(1500.0) == 1500
    assert to_int(1500.9) == 1500  # truncates, matching Int(d)


def test_absurd_values_clamp_rather_than_zero_or_explode():
    """`1e30` is corrupt. It must land on the ceiling, not on 0 and not on 1e30.

    Zeroing hides a real day's usage; passing it through hands the companion a
    lifetime spend no threshold can ever be reached past.
    """
    assert to_int(1e30) == MAX_PARSED_TOKEN_VALUE
    assert to_int(MAX_PARSED_TOKEN_VALUE + 1) == MAX_PARSED_TOKEN_VALUE


def test_clamped_values_stay_addable():
    """Gemini sums two parsed fields immediately (`output + thoughts`).

    The ceiling has to leave room for that, which is why it is not sys.maxsize.
    """
    assert MAX_PARSED_TOKEN_VALUE * 2 < 2**62


def test_negatives_and_junk_fold_to_zero():
    assert to_int(-5) == 0
    assert to_int(None) == 0
    assert to_int("nope") == 0
    assert to_int({}) == 0
    assert to_int(float("nan")) == 0
    assert to_int(float("inf")) == 0


def test_booleans_are_not_token_counts():
    """`isinstance(True, int)` is True in Python — a bool here is a schema error."""
    assert to_int(True) == 0
    assert to_int(False) == 0
