"""BUG-087 -- the vault index was written where nothing reads it.

The App Database Folder moved out of the vault to its own location. The
`vault-index` Skill named the old path in prose (`--data-path
"$SECOND_BRAIN_VAULT_PATH\\.second-brain"`), the prose did not follow the move,
and the agent dutifully passed it: the agent-facing index was written to
`<vault>/.second-brain/index` for weeks while every reader resolved
`SECOND_BRAIN_DATA_PATH` and looked in the new folder. Both folders existed, so
nothing errored -- it just answered from a stale file.

The fix is that the path is no longer something a caller can get wrong: the
script reads the environment, the same way it already did for the vault path.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPTS = (Path(__file__).resolve().parents[1] / "app" / "business" / "core" / "skills"
            / "catalog" / "vault" / "vault-index" / "scripts")
_MANAGERS = Path(__file__).resolve().parents[1] / "app" / "business" / "core" / "skills" / "managers"
for _path in (_SCRIPTS, _MANAGERS):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import build_vault_index  # noqa: E402

SKILL_MD = _SCRIPTS.parent / "SKILL.md"


def run_main(monkeypatch, argv, env):
    monkeypatch.setattr(sys, "argv", ["build_vault_index.py", *argv])
    for key in ("SECOND_BRAIN_VAULT_PATH", "SECOND_BRAIN_DATA_PATH"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return build_vault_index.main()


def test_the_data_path_comes_from_the_environment(monkeypatch, tmp_path):
    """Nobody passes it, so nobody can pass the wrong one."""
    vault, data = tmp_path / "vault", tmp_path / "config"
    (vault / "Work" / "Notes").mkdir(parents=True)
    (vault / "Work" / "Notes" / "n.md").write_text('---\ntype: "Note"\n---\n\nbody\n', encoding="utf-8")
    monkeypatch.setattr(build_vault_index, "notify_backend", lambda _url: {"notified": False})

    assert run_main(monkeypatch, [], {
        "SECOND_BRAIN_VAULT_PATH": str(vault), "SECOND_BRAIN_DATA_PATH": str(data),
    }) == 0
    assert (data / "index" / "vault_index.json").is_file()
    # Emphatically NOT the pre-move location.
    assert not (vault / ".second-brain").exists()


def test_a_missing_data_path_stops_rather_than_guessing(monkeypatch, tmp_path):
    """Guessing `<vault>/.second-brain` is exactly what wrote the index into a
    folder nothing read -- and because that folder existed, nothing complained."""
    vault = tmp_path / "vault"
    (vault / "Work").mkdir(parents=True)

    with pytest.raises(SystemExit) as stopped:
        run_main(monkeypatch, [], {"SECOND_BRAIN_VAULT_PATH": str(vault)})

    assert "SECOND_BRAIN_DATA_PATH" in str(stopped.value)
    assert not (vault / ".second-brain").exists()


def test_the_skill_no_longer_names_a_data_path():
    """The instruction is the thing that went stale, so pin the instruction."""
    skill_md = SKILL_MD.read_text(encoding="utf-8")
    command = next(line for line in skill_md.splitlines() if "build_vault_index.py" in line and "terminal(" in line)

    assert "--data-path" not in command, f"the Skill passes a data path again: {command}"
    assert ".second-brain" not in command
