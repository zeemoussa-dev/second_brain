---
id: REQ-SB-77-US-01-T01
title: New people_extraction.relink_people_for_thread_paths(thread_paths) — bounded per-Thread re-linking
parent_story: REQ-SB-77-US-01
requirement_id: REQ-SB-77
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-77-US-01-T01 — `relink_people_for_thread_paths()`

## Parent Story

- Story: [[REQ-SB-77-US-01]] — `../UserStories/REQ-SB-77-US-01-people-notes-linked-to-company-partner-note.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-77 *People Notes Linked to Their Real Company/Partner Note*
- Architecture: `Implementation/Architecture/architecture.md` → "People Notes Retroactively Linked to Company/Partner" (composes `ADR-009`)

---

## Objective

Add `people_extraction.relink_people_for_thread_paths(thread_paths: list[str]) -> list[dict]` — a bounded, per-Thread sibling of the already-existing, whole-vault `retrofit_people_from_emails()` — reusing `ensure_person_note` verbatim, introducing zero new linking primitive.

---

## Starting State → End State

**Before / Inputs:**
- `people_extraction.py` has `ensure_person_note(name, email, customer=None)` (`Done`) and `retrofit_people_from_emails()` (`Done`, whole-vault, scans every note via `vault_writer.list_all_note_paths()`, dedupes by `sender_email`).
- `librarian_housekeeping._thread_full_content(messages_dir)` already reads each Thread's own `messages/*.md` raw notes; those same notes carry `sender`/`sender_email` frontmatter (the identical shape `retrofit_people_from_emails` already reads off every note).
- No per-Thread-bounded relinking function exists yet.

**After / Outputs:**
- `relink_people_for_thread_paths(thread_paths: list[str]) -> list[dict]`: for each given Thread concept-note path, reads that Thread's own `messages/*.md` notes (same directory-derivation `_thread_full_content`/`backfill_files` already use: `Path(thread_path).parent / "messages"`), extracts `sender`/`sender_email` from each message's frontmatter, dedupes by lower-cased email **within this one call only** (mirrors `retrofit_people_from_emails`'s own dedup exactly — not a cross-call/global dedup), and calls `ensure_person_note(sender_name, sender_email)` once per unique sender. A message with no `sender_email` is skipped, not errored (mirrors `retrofit_people_from_emails`'s own `skipped_no_sender_email` status). Returns a list of per-sender result dicts, same shape as `retrofit_people_from_emails`'s own return (`{"note": ..., "status": ..., **ensure_person_note's own outcome}` or `{"note": ..., "status": "skipped_no_sender_email"}`).
- Lives in `people_extraction.py` (the composing module), not `librarian_housekeeping.py` — mirrors `ensure_person_note_for_captured_email`'s own "one bounded per-event wrapper around the same shared operation" shape.

---

## Files to Modify

- `src/backend/app/business/people_extraction.py` — new `relink_people_for_thread_paths` function, placed near `retrofit_people_from_emails` (its nearest structural sibling).

---

## Constraints

- Inherits from parent story.
- **No new linking primitive.** Every wikilink written goes through `ensure_person_note` (already calls `customer_hub_linking.link_note_to_customer_hub`/`partner_hub_linking.link_note_to_partner_hub` internally) — this task adds zero new write path.
- **Never move or duplicate an already-existing Person note** — inherited from `ensure_person_note`'s own contract, unchanged by this task.
- Dedup is scoped to **this one call** — do not reuse or persist `retrofit_people_from_emails`'s own dedup state; the two functions' dedup sets are independent by design (a bounded per-Thread call and a whole-vault call may legitimately re-process the same sender).
- Must respect the `api → business → data_access` layer boundary (`ADR-003`) — this task touches only the `business` layer.

---

## Tests

**Manual verification steps:**
1. Call `relink_people_for_thread_paths([<a real Thread concept-note path with 2+ real messages from the same real sender>])`. Confirm exactly ONE `ensure_person_note` outcome is returned for that sender (not one per message) — the within-call dedup works.
2. Call it against a Thread whose messages include one real message with a blank/missing `sender_email`. Confirm that message's own entry is `"skipped_no_sender_email"`, not an error, and every other message in the same call still processes normally.
3. Call it against an empty `thread_paths` list. Confirm it returns `[]` without error.
4. Confirm the returned per-sender dict shape matches `ensure_person_note`'s own outcome keys (`note_path`, `created`, `company`, `customer_matched`, `partner_matched`, `linked`) plus `note`/`status`, mirroring `retrofit_people_from_emails`'s own return shape.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `relink_people_for_thread_paths` exists, reuses `ensure_person_note` verbatim, introduces no new linking primitive
- [x] Within-call dedup by lower-cased `sender_email` confirmed live
- [x] A message with no `sender_email` is skipped, not errored
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — none emerged)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring this function into any real trigger point — `T02` (instant hook) and `T03`/`REQ-SB-79-US-01-T02` (scheduled self-heal) own that.
- Any change to `ensure_person_note`, `retrofit_people_from_emails`, `find_matching_customer`/`find_matching_partner`, or `build_person_tags` — reused unmodified.

---

## Context / Notes

This is the ONE new mechanism this story introduces; every other task (`T02`/`T03`) is pure wiring around it or the already-existing `retrofit_people_from_emails`. Read `people_extraction.retrofit_people_from_emails`'s own real implementation first — this task's own dedup/skip shape must mirror it exactly, not diverge.

---

## Implementation Log

**Built 2026-08-19.** Added `people_extraction.relink_people_for_thread_paths(thread_paths: list[str]) -> list[dict]`, placed directly after `retrofit_people_from_emails` (its nearest structural sibling), per `## Files to Modify`. Body mirrors `retrofit_people_from_emails` exactly: for each given Thread path, derives `messages_dir = Path(thread_path).parent / "messages"`, reads every `messages/*.md` note's `sender`/`sender_email` frontmatter, dedupes by lower-cased `sender_email` scoped to this one call (a fresh `seen_emails` set per call — never shared/persisted), and calls `ensure_person_note(sender_name, sender_email)` once per unique sender, verbatim/unmodified. No new linking primitive introduced — `ensure_person_note` is reused exactly as-is.

**Verification (manual mode, real vault + one disposable-test aside):**
1. Real Thread `Work/Threads/2026-07-28 MIC/2026-07-28 MIC.md` has 2 real messages, both from `amraze@microsoft.com`. Called `relink_people_for_thread_paths([<that path>])`: first message returned a real `ensure_person_note` outcome (`status: already_existed`, since this sender's Person note already existed from an earlier retrofit run), second message returned `status: skipped_duplicate_sender_this_run` — confirms exactly ONE `ensure_person_note` outcome per unique sender, not one per message. **PASS.**
2. No real Thread in the current vault happens to mix a real `sender_email` message with a real blank-`sender_email` message in the same Thread (checked live across all 141 real Threads — none matched). Constructed a disposable, clearly-labeled test Thread (2 message notes, correct frontmatter shape) outside the vault under the session scratchpad, `messages/msg1.md` (`sender_email: realsender@example-t01.com`) + `messages/msg2-noemail.md` (no `sender_email` key at all). Called `relink_people_for_thread_paths` against it: `msg1` produced a real `ensure_person_note` outcome (`created: True`, a genuine new Person note written to the real vault at `Work/People/realsender@example-t01.com.md`), `msg2-noemail` produced `status: skipped_no_sender_email` — no error, not counted against the dedup set. **PASS.** The disposable Person note this created was deleted immediately after (`Test-Path` confirmed absence post-cleanup); the disposable scratch Thread/messages directory was also deleted. No other real vault state touched by this step.
3. Called `relink_people_for_thread_paths([])` — returned `[]`, no error. **PASS.**
4. The returned dicts from steps 1/2 above carry exactly `note`, `status`, plus (on a real `ensure_person_note` call) `note_path`, `created`, `company`, `customer_matched`, `partner_matched`, `linked` — matches `retrofit_people_from_emails`'s own return shape exactly. **PASS.**

No locked story-level AC is directly tagged to this task (T01 is the shared root mechanism; the story's locked ACs are verified in `T02`/`T03`/`T04`). All 4 of this task's own Tests-block steps pass.

**MEMORY.md:** not updated — no new decision/pattern/constraint; this task is a pure mirror of `retrofit_people_from_emails`'s already-established shape, applied to a narrower input.

**Assumption logged for spot-check (scope-internal, non-blocking):** since no real Thread in the current vault had a mixed sender_email/no-sender_email message pair, step 2 above used a disposable, clearly-labeled scratch Thread outside the real vault (not a real Thread) to exercise the `skipped_no_sender_email` path — the real vault-write side effect (one real Person note) was created and then fully cleaned up. This mirrors this project's own "closest-to-real substitute, disclose disposable-test fallbacks explicitly" verification discipline.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired (no new ADR, no unresolved assumption beyond the disclosed scope-internal one above, no ESCALATIONS entry, not oversized, all 4 Tests-block steps verified with a real positive result).
