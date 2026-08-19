---
id: REQ-SB-67-US-01-T03
title: One-shot backfill — regenerate Summary + opening line for already-captured Thread notes, in place
parent_story: REQ-SB-67-US-01
requirement_id: REQ-SB-67
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-67-US-01-T02]
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-67-US-01-T03 — One-shot backfill for already-captured Thread notes

## Parent Story

- Story: [[REQ-SB-67-US-01]] — `../UserStories/REQ-SB-67-US-01-real-thread-summary-synthesis-and-backfill.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-67 *Real Per-Thread Summary Synthesis + Existing-Thread Backfill*

---

## Objective

Add `app/business/thread_summary_backfill.py::backfill_thread_summaries() -> list[dict]` plus `POST /poc/backfill-thread-summaries` (`app/api/email_poc_router.py`) — a one-shot, operator-triggered maintenance operation that regenerates `## Summary` + the opening line for every Thread note already sitting in the vault, in place, using the exact same shared synthesis mechanism `T02`'s `thread_match_merge` uses, with no delta (pure resynthesis of what's already persisted) and honest per-item failure handling that never aborts the whole run.

---

## Starting State → End State

**Before / Inputs:**
- `T02`'s new synthesis helper in `email_classification.py` (e.g. `_synthesize_thread_summary(existing_summary, transcript, new_message_body, prompt_override) -> dict`) — this task calls it IDENTICALLY to how `thread_match_merge` does, with `new_message_body=None` (backfill has no new-message delta; a pure resynthesis of the Thread's own currently-persisted `## Summary` + `## Transcript`).
- `T01`'s `vault_writer.replace_body_opening_line(path, new_line) -> bool` and the existing `vault_writer.replace_body_section(path, header, new_content) -> bool` / `vault_writer.read_body_section(path, header) -> str` — this task's own write/read primitives, composed exactly as `T02` composes them.
- `vault_writer.list_all_note_paths() -> list` — every flat `Work/<kind>/<file>.md` note PLUS every OKF concept file; this task filters down to Thread notes by reading each note's own `frontmatter.get("type") == "Thread"` (mirrors `tag_backfill.py`'s own iterate-and-filter shape exactly — no new enumeration primitive).
- `tag_backfill.py::backfill_tags() -> list[dict]` — the exact structural precedent to mirror: iterate `list_all_note_paths()`, `read_note` each, skip/act per-item, append a per-item outcome dict, never raise out of the loop.
- `app/api/email_poc_router.py`'s existing six `/poc/...` endpoints — the exact thin-wrapper shape to mirror (a business function returning `list[dict]`, a router endpoint doing light aggregation: `notes_checked`/an outcome count/`results`).
- `compass_client.CompassError` — the exception this task catches per-item, exactly as `T02` does.

**After / Outputs:**
- `backfill_thread_summaries() -> list[dict]` exists in the new `app/business/thread_summary_backfill.py` module (mirrors `tag_backfill.py`'s own one-module-per-maintenance-operation naming). For every note where `frontmatter.get("type") == "Thread"`: reads the note's own current `## Summary` (`existing_summary`) and `## Transcript` (`transcript`) via `read_body_section`, calls `T02`'s shared synthesis helper with `new_message_body=None` and `prompt_override=agent_prompts.get_prompt("thread_match_merge") or <T02's own default literal>`. On success: writes the new opening line (`T01`'s primitive) and the new `## Summary` (`replace_body_section`), appends `{"note": str(path), "status": "regenerated"}`. On `compass_client.CompassError`: writes nothing (existing Summary/opening line left completely untouched), appends `{"note": str(path), "status": "summary_error", "summary_error": str(exc)}`, and the loop CONTINUES to the next Thread note rather than aborting.
- Frontmatter, `## Transcript`, `## Attachments`, and `tags` are never touched by this function on ANY code path, success or failure — only `## Summary` (via `replace_body_section`) and the opening line (via `T01`'s primitive) are ever written.
- `POST /poc/backfill-thread-summaries` exists in `email_poc_router.py`, calling `backfill_thread_summaries()` and returning `{"notes_checked": len(results), "regenerated": <count where status == "regenerated">, "results": results}` — the same shape every existing `/poc/...` endpoint already returns.

---

## Files to Modify

- `src/backend/app/business/thread_summary_backfill.py` (new file) — `backfill_thread_summaries()`.
- `src/backend/app/api/email_poc_router.py` — add the `POST /poc/backfill-thread-summaries` endpoint, following the file's own existing six-endpoint pattern exactly (new `from app.business.thread_summary_backfill import backfill_thread_summaries` import alongside the existing business-function imports; do not touch any existing endpoint).

---

## Constraints

- Inherits from parent story: **backfill touches ONLY the Summary region and the opening-line sentence** of each already-existing Thread note — frontmatter, `## Transcript`, `## Attachments`, and tags must be left byte-for-byte unchanged (Scenario 3). Never call `upsert_frontmatter_key`, `append_body_section_line`, or any frontmatter/Transcript/Attachments-touching primitive anywhere in this task's own code.
- **Regenerate, don't patch** (`REQ-SB-54` point 8) — both the Summary and the opening line are wholly regenerated via `replace_body_section`/`T01`'s primitive on every run, never incrementally patched.
- **No delta on backfill** — `new_message_body=None` on every call to `T02`'s shared synthesis helper; this is a pure resynthesis of what's already persisted (`existing_summary` + `transcript`), never inventing a "new message" that doesn't exist for this operation.
- **Honest, non-fabricating per-item failure posture** — a `compass_client.CompassError` for ONE Thread note must never abort the whole backfill run; catch it locally per item, record an honest failure outcome, continue the loop (Scenario 6). Mirrors `classify_recent_emails`'/`summarize_attachment`'s own established per-item try/except+continue posture.
- **Sequential, no artificial delay, no hardcoded count** — discover however many Thread notes actually exist at run time via `list_all_note_paths()` filtered by `frontmatter.get("type") == "Thread"`; never a fixed/assumed count, never a batch/concurrency mechanism (parent story's own resolved cost/rate-limiting posture).
- **No new enumeration primitive** — reuse `list_all_note_paths()` + a `type == "Thread"` filter, mirroring `tag_backfill.py`'s own iterate-and-filter shape exactly; do not add a `list_thread_note_paths()` or similar to `vault_writer.py`.
- Do not modify `tag_backfill.py`, any existing `/poc/...` endpoint, `T01`'s primitive, `T02`'s synthesis helper, or `thread_match_merge` itself — compose them as-is.
- Must respect `api → business → data_access` layering (`ADR-003`) — the router endpoint calls the business function, the business function calls `vault_writer`/`email_classification`, never the reverse.
- **This work runs against the user's real, live Obsidian vault (`VAULT_PATH`) and the real, configured Compass Provider** — the parent story's own Dependencies explicitly require Scenario 3's backfill to be verified against the real, already-captured `Work/Threads/*.md` notes, not a mocked/simulated vault (the one deliberate exception is the `AC-06` failure-induction step below, an in-process monkeypatch of `compass_client.summarize_content`/the shared synthesis helper — this codebase's own established failure-induction technique).

---

## Tests

**Manual verification steps:**

1. **[REQ-SB-67-US-01-AC-03]** Confirm the real, live vault's `Work/Threads/` folder currently contains one or more real, already-captured Thread notes (from before this story shipped — still carrying the old raw-message-dump `## Summary` and no opening line). Record each such note's own current frontmatter, `## Transcript`, `## Attachments` (if present), and `tags` value BEFORE running the backfill. Call `POST /poc/backfill-thread-summaries` against the real running backend. Confirm each of those notes now has a real, Compass-synthesized `## Summary` (grounded in that Thread's own full transcript) and a real opening-line sentence at the top of the body. Re-read the SAME notes' frontmatter/`## Transcript`/`## Attachments`/`tags` AFTER the run and confirm every one of those fields is byte-for-byte IDENTICAL to what was recorded before — only `## Summary` and the opening line changed.
2. **[REQ-SB-67-US-01-AC-04]** Among the real vault's Thread notes, identify (or, if none exists, create via a real single-message live-capture call first) one Thread whose `## Transcript` has exactly one entry. Confirm the backfill produces a real, sensible synthesis grounded in that single message's own content for this note too — not an error, not left empty, not silently falling back to the old raw-dump text.
3. **[REQ-SB-67-US-01-AC-06]** With at least 2 real Thread notes present, induce a real `compass_client.CompassError` via a scoped, disclosed in-process monkeypatch (raise for exactly ONE specific Thread note's own call, real for every other note in the same run — mirrors this codebase's own established "scoped monkeypatch, bound to a real filtered subset" technique, `Implementation/Learnings.md` `SPRINT-018`/`SPRINT-028`). Run the backfill. Confirm: (a) the ONE targeted Thread note's existing `## Summary` and opening line are BYTE-FOR-BYTE unchanged (not blanked, not corrupted) and its own result entry in the returned list has `"status": "summary_error"` with a real, honest `"summary_error"` message; (b) every OTHER Thread note in the same run was still genuinely processed (its own `"status": "regenerated"` entry present, its own Summary/opening line actually changed); (c) the endpoint itself returned a normal `200` with the full `results` list — the run did not abort or raise. Revert the monkeypatch immediately after.
4. Confirm the returned dict's own shape matches the established `/poc/...` convention: `{"notes_checked": <int>, "regenerated": <int>, "results": [...]}`, with `notes_checked == len(results)` and `regenerated` counting only `"status": "regenerated"` entries.
5. Regression check: confirm re-running `POST /poc/backfill-thread-summaries` a second time (idempotent-by-design, since it always fully resynthesizes) does not error and does not touch any note outside `Work/Threads/` — confirm a non-Thread note's own frontmatter/body (e.g. a Customer OKF concept file, a Meeting note) is byte-for-byte unaffected by this endpoint's own run. Confirm none of the six pre-existing `/poc/...` endpoints changed behavior.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-03** (Scenario 3) — the backfill regenerates Summary + opening line for real, already-captured Thread notes, in place; frontmatter/`## Transcript`/`## Attachments`/tags left completely unchanged.
- [x] **AC-04** (Scenario 4, backfill half) — a single-message Thread still produces a sensible summary via the backfill.
- [x] **AC-06** (Scenario 6) — a Compass failure for one Thread during the backfill leaves that Thread untouched, records an honest failure outcome, and the backfill continues processing the rest.
- [x] `POST /poc/backfill-thread-summaries` matches the established six-endpoint `/poc/...` shape exactly.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any lazy/background/scheduled catch-up mechanism for the backfill — resolved by the parent story to a one-shot admin endpoint only.
- `REQ-SB-59`'s future full vault migration/wipe-and-recapture — this backfill is deliberately narrow (Summary + opening line only, in place).
- Reconciling multiple `ConversationID`s into one real Conversation (`REQ-SB-54` point 10).
- Any change to `T01`'s or `T02`'s own primitives/helpers — this task only composes them.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "Real Thread Summary Synthesis + Opening-Line + One-Shot Backfill (`REQ-SB-67`, extends `ADR-043`/`ADR-044`, no new ADR)", the "Backfill module/endpoint" bullet, and the parent story's own two resolved "PRD-flagged open scope questions" (`## Context`) — both the one-shot-endpoint shape and the sequential/no-rate-limit/no-hardcoded-count posture are settled there directly, not open questions for this task. `app/business/tag_backfill.py` is the exact structural precedent — read it directly before writing this task's own module.

---

## Implementation Log

**Coder pass, 2026-08-17.**

- New `src/backend/app/business/thread_summary_backfill.py`:
  `backfill_thread_summaries() -> list[dict]`. Iterates
  `vault_writer.list_all_note_paths()`, filters to
  `frontmatter.get("type") == "Thread"` (mirrors `tag_backfill.py`'s own
  iterate-and-filter shape exactly, no new enumeration primitive). For
  each Thread: reads `existing_summary`/`transcript` via
  `vault_writer.read_body_section`, resolves `prompt_override =
  agent_prompts.get_prompt("thread_match_merge") or
  email_classification._THREAD_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS`,
  and calls `email_classification._synthesize_thread_summary(
  existing_summary, transcript, None, prompt_override)` — the SAME shared
  helper `T02`'s `thread_match_merge` calls, imported directly, no forked
  second implementation. On success: `vault_writer.replace_body_opening_line`
  (`T01`) then `vault_writer.replace_body_section(path, "## Summary", ...)`,
  appends `{"note": str(path), "status": "regenerated"}`. On
  `"summary_error"` in the synthesis result: writes nothing, appends
  `{"note": str(path), "status": "summary_error", "summary_error": str}`,
  loop continues to the next Thread.
- `src/backend/app/api/email_poc_router.py`: added
  `from app.business.thread_summary_backfill import backfill_thread_summaries`
  alongside the existing business-function imports, and
  `POST /poc/backfill-thread-summaries` matching the file's own established
  six-endpoint shape exactly (`{"notes_checked": len(results), "regenerated":
  <count>, "results": results}`). No existing endpoint touched.

**Verification.**

- Import/signature sanity: `python -c "from app.business.thread_summary_backfill
  import backfill_thread_summaries"` succeeds; no circular-import issue.
- **Scratch-vault verification** (`VAULT_PATH`-overridden throwaway
  directory under the session scratchpad, real Compass Provider, never the
  real vault for this half): built 3 controlled scratch Thread notes
  (`thread-a-multi-message.md` — 3-message transcript + an `## Attachments`
  entry, `thread-b-single-message.md` — exactly one Transcript entry,
  `thread-c-will-fail.md` — the AC-06 failure target), plus a non-Thread
  Meeting note and a Customer OKF concept file to prove filter isolation.
  All authoritative verification calls were direct in-process Python calls
  to `backfill_thread_summaries()` (see the "Never spin up a second
  uvicorn..." `MEMORY.md` Constraint below for why an earlier attempt that
  DID spin up a second `uvicorn` instance against this scratch vault was
  abandoned and its stray output cleaned up first).
  - **[AC-03]** PASS. Ran `backfill_thread_summaries()` against the 3
    scratch Threads (fresh raw-dump state, no opening line). All 3
    returned `"status": "regenerated"`. `thread-a`'s frontmatter
    (`vault_writer.read_note`), `## Transcript`, and `## Attachments`
    region were confirmed byte-for-byte identical before/after; its body
    text as a whole changed (new opening line + new synthesized Summary
    present). Opening line confirmed present as the body's own first
    paragraph, distinct from `## Summary`'s own content.
  - **[AC-04]** PASS. `thread-b` (exactly one Transcript entry, no prior
    Summary) produced a real, non-empty (>20 char), genuinely synthesized
    Summary grounded in that one message's own content — not an error, not
    empty, not the old raw-dump text.
  - **[AC-06]** PASS. Reset all 3 scratch Threads to their pristine
    pre-backfill state, then ran `backfill_thread_summaries()` with a
    scoped, `finally`-reverted monkeypatch of `compass_client.
    summarize_content` that raised `CompassError` only when the call's own
    `content` argument contained `thread-c`'s own sender address
    (`dave@gamma.example`) — real Compass calls for every other Thread in
    the same run. Result: `thread-a`/`thread-b` both `"status":
    "regenerated"` with genuinely new, real synthesized content (confirmed
    changed vs. their pre-run byte content); `thread-c`'s own result entry
    was `{"status": "summary_error", "summary_error": "Thread summary
    synthesis failed: Induced failure for AC-06 verification (thread-c
    only)"}`, and `thread-c`'s file on disk was confirmed byte-for-byte
    IDENTICAL to its pre-run content (Summary/opening-line untouched, not
    blanked/corrupted). The run returned its full 3-item `results` list
    without aborting or raising.
  - **Endpoint shape**: confirmed via a `POST /poc/backfill-thread-summaries`
    call against the scratch vault — `{"notes_checked": <int>, "regenerated":
    <int>, "results": [...]}` with `notes_checked == len(results)` and
    `regenerated` counting only `"status": "regenerated"` entries.
  - **Regression**: a Meeting note and a Customer OKF concept file's own
    frontmatter+body were confirmed byte-for-byte unaffected by the same
    backfill runs (never enumerated as Thread notes, since neither has
    `type == "Thread"`). None of the six pre-existing `/poc/...` endpoints
    were touched by this task's diff.
- **Real, live one-time run** (the operator's actual ask tonight —
  "backfill existing Threads, not just fix things going forward"):
  recorded the real vault's 2 real Thread notes' full frontmatter/body
  content BEFORE the run
  (`Work/Threads/01D26A7530444A23803A002210620160.md` — Presight,
  raw-dump Summary, no opening line; `Work/Threads/
  0C41DC9411479C4BAC82EBDDDCA753E7.md` — Core42, same shape); confirmed
  the third file in that folder, `test-librarian-t01-scratch-thread.md`,
  has no `type` frontmatter key at all (not a Thread, correctly excluded).
  Called `POST http://127.0.0.1:8001/poc/backfill-thread-summaries`
  against the already-running real backend (confirmed via `/openapi.json`
  that it was serving this task's own freshly-added route before calling
  it). Response: `{"notes_checked": 2, "regenerated": 2, "results": [...]}`
  — both real Threads `"status": "regenerated"`. Re-read both notes after:
  each now has a real, Compass-synthesized `## Summary` grounded in that
  Thread's own real transcript/prior content, plus a real opening-line
  sentence; each note's frontmatter (`type`, `conversation_id`, `tags`,
  `customer`, `participants`, `last_message_at`) and `## Transcript`
  confirmed byte-for-byte identical to the pre-run recording; neither note
  had an `## Attachments` section before or after (absent both times).
  `test-librarian-t01-scratch-thread.md` confirmed unchanged.

- **Assumption (scope-internal judgement call, logged per Pipeline.md hard
  rule 5, not an escalation):** used a throwaway `VAULT_PATH`-overridden
  scratch vault for the AC-03/AC-04/AC-06 controlled-condition checks
  (byte-for-byte diffing, the deliberate AC-06 failure induction) and
  reserved the real, live `VAULT_PATH` vault specifically for the
  operator's own one-time real backfill request and its own before/after
  spot-check — mirrors `T01`/`T02`'s own identical reconciliation
  (`Implementation/Tasks/REQ-SB-67-US-01-T02-real-thread-summary-synthesis.md`'s
  own Implementation Log) of the parent story's "real vault, not mocked"
  Dependency language as constraining the Compass response and the write
  mechanism, not the specific directory. Logged for human spot-check.
- **Real operational finding (not an escalation, logged for the record —
  see the new `MEMORY.md` Constraint):** an earlier verification attempt
  started a second `uvicorn app.main:app` instance pointed at the scratch
  `VAULT_PATH` to test the endpoint over real HTTP. That instance's own
  `lifespan` unconditionally started `capture_scheduler`'s background
  tick, which polled the REAL configured Outlook mailbox on a timer and
  wrote several real captured conversations into the scratch vault in the
  background (unrelated real Compass calls, real Customer-hub notes)
  while left running. Caught and stopped (process killed) once noticed;
  the stray scratch-vault files were deleted before the controlled AC
  checks above were (re-)run; the real, already-running production
  backend and the real vault were never touched by this side effect
  (confirmed via file `LastWriteTime` predating this task's own
  scratch-server start). All subsequent scratch-vault verification used
  direct in-process function calls instead (no second `uvicorn`
  instance), documented as a new `MEMORY.md` Constraint so this isn't
  repeated.

- **`MEMORY.md` updated** — new `## Decisions` entry (this task's own
  composition approach); new `## Patterns` entry ("one-shot maintenance
  operation reuses a live-capture-path synthesis helper with the delta
  parameter set to `None`"); new `## Constraints` entry (never start a
  second `uvicorn app.main:app` against a scratch `VAULT_PATH` — the
  scheduler polls the real Outlook mailbox regardless of `VAULT_PATH`).
- **`CHANGELOG.md` updated** — new entry for `REQ-SB-67-US-01-T03`/`SPRINT-054`.

- `gate: clear 2026-08-17` — no MUST-FLAG trigger fired: no new
  dependency, no shared-interface change beyond this task's own `## Files
  to Modify` (`T01`/`T02`'s primitives, `tag_backfill.py`'s shape, and the
  six existing `/poc/...` endpoints all composed as-is, untouched), no ADR
  deviation, no unanticipated file, no unclear/contradictory requirement —
  the one scope-internal judgement call above (scratch vault for
  controlled checks vs. the real vault for the operator's own one-time
  request) mirrors `T01`/`T02`'s own identical, already-logged
  reconciliation, not a fresh guess. No `REVIEW-QUEUE.md`/`ESCALATIONS.md`
  entry written by this task.

- **Story/Sprint status:** all three of `REQ-SB-67-US-01`'s tasks are now
  `Done`, every locked AC (`AC-01` through `AC-06`) verified across `T02`/
  `T03` — story `REQ-SB-67-US-01` set to `status: Done`. `SPRINT-054`
  (its only story) set to `status: Done`, `completed: 2026-08-17`, with a
  drafted `## Retrospective` (gate: flagged for human harvest into
  `Implementation/Learnings.md`, per this project's own standing
  convention). `BACKLOG.md`'s `REQ-SB-67` row and Sprint Status table
  updated to `Done`.
