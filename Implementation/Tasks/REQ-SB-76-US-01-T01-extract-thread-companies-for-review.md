---
id: REQ-SB-76-US-01-T01
title: Boilerplate-aware company extraction call — compass_client.extract_thread_companies_for_review
parent_story: REQ-SB-76-US-01
requirement_id: REQ-SB-76
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-76-US-01-T01 — Boilerplate-aware company extraction call

## Parent Story

- Story: [[REQ-SB-76-US-01]] — `../UserStories/REQ-SB-76-US-01-company-review-extract-classify-and-batch-apply.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-76 *Company Review — Extract & Recommend, Customer/Partner/Affiliate Classification, Batch-Apply*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Company Review" (§ "Extraction"), `Implementation/Architecture/ADR.md` → `ADR-057` Decision 1

---

## Objective

Add `compass_client.extract_thread_companies_for_review(thread_content, known_companies, prompt_override=None) -> {"companies": [{"name", "confidence"}, ...]}` — a new, narrower Compass sibling that identifies every real company a Thread's own content genuinely relates to, EXPLICITLY instructed to disregard email-client/device signature boilerplate, mailing-list footers, and disclaimer text — never an edit to the frozen, `Done` `detect_customer_for_thread`.

---

## Starting State → End State

**Before / Inputs:**
- `compass_client.py` has `detect_customer_for_thread` (single-primary-customer question, no boilerplate exclusion, frozen/`Done`) and `detect_mentioned_companies` (multi-mention shape, but deliberately excludes the content's own already-known primary Customer — a different question).
- No function in this codebase asks "every real company this content genuinely relates to, including whichever should become primary, while explicitly excluding signature/device/footer/disclaimer noise."

**After / Outputs:**
- A new `extract_thread_companies_for_review` function exists, mirroring `detect_mentioned_companies`'s own multi-mention JSON parse contract (`{"companies": [...]}`, not `{"mentions": [...]}` — this function's own distinct key name, per `ADR-057`) and every sibling primitive's `httpx.post`/`CompassError` honest-failure shape.
- `detect_customer_for_thread` is untouched, byte-for-byte.

---

## Files to Modify

- `src/backend/app/data_access/compass_client.py` — add the new function (place alongside `detect_mentioned_companies`, its nearest structural sibling).

---

## Constraints

- Inherits from parent story.
- **Never edit `detect_customer_for_thread`** — it is `Done` (`REQ-SB-74-US-01`), frozen per `Implementation/Pipeline.md` hard rule 1.
- Prompt text must explicitly instruct Compass to disregard a name appearing ONLY inside an email-client/device signature line (e.g. "Sent from my iPhone," "Get Outlook for Android"), a mailing-list footer, or a legal disclaimer — these are not genuine mentions (`ADR-057` Decision 1).
- Reuses an exact known name from `known_companies` (caller supplies the UNION of `list_customer_folders()` + `list_known_partners()` — never hardcoded here) when it clearly matches one.
- Malformed/missing `"companies"` raises `CompassError` — never fabricates or silently returns an empty list on a parse failure.
- No retry loop, mirroring every sibling primitive's own precedent.

---

## Tests

**Read-only, zero vault writes** — this function only calls Compass and parses its response; no reversion/cleanup needed for any of the steps below.

**Manual verification steps:**
1. `[REQ-SB-76-US-01-AC-02]` Pick one real Thread from the live vault whose messages carry an email-client/device signature line (e.g. "Sent from my iPhone" or "Get Outlook for Android" — the story's own Context confirms 53 real messages in the vault carry one) and mentions NO other real company in its own substantive content. Call `extract_thread_companies_for_review` directly (Python shell or a throwaway script) against that Thread's real concatenated message content. Confirm the returned `"companies"` list does NOT include "Apple," "iPhone," "Microsoft," "Outlook," "Android," or any other boilerplate-derived name.
2. Pick a second real Thread whose content genuinely, substantively discusses a real, known company (from the live `known_companies` union). Call the function directly against it. Confirm the returned list correctly includes that company, using the exact known spelling.
3. Call the function with malformed/unparseable input (e.g. monkeypatch `httpx.post` in-process to return a response whose JSON body lacks a `"companies"` key) and confirm a `CompassError` is raised, never a silently-empty or fabricated result.
4. Confirm `detect_customer_for_thread`'s own source is byte-for-byte unchanged (diff against its pre-task state).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `extract_thread_companies_for_review` exists with the signature/return shape above
- [x] `[REQ-SB-76-US-01-AC-02]` verified live — a real boilerplate-only mention is never returned as a company
- [x] `detect_customer_for_thread` left byte-for-byte unedited
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision beyond `ADR-057`)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring this function into any Job — that is `T04`'s own scope.
- Any change to `detect_mentioned_companies`/`detect_customer_for_thread`.

---

## Context / Notes

Mirror `detect_mentioned_companies`'s own exact `httpx.post`/header/timeout/`CompassError` scaffolding (`compass_client.py` lines ~364-432) — only the prompt text and parse-contract key name (`"companies"`, not `"mentions"`) differ. `thread_content[:8000]` truncation, matching `detect_customer_for_thread`'s own precedent, is a reasonable default — no locked AC depends on the exact truncation length.

---

## Implementation Log

**2026-08-19, coder.** Added `compass_client.extract_thread_companies_for_review(thread_content, known_companies, prompt_override=None) -> {"companies": [{"name", "confidence"}, ...]}` immediately before `summarize_content` (placed alongside `detect_mentioned_companies`, its nearest structural sibling, per the task's own file-placement note — inserted directly above `summarize_content` since that was the unique, unambiguous insertion point). Mirrors `detect_mentioned_companies`'s own `httpx.post`/header/timeout/`CompassError` scaffolding exactly; only the prompt text and parse-contract key (`"companies"`, not `"mentions"`) differ, per `ADR-057` Decision 1. Prompt explicitly instructs Compass to disregard a name appearing only in an email-client/device signature line, mailing-list footer, or legal disclaimer. `thread_content[:8000]` truncation reused, matching `detect_customer_for_thread`'s own precedent. `detect_customer_for_thread` was NOT touched — the edit was a single-point insertion (`Edit` tool, unique `old_string` match on `def summarize_content(`), so no existing line in the file was altered.

**Verification — all manual, live, against the real vault (`VAULT_PATH`):**
- `[REQ-SB-76-US-01-AC-02]` **PASS.** Real Thread `Work/Threads/2026-08-01 Fw- Project scaffold` (content is almost entirely "Get Outlook for Android" + Microsoft safelinks boilerplate, a forwarded-header stub, no genuine company discussion) → `extract_thread_companies_for_review` returned `{"companies": []}` — no Microsoft/Outlook/Android name fabricated from the boilerplate.
- Real Thread `Work/Threads/2026-08-05 ADNOC Account Plan Review & Discussion Session - H2 FY26` (a real ADNOC account-plan document) → returned `ADNOC` (exact known spelling, confidence 1.0) plus 10 other real, substantively-discussed companies (Microsoft, Core42, AMD, Dell, Honeywell, EY, Schneider, SLB, Armada, "G42 In'tl") — confirms known-name reuse and genuine multi-company extraction.
- Malformed-response test (`httpx.post` monkeypatched to a JSON body missing `"companies"`): raised `CompassError("couldn't parse Compass response: 'companies'")` — never a silent empty/fabricated result.
- `detect_customer_for_thread`'s own source confirmed byte-for-byte unchanged (insertion was a unique, isolated `Edit` elsewhere in the file; also re-read the function's current text and diffed by eye against the pre-task read in this same session — identical).

**Assumption (scope-internal, logged per hard rule 5):** none beyond the task's own stated defaults (8000-char truncation, `prompt_override` parameter mirrored from siblings) — no locked AC depends on the exact truncation length.

No `MEMORY.md`-worthy new decision beyond what `ADR-057` already records. `CHANGELOG.md` entry appended.
