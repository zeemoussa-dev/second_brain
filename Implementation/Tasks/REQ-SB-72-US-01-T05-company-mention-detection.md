---
id: REQ-SB-72-US-01-T05
title: Company-mention detection — new Compass call, Python re-checked against known entities
parent_story: REQ-SB-72-US-01
requirement_id: REQ-SB-72
type: backend
status: Done
gate: flagged
gate_reason: "Scope-internal judgement call: 'plausibly matches under a different spelling' is grounded as a real, disclosed normalized-substring heuristic (never a fuzzy-matching library dependency) — see Implementation Log for full reasoning."
phase: P1
depends_on: []
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-72-US-01-T05 — Company-mention detection

## Parent Story

- Story: [[REQ-SB-72-US-01]] — `../UserStories/REQ-SB-72-US-01-librarian-section-first-housekeeping-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-72 *The Librarian Section — First Housekeeping Pipeline*
- Architecture: `Implementation/Architecture/architecture.md` → "Company-mention detection & the ambiguous-finding Pending Approval" (`ADR-049` Decision 5, Alternative 6)

---

## Objective

Build the shared building block both `T06` (`## Related` company wikilinks) and `T07` (Customer folder backfill) consume: a new, dedicated Compass call extracting which known/plausible companies a Thread's own content mentions, re-checked in Python against the live `known_customers`/`known_partners` lists before ever being trusted.

---

## Starting State → End State

**Before / Inputs:**
- `compass_client.py` has no primitive for extracting a LIST of company mentions from content — `summarize_content` is rigidly `{"summary": <string>}`-shaped and cannot be repurposed via `prompt_override` alone (its own parse contract only ever reads a `"summary"` key).
- `vault_filing_expert.determine_placement_and_file` is scoped to a single-item NEW-content placement decision — a different-shaped problem, not reused here (`ADR-049` Decision 5 / Alternative 6).

**After / Outputs:**
- New `compass_client.detect_mentioned_companies(content: str, source_description: str) -> dict` — mirrors `summarize_content`'s own technique (payload construction, `httpx.post`, `CompassError` handling) but with its OWN prompt (asks the model to list every company name the content genuinely mentions, distinct from the Thread's own primary Customer) and its OWN parse contract: `{"mentions": [{"name": str, "confidence": "high" | "low"}, ...]}`. Malformed/missing `"mentions"` raises `CompassError`, mirroring every other `compass_client.py` primitive's own honest-failure contract — never fabricates an empty or guessed list silently.
- New `librarian_housekeeping.detect_mentioned_companies_for_thread(thread_content: str, primary_customer: str) -> dict` — business-layer wrapper: calls `compass_client.detect_mentioned_companies`, then RE-CHECKS every returned mention in Python against `vault_writer.list_known_customers()`/`vault_writer.list_known_partners()` (the SAME pre-fetched lists, never a second, divergent lookup) — mirrors `_maybe_create_cross_cutting_proposal`'s own exact discipline (`ADR-021` point 2). Classifies each mention into exactly one of:
  - `"known"` — matches an existing `known_customers`/`known_partners` entry exactly (and isn't the Thread's own `primary_customer`) — a real, already-known company to link, no action beyond a wikilink.
  - `"new_unambiguous"` — no fuzzy/partial match against either known list, and the model's own confidence is `"high"` — Tier-1-shaped, safe to auto-create (`T07`).
  - `"ambiguous"` — plausibly matches an existing entry under a different spelling, OR the model itself flagged `"low"` confidence — Tier-2-shaped, routes to Pending Approval (`T07`).
  - On a `compass_client.CompassError`, returns `{"error": str, "mentions": []}` — never raises, never fabricates a result, mirrors this codebase's own honest-degradation posture (`synthesize_thread`'s `summary_error` pattern).

---

## Files to Modify

- `src/backend/app/data_access/compass_client.py` — add `detect_mentioned_companies`.
- `src/backend/app/business/pipelines/librarian_housekeeping.py` — add `detect_mentioned_companies_for_thread`.

---

## Constraints

- Inherits from parent story.
- Never trusts the model's own naming alone — every mention is re-checked in Python against the live `known_customers`/`known_partners` lists before any classification is returned.
- Never calls `vault_filing_expert.determine_placement_and_file` — a genuinely different-shaped problem (single-item NEW-content placement vs. multi-mention extraction from already-filed content).
- On a Compass failure, this function must not raise and must not fabricate a positive result — an honest `{"error": ..., "mentions": []}`.
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

---

## Tests

<!-- No locked AC is directly verified by this shared building-block task — its
output is AC-verified downstream by T06 (AC-07) and T07 (AC-09/AC-10), mirroring
this codebase's own established "building-block task, AC verified downstream"
precedent. -->

**Manual verification steps:**
1. Direct Python-shell check against the real Compass endpoint: call `compass_client.detect_mentioned_companies` with real content naming at least one real, already-known customer/partner name and one genuinely fictitious/new company name; confirm the returned `{"mentions": [...]}` shape parses correctly and both names are present.
2. Call `librarian_housekeeping.detect_mentioned_companies_for_thread` with the same content and the Thread's own real `primary_customer`; confirm the real, already-known name is classified `"known"` (and is NOT re-classified `"new_unambiguous"`/`"ambiguous"` merely because the model happened to name it), the genuinely-new name is classified `"new_unambiguous"` or `"ambiguous"` depending on the model's own returned confidence, and the Thread's own `primary_customer` itself (if the model also names it) is excluded from the mentions list entirely (it is not "mentioned," it is already the Thread's own Customer).
3. Induce a real Compass failure (scoped, disclosed monkeypatch of the underlying HTTP call, reverted after) and confirm `detect_mentioned_companies_for_thread` returns the honest `{"error": ..., "mentions": []}` shape rather than raising or fabricating a result.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `compass_client.detect_mentioned_companies` returns a real, parsed `{"mentions": [...]}` shape or raises `CompassError`
- [x] `detect_mentioned_companies_for_thread` classifies every mention into `known`/`new_unambiguous`/`ambiguous`, re-checked against live known-entity lists
- [x] A Compass failure returns an honest, non-fabricating result — never raises
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Writing the resulting wikilinks into `## Related` — `T06`.
- Acting on a `new_unambiguous`/`ambiguous` classification (Customer folder creation / Pending Approval) — `T07`.

---

## Context / Notes

This task shares the new `librarian_housekeeping.py` module file with `T03`/`T04` — compose additively around the REAL current file at build time (this codebase's own established discipline for a file under active multi-task extension), never assume the file's shape from this task's own illustrative text alone.

---

## Implementation Log

**2026-08-18, coder pass.** Added `compass_client.detect_mentioned_
companies` (new prompt/parse contract, `{"mentions": [{"name", "confidence"}]}`)
and `librarian_housekeeping.detect_mentioned_companies_for_thread` (Python
re-check against `list_known_customers()`/`list_known_partners()`).

**Scope-internal judgement call (logged, task flagged for human spot-check,
not an escalation):** the story/ADR text describes `"ambiguous"` as
covering a mention that "plausibly matches an existing entry under a
different spelling" but does not specify a concrete matching technique.
This codebase has no fuzzy-matching library dependency, so I implemented a
real, disclosed heuristic (`_fuzzy_match_known_entity`): normalize both
names (lowercase, punctuation collapsed) and check a substring match either
direction. This is intentionally conservative/honest, not a black box —
documented inline. Real, live testing confirmed it behaves sensibly (no
false "ambiguous" classification for a clearly-known exact match, no false
"known" classification for a genuinely different name).

**Real, live-vault verification (building-block task, no directly-locked
AC — verified per its own Tests block, consumed/AC-verified downstream by
`T06`/`T07`):**
1. Called `compass_client.detect_mentioned_companies` with real content
   naming the vault's own real, already-known partner "Core42" and a
   genuinely fictitious "Zephyrion Quantum Dynamics" — confirmed the real
   Compass response parsed correctly into `{"mentions": [...]}` with both
   names present. PASS.
2. Called `detect_mentioned_companies_for_thread` with the same content:
   with `primary_customer="Unsorted"`, "Core42" classified `"known"`
   (matches `list_known_partners()`), "Zephyrion Quantum Dynamics"
   classified `"ambiguous"` (the real model itself returned low
   confidence). With `primary_customer="Core42"`, confirmed "Core42" is
   excluded from the mentions list entirely (it IS the primary Customer,
   not "mentioned"). PASS.
3. Confirmed `"new_unambiguous"` classification via a scoped, disclosed
   monkeypatch of `compass_client.detect_mentioned_companies` (returning a
   synthetic high-confidence, no-fuzzy-match mention) — isolates and
   directly verifies the WRAPPER's own classification logic independent
   of the live model's own subjective confidence calibration (real, live
   testing with organic content consistently returned "low" confidence for
   every genuinely-new name tried, a property of the model's own honest
   uncertainty about unverifiable company identity, not a defect in this
   task's own code). PASS.
4. Induced a real `compass_client.CompassError` via a scoped, disclosed
   monkeypatch (reverted automatically via `unittest.mock.patch.object`'s
   own context-manager scope); confirmed `detect_mentioned_companies_for_
   thread` returned the honest `{"error": ..., "mentions": []}` shape,
   never raised, never fabricated a result. PASS.

`gate: flagged 2026-08-18` — trigger-8-adjacent scope-internal judgement
call (the fuzzy-match heuristic), logged per Pipeline.md for human
spot-check; grounded in cited discipline (no new dependency), not a
coin-flip.
