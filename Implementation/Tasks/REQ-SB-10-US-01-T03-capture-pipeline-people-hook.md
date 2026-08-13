---
id: REQ-SB-10-US-01-T03
title: Wire the per-write Person-note hook into email_classification.py
parent_story: REQ-SB-10-US-01
requirement_id: REQ-SB-10
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-10-US-01-T02]
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-10-US-01-T03 — Wire the per-write Person-note hook into email_classification.py

## Parent Story

- Story: [[REQ-SB-10-US-01]] — `../UserStories/REQ-SB-10-US-01-people-notes-from-email-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-10 *People Living Documents*

---

## Objective

Every newly captured email's sender automatically gets a Person note
created or topped-up as part of the same write, going forward — no separate
manual step afterward, per Scenario 7.

---

## Starting State → End State

**Before / Inputs:**
- `classify_recent_emails` already calls
  `customer_hub_linking.ensure_hub_note_and_link(note_path, customer)`
  immediately after writing each note, marking it processed, and recording
  it in the conversation index.
- T02 added `app/business/people_extraction.ensure_person_note_for_captured_email`.

**After / Outputs:**
- Immediately after the existing `ensure_hub_note_and_link` call, one
  additional call — `people_extraction.ensure_person_note_for_captured_email
  (email["sender_name"], email["sender_email"])` — ensures the sender's
  Person note exists and is up to date before `classify_recent_emails`
  returns.

---

## Files to Modify

- `src/backend/app/business/email_classification.py`:
  1. Add to the import block (alongside the existing
     `from app.business import customer_hub_linking`):
     ```python
     from app.business import customer_hub_linking, people_extraction
     ```
     (Replaces the single-name import with a two-name import from the same
     module — no other import line changes.)
  2. In `classify_recent_emails`, immediately after the existing
     ```python
     customer_hub_linking.ensure_hub_note_and_link(note_path, customer)
     ```
     add:
     ```python
     people_extraction.ensure_person_note_for_captured_email(
         email["sender_name"], email["sender_email"]
     )
     ```
     (placed before the `results.append(...)` call that already follows —
     no other line in this function changes).

---

## Constraints

- Inherits from parent story (ADR-003: `business/` calling another
  `business/` module, not `data_access/` directly — matches
  `architecture.md`'s documented shape for this hook).
- Must NOT modify `run_capture_and_record_completion`, the manual
  `POST /poc/classify-emails` endpoint, or any other function in this file
  beyond the import line and the two-line addition above.
- Must not change `classify_recent_emails`'s return shape (the `results`
  list entries are unchanged) — this is a side-effecting addition only.
- An email with a blank `sender_email` must not error the whole capture run
  (handled inside `ensure_person_note_for_captured_email` itself, per T02 —
  no guard needed here).

---

## Tests

**Manual verification steps:**
1. [REQ-SB-10-US-01-AC-07] (creation half) With the real Outlook desktop
   client running and at least one new, not-yet-processed email available
   from a sender with no existing Person note, call
   `email_classification.classify_recent_emails(limit=N)` directly in a
   Python shell against the `.venv` (`.venv\Scripts\python.exe`, cwd
   `src/backend`, `PYTHONPATH` set so `app.*` imports resolve) — increase
   `N` from a small starting value if the most recent emails are already
   processed (`.second-brain/processed_email_ids.json`), the same fallback
   REQ-SB-14-US-01-T03 used. Before the call, confirm (via `Work/People/`)
   that no Person note exists yet for that sender's email address. After
   the call, confirm a Person note now exists at
   `Work/People/<slug-of-lowercased-sender-email>.md` with `name`/`email`
   populated from that email's `sender_name`/`sender_email`, created as
   part of this same call — no separate manual step performed.
2. [REQ-SB-10-US-01-AC-07] (update half) Immediately afterward, call
   `people_extraction.ensure_person_note_for_captured_email(sender_name,
   sender_email)` again directly with the same sender's name/email
   (simulating a second captured email from the same sender) and confirm
   the returned dict has `created: False` — the existing Person note was
   topped up, not duplicated.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Every newly captured email's sender gets a Person note created or
      topped-up as part of the same write, with no separate manual step
- [x] A sender who already has a Person note is topped up, not duplicated
- [x] `classify_recent_emails`'s return shape and the manual endpoint are
      unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision/pattern/constraint emerged; see Implementation Log)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The one-time retrofit of already-existing Email notes — that is T04.
- Any change to `run_capture_and_record_completion` or the scheduling layer
  (REQ-SB-07) — untouched by this story.

---

## Context / Notes

`email["sender_name"]` and `email["sender_email"]` are the same two fields
already written into each note's frontmatter as `sender`/`sender_email`
(see the existing `vault_writer.write_note(...)` call earlier in this
function) — no new data extraction is needed, only passing the two values
already in scope to the new call.

---

## Implementation Log

**Coder pass (2026-08-11):** Edited `src/backend/app/business/email_classification.py`
exactly as specified in `## Files to Modify` — no other line changed:
1. Import line changed from `from app.business import customer_hub_linking`
   to `from app.business import customer_hub_linking, people_extraction`.
2. Added
   ```python
   people_extraction.ensure_person_note_for_captured_email(
       email["sender_name"], email["sender_email"]
   )
   ```
   immediately after the existing
   `customer_hub_linking.ensure_hub_note_and_link(note_path, customer)` call,
   before `results.append(...)`. `run_capture_and_record_completion`, the
   manual `POST /poc/classify-emails` endpoint, and every other line of the
   function are untouched.

**Verification (`REQ-SB-10-US-01-AC-07`, creation half):** Before the call,
confirmed `Work/People/` did not exist in the vault at all (no Person notes
of any kind — `Get-ChildItem` returned nothing), so any newly-captured
sender is guaranteed to be a fresh creation. Probed
`outlook_com.list_recent_mail`/dedup-check at `limit=10` (the function's own
default) without writing anything first — this already reached 2 genuinely
unprocessed emails (`already_processed` count was 47 of 47 fetched at
smaller past runs; at `limit=10` this run found 2 not yet in
`processed_email_ids.json`): "RE: Tadweer Group - Core42 Azure Services"
from Ahmad Hamzeh (`ahmad.hamzeh@core42.ai`) and "RE: URGENT: Request for
Sovereign Cloud & Compass Configuration Proposals for EWEC" from Shadi Shaat
(`shadi.shaat@core42.ai`) — no larger limit was needed. Invoked
`email_classification.classify_recent_emails(limit=10)` directly (the exact
function both the manual endpoint and the scheduler call — no separate code
path) against the real Outlook desktop client and the real `.env`-configured
vault. Result: two entries in the returned list, each with the same dict
shape as before this task (`subject`/`customer`/`kind`/`confidence`/
`attachments`/`related_emails`/`note_path` — no new key), confirming the
return-shape AC is unchanged. After the call, `Work/People/` now contains
`ahmad.hamzeh@core42.ai.md` and `shadi.shaat@core42.ai.md`, both created as
part of this same `classify_recent_emails` call with no separate manual
step. Opened both: each has
`type: "Person"`, `name`/`email` populated from that email's
`sender_name`/`sender_email` (`"Ahmad Hamzeh"`/`"ahmad.hamzeh@core42.ai"`
and `"Shadi Shaat"`/`"shadi.shaat@core42.ai"`), `tags: ["company/core42",
"kind/person"]`, and body `**Customer:** [[Core42]]` (Core42 is already a
known customer in this vault, so the wikilink half of `ensure_person_note`
fired too — expected behaviour, not part of this AC's own scope but
confirms the T02 call graph is wired correctly end-to-end).
**REQ-SB-10-US-01-AC-07 (creation half): PASS.**

**Verification (`REQ-SB-10-US-01-AC-07`, update half):** Immediately
afterward, called `people_extraction.ensure_person_note_for_captured_email(
"Ahmad Hamzeh", "ahmad.hamzeh@core42.ai")` again directly with the same
sender's name/email (simulating a second captured email from the same
sender). Returned dict: `{"note_path": ".../Work/People/
ahmad.hamzeh@core42.ai.md", "created": false, "company": "Core42",
"customer_matched": "Core42", "linked": false}` — `created: False` confirms
the existing Person note was topped up, not duplicated. Confirmed
`Work/People/` still contains exactly the same two files as after the
creation-half step (no third/duplicate file appeared).
**REQ-SB-10-US-01-AC-07 (update half): PASS.**

Dedup sanity check (unrelated to this task's own change, but confirms the
real pipeline ran end-to-end, not a partial/mocked path):
`processed_email_ids.json` went from 47 to 49 entries across the two newly
captured emails.

**Assumption logged for spot-check:** used `classify_recent_emails(limit=10)`
(the function's own default) as the starting/only probe value, per the
task's own "increase N from a small starting value if needed" fallback —
`limit=10` already reached 2 genuinely unprocessed emails on the first
probe, so no larger limit was needed. This is a verification-technique
judgement call, not a deviation from AC-07's intent (verifying the hook
fires on genuinely new email) or from the code change itself.

`gate: flagged` (`gate_reason: trigger-1`) — the `limit=10` starting-value
choice above is a scope-internal assumption (verification technique only,
no code-behavior implication), not an escalation: no new dependency, no
shared-interface change, no ADR deviation, no unanticipated file, no
unclear/contradictory requirement. Logged here for human spot-check per the
coder's role. No REVIEW-QUEUE.md entry needed beyond the standard flagged-
task visibility (nothing blocked; both AC-07 halves verified PASS).

**MEMORY.md:** not updated — no new decision/pattern/constraint emerged;
this task followed the decomposer's already-recorded plan (single import
change, one call-site addition) exactly, and the only judgement call
(starting `limit` for live verification) is a verification technique, not a
codebase decision/pattern/constraint.

---

**Orchestrator review (2026-08-11):** the `limit=10` probe value was the
exact pre-authorized fallback for finding genuinely unprocessed mail (same
pattern already approved for REQ-SB-14-US-01-T03) — it happened to be the
first value tried and worked immediately, no larger limit needed. Reviewed
and approved — `gate: flagged → clear`.
