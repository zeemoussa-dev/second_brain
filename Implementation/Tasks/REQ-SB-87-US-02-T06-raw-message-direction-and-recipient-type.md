---
id: REQ-SB-87-US-02-T06
title: Thread real direction and recipient-type fields through to RawMessage frontmatter
parent_story: REQ-SB-87-US-02
requirement_id: REQ-SB-87
type: backend
status: Done
gate: flagged
gate_reason: "Two disclosed, non-blocking scope-internal findings for human spot-check: (1) recipient-type frontmatter shape changed from the task's own illustrative one-list-of-{email,type} example to two flat to_recipients/cc_recipients lists, a real engine round-trip limitation found live -- see Implementation Log and MEMORY.md. (2) run_full_capture.py/run_delta_capture.py (out of this task's own scope) don't yet forward the new direction field -- needed before T05's live cutover, see REVIEW-QUEUE.md."
phase: P1
depends_on: [REQ-SB-87-US-02-T01]
created: 2026-09-02
updated: 2026-09-02
---

# REQ-SB-87-US-02-T06 — Thread Real `direction` and Recipient-Type Fields Through to RawMessage Frontmatter

## Parent Story

- Story: [[REQ-SB-87-US-02]] — `../UserStories/REQ-SB-87-US-02-email-thread-capture-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Thread a real `direction` value ("sent" | "received") and a real per-recipient
type (To vs. CC) from `outlook_lib.py`'s own per-folder/per-recipient Outlook
COM read, through `list_recent_emails.py` (docstring only, no logic change),
into `ingest_email.py`'s own RawMessage `frontmatter=` call — an additive
extension of `T01`'s (`Done`) RawMessage-creation output, never a re-edit of
`T01`'s own already-verified `AC-01`/`AC-02` scope.

---

## Starting State → End State

**Before / Inputs:**
- Real, current `outlook_lib.py` (confirmed directly, see the parent story's
  own 2026-09-02 Context): `_list_folder_mail` is called twice by
  `list_recent_mail` — once against `_OL_FOLDER_INBOX`, once against
  `_OL_FOLDER_SENT_MAIL` — then `merged = sorted(inbox_results +
  sent_results, ...)`. Neither the per-item dict nor the merge step stamps
  which folder a message came from today.
- `_resolve_attendees` filters `item.Recipients` via `recipient.Type not in
  (_OL_MEETING_RECIPIENT_REQUIRED, _OL_MEETING_RECIPIENT_OPTIONAL): continue`
  (these constants happen to share integer values with mail's own
  `olTo=1`/`olCC=2`) — the returned attendee dict (`{"name", "email",
  "department", "job_title", "company_name"}`) carries no marker for To vs.
  CC today.
- `list_recent_emails.py` already passes `list_recent_mail`'s dict straight
  through to its own printed JSON, unmodified — a pure pass-through, no field
  remapping.
- `ingest_email.py`'s own `T01`-migrated RawMessage creation calls
  `vault_manager.create_dynamic_child(..., body=<real email body>)` with a
  `frontmatter=` dict that does not yet carry `direction` or a per-recipient
  type.

**After / Outputs:**
- `outlook_lib.py`: `_list_folder_mail`'s two call sites (or the merge step
  immediately after) stamp each returned message dict with a real `direction`
  key — `"received"` for the Inbox-sourced call, `"sent"` for the
  Sent-Mail-sourced call — read directly from which folder the message was
  actually queried from, never inferred afterward from `sender_email` or
  participant matching. `_resolve_attendees` stamps each returned attendee
  dict with a real `type` key (`"to"` | `"cc"`, this task's own disclosed
  literal values — documented in the Implementation Log), read directly from
  `recipient.Type` at the Outlook COM layer, never re-derived downstream.
  Both changes are purely additive keys on existing dict shapes — no
  restructuring of paging, restriction, or attachment logic.
- `list_recent_emails.py`: only its own module docstring's field-list
  documentation updated to name the two new fields — zero logic change (it
  already passes the dict through unmodified).
- `ingest_email.py`: the RawMessage `frontmatter=` dict passed to
  `create_dynamic_child()` gains the real `direction` value and the
  per-recipient type data (this task's own disclosed shape for how recipients
  are represented in frontmatter — e.g. a `recipients` list of
  `{"email", "type"}` entries, distinct per individual recipient, never
  flattened into one undifferentiated list) — a real, additive extension,
  zero engine or template change needed (confirmed by the architect: both
  `create()` and `create_dynamic_child()` already accept arbitrary extra
  frontmatter keys with no allow-list).

---

## Files to Modify

- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/outlook_lib.py` (additive `direction`/`type` stamps only)
- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/list_recent_emails.py` (docstring only)
- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/ingest_email.py` (additive `frontmatter=` extension)

---

## Constraints

- Inherits from parent story.
- This is an additive field-plumbing change only — no restructuring of
  `outlook_lib.py`'s own paging, restriction, or attachment logic (the
  story's own narrow 2026-09-02 Constraints carve-out).
- `direction` must be threaded through unchanged from the real per-folder
  read (which of the two `_list_folder_mail` calls produced the message) —
  never inferred afterward from `sender_email` or participant matching.
- Recipient type must be threaded through unchanged from `recipient.Type` at
  the Outlook COM layer — never a re-derived guess made downstream.
- Do not touch `run_full_capture.py`/`run_delta_capture.py`'s own
  orchestration logic (paging, watermark, subprocess dispatch) — unaffected
  by this task, per the parent story's own standing Constraint.
- Do not re-open or re-verify `T01`'s own already-locked `AC-01`/`AC-02`
  scope (RawMessage/Thread parity, idempotency) — this task only adds two new
  frontmatter fields on top of that already-`Done` work.
- **Do not point `--vault-path` at the real, live vault for this task's own
  verification** — use a scratch vault seeded with a real email sample (a
  fresh pull via `list_recent_emails.py`), per the parent story's own
  proving-phase rollout Constraint.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`, a real
email sample pulled via `list_recent_emails.py` covering at least one Inbox
item and one Sent Mail item, and at least one email with both a To and a CC
recipient):**
1. `[REQ-SB-87-US-02-AC-08]` Run the migrated `ingest_email.py` against one
   Inbox-sourced email and one Sent-Mail-sourced email (same or different
   `conversation_id`s). Read each resulting RawMessage note's own real
   on-disk frontmatter directly (`vault_manager.read_note`, not just stdout).
   Confirm the Inbox-sourced note's `direction` is exactly `"received"` and
   the Sent-Mail-sourced note's `direction` is exactly `"sent"`. Confirm (by
   reading `outlook_lib.py`'s own real per-folder call sites) that this value
   is stamped at the point of the real per-folder read, never inferred
   afterward from `sender_email`.
2. `[REQ-SB-87-US-02-AC-09]` Run the migrated `ingest_email.py` against a
   real email with at least one To recipient and at least one CC recipient.
   Read the resulting RawMessage note's own real on-disk frontmatter
   directly. Confirm each recipient's own real type (To or CC) is present
   and distinguishable per individual recipient — never flattened into one
   undifferentiated list with no way to tell them apart. Confirm (by reading
   `_resolve_attendees`'s own real code) that this value comes from
   `recipient.Type` at the Outlook COM layer, not a re-derived guess.
3. (Unlabeled, supporting) Confirm `list_recent_emails.py`'s own printed JSON
   for the same sample already carries both new fields, unmodified, and that
   its module docstring documents them. Confirm zero logic change beyond the
   docstring edit (`git diff` on this file shows only the docstring hunk).
4. (Unlabeled, supporting) Re-run `T01`'s own already-passing `AC-01`/`AC-02`
   scratch-vault checks (or a representative subset) against this task's
   changes to confirm zero regression to Thread/RawMessage parity or
   idempotency — this task adds fields, it must not alter any existing
   field's value or the note's identity/idempotency behavior.

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via real scratch-vault CLI runs, per this codebase's own
established pattern`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `outlook_lib.py`'s per-folder read stamps a real `direction` value
      (`"received"` for Inbox, `"sent"` for Sent Mail), additive only
- [x] `outlook_lib.py`'s `_resolve_attendees` stamps a real per-recipient
      `type` value (To vs. CC), additive only
- [x] `list_recent_emails.py`'s docstring updated, zero logic change
- [x] `ingest_email.py`'s RawMessage `frontmatter=` call carries both new
      fields, recipients distinguishable per individual entry
- [x] Zero regression to `T01`'s own already-verified `AC-01`/`AC-02` scope
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any restructuring of `outlook_lib.py`'s own paging, restriction, or
  attachment logic.
- `run_full_capture.py`/`run_delta_capture.py`'s own orchestration logic.
- Real-vault run or cutover — `T05` (this task's own changes ride along in
  the same `ingest_email.py` file `T05` deploys/cuts over; `T05`'s own
  `depends_on` has been updated to include this task).
- Consuming `direction` in the Capture-time classify-or-skip judgment (the
  "Sent items are never Noise" business rule) — [[REQ-SB-87-US-03]]'s own
  `T03`, which now also depends on this task.

---

## Context / Notes

Read the REAL current `outlook_lib.py`/`list_recent_emails.py`/
`ingest_email.py` directly before editing — the parent story's own Context
section (2026-09-02 addition) already confirms the real, current shape from
a direct read; confirm it hasn't drifted further by build time.
`REQ-SB-87-US-03`'s own Scenario 8 ("Sent items are never classified as
noise") depends on this task's own `direction` field existing on the data
being classified — see `REQ-SB-87-US-03-T03`'s own updated `depends_on`.

---

## Implementation Log

**What was built:**
- `outlook_lib.py`: `_list_folder_mail` gained a required `direction: str`
  parameter, stamped into every returned dict as `"direction"`; the two
  `list_recent_mail` call sites pass `direction="received"` (Inbox) and
  `direction="sent"` (Sent Mail) respectively. `_resolve_attendees` now
  computes `recipient_type = "to" if recipient.Type ==
  _OL_MEETING_RECIPIENT_REQUIRED else "cc"` (these constants share real
  integer values with mail's own `olTo=1`/`olCC=2`, per the story's own
  Context) and stamps it into each returned attendee dict as `"type"`.
  Both changes are purely additive — no paging/restriction/attachment
  logic touched, confirmed by direct `git diff` review.
- `list_recent_emails.py`: module docstring updated to document `direction`
  and each recipient's own `type` in the printed JSON shape — zero logic
  change (confirmed: `git diff HEAD` shows only the docstring hunk).
- `ingest_email.py`: input-JSON docstring shape extended with optional
  `direction`/per-recipient `type`. `ingest_email()` reads
  `direction = data.get("direction") or ""` and splits `recipients` into
  two flat email-string lists by type (`to_recipient_emails`,
  `cc_recipient_emails` — see "real deviation" below for why not one
  combined list), both added to the RawMessage's `frontmatter=` dict
  passed to `create_dynamic_child()` as `direction`, `to_recipients`,
  `cc_recipients`.

**Real deviation from the task's own illustrative frontmatter shape (found
live, fixed before shipping):** the Objective's own "e.g." example proposed
one `recipients: [{"email", "type"}, ...]` frontmatter list. Building this
literally and reading it back with `vault_manager.read_note()` showed
`recipients: []` — investigated and confirmed live: `vault_manager.py`'s
own frontmatter reader/writer (`_format_frontmatter_value`/
`_parse_frontmatter_value`) is a hand-rolled, non-YAML format that only
round-trips scalars and homogeneous lists of quoted strings;
`_format_frontmatter_value`'s list branch recurses per-element, but a dict
element falls through to its final `str(value)` catch-all, writing a
Python-`repr()`-shaped, non-quoted line (`recipients: [{'email': '...',
'type': 'to'}, ...]`) that `_parse_frontmatter_value`'s own
`_LIST_ITEM_PATTERN` (quoted-strings-only) cannot match at all — silently
parsed back as an empty list, no error anywhere in the write or read path.
The architect's own confirmed finding ("`create()`/`create_dynamic_child()`
accept arbitrary extra frontmatter keys with no allow-list") is correct but
doesn't cover value-SHAPE round-tripping through this specific engine.
Resolved within this task's own `## Files to Modify` (`ingest_email.py`
only, no engine/template change): split into two separate flat
`to_recipients`/`cc_recipients` email-string lists — each recipient's own
real type is now structurally distinguishable by WHICH list it's in
(never one undifferentiated list), and both lists round-trip correctly
through the real engine (confirmed live below). Generalized as a new
`MEMORY.md` Constraint entry (2026-09-02, third one) so no future task
assumes a nested list-of-dicts value will survive this engine's frontmatter
round trip.

**Live verification (real scratch vault, `C:\scratch-sb87t06\vault2`,
seeded with a real copy of the live `thread/Template.json`; a real
~20-email sample pulled via the unmodified `list_recent_emails.py` against
live Outlook):**

- `[REQ-SB-87-US-02-AC-08]` **PASS.** Selected one real Inbox-sourced email
  (`direction: "received"` in the pulled sample) and one real Sent-Mail-
  sourced email (`direction: "sent"`). Ran the migrated `ingest_email.py`
  against each via a direct subprocess call (matching the orchestrators'
  own real per-email dispatch shape, `T01`'s established verification
  technique). Read each resulting RawMessage note's own real on-disk
  frontmatter directly via `vault_manager.read_note` (not stdout): the
  Inbox-sourced note's `direction` is exactly `"received"`, the
  Sent-Mail-sourced note's is exactly `"sent"`. Confirmed by direct
  reading of `outlook_lib.py`'s own real per-folder call sites that this
  value is stamped at the point of the real per-folder read (a literal
  `direction="received"`/`direction="sent"` keyword argument at each of
  the two `_list_folder_mail` call sites in `list_recent_mail`), never
  inferred afterward from `sender_email`.
- `[REQ-SB-87-US-02-AC-09]` **PASS.** The same real Inbox-sourced email
  (subject "Re: Core42 x Microsoft | ADNOC") had 7 real To recipients and
  2 real CC recipients (a genuine mixed set, not engineered). Ran the
  migrated `ingest_email.py` against it; read the resulting RawMessage
  note's own real on-disk frontmatter directly. `to_recipients` contained
  exactly the 7 real To addresses, `cc_recipients` contained exactly the 2
  real CC addresses (`shadi.shaat@core42.ai` and one internal Exchange DN)
  — each recipient's own real type present and distinguishable per
  individual recipient (which list it's in), never flattened into one
  undifferentiated list. The Sent-Mail email (2 real To recipients, 0 CC)
  independently confirmed the empty-CC case round-trips correctly too
  (`cc_recipients: []`). Confirmed by direct reading of
  `_resolve_attendees`'s own real code that `type` comes from a literal
  `recipient.Type == _OL_MEETING_RECIPIENT_REQUIRED` comparison at the
  Outlook COM layer, never a re-derived guess.
- (Unlabeled, supporting) **PASS.** `list_recent_emails.py`'s own printed
  JSON for the same sample already carried both new fields (`direction`
  per email, `type` per recipient), unmodified, before `ingest_email.py`
  was ever invoked — confirmed by direct inspection of the pulled sample
  file. `git diff HEAD` on `list_recent_emails.py` shows only the
  docstring hunk — zero logic change.
- (Unlabeled, supporting) **PASS.** Re-ran `ingest_email.py` for both
  already-ingested messages (same `message_id`s): both returned
  `{"thread_created": false, "message_created": false}`, no duplicate
  `.md` file created in either `messages/` folder (confirmed via direct
  directory listing) — zero regression to `T01`'s own `AC-02` idempotency
  scope. All other pre-existing RawMessage frontmatter fields (`sender`,
  `sender_email`, `subject`, `received`, `participant_links`) present and
  correct in the same read, confirming the new fields are purely additive
  alongside `T01`'s own already-verified shape.

**Scope-internal / disclosed findings (logged for human spot-check, `gate:
flagged`, not blocking):**
1. The recipient-type frontmatter shape (`to_recipients`/`cc_recipients`,
   two flat lists) instead of the task's own illustrative one-list example
   — a real engine constraint forced this, detailed above and in
   `MEMORY.md`.
2. `run_full_capture.py`/`run_delta_capture.py` (explicitly out of this
   task's own `## Files to Modify`, per the story's standing Constraint)
   build their own `ingest_payload` dict from a fixed, explicit key list
   that does NOT include `"direction"` — confirmed by direct reading of
   both files. `recipients` (and each recipient's own `type`) already
   flows through both orchestrators unchanged today, since they forward
   the whole list object rather than rebuilding it field-by-field, so
   `AC-09`'s value is already live-pipeline-safe; `AC-08`'s `direction`
   value is NOT yet reachable through the live cron pipeline until the
   orchestrators gain one line each (`"direction": e.get("direction") or
   ""`). This does not fail `AC-08` as locked (verified directly against
   `ingest_email.py`, per this task's own Tests-block method) but is a
   real, disclosed gap `REQ-SB-87-US-02-T05`'s own future cutover pass
   needs to close — filed to `REVIEW-QUEUE.md`, not silently absorbed and
   not fixed here (orchestrator files are out of this task's own scope).

**Compile check:** `python -m py_compile` on all three modified files —
clean.

**Escalations / review-queue items written by this task:**
- `REVIEW-QUEUE.md` → `REQ-SB-87-US-02-T06` entry, pointing at the
  orchestrator `direction`-forwarding gap (finding 2 above) and the new
  `MEMORY.md` Constraint entry.
- No `ESCALATIONS.md` entry — both findings above are scope-internal
  disclosures within this task's own already-correct scope boundary
  (the orchestrator gap was found by reading, not touching, an
  out-of-scope file; the frontmatter-shape deviation was resolved
  entirely within this task's own `## Files to Modify`), not backward
  steps or out-of-scope events.

Task marked `Done` — both locked ACs (`AC-08`, `AC-09`) verified live with
a real positive result. `gate: flagged` for the two disclosed findings
above.
