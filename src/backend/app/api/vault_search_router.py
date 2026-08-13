"""HTTP surface for browse/tag-filter/note-detail/ranked-search
(REQ-SB-02-US-01) -- delegates to app.business.vault_search/
vault_indexing only, HTTP-only, no data_access/filesystem access of its
own (ADR-003)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.business import vault_indexing, vault_search

router = APIRouter(prefix="/vault-search")


@router.get("/status")
def get_status() -> dict:
    """Scenario 7 -- the frontend calls this first, on page load.
    indexed=false means the entire browse/search surface should render
    the honest "nothing indexed yet" state instead of any list/search
    UI."""
    last_rebuilt_at = vault_indexing.get_last_rebuilt_at()
    return {"indexed": last_rebuilt_at is not None, "last_rebuilt_at": last_rebuilt_at}


@router.get("/notes")
def get_notes(tag: str | None = None, page: int = 1, page_size: int = 20) -> dict:
    """Scenarios 1, 2, 6 -- tag omitted = all notes."""
    return vault_search.list_notes(page=page, page_size=page_size, tag=tag)


@router.get("/notes/{stem}")
def get_note(stem: str) -> dict:
    """Scenario 3."""
    detail = vault_search.get_note_detail(stem)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"No indexed note with stem '{stem}'")
    return detail


@router.get("/search")
def get_search(q: str, limit: int = 20) -> dict:
    """Scenarios 4, 5."""
    return vault_search.search(q, limit=limit)


@router.get("/tags")
def get_tags() -> dict:
    """Feeds the frontend's tag-filter chip row (Scenario 2's own
    real-tag-discovery prerequisite)."""
    return vault_search.list_tags()
