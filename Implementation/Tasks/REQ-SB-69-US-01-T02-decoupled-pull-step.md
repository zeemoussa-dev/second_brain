---
id: REQ-SB-69-US-01-T02
title: outlook_com.list_recent_mail gains on_item_fetched callback; new app/business/pipelines/email_pull.py::pull_and_stage_emails
parent_story: REQ-SB-69-US-01
requirement_id: REQ-SB-69
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-69-US-01-T01]
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-69-US-01-T02 — Decoupled Pull step

## Parent Story

- Story: [[REQ-SB-69-US-01]] — `../UserStories/REQ-SB-69-US-01-decoupled-email-pull-and-human-readable-thread-notes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-69 *Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes*

---

## Objective

Give `outlook_com.list_recent_mail` an additive, backward-compatible
`on_item_fetched` callback (`ADR-046` Decision 2), and build the new
`app/business/pipelines/email_pull.py::pull_and_stage_emails` — the ONE
function in the whole email path that still imports `outlook_com`
(`ADR-046` Decision 3) — so a real Pull can incrementally, resumably
stage every item as it's fetched, never buffering until the whole COM
loop returns.

---

## Starting State → End State

**Before / Inputs:**
- `outlook_com.list_recent_mail(limit: int = 10, unread_only: bool =
  False) -> list[dict]` (`app/data_access/outlook_com.py`, lines
  216-249) resolves each item fully (sender/attachments/recipients)
  inside its own per-item loop, appends to a local `results` list, and
  only returns the WHOLE list once the loop ends or `limit` is reached —
  a stall/exception partway through the loop loses every already-fetched
  item this call session, since nothing is durably persisted until the
  function returns.
- No `email_pull.py` module exists. `T01`'s `email_staging.stage_email`
  exists and is ready to be called per-item.

**After / Outputs:**
- `outlook_com.list_recent_mail` gains one new, optional, additive
  parameter: `on_item_fetched: Callable[[dict], None] | None = None`.
  Inside the existing per-item loop, immediately after an item's own
  dict (`results.append({...})`'s own dict literal) is fully built —
  BEFORE continuing to the next item, never buffered — call
  `on_item_fetched(item_dict)` if it was given. The function's own
  return value and every existing behavior for a caller that passes
  nothing (`classify_recent_emails`, `email_poc_router.py`'s standalone
  endpoint) is byte-for-byte unaffected — this is a strictly additive
  signature change.
- A new `app/business/pipelines/email_pull.py` module, a sibling to
  `email_capture_pipeline.py` inside the existing `app/business/
  pipelines/` subpackage (`ADR-043` point 1), owning:
  `pull_and_stage_emails(limit: int = 10) -> dict` — calls
  `outlook_com.list_recent_mail(limit=limit, on_item_fetched=
  email_staging.stage_email)`, filtering out (never re-staging) any item
  whose `id` is already in `vault_writer.load_processed_email_ids()` OR
  already present in `email_staging.list_staged_emails()` (a light
  pre-check so a Pull re-run against an overlapping recent-N window
  doesn't re-stage a duplicate copy of mail already staged-but-not-yet-
  processed) — `already_processed`/`mark_email_processed` itself is
  UNCHANGED, still consulted a SECOND time later, at processing time
  (`T03`), exactly as `ADR-043` point 2 already established. Returns an
  honest summary dict, e.g. `{"fetched": int, "newly_staged": int,
  "already_staged_or_processed": int}`.

---

## Files to Modify

- `src/backend/app/data_access/outlook_com.py`:
  - Add `from typing import Callable` (or use `collections.abc.Callable`
    per this module's own existing import style) and widen
    `list_recent_mail`'s signature to accept
    `on_item_fetched: Callable[[dict], None] | None = None`.
  - Inside the existing per-item `for item in items:` loop, after the
    `results.append({...})` call succeeds for a given item, call
    `if on_item_fetched is not None: on_item_fetched(results[-1])` (or
    build the item dict as a local variable first, append it, then call
    the callback with that same local — either shape is fine as long as
    the callback receives the exact same dict that was appended). Every
    existing caller (no argument passed) is unaffected.

- `src/backend/app/business/pipelines/email_pull.py` (**new file**) —
  `pull_and_stage_emails(limit: int = 10) -> dict` per the End-State
  above. Imports `outlook_com` and `email_staging` (`T01`) and
  `vault_writer` (for `load_processed_email_ids`).

---

## Constraints

- Inherits from parent story.
- **`on_item_fetched` is optional and additive** — every existing caller
  of `list_recent_mail` (`email_classification.classify_recent_emails`,
  `email_poc_router.py`'s standalone `/poc/classify-emails` endpoint,
  and this story's own `T03`-restructured `email_capture_pipeline.py`,
  which no longer calls `list_recent_mail` at all after this story) must
  see zero behavior change if it passes nothing.
- **Never buffer staging until the whole COM loop returns** — the
  callback must fire per-item, inside the existing loop, immediately
  after that item is fully resolved. This is the concrete mechanism
  making a mid-loop stall leave every already-fetched item durably
  staged (the operator's own "live-updating, resumable, incremental"
  steer, `ADR-046` Context).
- **`email_pull.py` is the ONLY module in the whole email path that
  imports `outlook_com` after this story ships** (parent story's own
  Constraint) — no other file this task touches (or any later task in
  this story) may add an `outlook_com` import.
- **`already_processed`/`mark_email_processed` (`vault_writer.py`) are
  UNCHANGED** — this task only reads `load_processed_email_ids()` as a
  pre-filter; it never calls `mark_email_processed` (that stays `T03`'s
  own job, at processing time, per `ADR-043` point 2's already-
  established "consulted a second time" contract).
- No change to `email_capture_pipeline.py` in this task — that
  restructuring is `T03`.

---

## Tests

<!-- No locked AC maps directly to this task alone — Scenario 1's own
"real, live-triggered pull stages content" outcome is the shared basis
for AC-01, which is verified end-to-end once T03/T04 also land (see
T04's own Tests). This task's own Tests are plain, non-AC checks proving
the callback and the Pull step itself are correct in isolation before
any downstream task composes them. -->

**Manual verification steps** (real Outlook desktop running; real
configured `VAULT_PATH`):

1. Direct Python-shell call: `outlook_com.list_recent_mail(limit=3,
   on_item_fetched=lambda item: print("fetched:", item["subject"]))`.
   Confirm the callback prints once per item, in the same order the
   function's own returned list is later observed to be in, and confirm
   the function's own final return value is unaffected (still the same
   `list[dict]` shape as calling it with no callback at all).
2. Direct Python-shell call: `email_pull.pull_and_stage_emails(limit=3)`
   against a real inbox with at least one genuinely new (never-before-
   captured) email. Confirm `email_staging.list_staged_emails()` now
   contains a real, newly-staged entry for that email, and confirm the
   function's own returned summary dict's counts are consistent with
   what was actually staged.
3. Re-run `email_pull.pull_and_stage_emails(limit=3)` immediately again
   (no new mail arrived in between). Confirm no duplicate staged copy is
   created — `email_staging.list_staged_emails()`'s count is unchanged
   from step 2 (the "already staged" pre-filter working).
4. Confirm `outlook_com.py`'s own two other real callers
   (`classify_recent_emails`, `email_poc_router.py`'s POC endpoint) are
   unaffected — a plain code read confirming neither passes
   `on_item_fetched`, so both keep their exact pre-existing
   buffer-then-return behavior.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `on_item_fetched` callback fires per-item, inside the loop, never
      buffered
- [x] Every existing `list_recent_mail` caller unaffected (Test step 4)
- [x] `pull_and_stage_emails` stages real, newly-fetched mail and skips
      already-staged/already-processed mail on a re-run
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint — not
      warranted (see `## Implementation Log`): this task is a direct, mechanical
      build of `ADR-046` Decisions 2/3, no new decision/pattern/constraint beyond
      what the ADR already recorded
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `email_capture_pipeline.py` reading from staging — `T03`.
- Independent-dispatch capability wiring (`pull_email` as a schedulable
  Skill, the new processing lock, `capture_scheduler.py` restructuring)
  — `T04`.

---

## Context / Notes

`ADR-046` Decisions 2 and 3 (`Implementation/Architecture/ADR.md`) are
the full architectural reasoning. `outlook_com.py`'s own real per-item
loop (lines 216-249, as read for this story's grounding) does sender
resolution, attachment extraction, and recipient resolution per item —
any of which can stall; the callback must fire AFTER all of that work
for a given item has already completed (i.e. exactly where the existing
`results.append({...})` call already sits), not before.

---

## Implementation Log

**Built as designed, no deviations from `## Starting State → End State`.**

`src/backend/app/data_access/outlook_com.py`:
- Added `from collections.abc import Callable` (this module's own existing
  import style has no `typing` import at all, so `collections.abc.Callable`
  was used rather than introducing a new `typing` import for one type
  hint).
- `list_recent_mail` gained `on_item_fetched: Callable[[dict], None] |
  None = None`. Inside the existing per-item loop, the item's own dict is
  now built as a local (`fetched_item`), appended to `results` (unchanged
  behavior), and THEN, immediately after — still inside the loop, before
  continuing to the next item — `on_item_fetched(fetched_item)` is called
  if given. Every existing caller (no argument passed) is byte-for-byte
  unaffected; only a strictly additive, default-`None` parameter was
  added, and the function's own return value/shape is unchanged.

`src/backend/app/business/pipelines/email_pull.py` (**new file**):
- `pull_and_stage_emails(limit: int = 10) -> dict` — computes a `skip_ids`
  set once up front (`vault_writer.load_processed_email_ids()` unioned
  with every id already in `email_staging.list_staged_emails()`), then
  passes a small closure as `on_item_fetched` to
  `outlook_com.list_recent_mail(limit=limit, on_item_fetched=...)`. The
  closure increments `fetched`, and either stages the item (`email_staging
  .stage_email`, adds the id to `skip_ids` so a second occurrence of the
  same id later in the SAME call also doesn't double-count/double-stage)
  and increments `newly_staged`, or increments
  `already_staged_or_processed` if the id was already in `skip_ids`.
  Returns `{"fetched", "newly_staged", "already_staged_or_processed"}`.

**Scope-internal judgement call (logged per `Implementation/Pipeline.md`
hard rule 5, not a MUST-FLAG trigger):** the task's own End-State text
illustrates the call as literally `on_item_fetched=email_staging.
stage_email`, but the very same paragraph also requires "filtering out
(never re-staging)" already-processed/already-staged ids — passing
`stage_email` directly as the raw callback would stage every fetched item
unconditionally, with no filtering at all, contradicting that same
sentence. Reconciled by wrapping the filter-and-stage logic in a small
closure passed as the callback instead of passing `email_staging.
stage_email` raw — this is the only way to satisfy BOTH "staging fires
per-item, inside the loop" AND "already-staged/processed ids are filtered
out, never re-staged" from the one described mechanism; the illustrative
code snippet was simplified prose, not a literal contract (mirrors
`REQ-SB-55-US-01-T07`'s own precedent for reconciling illustrative text
against Constraints via the End-State intent).

**Observation (informational, not a MUST-FLAG trigger — logged for the
record, no action taken, no file outside this task's own `## Files to
Modify` was touched):** `src/backend/app/business/pipelines/
email_capture_pipeline.py` was read (read-only, for grounding, per this
task's Context) and already reflects `T03`'s own target end-state (reads
from `email_staging.list_staged_emails()`, no `outlook_com` import) —
confirmed mid-session that a concurrent coder session completed `T03` in
parallel with this one (both are independent siblings of `T01` per the
story's own dependency graph); `T03`'s own task file is now `status:
Done` with its own full Implementation Log. No conflict with this task's
own `## Files to Modify` (`outlook_com.py`, `email_pull.py` — neither
touched by `T03`).

**Manual verification — all four `## Tests` steps run live against the
real, configured Outlook desktop and the real, configured vault
(`VAULT_PATH=C:\myWorx\Moussa MD\Moussa Brain`), via the real backend
venv (`src/backend/.venv`). This task owns no locked AC directly (per the
story's own AC→task mapping table, `AC-01` is verified at `T04`, once
both `T02` and `T03` are composed) — every step below is a plain,
non-AC correctness check, per this task's own `## Tests` framing:**

1. **PASS.** `outlook_com.list_recent_mail(limit=3, on_item_fetched=...)`
   against the real inbox: the callback printed once per item — "Re:
   Naima Pipeline Review", "RE: Azure-Net New Revenue Forecast for H2 for
   AM Updates", "RE: Weekly Forecast l Major Clients" — in the exact same
   order as the function's own returned list (`callback order matches
   return order: True`, directly asserted). The function's own return
   value (3 dicts, same 9-key shape: `id`/`subject`/`sender_name`/
   `sender_email`/`received`/`body`/`attachments`/`conversation_id`/
   `recipients`) was independently confirmed byte-identical in shape to a
   sibling call to `list_recent_mail(limit=3)` with no callback at all —
   the signature change is genuinely additive.
2. **PASS.** `email_pull.pull_and_stage_emails(limit=3)` against the real
   inbox, with the real staging area starting genuinely empty (confirmed
   before the run — no `.second-brain/email_staging/` entries yet).
   Returned `{"fetched": 3, "newly_staged": 3,
   "already_staged_or_processed": 0}`. `email_staging.list_staged_emails()`
   afterward contained exactly those 3 real, newly-staged entries
   (matching subjects/ids), independently confirmed on real disk under
   `.second-brain/email_staging/<entry_id>/` (3 real directories). The
   summary counts matched what was actually staged exactly.
3. **PASS.** Immediately re-ran `pull_and_stage_emails(limit=3)` again, no
   new mail having arrived in between. Returned `{"fetched": 3,
   "newly_staged": 0, "already_staged_or_processed": 3}` —
   `list_staged_emails()`'s count stayed at 3, unchanged from step 2; the
   already-staged pre-filter worked, zero duplicate copies created.
4. **PASS.** Direct code read (`grep`): `email_classification.py::
   classify_recent_emails` line 619 calls `outlook_com.list_recent_mail(
   limit=limit)` — no `on_item_fetched` argument. `email_poc_router.py`'s
   `/poc/classify-emails` endpoint calls `classify_recent_emails(
   limit=limit)` only (confirmed by direct grep — it never imports or
   calls `outlook_com` itself). Neither passes `on_item_fetched`; both keep
   their exact pre-existing buffer-then-return behavior, unaffected by
   this task's additive signature change.

**Cleanup:** none needed/performed. The 3 real emails staged during Test
step 2 (genuinely new, real inbox content, not synthetic/disposable test
data) were deliberately left staged — this is the correct, intended
end-state of a real Pull run: durable staging that survives until a
future real processing run (`run_email_capture_pipeline`, already wired
to read from staging per `T03`) picks them up. No dev server/scheduler
was running during this session (confirmed no listener on ports
8000/8001), so nothing auto-processed them during verification.

gate: clear 2026-08-17 — no MUST-FLAG trigger fired: no material
assumption filling a genuine gap (the one judgement call above reconciles
an internal inconsistency in the task's own illustrative text using its
own stated Constraint, not a guess with no basis); no ADR/architecture
change (this task builds directly against the already-`Accepted`
`ADR-046`); no `ESCALATIONS.md` entry; task not oversized; this task owns
no locked AC directly (confirmed against the story's own AC→task mapping
table), and every one of its own plain Tests steps was verified live and
passed.
