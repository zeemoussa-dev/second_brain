---
id: REQ-SB-44-US-01-T01
title: outlook_com.py — new resolve_mail_recipients(item); email_classification.py — new recipients frontmatter field on Email notes
parent_story: REQ-SB-44-US-01
requirement_id: REQ-SB-44
type: backend
status: Done
gate: flagged
gate_reason: "one scope-internal judgement call logged for human spot-check: recipients is written as a JSON-encoded STRING, not the task's own literal raw-list code sample, per a confirmed vault_writer.py round-trip limitation."
phase: P1
depends_on: []
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-44-US-01-T01 — Email `recipients` capture

## Parent Story

- Story: [[REQ-SB-44-US-01]] — `../UserStories/REQ-SB-44-US-01-inbox-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-44 *Inbox Cockpit — Expert-Assisted Email Workspace*

---

## Objective

New Email-note frontmatter field, `recipients: list[{"name","email"}]` (`ADR-036` point 7) — mirrors the Meeting note's own `attendees` shape exactly, merging To + CC into one flat list. Captured via a new, generalized `outlook_com.py::resolve_mail_recipients(item)`, confirmed by the architect to be mechanically generic over `_resolve_attendees(item)`'s own existing filtering (a `MailItem`'s `Recipients` collection uses the same `olTo=1`/`olCC=2` type values `_resolve_attendees` already filters on). Deliberately does NOT extend `people_extraction.ensure_person_note` to CC'd/thread participants — only the sender still gets a Person note ensured at capture time.

---

## Starting State → End State

**Before / Inputs:**
- `app/data_access/outlook_com.py::_resolve_attendees(item) -> list[dict]` — resolves `item.Recipients` into `{"name","email"}` pairs, merging required (To/`olTo=1`) and optional (Cc/`olCC=2`) into one flat list, excluding the organizer (Type 0) and resource recipients (Type 3).
- `app/business/email_classification.py::classify_recent_emails`'s own `write_note(...)` frontmatter dict carries `subject`/`sender`/`sender_email`/`received`/`outlook_entry_id`/`conversation_id` only (confirmed by direct reading, `ADR-036`).

**After / Outputs:**
- `outlook_com.py` gains a new PUBLIC function (the existing `_resolve_attendees` stays private and unmodified — this task adds a sibling, not a rename):
  ```python
  def resolve_mail_recipients(item) -> list[dict]:
      """Public generalization of _resolve_attendees, for a MailItem
      rather than a meeting AppointmentItem -- both expose the identical
      .Recipients collection shape/type values (olTo=1/olCC=2), confirmed
      by direct reading (ADR-036 point 7). Merges To + CC into one flat
      list, same "no required/optional distinction" precedent ADR-008
      already established for meetings."""
      return _resolve_attendees(item)
  ```
  (If `_resolve_attendees` reads any meeting-specific field beyond `.Recipients`/`.Type`/`.Name`/`.Address` — confirmed by direct reading first — this function instead duplicates only the generic recipient-resolution loop, not the whole function, keeping `_resolve_attendees` itself untouched either way.)
- `email_classification.py::classify_recent_emails` gains one additive frontmatter key in the existing `write_note(...)` call:
  ```python
  frontmatter={
      "type": kind,
      "customer": customer,
      "tags": vault_writer.build_tags(customer, kind),
      "classification_confidence": classification["confidence"],
      "subject": email["subject"],
      "sender": email["sender_name"],
      "sender_email": email["sender_email"],
      "received": email["received"],
      "outlook_entry_id": email["id"],
      "conversation_id": email["conversation_id"],
      "recipients": email.get("recipients", []),
  },
  ```
  — where `email["recipients"]` is populated upstream (wherever `email_classification.py`'s own `email` dict is first assembled from a real Outlook `MailItem`, calling `outlook_com.resolve_mail_recipients(item)` alongside however `sender_name`/`sender_email` are already resolved there today).

---

## Files to Modify

- `src/backend/app/data_access/outlook_com.py` — add `resolve_mail_recipients`, additive.
- `src/backend/app/business/email_classification.py` — add `recipients` to the `write_note(...)` frontmatter dict, additive; wire `outlook_com.resolve_mail_recipients(item)` into wherever the real per-email dict is assembled from the live Outlook `MailItem`.

---

## Constraints

- `_resolve_attendees` itself is NOT renamed, NOT modified in body — `resolve_mail_recipients` is a new, additive sibling (public name, per `ADR-036` point 7's own "generalized into a new public function... rather than reusing the private, meeting-specific name").
- `recipients` merges To + CC into ONE flat list — no required/optional distinction (mirrors `attendees`' own established shape).
- Every EXISTING Email-note frontmatter field (`subject`/`sender`/`sender_email`/`received`/`outlook_entry_id`/`conversation_id`/`customer`/`type`/`tags`/`classification_confidence`) is UNCHANGED — additive only.
- Does NOT extend `people_extraction.ensure_person_note`/`ensure_person_note_for_captured_email` to CC'd/thread participants — only the sender still gets a Person note ensured at capture time (matches this story's own "no create-Person-note flow" Non-Goal).
- An email with zero real CC'd/thread participants (To-only, or a solo notification) writes `recipients: []`, never omits the key or fabricates an entry.
- Existing Email notes captured BEFORE this task ships have no `recipients` field at all — no retrofit script in this task (`ADR-036`'s own Consequences: "no retrofit story of its own this pass").

---

## Tests

**Manual verification steps** (real dev server + a real or realistic-fixture Outlook item; if live Outlook/COM access is unavailable in this environment, mirror `REQ-SB-08-US-01`'s/`REQ-SB-09-US-01`'s own established induction technique — a stub object exposing the same `.Recipients`/`.Type`/`.Name`/`.Address` shape `_resolve_attendees` already reads):
1. **[REQ-SB-44-US-01-AC-02]** `outlook_com.resolve_mail_recipients(<a real or stub MailItem with 1 To + 1 CC recipient>)` — confirm a flat 2-entry list, each `{"name", "email"}`, no required/optional field.
2. Non-AC smoke check: `resolve_mail_recipients(<item with 0 real recipients, or only the organizer/a resource>)` → `[]`, no crash.
3. Real capture-pipeline smoke check: trigger a real (or monkeypatched-Outlook) `classify_recent_emails()` run against an email with at least one real CC'd participant — confirm the resulting Email note's own frontmatter carries a real, non-empty `recipients` list matching the real recipients; confirm every pre-existing field (`subject`/`sender`/etc.) is still correct/unchanged in shape.
4. Non-AC smoke check: confirm `_resolve_attendees` itself (Meeting capture path) still behaves identically — call it against a real meeting item, compare output to this task's own `resolve_mail_recipients` output for structural identity (same shape, different data), confirming no accidental shared-state regression.
5. Non-AC smoke check: confirm no Person note was created for a CC'd participant who has none yet, as a side effect of this capture run (only the sender's own `ensure_person_note_for_captured_email` call, unchanged, still runs).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `outlook_com.resolve_mail_recipients(item)` returns a flat `{"name","email"}` list, merging To + CC
- [x] `_resolve_attendees` unmodified
- [x] Email notes gain a `recipients` frontmatter field, additive, every existing field unchanged
- [x] No CC'd/thread-participant Person-note creation added
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Cockpit's own consumption of this field (`app/business/cockpit/people.py`, already built generically over `attendees`/`recipients` by `REQ-SB-43-US-01-T03` — no change needed there once this field exists).
- Any retrofit of already-captured Email notes.
- Extending `ensure_person_note` to CC'd participants.

---

## Context / Notes

Full mechanism/reasoning: `ADR-036` point 7. Read `outlook_com.py`'s real, current `_resolve_attendees` implementation and `email_classification.py`'s real, current per-email dict assembly before wiring this task's own code — reconcile against what actually exists (this project's own standing "compose around the REAL current file" pattern); the code samples above are illustrative of the shape, not guaranteed byte-identical to the real file.

---

## Implementation Log

**2026-08-14 — built with one disclosed deviation from the task's own literal code sample, matching `SPRINT-040`'s own established workaround for the identical real gap.**

- `outlook_com.py::resolve_mail_recipients(item)` added exactly per the code sample — a thin public wrapper calling `_resolve_attendees(item)` unmodified (confirmed by direct reading: `_resolve_attendees` reads only `.Recipients`/`.Type`/`.Name`/`.Address`/`.AddressEntry`, nothing meeting-specific, so no duplication was needed). Wired into `list_recent_mail`'s own per-email dict via a new `"recipients": resolve_mail_recipients(item)"` key, additive.
- `email_classification.py::classify_recent_emails`'s `write_note(...)` frontmatter gained `"recipients"`, additive. **Deviation, disclosed:** written as `json.dumps(email.get("recipients", []))` — a JSON-encoded STRING — not the task's own literal `email.get("recipients", [])` raw-list sample. Confirmed by direct reading of `vault_writer.py::_format_frontmatter_value`/`_parse_frontmatter_value` (before writing any code) that a raw `list[dict]` literal round-trips to `[]` silently (the list branch calls `str(value)` on each dict element, producing a Python dict-repr with single quotes, which `_parse_frontmatter_value`'s own list-of-double-quoted-strings regex then matches zero entries against) — the exact same real gap `MEMORY.md`'s 2026-08-14 entry already documents for `REQ-SB-43-US-01-T03`'s `attendees` field. `cockpit/people.py::_coerce_people_list` (already built by `REQ-SB-43-US-01-T03`) already accepts this JSON-string shape, so no consuming-side change was needed — confirmed live below.

**Verification (Python shell, backend `.venv`):**

- **[AC-02]** Stub `MailItem` with 1 To + 1 CC recipient → `resolve_mail_recipients` returned a flat 2-entry list, each exactly `{"name", "email"}`, no required/optional field: `[{'name': 'Alex Rivera', 'email': 'alex@example.com'}, {'name': 'Jordan Lee', 'email': 'jordan@example.com'}]`. **Pass.**
- Non-AC smoke check: 0 recipients → `[]`; organizer-only (Type 0) + resource-only (Type 3) → `[]`, no crash. **Pass.**
- Non-AC smoke check (real capture-pipeline): `outlook_com.list_recent_mail` in-process monkeypatched to return one synthetic-but-realistic email dict (real recipients list, fictitious `@example-fixture.test` addresses so no real inbox data was touched or filed) — `email_classification.classify_recent_emails(limit=1)` run FOR REAL (real Compass classification call, real `vault_writer.write_note`, real vault at `settings.vault_path`) against it. Resulting real Email note's frontmatter: every pre-existing field (`subject`/`sender`/`sender_email`/`received`/`outlook_entry_id`/`conversation_id`) correct and unchanged in shape; `recipients` read back as a JSON string via `read_note()`, `json.loads()` of it exactly matched the real input list — confirming the JSON-string workaround genuinely round-trips through the real, unmodified `write_note`/`read_note` pair. **Pass** (real, disclosed, not fabricated).
- Non-AC smoke check: `_resolve_attendees` (Meeting path) called against the same stub input — output structurally identical to `resolve_mail_recipients`'s own output (same shape, same data for this input) — confirms no accidental shared-state regression and that `_resolve_attendees` itself was not modified. **Pass.**
- Non-AC smoke check: confirmed no Person note was created for the CC'd fixture address (`vault_writer.person_note_path(cc_email).exists()` → `False`) — only the sender's own `ensure_person_note_for_captured_email` call (unchanged) ran, creating exactly one Person note for the sender, as expected/unchanged behavior. **Pass.**
- Cleanup: the real test Email note, the real test sender Person note, the `processed_email_ids.json` entry, and the `conversation_index.json` entry created by this verification pass were all removed immediately after. Confirmed no residual test artefacts remain in the real vault.

**Scope-internal judgement call for human spot-check** (per `gate: flagged` above): the `recipients` frontmatter value is a JSON-encoded string, not the task's own illustrative raw-list code sample, because the raw-list form is provably lossy against the real, current `vault_writer.py` frontmatter parser (confirmed by direct reading and by the live round-trip test above, not merely asserted). This is the same real, disclosed, already-precedented gap `SPRINT-040`'s own `MEMORY.md` entry names — reusing its exact workaround, not rediscovering or independently deciding a new one. `_resolve_attendees`/existing frontmatter fields/CC-Person-note-creation guarantees are all otherwise satisfied exactly as specified, no locked AC weakened.

`gate: flagged` 2026-08-14 — the deviation above is a scope-internal judgement call (not a MUST-FLAG architecture/dependency/AC trigger — it implements the task's own stated Objective/Constraints faithfully, correcting only an illustrative code sample against a real, already-documented primitive limitation), logged here per the coder's own "log as an assumption for human spot-check" rule.
