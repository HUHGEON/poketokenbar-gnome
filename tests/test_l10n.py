import pytest

from poketokenbar import l10n


def test_english_is_the_default():
    assert l10n.t("home") == "Home"


@pytest.mark.parametrize("lang,expected", [("ko", "홈"), ("ja", "ホーム"), ("es", "Inicio")])
def test_other_languages_resolve(lang, expected):
    assert l10n.t("home", lang) == expected


def test_unknown_language_falls_back_to_english():
    assert l10n.t("home", "de") == "Home"


def test_unknown_key_returns_the_key_not_blank():
    # A blank label hides the bug; the key makes it visible.
    assert l10n.t("no_such_key", "ko") == "no_such_key"


def test_catalogue_covers_every_string():
    assert set(l10n.catalogue("ja")) == set(l10n.STRINGS)


def test_every_string_has_all_four_languages():
    for key, row in l10n.STRINGS.items():
        assert len(row) == 4, key
        assert all(isinstance(v, str) and v for v in row), key


def test_status_messages_exist_for_each_display_state():
    from poketokenbar.companion import STATUS_MESSAGE

    for kind in STATUS_MESSAGE:
        assert f"status_{kind.lower()}" in l10n.STRINGS or kind == "levelUp"
