---
id: BUGFIX-07-US-01
title: Customer/Project log.md and captures.md carry an identifying header, mirroring index.md's own convention (BUG-028 fix)
requirement_ids: [BUG-028]
requirement_section: "BUGS.md → BUG-028"
status: Done
gate: clear
gate_reason: "No MUST-FLAG trigger fired this pass. BUG-028's own note discloses the fix shape was confirmed directly with the operator before capture ('add a header line at creation ... mirroring index.md's own working pattern, and backfill it onto already-existing headerless files'), and it deliberately reuses a convention already live and correct in this exact codebase (index.md's own `# {name}` header) rather than inventing a new one -- no material assumption, no Draft/unfinalised PRD text relied on (BUG-028 is a finalised, non-Draft ledger entry), no ADR implicated (adding a header string to two already-existing, already-shared primitives is not a new architectural/tooling/structural decision), no ESCALATIONS.md entry needed, the fix is small and single-file-scoped (not oversized), no contradictory inputs, and exactly one workable interpretation once BUG-028's own 'Note' is read literally -- see ## Notes for the full trigger-by-trigger walkthrough."
sprint: "SPRINT-070"
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-07-US-01 — Customer/Project `log.md`/`captures.md` carry an identifying header, mirroring `index.md`'s own convention

## Story

**As a** Second Brain user browsing my Obsidian vault directly (tab bar,
quick switcher, or file explorer — not the app's own search/browse UI)
**I want** every Customer's and every Project's `log.md` and `captures.md`
to open with a stable header naming the Customer/Project they belong to
**So that** I can tell which Customer/Project a `log.md` or `captures.md`
tab belongs to at a glance, instead of every one of these identically-named
files reading as anonymous once opened on its own

## Context

Triage batch: `BUG-028` only — logged `2026-08-19`, `Open` at triage time,
found by the operator during live Obsidian browsing ("I noticed Something,
The Customer is a folder so if we updated the log file inside the Customer
we will have Multiple Log files Connect but no place to see the customer
name").

### BUG-028 — Customer/Project `log.md`/`captures.md` are created with zero identifying content (Logic, Minor)

- **Screen \ route:** N/A — this is a vault data-layer bug, not a Second
  Brain app UI screen. `BUGS.md` itself confirms `log.md`/`captures.md` are
  deliberately excluded from `vault_indexing` (`list_all_note_paths()`), so
  this does not affect search/backlinks/the Vault graph (`REQ-SB-75`) — it
  is purely an Obsidian-native file-browsing problem (tab bar, quick
  switcher, file explorer).
- **Repro:** create (or ensure) any Customer or Project OKF directory via
  `vault_writer.create_okf_directory_baseline`/`ensure_okf_directory_
  baseline` (the one shared primitive both Customer and Project route
  through — `ADR-042`, same OKF shape for both kinds), then open the
  resulting `log.md` or `captures.md` directly.
- **Expected:** a stable, identifying header naming the owning Customer/
  Project, mirroring `index.md`'s own already-correct `# {name}\n\n...`
  convention (its `index_listing_body` parameter, already written
  correctly today).
- **Actual, confirmed by direct code reading this pass (`src/backend/app/
  data_access/vault_writer.py`, lines 289-341):**
  - `create_okf_directory_baseline` (the FIRST-creation path) writes
    `paths["log"].write_text("", encoding="utf-8")` and
    `paths["captures"].write_text("", encoding="utf-8")` unconditionally
    the first time each file is created (guarded only by `if not
    paths["log"].exists()` / `if not paths["captures"].exists()` — i.e. it
    never overwrites an already-existing file, but the FIRST write is a
    bare empty string, no header).
  - `ensure_okf_directory_baseline` (the TOP-UP path, run against an
    already-existing directory) carries the exact same shape — `if not
    paths["log"].exists(): paths["log"].write_text("", encoding="utf-8")`
    — so it only ever creates a missing `log.md`/`captures.md` from
    scratch (still headerless), and never touches one that already exists,
    whether that existing file is genuinely empty or already carries real
    appended content. Nothing in either function retrofits a header onto
    an already-existing file today.
  - By contrast, `index.md` is written unconditionally in BOTH functions
    via `paths["index"].write_text(index_listing_body, encoding="utf-8")`,
    where every real caller (`create_customer_directory_baseline`/
    `ensure_customer_directory_baseline`, `create_project_directory_
    baseline`/`ensure_project_directory_baseline`) passes
    `index_listing_body=f"# {customer}\n\n- [[{_slugify(customer)}]]\n"` or
    the equivalent `f"# {project}\n\n..."` — this is the already-working
    convention `log.md`/`captures.md` need to mirror the identifying-header
    HALF of (not the wikilink-listing half, which is `index.md`-specific
    and does not apply to a log/captures file).
  - With 26+ real Customer folders already in the vault (more once
    `REQ-SB-74`'s backfill runs, plus every Project nested under a
    Customer, same shape via `_project_directory_root`), every one of these
    files is identically named (`log.md`, `captures.md`) and, once opened
    alone, completely anonymous.
  - **Shared primitive, both Customer and Project affected identically:**
    `create_okf_directory_baseline`/`ensure_okf_directory_baseline` are the
    one function pair both `create_customer_directory_baseline`/`ensure_
    customer_directory_baseline` and `create_project_directory_baseline`/
    `ensure_project_directory_baseline` route through (`ADR-042` — same OKF
    shape for both kinds, confirmed by direct reading of all four wrapper
    functions, lines 375-449). A fix at the shared primitive covers both
    kinds by construction — there is no separate Customer-only or
    Project-only code path to patch twice.
  - **The retrofit-must-not-disturb-real-content constraint, confirmed by
    direct code reading:** the raw-append write primitives that put real
    content into an already-existing `log.md` (`append_person_note_
    update_line`, lines 877-890 — an unconditional read-then-append-then-
    write, no idempotency check) never touch `captures.md` at all in this
    module (`create_okf_directory_baseline`'s own docstring: "`captures.md`
    is never opened by this function beyond that one existence check"). Any
    retrofit that adds a header to an already-existing `log.md` must
    prepend/insert that header without disturbing whatever real lines
    `append_person_note_update_line` (or any other future raw-append
    caller) has already written there — the same "byte-for-byte unchanged
    except for the addition itself" discipline this codebase already
    applies elsewhere (e.g. `move_okf_directory`'s own docstring).
- **Note (BUGS.md's own disclosed fix shape, confirmed with the operator
  before capture, not re-litigated here):** add a header line at creation
  (mirroring `index.md`'s own working pattern), and backfill it onto
  already-existing headerless files WITHOUT disturbing any real
  already-appended content.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then) by the analyst; the
decomposer locks and AC-IDs this at /plan-tasks. Per the triage-mode
contract: one bug (BUG-028), authored as two Scenario blocks covering its
two facets (fresh creation, retrofit of an already-existing directory) —
mirroring BUGFIX-06-US-01's/BUGFIX-05-US-01's own "one scenario, several
facets for one bug with one root cause" precedent. -->

### Scenario 1: A newly-created Customer or Project directory's log.md and captures.md carry an identifying header

```gherkin
Given a Customer or Project OKF directory does not yet exist
When it is created for the first time via `create_okf_directory_baseline`
    (through `create_customer_directory_baseline` or
    `create_project_directory_baseline` — the same shared primitive both
    kinds route through, ADR-042)
Then the resulting `log.md` and `captures.md` files each open with a
    stable header naming the owning Customer/Project, mirroring
    `index.md`'s own already-correct `# {name}` header convention
  And each file is otherwise empty beneath that header, ready to receive
    real appended content later
```
<!-- AC-ID: BUGFIX-07-US-01-AC-01 -->

### Scenario 2: Re-running the ensure step against an already-existing, pre-fix Customer or Project backfills the header without disturbing already-appended content

```gherkin
Given a Customer or Project OKF directory already exists, created before
    this fix, whose `log.md` and/or `captures.md` has no identifying
    header — either genuinely empty, or already carrying real content
    appended by `append_person_note_update_line` with no header at all
When `ensure_okf_directory_baseline` is run against that same directory
    again (through `ensure_customer_directory_baseline` or `ensure_
    project_directory_baseline`)
Then `log.md` and `captures.md` each gain the same identifying header
    Scenario 1 describes
  And any real content that was already appended to either file before
    this run is preserved byte-for-byte, unchanged, after the header —
    nothing already written is lost, reordered, or duplicated
```
<!-- AC-ID: BUGFIX-07-US-01-AC-02 -->

## Affected Screens

- None — backend only. Per `BUG-028`'s own "Screen \ route: N/A" note,
  this is a vault data-layer fix reaching Obsidian's own native file
  browsing (tab bar, quick switcher, file explorer), not a Second Brain
  app screen. No `html-prototype/` file is touched by this story.

## Dependencies

- **Blocked by:** none. `create_okf_directory_baseline`/`ensure_okf_
  directory_baseline` and their four Customer/Project wrapper functions
  (`REQ-SB-54-US-01`, `ADR-042`) are already `Done` and already live; this
  fix only adds a header write to two already-existing code paths inside
  them.
- **Related to:** `REQ-SB-54-US-01` (the OKF-directory story that
  originally shipped `create_okf_directory_baseline`/`ensure_okf_
  directory_baseline`), `ADR-042` (the shared Customer/Project OKF
  directory shape this fix must keep shared, not fork), `REQ-SB-74` (the
  Customer backfill pass that will create/touch more of these directories
  going forward — every one it creates or ensures should already carry the
  header once this fix ships).
- **External:** verification should run against at least one genuinely new
  Customer or Project (Scenario 1) and at least one already-existing real
  Customer folder from the live vault whose `log.md` already carries real
  appended content, if one exists, to exercise Scenario 2's
  content-preservation clause against real data rather than a synthetic
  fixture alone.

## Constraints

- **Fix lives in the shared primitive** — `create_okf_directory_baseline`/
  `ensure_okf_directory_baseline` — not duplicated separately into the
  Customer and Project wrapper functions. Both kinds must be fixed by the
  same change, per `ADR-042`'s existing shared shape.
- **Header content mirrors `index.md`'s own `# {name}` convention** — the
  identifying header names the same display value already passed as
  `index_listing_body`'s `{customer}`/`{project}` (the real display
  name/title, not the slug) — not a new, differently-derived name.
  `log.md`/`captures.md` need only the identifying-header half of
  `index.md`'s convention, not its trailing wikilink-listing line, which
  is `index.md`-specific and does not apply here.
- **The retrofit path must never disturb already-appended real content.**
  Any content `append_person_note_update_line` (or any future raw-append
  caller) has already written into an existing `log.md` must remain
  byte-for-byte intact after the header is backfilled — insertion, not
  replacement, of the file's pre-existing body.
- **`log.md`/`captures.md` stay excluded from `vault_indexing`** — this
  fix changes file CONTENT only; it does not add these files to
  `list_all_note_paths()` or any indexing/search/backlink surface.
- The exact mechanism for threading the identifying name into `create_
  okf_directory_baseline`/`ensure_okf_directory_baseline` (e.g. a new
  parameter, deriving it from `index_listing_body`'s own first line, or
  another shape) is an implementation-shape detail left to `/plan-tasks` —
  not decided here.

## Implementation Tasks

<!-- Decomposer pass, /plan-tasks step 2, 2026-08-19: confirms the analyst's
own starting-point table below unchanged -- one task, single-file scope,
no split warranted. This table is now authoritative. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| BUGFIX-07-US-01-T01 | backend | Add an identifying header write to `create_okf_directory_baseline` (fresh `log.md`/`captures.md`) and a backfill-only header write to `ensure_okf_directory_baseline` (already-existing headerless files, preserving any already-appended content) | `src/backend/app/data_access/vault_writer.py` | `../Tasks/BUGFIX-07-US-01-T01-okf-log-captures-header.md` |

**Dependency-graph summary:** `BUGFIX-07-US-01-T01` has `depends_on: []` —
a single-task story, no graph edges.

## Definition of Done

- [x] Both acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped
      with reason)
- [x] All Constraints respected — including that the fix stays in the
      shared primitive (covers both Customer and Project), and no
      already-appended real content in an existing `log.md`/`captures.md`
      is disturbed
- [x] Automated tests added/updated and passing (once test tooling exists)
      — n/a this pass, test tooling still pending per the task's own
      `## Tests` block; covered by manual verification instead
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] `BUG-028` flipped `In Sprint → Closed` in both `BUGS.md` and
      `BACKLOG.md`'s `## Bugs` mirror once this story is `Done`

**Coder pass, 2026-08-19:** `BUGFIX-07-US-01-T01` is `Done` — both locked
ACs (`AC-01` fresh creation, `AC-02` backfill without disturbing real
content) verified via the task's own manual `## Tests` steps against the
real `vault_writer` functions and the real, configured vault. Full outcome
detail in `../Tasks/BUGFIX-07-US-01-T01-okf-log-captures-header.md` →
`## Implementation Log`. Story status set `Ready → Done`.

## Non-Goals / Out of Scope

- Adding `log.md`/`captures.md` to `vault_indexing`/search/backlinks/the
  Vault graph — they stay deliberately excluded, per `BUG-028`'s own note;
  this is a content-only fix.
- Changing `index.md`'s own already-correct header/listing behavior — it
  is the working reference this fix mirrors, not something this fix
  touches.
- Changing `append_person_note_update_line`'s own append contract — this
  fix must coexist with it (preserve what it already wrote), not modify
  how it writes.
- Retrofitting `move_okf_directory`, `okf_directory_paths`, or any other
  OKF-directory primitive not named above.
- Any UI change — confirmed no screen is affected (`BUG-028`'s own
  "Screen \ route: N/A").

## Notes

**Why two Scenario blocks for one bug:** per the triage-mode contract, one
untagged Gherkin regression criterion per bug in this batch — this batch is
`BUG-028` only. Its two facets (a newly-created directory's `log.md`/
`captures.md` getting the header at creation; an already-existing,
pre-fix directory's `log.md`/`captures.md` being backfilled without
disturbing real content) are two aspects of the SAME root cause
(`create_okf_directory_baseline`/`ensure_okf_directory_baseline` never
writing a header at all, on either the creation or the top-up path) and
the SAME fix (mirror `index.md`'s own header convention on both paths).
This mirrors `BUGFIX-06-US-01`'s and `BUGFIX-05-US-01`'s own established
"one scenario, several facets for one bug" precedent. The decomposer may
keep these as two locked ACs or merge them, whichever reads more
verifiable at `/plan-tasks`.

**Why `gate: clear` — trigger-by-trigger:**
- Trigger 1 (material assumption): none — the root cause was re-confirmed
  by direct reading of the real, current `create_okf_directory_baseline`/
  `ensure_okf_directory_baseline`/`append_person_note_update_line` bodies
  and all four Customer/Project wrapper functions, not assumed from the
  bug note's text alone. The fix direction reuses `index.md`'s own
  already-live, already-correct header convention rather than inventing a
  new one, and was confirmed directly with the operator before capture
  (`BUG-028`'s own "Note").
- Trigger 2 (Draft/unfinalised requirement relied on): not applicable —
  `BUG-028` is a finalised, non-Draft bug-ledger entry, not a PRD
  requirement.
- Trigger 3 (ADR created/changed): not applicable to the analyst — no ADR
  is authored or implicated by this pass; whether the architect judges
  this small enough to need zero ADR touch is that role's own call at
  `/plan-tasks`.
- Trigger 4 (wrote an `ESCALATIONS.md` entry): not applicable — none
  written.
- Trigger 5 (oversized): no — one small, single-file-scoped fix
  (`vault_writer.py`, two functions), fits one working context easily.
- Trigger 7 (contradictory inputs): none — `BUG-028`'s repro, expected,
  actual, and disclosed fix-shape note all agree; this pass's direct code
  reading confirms every claim in them.
- Trigger 8 (multiple equally-valid interpretations / genuinely unclear):
  none — the header's content/placement is unambiguous once `BUG-028`'s
  own "mirroring `index.md`'s own already-correct `# {name}...`
  convention" is read literally, and the retrofit's
  never-disturb-real-content bound is equally unambiguous given
  `append_person_note_update_line`'s own confirmed append-only behavior.

`gate: clear` 2026-08-19 — no triggers fired (fix shape pre-confirmed with
the operator, `BUG-028` is a finalised ledger entry, no ADR/escalation
implicated by this pass, single-file-scoped, both scenarios verifiable,
no contradiction, one unambiguous fix direction).

---

**Architecture scope:** `Implementation/Architecture/architecture.md` →
§"Vault Knowledge Model Redesign — Threads, Manual Captures, OKF-Conformant
Customer & Project Directories" (`REQ-SB-54`, see `ADR-042`) — specifically
its `BUGFIX-07-US-01` correction bullet (2026-08-19), which records the
mechanism decided at this `/plan-tasks` pass. The coder is bounded to this
bullet plus the shared primitive it describes (`create_okf_directory_
baseline`/`ensure_okf_directory_baseline` in `src/backend/app/data_access/
vault_writer.py`) — no other architecture section is in scope for this fix.

**Architect pass, 2026-08-19 (`/plan-tasks` step 1) — mechanism decided,
no ADR:**

- **Header shape:** `# {identifying_name}\n\n` on `log.md`/`captures.md` —
  the bare `# {name}` HALF of `index.md`'s own already-`Accepted` header
  convention only (no trailing wikilink-listing line; no `— Log`/
  `— Captures` differentiating suffix — `BUG-028`'s complaint is
  cross-Customer/Project ambiguity, which Obsidian's own filename already
  resolves within one directory).
- **Mechanism:** a new explicit `identifying_name: str` parameter on both
  `create_okf_directory_baseline`/`ensure_okf_directory_baseline` (not a
  parse of `index_listing_body`'s own first line — every one of the four
  Customer/Project wrapper functions already has the display name in
  scope), plus one shared helper used identically by both functions for
  both Scenario 1 (fresh creation) and Scenario 2 (backfill).
- **Backfill-detection rule:** a file is "headerless" iff its current
  first line does not start with `# `. Confirmed against the real,
  current code that every real line any existing caller writes into these
  files (`append_person_note_update_line`'s three call sites —
  `project_customer_synthesizer.py`'s date-headed History lines;
  `person_note_proposals.py`'s/`skill_tools.py`'s `- <instruction>`
  bullets) never begins with `# `, so real already-appended content is
  always correctly detected as headerless (header gets PREPENDED, every
  existing byte preserved) and never mistaken for an already-headered
  file; an already-headered file (idempotent repeat `ensure_*` run) is
  correctly left untouched.
- **No ADR:** reuses the already-`Accepted` `# {name}` convention
  verbatim, changes neither the 4-file OKF directory shape nor `ADR-004`'s
  folder/tag boundary, and does not weaken or reach through `ADR-042`
  Decision point 1's captures.md-isolation-from-`<slug>.md`-regeneration
  guarantee (this fix is entirely within `log.md`/`captures.md`'s own
  creation/top-up logic, a different code path). `create_okf_directory_
  baseline`'s own docstring sentence claiming it "never opens captures.md
  beyond [an] existence check" becomes stale wording the coder must
  correct in-scope (a docstring-precision fix, not an architectural
  reopening — the guarantee that sentence protects is unaffected). Full
  reasoning: `Implementation/Architecture/architecture.md` → "Vault
  Knowledge Model Redesign" → `BUGFIX-07-US-01` correction bullet.

`gate: clear` 2026-08-19 (architect pass) — no ADR created/changed
(trigger 3 not fired), no assumption beyond the mechanism decision the
story's own Constraints explicitly deferred to this stage, no contradiction
of any Accepted ADR/PRD/MEMORY.md constraint, no escalation needed.

---

**Decomposer pass (`/plan-tasks` step 2), 2026-08-19:**

Locked both ACs exactly as authored (tightened wording only): `BUGFIX-07-
US-01-AC-01` (fresh-creation header on `log.md`/`captures.md`),
`BUGFIX-07-US-01-AC-02` (backfill on an already-existing headerless
directory, preserving already-appended real content byte-for-byte).
Neither is `locked: false` — both have a real, observable outcome (direct
file-content reads) verifiable without any UI/HTTP layer, per this
project's own standing manual-verification discipline.

Created one task, `BUGFIX-07-US-01-T01` (`depends_on: []`), covering the
full fix in the shared primitive: a new `identifying_name: str` parameter
on both `create_okf_directory_baseline`/`ensure_okf_directory_baseline`,
one shared `_write_or_backfill_identifying_header` helper used identically
by both functions for both the fresh-creation and backfill cases, the four
Customer/Project wrapper call sites updated to pass their own real display
name, and the in-scope docstring correction on `create_okf_directory_
baseline`. Single-file scope (`vault_writer.py`) — no separate task was
warranted; the fix is one shared primitive plus four thin, mechanical
call-site updates, not independently-buildable/verifiable units. Both
locked ACs are tagged in that task's `## Tests` with real, live manual
verification steps (direct Python-shell calls against the real functions,
using a throwaway directory under the real configured vault, plus an
optional real-pre-existing-directory check per this story's own
`## Dependencies` → External). `status: Ready` set on the task, in
lockstep with this story's own status transition below.

**Status transition:** `Draft → Ready` — every AC is locked (2 of 2), both
locked ACs have at least one AC-tagged manual verification step in
`BUGFIX-07-US-01-T01`'s `## Tests`, and `depends_on` is trivially acyclic
(the story's only task has no edges). No MUST-FLAG trigger fired during
this pass: no material assumption beyond direct code reading (re-confirmed
`create_okf_directory_baseline`/`ensure_okf_directory_baseline`'s real
current bodies, all four real wrapper call sites, and `append_person_note_
update_line`'s three real call sites' actual line shapes before writing the
task, confirming none begin with `# `); `BUG-028` is a finalised ledger
entry, not Draft; no ADR touched (architect's own pass already confirmed
this, unchanged here); no `ESCALATIONS.md` entry; the task is single-
session-sized (one file, one shared helper plus four mechanical call-site
edits); both locked ACs have a real, directly-observable file-content
outcome; no contradictory inputs; and the fix mechanism was already fully
decided by the architect's own pass, leaving no genuinely unclear or
multiple-equally-valid decomposition choice this pass.
