---
id: SPRINT-026
title: Browse & Search — tag filter, wikilink navigation, ranked keyword search
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "retro-harvest — human skims retrospective, propagates Learnings.md"
phase: MVP                         # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-025]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~4 tasks, M"      # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-08-13
started: "2026-08-13"              # YYYY-MM-DD when status → In Progress
completed: "2026-08-13"            # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — who drives each transition:
     Draft       → product-owner assembles the sprint. Bidirectional link is written
                   at creation: every story listed here already has sprint: SPRINT-NNN.
     Ready       → product-owner advances Draft→Ready when grouping is CLEAR (gate: clear).
                   Ambiguous, oversized, or blocked grouping stays Draft + gate: flagged.
                   Adding a story to a Ready sprint AUTO-REVERTS it to Draft.
     In Progress → /implement-sprint has started. Coder sets this + records started:.
     Blocked     → external dependency is unmet. Record it under Dependencies.
     Done        → every story is Done and every DoD box is checked. Coder sets this,
                   records completed:, DRAFTS the retrospective, and sets gate: flagged
                   for the human to skim and harvest Learnings.md.
-->

# SPRINT-026 — Browse & Search

## Sprint Goal

Build `REQ-SB-02-US-01`'s human-facing browse/search surface — list/filter
the indexed vault by tag, navigate a note's forward/back wikilinks, and run
a field-weighted BM25-style ranked keyword search — end to end (backend
query logic through the new frontend pages).

---

## Grouping Rationale & Sizing

- **Why grouped:** single-story sprint — `REQ-SB-02-US-01` is the only story
  assigned here. Its 4 tasks form one straight dependency chain
  (`T01 → T02 → T03 → T04`), and all of it (ranking algorithm, API, and two
  new frontend pages) belongs to one cohesive "Browse & Search" architecture
  scope (`ADR-026`) — no reason to split across sprints internally.
- **Why sequenced behind `SPRINT-025`, not combined with it:** this story's
  own first task, `REQ-SB-02-US-01-T01`, carries a real, decomposer-recorded
  cross-story edge — `depends_on: [REQ-SB-01-US-01-T02]` — confirmed by
  direct reading of `Implementation/Tasks/
  REQ-SB-02-US-01-T01-index-readiness-and-browse-query-logic.md`. This
  story's list/filter/navigate/search all read from `REQ-SB-01-US-01`'s
  index; it cannot be meaningfully built until that story's core index
  module exists. Per hard rule 7, this is honoured via a
  `depends_on_sprints: [SPRINT-025]` edge (ordered sprints) rather than
  same-sprint sequencing — see `SPRINT-025`'s own Grouping Rationale for why
  one combined 8-task sprint was rejected as oversized/mixed-surface for a
  single working context.
- **Sizing estimate:** ~4 tasks, M. `T01` (index-readiness signal +
  browse/tag-filter/note-detail query logic) → `T02` (ranked search,
  field-weighted BM25-style, per `ADR-026`) → `T03` (API surface) → `T04`
  (frontend — `VaultBrowserPage.tsx` **and** `NoteDetailPage.tsx`, plus a
  new API client and nav wiring). Only 4 tasks, but `T04` alone carries
  genuinely new UI surface across two pages (list/filter, note detail with
  forward/back links, search box + ranked results, the empty/not-yet-
  indexed state) — heavier per-task than `SPRINT-025`'s pure-backend chain,
  closer to `SPRINT-009`'s (~7 tasks, M) per-task weight than to a plain S
  sprint.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-026 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-02-US-01](../UserStories/REQ-SB-02-US-01-browse-and-search.md) | Browse & Search — list/filter the indexed vault by tag, navigate the wikilink graph, and run ranked keyword search | MVP | Done |

**Tasks in scope** (dependency order): [[REQ-SB-02-US-01-T01]]
(index-readiness signal + browse/tag-filter/note-detail query logic —
`app/business/vault_indexing.py` (additive) + new `app/business/
vault_search.py`, `depends_on: [REQ-SB-01-US-01-T02]` — **cross-sprint**),
[[REQ-SB-02-US-01-T02]] (ranked search, field-weighted BM25-style —
`vault_search.py::search()`, per `ADR-026`, `depends_on: [T01]`),
[[REQ-SB-02-US-01-T03]] (API surface — new `app/api/
vault_search_router.py`, `depends_on: [T01, T02]`), [[REQ-SB-02-US-01-T04]]
(frontend — `VaultBrowserPage.tsx` + `NoteDetailPage.tsx`, `features/
vault-browser/client.ts`, nav wiring, `depends_on: [T03]`).

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-025` (Vault Indexing) — must be `Done`
  before `/implement-sprint` may start this sprint; `REQ-SB-02-US-01-T01`'s
  own `depends_on: [REQ-SB-01-US-01-T02]` is the real, task-level ground
  truth for this edge.
- No other external blocker — the approved prototype
  (`html-prototype/vault-browser.html`, `html-prototype/note-detail.html`)
  and `ADR-026` are both already in place (`REVIEW-QUEUE.md`, approved
  2026-08-13).

---

## Out of Scope

- Building the index itself — `SPRINT-025`/`REQ-SB-01`.
- Semantic/embedding search, chunking, or reranking — `REQ-SB-06` (P2).
- A visual/interactive wikilink-graph canvas — resolved out of scope for
  this story (a textual, clickable forward-link/backlink list is the full
  wikilink-navigation scope).
- Editing notes from within Second Brain's UI, or any agent-facing MCP
  search tool — both explicitly out of this story's own scope.

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — n/a, already updated at `/plan-tasks` time (this sprint built exactly what that pass specified, no further architectural fact changed)
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-026`, already `Accepted` and human-reviewed/approved before this sprint's build started
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Retrospective

<!-- Filled in by the CODER when status: Done. -->

### Sizing accuracy

- **Estimated:** ~4 tasks, M — **Actual:** 4 tasks, M — matched. `T04`
  (frontend) was genuinely the heaviest task as predicted, but not
  disproportionately so; the straight `T01 → T02 → T03 → T04` dependency
  chain meant zero rework/reordering.

### What worked

- **Reading the real, current `vault_indexing.py` before writing
  anything** (per this run's own explicit instruction) confirmed the
  task files' own sample entry shape was still exactly accurate — zero
  drift since `SPRINT-025`, so `T01`'s additive edit and `T02`'s
  `vault_writer.read_note()` composition both worked on the first try
  with no adjustment needed.
- **Layer-by-layer live verification** (Python-shell function calls for
  `T01`/`T02`, real HTTP round-trips for `T03`, real browser for `T04`)
  caught every issue at the cheapest possible layer — e.g. the BM25
  multi-term-OR tokenization behavior (see Antipatterns) was found and
  understood at the Python-shell layer, before it could have surfaced as
  a confusing UI-layer discrepancy.
- **The zero-dependency headless-Chrome-via-CDP pattern** (`MEMORY.md`
  Patterns, reused verbatim from `SPRINT-008`/`SPRINT-009`/etc.) continued
  to work cleanly for a genuinely new screen pair — a Node v22 script
  using only built-in `fetch`/`WebSocket` drove real multi-hop SPA
  navigation (tag filter → search → note detail → backlink → another note
  detail) and captured real screenshots for direct visual review against
  the approved prototype, with no new tooling installed.
- **Disclosed, reverted client-side `window.fetch` stubs** (this
  codebase's own established "temporary-stub-and-revert" pattern, first
  used for AC states real data can't produce naturally) worked cleanly
  from *outside* the page too, via `Runtime.evaluate` — both for the
  zero-tag-match state (no real zero-match tag existed in the live vault
  at verification time) and the unindexed-backend state (AC-07).
- **Scoping the CDP-driven headless-Chrome kill to the specific launched
  PID tree** (`taskkill /PID <own-pid> /T /F`, not `/IM chrome.exe`)
  avoided `SPRINT-009`'s own documented antipattern of a blanket
  image-name kill risking a real user Chrome window or another concurrent
  session's own verification instance — many other real `chrome.exe`
  processes were confirmed still running afterward, untouched.

### What didn't work

- **The React-controlled-input `.value =` assignment trap, again.** The
  first CDP verification pass silently failed to trigger the search box's
  `onChange` (plain `input.value = ...` + a dispatched `'input'` event
  leaves React's internal value-tracker already in sync, so no state
  update fires) — diagnosed only after adding a debug pass with
  `Console`/`Runtime.exceptionThrown` listeners and comparing against a
  working control case. Fixed by using the native
  `HTMLInputElement.prototype.value` setter via
  `Object.getOwnPropertyDescriptor(...).set.call(input, value)` before
  dispatching `'input'` — the standard React-controlled-input CDP-testing
  workaround. Cost one extra debug round-trip; worth carrying forward as a
  named pattern so a future task doesn't rediscover it from scratch.
- **A `Page.reload()` inside a CDP script silently wipes any in-page
  `window.fetch` stub**, since it creates a fresh JS execution context —
  the first AC-07 attempt (unindexed-state stub) produced a false
  negative (the stub never took effect, `unindexed state present: false`)
  before this was diagnosed. Fixed by triggering an SPA-internal
  client-side remount instead (click a different nav link, then click
  back) — the stub survives because the JS context never actually
  reloads, only the target React component unmounts/remounts.
- **The task's own literal AC-05 example query
  (`"qwzxjklmnop_nonexistent_token_zzz"`) does not actually produce an
  empty result against this specific real, ~500-note vault** — its
  underscore-separated sub-words ("nonexistent", "token") are real English
  words that genuinely appear in real work-email bodies, and BM25's
  multi-term query is a term-union (any one matching term contributes a
  score), which is `search()`'s own correct, specified behavior, not a
  defect. A single alphanumeric nonsense token with no real-word
  sub-strings was substituted for the live check. Worth a `Learnings.md`
  entry: a decomposer-authored "known-empty" test query against a large,
  organically-grown real content corpus needs to be a single unbroken
  token (or otherwise verified not to decompose into real words), not
  assumed empty by construction.

### Patterns to carry forward

- **React-controlled-input CDP verification** — always set values via the
  native `HTMLInputElement.prototype.value` setter (`Object.
  getOwnPropertyDescriptor(window.HTMLInputElement.prototype,
  'value').set.call(input, value)`) before dispatching a synthetic
  `'input'` event, not a plain `.value =` assignment — the latter silently
  no-ops against React's own internal value tracker.
- **SPA-internal remount (nav-away/nav-back), not `Page.reload()`, to
  re-trigger a component's mount-time effect while keeping an in-page
  `window.fetch`/monkeypatch stub alive** — a hard reload wipes any
  same-context JS override; a client-side route change does not.
- **Scope a CDP-launched headless Chrome's own cleanup kill to its
  specific PID tree** (`taskkill /PID <pid> /T /F`), never `/IM
  chrome.exe` — this project's own `SPRINT-009` antipattern, reconfirmed
  worth actively avoiding rather than merely remembered.

### Antipatterns to avoid

- **Trusting a decomposer-authored "matches nothing" example query
  verbatim against a large, real, organically-grown text corpus** without
  first checking whether its sub-tokens happen to be real, common words —
  verify (or substitute a genuinely opaque single token) before relying on
  it as an AC-05-style "honest empty result" test case.
- **Silently trusting a first no-op CDP interaction** (e.g. a click or
  input that appears to run without error but produces no visible state
  change) instead of adding `Console`/`Runtime.exceptionThrown` listeners
  and a minimal debug harness the moment a result looks suspicious (empty
  where real data was expected) — cost real time to notice both root
  causes above; both would have been faster to isolate with observability
  wired in from the start rather than added reactively.

### Open follow-ups

- **`agent-panel.css`'s pre-existing `npm run build` failure** (a
  `lightningcss` "invalid dangling combinator" error in a comment block,
  unrelated to this sprint's own files, confirmed untracked/uncommitted
  from an earlier sprint) blocks a clean production build today —
  flagged to `REVIEW-QUEUE.md`; worth a small dedicated fix task, out of
  this story's own scope.
- **`BUG-011`** (the filename-stem collision first disclosed at
  `SPRINT-025`) remains open and unaffected by this sprint — this
  sprint's own live verification reconfirmed it (503 unique-stem notes
  vs. 504 real files today), consistent with the prior disclosure, not a
  new or worsening finding.

---

## Notes

**Sprint assembled 2026-08-13 (`/plan-sprints`).** Second of a two-sprint,
MVP-phase pair (`SPRINT-025` → `SPRINT-026`); see `SPRINT-025`'s own Notes
for the full pair-partitioning rationale.

**Gate: `gate: clear` 2026-08-13.** No MUST-FLAG trigger fires for this
product-owner pass: (1) no material assumption — the `depends_on_sprints`
edge mirrors `REQ-SB-02-US-01-T01`'s own real, decomposer-recorded task
edge exactly, not guessed or invented; (2) `REQ-SB-02` is finalized PRD
text; (3) product-owner does not write ADRs — `ADR-026` was already
reviewed and approved (`REVIEW-QUEUE.md`, 2026-08-13) before this pass; (4)
no new `ESCALATIONS.md` entry needed; (5) not oversized (4 tasks, M) and not
a blocked story (all 4 tasks are `Ready`); re-checked explicitly against the
"cross-sprint dependency" MUST-FLAG sub-trigger — this is the ordinary,
expected mechanical translation of an already-recorded task-level edge into
a sprint-level one (the same shape `SPRINT-009`/`SPRINT-012`/`SPRINT-015`/
`SPRINT-022`/`SPRINT-023`/`SPRINT-024` already used without a flag), not a
dependency this pass discovered or had to invent; (6) N/A (coder-only
trigger); (7) no contradictory inputs; (8) not ambiguous — a single-story
sprint with a straight dependency chain, sequenced behind its one real
cross-story prerequisite, has exactly one reasonable grouping. Advances
`Draft → Ready`.

**Update, 2026-08-13 (`/implement-sprint` — coder) — Done.** All 4 tasks
built and every locked AC verified live against the real, indexed vault
(backend: Python-shell + real HTTP; frontend: a real browser via
headless-Chrome-via-CDP). `REQ-SB-02-US-01` advanced to `status: Done`,
`gate: clear` — `ADR-026`'s own human review was already `Approved` in
`REVIEW-QUEUE.md` before this build started. Sprint advances to `status:
Done`, `gate: flagged` (retro-harvest only — see `REVIEW-QUEUE.md`).
`BACKLOG.md`'s `REQ-SB-02` row and Sprint Status table both updated.
Two non-blocking items written to `REVIEW-QUEUE.md` (a scope-internal
AC-05 test-query substitution, logged in `T02`'s own Implementation Log;
a pre-existing, out-of-scope `agent-panel.css` production-build failure)
— neither is an `ESCALATIONS.md` entry (no out-of-scope event, no
unresolvable AC, no deviation from `ADR-026`).
