"""HTTP surface for browse/tag-filter/note-detail/ranked-search
(REQ-SB-02-US-01) -- delegates to VaultManager only, HTTP-only, no
data_access/filesystem access of its own (ADR-003)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.business.core.semantic.semantic_manager import (
    SemanticIndexUnavailableError,
    SemanticManager,
)
from app.business.core.vault.vault_manager import VaultManager
from app.business.logic import hybrid_search
from app.data_access.compass_client import CompassClientError

router = APIRouter(prefix="/vault-search")
_vault_manager = VaultManager()
_semantic_manager = SemanticManager(_vault_manager)


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


@router.get("/semantic")
def get_semantic_search(q: str, limit: int = 20) -> dict:
    """REQ-SB-06 -- meaning-based ranking alone. 503 (not 500) for an
    unbuilt index or an embedding model this subscription cannot call:
    both are real, operator-fixable service states, not server faults."""
    try:
        return _semantic_manager.search(q, limit=limit)
    except (SemanticIndexUnavailableError, CompassClientError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/hybrid")
def get_hybrid_search(q: str, limit: int = 20) -> dict:
    """REQ-SB-06 -- keyword and meaning fused (RRF). Never 503s: it falls
    back to keyword-only and reports `semantic_available: false`, so this
    is the endpoint a caller should prefer when it wants an answer rather
    than a diagnosis."""
    return hybrid_search.search(q, limit=limit)


@router.get("/semantic/status")
def get_semantic_status() -> dict:
    """Whether a semantic index exists, what built it, and whether the
    provider will answer at all (this install's subscription lists
    embedding models it is not entitled to call)."""
    return _semantic_manager.get_status()


@router.post("/semantic/rebuild")
def post_semantic_rebuild(force: bool = False) -> dict:
    """Embeds every note whose content changed since the last build;
    `force=true` re-embeds the whole vault (needed after changing the
    embedding model, which invalidates every stored vector)."""
    try:
        return _semantic_manager.build(force=force)
    except CompassClientError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


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
