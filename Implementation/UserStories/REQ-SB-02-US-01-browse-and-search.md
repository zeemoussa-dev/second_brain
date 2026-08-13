---
id: REQ-SB-02-US-01
title: Browse & Search — list/filter the indexed vault by tag, navigate the wikilink graph, and run ranked keyword search
requirement_ids: [REQ-SB-02]
requirement_section: "REQ-SB-02: Browse & Search"
phase: MVP
status: Done
gate: clear
gate_reason: ""
sprint: "SPRINT-026"
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-02-US-01 — Browse & Search — list/filter the indexed vault by tag, navigate the wikilink graph, and run ranked keyword search

## Story

**As a** Second Brain user
**I want** to browse my indexed vault notes, filter/navigate them by tag and
by wikilink graph, and run a search that returns genuinely relevant results
ranked by relevance rather than a bare substring match
**So that** I can actually find and use my own notes directly inside Second
Brain, without opening Obsidian or already knowing exactly which file I'm
looking for

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-02: Browse & Search* — "The user can
  browse and search their indexed notes directly — no promotion/approval
  gate between 'indexed' and 'usable.' Search should be relevant to real
  queries, not a bare substring match... Acceptance: The user can
  list/browse all indexed notes, filter or navigate by tag and by wikilink
  graph, and run a search query that returns relevant notes ranked by
  relevance, not just notes containing an exact substring match." The PRD's
  own breadcrumb: "Ported from agentic-map REQ-008 (Hybrid KB search — make
  retrieval relevant to real queries); tool swap only — no Postgres/Qdrant
  hybrid-search stack implied, just the same quality bar."
- **This pass is ranked keyword/full-text search, not semantic/embedding
  search.** `Documentation/PRD.md`'s P2 section (`REQ-SB-06`, Search Quality
  Enhancements) explicitly defers "chunking note content ahead of embedding
  at scale, and reranking results" as a refinement "once basic search
  (REQ-SB-02) is in place... since there is nothing yet to refine until
  REQ-SB-02 ships." `Implementation/Plans/2026-08-10-agentic-map-requirement-
  port.md` confirms the same reading directly: agentic-map's REQ-009
  (chunking-before-embedding) "becomes a P1/P2 concern once semantic search
  is wanted, not an MVP one." Resolved here: this story's "relevant, ranked,
  not a bare substring match" bar is met by a real ranked keyword/full-text
  mechanism (e.g. term-frequency/field-weighted relevance scoring) — not
  vector embeddings, which stay out of scope for `REQ-SB-06`/P2.
- **Resolved 2026-08-13 (`ESC-022`, Resolved) — the ranking technique and
  the wikilink-graph navigation shape are both settled:** ranking is a real
  ranked keyword/full-text relevance score (e.g. BM25-style term-frequency
  scoring across frontmatter/tags/body, boosted by field) — not a bare
  substring match, not embeddings/semantic search; the exact
  library/implementation choice within that class (a small pure-Python
  BM25 implementation vs. hand-rolled TF scoring) is ordinary
  implementation latitude, left to `/plan-tasks`. Wikilink-graph navigation
  is a **link list** — forward/outgoing links and backward/incoming links,
  both textual and clickable — not a visual/interactive graph canvas
  (force-directed layout, zoom/pan); a full graph visualization is
  disproportionate scope for the MVP's first browse/search pass (this
  project's own "proportionate first" precedent, `ADR-011`'s reasoning) and
  can be a future enhancement later, not built now.
- **Zero search infrastructure exists in this codebase today.** Confirmed
  by direct inspection (2026-08-13): `app/business/vault_query_tools.py`
  and every `app/data_access/vault_writer.py` "list"/"query" function are
  narrow, ad hoc frontmatter scans (`list_known_customers`,
  `list_known_kinds`, `list_known_partners`, `list_notes_in_kind_folder`)
  with no ranking, no full-text matching, and — per
  `REQ-SB-01-US-01`'s own Context — no persistent index behind any of them
  at all.
- **Blocked by `REQ-SB-01-US-01` (Vault Indexing).** This story lists,
  filters, navigates, and searches what that story indexes; it cannot be
  built, and cannot be meaningfully designed against real data, until that
  story's index exists. `REQ-SB-01-US-01` is `status: Draft`, `gate: clear`
  (its own flagged question resolved 2026-08-13) — ready for `/plan-tasks`,
  but not yet built.
- **No `html-prototype/` screen covers this.** Confirmed by direct listing
  (2026-08-13): `index.html`, `agents-map.html` / `agents-map-exploration.
  html`, `my-day.html` + its five drill-downs (`my-day-emails`,
  `my-day-calendar`, `my-day-todo`, `my-day-reads`, `my-day-approvals`),
  `settings.html`, `system-health.html` — none of these is a notes
  browser/search screen. Per the analyst's mandatory prototype-
  reconciliation rule, this means `gate: flagged` (`net-new-design-needed`),
  recommending `/design REQ-SB-02` before `/plan-tasks`.
- **`REQ-SB-12`'s app shell** (`REQ-SB-12-US-01`, `Done`) already
  established a collapsible sidebar navigating between Agents Map/My
  Day/Settings — the natural integration point for a new nav entry to
  whatever this story's screen(s) turn out to be, once designed.
- **`REQ-SB-29-US-01`'s own narrower, ad hoc scoped-retrieval primitive is
  unaffected by this story** — it was deliberately built independently
  (`ESC-008`, Resolved 2026-08-12) rather than wait on `REQ-SB-01`/
  `REQ-SB-02`; this story does not require it to be rebuilt.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. Scenario 4 deliberately commits to the observable behaviour
(ranked by relevance, not a bare substring match) without naming a specific
ranking algorithm — the algorithm choice is left to /plan-tasks; see the flag
in Notes. -->

### Scenario 1: Browsing the full list of indexed notes

```gherkin
Given the vault has been indexed (REQ-SB-01)
When the user opens the notes browser
Then the user sees a list of all indexed notes
```
<!-- AC-ID: REQ-SB-02-US-01-AC-01 -->

### Scenario 2: Filtering notes by tag

```gherkin
Given the vault has been indexed and contains notes carrying various tags
    (e.g. "customer/masdar", "kind/email")
When the user filters/navigates by a specific tag
Then only notes carrying that tag are shown
```
<!-- AC-ID: REQ-SB-02-US-01-AC-02 -->

### Scenario 3: Navigating a note's wikilink graph

```gherkin
Given the user is viewing an indexed note that has outgoing wikilinks to
    other notes, and incoming wikilinks (backlinks) from other notes
When the user views that note
Then the user can see and navigate to the notes it links to
  And the user can see and navigate to the notes that link to it
```
<!-- AC-ID: REQ-SB-02-US-01-AC-03 -->

### Scenario 4: Searching returns results ranked by relevance, not a bare substring match

```gherkin
Given the vault has been indexed and contains multiple notes, some more
    relevant to a given query than others
When the user runs a search query
Then the returned notes are ordered by relevance to the query
  And a note more relevant to the query's intent ranks above a less
    relevant note, even if the less relevant note also happens to contain
    the literal query text as an incidental substring
```
<!-- AC-ID: REQ-SB-02-US-01-AC-04 -->

### Scenario 5: A search query with no matching notes returns an honest empty result

```gherkin
Given the vault has been indexed
When the user runs a search query that matches no notes
Then the user sees an honest empty/no-results state
  And the user is not shown an error, and is not shown a misleadingly
    non-empty list
```
<!-- AC-ID: REQ-SB-02-US-01-AC-05 -->

### Scenario 6: A tag filter with no matching notes returns an honest empty result

```gherkin
Given the vault has been indexed
When the user filters by a tag that currently matches no notes
Then the user sees an honest empty result for that filter
```
<!-- AC-ID: REQ-SB-02-US-01-AC-06 -->

### Scenario 7: Browsing or searching before the vault has ever been indexed

```gherkin
Given the vault has not yet been indexed (REQ-SB-01's index does not exist
    yet, or indexing has never completed)
When the user opens the notes browser or runs a search
Then the user sees an honest state explaining nothing is indexed yet
  And the user is not shown an error or a silently-empty list
    indistinguishable from "indexed, but no matches"
```
<!-- AC-ID: REQ-SB-02-US-01-AC-07 -->

## Affected Screens

- **No `html-prototype/` screen exists for this today.** A new screen (or
  set of screens — e.g. a notes-list/browse view, a note-detail view showing
  forward/back links, and a search results view) is needed, reachable from
  the app shell's existing sidebar navigation (`REQ-SB-12-US-01`'s
  established pattern). **Not present in the approved prototype** — see the
  flag below; run `/design REQ-SB-02` before `/plan-tasks`.

## Dependencies

- **Blocked by:** `REQ-SB-01-US-01` (Vault Indexing) — this story's list,
  filter, wikilink-graph navigation, and search all read from that story's
  index; it cannot be built, or meaningfully designed against real data,
  until that story exists.
- **Related to:** `REQ-SB-12-US-01` (App Shell — Agents Map, My Day,
  Settings, `Done`) — the sidebar navigation this story's new screen(s) will
  hang off of.
- **Related to:** `REQ-SB-29-US-01` (Agent-to-Tag/Folder Scoping) — that
  story already shipped its own independent, narrower ad hoc scoped-query
  primitive rather than wait on this one (`ESC-008`, Resolved). Unaffected
  by this story.
- **Related to:** `REQ-SB-06` (Search Quality Enhancements, P2) —
  chunking/embeddings/reranking are explicitly deferred until this story's
  baseline ships; this story is the thing `REQ-SB-06` refines.
- **External:** none new.

## Constraints

- **Resolved 2026-08-13 — search this pass is a real ranked keyword/
  full-text relevance mechanism** (e.g. BM25-style term-frequency scoring
  across frontmatter/tags/body, boosted by field) — not a bare substring
  match, and not semantic/embedding-based (`REQ-SB-06`, P2, stays out of
  scope). The exact library/implementation choice within that class (a
  small pure-Python BM25 implementation vs. hand-rolled TF scoring) is
  ordinary implementation latitude, left to `/plan-tasks` — the
  requirement-level decision (real ranked relevance, not substring, not
  embeddings) is settled.
- **Resolved 2026-08-13 — wikilink-graph navigation is a link list.** A
  note's forward/outgoing links and backward/incoming links (backlinks) are
  both textual and clickable. **Not** a visual/interactive graph canvas
  (force-directed layout, zoom/pan, etc.) — disproportionate scope for the
  MVP's first browse/search pass; a visual graph view can be a future
  enhancement if wanted later, not built now.
- **No staging/promotion gate** — every indexed note is immediately
  browsable/searchable, with no "pending"/"unreviewed" state (standing
  `MEMORY.md` decision, restated directly in the PRD's own requirement
  text).
- **Read-only.** This story does not add any vault-write capability.

## Implementation Tasks

| Task | Title | Covers | depends_on |
|---|---|---|---|
| `REQ-SB-02-US-01-T01` | Index-readiness signal + browse/tag-filter/note-detail query logic — `app/business/vault_indexing.py` (additive) + new `app/business/vault_search.py` | AC-01, AC-02, AC-03, AC-06, AC-07 (readiness signal) | — |
| `REQ-SB-02-US-01-T02` | Ranked search (field-weighted BM25-style) — `app/business/vault_search.py::search()`, per `ADR-026` | AC-04, AC-05 | T01 |
| `REQ-SB-02-US-01-T03` | API surface — new `app/api/vault_search_router.py` | AC-01–AC-07 (HTTP surface) | T01, T02 |
| `REQ-SB-02-US-01-T04` | Frontend — `VaultBrowserPage.tsx` + `NoteDetailPage.tsx`, `features/vault-browser/client.ts`, nav wiring | AC-01–AC-07 (UI surface) | T03 |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, manual verification mode (no test stack ADR yet); every locked AC verified live per each task's own Implementation Log
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Building the index itself** — `REQ-SB-01`.
- **Semantic/embedding search, chunking, or reranking** — `REQ-SB-06` (P2).
- **Editing notes from within Second Brain's UI** — Obsidian remains the
  authoring surface; this story is read-only browse/search.
- **Agent-facing MCP search tools** (the eventual `REQ-SB-03`-style
  `kb_read`-equivalent for Hermes-connected agents, P1) — this story is the
  human-facing browse/search UI and its underlying query API; wrapping that
  query API as an agent tool is separate, later work.
- **Any change to `REQ-SB-29-US-01`'s own already-shipped narrower
  scoped-retrieval primitive** — unaffected by this story.
- **A visual/interactive wikilink-graph canvas** (force-directed layout,
  zoom/pan, etc.) — resolved out of scope this pass (see Constraints); a
  textual, clickable forward-link/backlink list is this story's full
  wikilink-graph-navigation scope. A future story can add a visual graph
  view if wanted later.

## Notes

**Prototype parity:** no `html-prototype/` screen exists for this
requirement at all — every visible region this story needs (notes list, tag
filter, note detail with forward/back links, search box + ranked results,
the empty/no-index-yet state) is **net-new**, none of it Specced/Deferred/
Superseded against an existing screen. See the flag below.

**Update, 2026-08-13 — `ESC-022` Resolved; one flag reason remains.** Both
open questions this story originally flagged are now settled (operator's
delegated "sane defaults" call, relayed via the coordinating session, not
guessed by the analyst): (1) ranking is a real ranked keyword/full-text
relevance score (BM25-style, field-weighted) — not substring, not
embeddings; exact library choice is ordinary `/plan-tasks` latitude; (2)
wikilink-graph navigation is a textual, clickable forward-link/backlink
list — not a visual graph canvas, which is deferred as a possible future
enhancement. Reflected above in Context, Constraints, and Non-Goals.
`ESCALATIONS.md` → `ESC-022` flipped to `Resolved`, naming this update as
the resolving artefact. **This story stays `gate: flagged`** — not because
the requirement is unclear anymore, but because the one remaining,
independent MUST-FLAG trigger is still live and unresolved by a requirement
decision alone:

1. **`net-new-design-needed`** — confirmed by direct listing of
   `html-prototype/*.html` (2026-08-13): no screen shows a notes browser, a
   tag filter, wikilink/backlink navigation, or a search box/results view.
   Per the analyst's mandatory prototype-reconciliation rule, this requires
   `gate: flagged` until a real `/design REQ-SB-02` pass produces and the
   human signs off on approved prototype screens — resolving the underlying
   requirement questions does not substitute for that design pass, since
   the exact layout/interaction shape (now bounded — link list, not graph
   canvas — but not yet drawn) is still undecided.

Separately (not itself a flag reason, but the practical next-step order):
this story is also **blocked by `REQ-SB-01-US-01`**, which is now
`gate: clear` and ready for `/plan-tasks`, but still `status: Draft` until
that pipeline stage runs — `/design REQ-SB-02` can reasonably proceed in
parallel (it does not need the index built, only the requirement's own
resolved shape, which is now settled), but `/plan-tasks REQ-SB-02` cannot
complete until `REQ-SB-01-US-01` reaches `Ready`.

**What to do:** run `/design REQ-SB-02` to produce the new notes-browser/
search screen(s) (a list view, a note-detail view with the resolved
forward-link/backlink list, and a search box + ranked-results view),
reachable from the existing app-shell sidebar (`REQ-SB-12-US-01`'s
pattern); once approved, reset `gate:` to `clear` and run `/plan-tasks
REQ-SB-02` (after confirming `REQ-SB-01-US-01` has reached `Ready`).

gate: flagged 2026-08-13, gate_reason: net-new-design-needed (only —
`unclear-requirement`/`ESC-022` is Resolved, see above). `REQ-SB-02` itself
is finalised PRD text (no `<!-- Draft -->` marker) — the flag is solely
about the missing prototype coverage, not the requirement's own
finalization state or any remaining ambiguity in its own scope.

**Update, 2026-08-13 — `/design REQ-SB-02` resolved; `/plan-tasks REQ-SB-02`
run (architect → decomposer).** `html-prototype/vault-browser.html` and
`html-prototype/note-detail.html` were produced and approved (the human
browser sign-off `/design` always requires) — the prior
`net-new-design-needed` flag's own underlying gap is closed; `gate:` was
reset to `clear` ahead of this pass (not re-narrated in a rewritten prior
paragraph, per this project's append-only convention). `REQ-SB-01-US-01`
(Vault Indexing) is confirmed `status: Ready`, `gate: clear` — this story's
build dependency is satisfied for planning purposes (not yet built, which
is fine; `/plan-tasks` designs against `ADR-024`'s already-decided index
shape, not against running code).

**Architecture:** one new ADR, **`ADR-026`** (search ranking mechanism —
field-weighted BM25-style scoring, computed at query time over
`vault_indexing.get_index()`, no new dependency, no persisted ranking
index) — the genuinely new algorithmic decision this story's own resolved
Constraint left as "/plan-tasks latitude." `architecture.md` gained a new
"Browse & Search" section (new `app/business/vault_search.py`, new
`app/api/vault_search_router.py`, a small additive `vault_indexing.py`
index-readiness accessor extending, not reopening, `ADR-024`, and the new
`VaultBrowserPage.tsx`/`NoteDetailPage.tsx` frontend). **Architecture
scope: "Browse & Search" and "Vault Indexing Layer" (read-only) in
`Implementation/Architecture/architecture.md`** — the coder is bounded to
these two sections plus `ADR-024`/`ADR-026`.

**Gate: flagged again, for an independent reason (trigger-3, this ADR).**
Per `Pipeline.md`, an ADR change always flags the story but does **not**
halt the stage — the decomposer still locked all 7 ACs (`AC-01`–`AC-07`,
above) and created `REQ-SB-02-US-01-T01`–`T04` (see Implementation Tasks)
in the same pass, so the human reviews `ADR-026` and the resulting tasks
together, in one pass, per `REVIEW-QUEUE.md`. `status:` set to `Ready`
(ACs locked, tasks created, no blocking dependency remains) — see
`REVIEW-QUEUE.md` for the pointer; whether `/plan-sprints`/
`/implement-sprint` proceed on a still-`flagged` story before a human
resolves this entry is that stage's own call, not decided here.

**Update, 2026-08-13 (`/implement-sprint` — coder, `SPRINT-026`) — Done.**
`ADR-026` was already reviewed and **Approved** in `REVIEW-QUEUE.md`
("ADR-026's field-weighted BM25 design is technically sound...") before
this build started — `gate:` reset to `clear` here, since that human
review is what this build was itself gated on and it already resolved
favorably; no rebuild needed against a changed design. All 4 tasks
(`T01`–`T04`) built and every locked AC (`AC-01`–`AC-07`) verified live
against the real, indexed vault (503 unique-stem notes; `BUG-011`'s
already-disclosed, out-of-scope filename-stem collision remains the only
known discrepancy from the raw file count, unchanged from `SPRINT-025`)
and a real browser (headless-Chrome-via-CDP, zero dependency). Full
verification detail, per AC, is in each task's own Implementation Log.

Two items surfaced during this build, both written to `REVIEW-QUEUE.md`,
neither blocking a locked AC:
1. **`T02`'s own AC-05 test-query substitution** — the task's literal
   example nonsense query (`"qwzxjklmnop_nonexistent_token_zzz"`)
   tokenizes into real English sub-words ("nonexistent", "token") that
   genuinely appear somewhere across ~500 real work emails, so it does not
   produce an empty result against the real vault — not a defect in
   `search()` (multi-term-OR matching is its own correct, specified
   behavior), just an untested example string. Substituted a genuinely
   nonexistent single alphanumeric token for the live verification; logged
   as a scope-internal assumption in `T02`'s own Implementation Log.
2. **`T04`'s own `npm run build` failure** — pre-existing, in
   `styles/agent-panel.css` (an earlier sprint's own untracked file, not
   touched by this story), unrelated to any file in this story's `##
   Files to Modify`. `npx tsc --noEmit` is clean; every locked AC was
   verified live via the dev server (this task's own specified
   verification surface). Flagged for a human decision on whether to
   fix/commit that pre-existing file.
