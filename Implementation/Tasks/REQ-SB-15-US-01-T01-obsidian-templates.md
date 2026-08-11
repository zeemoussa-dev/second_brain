---
id: REQ-SB-15-US-01-T01
title: Author the four Obsidian core-Templates note-type templates
parent_story: REQ-SB-15-US-01
requirement_id: REQ-SB-15
type: content
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-15-US-01-T01 — Author the four Obsidian core-Templates note-type templates

## Parent Story

- Story: [[REQ-SB-15-US-01]] — `../UserStories/REQ-SB-15-US-01-manual-entry-templates-and-guide.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-15 *Manual-Entry Templates & Guidelines*

---

## Objective

Author the four Obsidian core-Templates-plugin template files (Customer,
Opportunity, Agreement, Consumption-Snapshot) at the architect-decided
`Templates/` vault root, each pre-filling the resolved schema from
`Implementation/Plans/2026-08-10-vault-taxonomy-draft.md` field-for-field,
plus the customer wikilink placement convention `REQ-SB-14-US-01`
established (inline body `**Customer:** [[Hub]]`).

**This is vault-content authoring, not application code.** No
`src/backend`/`src/frontend` file is touched by this task — every path below
is vault-relative, resolved against `VAULT_PATH` in `src/backend/.env` (the
coder reads that value, then writes/edits the files directly at
`<VAULT_PATH>/Templates/*.md` with the Write/Edit tools).

---

## Starting State → End State

**Before / Inputs:**
- `Templates/` does not yet exist as a vault root (per ADR-006, newly
  decided this `/plan-tasks` pass).
- The resolved schema for all four note types, and the inline-wikilink
  convention, are both already documented (taxonomy plan;
  `architecture.md`'s "Customer Hub Notes & Graph Linking" section).

**After / Outputs:**
- `Templates/Customer.md`, `Templates/Opportunity.md`,
  `Templates/Agreement.md`, `Templates/Consumption-Snapshot.md` all exist,
  vault-relative, each schema-matching and (except Customer, which is the
  hub note itself) carrying the customer-wikilink body line.

---

## Files to Modify

<!-- Vault-relative paths, resolved against VAULT_PATH in src/backend/.env
— not src/backend or src/frontend paths. -->

- `Templates/Customer.md` (new file):

  ```markdown
  ---
  type: Customer
  customer: REPLACE_WITH_CUSTOMER_NAME
  tags: [customer/replace-with-customer-slug, kind/customer]
  affiliate_of: ""
  ---

  # {{title}}

  _Add your own overview, key contacts, and current focus below — this
  section is never programmatically rewritten once you do._

  ## Overview

  ## Key Contacts

  ## Current Focus
  ```

  No self-referential customer wikilink — a hub note does not link to
  itself; this mirrors the auto-created baseline body
  `REQ-SB-14-US-01-T01`'s `create_customer_hub_note_baseline` writes, for
  structural parity (Scenario 1).

- `Templates/Opportunity.md` (new file):

  ```markdown
  ---
  type: Opportunity
  customer: REPLACE_WITH_CUSTOMER_NAME
  stage: REPLACE_WITH_STAGE
  value_usd: 0
  description: ""
  tags: [customer/replace-with-customer-slug, kind/opportunity]
  ---

  # {{title}}

  **Customer:** [[REPLACE_WITH_CUSTOMER_NAME]]

  ## Notes
  ```

- `Templates/Agreement.md` (new file):

  ```markdown
  ---
  type: Agreement
  customer: REPLACE_WITH_CUSTOMER_NAME
  start_date: "YYYY-MM-DD"
  end_date: "YYYY-MM-DD"
  value_usd: 0
  status: active
  tags: [customer/replace-with-customer-slug, kind/agreement]
  ---

  # {{title}}

  **Customer:** [[REPLACE_WITH_CUSTOMER_NAME]]

  ## Notes
  ```

- `Templates/Consumption-Snapshot.md` (new file):

  ```markdown
  ---
  type: Consumption-Snapshot
  customer: REPLACE_WITH_CUSTOMER_NAME
  snapshot_date: "YYYY-MM-DD"
  azure_consumption_usd: 0
  tags: [customer/replace-with-customer-slug, kind/consumption-snapshot]
  ---

  # {{title}}

  **Customer:** [[REPLACE_WITH_CUSTOMER_NAME]]
  ```

---

## Constraints

- Must use only Obsidian's **core** Templates plugin syntax (`{{title}}` —
  no Templater-style dynamic scripting).
- Frontmatter keys/shape must match the taxonomy plan field-for-field —
  do not add, rename, or drop a key.
- `REPLACE_WITH_...` / `"YYYY-MM-DD"` placeholders must remain valid YAML
  as-written (Scenario 6) — no placeholder may break frontmatter parsing.
- `affiliate_of` stays blank (`""`) by default — only ever set by hand, for
  an actual Affiliate note.
- Nothing besides these four files goes in `Templates/` — the folder is
  configured as Obsidian's "Insert Template" source, and every file in it
  is listed as insertable.
- No `src/backend`/`src/frontend` file may be touched by this task.

---

## Tests

<!-- Obsidian's own "Insert Template" UI action is a manual human step this
coder subagent cannot drive interactively — per the story's own framing,
verification here means inspecting the written template files directly
(their literal frontmatter/body content) and cross-checking field-for-field
against the resolved schema, not literally exercising Obsidian's UI. -->

**Manual verification steps:**
1. [REQ-SB-15-US-01-AC-01] Read `Templates/Customer.md` from the real vault
   (`VAULT_PATH` in `src/backend/.env`). Confirm its frontmatter block
   parses as valid YAML and contains exactly `type: Customer`, `customer:`,
   `tags: [customer/..., kind/customer]`, `affiliate_of:` — matching
   `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`'s Customer
   schema field-for-field, and structurally identical in shape (same four
   frontmatter keys, same auto-body-stub pattern) to what
   `REQ-SB-14-US-01-T01`'s `create_customer_hub_note_baseline` produces.
2. [REQ-SB-15-US-01-AC-02] Read `Templates/Opportunity.md`. Confirm valid
   YAML frontmatter with exactly `type: Opportunity`, `customer:`,
   `stage:`, `value_usd:`, `description:`, `tags: [customer/...,
   kind/opportunity]` — matching the taxonomy plan's Opportunity schema
   field-for-field.
3. [REQ-SB-15-US-01-AC-03] Read `Templates/Agreement.md`. Confirm valid
   YAML frontmatter with exactly `type: Agreement`, `customer:`,
   `start_date:`, `end_date:`, `value_usd:`, `status:`, `tags:
   [customer/..., kind/agreement]` — matching the taxonomy plan's Agreement
   schema field-for-field.
4. [REQ-SB-15-US-01-AC-04] Read `Templates/Consumption-Snapshot.md`.
   Confirm valid YAML frontmatter with exactly `type:
   Consumption-Snapshot`, `customer:`, `snapshot_date:`,
   `azure_consumption_usd:`, `tags: [customer/..., kind/consumption-
   snapshot]` — matching the taxonomy plan's Consumption-Snapshot schema
   field-for-field. Confirm the template itself contains no logic that
   could edit an existing snapshot note (it is a fresh-note template only,
   satisfying the append-only-in-spirit second clause by construction —
   inserting it always targets a new note the user just created).
5. [REQ-SB-15-US-01-AC-06] Confirm `Templates/Customer.md`'s
   `affiliate_of: ""` (left at its template-provided default, the
   scenario's own example) parses as valid YAML on its own — i.e., the
   frontmatter block is syntactically complete and correct with that field
   left blank, not requiring it to be filled in for the block to parse.

**Automated tests:** `n/a — test tooling pending; this is vault content, not
application code, so no pytest/vitest coverage applies`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] All four template files exist at `Templates/<Type>.md`, vault-relative
- [x] Each matches its resolved schema field-for-field
- [x] Customer template is structurally parallel to
      `REQ-SB-14-US-01`'s auto-created hub note baseline
- [x] Opportunity/Agreement/Consumption-Snapshot templates carry the inline
      `**Customer:** [[REPLACE_WITH_CUSTOMER_NAME]]` wikilink line
- [x] Every placeholder value remains valid YAML as-written
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (not applicable — none emerged, see Implementation Log)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The in-vault guide note — that is T02.
- Configuring Obsidian's Settings → Templates → "Template folder location"
  to point at `Templates/` — a one-time manual step in the user's own
  Obsidian install (ADR-006), not something this task scripts or verifies.
- Any `src/backend`/`src/frontend` code change — none is implied.
- Frontmatter schema validation/enforcement tooling — out of scope per the
  taxonomy plan's own non-goals.

---

## Context / Notes

`REPLACE_WITH_CUSTOMER_NAME` / `REPLACE_WITH_STAGE` / `"YYYY-MM-DD"` are
this task's own placeholder convention — loud, unambiguous, and impossible
to leave in by accident, while still valid YAML/Obsidian-tag-safe (no
characters Obsidian's tag parser rejects) if a user forgets to edit them.
The guide note (T02) explains what to replace them with.

---

## Implementation Log

**Coder pass (2026-08-11):** Read `VAULT_PATH` from `src/backend/.env`
(value not reproduced here per the task's own instruction to extract only
that key). `Templates/` did not yet exist in the vault. Wrote the four
template files verbatim from this task's `## Files to Modify` block, using
the Write tool, directly at `<VAULT_PATH>/Templates/*.md`:
`Templates/Customer.md`, `Templates/Opportunity.md`,
`Templates/Agreement.md`, `Templates/Consumption-Snapshot.md`. No
`src/backend`/`src/frontend` file touched — matches the task's own
Constraints. No deviation from the literal content specified in the task.

**Verification (manual mode — direct file inspection, per this task's own
`## Tests` framing that Obsidian's "Insert Template" UI is a human-only
step outside what a coder subagent can drive):**

Read all four files back from the real vault, and additionally ran a
YAML-frontmatter parse check (`py -c "... yaml.safe_load(...)"` against the
literal bytes on disk, isolating each file's `---`-delimited frontmatter
block) to confirm "parses as valid YAML" beyond visual inspection alone.

- **[REQ-SB-15-US-01-AC-01]** PASS. `Templates/Customer.md` frontmatter
  parsed to exactly `{type: Customer, customer:
  REPLACE_WITH_CUSTOMER_NAME, tags: [customer/replace-with-customer-slug,
  kind/customer], affiliate_of: ''}` — matches the taxonomy plan's Customer
  schema field-for-field (same 4 keys, no additions/renames/drops).
  Structurally parallel to `REQ-SB-14-US-01-T01`'s
  `create_customer_hub_note_baseline` (`app/data_access/vault_writer.py`
  lines 294-317, read for comparison): same 4 frontmatter keys in the same
  order, same auto-body-stub sentence verbatim ("Add your own overview, key
  contacts, and current focus below — this section is never
  programmatically rewritten once you do."). No self-referential customer
  wikilink, as specified — matches the hub-note baseline's own lack of one.
- **[REQ-SB-15-US-01-AC-02]** PASS. `Templates/Opportunity.md` frontmatter
  parsed to exactly `{type: Opportunity, customer:
  REPLACE_WITH_CUSTOMER_NAME, stage: REPLACE_WITH_STAGE, value_usd: 0,
  description: '', tags: [customer/replace-with-customer-slug,
  kind/opportunity]}` — matches the taxonomy plan's Opportunity schema
  field-for-field. Body carries `**Customer:** [[REPLACE_WITH_CUSTOMER_NAME]]`.
- **[REQ-SB-15-US-01-AC-03]** PASS. `Templates/Agreement.md` frontmatter
  parsed to exactly `{type: Agreement, customer:
  REPLACE_WITH_CUSTOMER_NAME, start_date: 'YYYY-MM-DD', end_date:
  'YYYY-MM-DD', value_usd: 0, status: active, tags:
  [customer/replace-with-customer-slug, kind/agreement]}` — matches the
  taxonomy plan's Agreement schema field-for-field. Body carries
  `**Customer:** [[REPLACE_WITH_CUSTOMER_NAME]]`.
- **[REQ-SB-15-US-01-AC-04]** PASS. `Templates/Consumption-Snapshot.md`
  frontmatter parsed to exactly `{type: Consumption-Snapshot, customer:
  REPLACE_WITH_CUSTOMER_NAME, snapshot_date: 'YYYY-MM-DD',
  azure_consumption_usd: 0, tags: [customer/replace-with-customer-slug,
  kind/consumption-snapshot]}` — matches the taxonomy plan's
  Consumption-Snapshot schema field-for-field. Body carries `**Customer:**
  [[REPLACE_WITH_CUSTOMER_NAME]]`. The file contains no logic of any kind
  (it is static template markup with only `{{title}}` core-Templates
  syntax) — inserting it always creates a brand-new note under
  `Work/Consumption/`, never edits an existing snapshot note, satisfying
  the append-only-in-spirit clause by construction.
- **[REQ-SB-15-US-01-AC-06]** PASS. `Templates/Customer.md`'s
  `affiliate_of: ""` parsed cleanly via `yaml.safe_load` in isolation (see
  parse output above: `affiliate_of: ''`) — the frontmatter block is
  syntactically complete and correct with that field left at its blank
  default; no fill-in required for the block to parse.

All 5 tagged verification steps in this task's `## Tests` (AC-01 through
AC-04, AC-06) passed. AC-05 belongs to sibling task T02 (guide note), not
this task.

**Assumption (scope-internal judgement call, logged per Pipeline.md §5, not
an escalation):** none beyond what the task file itself already specified
verbatim — all four files were written exactly as given in `## Files to
Modify`, no interpretation required.

**MEMORY.md:** not updated — no new decision/pattern/constraint emerged;
this task executed content already fully specified by ADR-006 and the
taxonomy plan, with no new judgement call of its own.

gate: clear 2026-08-11 — no triggers fired (no ADR change, no new
assumption beyond what the task already specified, no contradictory
inputs, all 5 tagged ACs verified against the real vault files).
