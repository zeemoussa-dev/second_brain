---
id: REQ-SB-15-US-01-T02
title: Author the in-vault Manual Entry Guide note
parent_story: REQ-SB-15-US-01
requirement_id: REQ-SB-15
type: content
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-15-US-01-T01]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-15-US-01-T02 — Author the in-vault Manual Entry Guide note

## Parent Story

- Story: [[REQ-SB-15-US-01]] — `../UserStories/REQ-SB-15-US-01-manual-entry-templates-and-guide.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-15 *Manual-Entry Templates & Guidelines*

---

## Objective

Author a single in-vault guide note, at the architect-decided
`Work/Guides/Manual-Entry-Guide.md`, explaining what each of the four note
types is for and how to use its Templates-feature template — living inside
the vault itself, not only as project-repo documentation.

**This is vault-content authoring, not application code.** The path below
is vault-relative, resolved against `VAULT_PATH` in `src/backend/.env`.

---

## Starting State → End State

**Before / Inputs:**
- T01 has authored the four template files this guide describes and
  references by exact path/name.
- No guide note exists yet.

**After / Outputs:**
- `Work/Guides/Manual-Entry-Guide.md` exists, explaining all four types and
  how to insert each type's template.

---

## Files to Modify

<!-- Vault-relative path, resolved against VAULT_PATH in src/backend/.env
— not a src/backend or src/frontend path. -->

- `Work/Guides/Manual-Entry-Guide.md` (new file):

  ```markdown
  ---
  type: Guide
  tags: [kind/guide]
  ---

  # Manual Entry Guide

  This vault has four note types you enter by hand — Customer, Opportunity
  (Pipeline), Agreement, and Consumption-Snapshot — one Obsidian template
  per type, all living in the `Templates/` folder. Automated email capture
  already creates and links Customer hub notes for you (see
  `Work/Customers/`); the other three types have no automated capture yet
  — you enter them here.

  ## How to insert a template

  1. Create (or open) the note you want to fill in, in the correct folder
     for its type (see each section below).
  2. Open the command palette (`Ctrl+P`), run **"Templates: Insert
     template"**, and choose the template matching the note type.
  3. Replace every `REPLACE_WITH_...` placeholder with the real value —
     the `customer:` frontmatter field and the `**Customer:**
     [[REPLACE_WITH_CUSTOMER_NAME]]` body line both need the exact same
     customer name/hub-note title, so the wikilink resolves to the right
     hub note.
  4. Leave `affiliate_of` blank unless this note is for an Affiliate of
     another Customer — then set it to that parent Customer's name.

  ## Customer

  **Folder:** `Work/Customers/` · **Template:** `Templates/Customer.md`

  A hub note, one per customer (or per Affiliate — an Affiliate is a
  Customer note with `affiliate_of:` set to its parent Customer's name, no
  separate note type). Automated email capture already creates and updates
  these for you; only create one by hand if you want to add a customer
  before any email for them has been captured yet, or to add your own
  overview/key-contacts/current-focus notes to an existing one — anything
  you add below the auto-populated frontmatter is never overwritten by
  automation.

  ## Opportunity (Pipeline)

  **Folder:** `Work/Pipeline/` · **Template:** `Templates/Opportunity.md`

  One note per sales opportunity/pipeline item for a customer. `stage:` is
  free text, not a fixed list — use whatever stage name you're tracking
  (e.g. `Prospecting`, `Negotiation`, `Closed-Won`); new stage names need no
  setup, the vault picks them up automatically.

  ## Agreement

  **Folder:** `Work/Agreements/` · **Template:** `Templates/Agreement.md`

  One note per signed agreement/contract with a customer. `status:` is one
  of `active`, `expired`, or `renewal-pending`.

  ## Consumption-Snapshot

  **Folder:** `Work/Consumption/` · **Template:**
  `Templates/Consumption-Snapshot.md`

  One note per point-in-time Azure consumption reading for a customer,
  **append-only** — always create a new snapshot note for a new reading
  (name it `<Customer>-<snapshot-date>.md`), never edit an existing
  snapshot note's numbers after the fact. "Latest consumption for a
  customer" is whichever snapshot note has the most recent
  `snapshot_date:`, found by searching notes tagged `customer/<slug>` and
  `kind/consumption-snapshot` — not a single always-updated file.
  ```

---

## Constraints

- Must live at `Work/Guides/Manual-Entry-Guide.md` — deliberately outside
  `Templates/`, so it is never listed by Obsidian's "Insert Template"
  picker (ADR-006).
- Must explain all four note types and how to use each one's template
  (Scenario 5) — no type may be omitted.
- Must accurately describe T01's actual template file paths/placeholder
  convention — write this task after T01 so the two stay consistent.
- No `src/backend`/`src/frontend` file may be touched by this task.

---

## Tests

<!-- The user opening this note "in Obsidian" (Scenario 5's Given) is a
manual human action; verification here inspects the written file's content
directly, the observable proxy available to a coder subagent. -->

**Manual verification steps:**
1. [REQ-SB-15-US-01-AC-05] Read `Work/Guides/Manual-Entry-Guide.md` from
   the real vault. Confirm it exists inside the vault itself (not only in
   this project's repo), and that it contains a section for each of the
   four note types (Customer, Opportunity, Agreement, Consumption-Snapshot)
   explaining what it's for and when to use it, plus instructions for using
   each type's Templates-feature template (folder + template name +
   how-to-insert steps). Confirm the folder/template names cited exactly
   match T01's actual output (`Templates/Customer.md`,
   `Templates/Opportunity.md`, `Templates/Agreement.md`,
   `Templates/Consumption-Snapshot.md`, and their respective
   `Work/<Kind>/` target folders).

**Automated tests:** `n/a — test tooling pending; this is vault content, not
application code, so no pytest/vitest coverage applies`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Guide note exists at `Work/Guides/Manual-Entry-Guide.md`, inside the
      real vault
- [x] Explains all four note types and when to use each
- [x] Explains how to use each type's Templates-feature template
- [x] Folder/template names cited match T01's actual files exactly
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (not applicable — none emerged, see Implementation Log)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The four template files themselves — that is T01.
- Any `src/backend`/`src/frontend` code change — none is implied.

---

## Context / Notes

`Guides` becomes a new dynamically-discoverable `kind` folder under the
existing `Work/<Kind>/` convention — `list_known_kinds()` already scans
folder names under `Work/`, so no code change is needed for it to be found;
this task adds no backend code regardless (vault-content authoring only).

---

## Implementation Log

**Coder pass (2026-08-11):** Read `VAULT_PATH` from `src/backend/.env`
(value not reproduced here per the task's own instruction to extract only
that key). Confirmed T01's four dependency files exist and are `Done`
(`Templates/Customer.md`, `Templates/Opportunity.md`,
`Templates/Agreement.md`, `Templates/Consumption-Snapshot.md`) before
authoring content that references them by exact name. Neither
`Work/Guides/` nor `Work/Guides/Manual-Entry-Guide.md` existed yet. Wrote
the guide note verbatim from this task's `## Files to Modify` block, using
the Write tool, directly at
`<VAULT_PATH>/Work/Guides/Manual-Entry-Guide.md`. No
`src/backend`/`src/frontend` file touched — matches the task's own
Constraints. No deviation from the literal content specified in the task.

**Verification (manual mode — direct file inspection, per this task's own
`## Tests` framing that opening the note "in Obsidian" is a human-only step
outside what a coder subagent can drive):**

- **[REQ-SB-15-US-01-AC-05]** PASS. Read
  `Work/Guides/Manual-Entry-Guide.md` back from the real vault (not just
  the project repo) — confirmed it exists inside the vault itself at
  `<VAULT_PATH>/Work/Guides/Manual-Entry-Guide.md`. Confirmed it contains a
  section for each of the four note types — `## Customer`, `## Opportunity
  (Pipeline)`, `## Agreement`, `## Consumption-Snapshot` — each explaining
  what it's for and when to use it, plus a shared "How to insert a
  template" section with step-by-step instructions (command palette →
  "Templates: Insert template" → placeholder replacement → `affiliate_of`
  guidance). Cross-checked every folder/template name cited against T01's
  actual written files: `Templates/Customer.md` (→ `Work/Customers/`),
  `Templates/Opportunity.md` (→ `Work/Pipeline/`),
  `Templates/Agreement.md` (→ `Work/Agreements/`),
  `Templates/Consumption-Snapshot.md` (→ `Work/Consumption/`) — all four
  match exactly, no naming drift from T01's output.

**Assumption (scope-internal judgement call, logged per Pipeline.md §5, not
an escalation):** none beyond what the task file itself already specified
verbatim — the guide note was written exactly as given in `## Files to
Modify`, no interpretation required.

**MEMORY.md:** not updated — no new decision/pattern/constraint emerged;
this task authored content already fully specified by the task file
itself, with T01's output confirmed to match before writing.

gate: clear 2026-08-11 — no triggers fired (no ADR change, no new
assumption beyond what the task already specified, no contradictory
inputs, the one locked AC verified against the real vault file).
