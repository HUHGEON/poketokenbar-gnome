"""Extra scan folders — ports CustomScanRootsTests.swift.

The interesting cases are the ones where an extra folder makes things *worse*:
swallowing a curated default, or duplicating it into a doubled scan.
"""

import pytest

from poketokenbar import providers, scan_roots
from poketokenbar.providers.gemini import GeminiProvider


def test_comma_and_newline_both_separate(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "c").mkdir()
    raw = f"{tmp_path/'a'}, {tmp_path/'b'}\n{tmp_path/'c'}"
    assert set(scan_roots.expand(raw)) == {tmp_path / "a", tmp_path / "b", tmp_path / "c"}


def test_missing_paths_are_not_an_error(tmp_path):
    """A pattern can legitimately be registered before the tool that fills it runs."""
    assert scan_roots.expand(str(tmp_path / "not-yet")) == []


def test_files_are_not_roots(tmp_path):
    (tmp_path / "f.txt").write_text("x", encoding="utf-8")
    assert scan_roots.expand(str(tmp_path / "f.txt")) == []


def test_glob_segments_are_expanded(tmp_path):
    for name in ("proj-a", "proj-b", "other"):
        (tmp_path / name / "logs").mkdir(parents=True)
    found = scan_roots.expand(str(tmp_path / "proj-*" / "logs"))
    assert set(found) == {tmp_path / "proj-a" / "logs", tmp_path / "proj-b" / "logs"}


def test_relative_patterns_are_refused():
    """Resolving these against the daemon's working directory would be arbitrary."""
    assert scan_roots.expand("relative/path") == []
    assert scan_roots.expand("") == []


def test_blank_entries_are_skipped(tmp_path):
    (tmp_path / "a").mkdir()
    assert scan_roots.expand(f",,  \n {tmp_path/'a'} ,\n") == [tmp_path / "a"]


# MARK: folding


def test_nested_roots_fold_into_the_ancestor(tmp_path):
    (tmp_path / "root" / "child").mkdir(parents=True)
    folded = scan_roots.fold([tmp_path / "root", tmp_path / "root" / "child"])
    assert folded == [tmp_path / "root"]


def test_duplicate_roots_collapse(tmp_path):
    (tmp_path / "root").mkdir()
    assert scan_roots.fold([tmp_path / "root", tmp_path / "root"]) == [tmp_path / "root"]


def test_symlinked_duplicate_collapses(tmp_path):
    """`~/.config/claude` linking to `~/.claude` is a common XDG setup.

    Comparing the literal paths would scan the same tree twice.
    """
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    assert len(scan_roots.fold([real, link])) == 1


def test_fold_preserves_priority_order(tmp_path):
    for name in ("first", "second"):
        (tmp_path / name).mkdir()
    assert scan_roots.fold([tmp_path / "second", tmp_path / "first"]) == [
        tmp_path / "second",
        tmp_path / "first",
    ]


# MARK: the eviction guard


def test_an_extra_that_swallows_a_default_is_dropped(tmp_path):
    """Adding `~` used to fold every curated root away.

    The scan then never descended into the dotted directories underneath, so a
    real install silently read as zero usage.
    """
    default = tmp_path / ".claude" / "projects"
    default.mkdir(parents=True)
    united = scan_roots.union([default], str(tmp_path))
    assert united == [default], "the ancestor extra must not evict the default"


def test_an_unrelated_extra_is_added(tmp_path):
    default = tmp_path / ".claude" / "projects"
    default.mkdir(parents=True)
    extra = tmp_path / "elsewhere"
    extra.mkdir()
    assert scan_roots.union([default], str(extra)) == [default, extra]


def test_extras_only_add_and_never_replace(tmp_path):
    default = tmp_path / ".claude" / "projects"
    default.mkdir(parents=True)
    extra = tmp_path / "elsewhere"
    extra.mkdir()
    assert default in scan_roots.union([default], str(extra))


def test_no_extras_leaves_the_defaults_alone(tmp_path):
    default = tmp_path / "d"
    default.mkdir()
    for empty in (None, "", "   ", "\n"):
        assert scan_roots.union([default], empty) == [default]


def test_surviving_count_reports_what_actually_made_it(tmp_path):
    """Counting the raw patterns would tell someone their folder was accepted
    when it had been dropped for swallowing a default."""
    default = tmp_path / ".claude" / "projects"
    default.mkdir(parents=True)
    good = tmp_path / "good"
    good.mkdir()

    assert scan_roots.surviving_extra_count([default], str(good)) == 1
    assert scan_roots.surviving_extra_count([default], str(tmp_path)) == 0
    assert scan_roots.surviving_extra_count([default], str(tmp_path / "absent")) == 0


# MARK: wired through the providers


def test_a_provider_scans_its_extra_folder(tmp_path):
    """The whole point: usage in a non-default location still gets counted."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "session-a.jsonl").write_text(
        '{"id":"a","timestamp":"2026-06-30T10:00:00.000Z","tokens":{"input":10}}',
        encoding="utf-8",
    )

    without = GeminiProvider(home=tmp_path)
    assert without.scan_entries() == []

    with_extra = GeminiProvider(home=tmp_path, custom_roots=lambda _id: str(elsewhere))
    assert len(with_extra.scan_entries()) == 1


def test_extras_are_per_provider_not_shared(tmp_path):
    """A folder added for Gemini must never be handed to another parser."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    def only_gemini(provider_id):
        return str(elsewhere) if provider_id == "gemini" else None

    built = {p.id: p for p in providers.build(home=tmp_path, custom_roots=only_gemini)}
    assert elsewhere in built["gemini"].roots()
    assert elsewhere not in built["claude_code"].roots()


def test_the_lookup_is_re_read_rather_than_captured(tmp_path):
    """The daemon reloads config in place; a captured value would go stale."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    current = {"value": None}

    provider = GeminiProvider(home=tmp_path, custom_roots=lambda _id: current["value"])
    assert provider.roots() == []

    current["value"] = str(elsewhere)
    assert provider.roots() == [elsewhere]


@pytest.mark.parametrize("cls", providers.REGISTRY, ids=lambda c: c.id)
def test_every_provider_honours_an_extra_folder(cls, tmp_path):
    """Registry-wide, because forgetting one is invisible from its own tests."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    provider = cls(home=tmp_path, custom_roots=lambda _id: str(elsewhere))
    assert elsewhere in provider.roots()
