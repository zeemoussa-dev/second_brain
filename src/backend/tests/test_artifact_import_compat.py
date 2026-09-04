"""Screening an incoming bundle for the regression that caused the
2026-09-04 email-capture outage.

A Skill script that resolves the App Database Folder at the hardcoded
`<vault>/.second-brain` instead of via `vault_manager.data_root()` will
silently stop writing anything once config lives outside the vault. The
export/import placeholder machinery cannot catch it -- it substitutes
absolute paths, and this is a relative literal in the script's own source.
"""
from app.business.logic import artifact_import_compat


def _skill(artifact_id: str) -> dict:
    return {"id": artifact_id, "kind": "skill"}


def test_a_script_with_the_old_hardcoded_path_is_flagged() -> None:
    payload = {
        "skills/capture/scripts/ingest.py": b'PATH = vault_path / ".second-brain" / "data"',
    }

    [entry] = artifact_import_compat.flag_stale_data_paths([_skill("capture")], payload)

    assert entry["stale_data_path"] is True
    assert entry["stale_data_path_detail"]["files"] == ["skills/capture/scripts/ingest.py"]


def test_a_script_going_through_the_resolver_is_not_flagged() -> None:
    """The resolver's own fallback branch legitimately names the legacy
    folder, so the mere presence of that string must not trip the check."""
    payload = {
        "skills/capture/scripts/vault_manager.py": (
            b'def data_root(vault_path):\n'
            b'    return Path(os.environ["SECOND_BRAIN_DATA_PATH"]) or vault_path / ".second-brain"\n'
        ),
    }

    [entry] = artifact_import_compat.flag_stale_data_paths([_skill("capture")], payload)

    assert entry["stale_data_path"] is False


def test_only_the_artifacts_own_files_are_screened() -> None:
    payload = {
        "skills/other/scripts/legacy.py": b'p = vault / ".second-brain"',
        "skills/capture/scripts/fine.py": b"print('hello')",
    }

    [entry] = artifact_import_compat.flag_stale_data_paths([_skill("capture")], payload)

    assert entry["stale_data_path"] is False


def test_non_skill_artifacts_are_never_flagged() -> None:
    payload = {"skills/thing/scripts/legacy.py": b'p = vault / ".second-brain"'}

    [entry] = artifact_import_compat.flag_stale_data_paths([{"id": "thing", "kind": "template"}], payload)

    assert entry["stale_data_path"] is False


def test_every_artifact_is_screened_even_after_a_hit() -> None:
    """An earlier hit must never short-circuit the rest -- same per-artifact
    discipline detect_conflicts already follows."""
    payload = {
        "skills/a/scripts/x.py": b'p = vault / ".second-brain"',
        "skills/b/scripts/y.py": b'p = vault / ".second-brain"',
    }

    flagged = artifact_import_compat.flag_stale_data_paths([_skill("a"), _skill("b")], payload)

    assert [e["stale_data_path"] for e in flagged] == [True, True]


def test_undecodable_bytes_are_surfaced_rather_than_assumed_safe() -> None:
    payload = {"skills/capture/scripts/broken.py": b"\xff\xfe not utf-8"}

    [entry] = artifact_import_compat.flag_stale_data_paths([_skill("capture")], payload)

    assert entry["stale_data_path"] is True


def test_non_python_members_are_ignored() -> None:
    payload = {"skills/capture/SKILL.md": b"Documents the old .second-brain layout"}

    [entry] = artifact_import_compat.flag_stale_data_paths([_skill("capture")], payload)

    assert entry["stale_data_path"] is False
