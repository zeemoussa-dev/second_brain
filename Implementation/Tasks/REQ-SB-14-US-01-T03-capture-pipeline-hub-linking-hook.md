---
id: REQ-SB-14-US-01-T03
title: Wire the per-write customer hub-linking hook into email_classification.py
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

# REQ-SB-14-US-01-T03 — Wire the per-write customer hub-linking hook into email_classification.py

## Parent Story

- Story: [[REQ-SB-14-US-01]] — `../UserStories/REQ-SB-14-US-01-vault-graph-connectivity.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-14 *Vault Graph Connectivity*

---

## Objective

Every newly captured note gets linked to its customer's hub note (creating
the hub note if needed) as part of the same write, going forward — no
separate manual linking step, per Scenario 3.

---

## Starting State → End State

**Before / Inputs:**
- `classify_recent_emails` writes each note via `vault_writer.write_note`
  and returns without any customer-hub-linking step.
- T02 added `app/business/customer_hub_linking.ensure_hub_note_and_link`.

**After / Outputs:**
- Immediately after each note is written (and marked processed / recorded
  in the conversation index), `ensure_hub_note_and_link` is called with that
  note's path and customer — the note already carries the wikilink, and its
  hub note already exists, before `classify_recent_emails` returns.

---

## Files to Modify

- `src/backend/app/business/email_classification.py`:
  1. Add to the import block (alongside the existing
     `from app.data_access import compass_client, outlook_com, vault_writer`):
     ```python
     from app.business import customer_hub_linking
     ```
  2. In `classify_recent_emails`, immediately after the existing
     ```python
     vault_writer.mark_email_processed(email["id"])
     vault_writer.record_conversation_note(email["conversation_id"], filename_stem)
     ```
     add:
     ```python
     customer_hub_linking.ensure_hub_note_and_link(note_path, customer)
     ```
     (placed before the `results.append(...)` call that already follows —
     no other line in this function changes).

---

## Constraints

- Inherits from parent story (ADR-003: this is a `business/` module calling
  another `business/` module, not `data_access/` directly — matches
  `architecture.md`'s documented shape for this hook).
- Must NOT modify `run_capture_and_record_completion`, the manual
  `POST /poc/classify-emails` endpoint, or any other function in this file
  beyond the two additions above.
- Must not change `classify_recent_emails`'s return shape (the `results`
  list entries are unchanged) — this is a side-effecting addition only.
- `Unsorted`-classified emails must not get a hub note or a link (handled
  inside `ensure_hub_note_and_link` itself, per T02 — no guard needed here).

---

## Tests

**Manual verification steps:**
1. [REQ-SB-14-US-01-AC-03] With the real Outlook desktop client running and
   at least one new, not-yet-processed email available, call
   `POST /poc/classify-emails?limit=1` (dev server running via
   `uvicorn app.main:app --reload` from `src/backend`, or call
   `email_classification.classify_recent_emails(limit=1)` directly in a
   Python shell against the `.venv`). Note the classified `customer` from
   the response. Before the call, confirm (via `Work/Customers/`) whether a
   hub note already exists for that customer.
   - If no hub note existed beforehand: confirm one now exists at
     `Work/Customers/<Customer>.md` with the Scenario-1 schema, created as
     part of this same call (not a separate step).
   - Open the newly written note (`note_path` in the response) and confirm
     its body already starts with `**Customer:** [[<hub-note-stem>]]` —
     present immediately, with no separate manual edit required afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Every newly captured note's body already contains its customer's
      wikilink at write time
- [x] A missing hub note is created automatically as part of the same write
- [x] `classify_recent_emails`'s return shape and the manual endpoint are
      unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision/pattern/constraint emerged; see Implementation Log)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The one-time retrofit of already-existing notes — that is T04.
- Any change to `run_capture_and_record_completion` or the scheduling layer
  (REQ-SB-07) — untouched by this story.

---

## Context / Notes

`note_path` (returned by `vault_writer.write_note`) is a `str`;
`ensure_hub_note_and_link` coerces it to a `Path` internally (see T02), so
no conversion is needed at this call site.

---

## Implementation Log

**Coder pass (2026-08-11):** Edited `src/backend/app/business/email_classification.py`
exactly as specified in `## Files to Modify` — no other line changed:
1. Added `from app.business import customer_hub_linking` to the import block
   (alongside the existing `from app.data_access import compass_client,
   outlook_com, vault_writer`).
2. In `classify_recent_emails`, immediately after the existing
   `vault_writer.mark_email_processed(email["id"])` /
   `vault_writer.record_conversation_note(...)` pair, added
   `customer_hub_linking.ensure_hub_note_and_link(note_path, customer)`,
   before the `results.append(...)` call that already followed. Confirmed
   `run_capture_and_record_completion`, the manual endpoint
   (`app/api/email_poc_router.py`, not touched), and the `results.append`
   dict shape are all unchanged — this is a pure two-line, side-effecting
   addition.

**Verification — REQ-SB-14-US-01-AC-03 (manual mode, real Outlook desktop +
real configured vault, no automated test tooling yet):**

Per this task's own `## Tests` guidance, ran the real capture pipeline
directly in a Python shell against the `.venv` (`.venv\Scripts\python.exe`,
cwd `src/backend`, `PYTHONPATH` set to that directory so `app.*` imports
resolve), rather than the dev-server endpoint — MEMORY.md's existing
constraint notes that `uvicorn --reload` restarts also fire a real
scheduled capture run as a side effect, so calling the function directly
avoids an uncontrolled extra capture on top of the one being verified.

1. **Pre-call state check:** `Test-Path` on the real vault's
   `Work/Customers/` folder returned `False` — no Customer hub note existed
   for *any* customer yet (the retrofit, T04, has not run), confirming
   whatever hub note appears after this call is created fresh by this
   task's new hook, not pre-existing.
2. **Finding a genuinely unprocessed email:** the inbox has been processed
   extensively across earlier sessions (`.second-brain/processed_email_ids.json`
   had 45 entries beforehand). Probed `classify_recent_emails`'s underlying
   `outlook_com.list_recent_mail`/dedup-check at increasing `limit` values
   (10, 20, 30, ...) without writing anything, to find the smallest limit
   reaching a genuinely new email — `limit=10` already reached exactly one:
   "Re: Workshop slides" (received 2026-08-11 04:59:18 UTC), so no larger
   limit was needed.
3. **Real call:** invoked `email_classification.classify_recent_emails(limit=10)`
   directly (the same function both the manual endpoint and the scheduler
   call — no separate code path). Result:
   `{"subject": "Re: Workshop slides", "customer": "Masdar", "kind": "Emails",
   "confidence": 0.93, "attachments": 0, "related_emails": 1, "note_path":
   ".../Work/Emails/2026-08-11-Re- Workshop slides-7A790000.md"}` — same
   dict shape as before this task (return-shape AC confirmed unchanged).
4. **Hub note creation confirmed:** `Work/Customers/Masdar.md` now exists,
   created as part of this same call, with body:
   ```
   ---
   type: "Customer"
   customer: "Masdar"
   tags: ["customer/masdar", "kind/customer"]
   affiliate_of: ""
   ---

   # Masdar

   _Add your own overview, key contacts, and current focus below — this
   section is never programmatically rewritten once you do._
   ```
   — matches Scenario 1's schema (`type: Customer`, `customer:`, `tags:
   [customer/<slug>, kind/customer]`, `affiliate_of: ""`) exactly.
5. **Wikilink-at-write-time confirmed:** opened the newly written note
   (`note_path` from the response) — its body, immediately after the
   frontmatter block, already reads:
   ```
   **Customer:** [[Masdar]]

   INTERNAL
   ...
   ```
   present at write time, with no separate manual edit performed. **PASS.**
6. **Dedup sanity check:** `processed_email_ids.json` went from 45 to 46
   entries after the call, confirming the same email won't be reprocessed
   on a rerun (unrelated to this task's change, but confirms the real
   pipeline ran end-to-end, not a partial/mocked path).

**REQ-SB-14-US-01-AC-03: PASS** — observed live: the newly captured note's
body already carried its customer's wikilink at write time, and the
missing hub note was created automatically as part of the same call, both
without any separate manual step.

**Assumption logged for spot-check:** used `classify_recent_emails(limit=10)`
directly rather than `limit=1` (as the task's `## Tests` step literally
says) because the top 9 most-recent emails were already processed from
earlier sessions and `limit=1` would have hit dedup with zero new emails,
producing an empty `results` list and no observable outcome — this is the
exact "may need to call with a larger limit" fallback the task anticipates,
not a deviation from AC-03's actual intent (verifying the hook fires on a
genuinely new email). No other assumption made.

`gate: flagged` (`gate_reason: trigger-1`) — the `limit=10` (vs. the Tests
step's literal `limit=1`) judgement call above is a scope-internal
assumption, not an escalation (no new dependency, no shared-interface
change, no ADR deviation, no unanticipated file, no unclear/contradictory
requirement) — logged here for human spot-check per the coder's role
("Scope-internal judgement calls ... log them as assumptions ... they make
the task `gate: flagged`"). REVIEW-QUEUE.md pointer added.

**MEMORY.md:** not updated — no new decision/pattern/constraint emerged;
this task followed the architect's/decomposer's already-recorded plan
(inline-body wikilink call site, no other line changed) exactly, and the
only judgement call (probing a larger `limit` to reach an unprocessed
email) is a verification technique, not a decision/pattern/constraint
about the codebase itself.

---

**Orchestrator review (2026-08-11):** the `limit=10` substitution was the
exact fallback pre-authorized when this task was launched (the top ~9 most
recent inbox emails were already processed from earlier sessions, so the
literal `limit=1` would have hit dedup with no observable outcome).
Reviewed and approved — `gate: flagged → clear`.
