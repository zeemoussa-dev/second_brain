"""HTTP surface for browse/tag-filter/note-detail/ranked-search
(REQ-SB-02-US-01) -- delegates to VaultManager only, HTTP-only, no
data_access/filesystem access of its own (ADR-003)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.business.core.vault.vault_manager import VaultManager

router = APIRouter(prefix="/vault-search")
_vault_manager = VaultManager()


@router.get("/status")
def get_status() -> dict:
    """Scenario 7 -- the frontend calls this first, on page load.
    indexed=false means the entire browse/search surface should render
    the honest "nothing indexed yet" state instead of any list/search
    UI."""
    last_rebuilt_at = _vault_manager.get_last_rebuilt_at()
    return {"indexed": last_rebuilt_at is not None, "last_rebuilt_at": last_rebuilt_at}


@router.get("/notes")
def get_notes(tag: str | None = None, page: int = 1, page_size: int = 20) -> dict:
    """Scenarios 1, 2, 6 -- tag omitted = all notes."""
    return _vault_manager.list_notes(page=page, page_size=page_size, tag=tag)


@router.get("/notes/{stem}")
def get_note(stem: str) -> dict:
    """Scenario 3."""
    detail = _vault_manager.get_note_detail(stem)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"No indexed note with stem '{stem}'")
    return detail


@router.get("/notes/{stem}/assets/{filename}")
def get_note_asset(stem: str, filename: str) -> FileResponse:
    """Serves a real, co-located asset (an image referenced via a File
    note's own Obsidian-style `![[filename]]` embed) as raw bytes --
    2026-08-24, operator: "Images are not shown." `FileResponse` infers
    the response's own media type from the real file's extension."""
    path = _vault_manager.resolve_asset_path(stem, filename)
    if path is None:
        raise HTTPException(status_code=404, detail=f"No asset {filename!r} for note '{stem}'")
    return FileResponse(path)


@router.get("/search")
def get_search(q: str, limit: int = 20) -> dict:
    """Scenarios 4, 5."""
    return _vault_manager.search(q, limit=limit)


@router.get("/tags")
def get_tags() -> dict:
    """Feeds the frontend's tag-filter chip row (Scenario 2's own
    real-tag-discovery prerequisite)."""
    return _vault_manager.list_tags()


@router.get("/scope-suggestions")
def get_scope_suggestions() -> dict:
    """REQ-SB-50-US-01-T01 -- feeds the Agent Settings Vault Scope field's
    own typeahead (T02) with a real, vault-derived tag/folder snapshot."""
    return _vault_manager.list_scope_suggestions()


@router.get("/graph")
def get_graph() -> dict:
    """REQ-SB-75-US-01-T01 -- The Vault knowledge graph screen's own
    {"nodes", "edges"} snapshot. No query parameters -- the frontend
    fetches the full current graph once and filters/searches client-side
    (the story's own "large-corpus performance work out of scope at
    ~680 notes" Constraint)."""
    return _vault_manager.get_graph()
