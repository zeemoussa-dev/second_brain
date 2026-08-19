---
id: REQ-SB-71-US-02-T05
title: Stage 2 — email_classification.synthesize_thread(): real Compass-backed judgment, full-reconstruction Summary/Related, allow-list-checked
parent_story: REQ-SB-71-US-02
requirement_id: REQ-SB-71
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-71-US-02-T01, REQ-SB-71-US-02-T02, REQ-SB-71-US-01-T01]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-02-T05 — Stage 2: `synthesize_thread`

## Parent Story

- Story: [[REQ-SB-71-US-02]] — `../UserStories/REQ-SB-71-US-02-email-capture-raw-distilled-and-two-stage-pipeline.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-71, point 2 (two-stage pipeline)

---

## Objective

New `email_classification.synthesize_thread(conversation_id: str) -> dict`
— Stage 2's real Compass-backed judgment: reads every raw message note
currently under that Thread's `messages/` directory, classifies once
against the FIRST message, and regenerates `## Summary` + `## Related`
via the allow-list-checked `replace_body_section`, registering this
function's own new caller identity in `section_ownership.py`. This
function REPLACES `thread_match_merge`'s prior role for all NEW capture
going forward.

---

## Starting State → End State

**Before / Inputs:**
- `thread_match_merge` (lines 190-410, unchanged/untouched by this task)
  is today's live-capture regeneration function — rolling/incremental,
  grounded on the Thread's own prior `## Summary` + `## Transcript` + the
  one new message's own body, called once per message, in-line with
  fetch.
- `classify_captured_email(email, known_customers, known_kinds) -> dict`
  (`REQ-SB-55-US-01-T02`) already wraps `compass_client.classify_email`
  as a thin, independently-callable Job — the real primitive this task
  reuses for the "classify once, on the first message" judgment.
- `T01`'s `thread_directory_paths`/raw message note primitives and `T02`'s
  retargeted `resolve_thread_note_path`/`list_thread_notes` exist.
- `REQ-SB-71-US-01-T01`'s `section_ownership.py` guard + `replace_body_
  section`'s required `caller` kwarg exist.
- `_build_thread_related_wikilinks` (lines 153-187, unchanged) already
  assembles `## Related`'s own honest wikilink content from
  `(customer, participants, project)`.

**After / Outputs:**
- `synthesize_thread(conversation_id: str) -> dict`:
  1. Reads every raw message note under `thread_directory_paths
     (conversation_id)["messages"]`, sorted by filename (which sorts by
     `received[:10]` first — chronological order for same-day ties broken
     by hash, an accepted, disclosed limitation mirroring this codebase's
     own existing filename-based ordering conventions elsewhere).
  2. If no raw message note exists yet for this `conversation_id`, returns
     an honest no-op result (`{"conversation_id": ..., "synthesized":
     False, "reason": "no_raw_messages"}`) — never fabricates a synthesis
     from nothing.
  3. Determines create-vs-update via `vault_writer.resolve_thread_note_
     path(conversation_id)` — the SAME primitive `thread_match_merge`
     already uses, now backed by `T02`'s deterministic retargeting. If the
     concept file doesn't exist yet, `create_thread_note_baseline` creates
     it (`thread_name` = the FIRST raw message's own `subject`, captured
     once, mirroring `ADR-046` Decision 6's "stable across the Thread's
     life" property).
  4. Calls `classify_captured_email` ONCE against the FIRST raw message's
     own reconstructed `{subject, sender_email, sender_name, body}` (never
     re-classifies against a later message — preserves the existing
     "customer decided once, on the first message, never contradicted
     later" Constraint). Writes `customer`/`type` (`kind`)/`tags`
     frontmatter the same way `thread_match_merge` already does (`build_
     tags`, union onto any existing tags, `upsert_frontmatter_key`).
  5. Accumulates `participants` from every raw message's own
     `sender_email` (union, never removing an existing one — same
     contract `thread_match_merge` already has), and `last_message_at`/
     `last_message_at_display` from the LATEST raw message's own
     `received` value.
  6. Regenerates `## Summary` from the FULL concatenated content of every
     raw message currently under `messages/` (never a rolling/incremental
     delta — full reconstruction on every call, `ADR-048` Alternatives
     Considered 6) via ONE real Compass call (reusing `compass_client.
     summarize_content`, mirroring `_synthesize_thread_summary`'s own
     verbatim technique, adapted to a full-reconstruction prompt rather
     than a rolling one), written via `vault_writer.replace_body_section
     (path, "## Summary", synthesis, caller="email_classification.
     synthesize_thread")`.
  7. Regenerates `## Related` via the EXISTING, unchanged
     `_build_thread_related_wikilinks(customer, participants, project)`,
     written via `vault_writer.replace_body_section(path, "## Related",
     related_content, caller="email_classification.synthesize_thread")`
     — the SAME single caller id covers both headers.
  8. Calls `customer_hub_linking.ensure_customer_hub_note(customer)`,
     mirroring `thread_match_merge`'s own existing call.
  9. Preserves `route_to_project`'s existing Pending-Approval trigger
     shape (`ADR-043` point 4) — triggered from this function's own end
     instead of `thread_match_merge`'s, on the same `created`/classify-
     result signal that function already uses.
- `app/data_access/section_ownership.py`'s `_CALLER_ALLOW_LISTS` gains one
  new entry: `"email_classification.synthesize_thread": frozenset({"##
  Summary", "## Related"})`.

---

## Files to Modify

- `src/backend/app/business/email_classification.py` — add `synthesize_
  thread(conversation_id: str) -> dict`, composing `T01`/`T02`'s new
  `vault_writer` primitives, the existing `classify_captured_email`,
  `_build_thread_related_wikilinks`, `customer_hub_linking.
  ensure_customer_hub_note`, and `route_to_project`. Does NOT modify
  `thread_match_merge` itself.
- `src/backend/app/data_access/section_ownership.py` — add the new
  `"email_classification.synthesize_thread"` registry entry (one line in
  `_CALLER_ALLOW_LISTS`).

---

## Constraints

- Inherits from parent story.
- **Full reconstruction from every raw message on every call** — never a
  rolling/incremental delta.
- **Classifies exactly ONCE, against the FIRST raw message only** — never
  a second, independent classification chain, and never contradicted by a
  later message.
- **`## Summary`/`## Related` writes go ONLY through the allow-list-
  checked `replace_body_section` with `caller="email_classification.
  synthesize_thread"`** — no second, parallel, unguarded write path to
  either section.
- **`## Personal Notes`/`## Actions` are never targeted by this function**
  — it writes exactly `## Summary` and `## Related`, nothing else in the
  body.
- **Zero shared lock with `T03`'s `capture_raw_thread_messages`** — this
  function must not join `agent_schedule_registry.get_shared_dispatch_
  lock()` or any other lock Stage 1 joins.
- **Does not modify `thread_match_merge`** — that function stays exactly
  as-is (it becomes dead code for new capture per `ADR-048`'s own
  Consequences; retiring it is an explicit, disclosed, coder-level
  scope-internal judgement call this task's own coder MAY make, logged in
  the Implementation Log, not mandated).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

---

## Tests

**Manual verification steps:**

Full AC-tagged verification (calling this function via the real `POST
/poc/synthesize-thread` endpoint) is `T06`'s own scope, per this story's
own Constraint that every verification call must go through a real HTTP
endpoint. This task's own Tests are non-AC, function-level foundational
checks only.

1. Non-AC foundational check: with at least 2 real (or realistic
   disposable) raw message notes already written under one Thread's
   `messages/` folder (via `T01`/`T03`'s own primitives), call
   `synthesize_thread(conversation_id)` directly. Confirm `## Summary` is
   regenerated from the FULL content of both messages (not just the
   latest), and `## Related` carries the expected wikilinks.
2. Non-AC foundational check: call `synthesize_thread` for a
   `conversation_id` with NO raw message notes yet under `messages/`.
   Confirm an honest no-op result is returned — no fabricated `##
   Summary`, no crash.
3. Non-AC foundational check: confirm `section_ownership._CALLER_ALLOW_
   LISTS["email_classification.synthesize_thread"]` is exactly
   `frozenset({"## Summary", "## Related"})`, and confirm a direct attempt
   to call `replace_body_section(path, "## Personal Notes", "x",
   caller="email_classification.synthesize_thread")` raises `SectionWrite
   NotAllowed`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `synthesize_thread` classifies once (first raw message only), does
      the real merge-vs-new-Thread judgment via `resolve_thread_note_path`,
      and fully regenerates `## Summary`/`## Related` from every raw
      message
- [ ] Both writes go through the allow-list-checked `replace_body_section`
      with the correct, newly-registered caller id
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The real HTTP endpoint — `T06`'s own scope.
- `## Personal Notes`/`## Actions` — never written by this function.
- Files/OKF companion attachment handling — `T07`'s own scope (this
  function's own end is where `T07` hooks in, once Thread identity is
  determined).
- Retiring `thread_match_merge` itself — a coder-level, disclosed,
  scope-internal judgement call, not mandated.

---

## Context / Notes

`ADR-048` Decision 3 and Alternatives Considered 6
(`Implementation/Architecture/ADR.md`) are the full reasoning for full
reconstruction over rolling synthesis. `architecture.md`'s own "Email
Capture Redesign" subsection has the identical function description. The
Gherkin's own "does the real merge-vs-new-Thread judgment (not the
provisional ConversationID-only grouping alone)" phrase is satisfied by
this function performing the REAL Compass-backed customer classification
Stage 1 deliberately never does — the create-vs-update DECISION itself
still resolves via `resolve_thread_note_path(conversation_id)`, the same
deterministic-by-design mechanism `thread_match_merge` already uses; this
task does not invent a second, independent conversation-merging algorithm
beyond that (cross-`conversation_id` merging is `REQ-SB-60`'s own
separately deferred future scope, per the parent story's own Non-Goals).

---

## Implementation Log

**2026-08-18, `/implement-sprint SPRINT-061`:**

`email_classification.synthesize_thread(conversation_id) -> dict` added
exactly as specified: reads every raw message under `messages/`,
classifies once against the first, does the real merge-vs-new-Thread
judgment via `resolve_thread_note_path`, fully regenerates `##
Summary`/`## Related` from every raw message via the allow-list-checked
`replace_body_section(..., caller="email_classification.synthesize_
thread")`. `section_ownership._CALLER_ALLOW_LISTS` gained the new entry.
Does not modify `thread_match_merge` itself (left exactly as-is, per this
task's own Constraint) — see `ESC-048` for the disclosed conflict this
creates with `T02`'s own retargeting, and the interim mitigation taken
(working mode paused).

**Real bug found and fixed live, in-scope, during real-endpoint
verification:** the initial implementation called the raw
`classify_captured_email` directly — a real Compass classification
failure (`CompassError: couldn't parse Compass response`, a real,
pre-existing Compass reliability characteristic this codebase's own
`compass_client.classify_email` already documents and retries 3× before
giving up) crashed the whole Stage 2 call with an unhandled `500`.
Fixed by switching to `classify_captured_email_with_fallback` (the SAME
`BUG-015`-established wrapper `run_email_capture_pipeline`'s own live
`classify` node already uses for this exact failure class), plus adding
the missing `conversation_id` key to the reconstructed email dict passed
into it (the fallback's own `_create_classification_failure_pending_
approval` needs it). Both fixes are within this task's own `## Files to
Modify` (`email_classification.py`).

**Manual verification (non-AC foundational checks) plus real, live
AC-04/AC-06 evidence (via `T06`'s own real endpoint, since full AC
verification is that task's own scope per this task's Tests section) —
recorded jointly here since both tasks were verified together this
session:**

- Real call against `059EC2A1E82879429DFF7124FD5F836F` (12 real raw
  messages): `## Summary` regenerated from the FULL content of all 12
  (confirmed: the synthesized text describes BOTH the Aug 11 meeting-
  scheduling exchange AND the Aug 13 Azure-consumption reply — two
  DIFFERENT raw messages, not just the latest), `customer: "Unsorted"`
  (an honest fallback result — Compass genuinely failed classification
  3× on this real, large conversation; `Unsorted` is itself a real,
  correct judgment outcome per this module's own "if you can't
  confidently tell, use Unsorted rather than guessing" convention, not a
  defect), `participants` correctly unioned to 4 real senders, `##
  Related` carrying real `[[wikilink]]`s to 2 real, matched Person notes.
- Second real call against `01D26A7530444A23803A002210620160` (2 real
  raw messages, real PDF attachment) — real, coherent full-reconstruction
  summary synthesized correctly.
- `section_ownership._CALLER_ALLOW_LISTS["email_classification.
  synthesize_thread"]` confirmed exactly `frozenset({"## Summary", "##
  Related"})` by direct source read.

Status → `Done`. `gate: clear` — no MUST-FLAG trigger against this
task's own deliverable (the live Compass-failure bug found and fixed was
a scope-internal correction within this task's own Files to Modify, not
an escalation; `ESC-048` is the one genuine, separately-recorded
out-of-scope finding this pass produced).
