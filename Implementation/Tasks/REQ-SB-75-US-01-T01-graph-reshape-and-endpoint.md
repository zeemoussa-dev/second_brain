---
id: REQ-SB-75-US-01-T01
title: vault_search.get_graph() + GET /vault-search/graph endpoint
parent_story: REQ-SB-75-US-01
requirement_id: REQ-SB-75
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-75-US-01-T01 — vault_search.get_graph() + GET /vault-search/graph endpoint

## Parent Story

- Story: [[REQ-SB-75-US-01]] — `../UserStories/REQ-SB-75-US-01-the-vault-knowledge-graph-screen.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-75 *The Vault — Real-Data Knowledge Graph Screen*

---

## Objective

Add a new `get_graph()` function to `app/business/vault_search.py` that
reshapes the existing `vault_indexing.get_index()` snapshot into
`{"nodes": [...], "edges": [...]}`, and expose it via a new, additive
`GET /vault-search/graph` route on the existing `/vault-search/*` router —
zero new indexing/caching, zero new router/module.

---

## Starting State → End State

**Before / Inputs:**
- `vault_search.py` already has `_summary(entry)` (`{"stem", "title",
  "kind", "tags"}`, `kind` via `_kind_for(entry)` =
  `entry["frontmatter"].get("type", "Unknown")`) and
  `_resolve_forward_links(entry, index)` (case-insensitive stem-matching
  over `entry["outgoing_wikilinks"]`, silently skipping a target that
  doesn't resolve to any indexed stem or resolves to the entry itself).
- `vault_search_router.py` already has `/status`, `/notes`,
  `/notes/{stem}`, `/search`, `/tags`, `/scope-suggestions`, all
  delegating to `vault_search`/`vault_indexing` only.

**After / Outputs:**
- `vault_search.get_graph() -> dict` returns:
  - `"nodes"`: `[_summary(entry) for entry in index.values()]` — one entry
    per real indexed note, unmodified `_summary()` shape (`stem`, `title`,
    `kind`, `tags`). `kind` is whatever real `frontmatter.type` value the
    note carries — no coercion into a fixed enum.
  - `"edges"`: one `{"source": <stem>, "target": <matched_stem>}` entry per
    real, resolved `outgoing_wikilinks` target — reusing the exact same
    case-insensitive stem-matching rule `_resolve_forward_links` already
    applies (a dangling target, or a target resolving to the entry itself,
    is silently omitted — no crash, no fabricated edge). No dedup of
    reciprocal A→B/B→A pairs (implementation-internal, not AC-locked).
- `GET /vault-search/graph` returns `vault_search.get_graph()` directly, no
  query parameters (no pagination/filter — the full current graph every
  call, matching the vault's real ~680-note scale and the story's own
  "large-corpus performance work is out of scope" Constraint).

---

## Files to Modify

- `src/backend/app/business/vault_search.py` — add `get_graph()`, reusing
  `_summary()` and the same case-insensitive stem-matching rule
  `_resolve_forward_links` already implements (a small private helper is
  fine if it avoids duplicating `_resolve_forward_links`'s own logic
  inline — coder's choice of exact factoring).
- `src/backend/app/api/vault_search_router.py` — add
  `GET /vault-search/graph` → `vault_search.get_graph()`, registered
  alongside the router's existing routes.

---

## Constraints

- Inherits from parent story: zero new indexing/caching — compose
  `vault_indexing.get_index()` directly, never a second, divergent
  graph-construction mechanism.
- Additive only — never a new router or module; this endpoint lives in the
  same `vault_search.py`/`vault_search_router.py` pair every other
  `/vault-search/*` route already uses.
- `kind` derivation is `_kind_for(entry)` directly — no new classification
  pass, no fixed kind-name enum/mapping table.
- Edge resolution must reuse the SAME case-insensitive stem-matching rule
  `_resolve_forward_links`/`ADR-024` already establish — not a
  reimplementation with different matching semantics.
- No pagination or `q=`/`tag=` filter query parameters on this endpoint —
  kind-filtering and name search are the frontend's own client-side
  concern (`T02`/`T03`) over the one fetched snapshot.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`) — the router calls `vault_search` only, never
  `vault_writer`/filesystem directly.

---

## Tests

**Manual verification steps** (`src/backend`: `uvicorn app.main:app
--reload`; real vault, real index):

1. [REQ-SB-75-US-01-AC-01] Call `GET /vault-search/graph` against the real,
   currently-indexed vault. Confirm `len(response["nodes"])` equals
   `len(vault_indexing.get_index())` (every real indexed note produced
   exactly one node), and spot-check at least 3 real notes of different
   real `frontmatter.type` values (e.g. a `Customer`, a `Thread`, a
   `Meeting` note) each have a node whose `"kind"` equals that note's own
   real `frontmatter.type` — never a default/fabricated value.
2. [REQ-SB-75-US-01-AC-02] Pick one real note A whose real
   `outgoing_wikilinks` includes a target that resolves (case-insensitively,
   by stem) to a real note B. Confirm `response["edges"]` contains
   `{"source": A.stem, "target": B.stem}`. Separately, confirm a real note
   with at least one genuinely dangling/unresolvable `outgoing_wikilinks`
   target produces NO edge for that specific target (cross-check against
   `_resolve_forward_links(A, index)`'s own real output for the same note —
   identical resolved-target set).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `vault_search.get_graph()` returns `{"nodes": [...], "edges": [...]}`
      composing `vault_indexing.get_index()` directly, zero new
      indexing/caching
- [x] Every real indexed note produces exactly one node via `_summary()`,
      `kind` via `_kind_for(entry)` unmodified
- [x] Every edge is produced via the SAME case-insensitive stem-matching
      rule `_resolve_forward_links` already applies; dangling/self targets
      silently omitted
- [x] `GET /vault-search/graph` is registered on the existing
      `/vault-search/*` router, no new router/module, no query parameters
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision/pattern/constraint emerged, ordinary composition)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend rendering, filtering, search, or navigation — `T02`/`T03`.
- Client-side kind-filter counts / name search — computed client-side over
  this endpoint's one fetched snapshot, not a backend concern.

---

## Context / Notes

Foundation task — no dependencies, can start immediately. See
`Implementation/Architecture/architecture.md` → "The Vault — Knowledge
Graph Screen (REQ-SB-75-US-01, no new ADR)" for the full reasoning
(reuse points, no-new-ADR justification). `T02` depends on this task since
its `client.ts` fetch wrapper and canvas rendering need the real, running
endpoint to build and verify against (this project's own established
"backend-layer-first" precedent).

---

## Implementation Log

**Implementation (2026-08-19):** Added `vault_search._resolve_forward_link_stems(entry, index)`
(a stem-only sibling of the existing `_resolve_forward_links`, factored
out so `get_graph()` doesn't pay for a full `_summary()` resolve per
edge target — same case-insensitive stem-matching rule, same
dangling/self-target silent-omission posture, zero duplicated logic) and
`vault_search.get_graph()` composing `vault_indexing.get_index()`
directly. Added `GET /vault-search/graph` → `vault_search.get_graph()`
on the existing router, no query params.

**Manual verification** (real backend, `uvicorn --reload` port 8001,
real vault at `VAULT_PATH`, real index rebuilt via
`POST /vault-index/rebuild` → 686 notes indexed):

- **[REQ-SB-75-US-01-AC-01] PASS.** `GET /vault-search/graph` →
  `len(nodes) == 686 == len(vault_indexing.get_index())`. Spot-checked 3
  real notes of different real `frontmatter.type` values against the
  real file on disk (not just the API's own derivation, to avoid
  circularity):
  - `Google` (`Work/Archive/Customers/Google/Google.md`) — real file
    `type: "customer"`, graph node `"kind": "customer"`. Match.
  - `040000008200E00074C5B7101A82E0080000000000BCF1EFF424DD01000000000000000010000000`
    (`Work/Meetings/.../...md`) — real file `type: "Meeting"`, graph
    node `"kind": "Meeting"`. Match.
  - `-Account Plans Core42 Template July-26- has been shared with
    you-2026-07-27-7c74` (`Work/Threads/...md`) — real file
    `type: "Thread"`, graph node `"kind": "Thread"`. Match.
  - Full kind distribution observed across all 686 real nodes: `RawMessage`
    259, `Thread` 138, `File` 125, `Person` 80, `Meeting` 51, `customer`
    29, `Partner` 2, `Unknown` 1, `project` 1 — every real `type` value
    rendered as its own kind, no coercion, no default-for-everyone value.
- **[REQ-SB-75-US-01-AC-02] PASS.** Picked a real note A
  (`040000008200E0...`) with 2 real edges to
  `nalsulaimani@masdar.ae` in `response["edges"]`; cross-checked against
  `GET /vault-search/notes/{stem}`'s own `forward_links` (which calls
  `_resolve_forward_links` directly) — identical 2-entry resolved-target
  set (`nalsulaimani@masdar.ae`, `Person` kind, twice). Separately, found a
  real note `Azure Demo Account Request` whose real, raw
  `outgoing_wikilinks` contains a genuinely dangling target ("Requested
  Item RITM0108464 has been updated-2026-07-27-025663bd", confirmed via a
  direct in-process check: `_resolve_forward_link_stems` returns `[]` for
  it) — confirmed `response["edges"]` contains zero entries with
  `"source": "Azure Demo Account Request"`. Silent omission confirmed,
  no crash, no fabricated edge.

No scope-internal judgement calls beyond the task's own explicitly-permitted
"coder's choice of exact factoring" for the private stem-resolution helper.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired (no assumption beyond
the task's own explicitly-permitted factoring choice, no ADR touched, no
escalation, both locked ACs verified live and passing).
