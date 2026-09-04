---
id: BUGFIX-05-US-01-T01
title: Rewire run_email_capture_pipeline to compose capture_raw_thread_messages + synthesize_thread instead of the old StateGraph/thread_match_merge
parent_story: BUGFIX-05-US-01
requirement_id: BUG-026
type: backend
status: Done
gate: clear
gate_reason: ""
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-05-US-01-T01 — Rewire run_email_capture_pipeline to compose capture_raw_thread_messages + synthesize_thread instead of the old StateGraph/thread_match_merge

## Parent Story

- Story: [[BUGFIX-05-US-01]] — `../UserStories/BUGFIX-05-US-01-email-thread-processing-retires-legacy-thread-match-merge.md`
- Requirement: `BUGS.md` → `BUG-026` (bugfix story; no PRD requirement anchor)

---

## Objective

Retarget `process_staged_email`'s own underlying implementation
(`email_capture_pipeline.run_email_capture_pipeline`, same name/module/
zero-argument call shape — `skill_tools.py` itself needs no change) off
the old compiled `StateGraph`/`thread_match_merge` path onto a plain,
sequential composition of Stage 1 (`capture_raw_thread_messages`) + Stage
2 (`synthesize_thread`), explicitly re-composing the three old-graph side
effects that have no equivalent elsewhere (`detect_recurring_pattern`,
`consult_librarian`, `resync_project_from_thread`) as plain calls — per
`ADR-051` and `architecture.md`'s "`process_staged_email` Retargeted onto
Stage 1/Stage 2 Composition" section. This closes `AC-02` (the orphaning
facet) by construction. It does **not**, by itself, close `AC-01` (the
flat-shape duplication facet) — that AC is currently `locked: false`,
pending a separate architecture decision; see the story's own `## Notes`
and `ESCALATIONS.md` → `ESC-055`. Do not attempt to fix `AC-01` in this
task — out of scope (see `## Out of Scope`).

---

## Starting State → End State

**Before / Inputs:**
- `app/business/pipelines/email_capture_pipeline.py::run_email_capture_
  pipeline()` (lines ~295-371) reads every staged item from `email_
  staging.list_staged_emails()` and invokes the module's compiled
  `StateGraph` (`_GRAPH.invoke(...)`) once per email — its second fork
  point, `thread_match_merge`, is `BUG-026`'s own named legacy mechanism.
- `app/business/pipelines/raw_message_capture.py::capture_raw_thread_
  messages(limit)` (Stage 1, already `Done`, `REQ-SB-71-US-02`) already
  drains every staged email into a raw message note per Thread; its
  return dict is `{"pulled", "processed", "skipped_already_noted"}` — no
  way for a caller to know WHICH `conversation_id`s received a new
  message this run.
- `app/business/email_classification.py::synthesize_thread(conversation_
  id)` (Stage 2, already `Done`, `REQ-SB-71-US-02`) already performs
  create-vs-update, `## Summary` regeneration, and `route_to_project`'s
  own trigger — unchanged by this task.
- `app/business/skill_tools.py::process_staged_email` (lines ~352-398)
  calls `run_email_capture_pipeline()` and reports `"N email(s) filed"` —
  wording that assumed one result row per email; the retargeted function
  returns one row per synthesized Thread instead (`ADR-051` Decision 5).

**After / Outputs:**
- `capture_raw_thread_messages`'s return dict gains ONE additive key,
  `conversation_ids_touched: list[str]` — the distinct `conversation_id`s
  of every item appended to `processed` this run (never `skipped_already_
  noted`). Every existing key (`pulled`, `processed`, `skipped_already_
  noted`) is untouched — a pure superset; `/poc/capture-raw-thread-
  messages`'s existing response shape is unaffected for any existing
  consumer.
- `run_email_capture_pipeline()` no longer builds or invokes the
  `StateGraph` — it composes Stage 1 + Stage 2 + the three re-composed
  side effects directly, returning one row per synthesized Thread.
- `_build_graph()`, `_GRAPH`, `get_job_tree()`, and every graph NODE
  function (`_classify_node`, `_summarize_attachment_node`, `_thread_
  match_merge_node`, `_route_to_project_node`, `_detect_recurring_
  pattern_node`, `_consult_librarian_node`, `_trigger_project_synthesis_
  node`) remain byte-for-byte unchanged — deprecated (no longer on any
  live execution path), not deleted, per `ADR-051` Decision 6 (kept
  because `get_job_tree()`, `REQ-SB-65-US-01`, still reads the same
  compiled `_GRAPH`).
- `skill_tools.process_staged_email`'s success-message wording reflects
  per-Thread granularity ("N thread(s) updated"); its own signature and
  deferred-import call site are untouched.

---

## Files to Modify

- `src/backend/app/business/pipelines/raw_message_capture.py`:
  1. Replace `capture_raw_thread_messages`'s exact body (keep the
     function's own docstring's first two paragraphs; update its
     "Returns" paragraph to name the new key) with:

     ```python
     def capture_raw_thread_messages(limit: int = 10) -> dict:
         """Stage 1 -- real Outlook-COM fetch (via `pull_and_stage_emails`),
         then drains every currently-staged, not-yet-message-noted email into
         its own immutable raw message note, ensuring each Thread's own
         distilled concept file exists (created empty -- Stage 1 itself never
         writes `## Summary`, per Scenario 1/AC-01). A staged email is removed
         from `email_staging` only AFTER its own raw message note has been
         durably written (never removed first -- avoids losing content on a
         mid-write crash). Every raw message note write is guarded by `raw_
         message_note_exists` first, so a re-run over an overlapping staged
         batch never double-writes the same `message_id` (Scenario 2/AC-02).

         Returns `{"pulled": <pull_and_stage_emails summary dict>, "processed":
         [<message_id>, ...], "skipped_already_noted": [<message_id>, ...],
         "conversation_ids_touched": [<conversation_id>, ...]}` -- the last key
         is additive (`BUGFIX-05-US-01`, `ADR-051`), the distinct
         `conversation_id`s of every item in `processed` this run (never
         `skipped_already_noted` -- if a message's own note already existed,
         nothing NEW happened this tick for that conversation), consumed by
         `run_email_capture_pipeline`'s own Stage-2 composition to know which
         Threads need re-synthesis. An honest per-run summary, never raising
         for an individual staged email's own processing (mirrors this
         codebase's own per-item resilience posture elsewhere)."""
         pull_summary = email_pull.pull_and_stage_emails(limit=limit)

         processed: list[str] = []
         skipped_already_noted: list[str] = []
         conversation_ids_touched: list[str] = []

         for staged_email in email_staging.list_staged_emails():
             message_id = staged_email["id"]
             conversation_id = staged_email["conversation_id"]
             received = staged_email["received"]

             if vault_writer.raw_message_note_exists(conversation_id, message_id, received):
                 skipped_already_noted.append(message_id)
                 email_staging.remove_staged_email(message_id)
                 continue

             vault_writer.create_raw_message_note(
                 conversation_id=conversation_id,
                 message_id=message_id,
                 received=received,
                 sender=staged_email["sender_name"],
                 sender_email=staged_email["sender_email"],
                 subject=staged_email["subject"],
                 body=staged_email["body"],
             )

             # Durable attachment-byte persistence -- see this module's own
             # docstring. Reuses write_attachments verbatim; a no-op (returns
             # []) when this email carries no real attachments.
             if staged_email.get("attachments"):
                 vault_writer.write_attachments(
                     subfolder="Work/Threads",
                     note_stem=conversation_id,
                     message_segment=message_id,
                     attachments=staged_email["attachments"],
                 )

             # Provisional grouping is ConversationID-only -- this function
             # never performs a merge-vs-new-Thread judgment (Stage 2's own
             # scope); it only ensures a Thread concept file exists somewhere,
             # nothing more.
             if vault_writer.resolve_thread_note_path(conversation_id) is None:
                 vault_writer.create_thread_note_baseline(
                     conversation_id, thread_name=staged_email["subject"]
                 )

             email_staging.remove_staged_email(message_id)
             processed.append(message_id)
             if conversation_id not in conversation_ids_touched:
                 conversation_ids_touched.append(conversation_id)

         return {
             "pulled": pull_summary,
             "processed": processed,
             "skipped_already_noted": skipped_already_noted,
             "conversation_ids_touched": conversation_ids_touched,
         }
     ```

     (Note: this task's own version of `capture_raw_thread_messages`
     carries the same `write_attachments(..., message_segment=message_id)`
     call `BUGFIX-03-US-01-T02` already shipped — verify the real, current
     file before applying this replacement, per this project's own
     established "compose around the REAL current file" Learnings pattern;
     the exact attachment-call shape may already differ slightly from what
     is shown here if a sibling story landed additional changes.)

- `src/backend/app/business/pipelines/email_capture_pipeline.py`:
  1. Rewrite the module's own top-level docstring (lines 1-66) to
     describe the new composed shape — do not describe the composed
     function's own exact internals in the module docstring (that
     belongs on `run_email_capture_pipeline`'s own docstring below);
     the module docstring should instead explain that this module now
     holds BOTH the deprecated-but-kept `StateGraph`/`get_job_tree()`
     machinery (unchanged, for `REQ-SB-65-US-01` only) AND the real, live
     `run_email_capture_pipeline` entry point, which no longer invokes
     that graph. Reference `ADR-051` and `BUGFIX-05-US-01`.
  2. Add one import (`from pathlib import Path`) and extend the existing
     `email_classification` import block to also import `synthesize_
     thread`; add a new import for Stage 1:

     ```python
     from __future__ import annotations

     from pathlib import Path
     from typing import TypedDict

     from langgraph.graph import END, START, StateGraph

     from app.business import project_customer_synthesizer
     from app.business.email_classification import (
         classify_captured_email_with_fallback,
         consult_librarian,
         detect_recurring_pattern,
         route_to_project,
         summarize_attachment,
         synthesize_thread,
         thread_match_merge,
     )
     from app.business.pipelines.raw_message_capture import capture_raw_thread_messages
     from app.data_access import email_staging, vault_writer
     ```

     `route_to_project`, `summarize_attachment`, `thread_match_merge`, and
     every existing name stay imported and used exactly as before, by the
     UNCHANGED node functions below — do not remove any of them even
     though `run_email_capture_pipeline` itself no longer calls them
     directly.
  3. Replace `run_email_capture_pipeline`'s exact signature + body (lines
     ~295-371) — everything ABOVE it (`EmailCapturePipelineState`, every
     `_..._node` function, `_route_after_classify`, `_route_after_thread_
     match_merge`, `_build_graph`, `_GRAPH`, `get_job_tree`) stays
     byte-for-byte unchanged — with:

     ```python
     def run_email_capture_pipeline(limit: int = 10) -> list[dict]:
         """The public entry point (ADR-043 point 1) -- what `email-
         capture-pipeline`'s `process_staged_email` capability calls.
         RETARGETED (`BUGFIX-05-US-01`, `ADR-051`) off the compiled
         `StateGraph` above entirely -- a plain, sequential composing
         function now:

         1. Calls `capture_raw_thread_messages(limit=limit)` once (Stage 1
            -- zero-Compass raw capture, unchanged). Its own additive
            `conversation_ids_touched` key names every conversation_id
            that received at least one genuinely NEW raw message this run.
         2. For each such `conversation_id`, calls `synthesize_thread
            (conversation_id)` (Stage 2) -- which, internally, already
            performs create-vs-update, customer/tags/participants,
            `## Summary` regeneration, the Files/OKF companion writes, and
            `route_to_project`'s own created-only Pending-Approval trigger.
         3. For each such Thread, three of the old graph's other real
            branch effects -- which have NO equivalent anywhere in the
            REQ-SB-71/REQ-SB-72 redesign -- are explicitly, directly
            re-composed as plain calls, never re-implemented (ADR-051
            Decision 3):
            - `detect_recurring_pattern`, for each raw message note under
              this Thread's own `messages/` directory whose `message_id`
              is in Stage 1's own `processed` list this run (a genuinely
              NEW message, not `skipped_already_noted`) -- reads that
              message's own just-written raw note back, reconstructs an
              `email`-shaped dict, classifies it again (`classify_
              captured_email_with_fallback`, a genuine, additional Compass
              call separate from `synthesize_thread`'s own Thread-
              lifetime-scoped classify), and calls `detect_recurring_
              pattern(email, classification)` when `recurring_candidate`
              is true. Wrapped in its own try/except -- never gates the
              enclosing Thread's own already-successful capture/
              synthesis.
            - `consult_librarian(thread_result)`, once per synthesized
              Thread (`synthesized: True`) -- unconditional for both a
              brand-new and an updated Thread alike. Already has its own
              internal broad try/except; no additional wrapping needed
              here.
            - `project_customer_synthesizer.resync_project_from_thread(
              thread_result["thread_path"])`, once per synthesized Thread
              -- unconditional. Wrapped in its own try/except, same
              non-gating reason as the recurring-pattern step.
         4. The whole per-`conversation_id` unit (Stage 2 plus its three
            composed side effects) is ALSO wrapped in one outer
            try/except at the loop level -- a genuinely unexpected
            exception anywhere in that unit is caught, reported as
            `{"conversation_id", "error"}`, and the loop continues to the
            next `conversation_id`; it never aborts the whole tick's
            remaining Threads.

         Returns one row per synthesized Thread this run, not one row per
         fetched email -- a real, disclosed behavior change (ADR-051
         Decision 5); `skill_tools.process_staged_email`'s own
         `"error"`-key-presence convention (`filed = [r for r in results
         if "error" not in r]`) stays compatible as-is.

         NOTE: this composition does NOT close BUGFIX-05-US-01's own
         `AC-01` (a new message for a pre-redesign, FLAT-shape Thread) --
         `synthesize_thread`'s own create-vs-update check is blind to a
         flat, top-level `Work/Threads/<name>.md` note (a separate,
         disclosed gap in `resolve_thread_directory`/`list_thread_notes`,
         see `ESCALATIONS.md` -> `ESC-055`, out of this task's own
         scope)."""
         capture_summary = capture_raw_thread_messages(limit=limit)
         newly_processed_message_ids = set(capture_summary["processed"])
         known_customers = vault_writer.list_known_customers()
         known_kinds = vault_writer.list_known_kinds()
         results: list[dict] = []

         for conversation_id in capture_summary["conversation_ids_touched"]:
             try:
                 thread_result = synthesize_thread(conversation_id)
                 if not thread_result.get("synthesized"):
                     results.append({
                         "conversation_id": conversation_id,
                         "error": thread_result.get("reason", "synthesis_skipped"),
                     })
                     continue

                 messages_dir = Path(thread_result["thread_path"]).parent / "messages"
                 for message_path in messages_dir.glob("*.md"):
                     message_frontmatter, message_body = vault_writer.read_note(message_path)
                     message_id = message_frontmatter.get("message_id", "")
                     if message_id not in newly_processed_message_ids:
                         continue
                     try:
                         email = {
                             "subject": message_frontmatter.get("subject", ""),
                             "sender_name": message_frontmatter.get("sender", ""),
                             "sender_email": message_frontmatter.get("sender_email", ""),
                             "body": message_body.strip(),
                             "conversation_id": conversation_id,
                         }
                         classification = classify_captured_email_with_fallback(
                             email, known_customers, known_kinds,
                         )
                         if classification.get("recurring_candidate"):
                             detect_recurring_pattern(email, classification)
                     except Exception:  # noqa: BLE001 -- never gates this Thread's own already-successful capture/synthesis (ADR-051 Decision 3)
                         pass

                 try:
                     consult_librarian(thread_result)
                 except Exception:  # noqa: BLE001 -- defensive only; consult_librarian already returns an honest {"status": "unavailable", ...} internally
                     pass

                 try:
                     project_customer_synthesizer.resync_project_from_thread(
                         thread_result["thread_path"]
                     )
                 except Exception:  # noqa: BLE001 -- never gates this Thread's own already-successful capture/synthesis (ADR-051 Decision 3)
                     pass

                 results.append({
                     "conversation_id": conversation_id,
                     "customer": thread_result.get("customer"),
                     "thread_path": thread_result.get("thread_path"),
                     "created": thread_result.get("created"),
                     "message_count": thread_result.get("message_count"),
                 })
             except Exception as exc:  # noqa: BLE001 -- honest per-Thread failure funnel (ADR-051 Decision 4); never crashes the whole tick's own loop over the remaining conversation_ids
                 results.append({"conversation_id": conversation_id, "error": str(exc)})

         return results
     ```

- `src/backend/app/business/skill_tools.py`:
  1. In `process_staged_email` (lines ~381-398), replace this exact line:

     ```python
             message = f"Done — {len(filed)} email(s) filed."
     ```

     with:

     ```python
             message = f"Done — {len(filed)} thread(s) updated."
     ```

     No other line in this function changes — `filed`/`failed`'s own
     `"error"`-key-presence filtering stays exactly as-is (ADR-051
     Decision 5 confirms it remains compatible), and the deferred-import
     call site (`from app.business.pipelines.email_capture_pipeline
     import run_email_capture_pipeline`) is untouched.

---

## Constraints

- Inherits from parent story (real, live vault — no fixture; must not
  touch `pull_email`/`email_pull.py`; no-data-loss is load-bearing).
- Must NOT modify `_build_graph()`, `_GRAPH`, `get_job_tree()`,
  `EmailCapturePipelineState`, or any `_..._node`/`_route_after_...`
  function in `email_capture_pipeline.py` — all remain byte-for-byte
  unchanged (deprecated, not deleted, `ADR-051` Decision 6); `get_job_
  tree()` must keep reading the SAME compiled `_GRAPH` singleton.
- Must NOT modify `email_classification.py`, `project_customer_
  synthesizer.py`, or any of their functions — `synthesize_thread`,
  `detect_recurring_pattern`, `consult_librarian`, `classify_captured_
  email_with_fallback`, and `resync_project_from_thread` are all called
  exactly as they already exist, never re-implemented or altered.
- Must NOT change `skill_registry.py`'s `"process_staged_email"` mapping
  or `skill_tools.process_staged_email`'s own signature/deferred-import
  call site — only its internal success-message wording changes.
- `capture_raw_thread_messages`'s return dict must gain ONLY the
  additive `conversation_ids_touched` key — every existing key
  (`pulled`, `processed`, `skipped_already_noted`) stays exactly as-is,
  so `/poc/capture-raw-thread-messages`'s response shape is a pure
  superset for any existing consumer.
- The three composed side effects (`detect_recurring_pattern`
  reclassification+call, `consult_librarian`, `resync_project_from_
  thread`) must never gate or abort the enclosing Thread's own
  already-successful capture/synthesis — each gets its own inner
  try/except (per the code above), PLUS the outer per-`conversation_id`
  try/except for genuinely unexpected failures.
- Do NOT attempt to fix `AC-01` (the flat-shape duplication facet) in
  this task — the underlying `resolve_thread_directory`/`list_thread_
  notes()` gap is a separate, not-yet-decided architecture question
  (`ESCALATIONS.md` → `ESC-055`), out of this task's own `## Files to
  Modify`.

---

## Tests

<!-- No locked AC is verified in this task — AC-02 is verified live in
T02, once this task's rewire is in place. This task carries its own real,
non-AC-tagged regression/smoke checks of the composition itself. AC-01 is
not locked (see the story's own Notes / ESC-055) and has no verification
step anywhere in this story's current task set. -->

**Manual verification steps (not locked-AC-tagged — smoke/regression
checks of this task's own composition, against the real `.venv`,
`.venv\Scripts\python.exe`, cwd `src/backend`):**

1. Import `app.business.pipelines.raw_message_capture` and
   `app.business.pipelines.email_capture_pipeline` cleanly (`python -c
   "import app.business.pipelines.raw_message_capture; import
   app.business.pipelines.email_capture_pipeline"`) — confirms no syntax
   error and no import-cycle regression (this module's own deferred-import
   discipline elsewhere in the codebase is a known, real constraint —
   confirm this task's own new top-level `from app.business.pipelines.
   raw_message_capture import capture_raw_thread_messages` import does
   NOT reintroduce the transitive-cycle `ImportError` `skill_tools.
   process_staged_email`'s own docstring already documents; if it does,
   this is a real, unanticipated finding — escalate rather than silently
   route around it).
2. In a Python shell, call the real, unmodified `capture_raw_thread_
   messages(limit=1)` (or a small limit) against the real, configured
   vault and confirm its returned dict has all four keys — `pulled`,
   `processed`, `skipped_already_noted`, `conversation_ids_touched` — and
   that `conversation_ids_touched` contains exactly the distinct
   `conversation_id`s of every item in `processed` (cross-check by
   reading each processed message's own raw note frontmatter directly),
   never anything from `skipped_already_noted`.
3. Call the real, unmodified `run_email_capture_pipeline()` (or, if no
   staged mail exists at the moment, first run `capture_raw_thread_
   messages`/`pull_email` to genuinely stage at least one new message)
   against the real, configured vault and confirm: (a) it returns a list
   with one row per synthesized `conversation_id`, not one row per email;
   (b) `_GRAPH`/`_build_graph`/`get_job_tree` are never invoked during
   this call (e.g. via a temporary print/log or by confirming `get_job_
   tree()`'s own separately-called output is unaffected/unchanged
   before/after); (c) the resulting Thread note(s) show real, current
   `## Summary` content, confirming Stage 2 genuinely ran.
4. Call `skill_tools.process_staged_email("email-capture-pipeline")`
   directly (Python shell, not the HTTP layer) against a state with at
   least one genuinely new staged message; confirm the returned
   `"message"` string reads `"...thread(s) updated."`, not `"...email(s)
   filed."`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `capture_raw_thread_messages` returns an additive
      `conversation_ids_touched` key (distinct `conversation_id`s from
      newly-`processed` messages only); all existing keys unchanged
- [ ] `run_email_capture_pipeline()` no longer builds/invokes the
      `StateGraph`; composes `capture_raw_thread_messages` (Stage 1) +
      `synthesize_thread` (Stage 2) per touched `conversation_id`
- [ ] `detect_recurring_pattern`, `consult_librarian`, `resync_project_
      from_thread` are each explicitly re-composed as plain calls once
      per synthesized Thread, matching `ADR-051` Decision 3's exact shape
- [ ] `_build_graph()`/`_GRAPH`/`get_job_tree()` and every node function
      remain byte-for-byte unchanged
- [ ] `skill_tools.process_staged_email`'s success-message wording
      reflects per-Thread granularity ("N thread(s) updated"); its
      signature/call site unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Fixing `AC-01` (flat-shape duplication) — the underlying architecture
  decision is now made (`ADR-052`), but the fix itself lives at the
  shared-primitive layer (`vault_writer.resolve_thread_directory`/new
  `migrate_flat_thread_to_directory`) — `T03`, not this task; none of
  `T03`'s files overlap this task's own `## Files to Modify`. See
  `ESCALATIONS.md` → `ESC-055` (now `Resolved`, naming `ADR-052` as the
  resolving artefact).
- Retiring/deleting `thread_match_merge`'s function body, `_build_
  graph()`, `_GRAPH`, or `get_job_tree()` — deprecated, not deleted
  (`ADR-051` Decision 6).
- Rebuilding `get_job_tree()`'s Pipeline Job Tree visualization against
  the new composed shape — a disclosed, future follow-up (`ADR-051`
  Consequences).
- Any change to `pull_email`/`email_pull.py`.
- Live AC verification and the working-mode flip — `T02` (`AC-02`) and
  `T04` (`AC-01` and the flip itself, once `T01`/`T02`/`T03` are all
  `Done`).

---

## Context / Notes

Full architectural reasoning: `Implementation/Architecture/ADR.md` →
`ADR-051`; `Implementation/Architecture/architecture.md` → "`process_
staged_email` Retargeted onto Stage 1/Stage 2 Composition". The story's
own `## Notes` and `ESCALATIONS.md` → `ESC-055` explain why `AC-01` is not
in this task's own scope, and why `email-capture-pipeline`'s working mode
stays `supervised` (not flipped by this task or `T02`).

---

## Implementation Log

**2026-08-19, coder.** Implemented as specced against the real, current
`src/backend/app/business/pipelines/raw_message_capture.py`,
`email_capture_pipeline.py`, `skill_tools.py`: `capture_raw_thread_
messages` gained the additive `conversation_ids_touched` key (all 3
existing keys untouched); `run_email_capture_pipeline`'s body replaced
with the plain Stage-1+Stage-2 composition plus the three re-composed
side effects (`detect_recurring_pattern`, `consult_librarian`,
`resync_project_from_thread`), each with its own try/except plus the
outer per-`conversation_id` try/except, exactly matching the spec's own
code block; `_build_graph`/`_GRAPH`/`get_job_tree`/every `_..._node`
function left byte-for-byte unchanged (confirmed by diff review — only
the module docstring, the import block, and `run_email_capture_pipeline`'s
own body were touched); `skill_tools.process_staged_email`'s message
wording updated to "N thread(s) updated."

**No locked AC in this task** (AC-02 is verified live in T02). All 4
manual smoke/regression steps run against the real, live configured vault
(`VAULT_PATH = <OPERATOR_VAULT_OLD>`), `.venv\Scripts\python.exe`,
cwd `src/backend`:

1. `python -c "import app.business.pipelines.raw_message_capture; import
   app.business.pipelines.email_capture_pipeline"` — clean import, no
   syntax error. PASS. Also directly re-checked the ALREADY-DOCUMENTED
   transitive-cycle constraint (`skill_tools.process_staged_email`'s own
   docstring): confirmed, by direct testing, that `import app.business.
   skill_tools` as the FIRST module imported in a fresh process still
   hits the SAME pre-existing cycle (`skill_tools` → `email_classification`
   → `vault_filing_expert` → `agent_orchestration` → ... → `knowledge_
   bootstrap` → `skill_registry` → `skill_tools`) — this cycle occurs
   entirely WITHOUT ever reaching `email_capture_pipeline.py` (confirmed
   by reading the traceback: it fails before `email_capture_pipeline`
   would even be imported), proving this task's own new top-level import
   (`from app.business.pipelines.raw_message_capture import capture_raw_
   thread_messages` in `email_capture_pipeline.py`) does NOT reintroduce
   or worsen it — it is the exact same pre-existing constraint the
   deferred-import discipline inside `process_staged_email` already
   exists to route around. Confirmed the real production import order
   (`import app.main` first, matching real `uvicorn` startup) avoids the
   cycle entirely and `process_staged_email` then runs cleanly (see step
   4). Not an out-of-scope finding — a re-confirmation of an
   already-documented, unchanged constraint.
2. Called the real, unmodified `capture_raw_thread_messages(limit=2)`
   against the real vault: returned dict has all four keys; `pulled`
   fetched+staged 2 real emails, `processed` had 2 message_ids,
   `skipped_already_noted` empty, `conversation_ids_touched` =
   `['8939F134E8E14C998478E34026921ADF', '227EC9A9963D4D9DB407CEFFE5D08F98']`
   — cross-checked directly against each processed message's own raw note
   frontmatter (`resolve_thread_directory` on each id resolves to a real
   Thread) — exactly the distinct `conversation_id`s of the two processed
   items, nothing from `skipped_already_noted`. PASS.
3. Called the real, unmodified `run_email_capture_pipeline()`: an initial
   call with fresh Outlook fetch found no genuinely NEW messages this run
   (mailbox already drained earlier this session — an honest empty
   `results: []`, correctly zero rows since `conversation_ids_touched`
   was empty that tick — not a bug). To positively exercise the full
   composed loop end-to-end (including all 3 re-composed side effects),
   staged one clearly-marked synthetic verification message
   (`id: "T01-SMOKE-VERIFICATION-0001"`, subject prefixed
   `[BUGFIX-05-US-01-T01 verification]`) via the real `email_staging.
   stage_email` primitive for the already-real
   `8939F134E8E14C998478E34026921ADF` Thread (created moments earlier by
   step 2's own real capture), then called `run_email_capture_pipeline
   (limit=1)`: (a) returned exactly ONE row for that one touched
   `conversation_id` (`message_count: 2`, confirming it threaded in, not
   one row per email) — PASS; (b) `get_job_tree()`'s own output was
   byte-identical before/after the call — confirms `_GRAPH`/`_build_graph`
   were never invoked — PASS; (c) directly re-read the Thread's own
   concept file afterward and confirmed a real, current `## Summary`
   reflecting the new content — Stage 2 genuinely ran — PASS. No error
   surfaced in the result row, confirming the 3 composed side effects
   (`detect_recurring_pattern` reclassify, `consult_librarian`,
   `resync_project_from_thread`) all completed without an unhandled
   exception aborting the row. **Cleanup performed immediately after**
   (this synthetic content was never left in the real vault): deleted the
   synthetic raw message note, reverted the Thread's own `participants`
   frontmatter key (removed the synthetic sender), and re-ran
   `synthesize_thread` for that `conversation_id` to regenerate an honest
   `## Summary` from its one remaining real message alone (`message_count`
   back to `1`, confirmed). Separately, one of step-2's two real,
   genuinely-captured Threads (`227EC9A9963D4D9DB407CEFFE5D08F98`, a real
   2-message Thread, no synthetic content involved) hit one transient real
   Compass timeout during ad hoc verification reading — the honest
   `summary_error` degradation path worked exactly as designed (no crash,
   existing Summary left untouched) — retried once and it synthesized
   cleanly; left in this correct, fully-synthesized final state (real
   capture work completing normally, not verification noise requiring
   reversion).
4. Called `skill_tools.process_staged_email("email-capture-pipeline")`
   directly (via `import app.main` first, matching the real production
   import order, then the direct Python call — not the HTTP layer, per
   this step's own instruction) with an empty staging queue at that point:
   returned `{"available": True, "message": "Done — 0 thread(s)
   updated."}` — confirms the wording change ("...thread(s) updated.",
   not "...email(s) filed."). PASS.

**Acceptance Criteria checklist:**
- [x] `capture_raw_thread_messages` returns additive `conversation_ids_
      touched`; existing keys unchanged (step 2)
- [x] `run_email_capture_pipeline()` no longer builds/invokes the
      `StateGraph`; composes Stage 1 + Stage 2 per touched
      `conversation_id` (step 3)
- [x] `detect_recurring_pattern`/`consult_librarian`/`resync_project_
      from_thread` each explicitly re-composed as plain calls once per
      synthesized Thread, matching `ADR-051` Decision 3's exact shape
      (code review + step 3's own no-error-row confirmation)
- [x] `_build_graph()`/`_GRAPH`/`get_job_tree()` and every node function
      remain byte-for-byte unchanged (diff review + step 3's own
      before/after job-tree equality check)
- [x] `skill_tools.process_staged_email`'s success-message wording
      reflects per-Thread granularity; signature/call site unchanged
      (step 4)
- [ ] `MEMORY.md` — see story-level `MEMORY.md` entry recorded once the
      full story reaches `Done` (single consolidated entry, not per-task)
- [x] `CHANGELOG.md` entry appended (this task's own commit)

No deviations from the plan. No out-of-scope event — the transitive
import-cycle re-check (step 1) is a re-confirmation of an already-known,
unchanged constraint, not a new finding. The live vault was left in its
correct state throughout (synthetic verification content fully cleaned
up; the two real Threads legitimately touched by real capture during
testing are left correctly, fully synthesized — not reverted, since that
is their correct real end state). Gate: clear.
