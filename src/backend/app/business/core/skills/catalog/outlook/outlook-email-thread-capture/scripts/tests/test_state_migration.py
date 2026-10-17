"""Migrating the capture watermark out of its in-vault island.

The collision direction is the whole point. The app's own retired native
capture left a stale copy of this exact filename in the data folder
(watermark 2026-09-03, written by code that no longer runs), while
<vault>/.second-brain/ holds what this Skill actually read and wrote
(2026-09-01, after the incident rewind). Preferring the data-folder copy
would silently skip every email between the two.
"""
import importlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

LEGACY_WATERMARK = "2026-09-01 17:36:51.497814+00:00"
STALE_WATERMARK = "2026-09-03 19:30:31.671000+00:00"


def _load_module(vault: Path, data: Path):
    """Reimported per test: VAULT_PATH is read at module scope."""
    os.environ["SECOND_BRAIN_VAULT_PATH"] = str(vault)
    os.environ["SECOND_BRAIN_DATA_PATH"] = str(data)
    for name in ("run_delta_capture", "vault_manager"):
        sys.modules.pop(name, None)
    return importlib.import_module("run_delta_capture")


def _write(path: Path, watermark: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"last_captured_at": watermark}), encoding="utf-8")


def test_a_legacy_file_is_moved_into_the_data_root(tmp_path: Path) -> None:
    vault, data = tmp_path / "vault", tmp_path / "data"
    _write(vault / ".second-brain" / "email_capture_state.json", LEGACY_WATERMARK)

    module = _load_module(vault, data)
    resolved = module._state_path()

    assert resolved == data / "email_capture_state.json"
    assert json.loads(resolved.read_text(encoding="utf-8"))["last_captured_at"] == LEGACY_WATERMARK
    assert not (vault / ".second-brain").exists()


def test_the_legacy_file_wins_a_collision(tmp_path: Path) -> None:
    """The exact live situation: both files exist and disagree."""
    vault, data = tmp_path / "vault", tmp_path / "data"
    _write(vault / ".second-brain" / "email_capture_state.json", LEGACY_WATERMARK)
    _write(data / "email_capture_state.json", STALE_WATERMARK)

    module = _load_module(vault, data)
    resolved = module._state_path()

    assert json.loads(resolved.read_text(encoding="utf-8"))["last_captured_at"] == LEGACY_WATERMARK
    # The displaced copy is kept, never silently destroyed.
    superseded = data / "email_capture_state.json.superseded"
    assert json.loads(superseded.read_text(encoding="utf-8"))["last_captured_at"] == STALE_WATERMARK


def test_no_legacy_file_means_the_data_root_copy_is_left_alone(tmp_path: Path) -> None:
    vault, data = tmp_path / "vault", tmp_path / "data"
    _write(data / "email_capture_state.json", STALE_WATERMARK)

    module = _load_module(vault, data)

    assert json.loads(module._state_path().read_text(encoding="utf-8"))["last_captured_at"] == STALE_WATERMARK


def test_migration_is_idempotent(tmp_path: Path) -> None:
    vault, data = tmp_path / "vault", tmp_path / "data"
    _write(vault / ".second-brain" / "email_capture_state.json", LEGACY_WATERMARK)

    module = _load_module(vault, data)
    module._state_path()
    resolved = module._state_path()

    assert json.loads(resolved.read_text(encoding="utf-8"))["last_captured_at"] == LEGACY_WATERMARK


def test_a_legacy_folder_holding_other_files_is_not_removed(tmp_path: Path) -> None:
    """Only an emptied island goes; anything else there is someone's data."""
    vault, data = tmp_path / "vault", tmp_path / "data"
    _write(vault / ".second-brain" / "email_capture_state.json", LEGACY_WATERMARK)
    (vault / ".second-brain" / "something_else.json").write_text("{}", encoding="utf-8")

    module = _load_module(vault, data)
    module._state_path()

    assert (vault / ".second-brain" / "something_else.json").is_file()
