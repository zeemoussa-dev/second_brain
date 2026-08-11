---
id: REQ-SB-14-US-01-T04
title: New POST /poc/retrofit-customer-hub-links endpoint
parent_story: REQ-SB-14-US-01
requirement_id: REQ-SB-14
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-14-US-01-T02]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-14-US-01-T04 — New POST /poc/retrofit-customer-hub-links endpoint

## Parent Story

- Story: [[REQ-SB-14-US-01]] — `../UserStories/REQ-SB-14-US-01-vault-graph-connectivity.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-14 *Vault Graph Connectivity*

---

## Objective

Expose T02's `retrofit_customer_hub_links` batch operation as a new one-off
HTTP endpoint, matching the existing `/poc/backfill-tags` and
`/poc/flatten-customer-folders` one-off-migration-endpoint precedent, so the
operator can trigger the one-time retrofit against the real vault.

---

## Starting State → End State

**Before / Inputs:**
- `email_poc_router.py` has `/poc/classify-emails`, `/poc/backfill-tags`,
  `/poc/flatten-customer-folders`, each a thin wrapper calling one business
  function and tallying its results list.
- T02 added `app/business/customer_hub_linking.retrofit_customer_hub_links`.

**After / Outputs:**
- A new `POST /poc/retrofit-customer-hub-links` route, same thin shape as
  the three existing routes.

---

## Files to Modify

- `src/backend/app/api/email_poc_router.py`:
  1. Add to the import block:
     ```python
     from app.business.customer_hub_linking import retrofit_customer_hub_links
     ```
  2. Append the new route at the end of the file:
     ```python
     @router.post("/retrofit-customer-hub-links")
     def retrofit_customer_hub_links_endpoint() -> dict:
         results = retrofit_customer_hub_links()
         linked = sum(1 for r in results if r["status"] == "linked")
         hub_notes_created = sum(1 for r in results if r.get("hub_created"))
         return {
             "notes_checked": len(results),
             "linked": linked,
             "hub_notes_created": hub_notes_created,
             "results": results,
         }
     ```

---

## Constraints

- Inherits from parent story (ADR-003: `api/` calls into `business/` only,
  never `data_access/` directly).
- Must NOT modify the three existing routes or their imports.
- Idempotent by construction (delegates entirely to T02's
  `retrofit_customer_hub_links`, already idempotent) — safe to call
  repeatedly against the real live vault.

---

## Tests

**Manual verification steps (run in this order, live against the real
configured vault — `VAULT_PATH` in `src/backend/.env`):**

1. Start the dev server: `.venv\Scripts\python.exe -m uvicorn app.main:app
   --reload` from `src/backend` (note: this also fires one real email
   capture run on startup per ADR-005 — an unrelated, already-known side
   effect).
2. List `Work/Customers/` and identify a customer that has one or more
   existing `Work/<Kind>/*.md` notes with `customer: <that customer>`
   frontmatter but no `Work/Customers/<Customer>.md` hub note yet. (If every
   customer already has a hub note, pick any existing customer-tagged note
   that has no wikilink in its body yet, or temporarily note the pre-state
   of one that does, to compare against.)
3. `Invoke-RestMethod -Method Post
   http://127.0.0.1:8000/poc/retrofit-customer-hub-links`.
   - **[REQ-SB-14-US-01-AC-01]** Confirm a hub note now exists at
     `Work/Customers/<Customer>.md` matching the Scenario-1 schema
     (`type: Customer`, `customer:`, `tags: [customer/<slug>,
     kind/customer]`, `affiliate_of: ""`) for the customer identified in
     step 2.
   - **[REQ-SB-14-US-01-AC-02]** Confirm that customer's pre-existing,
     previously-unlinked note now has `**Customer:**
     [[<hub-note-stem>]]` as the first line of its body — the wikilink
     Obsidian's graph view resolves into an edge to the hub note (this
     project's established inline-body-wikilink convention already drives
     the graph reliably, per `architecture.md`; not independently
     re-screenshotted here).
4. Manually add a distinctive line (e.g. `## My Notes\nManually added
   overview text.`) to the hub note's body from step 3 via the Edit tool —
   simulating user-added content beyond the auto-populated baseline.
5. `Invoke-RestMethod -Method Post
   http://127.0.0.1:8000/poc/retrofit-customer-hub-links` again.
   - **[REQ-SB-14-US-01-AC-04]** Confirm the hub note's manually-added line
     from step 4 is still present, unchanged, and its baseline frontmatter
     keys are unchanged (no wholesale rewrite).
   - **[REQ-SB-14-US-01-AC-01]** (idempotency half) Confirm no second/
     duplicate hub note file was created for that customer.
   - **[REQ-SB-14-US-01-AC-05]** Confirm the note linked in step 3 is
     byte-for-byte unchanged by this second run — no duplicate
     `**Customer:** [[...]]` line was added.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `POST /poc/retrofit-customer-hub-links` creates missing hub notes for
      every customer with existing customer-tagged notes
- [x] Existing customer-tagged notes gain the wikilink to their hub note
- [x] Manually-added hub-note content survives a rerun; only missing
      baseline frontmatter keys are ever inserted
- [x] A second run is a true no-op on already-linked notes/already-created
      hub notes — no duplicates
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision/pattern/constraint emerged; see Implementation Log)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The retrofit logic itself (the loop, the per-note decision) — that is T02;
  this task only adds the HTTP wrapper.
- The per-write capture hook — that is T03 (verifies AC-03 separately).

---

## Context / Notes

Matches `/poc/backfill-tags`/`/poc/flatten-customer-folders`'s exact shape:
router imports one business function, calls it, tallies simple counts from
the results list, returns a dict. No new dependency, no request body/query
params needed (mirrors `/poc/backfill-tags`, which also takes none).

---

## Implementation Log

**Coder pass (2026-08-11):** Edited `src/backend/app/api/email_poc_router.py`
exactly as specified in `## Files to Modify` — no other line changed:
1. Added `from app.business.customer_hub_linking import
   retrofit_customer_hub_links` to the import block (alongside the three
   existing `from app.business...` imports).
2. Appended `retrofit_customer_hub_links_endpoint` (`POST
   /poc/retrofit-customer-hub-links`) at the end of the file, exact shape
   from the task spec — thin wrapper, tallies `linked` and
   `hub_notes_created` from the results list. The three existing routes
   (`/classify-emails`, `/backfill-tags`, `/flatten-customer-folders`) and
   their imports are untouched.

**Verification setup (manual mode, real live vault, no automated test
tooling yet):** Started the dev server (`.venv\Scripts\python.exe -m
uvicorn app.main:app --reload` from `src/backend`), which — per MEMORY.md's
already-documented constraint — fired one real scheduled capture run on
startup (an unrelated, already-known side effect, not part of this task's
own logic).

**Assumption logged for spot-check (scope-internal, same shape as T03's):**
Step 2 of this task's `## Tests` says to find a customer with existing
customer-tagged notes but no hub note yet, suggesting ADNOC as an obvious
multi-note candidate. By the time I checked (after the startup capture run,
which — now that T03 wired the per-write hub-linking hook into
`email_classification.py` — also creates/links hub notes as a side effect
of whatever it captures), `Work/Customers/ADNOC.md` already existed
(created by that startup run's own hook call, not by this task's
endpoint), so ADNOC no longer fit the "missing hub note" scenario cleanly.
Rescanned the vault and substituted **TAQA** — confirmed via a fresh scan
that TAQA had multiple existing `customer: "TAQA"` notes and no
`Work/Customers/TAQA.md` — as the AC-01/AC-02 candidate instead. This is
the exact "vault state doesn't match a clean scenario, adapt using
judgement" fallback anticipated by this task's own Tests step 2 wording
("If every customer already has a hub note, pick any existing
customer-tagged note..."), not a deviation from AC intent. No other
assumption made.

**Verification — REQ-SB-14-US-01-AC-01 and AC-02 (first
`POST /poc/retrofit-customer-hub-links` call):**

Pre-call baseline confirmed: `Work/Customers/` contained only `ADNOC.md`
and `Masdar.md` (both created by the live capture pipeline's own hook
before this task's endpoint was ever called); `TAQA` had multiple
`customer: "TAQA"`-tagged notes (e.g. `2026-08-06-Re- Sovereignty - Oracle
on Azure (TAQA)-21350000.md`) and no hub note; that note's body had no
`**Customer:**` wikilink.

Called `Invoke-RestMethod -Method Post
http://127.0.0.1:8000/poc/retrofit-customer-hub-links` → `{"notes_checked":
44, "linked": 38, "hub_notes_created": 5, "results": [...]}`. The TAQA
Sovereignty note's result entry: `{"status": "linked", "hub_note_path":
".../Work/Customers/TAQA.md", "hub_created": true, "linked": true}`.

- **AC-01:** Read `Work/Customers/TAQA.md` — created with exactly the
  Scenario-1 schema: `type: "Customer"`, `customer: "TAQA"`, `tags:
  ["customer/taqa", "kind/customer"]`, `affiliate_of: ""`. **PASS.**
- **AC-02:** Read the TAQA Sovereignty note — its body now begins
  `**Customer:** [[TAQA]]` immediately after the frontmatter block, before
  the rest of the original email content (unchanged otherwise). This is
  this project's established inline-body-wikilink convention, which
  Obsidian's graph view resolves into an edge (per `architecture.md`; not
  independently re-screenshotted here, per this task's own Tests
  wording). **PASS.**

**Verification — REQ-SB-14-US-01-AC-04, AC-01 (idempotency half), AC-05
(second `POST /poc/retrofit-customer-hub-links` call):**

Recorded the linked TAQA note's SHA-256 hash
(`772506E3A538DE07481C176B8A8227DD206D684CDE1B49EE65C89568397FB4DE`) before
the second call. Manually edited `Work/Customers/TAQA.md` via the Edit
tool, appending a distinctive line beyond the auto-populated baseline:
```
## My Notes
Manually added overview text — REQ-SB-14-US-01-T04 verification marker, distinctive-line-2026-08-11.
```
Called the endpoint again → `{"notes_checked": 49, "linked": 0,
"hub_notes_created": 0, ...}` (the `notes_checked` rise from 44→49 reflects
new notes the scheduled capture wrote to the vault between the two calls —
an unrelated side effect of the already-running scheduler, not this
endpoint's own logic). The TAQA Sovereignty note's result entry on this
second run: `{"status": "already_linked", "hub_created": false, "linked":
false}`.

- **AC-04:** Read `Work/Customers/TAQA.md` after the second call — the
  manually-added `## My Notes` line is present, unchanged; the four
  baseline frontmatter keys (`type`, `customer`, `tags`, `affiliate_of`)
  are unchanged; no wholesale rewrite occurred. **PASS.**
- **AC-01 (idempotency half):** `Get-ChildItem` on `Work/Customers/`
  filtered to `TAQA*` shows exactly one file, `TAQA.md` — no
  second/duplicate hub note was created. **PASS.**
- **AC-05:** Re-hashed the TAQA Sovereignty note after the second call —
  identical SHA-256
  (`772506E3A538DE07481C176B8A8227DD206D684CDE1B49EE65C89568397FB4DE`),
  confirming byte-for-byte unchanged; no duplicate `**Customer:** [[...]]`
  line was added. **PASS.**

**Cleanup:** stopped the dev server (`Stop-Process` on the uvicorn reloader
and server processes it spawned); confirmed via `Get-Process python` that
no python process remains running.

**`gate: flagged` (`gate_reason: trigger-1`)** — the ADNOC→TAQA
test-candidate substitution above is a scope-internal assumption (no new
dependency, no shared-interface change, no ADR deviation, no unanticipated
file, no unclear/contradictory requirement), logged here for human
spot-check per the coder's role. `REVIEW-QUEUE.md` pointer added.

**MEMORY.md:** not updated — no new decision/pattern/constraint emerged.
The endpoint is a pure thin-wrapper mirror of the three existing
`/poc/*` routes, exactly as the task and story's architect notes already
specified. The observation that the already-documented "every dev-server
start fires a real capture run with real vault-write side effects"
constraint now also covers hub-note creation/linking (since T03 wired
the hook into the capture pipeline) doesn't need a new/updated entry — the
existing MEMORY.md wording ("vault writes against the live
`.env`-configured vault") already covers this without needing to be more
specific.

**Story-level note:** this was the last task in `REQ-SB-14-US-01`
(`T01`/`T02`/`T03` already `Done`); all five of the story's locked ACs
(`AC-01` through `AC-05`) are now verified — `AC-03` live in `T03`, the
rest live here. Per this task's own scope, propagating the parent story's
`status:`/`BACKLOG.md` is left to the orchestrator, not done by this task
directly.

---

**Orchestrator review (2026-08-11):** the ADNOC→TAQA substitution is exactly
the fallback this task's own Tests step 2 anticipated ("if every customer
already has a hub note, pick any existing customer-tagged note..."), and
ADNOC lost its "missing hub note" status only because T03's own newly-wired
hook fired first during the startup capture run — a direct, expected
consequence of the story's own prior task, not an error. Reviewed and
approved — `gate: flagged → clear`.
