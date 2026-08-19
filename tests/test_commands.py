import json

from poketokenbar import commands, config, ctl


def test_enqueue_then_drain_returns_the_command(tmp_path):
    commands.enqueue("refresh", {}, spool=tmp_path)
    drained = commands.drain(spool=tmp_path)
    assert len(drained) == 1
    assert drained[0]["name"] == "refresh"


def test_drain_empties_the_spool(tmp_path):
    commands.enqueue("refresh", {}, spool=tmp_path)
    commands.drain(spool=tmp_path)
    assert commands.drain(spool=tmp_path) == []


def test_drain_preserves_enqueue_order(tmp_path):
    for i in range(3):
        commands.enqueue("refresh", {"n": i}, spool=tmp_path)
    assert [c["args"]["n"] for c in commands.drain(spool=tmp_path)] == [0, 1, 2]


def test_drain_discards_corrupt_files_without_failing(tmp_path):
    commands.enqueue("refresh", {}, spool=tmp_path)
    (tmp_path / "999-bad.json").write_text("{corrupt", encoding="utf-8")
    drained = commands.drain(spool=tmp_path)
    assert [c["name"] for c in drained] == ["refresh"]
    assert list(tmp_path.iterdir()) == []


def test_ctl_set_writes_config(tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    monkeypatch.setattr(config, "default_path", lambda: cfg)
    monkeypatch.setattr(commands, "spool_dir", lambda: tmp_path / "spool")
    assert ctl.main(["set", "refresh_interval", "30"]) == 0
    assert json.loads(cfg.read_text(encoding="utf-8"))["refresh_interval"] == 30


def test_ctl_set_rejects_unknown_key(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "default_path", lambda: tmp_path / "config.json")
    monkeypatch.setattr(commands, "spool_dir", lambda: tmp_path / "spool")
    assert ctl.main(["set", "nonsense", "1"]) != 0


def test_ctl_refresh_enqueues(tmp_path, monkeypatch):
    monkeypatch.setattr(commands, "spool_dir", lambda: tmp_path)
    assert ctl.main(["refresh"]) == 0
    assert [c["name"] for c in commands.drain(spool=tmp_path)] == ["refresh"]
