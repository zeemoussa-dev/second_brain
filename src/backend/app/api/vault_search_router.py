"""HTTP surface for browse/tag-filter/note-detail/ranked-search
(REQ-SB-02-US-01) -- HTTP-only, no data_access/filesystem access of its
own (ADR-003). It delegates to `VaultManager` and, for the two reads
that compose more than one source, to a `business/logic` module
(`hybrid_search`, and `scoped_entity_read` since REQ-SB-95-US-05-T05)."""
from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.business.core.semantic.semantic_manager import (
    SemanticIndexUnavailableError,
    SemanticManager,
)
from app.business.core.vault import text_tidy
from app.business.core.vault import vault_manager as vault_manager_module
from app.business.core.vault.vault_manager import VaultManager
from app.business.logic import hybrid_search, scoped_entity_read
from app.data_access.compass_client import CompassClientError

router = APIRouter(prefix="/vault-search")
_vault_manager = VaultManager()
_semantic_manager = SemanticManager(_vault_manager)


class WikilinkTargets(BaseModel):
    targets: list[str]


@router.get("/status")
def get_status() -> dict:
    """Scenario 7 -- the frontend calls this first, on page load.
    indexed=false means the entire browse/search surface should render
    the honest "nothing indexed yet" state instead of any list/search
    UI."""
    last_rebuilt_at = _vault_manager.get_last_rebuilt_at()
    return {
        "indexed": last_rebuilt_at is not None,
        "last_rebuilt_at": last_rebuilt_at,
        # The index is in memory, so a restarted process has none until the
        # boot rebuild lands. `indexed: false` alone made the screen say
        # "Nothing indexed yet" for those seconds, which is a false statement
        # about the vault rather than a true one about the server.
        "building": _vault_manager.is_rebuilding(),
    }


@router.get("/notes")
def get_notes(
    tag: str | None = None,
    kind: str | None = None,
    folder: str | None = None,
    sort: str = "name",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Scenarios 1, 2, 6 -- every filter omitted = all notes. `kind`, `folder`
    and `sort` (name | recent) added 2026-10-24. `tag` matches the tag and
    everything under it: these tags are paths, so "azure" has to mean the
    branch."""
    return _vault_manager.list_notes(
        page=page, page_size=page_size, tag=tag, kind=kind, folder=folder, sort=sort
    )


@router.get("/notes/{stem}")
def get_note(stem: str) -> dict:
    """Scenario 3."""
    detail = _vault_manager.get_note_detail(stem)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"No indexed note with stem '{stem}'")
    return detail


class NoteBodyUpdate(BaseModel):
    body: str
    #: The version the editor opened. Required, never optional: a save with no
    #: version is a save that cannot notice it is overwriting somebody.
    version: str


@router.put("/notes/{stem}/body")
def put_note_body(stem: str, update: NoteBodyUpdate) -> dict:
    """Edit a note in place (operator, 2026-10-24).

    409, not 500, when the file moved on: another writer got there first,
    which is an ordinary event in a vault that agents also write, and the
    frontend shows it as a refusal with the operator's text still in hand.
    """
    try:
        result = _vault_manager.update_note_body(stem, update.body, update.version)
    except vault_manager_module.NoteChangedError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except vault_manager_module.NoteNotEditableError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"The note could not be written: {exc}") from exc
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("detail", "No such note"))
    return result


class TidyRequest(BaseModel):
    text: str


@router.post("/tidy")
def post_tidy(request: TidyRequest) -> dict:
    """Fix the typing in a draft, through Compass (operator, 2026-10-24).

    Takes the TEXT rather than a stem: what wants tidying is what is in the
    editor right now, which is not what is on disk -- that is the whole point
    of tidying before saving.

    422 for a refusal, because a refusal here is about the content and is
    written to be read: "Compass changed a link" tells the operator both what
    happened and why nothing was applied.
    """
    try:
        return text_tidy.tidy(request.text)
    except text_tidy.TidyRefused as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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


@router.get("/tag-tree")
def get_tag_tree() -> dict:
    """Tags as the tree they already are. This vault has 312 of them across 15
    top-level categories, so the flat chip row was a screenful of chips before
    the notes started (operator, 2026-10-24)."""
    return _vault_manager.list_tag_tree()


@router.get("/folders")
def get_folders() -> dict:
    """The vault's own folder tree, the other way people know where a note
    is."""
    return _vault_manager.list_folders()


@router.get("/kinds")
def get_kinds() -> dict:
    """Feeds the browse screen's kind filter, the same way /tags feeds its
    tag chips."""
    return _vault_manager.list_kinds()


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


@router.post("/resolve")
def post_resolve(payload: WikilinkTargets) -> dict:
    """Which of these `[[wikilink]]` targets are real notes (`BUG-079`).

    Every surface that shows vault text needs this answer, and each one used to
    find it for itself -- so a wikilink linked only where somebody remembered.
    A text mentions a dozen notes at most, whereas an install can index tens of
    thousands, so the browser asks about the targets it actually holds instead of
    downloading the index."""
    return {"resolved": _vault_manager.resolve_wikilink_targets(payload.targets)}


@router.get("/entity-read")
def get_entity_read(
    name: str,
    evidence_limit: int = scoped_entity_read.DEFAULT_EVIDENCE_LIMIT,
) -> dict:
    """Everything known about ONE named entity, read from that entity's own
    tag scope -- hub synthesis first, then its tagged evidence newest first
    (`REQ-SB-95-US-05-T05`, `ADR-037`). This is the `http` implementation of
    the shipped scoped-read Action, so an agent reaches it through the Action
    call gate and never as a private endpoint of its own (`ADR-033`).

    **It performs no search**, despite the prefix it is mounted under. The
    read reaches the vault only through the tag-keyed projection
    (`scoped_entity_read`'s own guarantee, asserted in its tests by arming
    every search entry point to fail), so this route is the honest
    alternative to `/vault-search/search` for a question that names an
    entity, sitting beside it rather than inside it.

    **An honest non-answer is a 200, not a 404.** A name that did not
    resolve, a name two registered entries both claim, and an entity nothing
    has been written about are three real answers to a question this app
    understood -- and the call gate treats any non-2xx as "the operation did
    NOT happen" (`ADR-033`), which would report all three to the agent as a
    failed call rather than as what is actually known. A status is reserved
    for the app failing, and these are the app succeeding at telling the
    truth.

    **It surfaces the result; it does not flatten it.** The body is the read
    itself, field for field -- `performed`, the resolution that produced it
    (`resolved` / `ambiguous` / `did_not_resolve`, with the candidates when
    two entries matched), `hub_status`, the synthesis, the evidence newest
    first with each note's own `recency_field` and `undated_because`, and
    `evidence_total` beside the capped list. The five keys added below are
    what `asdict` cannot carry -- four computed properties of the result, and
    the undated rule itself -- each one a distinction a caller would otherwise
    have to re-derive or go to the source for. `every_namespace_answered` is
    the sharpest: false means a registered namespace could not be asked, which
    makes this answer incomplete rather than final.
    """
    result = scoped_entity_read.read_entity_named(name, evidence_limit=evidence_limit)
    resolution = result.resolution
    return {
        **asdict(result),
        "resolution_outcome": resolution.outcome if resolution is not None else None,
        "every_namespace_answered": (
            resolution.every_namespace_answered if resolution is not None else None
        ),
        "found_anything": result.found_anything,
        "evidence_returned": len(result.evidence),
        "undated_evidence_rule": scoped_entity_read.UNDATED_EVIDENCE_RULE,
    }


@router.get("/graph")
def get_graph(
    tag: str | None = None,
    kind: str | None = None,
    folder: str | None = None,
    limit: int | None = None,
) -> dict:
    """The knowledge graph's {"nodes", "edges"} snapshot for a scope.

    The story this came from (`REQ-SB-75-US-01-T01`) deliberately took no
    parameters and filtered client-side, at ~680 notes. This vault is at 4,300
    and the screen became a cloud, so the same tag/kind/folder the browse list
    uses now scopes the graph, and `limit` caps what is drawn."""
    return _vault_manager.get_graph(tag=tag, kind=kind, folder=folder, limit=limit)
