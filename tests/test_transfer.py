import json

import pytest

from poketokenbar import save, transfer
from poketokenbar.balance import Rarity
from poketokenbar.companion import CompanionState, DexEntry


def _state(dex=2, tokens=1234):
    s = CompanionState()
    s.used_since_install = tokens
    s.dex = [
        DexEntry(base_id=i, final_id=i, chain_order=[i], rarity=Rarity.COMMON)
        for i in range(1, dex + 1)
    ]
    s.inventory = {"rareCandy": 3}
    return s


def test_roundtrip_preserves_progress(tmp_path):
    path = tmp_path / "export.json"
    transfer.export_to(path, _state())
    target = tmp_path / "companion.json"
    restored = transfer.import_from(path, target=target)
    assert restored.used_since_install == 1234
    assert len(restored.dex) == 2
    assert restored.inventory == {"rareCandy": 3}


def test_export_envelope_carries_provenance(tmp_path):
    path = tmp_path / "export.json"
    transfer.export_to(path, _state())
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["format"] == transfer.FORMAT
    assert raw["format_version"] == transfer.FORMAT_VERSION
    assert raw["device"]
    assert raw["exported_at"] > 0


def test_export_is_atomic(tmp_path):
    path = tmp_path / "export.json"
    transfer.export_to(path, _state())
    assert list(tmp_path.iterdir()) == [path]


def test_importing_a_foreign_file_is_refused(tmp_path):
    path = tmp_path / "other.json"
    path.write_text(json.dumps({"hello": "world"}), encoding="utf-8")
    with pytest.raises(transfer.TransferError):
        transfer.import_from(path, target=tmp_path / "companion.json")


def test_importing_a_future_version_is_refused(tmp_path):
    # Silently dropping fields we cannot read would lose progress invisibly.
    path = tmp_path / "future.json"
    path.write_text(
        json.dumps({"format": transfer.FORMAT, "format_version": 99, "save": {}}),
        encoding="utf-8",
    )
    with pytest.raises(transfer.TransferError):
        transfer.import_from(path, target=tmp_path / "companion.json")


def test_importing_corrupt_json_is_refused(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(transfer.TransferError):
        transfer.import_from(path, target=tmp_path / "companion.json")


def test_a_refused_import_leaves_the_existing_save_untouched(tmp_path):
    target = tmp_path / "companion.json"
    save.save(_state(dex=5, tokens=999), target)

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"format": "something-else"}), encoding="utf-8")
    with pytest.raises(transfer.TransferError):
        transfer.import_from(bad, target=target)

    assert save.load(target).used_since_install == 999


def test_import_backs_up_the_previous_save(tmp_path):
    target = tmp_path / "companion.json"
    save.save(_state(dex=5, tokens=999), target)

    incoming = tmp_path / "export.json"
    transfer.export_to(incoming, _state(dex=1, tokens=1))
    transfer.import_from(incoming, target=target)

    backup = tmp_path / "companion.json.before-import"
    assert backup.is_file()
    assert save.load(backup).used_since_install == 999
    assert save.load(target).used_since_install == 1


def test_summary_describes_progress_for_the_overwrite_prompt():
    s = transfer.summary(_state(dex=4, tokens=50))
    assert s["dex_count"] == 4
    assert s["used_since_install"] == 50
    assert s["items"] == 3


def test_suggested_filename_is_dated():
    assert transfer.suggested_filename().startswith("poketokenbar-save-")
    assert transfer.suggested_filename().endswith(".json")
