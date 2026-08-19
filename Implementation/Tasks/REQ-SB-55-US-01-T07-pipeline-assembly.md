---
id: REQ-SB-55-US-01-T07
title: Pipeline assembly — new app/business/pipelines/email_capture_pipeline.py, StateGraph wiring all 6 Jobs, Fetch pre-graph batch loop
parent_story: REQ-SB-55-US-01
requirement_id: REQ-SB-55
type: backend
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-043 created) — carried from the parent story; the human reviews ADR-043 alongside this task breakdown. No decomposer-owned trigger fired on this task itself."
phase: P1
depends_on: [REQ-SB-55-US-01-T03, REQ-SB-55-US-01-T04, REQ-SB-55-US-01-T05, REQ-SB-55-US-01-T06]
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-55-US-01-T07 — Pipeline assembly

## Parent Story

- Story: [[REQ-SB-55-US-01]] — `../UserStories/REQ-SB-55-US-01-email-capture-and-threading-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-55 *Email Capture & Threading Pipeline*

---

## Objective

Create `app/business/pipelines/email_capture_pipeline.py` (this codebase's first Pipeline-DAG-assembly module, `ADR-043` point 1) — a code-defined `langgraph.graph.StateGraph` wiring `Classify` → `Thread-Match/Merge` → (conditionally) `Route-to-Project`, plus the two branch Jobs `Summarize-Attachment` (fans out per attachment, fans back into `Thread-Match/Merge`'s own input) and `Detect-Recurring-Pattern` (independent, self-terminating) — compiled once, invoked ONCE PER FETCHED EMAIL from a pre-graph, per-tick `Fetch` batch loop reusing `outlook_com.list_recent_mail` unchanged. Public entry point: `run_email_capture_pipeline(limit: int = 10) -> list[dict]`.

---

## Starting State → End State

**Before / Inputs:**
- `T02`'s `classify_captured_email`, `T03`'s `thread_match_merge`, `T04`'s `route_to_project`, `T05`'s `summarize_attachment`, `T06`'s `detect_recurring_pattern` — five plain, LangGraph-ignorant functions in `email_classification.py`, each independently callable/testable, each taking/returning ordinary Python data.
- `outlook_com.list_recent_mail(limit, unread_only)`, `vault_writer.load_processed_email_ids()`/`mark_email_processed(entry_id)` — the real Fetch/dedup mechanism `classify_recent_emails` already uses today, unchanged.
- `app/business/agent_orchestration/graph.py` is this codebase's only existing real `StateGraph` precedent (a chat/tool-calling graph, a different shape) — read for the project's own general LangGraph conventions (node functions taking/returning a state dict, `add_conditional_edges`, `END`), not as a literal template (that graph's own domain is conversation turns, not a per-email fork/merge DAG).
- `app/business/pipelines/` does not exist yet.

**After / Outputs:**
- `app/business/pipelines/__init__.py` (empty, mirrors `agent_orchestration/__init__.py`/`cockpit/__init__.py`'s own subpackage convention).
- `app/business/pipelines/email_capture_pipeline.py`:
  - A typed pipeline state (e.g. a `TypedDict`) threading: the fetched `email` dict, the `classification` result, the `thread_result` (`Thread-Match/Merge`'s own return dict), a list of attachment `summarize_attachment` results, and the `detect_recurring_pattern` result.
  - Node wrappers around each of the five imported plain functions (`classify`, `thread_match_merge`, `route_to_project`, `summarize_attachment`, `detect_recurring_pattern`) — each reads its own inputs off the state dict, calls the real plain function, returns a partial state update. NEVER imports `outlook_com`/`compass_client` directly in this module — every node composes ONLY the plain functions in `email_classification.py`.
  - Graph topology (`ADR-043` point 3): `classify` is the fork point — unconditionally routes toward `thread_match_merge`; when the email has one or more real attachments, first fans out to `summarize_attachment` (once per attachment) and fans the results back INTO `thread_match_merge`'s own `attachment_entries` input (so the `## Attachments` region and the regenerated `## Summary` land in the SAME pass); independently and in parallel, when `classification["recurring_candidate"]` is true, routes to `detect_recurring_pattern`, which terminates on its own (never feeds into `thread_match_merge`). `thread_match_merge` conditionally routes to `route_to_project` ONLY when its own return value's `created` is `True` (a brand-new Thread) — an update to an already-existing Thread routes straight to the graph's end for this item (the concrete mechanism behind `AC-04`).
  - `run_email_capture_pipeline(limit: int = 10) -> list[dict]` — the public entry point: fetches emails via `outlook_com.list_recent_mail(limit=limit)`, skips already-processed ids (`load_processed_email_ids()`), and for each new email, invokes the compiled graph once, then calls `mark_email_processed`. Mirrors `classify_recent_emails`'s own existing per-email loop shape and per-item result-collection contract (a list of per-email result dicts) — this function is what `T08` wires `run_capture_for_agent`'s new agent_id branch to call.

---

## Files to Modify

- `src/backend/app/business/pipelines/__init__.py` — new, empty.
- `src/backend/app/business/pipelines/email_capture_pipeline.py` — new.

---

## Constraints

- Inherits from parent story: **no persisted queue/staging between `Fetch` and the rest of the graph, and no cross-email graph state** — the compiled `StateGraph` runs once per email, fresh, with no state carried over from the previous email's own run.
- **Never imports `outlook_com`/`compass_client` directly** in this module — every node composes a plain function already living in `email_classification.py` (`ADR-043` point 1). `outlook_com.list_recent_mail` is called ONLY from `run_email_capture_pipeline`'s own pre-graph Fetch loop, never from inside a graph node.
- Mid-pipeline human approval (`route_to_project`/`detect_recurring_pattern`) is NEVER a LangGraph `interrupt()`/checkpointer suspension — both branches run to a clean, ordinary completion on every invocation (they create their own Pending Approval internally and return; the graph run for that item simply ends). Do not introduce `MemorySaver`/`SqliteSaver` or any checkpointer.
- `thread_match_merge` must be invoked with the fully resolved `attachment_entries` list (i.e. AFTER the `summarize_attachment` fan-out branch has completed, when the email has attachments) — never invoked with a partial/incomplete attachment-summary set for an email that has attachments still pending.
- `route_to_project` is invoked ONLY when `thread_match_merge`'s own returned `created` is `True` — this is the graph's own conditional-edge mechanism satisfying `AC-04`; do not rely solely on `route_to_project`'s own internal defensive no-op (`T04`) as the primary gate.
- A per-email failure (e.g. a `CompassError` from `classify`) must not crash the whole tick's own loop over every other email — mirrors `classify_recent_emails`'s own existing per-email `try/except`+continue+honest-error-result posture; apply the same discipline at the `run_email_capture_pipeline` loop level (per email), not necessarily inside the graph itself.
- The compiled graph must be built/compiled ONCE at module load (or lazily, memoized) — not recompiled on every call, mirroring `graph.py`'s own existing `_GRAPH` module-level-singleton convention.
- Do not modify `email_classification.py`'s existing `classify_recent_emails`/`run_capture_for_agent`/`run_capture_and_record_completion` — those are `T08`'s own scope.

---

## Tests

**Manual verification steps:**
1. Confirm the compiled graph's own node set (e.g. `_GRAPH.get_graph().nodes`) includes `classify`, `thread_match_merge`, `route_to_project`, `summarize_attachment`, `detect_recurring_pattern` (naming may vary — confirm all 5 Job functions are represented as real graph nodes), plus `__start__`/`__end__`.
2. **[REQ-SB-55-US-01-AC-01]** Against a throwaway scratch vault, with real Outlook COM monkeypatched (or a real, disposable test mailbox conversation) to return two messages sharing one `conversation_id`, call `run_email_capture_pipeline(limit=10)` twice in sequence (simulating two ticks, one per message becoming "new" between ticks — or, if both are fetched in one tick, confirm the SAME within-tick ordering still produces one Thread, not two). Confirm exactly ONE Thread note results, with `## Summary` regenerated after the second message and `## Transcript` containing both.
3. **[REQ-SB-55-US-01-AC-04]** Using the same two-message conversation as above: confirm EXACTLY ONE Pending Approval with `action_id="route_thread_to_project"` exists after both messages have been processed (created only after the FIRST message; the second message's own graph run never reaches `route_to_project` at all — confirm this directly, e.g. via a call-count check on `route_to_project` across the two invocations, not just the end-state approval count).
4. Confirm a real attachment on a captured email results in `summarize_attachment` completing BEFORE `thread_match_merge` runs for that same email (e.g. via ordering/timing evidence, or by confirming `thread_match_merge`'s own `attachment_entries` argument is non-empty and correctly populated on that call) — the fan-in behaves as designed.
5. Confirm a `classify`-stage failure for ONE synthetic email (a real, scoped, reverted monkeypatch of `compass_client.classify_email` raising `CompassError` for one call only) does not prevent `run_email_capture_pipeline` from still processing the REMAINING fetched emails in the same tick — an honest per-item error result for the failed one, real results for the others.
6. Confirm `run_email_capture_pipeline`'s own dedup behavior: a rerun with the same already-processed email ids produces zero new Thread notes/approvals (mirrors `classify_recent_emails`'s own existing "already processed, skip" contract).
7. Regression check: confirm `outlook_com.py`/`compass_client.py`'s own pre-existing functions this module composes are called with unmodified signatures (no divergent parameter shape introduced), and confirm this new module is never imported by `outlook_com.py`/`compass_client.py` themselves (one-directional composition, no import cycle).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** (Scenario 1, full pipeline integration) — the compiled graph correctly produces one Thread note across two messages in the same conversation.
- [x] **AC-04** (Scenario 4, the primary mechanism) — the conditional edge ensures `route_to_project` fires only on a brand-new Thread, never on a later message in an already-routed conversation.
- [x] Fan-in ordering: `summarize_attachment`'s output is available to `thread_match_merge` before it runs, when attachments exist.
- [x] No LangGraph checkpointer/`interrupt()` introduced; no cross-email graph state; `Fetch` stays outside the compiled graph.
- [x] A single email's own classification failure does not abort the whole tick's processing of other emails.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring `run_email_capture_pipeline` into `run_capture_for_agent`/the real agent identity/the scheduler — `T08`'s own job.
- Any change to the five composed Job functions' own internal logic — this task only wires them together; a defect found in one belongs to that Job's own task.
- A real, live Outlook-backed end-to-end run against the actual configured mailbox (`AC-09`) — `T08`'s own final integration verification, once the new agent identity is also wired in.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/ADR.md` → `ADR-043` points 1, 2, 3, 4 (Alternatives Considered also explains why a LangGraph checkpointer was rejected for this Pipeline specifically); `Implementation/Architecture/architecture.md` → "Email Capture & Threading Pipeline — First Concrete Pipeline". This is this codebase's FIRST genuine fork/merge/conditional-branch DAG — `agent_orchestration/graph.py` is a useful reference for this project's own general LangGraph idioms (node-function shape, `add_conditional_edges`, `END`), but its own domain (a linear-ish conversation loop with tool-call interception) is not a literal template for this task's genuinely different fork/merge topology — consult LangGraph's own documentation for fan-out/fan-in conditional-edge patterns as needed.

**Why this is its own task, not folded into `T03`/`T04`:** the graph assembly is the one place all 5 Job functions' own contracts must agree with each other (return shapes, `created`/`recurring_candidate` flags) — building it last, after every Job function is real and independently tested, avoids reconciling a half-built graph against Job functions that are still changing shape.

---

## Implementation Log

**Built:** `src/backend/app/business/pipelines/__init__.py` (new, empty,
mirrors `agent_orchestration/__init__.py`/`cockpit/__init__.py`) and
`src/backend/app/business/pipelines/email_capture_pipeline.py` (new) —
the only two files touched, matching `## Files to Modify` exactly.

`EmailCapturePipelineState` (`TypedDict`, mirrors `AgentConversationState`'s
own plain-`TypedDict` shape, no `Annotated` reducers needed — every node
writes its own distinct key, no list-append-merge semantics required):
`email`, `known_customers`, `known_kinds`, `classification`,
`attachment_entries`, `thread_result`, `route_to_project_result`,
`recurring_pattern_result`. Five thin node wrappers
(`_classify_node`, `_summarize_attachment_node`,
`_thread_match_merge_node`, `_route_to_project_node`,
`_detect_recurring_pattern_node`) each call exactly one imported plain
Job function and return a partial state update — no business logic
duplicated into any node body.

**Topology, exactly as built:** `classify` (entry) → conditional edges
(`_route_after_classify`, returns a `list[str]`) → always
`["summarize_attachment"]`, plus `"detect_recurring_pattern"` appended
when `classification["recurring_candidate"]` is true. `summarize_attachment`
is a MANDATORY pass-through node (runs for every email; loops 0-or-more
times over `email["attachments"]`, calling the real per-attachment plain
`summarize_attachment` Job each time, collecting only entries with a real
`dated_entry`) with one FIXED (non-conditional) outgoing edge straight to
`thread_match_merge` — this is what structurally guarantees the fan-in
ordering constraint (`thread_match_merge` is never reachable in the same
LangGraph superstep as `summarize_attachment`, so it always sees the
fully resolved `attachment_entries` list, confirmed live below).
`detect_recurring_pattern` has one fixed outgoing edge straight to `END`
— it never feeds back into `thread_match_merge`. `thread_match_merge` →
conditional edges (`_route_after_thread_match_merge`) → `"route_to_project"`
when `thread_result["created"]` is `True`, else `END` directly — the
concrete mechanism satisfying AC-04. `route_to_project` → `END`. Compiled
once at module load (`_GRAPH = _build_graph()`), mirroring `graph.py`'s
own `_GRAPH` singleton convention — never recompiled per call. No
`MemorySaver`/`SqliteSaver`/checkpointer anywhere in `.compile()` or
elsewhere in this module; `route_to_project`/`detect_recurring_pattern`
each run their own branch to a clean, ordinary completion on every
invocation (no `interrupt()`).

`run_email_capture_pipeline(limit=10) -> list[dict]`: fetches via
`outlook_com.list_recent_mail(limit=limit)` (unmodified signature),
skips ids already in `vault_writer.load_processed_email_ids()`, invokes
the compiled graph once per new email (`_GRAPH.invoke(initial_state)`,
sync — no async node anywhere in this graph, unlike `agent_orchestration/
graph.py`), then `vault_writer.mark_email_processed(email["id"])` only
on a successful run. A per-email failure is caught at THIS loop level
(`except Exception`, honest per-item error result appended, `continue`)
— never inside the graph itself, per this task's own Constraint; a
failed email is left unmarked so a future run retries it, mirroring
`classify_recent_emails`' own existing posture.

**Scope-internal judgement call, logged for human spot-check (not an
escalation):** the task file's own Constraints bullet reads "Never
imports `outlook_com`/`compass_client` directly in this module" in one
sentence, then in the very next sentence states `outlook_com.
list_recent_mail` is called "ONLY from `run_email_capture_pipeline`'s
own pre-graph Fetch loop" — which necessarily requires importing
`outlook_com` somewhere in this same file. Read together with the
Objective/End-State section's own explicit, unambiguous text ("`run_
email_capture_pipeline`... fetches emails via `outlook_com.
list_recent_mail(limit=limit)`") and `ADR-043` point 1's own parenthetical
("Fetch reuses `outlook_com.list_recent_mail` unchanged"), the only
buildable reading is: the "never imports directly" rule binds the GRAPH
NODES only (none of the five node wrappers ever call `outlook_com`/
`compass_client`, confirmed by direct inspection above and by the live
per-email-failure test below, which raises `CompassError` from inside a
graph-invoked node path and confirms it propagates OUT of `_GRAPH.
invoke()` rather than being caught inside any node) — `run_email_capture_
pipeline` itself, the pre-graph Fetch step, imports and calls `outlook_com.
list_recent_mail`/`vault_writer.load_processed_email_ids`/`vault_writer.
mark_email_processed` directly, exactly as the End-State section
specifies. `compass_client` itself is never imported into this module at
all (not needed — the per-email `except Exception` at the loop level
catches any Job's own failure, including a `CompassError` from either
`classify_captured_email` or `route_to_project`, without needing the
exception class imported by name).

**Verified live (manual mode), all real components except `outlook_com.
list_recent_mail` (a real, disposable scratch vault, `settings.vault_path`
reassigned to a session-scratchpad directory, never the real configured
vault; real Compass Provider for every classify/route/summarize call; no
mocking of any Job's own real logic):**

1. `_GRAPH.get_graph().nodes` confirmed to contain exactly `classify`,
   `summarize_attachment`, `thread_match_merge`, `route_to_project`,
   `detect_recurring_pattern`, plus `__start__`/`__end__` — all 5 Job
   functions present as real graph nodes.
2. **AC-01** — two real messages sharing one `conversation_id` (Zenith
   Manufacturing kickoff + a follow-up naming a real SOW reference
   `ZX-2201`), fetched across two separate `run_email_capture_pipeline`
   ticks (msg1 present only in tick 1; msg1+msg2 present in tick 2,
   msg1 already processed and correctly skipped) via a monkeypatched
   `outlook_com.list_recent_mail`. Confirmed exactly ONE `.md` file under
   `Work/Threads/` on disk; `## Transcript` grew to 2 lines in call order;
   `## Summary` was regenerated from scratch after the second message
   (contains `ZX-2201`, the SECOND message's own real content) with ZERO
   residue of the first message's own "Looking forward to working
   together" wording — confirmed by directly asserting that exact string
   is absent from the `## Summary` region's own text. **PASS.**
3. **AC-04** — using the same two-message conversation: exactly ONE
   `route_thread_to_project` Pending Approval existed after both ticks
   (`pending_approval_registry.list_pending_approvals()` filtered by
   `action_id`); a real call-count spy wrapped around the REAL
   `route_to_project` function (not a mock — it still executes its real
   body) confirmed it was invoked exactly ONCE total across both graph
   invocations — the second message's own graph run never reached
   `route_to_project` at all, confirmed directly via the call-count
   assertion (`== 1`), not just the end-state approval count. **PASS.**
4. **Fan-in ordering** — a real `.txt` attachment (`status-note.txt`,
   real bytes) on a captured email: instrumented wrappers around the
   real `summarize_attachment`/`thread_match_merge` functions (both still
   executing their real bodies) confirmed the exact call order
   (`summarize_attachment` first, `thread_match_merge` second) AND that
   `thread_match_merge` received a resolved `attachment_entries` list of
   length 1 (not 0, not partial) on that same call. The resulting Thread
   note's `## Attachments` region contains the real `status-note.txt`
   dated sub-entry, kept structurally separate from `## Summary`.
   **PASS.**
5. **Per-email failure isolation** — a real, scoped, `finally`-reverted
   monkeypatch of `compass_client.classify_email` raised a real
   `CompassError` for exactly one of two fetched emails in the same tick
   (matched by sender). `run_email_capture_pipeline` returned exactly 2
   results: 1 honest `{"subject", "error"}` entry for the failed email,
   1 real, successful result (real Thread note created, real Compass
   classification) for the other. The failed email's own `entry_id` was
   confirmed absent from `load_processed_email_ids()` afterward (retry-
   eligible on a future run); the successful one was confirmed present.
   A follow-up real (unmocked) `compass_client.classify_email` call after
   the `finally` revert succeeded normally, confirming the monkeypatch
   was genuinely reverted, not left dangling. **PASS.**
6. **Dedup rerun** — re-fetching a set of already-processed ids (via a
   third monkeypatched `outlook_com.list_recent_mail` call) produced an
   empty results list, and a before/after count of both
   `list_pending_approvals()` and `Work/Threads/*.md` confirmed ZERO new
   records/files were created. **PASS.**
7. **Regression / no-import-cycle check** — direct source inspection: no
   file under `app/data_access/` (`outlook_com.py`, `compass_client.py`)
   imports anything from `app/business/pipelines/` (confirmed via
   `Grep` for `email_capture_pipeline`/`pipelines` in both files — zero
   matches); `outlook_com.list_recent_mail(limit=limit)` and `vault_writer.
   load_processed_email_ids()`/`mark_email_processed(entry_id)` are called
   with their exact existing, unmodified signatures throughout every live
   run above — neither file was edited by this task (not in `## Files to
   Modify`). **PASS.**

`ast.parse()` of both new files confirmed clean. No file outside `##
Files to Modify` was edited. No `MemorySaver`/`SqliteSaver`/`interrupt()`
introduced anywhere — confirmed by direct source inspection of the final
`email_capture_pipeline.py`. All 5 substantive locked ACs/bullets
verified live with a real, observed outcome; no `ESCALATIONS.md`/
`REVIEW-QUEUE.md` entries needed from this task's own pass (the task's
own `gate: flagged` inherited from the parent story's `ADR-043` review
stays open as a standing breadcrumb, not resolved or reopened by this
pass).
