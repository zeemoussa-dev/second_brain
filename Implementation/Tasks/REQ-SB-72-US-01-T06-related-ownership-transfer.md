---
id: REQ-SB-72-US-01-T06
title: ## Related ownership transfers wholesale to the Librarian
parent_story: REQ-SB-72-US-01
requirement_id: REQ-SB-72
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-72-US-01-T02, REQ-SB-72-US-01-T05]
created: 2026-08-18
updated: 2026-08-19
---

# REQ-SB-72-US-01-T06 — `## Related` ownership transfers wholesale to the Librarian

## Parent Story

- Story: [[REQ-SB-72-US-01]] — `../UserStories/REQ-SB-72-US-01-librarian-section-first-housekeeping-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-72 *The Librarian Section — First Housekeeping Pipeline*
- Architecture: `Implementation/Architecture/architecture.md` → "`## Related` ownership transfer" (`ADR-049` Decision 4)

---

## Objective

`email_classification.synthesize_thread` stops writing `## Related` entirely; the Librarian's new `populate_thread_related_links` Job becomes its sole owner, extending the existing honest-omission Person/Customer wikilink contract with `T05`'s new company-mention wikilinks.

---

## Starting State → End State

**Before / Inputs:**
- `email_classification.py`'s `_build_thread_related_wikilinks(customer, participants, project)` (private) assembles Customer + Person + Project wikilinks; `synthesize_thread` calls it near its own end and writes the result via `replace_body_section(path, "## Related", ..., caller="email_classification.synthesize_thread")`.
- `section_ownership.py`'s `_CALLER_ALLOW_LISTS["email_classification.synthesize_thread"]` is `frozenset({"## Summary", "## Related"})`.

**After / Outputs:**
- `_build_thread_related_wikilinks` is renamed to a PUBLIC `build_thread_related_wikilinks(customer, participants, project, mentioned_companies: list[str] | None = None)` (dropping the leading underscore — it now has a real cross-module caller) and extended: after the existing Customer/Person/Project lines, appends one `- [[<company-hub-stem>]]` line per name in `mentioned_companies` (each resolved to its own hub note stem via the SAME `vault_writer.hub_note_path` convention the existing Customer line already uses) — the existing honest-omission contract (an unresolvable relationship is omitted, never guessed) is preserved unchanged for the pre-existing three link kinds.
- `synthesize_thread`'s own call to `build_thread_related_wikilinks`/`replace_body_section(..., "## Related", ...)` is REMOVED entirely — it now writes exactly `## Summary`, nothing else in the body.
- `section_ownership.py`: `_CALLER_ALLOW_LISTS["email_classification.synthesize_thread"]` narrows to `frozenset({"## Summary"})`; a new entry `"librarian_housekeeping.populate_thread_related_links": frozenset({"## Related"})` is added in the SAME change — never a window where both are simultaneously permitted.
- New `librarian_housekeeping.populate_thread_related_links() -> dict` Job in `app/business/pipelines/librarian_housekeeping.py`:
  - Iterates `vault_writer.list_thread_notes()`.
  - For each Thread, reads its current `customer`/`participants`/`project` frontmatter and its full `messages/` content (composed the same way `synthesize_thread` already assembles `full_content`), calls `T05`'s `detect_mentioned_companies_for_thread(full_content, primary_customer=customer)`, filters to `"known"` + `"new_unambiguous"` mentions only (an `"ambiguous"` one is `T07`'s own concern — never wikilinked here as if it were resolved) — wait, an `"ambiguous"` mention is genuinely unresolved and must be omitted from `## Related` too, honest-omission-style, since linking it would contradict the very Pending-Approval gate `T07` puts it behind.
  - Calls `build_thread_related_wikilinks(customer, participants, project, mentioned_companies=[m["name"] for m in known_and_new_unambiguous_mentions])`.
  - Writes the result via `vault_writer.replace_body_section(path, "## Related", content, caller="librarian_housekeeping.populate_thread_related_links")`.
  - Returns `{"updated": [conversation_id, ...]}`.

---

## Files to Modify

- `src/backend/app/business/email_classification.py` — rename/extend `_build_thread_related_wikilinks` → `build_thread_related_wikilinks`; remove `synthesize_thread`'s own `## Related` write.
- `src/backend/app/data_access/section_ownership.py` — narrow `synthesize_thread`'s entry; add the new `librarian_housekeeping.populate_thread_related_links` entry, in the SAME change.
- `src/backend/app/business/pipelines/librarian_housekeeping.py` — add `populate_thread_related_links()` Job.

---

## Constraints

- Inherits from parent story.
- The allow-list narrowing (`synthesize_thread`) and the new caller registration must land in the SAME commit/change — never a window where both callers are simultaneously permitted to write `## Related` (Scenario 6/8's own "sole ownership by construction" requirement).
- An `"ambiguous"` company mention (per `T05`'s classification) is never wikilinked into `## Related` — honest omission, mirrors the existing "unresolved relationship is omitted, never guessed" contract for Person/Project links.
- `build_thread_related_wikilinks`'s existing Customer/Person/Project honest-omission behavior must not change for any Thread that names no company mentions at all.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-72-US-01-AC-06]` Direct Python-shell check: call `email_classification.synthesize_thread(conversation_id)` for a real Thread with an existing `## Related` section; confirm `## Summary` is regenerated but `## Related` is left byte-for-byte unchanged by this call. Then directly attempt `vault_writer.replace_body_section(path, "## Related", "anything", caller="email_classification.synthesize_thread")` and confirm it raises `section_ownership.SectionWriteNotAllowed` — the SAME code-enforced guard, not merely a convention.
2. `[REQ-SB-72-US-01-AC-07]` Direct Python-shell check: pick (or construct) a real Thread whose content genuinely names at least one other real, already-known company beyond its own primary Customer, and whose participants include at least one sender with a real, existing Person note. Call `librarian_housekeeping.populate_thread_related_links()`. Confirm `## Related` now contains a real `[[wikilink]]` to the Thread's own Customer hub, a real `[[wikilink]]` for the participant with an existing Person note (any participant with none is confirmed absent, not guessed), and a real `[[wikilink]]` for the other mentioned company — never a raw, unlinked email address anywhere in the section.
3. `[REQ-SB-72-US-01-AC-08]` Immediately after step 2, call `email_classification.synthesize_thread(conversation_id)` again for the SAME Thread (e.g. after a further raw message arrives). Confirm `## Summary` is regenerated as normal, and `## Related`'s own content is byte-for-byte identical before and after this call — proving sole ownership by construction, not by the two callers happening to agree.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `synthesize_thread` writes exactly `## Summary`, nothing else
- [x] `synthesize_thread`'s allow-list no longer includes `## Related`; the write is rejected outright, not merely undeclared
- [x] `populate_thread_related_links` fully regenerates `## Related` with real Customer/Person/Company wikilinks, honest-omission preserved
- [x] A subsequent `synthesize_thread` re-synthesis leaves `## Related` byte-for-byte unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Acting on an `"ambiguous"`/`"new_unambiguous"` company mention beyond linking it (Customer folder creation, Pending Approval) — `T07`.
- The `/poc/librarian-populate-related` HTTP endpoint and the orchestrating `run_housekeeping_pass` — `T08`.

---

## Context / Notes

Depends on `T02` because both this task and `T02` edit `synthesize_thread`'s own body (`T02` reorders the `messages/` read; this task removes the `## Related` write) — sequenced to avoid two tasks landing conflicting edits to the same function. Depends on `T05` for `detect_mentioned_companies_for_thread`.

---

## Implementation Log

**Resumed session, 2026-08-18/19.** Code for this task (`build_thread_related_wikilinks` promoted/extended in `email_classification.py`, `synthesize_thread`'s own `## Related` write removed, `section_ownership.py`'s allow-list narrowed + new caller registered in the same change, `populate_thread_related_links` Job in `librarian_housekeeping.py`) was already present on disk from an earlier interrupted coder session — confirmed correct by direct reading before any further action, not re-implemented from scratch.

**`[REQ-SB-72-US-01-AC-06]` — verified, real evidence:**
1. Real Thread `D05C9002AFC20B4DB222A45E202B1862` had a pre-existing `## Related` = `- [[Aldar]]`. Called the real endpoint `POST /poc/synthesize-thread?conversation_id=D05C9002AFC20B4DB222A45E202B1862` (200 OK). Read `## Related` after: byte-identical (`- [[Aldar]]`); `## Summary` was regenerated (new content confirmed). `synthesize_thread` did not touch `## Related`.
2. Direct guard check (single, non-mutating Python-shell call — this raises BEFORE any file I/O, confirmed by reading `replace_body_section`'s own source first): `vault_writer.replace_body_section(path, "## Related", "anything", caller="email_classification.synthesize_thread")` raised `section_ownership.SectionWriteNotAllowed: caller 'email_classification.synthesize_thread' is not allowed to write header '## Related'`. Confirmed code-enforced, not conventional.

**`[REQ-SB-72-US-01-AC-07]` — verified, real evidence:** Called the real endpoint `POST /poc/librarian-populate-related` (the Librarian's Job, which iterates the full real Thread corpus). Re-read `D05C9002AFC20B4DB222A45E202B1862`'s `## Related` afterward: `- [[naima.bikbi@core42.ai]]\n- [[Aldar]]\n- [[Inception]]` — a real Person wikilink (confirmed `Work/People/naima.bikbi@core42.ai.md` exists on disk), the Thread's own Customer, and a real mentioned company ("Inception AI" is named in the Thread's own synthesized content) — no raw, unlinked email address anywhere. Cross-checked against dozens of other real Threads (e.g. `BF8E5A20C38D4B36B1687E39FCB3172F` → `Microsoft`/`Sindan`/`Mubadala`) — same honest, real-wikilink shape throughout.

**`[REQ-SB-72-US-01-AC-08]` — verified, real evidence:** Immediately after the above, called `POST /poc/synthesize-thread?conversation_id=D05C9002AFC20B4DB222A45E202B1862` again (200 OK). Re-read `## Related`: byte-for-byte identical (`- [[naima.bikbi@core42.ai]]\n- [[Aldar]]\n- [[Inception]]`) — confirmed via a captured-before/captured-after string equality check, not eyeballing. `## Summary` was regenerated as normal. Sole ownership by construction, confirmed live.

**Real-vault bulk backfill progress (operational work, not itself a locked AC):** at session start, 20/126 real Threads had a populated `## Related`. Ran `POST /poc/librarian-populate-related` (the real endpoint, never a raw script) multiple times across this session; ended at 87/126 with real, non-empty content (the remainder is a mix of genuinely-not-yet-reprocessed Threads and Threads that honestly resolve to no customer/person/company at all, indistinguishable from content alone). **A real, disclosed, reproducible infrastructure finding, not a code defect:** this Job has no per-thread scope/limit — every call re-processes the full 126-Thread corpus (one real Compass call per Thread), taking 30–60+ minutes end-to-end. Three separate attempts in this session had their backing background server process reclaimed by the coding-session's own tool harness partway through (once after ~40 min, once after ~35 min, once after ~55 min) — confirmed via live log inspection each time that the Job itself was still actively succeeding (`HTTP Request: POST https://api.core42.ai/v1/chat/completions "200 OK"` lines continuing) right up to the kill, never a server crash or application error. This is the same failure class the two PRIOR coder sessions on this task hit, now reproduced a third time with root cause narrowed to the coding session's own background-process lifecycle, not the application. See `ESCALATIONS.md`/`REVIEW-QUEUE.md` and `SPRINT-063`'s own retrospective. The remaining Threads will be completed by `T09`'s own real, persisted 6-hour scheduled `run_housekeeping_pass` once running on the operator's own normally-launched (non-session-bounded) backend — the story's own intended self-healing mechanism.

**No concurrent mutating calls were ever made** — every attempt at `populate_thread_related_links`/`backfill_company_folders` was verified via live log tailing to be single-in-flight before any further action; a second call was only ever issued after confirming (via process absence + `/system-health`) that the prior one had actually ended.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired for this task's own scope (the infra finding above is disclosed via `REVIEW-QUEUE.md`/`ESCALATIONS.md` and the sprint retro, not a scope-internal ambiguity in this task's own build).
