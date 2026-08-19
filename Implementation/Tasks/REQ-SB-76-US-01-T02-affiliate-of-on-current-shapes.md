---
id: REQ-SB-76-US-01-T02
title: Restore affiliate_of onto Customer's OKF shape; add it to Partner's hub-note shape
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

# REQ-SB-76-US-01-T02 — affiliate_of on Customer's OKF shape + Partner's hub-note shape

## Parent Story

- Story: [[REQ-SB-76-US-01]] — `../UserStories/REQ-SB-76-US-01-company-review-extract-classify-and-batch-apply.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-76 *Company Review — Extract & Recommend, Customer/Partner/Affiliate Classification, Batch-Apply*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Company Review" (§ "`affiliate_of`"), `Implementation/Architecture/ADR.md` → `ADR-057` Decision 4 (narrowly revises `ADR-009` point 3)

---

## Objective

Add a real `affiliate_of` frontmatter key (default `""`) to both `vault_writer.build_customer_concept_frontmatter` (the current OKF Customer concept-file shape) and `vault_writer._PARTNER_HUB_NOTE_BASELINE_KEYS`/`create_partner_hub_note_baseline`/`ensure_partner_hub_note_baseline_frontmatter` (Partner's hub-note shape) — restoring it for Customer, adding it for Partner.

---

## Starting State → End State

**Before / Inputs:**
- `build_customer_concept_frontmatter` returns `type/title/description/tags/status/stale_after/generated/verified/sources` — no `affiliate_of` key. (The LEGACY flat `create_customer_hub_note_baseline`/`_HUB_NOTE_BASELINE_KEYS` still carries it — untouched by this task.)
- `_PARTNER_HUB_NOTE_BASELINE_KEYS = ("type", "partner", "tags")` — no `affiliate_of` key at all; `create_partner_hub_note_baseline`'s docstring explicitly says "deliberately no affiliate_of."

**After / Outputs:**
- `build_customer_concept_frontmatter(customer)` includes `"affiliate_of": ""`.
- A brand-new Customer OKF directory (`create_customer_directory_baseline`) carries `affiliate_of: ""`; an already-existing one gets it top-up-inserted on the next `ensure_customer_directory_baseline` call, with zero further code change (both already iterate the dict this function returns).
- `_PARTNER_HUB_NOTE_BASELINE_KEYS = ("type", "partner", "tags", "affiliate_of")`; `create_partner_hub_note_baseline`/`ensure_partner_hub_note_baseline_frontmatter` both default it to `""`.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — `build_customer_concept_frontmatter`, `_PARTNER_HUB_NOTE_BASELINE_KEYS`, `create_partner_hub_note_baseline`, `ensure_partner_hub_note_baseline_frontmatter`.

---

## Constraints

- Inherits from parent story.
- Additive only — one new dict key. No other field in either shape changes.
- Setting a REAL (non-empty) `affiliate_of` value is out of this task's scope — it reuses the already-existing generic `vault_writer.upsert_frontmatter_key`, wired by `T06`. This task only adds the KEY with an empty-string default.
- `create_partner_hub_note_baseline`'s own docstring line ("deliberately no `affiliate_of`, Partner has no Affiliate concept, ADR-009") must be corrected to reflect this revision — a stale docstring contradicting the real code is worse than none.
- Narrowly, additively revises `ADR-009` point 3 only (already recorded in `ADR-009`'s own `**Status:**` line by the architect) — this task does not itself edit `ADR.md`.

---

## Tests

**Manual verification steps:**
1. Call `build_customer_concept_frontmatter("Test Co")` directly; confirm the returned dict includes `"affiliate_of": ""` alongside every pre-existing key, unchanged.
2. `[REQ-SB-76-US-01-AC-05]` (structural half) Call `create_customer_directory_baseline` for a real, new, disposable test Customer name (clearly labeled, e.g. `"ZZ-Decomposer-Test-Customer"`); confirm the written `<slug>.md` concept file's real frontmatter on disk includes `affiliate_of: ""`. Clean up the disposable directory afterward (delete — this is a throwaway test artefact under a clearly non-real name, not real production data).
3. Call `ensure_customer_directory_baseline` against a REAL, already-existing Customer folder in the live vault (one that predates this task, so it currently lacks `affiliate_of`); confirm the top-up inserts `affiliate_of: ""` without touching any other existing key or the body.
4. `[REQ-SB-76-US-01-AC-06]` (structural half) Call `create_partner_hub_note_baseline` for a real, new, disposable test Partner name; confirm the written note's frontmatter includes `affiliate_of: ""`. Clean up afterward.
5. Call `ensure_partner_hub_note_baseline_frontmatter` against a REAL, already-existing Partner hub note in the live vault; confirm the top-up inserts `affiliate_of: ""` without disturbing any other key or the body.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `build_customer_concept_frontmatter` gains `"affiliate_of": ""`
- [x] `_PARTNER_HUB_NOTE_BASELINE_KEYS` gains `"affiliate_of"`; both Partner baseline functions default it to `""`
- [x] Top-up (`ensure_*`) paths confirmed live against a real, pre-existing Customer folder and a real, pre-existing Partner hub note
- [x] `create_partner_hub_note_baseline`'s stale "deliberately no affiliate_of" docstring line corrected
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision beyond `ADR-057`)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Setting a real `affiliate_of` value on any real entity (`T06`'s own scope).
- The legacy flat Customer hub-note shape (`create_customer_hub_note_baseline`/`_HUB_NOTE_BASELINE_KEYS`) — already carries `affiliate_of`, untouched.
- Editing `ADR.md` — the architect already recorded this revision in `ADR-009`'s `**Status:**` line.

---

## Context / Notes

The AC-05/AC-06 full scenarios (a real value pointing at a real parent) are completed by `T06`; this task only proves the field exists on both shapes and top-ups correctly — the structural precondition `T06`'s own `upsert_frontmatter_key` call depends on.

---

## Implementation Log

**2026-08-19, coder.** `build_customer_concept_frontmatter` gained `"affiliate_of": ""` as its final dict key. `_PARTNER_HUB_NOTE_BASELINE_KEYS` extended to `("type", "partner", "tags", "affiliate_of")`; `create_partner_hub_note_baseline` and `ensure_partner_hub_note_baseline_frontmatter` both gained the `"affiliate_of": ""` default. `create_partner_hub_note_baseline`'s stale "deliberately no affiliate_of, Partner has no Affiliate concept, ADR-009" docstring line corrected to reflect `ADR-057` Decision 4's narrow revision. Purely additive — no other field touched in either shape.

**Verification — all manual, live:**
1. `build_customer_concept_frontmatter("Test Co")` → confirmed `"affiliate_of": ""` present alongside every pre-existing key.
2. `[REQ-SB-76-US-01-AC-05]` (structural half) `create_customer_directory_baseline("ZZ-Decomposer-Test-Customer")` → written concept file's real frontmatter on disk carried `affiliate_of: ""`; disposable directory deleted afterward.
3. `ensure_customer_directory_baseline("ADNOC")` against the REAL, pre-existing ADNOC OKF Customer folder (predates this task, confirmed missing `affiliate_of` before the call) → top-up inserted exactly `affiliate_of: ""`, every other key/the body untouched. A second, later re-run (during `T06`/`T09` prep) returned `inserted: []` — confirms idempotent top-up.
4. `[REQ-SB-76-US-01-AC-06]` (structural half) `create_partner_hub_note_baseline("ZZ-Decomposer-Test-Partner")` → written note's frontmatter included `affiliate_of: ""`; disposable note deleted afterward.
5. `ensure_partner_hub_note_baseline_frontmatter` against TWO real, pre-existing Partner hub notes: `Core42.md` (found already carrying `affiliate_of: ""` at test time — a real, disclosed side effect: this project's own automatic capture-on-startup scheduler, per `architecture.md` → "Local Development," fired between the code change landing and this check, independently exercising the exact same top-up path live) and `Presight.md` (genuinely missing `affiliate_of` beforehand) → top-up inserted `affiliate_of: ""` for Presight, correctly no-op'd for the already-topped-up Core42, neither disturbed any other key or the body.

**Assumption (scope-internal):** none beyond the task's own text.

No `MEMORY.md`-worthy new decision beyond `ADR-057`. `CHANGELOG.md` entry appended. This closes the disclosed `REQ-SB-54-US-01-T04`/`ADR-009` gap jointly with `T03`.
