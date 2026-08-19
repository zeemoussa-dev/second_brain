"""One-off vault base provisioning (REQ-SB-70-US-01, see ADR-048 in
Implementation/Architecture/ADR.md) -- mirrors vault_migration.py's own
module shape (flat, operator-triggered, one-off) but is explicitly NOT a
migration: no archiving, no wipe, no re-run over Outlook history. Lays down
exactly the empty Work/ PARA/OKF base skeleton the redesigned Email/Meeting
capture pipelines (REQ-SB-71) write into, using this codebase's own already-
proven idempotent-mkdir convention (_write_frontmatter_note's/
write_attachments' own mkdir(parents=True, exist_ok=True)) -- never a new
idempotency mechanism.
"""
from __future__ import annotations

from app.config import settings

_WORK_ROOT = "Work"
_BASE_BUCKETS = ("Customers", "Threads", "Meetings", "Resources")
_ARCHIVE_SUBFOLDERS = ("Opportunities", "Customers", "Resources")


def provision_vault_base() -> dict:
    """Idempotent mkdir(parents=True, exist_ok=True) for exactly:
    Work/Customers/, Work/Threads/, Work/Meetings/, Work/Resources/,
    Work/Archive/{Opportunities,Customers,Resources}/ -- mirroring
    _write_frontmatter_note's/write_attachments' own already-proven
    idempotent-mkdir convention. Creates nothing else -- no individual
    Customer OKF directory, no Work/Opportunities/, Work/Websites/,
    Work/Notes/. Does not touch, wipe, or inspect any pre-existing Work/
    content beyond checking each named bucket's own existence -- the
    operator's own responsibility to ensure Work/ is otherwise empty first.

    Returns {"created": [...], "already_existed": [...]} -- both lists hold
    vault-relative POSIX-style paths, mirroring this codebase's own
    established "report what actually happened" return-shape convention
    (e.g. ensure_person_note's own created: bool)."""
    work_root = settings.vault_path / _WORK_ROOT

    target_dirs = [work_root / bucket for bucket in _BASE_BUCKETS]
    archive_root = work_root / "Archive"
    target_dirs.extend(archive_root / subfolder for subfolder in _ARCHIVE_SUBFOLDERS)

    created: list[str] = []
    already_existed: list[str] = []
    for target_dir in target_dirs:
        relative_path = target_dir.relative_to(settings.vault_path).as_posix()
        if target_dir.exists():
            already_existed.append(relative_path)
        else:
            created.append(relative_path)
        target_dir.mkdir(parents=True, exist_ok=True)

    return {"created": created, "already_existed": already_existed}
