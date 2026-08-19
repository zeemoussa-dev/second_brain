---
id: REQ-SB-77-US-01-T01
title: New people_extraction.relink_people_for_thread_paths(thread_paths) — bounded per-Thread re-linking
parent_story: REQ-SB-77-US-01
requirement_id: REQ-SB-77
type: backend
status: Ready
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

- [ ] `relink_people_for_thread_paths` exists, reuses `ensure_person_note` verbatim, introduces no new linking primitive
- [ ] Within-call dedup by lower-cased `sender_email` confirmed live
- [ ] A message with no `sender_email` is skipped, not errored
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring this function into any real trigger point — `T02` (instant hook) and `T03`/`REQ-SB-79-US-01-T02` (scheduled self-heal) own that.
- Any change to `ensure_person_note`, `retrofit_people_from_emails`, `find_matching_customer`/`find_matching_partner`, or `build_person_tags` — reused unmodified.

---

## Context / Notes

This is the ONE new mechanism this story introduces; every other task (`T02`/`T03`) is pure wiring around it or the already-existing `retrofit_people_from_emails`. Read `people_extraction.retrofit_people_from_emails`'s own real implementation first — this task's own dedup/skip shape must mirror it exactly, not diverge.

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
