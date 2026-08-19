from poketokenbar.providers import claude


def test_default_root_is_dot_claude_projects(tmp_path):
    (tmp_path / ".claude" / "projects").mkdir(parents=True)
    roots = claude.project_roots(home=tmp_path, env={})
    assert tmp_path / ".claude" / "projects" in roots


def test_xdg_style_root_is_included(tmp_path):
    (tmp_path / ".config" / "claude" / "projects").mkdir(parents=True)
    roots = claude.project_roots(home=tmp_path, env={})
    assert tmp_path / ".config" / "claude" / "projects" in roots


def test_claude_config_dir_env_is_honoured(tmp_path):
    custom = tmp_path / "elsewhere"
    (custom / "projects").mkdir(parents=True)
    roots = claude.project_roots(home=tmp_path, env={"CLAUDE_CONFIG_DIR": str(custom)})
    assert custom / "projects" in roots


def test_missing_roots_are_dropped(tmp_path):
    assert claude.project_roots(home=tmp_path, env={}) == []


def test_symlinked_duplicate_root_is_collapsed(tmp_path):
    # ~/.config/claude -> ~/.claude is a common XDG layout. Counting both roots
    # would scan every file twice; the global dedup fixes the total but not the
    # doubled scan cost.
    real = tmp_path / ".claude"
    (real / "projects").mkdir(parents=True)
    (tmp_path / ".config").mkdir()
    (tmp_path / ".config" / "claude").symlink_to(real)
    roots = claude.project_roots(home=tmp_path, env={})
    assert len(roots) == 1


def test_jsonl_files_finds_hidden_nested_files(tmp_path):
    # .claude is a hidden directory — a scan that skips hidden entries finds
    # nothing at all.
    deep = tmp_path / "a" / "b"
    deep.mkdir(parents=True)
    (deep / "s.jsonl").write_text("", encoding="utf-8")
    (deep / "notes.txt").write_text("", encoding="utf-8")
    found = list(claude.jsonl_files(tmp_path))
    assert [p.name for p in found] == ["s.jsonl"]
