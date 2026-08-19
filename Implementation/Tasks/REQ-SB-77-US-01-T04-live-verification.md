---
id: REQ-SB-77-US-01-T04
title: Live verification — Scenarios 1-5/7 across the real vault
parent_story: REQ-SB-77-US-01
requirement_id: REQ-SB-77
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-77-US-01-T01]
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-77-US-01-T04 — Live verification, Scenarios 1-5/7

## Parent Story

- Story: [[REQ-SB-77-US-01]] — `../UserStories/REQ-SB-77-US-01-people-notes-linked-to-company-partner-note.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-77 *People Notes Linked to Their Real Company/Partner Note*
- Architecture: `Implementation/Architecture/architecture.md` → "People Notes Retroactively Linked to Company/Partner"

---

## Objective

Confirm, live, against the real vault: matched-Customer linking (Scenario 1), matched-Partner linking (Scenario 2), Affiliate linking with no special-casing (Scenario 3), non-match stays unblocked (Scenario 4), no-company-at-all stays unchanged (Scenario 5), and idempotent re-run (Scenario 7) — using `T01`'s new `relink_people_for_thread_paths` (or the already-existing whole-vault `retrofit_people_from_emails`, either satisfies these Gherkin's own "the re-linking capability runs" wording).

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed: `relink_people_for_thread_paths` exists.
- The real vault has (or this task creates, disposably, where a genuine real example isn't available) Person notes covering each of the 5 cases above.

**After / Outputs:**
- Each of the 6 scenarios (1,2,3,4,5,7) is independently confirmed against real vault state, with a real before/after check proving no existing Person note is ever moved or duplicated.
- Every real write this task makes (or disposable test note it creates) is recorded explicitly in the Implementation Log.

---

## Files to Modify

- `src/backend/app/business/people_extraction.py` — no code change expected (verification-only); fix a genuine live-found defect here, in scope, if one surfaces.

---

## Constraints

- Inherits from parent story.
- **Prefer real vault data over disposable test entities wherever a genuine real example exists** — a real company/Person pair the operator would want linked anyway is stronger evidence than a fabricated one; use a clearly-labeled disposable example only where no real, low-risk case is currently available (e.g. Scenario 3's Affiliate case, if `REQ-SB-76-US-01` has not yet produced a real Affiliate).
- **Never move or duplicate an already-existing Person note** — every scenario's own before/after check must explicitly confirm the note's own file path is byte-identical before and after.
- Any disposable test artefact created for this task's own verification must be cleaned up afterward and disclosed in the Implementation Log.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-77-US-01-AC-01]` Find (or construct, disposably) a real Person note tagged `company/<slug>` for a company NOT yet a known Customer. Confirm that company as a real Customer (via a real `REQ-SB-76` approval, or by direct `customer_hub_linking.ensure_customer_hub_note` call as a disposable-test substitute if `REQ-SB-76` has not shipped yet). Record the Person note's own file path. Call `relink_people_for_thread_paths` for that Person's own Thread (or `retrofit_people_from_emails()` for the whole vault). Confirm the Person note's body now carries the real `**Customer:** [[Hub]]` wikilink, AND its file path is unchanged from the recorded value.
2. `[REQ-SB-77-US-01-AC-02]` Same shape, for a company confirmed as a real Partner. Confirm the real `**Partner:** [[Hub]]` wikilink and unchanged file path.
3. `[REQ-SB-77-US-01-AC-03]` Same shape, for a company confirmed as an Affiliate (a Customer- or Partner-kind entity with `affiliate_of` set — real if available from `REQ-SB-76`, disposable-test otherwise). Confirm the Person note links to the Affiliate's own concept file with no special-case code path — the same `find_matching_customer`/`find_matching_partner` scan as steps 1/2.
4. `[REQ-SB-77-US-01-AC-04]` Find a real Person note tagged `company/<slug>` for a company matching neither a known Customer nor Partner. Run the re-linking capability. Confirm the note is left with its tag and no wikilink, at its normal location — never blocked or erroring.
5. `[REQ-SB-77-US-01-AC-05]` Find a real Person note derived from a personal/free-email domain (or no email at all), carrying no company tag. Run the re-linking capability. Confirm the note is completely unchanged (byte-for-byte, including file path).
6. `[REQ-SB-77-US-01-AC-07]` Re-run the re-linking capability a second time against the same real Threads/Persons from steps 1-3 (already fully linked). Confirm zero content or location change on any of them — a true no-op.
7. Record every real write and every disposable artefact created/cleaned up explicitly in the Implementation Log.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `[REQ-SB-77-US-01-AC-01]` Customer-match linking verified live, note location unchanged
- [ ] `[REQ-SB-77-US-01-AC-02]` Partner-match linking verified live, note location unchanged
- [ ] `[REQ-SB-77-US-01-AC-03]` Affiliate linking verified live via the same scan, no special-casing
- [ ] `[REQ-SB-77-US-01-AC-04]` Non-match stays unblocked, tag-only
- [ ] `[REQ-SB-77-US-01-AC-05]` No-company-at-all note stays completely unchanged
- [ ] `[REQ-SB-77-US-01-AC-07]` Re-run against an already-linked vault is a true no-op
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Scenario 6 (both trigger points) — `T02`/`T03` own that.
- Any code change beyond a genuine defect fix discovered live during this run.

---

## Context / Notes

Mirrors this project's own established "prefer the closest-to-real substitute, disclose disposable-test fallbacks explicitly" verification discipline (`Implementation/Learnings.md`, `SPRINT-022`/`SPRINT-024`/`SPRINT-028`).

---

## Implementation Log

_(Filled in by the coder during implementation: what was changed, any deviations
from the plan, observed verification outcomes keyed by AC-ID.)_
