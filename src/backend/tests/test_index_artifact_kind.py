"""Index became the fifth artifact kind on 2026-09-06.

Before that it had a Manager, a router and its own on-disk store, but the
export/import machinery only knew skill/template/agent/pipeline -- so an
Index could not travel in a `.sbf` bundle at all, which is the defining
property of an artifact. These tests pin the two things most likely to
regress: the payload folder name, and the fact that importing an Index
never mints a live cron job on the receiving machine.
"""
import json

import pytest

from app.business.core.index.index_manager import IndexManager
from app.business.logic import artifact_export, artifact_import


def test_the_payload_folder_is_not_naively_pluralised() -> None:
    """`f"{kind}s/"` would emit "indexs/", and the import side looks for
    "indexes/" -- the bundle would export and then silently import nothing."""
    assert artifact_export._PAYLOAD_FOLDER["index"] == "indexes"


def test_importing_an_index_keeps_no_foreign_cron_ids(monkeypatch) -> None:
    """cron_job_id is an opaque id minted by the EXPORTING machine's Hermes.
    Carrying it over would leave this install pointing at a job it does not
    have -- or, worse, at an unrelated job that happens to share the id."""
    written: dict = {}
    monkeypatch.setattr(
        "app.business.core.index.index_manager.indexes_data.write_index_json",
        lambda index_id, data: written.update({index_id: data}),
    )
    monkeypatch.setattr(
        "app.business.core.index.index_manager.indexes_data.read_index_json",
        lambda index_id: written[index_id],
    )

    IndexManager().import_index("adnoc", {
        "id": "adnoc", "name": "ADNOC", "folders": ["Work"], "tags": [], "depth": None,
        "storage_path": r"C:\other-machine\out.json", "schedule": "every 60m",
        "cron_job_id": "923faa911fa1", "cron_profile_id": "someone-elses-profile",
    })

    assert written["adnoc"]["cron_job_id"] is None
    assert written["adnoc"]["cron_profile_id"] is None
    # Everything the operator actually authored survives.
    assert written["adnoc"]["name"] == "ADNOC"
    assert written["adnoc"]["folders"] == ["Work"]
    assert written["adnoc"]["schedule"] == "every 60m"


def test_an_imported_index_is_listed_but_unscheduled(monkeypatch) -> None:
    """The honest end state: real and rebuildable, not silently running."""
    written: dict = {}
    monkeypatch.setattr(
        "app.business.core.index.index_manager.indexes_data.write_index_json",
        lambda index_id, data: written.update({index_id: data}),
    )
    monkeypatch.setattr(
        "app.business.core.index.index_manager.indexes_data.read_index_json",
        lambda index_id: written[index_id],
    )

    index = IndexManager().import_index("adnoc", {"id": "adnoc", "name": "ADNOC", "schedule": "every 60m"})

    assert index.cron_job_id is None
    assert index.cron_enabled is None
    assert index.schedule == "every 60m"


def test_the_import_dispatcher_recognises_the_index_kind(monkeypatch) -> None:
    """An unrecognised kind raises ValueError -- this pins that "index" is
    no longer one."""
    captured: dict = {}
    monkeypatch.setattr(
        artifact_import, "_deploy_index",
        lambda artifact_id, conflicts, decision, payload: captured.setdefault("id", artifact_id) or {"ok": True},
    )

    payload = {"indexes/adnoc/Index.json": json.dumps({"id": "adnoc", "name": "ADNOC"}).encode("utf-8")}
    artifact_import._deploy_one(
        {"kind": "index", "id": "adnoc"}, None, payload, {}, None,
    )

    assert captured["id"] == "adnoc"
