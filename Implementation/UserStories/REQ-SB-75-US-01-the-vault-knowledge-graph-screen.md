---
id: REQ-SB-75-US-01
title: The Vault — Real-Data Knowledge Graph Screen
requirement_ids: [REQ-SB-75]
requirement_section: "REQ-SB-75: The Vault — Real-Data Knowledge Graph Screen"
phase: P1
status: Done
gate: flagged
gate_reason: "T03 scope-internal judgement call (main.tsx touch) — see REVIEW-QUEUE.md"
sprint: "SPRINT-069"
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-75-US-01 — The Vault — Real-Data Knowledge Graph Screen

## Story

**As a** Second Brain operator
**I want** a new "The Vault" screen that renders my real, currently-indexed
vault as an interactive force-directed graph — every note a node, colored/
grouped by its real kind, every real wikilink an edge — with kind filters,
name search, and click-through to the note's real content
**So that** I can see and navigate the real shape of my knowledge base (how
Customers, Threads, Meetings, People, and Files actually connect) instead of
only ever finding one note at a time through the flat browse/search list

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-75: The Vault — Real-Data Knowledge
  Graph Screen* (P1 section, immediately after `REQ-SB-74`). No
  `<!-- Draft -->` marker — finalized text.
- **Design sign-off already happened — this story deliberately skips the
  `/design` precursor, per an explicit operator override disclosed in the
  PRD entry's own `<!-- Raised -->` comment.** Operator, 2026-08-19: "I want
  to put this Graph with a Click on it to let me see the note at some point
  as the next sprint. We are Going to Call this the Vault" — then, when
  asked whether to route through the standing `/design` precursor first:
  "No Need for Designer What we have is amazing." The sign-off happened
  live, against a real interactive artifact (drag, zoom/pan, kind filters
  with live counts, name search, click-to-select with connection
  highlighting, an inspector panel) built and iterated the same
  conversation, including a real correction (a stale light/green
  `html-prototype/styles.css` theme caught by the operator and fixed
  against the REAL current `tokens.css` dark/copper theme before this
  requirement was drafted). **This story does NOT flag for a missing
  `/design` pass or `net-new-design-needed`** — that gate is already
  satisfied. The PRD entry's own written description of the sketch is this
  story's design reference (the artifact itself is not reachable from this
  pipeline).
- **Reuse point 1, confirmed live by reading the real code, 2026-08-19:**
  `app/business/vault_indexing.py`'s `get_index()`/`_build_entry()`
  already carries every note's `stem`, `frontmatter` (a dict, `type` and
  `tags` among its keys — `app/business/vault_search.py`'s own existing
  `_kind_for(entry) -> entry["frontmatter"].get("type", "Unknown")` is the
  exact reuse point for kind derivation), `outgoing_wikilinks` (raw,
  unresolved target text — body text AND frontmatter-shaped wikilinks,
  strengthened this same session by `REQ-SB-73`'s architect pass), and
  `incoming_wikilinks` (already resolved to real stems by
  `rebuild_index()`'s own backlink-inversion pass). This story's new
  endpoint reshapes this SAME index into `{nodes, edges}` — zero new
  indexing/caching, never a second, divergent graph-construction
  mechanism, per the PRD's own Constraint 1.
- **Reuse point 2, confirmed live by reading the real code:**
  `app/api/vault_search_router.py` is the existing `/vault-search/*`
  endpoint family (`/status`, `/notes`, `/notes/{stem}`, `/search`,
  `/tags`, `/scope-suggestions`) — all delegating to
  `app/business/vault_search.py`/`vault_indexing.py` only, HTTP-only, no
  filesystem access of its own (`ADR-003`). This story's new graph
  endpoint is ADDITIVE to this SAME router/module family — never a new
  router or module. Exact route name/mechanism (a new
  `vault_search.py` function + router path) is left to the architect at
  `/plan-tasks` — see `## Notes`.
- **Reuse point 3, confirmed live by reading the real code:**
  `src/frontend/src/App.tsx`'s route table already has
  `<Route path="/browse/:stem" element={<NoteDetailPage />} />`, and
  `src/frontend/src/pages/NoteDetailPage.tsx` already calls
  `fetchNoteDetail(stem)` (from
  `src/frontend/src/features/vault-browser/client.ts`) and renders the
  real note's title/kind/tags/forward-links/backlinks. **Both are reused
  completely unmodified** — clicking a Vault node navigates to this
  EXISTING route; this story invents no new note-viewing mechanism, per
  the PRD's own Constraint 3.
- **Node kind, per the PRD's own Constraint 4:** derived from existing
  `frontmatter`/`tags` only (the SAME `type` field `_kind_for` already
  reads) — no new classification pass. Directly confirmed against the real
  corpus (`src/backend/app/data_access/vault_writer.py`) that `type` values
  in real use include at least `File`, `Customer`, `Person`, `Meeting`,
  `Thread` (the PRD's named 5 kinds) plus others (`Partner`, `RawMessage`,
  `Task`, `Research`) — every real note still renders as a node (the PRD's
  own "every real note" acceptance text), grouped/colored by its own real
  `type` value; the 5 named kinds are only what the PRD requires the
  click-through to be demonstrated against, not an exhaustive allowlist
  that would silently drop other real notes. Whether the filter/kind-chip
  UI needs a small `type`/tag → fixed-kind mapping table, or renders
  whatever `type` values actually exist, is a mechanism question left to
  the architect — see `## Notes`.
- **Explicitly deferred, per the PRD's own text — not this story's scope:**
  any new note-detail rendering/editing beyond what `/browse/:stem`
  already does; the "Vault Browser" vs. "The Vault" naming overlap
  (flagged live to the operator, not yet resolved, explicitly non-blocking
  for this requirement); large-corpus performance work (neighborhood
  scoping/clustering) — explicitly out of scope at the vault's current real
  scale (~680 notes).

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: Every real note in the vault renders as a node, grouped/colored by its own real kind

```gherkin
Given the real, currently-indexed vault (vault_indexing.get_index()), whose
    notes carry real frontmatter type values (e.g. Customer, Thread,
    Meeting, Person, File, and any other real type in current use)
When the operator opens The Vault screen
Then every real indexed note renders as exactly one node
  And each node is colored/grouped according to its own real kind, derived
    from that note's own frontmatter (the same type field vault_search.py's
    _kind_for already reads) — never a fabricated or default-for-everyone
    kind
```
<!-- AC-ID: REQ-SB-75-US-01-AC-01 -->

### Scenario 2: Every real wikilink between two indexed notes renders as one real edge

```gherkin
Given two real indexed notes, A and B, where A's outgoing_wikilinks
    resolves (case-insensitively, by stem) to B
When the operator opens The Vault screen
Then a real edge renders connecting A's node to B's node
  And no edge renders for a wikilink target that does not resolve to any
    real indexed note's stem (an honest, silent omission — the same
    "unresolved target is never fabricated" posture vault_indexing.py's
    own rebuild_index() already applies to backlinks)
```
<!-- AC-ID: REQ-SB-75-US-01-AC-02 -->

### Scenario 3: Unchecking a kind filter fully hides that kind's nodes and edges — never merely dims them

```gherkin
Given The Vault screen is showing nodes of multiple real kinds
When the operator unchecks one kind's filter (e.g. Meeting)
Then every node of that kind is fully removed from the visible graph, not
    just dimmed or faded
  And every edge that touched a now-hidden node is also fully hidden
  And the kind filter's own live count for that kind reflects the hidden
    node count
When the operator re-checks that kind's filter
Then that kind's nodes and edges reappear exactly as before
```
<!-- AC-ID: REQ-SB-75-US-01-AC-03 -->

### Scenario 4: Name search narrows the visible graph to matching notes

```gherkin
Given The Vault screen is showing the full real graph
When the operator types a search term into the name search field
Then only nodes whose real title/stem matches the search term remain
    visible, exactly as the verified sketch's own search behavior
When the operator clears the search field
Then the full real graph is shown again
```
<!-- AC-ID: REQ-SB-75-US-01-AC-04 -->

### Scenario 5: Clicking a node navigates to that note's real content at /browse/:stem, for at least one node of each of the 5 named kinds

```gherkin
Given The Vault screen is showing at least one real node of each of
    Customer, Thread, Meeting, Person, and File kind
When the operator clicks any one node
Then the app navigates to the existing /browse/:stem route for that node's
    own real stem
  And the existing, unmodified NoteDetailPage renders that note's real
    title, kind, tags, forward links, and backlinks — no new note-viewing
    mechanism
  And this holds for at least one node of each of the 5 named kinds
```
<!-- AC-ID: REQ-SB-75-US-01-AC-05 -->

### Scenario 6: The screen renders entirely through real tokens.css values — zero hardcoded colors

```gherkin
Given The Vault screen's own stylesheet/inline styles
When inspected
Then every color value used (node fill per kind, edge stroke, background,
    filter chips, search field, inspector panel) resolves through a real
    tokens.css custom property
  And no color value is hardcoded outside tokens.css
```
<!-- AC-ID: REQ-SB-75-US-01-AC-06 -->

## Affected Screens

- **No `html-prototype/` file exists for The Vault** — its design was
  validated directly against a live, interactive HTML/CSS/JS Artifact built
  and iterated in the same conversation that raised this requirement (an
  Artifact, not a saved `html-prototype/` screen), per the operator's own
  explicit override of the normal `/design`-first convention (see
  `## Context`). This story's design reference is the PRD entry's own
  written description of that Artifact's real interactions — see
  `## Notes` → *Design reference parity* below. A saved
  `html-prototype/the-vault.html` companion file is NOT required by this
  story; the architect/coder may optionally add one for future parity, but
  its absence is not a gap in this story.

## Dependencies

- **Blocked by (hard):** `REQ-SB-01` (Vault Indexing, `Done`) —
  `vault_indexing.get_index()` this story's new endpoint reshapes,
  unmodified.
- **Blocked by (hard):** `REQ-SB-02` (Browse & Search, `Done`) —
  `/browse/:stem`/`NoteDetailPage`/`fetchNoteDetail` this story navigates
  to, unmodified.
- **Related to:** `REQ-SB-73` (Bidirectional Thread ↔ Message Linking,
  `Draft`) — the frontmatter-wikilink scanning strengthening
  `outgoing_wikilinks` this story's edges benefit from directly (no code
  dependency; same underlying index).
- **External:** none new.

## Constraints

- **Zero new indexing/caching** — reuses `vault_indexing.get_index()`
  directly; never a second, divergent graph-construction mechanism.
- **Additive endpoint under the existing `/vault-search/*` family** — never
  a new router or module.
- **No new note-viewing mechanism** — clicking a node navigates to the
  existing, unmodified `/browse/:stem` route.
- **Node kind is derived from existing frontmatter/tags only** — no new
  classification pass.
- **Kind filter unchecking must fully hide, never merely dim** — nodes and
  their edges.
- **Zero hardcoded colors** — every visual value resolves through
  `tokens.css` (`src/frontend/src/styles/tokens.css`).
- **Large-corpus performance work (neighborhood scoping/clustering) is
  explicitly out of scope** at the vault's current real scale (~680
  notes).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Analyst-authored starting point, non-authoritative — the decomposer's
own table at /plan-tasks supersedes this. Task count/shape is provisional
until the architect resolves the mechanism-level open questions in ## Notes
(endpoint name, kind-mapping mechanism, frontend route/nav naming). -->

<!-- Decomposer's table (2026-08-19) — supersedes the analyst's provisional
table above per this file's own note. Task shape follows the architect's
resolved mechanism (see the "Architect pass" section above): one backend
reshape+endpoint task, then a strict two-step frontend chain (rendering
engine → page assembly/route/nav) since the page cannot be built or
verified without the real endpoint (T01), and the page cannot be built or
verified without the canvas/physics/client layer (T02) it composes —
mirrors this project's own established "backend-layer-first, then build
the frontend against the real, running endpoint" precedent
(`SPRINT-019`/`SPRINT-049` Learnings). -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-75-US-01-T01 | backend | `vault_search.get_graph()` reshaping `vault_indexing.get_index()` into `{nodes, edges}` (nodes via existing `_summary()`; edges via the existing `_resolve_forward_links`/`ADR-024` case-insensitive stem-matching rule, dangling/self targets silently omitted) + new `GET /vault-search/graph` endpoint | `app/business/vault_search.py`, `app/api/vault_search_router.py` | `../Tasks/REQ-SB-75-US-01-T01-graph-reshape-and-endpoint.md` |
| REQ-SB-75-US-01-T02 | frontend | Rendering engine — `forceLayout.ts` (pure physics), `VaultGraphCanvas.tsx` (hand-rolled `<canvas>` + `requestAnimationFrame` force-directed layout, drag/zoom/pan, click-to-navigate via `useNavigate()`), `features/vault-graph/client.ts` (thin fetch wrapper), new `tokens.css` kind-color-palette + edge-color custom properties | `src/frontend/src/features/vault-graph/`, `src/frontend/src/styles/tokens.css` | `../Tasks/REQ-SB-75-US-01-T02-vault-graph-canvas-and-client.md` |
| REQ-SB-75-US-01-T03 | frontend | `VaultGraphPage.tsx` — fetches via `client.ts`, mounts `VaultGraphCanvas`, kind filter chips with live counts (fully hide, never dim), name search, new `vault-graph.css` (tokens.css-only); route `/vault` in `App.tsx`, nav entry "The Vault" in `Sidebar.tsx` | `src/frontend/src/pages/VaultGraphPage.tsx`, `src/frontend/src/App.tsx`, `src/frontend/src/components/shell/Sidebar.tsx`, `src/frontend/src/styles/vault-graph.css` | `../Tasks/REQ-SB-75-US-01-T03-vault-graph-page-and-nav.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — manual mode still in effect, per `Implementation/Pipeline.md` (real live browser/HTTP verification performed for every locked AC, per manual mode)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints (n/a — no new decision/pattern/constraint emerged; see each task's own Implementation Log)
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Any new note-detail rendering, editing, or note-content interaction**
  beyond what `/browse/:stem`/`NoteDetailPage` already does today.
- **Resolving the "Vault Browser" vs. "The Vault" naming overlap** — both
  names may coexist for now; flagged to the operator, not decided here.
- **Large-corpus performance work** (neighborhood scoping / clustering
  instead of rendering every note at once) — a real, disclosed future
  concern, explicitly out of scope at the vault's current real scale.
- **A new `html-prototype/` screen file** — design sign-off already
  happened against a live Artifact; not required by this story.

## Notes

**Design reference parity** (the PRD entry's own written description of the
verified live Artifact — the artifact itself is unreachable from this
pipeline, so this is the design reference of record):

- **Force-directed canvas (drag/zoom/pan)** — Specced, Scenario 1/2 (node/
  edge rendering); the drag/zoom/pan interaction mechanics themselves are
  implementation detail within T02, not separately AC'd (no observable
  business outcome distinct from "the graph renders and is navigable").
- **Kind filters with live counts** — Specced, Scenario 3.
- **Name search** — Specced, Scenario 4.
- **Click-to-select with connection highlighting** — the click-to-navigate
  half is Specced, Scenario 5; the connection-highlighting visual (pre-
  navigation hover/select state) is Deferred to T03/coder-level polish —
  the PRD's own Acceptance paragraph does not name a highlighting
  assertion, only click-to-navigate, so no scenario locks a specific
  highlighting behavior here.
- **Inspector panel** — Deferred to T02/coder-level detail — the PRD's own
  Acceptance paragraph does not assert a specific inspector-panel
  behavior distinct from Scenario 5's click-to-navigate outcome (the PRD
  frames navigation to the real note, via `/browse/:stem`, as the
  intended "inspect" outcome, not a separate on-canvas panel with its own
  new content). If an on-canvas inspector panel is also desired as a
  peek-before-navigate affordance, that is a coder-level enhancement
  within T02, not a locked AC — the PRD's Acceptance text does not
  require it.
- **App's real dark/copper theme, `tokens.css`, `.cockpit-layout` 3-column
  recipe** — Specced, Scenario 6 (zero hardcoded colors) plus the
  Constraints table above; the 3-column layout recipe itself is a T02
  implementation choice, not independently AC'd (no distinct observable
  outcome beyond "renders correctly, tokens.css-only").

**Mechanism-level questions left to `/plan-tasks`, not resolved by this
pass** (the Gherkin above specifies the OUTCOME, not the mechanism):

1. **Exact new endpoint path/name** under the existing `/vault-search/*`
   family (e.g. `/vault-search/graph`) — left to the architect.
2. **Whether node "kind" derivation needs a small mapping table** from
   `type`/tags to a fixed kind enum (for consistent filter-chip
   ordering/coloring), or renders whatever real `type` values exist
   directly — left to the architect.
3. **Frontend route path and nav-entry naming** (e.g. `/vault`,
   `/the-vault`) — left to the architect, informed by the still-open
   "Vault Browser" vs. "The Vault" naming question the PRD itself defers.
4. **The "Vault Browser" vs. "The Vault" naming overlap** — the PRD
   explicitly flags this as unresolved-but-non-blocking; not resolved
   here, not blocking `/plan-tasks`.

**Why this does NOT trip trigger 1 (material assumption):** every open
item above is a MECHANISM question this project's own role boundaries
assign to the architect at `/plan-tasks`; the PRD's own text (plus this
pass's own direct reading of `vault_indexing.py`, `vault_search.py`,
`vault_search_router.py`, `App.tsx`, `NoteDetailPage.tsx`) resolves every
SCOPE-level question directly: what renders, how kind filters/search
behave, where clicks navigate, and the theme constraint. This pass adds no
scope the PRD did not already state.

**Why this does NOT trip trigger 2:** `REQ-SB-75` carries no
`<!-- Draft -->` marker in the PRD — finalized text.

**Why this does NOT trip trigger 3:** N/A — ADR creation/change is the
architect's own trigger, not this role's.

**Why this does NOT trip trigger 4:** no `ESCALATIONS.md` entry was
written — nothing in this pass is a backward pipeline step or an
out-of-scope event.

**Why this does NOT trip trigger 5 (oversized):** 3 starting tasks (one
additive backend reshape + endpoint, two frontend screen tasks) — small,
comparable to this project's own smaller recent stories; not oversized.

**Why this does NOT trip trigger 7:** no contradictory PRD inputs found —
direct reading of the real, already-shipped `vault_indexing.py`,
`vault_search.py`, `vault_search_router.py`, `App.tsx`, and
`NoteDetailPage.tsx` confirms every reuse point the PRD names (the index's
own fields, the `/vault-search/*` family, the `/browse/:stem` route, and
`_kind_for`'s existing `type`-field convention) already exists exactly as
described, with no discrepancy.

**Why this does NOT trip trigger 8 (multiple equally-valid / unclear):**
the PRD's own text does not leave this requirement's SCOPE unclear — it
explicitly names the 4 acceptance behaviors (render every note as a node
by kind with real edges; kind filters/search fully hide, not dim;
click-through to `/browse/:stem` for each of the 5 named kinds; zero
hardcoded colors) and explicitly resolves the two items that could
otherwise look like open scope questions (naming overlap, large-corpus
performance) as deliberately deferred, non-blocking. What remains open
(items 1–3 above) are MECHANISM choices, not competing SCOPE
interpretations.

**Why this does NOT need a `/design` flag / `net-new-design-needed`:** the
operator's own explicit, disclosed override ("No Need for Designer What we
have is amazing") already satisfies this project's design-sign-off gate
for this requirement — sign-off happened live against a real interactive
artifact this same conversation, per the PRD entry's own `<!-- Raised -->`
comment. Flagging for a missing `/design` pass here would contradict that
disclosed operator decision.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired (see the itemized
trigger-by-trigger reasoning above).

---

## Architect pass (`/plan-tasks` step 1, 2026-08-19)

Resolved the 4 mechanism-level questions this story's own `## Notes` left
open, all as pure compositions of already-`Accepted` `ADR-003`/`ADR-010` —
**no new ADR written, no contradiction found:**

1. **Endpoint:** `GET /vault-search/graph` → new `vault_search.get_graph()`
   → `{"nodes": [...], "edges": [...]}`. Nodes reuse `_summary()` verbatim
   (`stem`/`title`/`kind`/`tags`); `kind` is `_kind_for(entry)` directly, no
   wrapper. Edges resolve `outgoing_wikilinks` via the same case-insensitive
   stem-matching rule `ADR-024`/`_resolve_forward_links` already use;
   dangling/self targets silently omitted. No pagination/filter params —
   kind counts and name search are a client-side-only concern over the one
   fetched snapshot.
2. **Kind derivation:** direct reuse of `vault_search.py`'s own
   `_kind_for(entry)` — no wrapper, no fixed-enum mapping table. Every real
   `type` value in current use renders as its own kind.
3. **Frontend route/nav:** new `pages/VaultGraphPage.tsx`, route `/vault`,
   nav label **"The Vault"** (`Sidebar.tsx`, placed after the existing
   "Browse & Search" item). Naming-overlap concern resolved, not just
   deferred: direct reading of the real `Sidebar.tsx` confirms the existing
   `/browse` item's own on-screen label is "Browse & Search," never "Vault
   Browser" — no actual on-screen collision exists today. This screen's own
   component/feature names (`VaultGraphPage.tsx`, `features/vault-graph/`)
   are deliberately distinct from `VaultBrowserPage`/`vault-browser` at the
   code level too, so no future collision is introduced by this story.
4. **Frontend implementation:** hand-rolled `<canvas>` + `requestAnimationFrame`
   force-directed physics (new `VaultGraphCanvas.tsx` + `forceLayout.ts`
   under `features/vault-graph/`) — zero new npm dependency. Confirmed
   against the real, current `src/frontend/package.json`: no graph/
   visualization library exists today (`react`/`react-dom`/`react-markdown`/
   `react-router` only); none is added. Not a reuse of `AgentsMapCanvas.tsx`
   (a structurally different, non-physics SVG+div radial layout) — a new
   sibling "one component owns one bespoke visualization" instance.

**Full reasoning, field shapes, and file list:** see
`Implementation/Architecture/architecture.md` → **"The Vault — Knowledge
Graph Screen (REQ-SB-75-US-01, no new ADR)"** (appended directly after
"Browse & Search" → "Tag/Folder Scope Suggestions").

**Architecture scope:** §The Vault — Knowledge Graph Screen
(REQ-SB-75-US-01, no new ADR), §Browse & Search (REQ-SB-02-US-01) —
specifically `app/business/vault_search.py` / `app/api/
vault_search_router.py`, §Frontend Application Architecture (routing/
styling/data-fetching conventions, `ADR-010`) — the sections the decomposer
and coder are bounded by.

**Why this does NOT trip trigger 3:** no ADR was created or changed — every
decision above is a pure composition of already-`Accepted` `ADR-003` and
`ADR-010`, neither reopened, no new tool/framework/storage/trust-surface.

**Why this does NOT trip an escalation:** no contradiction found against
any `Accepted` ADR, the PRD, or a `MEMORY.md` constraint — direct reading of
`vault_indexing.py`, `vault_search.py`, `vault_search_router.py`, `App.tsx`,
`Sidebar.tsx`, and `package.json` confirmed every reuse point and the
"zero new dependency" decision before locking it in.

gate: clear 2026-08-19 — architect pass, no MUST-FLAG trigger fired (no ADR
touched, no contradiction found).

**What to do next:** eligible for the decomposer (`/plan-tasks` step 2) to
lock ACs and write tasks against the architecture scope above.

---

## Decomposer pass (`/plan-tasks` step 2, 2026-08-19)

**AC authoring + locking.** The analyst/architect's Gherkin was already
tight and buildable — no wording changes needed beyond assigning IDs.
Locked all 6 scenarios verbatim, sequential IDs
`REQ-SB-75-US-01-AC-01`..`AC-06` (one per scenario, in document order):

- `AC-01` — Scenario 1 (every real note renders as a node, colored/grouped
  by its own real kind)
- `AC-02` — Scenario 2 (every real, resolved wikilink renders as an edge;
  dangling/self targets silently omitted)
- `AC-03` — Scenario 3 (unchecking a kind filter fully hides, never dims,
  that kind's nodes+edges; live count reflects it; re-checking restores)
- `AC-04` — Scenario 4 (name search narrows the visible graph; clearing
  restores it)
- `AC-05` — Scenario 5 (clicking a node navigates to the existing
  `/browse/:stem` route, for at least one node of each of the 5 named
  kinds)
- `AC-06` — Scenario 6 (every color value resolves through a real
  `tokens.css` custom property — zero hardcoded colors)

All 6 are **locked** (no `locked: false` exceptions — every scenario has an
unambiguous, DOM/HTTP-observable outcome; none is pure-visual polish, per
this role's own "structural, not visual" boundary).

**Node-kind color mechanism (task-level design decision, not a new ADR):**
the vault's real `type` values are open-ended (`AC-01` — every real kind
renders as its own kind, never coerced into a fixed 5-kind enum), so
`AC-06`'s "zero hardcoded colors" cannot be satisfied by a fixed
kind-name → hex mapping. `T02` adds a small **rotating palette** of new
`tokens.css` custom properties (`--graph-kind-color-1`..`-8`, values drawn
from this app's own already-established curated palette —
`visualOptions.ts`'s `VISUAL_COLORS` / the existing `--agent-color-*`,
`--color-success`, `--color-warning`, `--color-danger` tokens, not new
arbitrary hues) plus one `--graph-edge-color` token; a deterministic
string-hash of each note's real `kind` value picks one of the 8 palette
slots. This generalizes to any future real `type` value with zero code
change, and keeps every color sourced from `tokens.css` (read via
`getComputedStyle`, since `<canvas>` has no CSS cascade) — an ordinary
extension of the already-established `--agent-color-*` rotating-palette
pattern in the same file, not a new architectural decision.

**Task files created (flat root, `Implementation/Tasks/`):**

| Task | depends_on | Locked ACs covered (Tests block) |
|---|---|---|
| `REQ-SB-75-US-01-T01` | — | `AC-01`, `AC-02` (real HTTP call against the real vault) |
| `REQ-SB-75-US-01-T02` | `T01` | non-AC smoke checks only (rendering engine — no independent screen-level observable yet, same posture as `REQ-SB-38-US-01-T02`'s own CSS-port precedent) |
| `REQ-SB-75-US-01-T03` | `T02` | `AC-01`..`AC-06` (full real screen at `/vault`, real backend, real navigation — the integration point where every scenario's own "operator opens The Vault screen" / "clicks a node" Given/When is actually observable) |

`AC-01`/`AC-02` are deliberately **verified twice** — once cheaply at the
backend layer (`T01`, real HTTP call, no browser needed) and once at the
full screen level (`T03`) — mirroring this project's own established
"layer-by-layer live verification, cheapest layer first" pattern
(`SPRINT-019`/`SPRINT-026` Learnings). No cycle: `T01 → T02 → T03`, a
strict chain.

**Dependency-graph summary:** `REQ-SB-75-US-01-T01` (no deps) →
`REQ-SB-75-US-01-T02` (depends on `T01`) → `REQ-SB-75-US-01-T03` (depends
on `T02`). Acyclic, single chain — condition (c) for the `Ready`
transition holds.

**Status transition:** all 6 ACs locked (a), every locked AC has ≥1
tagged step across the task set (b — see table above), `depends_on` is
acyclic (c). All three conditions hold → story `status: Draft → Ready`.
Every task file is written at `status: Ready` in lockstep (not `Draft`),
per this role's own "status moves in lockstep" rule, so
`/plan-sprints`/`/implement-sprint` pick them up.

**MUST-FLAG check (all 8 triggers) — none fired, `gate: clear`:**

1. No material assumption — every scope question was already resolved by
   the analyst/architect; the only decomposer-level design choice (the
   rotating kind-color palette, above) is an ordinary implementation-level
   extension of an already-established `tokens.css` pattern, not a gap-fill
   assumption.
2. `REQ-SB-75` carries no `<!-- Draft -->` marker — finalized PRD text
   (reconfirmed).
3. No ADR created or changed by this pass (decomposer never touches ADRs).
4. No `ESCALATIONS.md` entry written this pass.
5. Not oversized — 3 tasks, comparable to this project's own smaller
   recent stories (`SPRINT-023`/`SPRINT-024`/`SPRINT-050`, all 3-task/S).
6. Every locked AC has a concrete, observable, verifiable outcome (real
   HTTP JSON shape; real DOM node/edge count and count text; real URL
   navigation; real computed CSS custom-property resolution) — none is
   unverifiable.
7. No contradictory inputs — the architect's resolved mechanism and the
   real, current code (`vault_search.py`, `vault_search_router.py`,
   `App.tsx`, `Sidebar.tsx`, `tokens.css`, `visualOptions.ts`,
   `package.json`) were all read directly before writing these tasks; no
   discrepancy found.
8. No multiple equally-valid breakdowns / no genuine ambiguity — the
   architect's own mechanism resolution left one natural task shape (a
   strict backend → rendering-engine → page chain); the only open
   implementation choice (kind-color palette mechanism) has one clear,
   precedent-following answer, not a fork.

gate: clear 2026-08-19 — decomposer pass, no MUST-FLAG trigger fired (see
itemized reasoning above). Story advances `Draft → Ready`.

**What to do next:** eligible for `/plan-sprints` (Ready, ungrouped,
dependency-acyclic).

---

## Coder pass (`/implement-sprint SPRINT-069`, 2026-08-19)

All 3 tasks built in strict dependency order (`T01 → T02 → T03`), all
`Done`. All 6 locked ACs verified live against the real backend
(`GET /vault-search/graph`, real 686-note/1467-edge vault) and the real,
running frontend at `/vault` (headless-Edge/CDP, screenshots + React
Fiber state reads — see each task's own `## Implementation Log` for full
evidence):

- `AC-01` — PASS (backend layer, `T01`; screen layer, `T03`)
- `AC-02` — PASS (backend layer, `T01`; screen layer, `T03`)
- `AC-03` — PASS (`T03`, ground-truth DOM/screenshot evidence — see `T03`'s
  own disclosed testing-technique finding about a Fiber-introspection
  false negative, not a product defect)
- `AC-04` — PASS (`T03`)
- `AC-05` — PASS, all 5 named kinds (`T03`)
- `AC-06` — PASS (`T03`)

**One scope-internal judgement call, disclosed and flagged for human
spot-check** (`T03` — `src/frontend/src/main.tsx` touched outside its own
`## Files to Modify` list, to wire the new `vault-graph.css` import; see
`REQ-SB-75-US-01-T03`'s own `## Implementation Log` and the
`REVIEW-QUEUE.md` entry). No escalation, no ADR touched, no blocked task.

Status: `Ready → Done`. `gate: flagged` (the `T03` spot-check item above)
— not a blocker, no locked AC failed.
