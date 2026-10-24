"""A server that has not finished reading the vault says so.

The index lives in memory, so a restarted process has none until the boot
rebuild lands. For those seconds every reader asked "is there an index?" and
was told no -- which the Vault screen rendered as "Nothing indexed yet" and a
note lookup rendered as "No indexed note found", both of them false statements
about the operator's vault rather than true ones about the server (operator,
2026-10-24, hit twice: a real note 404'd, then a restart showed an empty
vault).

"Not finished" and "nothing there" are opposite answers and the API has to be
able to give both.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.business.core.vault import vault_manager as vault_manager_module
from app.business.core.vault.vault_manager import VaultManager
from app.main import app

client = TestClient(app)


def test_a_queued_rebuild_reads_as_building(monkeypatch) -> None:
    """Marked where the rebuild is QUEUED, before its thread gets a turn: a
    request arriving in that gap would otherwise be told nothing is indexed
    and nothing is building either."""
    monkeypatch.setattr(vault_manager_module, "_rebuild_scheduled", False)
    monkeypatch.setattr(vault_manager_module, "_last_rebuilt_at", None)

    vault_manager_module.mark_rebuild_scheduled()

    body = client.get("/vault-search/status").json()
    assert body["indexed"] is False
    assert body["building"] is True


def test_a_finished_rebuild_is_not_building(monkeypatch, tmp_path) -> None:
    from app.config import settings

    root = tmp_path / "vault"
    (root / "Work" / "Notes").mkdir(parents=True)
    (root / "Work" / "Notes" / "a-note.md").write_text(
        '---\ntype: "note"\nsubject: "A note"\n---\n\nBody.\n', encoding="utf-8"
    )
    monkeypatch.setattr(settings, "vault_path", root)

    VaultManager().rebuild_index()

    body = client.get("/vault-search/status").json()
    assert body["indexed"] is True
    assert body["building"] is False


def test_a_rebuild_that_gave_up_stops_the_waiting(monkeypatch) -> None:
    """A flag left on would leave the screen waiting forever for an index that
    is never coming. Whoever scheduled the rebuild reports it settled, success
    or failure -- in `main.py` that is the task's done callback."""
    monkeypatch.setattr(vault_manager_module, "_last_rebuilt_at", None)
    vault_manager_module.mark_rebuild_scheduled()
    assert VaultManager().is_rebuilding() is True

    vault_manager_module.mark_rebuild_finished()

    assert VaultManager().is_rebuilding() is False


def test_a_finished_index_is_never_still_building(monkeypatch) -> None:
    """Belt and braces: once there IS an index there is nothing to wait for,
    so a caller that forgot to report the rebuild cannot strand the screen on
    a spinner."""
    monkeypatch.setattr(vault_manager_module, "_rebuild_scheduled", True)
    monkeypatch.setattr(vault_manager_module, "_last_rebuilt_at", "2026-10-24T12:00:00+00:00")

    assert VaultManager().is_rebuilding() is False


def test_an_empty_vault_is_still_honestly_empty(monkeypatch, tmp_path) -> None:
    """The guard must not turn a genuinely empty vault into a permanent
    "building" spinner -- that is the state it exists to tell apart."""
    from app.config import settings

    root = tmp_path / "vault"
    (root / "Work").mkdir(parents=True)
    monkeypatch.setattr(settings, "vault_path", root)

    VaultManager().rebuild_index()

    body = client.get("/vault-search/status").json()
    assert body["building"] is False
    # Indexed, with nothing in it: a vault that HAS no notes is a different
    # answer again from one that has not been read.
    assert body["indexed"] is True
