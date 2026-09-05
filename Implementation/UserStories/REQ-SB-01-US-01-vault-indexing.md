---
id: REQ-SB-01-US-01
title: Vault Indexing — a real, re-runnable index of frontmatter, tags, and wikilinks
requirement_ids: [REQ-SB-01]
requirement_section: "REQ-SB-01: Vault Indexing"
phase: MVP
status: Done
gate: flagged
gate_reason: "trigger-7 (real, live-discovered filename-stem collision — ESC-027, Open)"
sprint: "SPRINT-025"
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-01-US-01 — Vault Indexing — a real, re-runnable index of frontmatter, tags, and wikilinks

## Story

**As a** Second Brain user
**I want** my Obsidian vault's notes parsed into one real, re-runnable index
that correctly captures each note's frontmatter, tags, and outgoing/incoming
wikilinks
**So that** every other Second Brain feature that needs to know what's
actually in the vault (browsing, search, agent tool-calls, scoped retrieval)
can read from one accurate, up-to-date structure instead of each feature
re-scanning the filesystem its own ad hoc way

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-01: Vault Indexing* — "The user
  points Second Brain at an Obsidian vault directory, and it parses and
  indexes the markdown notes there — frontmatter, wikilinks, and tags — with
  no staging or promotion step... Acceptance: Pointing Second Brain at a
  vault directory produces a complete index of that vault's notes, correctly
  capturing each note's frontmatter fields, outgoing/incoming wikilinks, and
  tags; re-running the index after the vault changes picks up additions,
  edits, and deletions without manual intervention."
- **Genuinely foundational, never-built work.** Confirmed by direct
  inspection (2026-08-13): despite 30+ P1 requirements already `Done` this
  session, **no persistent index exists anywhere in this codebase.** Every
  vault-query primitive walks the filesystem fresh, on every call:
  `app/data_access/vault_writer.py`'s `list_all_note_paths()`/
  `list_notes_in_kind_folder()` glob the directory tree each time;
  `list_known_customers()`/`list_known_kinds()`/`list_known_partners()` each
  loop over every note's frontmatter via `read_note()` (a hand-rolled
  simple-`key: "value"` parser, not a general YAML parser, by its own
  docstring) on every call, with no caching or persisted data structure
  in between. `app/business/vault_query_tools.py` (built for REQ-SB-25's
  agent tool-calling) is a thin pass-through over those same ad hoc
  `vault_writer` scans — not a real index either. No wikilink-graph
  structure (forward or backward) is computed or stored anywhere; Obsidian's
  own graph view is the only place backlinks currently render at all.
- **Real vault, grounded numbers (2026-08-13, `VAULT_PATH` from `.env`:
  `<OPERATOR_VAULT_OLD>`):** 496 real notes under `Work/`
  (204 Email, 134 People, 51 Meetings, 6 Customers, 1 Partner, plus
  Notifications/Files/Newsletters not individually counted here) — each
  produced by this project's own capture pipelines or manual templates, so
  all share the simple `write_note()`-produced frontmatter shape. The vault
  also contains `Templates/` (5 template stub files: Customer, Opportunity,
  Agreement, Consumption-Snapshot, Research — not real captured/authored
  content) and Obsidian's own `.obsidian/` configuration directory (app
  settings, not notes) — both must stay excluded from the index (see
  Constraints).
- **This pass is structural indexing, not semantic/embedding indexing.**
  `Documentation/PRD.md`'s P2 section (`REQ-SB-06`, Search Quality
  Enhancements) explicitly defers "chunking note content ahead of embedding
  at scale, and reranking results... since there is nothing yet to refine
  until REQ-SB-02 ships" — confirming this story's index is the frontmatter/
  tags/wikilinks structure the PRD's own Acceptance text names, not a vector
  store. `Implementation/Plans/2026-08-10-agentic-map-requirement-port.md`
  independently confirms the same reading (agentic-map's REQ-009
  chunking-before-embedding "becomes a P1/P2 concern once semantic search is
  wanted, not an MVP one").
- **`REQ-SB-02` (Browse & Search) depends on this story** — it lists/browses/
  filters/searches what this story indexes; it cannot be built or
  meaningfully designed against real data until this story exists. See
  `REQ-SB-02-US-01`.
- **`REQ-SB-29-US-01` (Agent-to-Tag/Folder Scoping) deliberately did NOT wait
  on this story** — it was flagged (`ESCALATIONS.md` → `ESC-008`) and the
  operator resolved it by building its own narrower, story-scoped ad hoc
  retrieval primitive instead (2026-08-12). This story does not retroactively
  require `REQ-SB-29-US-01` to be rebuilt against it.
- **Resolved 2026-08-13 (`ESC-021`, Resolved) — the re-index trigger
  mechanism is BOTH of the following, not a single choice:** (a) an explicit
  on-demand re-index call/endpoint — needed regardless, for correctness
  immediately after any vault change, without waiting on a schedule; AND
  (b) wired into `REQ-SB-07`'s already-`Done` recurring capture cadence
  (hourly, plus once on app start, with missed-run catch-up) — the vault
  index refreshes as part of that same existing scheduler tick, alongside
  email/meeting/to-do capture, rather than needing its own separate
  schedule. **Live filesystem watching is explicitly NOT in scope this
  pass** — a materially bigger technical lift (watcher infrastructure,
  debouncing) disproportionate to a personal, single-user vault, matching
  this project's own repeated "proportionate first, escalate only if proven
  insufficient" precedent (`ADR-011`'s reasoning). See Constraints and the
  two additional scenarios below.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. Scenarios 3-5 say "the index is re-run" — satisfied by either of
Scenarios 8/9's two resolved trigger paths (on-demand call, or the existing
hourly schedule); neither scenario 3-5 needs to name which path ran. -->

### Scenario 1: Indexing the vault captures frontmatter, tags, and outgoing wikilinks for every real note

```gherkin
Given a vault directory containing real markdown notes with frontmatter,
    tags, and body wikilinks (matching the shapes already produced by this
    project's existing capture pipelines and manual templates)
When the vault is indexed
Then the resulting index contains one entry per real note in the vault
  And each entry correctly captures that note's frontmatter fields
  And each entry correctly captures that note's tags
  And each entry correctly captures that note's outgoing wikilinks (the
    notes it links to)
```
<!-- AC-ID: REQ-SB-01-US-01-AC-01 -->

### Scenario 2: Indexing derives incoming wikilinks (backlinks) from other notes' outgoing links

```gherkin
Given Note A's body contains a wikilink to Note B (e.g. "[[Note B]]")
  And Note B's own file contains no reference to Note A anywhere
When the vault is indexed
Then Note B's index entry lists Note A among its incoming wikilinks
    (backlinks)
```
<!-- AC-ID: REQ-SB-01-US-01-AC-02 -->

### Scenario 3: Re-indexing after a note is added picks it up

```gherkin
Given the vault has already been indexed once
  And a new markdown note is subsequently added to the vault
When the index is re-run
Then the new note appears in the index with its own frontmatter, tags, and
    wikilinks correctly captured
  And no manual step beyond re-running the index was required
```
<!-- AC-ID: REQ-SB-01-US-01-AC-03 -->

### Scenario 4: Re-indexing after a note is edited reflects the change

```gherkin
Given a note already present in the index
  And that note's frontmatter, tags, or body wikilinks are subsequently
    edited directly in the vault
When the index is re-run
Then the note's index entry reflects the edited content
  And no stale prior version of that entry remains
```
<!-- AC-ID: REQ-SB-01-US-01-AC-04 -->

### Scenario 5: Re-indexing after a note is deleted removes it from the index

```gherkin
Given a note already present in the index
  And that note is subsequently deleted from the vault
When the index is re-run
Then the note no longer appears in the index
  And any other note's previously-recorded outgoing wikilink to the deleted
    note is handled honestly (the index does not crash and does not present
    a now-nonexistent note as if it still existed)
```
<!-- AC-ID: REQ-SB-01-US-01-AC-05 -->

### Scenario 6: A note with no tags and no wikilinks is indexed correctly

```gherkin
Given a note with valid frontmatter but no "tags" field and no "[[wikilinks]]"
    anywhere in its body
When the vault is indexed
Then the note's index entry exists
  And its tags list and outgoing-wikilinks list are both empty, not an error
```
<!-- AC-ID: REQ-SB-01-US-01-AC-06 -->

### Scenario 7: Indexing scope excludes non-note vault content

```gherkin
Given the vault directory also contains Obsidian's own configuration folder
    (".obsidian/") and template stub files ("Templates/") that are not real
    captured or authored notes
When the vault is indexed
Then the index contains only real vault notes
  And no ".obsidian/" configuration file or "Templates/" stub file appears
    as an index entry
```
<!-- AC-ID: REQ-SB-01-US-01-AC-07 -->

### Scenario 8: An explicit on-demand re-index reflects a vault change immediately

```gherkin
Given the vault has changed since the index was last built or refreshed
When an explicit on-demand re-index is triggered
Then the index reflects the vault's current state immediately
  And the caller did not have to wait for the next scheduled run
```
<!-- AC-ID: REQ-SB-01-US-01-AC-08 -->

### Scenario 9: The index also refreshes automatically on the existing hourly capture schedule

```gherkin
Given REQ-SB-07's already-established scheduled recurring capture cadence
    (hourly, plus once on app start, with missed-run catch-up)
When that scheduled cadence fires
Then the vault index is refreshed as part of that same run, alongside
    email/meeting/to-do capture
  And no separate, independent schedule was needed for the index specifically
```
<!-- AC-ID: REQ-SB-01-US-01-AC-09 -->

## Affected Screens

None — backend only. This story has no UI of its own; `REQ-SB-02-US-01`
builds the browse/search UI that reads from this story's index.

## Dependencies

- **Blocked by:** none.
- **Related to:** `REQ-SB-02-US-01` (Browse & Search) — depends on this
  story's index; cannot be built first.
- **Related to:** `REQ-SB-29-US-01` (Agent-to-Tag/Folder Scoping) — that
  story already shipped its own independent, narrower ad hoc scoped-query
  primitive rather than wait on this one (`ESC-008`, Resolved). Unaffected
  by this story.
- **Related to:** `REQ-SB-07-US-01` (Scheduled Recurring Agent Capture,
  `Done`) — this story's automatic-refresh path wires into that story's
  already-built hourly-plus-app-start scheduler tick (resolved 2026-08-13,
  see Context/Constraints); not a build dependency on new capability, since
  the scheduler itself already exists.
- **External:** none.

## Constraints

- **No staging/promotion gate** — an indexed note is immediately usable; no
  "pending"/"unreviewed" state (standing `MEMORY.md` decision, restated
  directly in the PRD's own requirement text).
- **Index scope: real vault notes only.** Markdown files under the vault
  root representing actual captured/authored content — excluding Obsidian's
  own `.obsidian/` configuration directory and the `Templates/` folder's
  template stubs. Resolved by direct inspection of the real vault (see
  Context), not guessed.
- **Must correctly handle every note shape this project already produces** —
  Email, Meeting, Person, Customer hub, Partner hub notes (automated
  capture) and Customer/Opportunity/Agreement/Consumption-Snapshot/Research
  notes (manual templates, `REQ-SB-15`/`REQ-SB-17`) — not just a
  hypothetical generic shape.
- **Re-running the index must reconcile additions, edits, AND deletions
  without the caller manually specifying what changed** — a full/idempotent
  reconciliation on each run, not a manually-fed diff.
- **Resolved 2026-08-13 — the re-index trigger mechanism is BOTH:** (a) an
  explicit on-demand call/endpoint/function, AND (b) wired into `REQ-SB-07`'s
  existing hourly-plus-app-start scheduled capture cadence, refreshing the
  index as part of that same tick. **Live filesystem watching is explicitly
  out of scope this pass** (disproportionate technical lift for a personal,
  single-user vault — see Context). If (a)+(b) together prove insufficient
  in practice, escalate to live watching later rather than build it
  speculatively now.
- **The index's storage mechanism remains an architecture-level decision,
  left to `/plan-tasks`** (in-memory only, rebuilt fresh each run, vs.
  persisted to a `.second-brain/` state file mirroring this project's
  existing convention) — not a requirement-level open question, so not
  flagged; ordinary implementation latitude for the architect/decomposer.

## Implementation Tasks

| Task | Title | Covers | depends_on |
|---|---|---|---|
| `REQ-SB-01-US-01-T01` | `vault_writer.py` frontmatter list-value round-trip fix + public wikilink-extraction primitive | (foundational — no AC directly) | — |
| `REQ-SB-01-US-01-T02` | Core index build/rebuild/backlink logic — `app/business/vault_indexing.py` | AC-01–AC-07 | T01 |
| `REQ-SB-01-US-01-T03` | On-demand re-index endpoint — `app/api/vault_index_router.py` | AC-08 | T02 |
| `REQ-SB-01-US-01-T04` | Scheduler-tick wiring — `email_classification.py` unconditional call | AC-09 | T02 |

## Definition of Done

- [x] All acceptance-criteria scenarios pass (AC-01 with one disclosed,
      escalated, out-of-scope exception — `ESC-027`, see `## Notes`)
- [x] Every Implementation Task above is complete (T01-T04, all `Done`)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists — n/a this pass)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Any browse/search UI or API** — `REQ-SB-02`.
- **Ranked/relevance search of any kind** — `REQ-SB-02`; this story only
  builds the index, not a query/search layer over it.
- **Embeddings, chunking, semantic search, or reranking** — `REQ-SB-06`
  (P2), explicitly deferred until this story's structural index exists.
- **Writing to the vault** — this story only reads/indexes; it never
  creates, edits, or deletes a vault note.
- **Real-time multi-writer conflict resolution** — the vault is
  single-user, locally trusted personal data (standing `MEMORY.md`
  decision); this story does not add any concurrency-control mechanism.
- **Live filesystem watching** — resolved out of scope this pass (see
  Constraints); on-demand + hourly-scheduled re-indexing is this story's
  full trigger-mechanism scope. A future story can add live watching if the
  on-demand/hourly combination proves insufficient in practice.

## Notes

**Prototype parity:** N/A — this story is backend-only, no screen.

**Update, 2026-08-13 — Resolved.** The re-index trigger mechanism
(`ESCALATIONS.md` → `ESC-021`) was genuinely open at first draft: the PRD's
own Acceptance text — "re-running the index after the vault changes picks
up additions, edits, and deletions without manual intervention" — describes
WHAT a re-index run must accomplish, not WHEN/HOW it's triggered, and this
codebase had precedent pointing at more than one equally-literal answer.
Decided (operator's delegated "sane defaults" call, relayed via the
coordinating session, not guessed by the analyst): **both** an explicit
on-demand re-index call/endpoint (needed regardless, for immediate
correctness after any vault change) **and** wiring into `REQ-SB-07`'s
already-`Done` hourly-plus-app-start scheduled capture cadence — mirroring
that story's own established pattern exactly, rather than inventing a new
one. Live filesystem watching is explicitly excluded this pass as
disproportionate for a personal, single-user vault (`ADR-011`'s
"proportionate first" precedent). Reflected above in Context, Constraints,
Non-Goals, and two new Acceptance Criteria scenarios (8, 9). No other
requirement-level open question remains for this story — the index's
storage mechanism (in-memory vs. persisted) stays ordinary architecture
latitude for `/plan-tasks`, not a requirement-level ambiguity.
`ESCALATIONS.md` → `ESC-021` flipped to `Resolved`, naming this update as
the resolving artefact. `gate:` reset to `clear`.

gate: clear 2026-08-13 — no requirement-level triggers remain open (index
scope was already resolved by direct vault inspection at first draft; the
re-index trigger mechanism is now resolved above; no UI/prototype surface
applies, this story is backend-only). Ready for `/plan-tasks REQ-SB-01`.

**Architect pass, 2026-08-13.** This is genuinely new architectural
structure — every existing vault-query primitive is stateless pass-through
I/O (`vault_writer.py`/`vault_query_tools.py`); this story is the first to
need a real, persistent, re-runnable index. Wrote **ADR-024** deciding the
storage/rebuild shape: an in-memory-only, module-level singleton
(`app/business/vault_indexing.py`), rebuilt wholesale (never incrementally
diffed) and atomically swapped in on every trigger — no `.second-brain/`
persistence file, no database (SQLite rejected as disproportionate to a
~500-note single-user vault with no query surface yet to serve). Full
reasoning, alternatives, and consequences: `Implementation/Architecture/
ADR.md` → ADR-024. `architecture.md` updated: new "Vault Indexing Layer"
section (§ before "Data Model"), a `Source Layout` paragraph, the `Last
reviewed` footer, and a stale `Local Development` note about vault-path
configurability corrected in passing (the config already exists in code;
the note predated it).

**Architecture scope: "Vault Indexing Layer" (architecture.md), "Source
Layout"'s `vault_indexing.py` paragraph, ADR-024.** The coder is bounded to
these sections — do not reach into "My Day & Agent Panel APIs," "In-App
Agent Orchestration," or any other section's own modules for this story's
tasks.

**Gate: flagged — trigger 3 (ADR-024 created).** Per pipeline rule, the
stage does not halt here; the decomposer still runs so a human reviews the
ADR and the resulting tasks together in one pass. See `REVIEW-QUEUE.md`.

**Decomposer pass, 2026-08-13.** All 9 scenarios locked as
`AC-01`…`AC-09` (tags appended after each Gherkin fence, wording
unchanged from the analyst's own text — already buildable as written).
4 tasks written (`T01`–`T04`, see `## Implementation Tasks` above),
`depends_on` acyclic (`T01 → T02 → {T03, T04}`), every locked AC has at
least one AC-tagged manual verification step (`AC-01`–`AC-07` in `T02`,
`AC-08` in `T03`, `AC-09` in `T04`). Story `status: Draft → Ready`, every
task written directly at `status: Ready`. `gate: flagged` is unchanged
(carried from the architect's ADR-024 flag, per Pipeline.md's "an
ADR-creation flag does not halt `/plan-tasks`" rule) — if `ADR-024`
changes as a result of the pending review, reset the affected task(s)
back to `Draft`/`Ready` as appropriate and re-run. No new MUST-FLAG
trigger fired during decomposition itself (no material assumption beyond
the architect's own already-flagged ADR, no contradictory inputs, no
oversized task, every locked AC has an observable verification path,
exactly one reasonable task breakdown given the code's own natural
seams — read/parse fix → core index → the two independent trigger
surfaces). Eligible for `/plan-sprints` once `ADR-024`'s review closes (or
immediately, at the operator's discretion, per this pipeline's
non-blocking-on-flag convention).

**Coder pass, 2026-08-13 (`/implement-sprint SPRINT-025`).** All 4 tasks
(`T01`-`T04`) built and verified live against the real vault (`VAULT_PATH`,
502-503 real notes across the build, growing as real capture runs
continued during verification) and, for `T04`, real Outlook COM/Compass
calls. `T01`: `vault_writer._parse_frontmatter_value` gained the
bracketed-list branch, `extract_wikilink_targets(body)` added — both
verified against real vault notes. `T02`: new
`app/business/vault_indexing.py` (`rebuild_index`/`get_index`/
`_build_entry`), exactly per `ADR-024`. `T03`: new
`app/api/vault_index_router.py` (`POST /vault-index/rebuild`), registered
in `main.py`. `T04`: one new unconditional
`vault_indexing.rebuild_index()` call inside
`email_classification.run_capture_and_record_completion`, zero changes to
`capture_scheduler.py` (confirmed via `git diff`).

All 9 locked ACs verified: `AC-01`-`AC-07` (`T02`), `AC-08` (`T03`),
`AC-09` (`T04`) — see each task's own Implementation Log for full detail.
**One real, live-discovered, disclosed exception, not silently
hidden:** `AC-01`'s own `len(index) == len(list_all_note_paths())` check
found a genuine, pre-existing filename-stem collision between two
distinct real notes (`_slugify`'s 80-character truncation silently eats
`email_classification.py`'s trailing disambiguating id-suffix when a
subject alone already fills the 80-char budget) — a real gap in
`ADR-024`'s own "filename stem is unique" founding assumption, root-caused
to already-`Done`, out-of-scope code, not to this story's own new
indexing logic (which is verified correct against every other one of the
vault's real notes, and correctly derives backlinks, handles adds/edits/
deletes, empty-tag/no-wikilink notes, and `.obsidian`/`Templates`
exclusion). Escalated, not worked around: `ESCALATIONS.md` → `ESC-027`
(Open), `REVIEW-QUEUE.md` pointer added, `/bug` capture recommended,
mirroring this project's own established `ESC-002`/`ESC-003`/`ESC-012`
precedent (real, out-of-scope, root-caused defects found via due-diligence
verification are surfaced honestly, not silently patched, and do not
block the task/story that found them). `T02`'s own `gate: flagged` for
this reason; every other task `gate: clear`.

Two verification-method deviations, both logged as scope-internal
assumptions for spot-check, neither an escalation: `T03` fell back to
`fastapi.testclient.TestClient(app)` (instantiated without the `with`
lifespan context, to avoid `BUGS.md` → `BUG-008`'s known real app-start
hang) instead of a literal separate `uvicorn` process — still the real
FastAPI HTTP routing/dependency-injection layer, confirmed via the real
`HTTP/1.1 200 OK` request log; `T04` called
`capture_scheduler.run_capture_if_idle()` directly via `asyncio.run(...)`
instead of starting a full server — the literal same function object the
real app-start lifespan event calls, including a real, live Outlook COM +
Compass capture run. Both mirror `Implementation/Learnings.md`'s own
`SPRINT-023` "skip the HTTP layer when it isn't load-bearing" pattern.

Story `status: Draft/Ready → Done` — every task `Done`, every locked AC
verified (`AC-01` with the one disclosed, escalated, out-of-scope
exception above). `gate: flagged` for `ESC-027`'s own open status, not a
blocker to `Done`.
