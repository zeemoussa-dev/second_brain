---
id: BUGFIX-05-US-01
title: process_staged_email retires legacy thread_match_merge so Threads no longer duplicate or orphan on new messages (BUG-026 fix)
requirement_ids: [BUG-026]
requirement_section: "BUGS.md → BUG-026"
status: Done
gate: flagged
gate_reason: "Resolved directly, 2026-08-19, operator in full autopilot for the remainder of the session: ADR-053 is exactly the right shape of fix for a content-loss finding -- it strictly adds preservation (a durable, human-visible sidecar file, fed into the same live regeneration so nothing visibly regresses either, archived not deleted on success, left untouched on failure) rather than removing any safety property. Explicitly confirmed by the architect: no risk of silent content loss. This is the same 'resolve directly when the fix only adds safety, never removes it' judgment used all night. Flag cleared; eligible for the decomposer to re-lock AC-01 and unblock T04. Prior flagged history (trigger-3, ADR-053 created) preserved in git history of this file. Decomposer re-lock #2, 2026-08-19: AC-01 re-locked against ADR-053; new task T05 created (both sidecar halves, one combined task); T04 amended in place and unblocked (Blocked/flagged -> Ready/clear); no new trigger fired this pass. Status stays In Progress (already past Draft -> Ready; T01/T02/T03 already Done) -- see the story's own 'Decomposer pass (re-lock #2)' Notes section for full reasoning. Coder pass, 2026-08-19 (session close): T05 built and verified (sidecar write/fold/archive, plus the one-time RITM0108464 backfill). T04 re-attempted against the now-Done T05 -- both AC-01 and AC-02's flip clause genuinely verified PASS live (see T04's own second Implementation Log entry), after T04's own attempt self-caught and fully repaired two real-vault incidents (a diagnostic call that side-effect-triggered a migration outside the real endpoint; a stale pre-edit server process). email-capture-pipeline's working mode flipped supervised -> autonomous, confirmed via a fresh GET, permanent -- the final undo of ESC-048's protective measure. All five tasks now Done; every locked AC verified; story advances to Done. gate: flagged (not blocking) purely to carry T04's own disclosed incident forward for human awareness, per this project's established convention -- see T04's own Implementation Log for the full incident record."
sprint: "SPRINT-065"
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-05-US-01 — process_staged_email retires legacy thread_match_merge so Threads no longer duplicate or orphan on new messages (BUG-026 fix)

## Story

**As a** Second Brain user whose captured email Threads live in the vault
**I want** a new message arriving for an existing conversation to always
update that SAME Thread — whether it is a pre-redesign flat note or an
already-migrated directory-shaped note — without ever creating a duplicate
Thread note or silently disconnecting that Thread's own `messages/`/`files/`
content from its concept file
**So that** a conversation's history and captured attachments stay intact
and discoverable in one place, and the `email-capture-pipeline` Agent can
safely run unattended again

## Context

- Bug ledger: `BUGS.md` → `BUG-026` — "`thread_match_merge`'s legacy rename
  logic duplicates old-shape Threads and orphans `messages/`/`files/` on
  new-shape Threads" (Logic, Major, `Open` at triage time, found
  2026-08-18/19, originally disclosed as `ESC-048`/`ESC-050` during
  `REQ-SB-71`/`REQ-SB-72` planning and build).
  - **Repro (two distinct failure modes, one root cause):**
    1. **Duplication (old-shape Thread):** a real, pre-redesign, FLAT
       `Work/Threads/<name>.md` Thread note exists. A new message arrives
       for that same `conversation_id`. `resolve_thread_note_path`
       (post-`ADR-049`, frontmatter-scan-based) does not find the flat file
       at its expected location, so `thread_match_merge` treats it as a
       brand-new conversation and creates a SECOND, duplicate Thread note
       under the OLD flat naming scheme.
    2. **Orphaning (new-shape Thread):** a real, already-existing, NEW-shape
       (directory-based, `ADR-048`) Thread exists with real `messages/`
       and/or `files/` content. A new message arrives for that same
       `conversation_id`. `resolve_thread_note_path` correctly finds it,
       but `thread_match_merge` then computes a rename target via its own
       still-live legacy `thread_note_path_for(...)` (a flat, hash-suffixed
       filename) and calls `rename_thread_note(path, new_path)`, physically
       moving ONLY the concept file out of its own directory — its sibling
       `messages/`/`files/` subfolders are left behind, disconnected from
       the concept file that now sits elsewhere.
  - **Expected:** `process_staged_email` correctly threads a new message
    into its existing Thread — old-shape or new-shape — without creating a
    duplicate note or orphaning any of that Thread's own content.
  - **Actual:** either a real duplicate Thread is created (old-shape case)
    or a real Thread's own `messages/`/`files/` content is silently
    disconnected from its concept file (new-shape case), depending on the
    target Thread's shape.
  - **Note (currently contained, not actively firing):** `email-capture-
    pipeline`'s working mode has been kept `supervised` since `ESC-048` was
    found — a scheduled tick creates a Pending Approval instead of
    executing `thread_match_merge` — but a manual "Run Capture Now" or
    approving that Pending Approval would still trigger it.

- **Real, current call chain confirmed by direct code reading this triage
  pass (not restated from `ESC-048`/`ESC-050`'s own text alone):**
  - `skill_registry.py` registers `"process_staged_email":
    skill_tools.process_staged_email`, granted to the `email-capture-
    pipeline` Agent identity alone.
  - `skill_tools.process_staged_email(agent_id)` — dispatched exclusively
    through `agent_schedule_registry.dispatch_with_dedicated_processing_
    lock`, per its own docstring — for `agent_id == "email-capture-
    pipeline"`, calls (via a deliberately deferred, inside-function import
    to avoid a real transitive-cycle `ImportError` this codebase already
    documented) `app.business.pipelines.email_capture_pipeline.
    run_email_capture_pipeline()`.
  - `run_email_capture_pipeline` (`app/business/pipelines/email_capture_
    pipeline.py`) reads every item from `email_staging.list_staged_emails()`
    and, for each not-yet-processed one, invokes the module's compiled
    LangGraph `StateGraph` (`_GRAPH`). That graph's `thread_match_merge`
    node (`_thread_match_merge_node`) calls
    `email_classification.thread_match_merge(email, classification,
    attachment_entries)` directly — the exact function `BUG-026` names,
    still the live implementation behind the graph's second fork point.
  - `email_classification.thread_match_merge` (lines 205-435) is confirmed,
    by direct reading, to contain both failure mechanisms verbatim:
    `existing_path = vault_writer.resolve_thread_note_path(conversation_id)`
    decides create-vs-update (the duplication mechanism when it wrongly
    returns `None` for a flat old-shape note); and, on the update branch
    only, its own trailing block (`if not created: new_path =
    vault_writer.thread_note_path_for(thread_name, ...); if new_path !=
    path: vault_writer.rename_thread_note(path, new_path)`) computes a
    flat rename target via the legacy `thread_note_path_for` and moves only
    the concept file — the orphaning mechanism.
  - The REAL new-shape functions already exist and are correct:
    `email_classification.synthesize_thread(conversation_id)` (lines
    461-668+) resolves the SAME `resolve_thread_note_path` primitive,
    reads/regenerates strictly from the Thread's own current `messages/`
    directory (derived from `existing_path.parent / "messages"` on the
    update branch — never a stale pre-rename path), and never computes or
    calls any rename — no orphaning is structurally possible. `app/
    business/pipelines/raw_message_capture.py::capture_raw_thread_messages`
    is Stage 1 (writes the raw per-message notes under `messages/` that
    `synthesize_thread` then reads). Both are already fully built
    (`REQ-SB-71-US-02`, `Done`).
  - **However, `capture_raw_thread_messages`/`synthesize_thread` are
    reachable TODAY only via `app/api/email_poc_router.py`'s `/poc`-prefixed
    endpoints** (`POST /poc/capture-raw-thread-messages`, and the
    `synthesize_thread` call a few lines below it in that same file) — a
    manual/dev-only router, never granted to any real Agent identity and
    never dispatched by the scheduler. `process_staged_email` — the ONLY
    capability the real `email-capture-pipeline` Agent's schedule or
    manual "Run Capture Now" action actually invokes for processing staged
    mail — still composes the OLD path (`run_email_capture_pipeline` →
    `thread_match_merge`) end-to-end, exactly as `ESC-048`/`ESC-050`
    disclosed. Nothing in the current codebase has rewired it.
  - `pull_email` (`skill_tools.pull_email` → `email_pull.
    pull_and_stage_emails`) is unaffected either way — it only fetches and
    durably stages raw Outlook mail; it never imports or reaches
    `email_capture_pipeline.py`/`thread_match_merge` at all, confirmed by
    direct reading. Nothing about this fix changes `pull_email`'s own
    behaviour or files.
  - **What this means for the fix's real shape:** the fix is a rewiring of
    `process_staged_email`'s underlying implementation — replacing its call
    into `run_email_capture_pipeline`/`thread_match_merge` with a call that
    composes `capture_raw_thread_messages` (Stage 1, raw per-message
    capture) and `synthesize_thread` (Stage 2, threading/synthesis) instead
    — exactly the direction `ESC-048`, `ESC-050`, and `architecture.md`'s
    own already-stated intent name. This retires `thread_match_merge`'s
    live call site for real capture going forward (the function itself may
    stay in the file if anything else still legitimately calls it — the
    decomposer/architect should confirm at `/plan-tasks`); it does not
    touch `pull_email`/`email_pull.py`.

- No `html-prototype/` screen applies — like `BUGFIX-01-US-01`/
  `BUGFIX-03-US-01`, this is backend/vault-content-only work with no
  application UI surface.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then) by the analyst; the
decomposer locks and AC-IDs this at /plan-tasks. One scenario, two
sequential When/Then facets — mirrors BUGFIX-02-US-01's and
BUGFIX-03-US-01's own "one scenario, two facets for one bug" precedent —
since both failure modes are aspects of the SAME BUG-026 regression
criterion (thread_match_merge's own legacy rename check, now replaced by
process_staged_email composing capture_raw_thread_messages/
synthesize_thread instead). The decomposer may split this into two locked
ACs at /plan-tasks if that reads more verifiable, same as those stories'
own precedent. -->

### Scenario 1: A new message for a pre-redesign, flat-shape Thread migrates and updates it in place, never duplicating it

```gherkin
Given process_staged_email's own real implementation composes
    capture_raw_thread_messages and synthesize_thread instead of the
    legacy run_email_capture_pipeline/thread_match_merge path
  And resolve_thread_directory() recognizes a legacy flat-shape Thread
    note via its own second scan tier and migrates it, lazily and on
    first touch, to the standard directory shape, preserving its own
    pre-migration ## Summary via a one-time pre_migration_summary.md
    sidecar that synthesize_thread folds into its own regenerated
    Summary and then archives (ADR-052, ADR-053)
  And a real, pre-redesign, FLAT Work/Threads/<name>.md Thread note
    exists for a given conversation_id, with a real, non-empty
    pre-migration ## Summary and no directory-shaped duplicate already
    existing for that SAME conversation_id
When a new staged message belonging to that SAME conversation_id is
    processed via process_staged_email
Then the flat Thread note is migrated in place to the standard
    <slug>/<slug>.md + messages/ directory shape
  And the migrated Thread's regenerated ## Summary genuinely reflects
    BOTH the real pre-migration history AND the new message's own
    content -- never silently replaced by a synopsis of the new
    message alone
  And the pre_migration_summary.md sidecar is renamed in place to
    pre_migration_summary.consumed.md once the fold-in succeeds --
    archived, never deleted
  And the new message is threaded into that SAME migrated Thread's
    history -- not treated as a new conversation
  And no second, duplicate Thread note is created for that conversation_id
```
<!-- AC-ID: BUGFIX-05-US-01-AC-01 -->

### Scenario 2: A new message for an already-migrated, directory-shaped Thread updates it in place, never orphaning its messages/files content

```gherkin
Given process_staged_email's own real implementation composes
    capture_raw_thread_messages and synthesize_thread instead of the
    legacy run_email_capture_pipeline/thread_match_merge path
  And a real, already-migrated, NEW-shape (directory-based) Thread exists
    for a given conversation_id, with real content under its own
    messages/ and/or files/ subfolders
When a new staged message belonging to that SAME conversation_id is
    processed via process_staged_email
Then that new message is threaded into the SAME existing Thread note
  And the Thread's own messages/ and files/ subfolders remain alongside
    their concept file -- never left behind at a stale path, never
    disconnected from it
  And, once this scenario and Scenario 1 are both verified live,
    email-capture-pipeline's working mode is flipped back to autonomous,
    undoing ESC-048's protective supervised-mode measure
```
<!-- AC-ID: BUGFIX-05-US-01-AC-02 -->

<!-- Decomposer pass, /plan-tasks step 2, 2026-08-19: split the analyst's
one scenario (two Given/When/Then facets under one heading) into two
locked-by-default ACs, tightened wording only ("via process_staged_email"
added to both Whens for precision; AC-02's trailing And reworded to make
the working-mode flip's own precondition -- BOTH facets verified, not just
this one -- explicit). AC-02 is locked as authored. AC-01 is EXCEPTIONALLY
marked `locked: false` -- direct code + real live vault reading during
this pass found that ADR-051's own composed-function rewire does not
actually close AC-01's own regression: see this story's own new
"Decomposer pass" section below and ESCALATIONS.md -> ESC-055 for the
full finding and reasoning. Per Implementation/Pipeline.md, the decomposer
is the sole role that may mark an AC non-locked, with the reason recorded
here and in that new section. -->

## Affected Screens

None — backend/vault-content only. No `html-prototype/` screen exists or
is needed for this fix.

## Dependencies

- **Blocked by:** none. `REQ-SB-71-US-02` (`Done`) already built
  `capture_raw_thread_messages`/`synthesize_thread`; this story only
  rewires `process_staged_email`'s own call site onto functions that
  already exist and already work correctly (proven live via the `/poc`
  endpoints).
- **Related to:** `REQ-SB-55-US-01` (built the original `thread_match_
  merge`-based pipeline this story retires the live call site of),
  `REQ-SB-69-US-01` (built the `pull_email`/`process_staged_email` staging
  split this story's fix sits inside, untouched otherwise), `REQ-SB-71-
  US-02` (built the replacement `capture_raw_thread_messages`/
  `synthesize_thread` functions), `REQ-SB-72-US-01` (found and disclosed
  the orphaning failure mode as `ESC-050`).
- **External:** verification needs to run against the user's real, live
  Outlook/vault configuration (`VAULT_PATH`), including at least one
  pre-redesign flat Thread note and one already-migrated directory-shaped
  Thread note with real `messages/`/`files/` content, same as every other
  capture-pipeline bugfix in this project.

## Constraints

- **Fix direction is adopted, not open:** rewire `process_staged_email`'s
  underlying implementation to compose `capture_raw_thread_messages` +
  `synthesize_thread` instead of `run_email_capture_pipeline`/`thread_
  match_merge` — this is the direction `ESC-048`, `ESC-050`, and
  `architecture.md`'s own already-stated intent all name; not a
  rename/patch of `thread_match_merge` itself. The exact call-site/graph
  restructuring (e.g. whether `email_capture_pipeline.py`'s own
  `StateGraph` is retargeted, replaced, or a new equivalent composition is
  built) is an architecture-level detail for `/plan-tasks`, not decided
  here.
- Must not change `pull_email`/`email_pull.pull_and_stage_emails` — direct
  reading confirms that path never reaches `thread_match_merge` and is
  unaffected by this fix; it stays completely untouched.
- Must not regress any of `thread_match_merge`'s other still-needed
  behaviour that `synthesize_thread`/`capture_raw_thread_messages` do not
  yet cover on their own composed path (e.g. attachment entries, recurring-
  pattern detection, route-to-project, consult-librarian, project-synthesis
  triggers) — the decomposer/architect must confirm at `/plan-tasks` that
  every real side-effect the OLD graph's other nodes (`summarize_
  attachment`, `detect_recurring_pattern`, `route_to_project`, `consult_
  librarian`, `trigger_project_synthesis`) provided is preserved by
  whatever composition replaces it, or explicitly, consciously scoped out
  with a reason.
- `email-capture-pipeline`'s working mode must stay `supervised` until this
  fix is verified live and Done — only then flip it back to `autonomous`,
  undoing `ESC-048`'s protective measure. Do not flip it back speculatively
  before verification.
- This work runs against the user's real, live Obsidian vault and real
  Outlook mailbox, not a fixture/test vault — no-data-loss (never silently
  duplicate or orphan a real Thread's content) is load-bearing, not a
  convenience, per `BUG-026`'s severity (Major).

## Implementation Tasks

<!-- Decomposer pass, /plan-tasks step 2, 2026-08-19 — supersedes the
analyst's own starting-point table. T01's scope is unchanged from the
analyst's draft (real, needed, unblocked work regardless of ESC-055).
T02's scope is NARROWED from the analyst's draft: it now verifies AC-02
only and does NOT flip the working mode to autonomous — see ESC-055 and
this story's own "Decomposer pass" section below for why. -->

<!-- Decomposer pass (re-lock), /plan-tasks step 2, 2026-08-19 — ADR-052
unblocks AC-01; two new tasks added. T03 is the vault_writer.py-only
primitive fix (independent of T01 — different files, no depends_on
edge). T04 is the live verification of AC-01 AND the working-mode flip
(the flip moves here from being permanently out-of-scope for T02, since
it now has a real place to land once all three of T01/T02/T03 are Done).
T01/T02's own tables rows below are otherwise unchanged from the prior
pass. -->

<!-- Decomposer pass (re-lock #2), /plan-tasks step 2, 2026-08-19 —
ADR-053 closes ESC-056's content-loss gap; one new task added, T04
amended in place (not rewritten). T05 is the pre_migration_summary.md
sidecar write+read+archive mechanism, spanning BOTH vault_writer.py (T03's
own file) and email_classification.py (untouched by T01/T03) -- kept as
ONE task, not split across two, since the write and read halves are
tightly coupled (one sidecar, one producer, one consumer, in the SAME
pipeline tick) and cannot be meaningfully built/verified in isolation from
each other. T04's own depends_on gains T05; its Objective/Starting
State/Tests are updated in place to verify the sidecar fold-in/archive
alongside its own already-existing migration/threading/no-duplicate
checks; its own prior FAIL attempt stays untouched in its Implementation
Log (append-only). T01/T02/T03's own rows are unchanged. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| BUGFIX-05-US-01-T01 | backend | Rewire `process_staged_email`'s underlying implementation (`run_email_capture_pipeline`) to compose `capture_raw_thread_messages`/`synthesize_thread` instead of the old `StateGraph`/`thread_match_merge`; explicitly re-compose `detect_recurring_pattern`/`consult_librarian`/`resync_project_from_thread` as plain calls, per `ADR-051` | `app/business/pipelines/raw_message_capture.py`, `app/business/pipelines/email_capture_pipeline.py`, `app/business/skill_tools.py` | `../Tasks/BUGFIX-05-US-01-T01-rewire-process-staged-email-onto-synthesize-thread.md` |
| BUGFIX-05-US-01-T02 | backend | Live verification of `AC-02` ONLY against a real, already-migrated, directory-shaped Thread with real `messages/`/`files/` content — does NOT flip the working mode (moved to `T04`) | None expected — calls the real, already-built `process_staged_email` capability endpoint only | `../Tasks/BUGFIX-05-US-01-T02-live-verification-directory-shaped-thread.md` |
| BUGFIX-05-US-01-T03 | backend | `resolve_thread_directory()` gains a second scan tier recognizing a legacy flat-shape Thread note and lazily migrating it to the standard directory shape via a new `migrate_flat_thread_to_directory` primitive, per `ADR-052` | `app/data_access/vault_writer.py` | `../Tasks/BUGFIX-05-US-01-T03-migrate-flat-thread-on-first-touch.md` |
| BUGFIX-05-US-01-T04 | backend | Live verification of `AC-01` (flat-shape Thread migrated and threaded, its `## Summary` genuinely preserving pre-migration content, never duplicated) against a real, clean flat Thread note (NOT the already-diverged Azure conversation); once both `AC-01` and `AC-02` are confirmed PASS, flips `email-capture-pipeline`'s working mode `supervised → autonomous` | None expected — calls the real, already-built `process_staged_email` capability endpoint and the real agent working-mode endpoints only | `../Tasks/BUGFIX-05-US-01-T04-live-verification-flat-thread-migration-and-mode-flip.md` |
| BUGFIX-05-US-01-T05 | backend | `migrate_flat_thread_to_directory` writes a one-time `pre_migration_summary.md` sidecar before the rename; `synthesize_thread` folds it into its SAME existing Compass call and archives it to `pre_migration_summary.consumed.md` on success; `list_all_note_paths()` excludes both filenames; per `ADR-053`. Also performs a bounded, one-time manual sidecar backfill for the ONE already-migrated, sidecar-less real Thread (`RITM0108464`) `T03`'s own smoke test produced before this mechanism existed | `app/data_access/vault_writer.py`, `app/business/email_classification.py` | `../Tasks/BUGFIX-05-US-01-T05-preserve-pre-migration-summary-via-sidecar.md` |

## Definition of Done

- [x] The acceptance-criteria scenario passes (verified live: a new message
      for a pre-existing flat Thread updates it in place, no duplicate
      created; a new message for a pre-existing directory-shaped Thread
      updates it in place, its `messages/`/`files/` stay attached)
- [x] Every Implementation Task above is complete (or explicitly dropped
      with reason)
- [x] All Constraints respected — including that `pull_email` stays
      untouched and every other real side-effect of the old graph's
      remaining nodes is preserved or consciously, explicitly scoped out
- [x] `email-capture-pipeline`'s working mode is flipped back to
      `autonomous` once verified
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] `BUG-026` flipped `In Sprint → Closed` in both `BUGS.md` and
      `BACKLOG.md`'s `## Bugs` mirror once this story is `Done`
- [x] `ESC-048` and `ESC-050` marked `Resolved` in `ESCALATIONS.md`, naming
      this story as the resolving artefact — done at `/triage` time
      (2026-08-19), since both entries' own "what still needs a human/
      architect decision" question was exactly "file a `/bug` batched into
      a `BUGFIX-NN-US-01` fix story," now answered; the underlying CODE fix
      itself still ships via `T01`/`T02` below, tracked separately by this
      story's own `status:`

## Non-Goals / Out of Scope

- Retiring `thread_match_merge`'s function body/definition itself, if
  anything else in the codebase still legitimately calls it — this story
  only retires its live call site from `process_staged_email`'s own real
  path. Confirming whether the function can be deleted entirely is a
  `/plan-tasks`-level judgement call.
- Any change to `pull_email`/`email_pull.pull_and_stage_emails` — confirmed
  out of this bug's own call chain.
- Backfilling/repairing any already-orphaned Thread from a PAST live
  `thread_match_merge` run (if any occurred before `email-capture-
  pipeline` was flipped `supervised`) — out of scope unless a human
  explicitly asks for a retrofit/repair pass once this fix ships; not
  assumed here.
- Any change to `/poc/capture-raw-thread-messages`/`/poc/synthesize-thread`
  themselves — they already work correctly and stay as-is; this story only
  adds a second, real caller for the SAME already-correct functions.

## Notes

**Prototype parity:** not applicable — this story has no screen surface,
same as `BUGFIX-01-US-01`/`BUGFIX-03-US-01`.

**Why one scenario, two facets:** per the triage-mode contract, one
untagged Gherkin scenario per bug in the batch — this batch is `BUG-026`
only. Its two `Given`/`When`/`Then` facets (old-shape duplication, then
new-shape orphaning) are two aspects of the SAME regression criterion
`BUG-026` itself names: one root cause (`thread_match_merge`'s own legacy
rename logic, computed against a flat filename scheme incompatible with
`ADR-048`'s directory shape) and one fix (retiring that call site in favour
of `capture_raw_thread_messages`/`synthesize_thread`, which has neither
failure mode by construction). This mirrors `BUGFIX-02-US-01`'s and
`BUGFIX-03-US-01`'s own established precedent of one scenario with
sequential `When`/`Then` facets for one bug with one root cause. The
decomposer may split this into two locked ACs at `/plan-tasks` if that
reads more verifiable — same latitude those two stories' own Notes
invited.

**Why `gate: clear`:** no MUST-FLAG trigger fired this pass.
- Trigger 1 (material assumption): none — the fix's real shape (rewire
  `process_staged_email` onto `capture_raw_thread_messages`/`synthesize_
  thread`) is not this analyst's own invention; it is the direction
  `ESC-048`, `ESC-050`, and `architecture.md`'s own already-stated intent
  all independently name, and this pass additionally confirmed by direct
  code reading (not assumed) that: (a) `process_staged_email`'s real,
  current call chain still runs the old `thread_match_merge` path
  end-to-end; (b) `capture_raw_thread_messages`/`synthesize_thread` already
  exist, already work, and are reachable today only via the `/poc` router,
  never any real Agent capability; (c) `pull_email` never reaches
  `thread_match_merge` at all and needs no change.
- Trigger 2 (Draft/unfinalised requirement relied on): not applicable —
  `BUG-026` is a finalised, non-Draft bug-ledger entry, not a PRD
  requirement.
- Trigger 4 (wrote an `ESCALATIONS.md` entry): not applicable — this pass
  marks `ESC-048`/`ESC-050` `Resolved` (an append-only status update +
  resolution note on already-existing entries, per this project's own
  established `ESC-041` convention), it does not write a NEW escalation
  entry.
- Trigger 5 (oversized): no — this is one well-bounded rewiring of one
  capability's own call site onto two already-built, already-correct
  functions; not a new design.
- Trigger 7 (contradictory inputs): none — `ESC-048` and `ESC-050` agree
  with each other (same root cause, `ESC-050` explicitly "reinforces, does
  not replace" `ESC-048`) and both are confirmed, not contradicted, by this
  pass's own direct code reading.
- Trigger 8 (multiple equally-valid interpretations / genuinely unclear):
  none — the fix direction has one clearly-named answer across three
  independent sources (`ESC-048`, `ESC-050`, `architecture.md`); the one
  open question (whether `thread_match_merge`'s other real side-effects —
  attachments, recurring-pattern, route-to-project, consult-librarian,
  project-synthesis — need an equivalent on the new composed path) is
  correctly a `/plan-tasks`-level architecture question, not a story-scope
  ambiguity, and is called out explicitly in `## Constraints` above so the
  architect does not miss it.

gate: clear 2026-08-19 — no triggers fired (no ADRs touched by this
analyst pass, no material assumption, `BUG-026` is a finalised ledger
entry, `ESC-048`/`ESC-050` marked `Resolved` via the established
status-update convention rather than a new entry, fix direction
unambiguous across three independent sources).

---

**Architect pass (`/plan-tasks` step 1, 2026-08-19) — resolves this
story's own open `## Constraints` question ("does every real side-effect
of the OLD graph's other nodes get preserved by whatever composition
replaces it") with a concrete technical decision, `ADR-051`.**

Direct reading of the current, real code this pass (`email_capture_
pipeline.py`'s `_build_graph()`, `email_classification.py`'s
`thread_match_merge`/`synthesize_thread`/`route_to_project`/`consult_
librarian`/`detect_recurring_pattern`/`summarize_attachment`,
`raw_message_capture.capture_raw_thread_messages`, `librarian_
housekeeping.py`'s full `run_housekeeping_pass` composition, and
`project_customer_synthesizer.resync_project_from_thread`) found:

- `synthesize_thread` ALREADY internally re-implements `thread_match_
  merge`'s create-vs-update/customer-tags-participants/`## Summary`
  responsibilities, the Files/OKF companion write, AND `route_to_project`'s
  own created-only Pending-Approval trigger — no separate composition
  needed for any of these.
- `summarize_attachment`'s old role needs NO equivalent — already,
  deliberately superseded by the Files/OKF companion mechanism
  (`synthesize_thread`'s own `write_file_companion` calls) plus the
  Librarian's structured `## Files` backfill (`REQ-SB-72-US-01-T04`);
  `## Attachments` does not exist in the new Thread body shape at all.
- **Three real side-effects have NO equivalent anywhere in the shipped
  `REQ-SB-71`/`REQ-SB-72` redesign** — `detect_recurring_pattern`,
  `consult_librarian` (the GENERALIZED Vault Filing Expert consult,
  `ADR-021`/`REQ-SB-63` — confusingly NOT the same "Librarian" as the new
  `REQ-SB-72` `librarian-housekeeping` Agent, which does something
  unrelated), and `project_customer_synthesizer.resync_project_from_
  thread` (the ongoing Project-`## Glimpse`-resync-on-every-update
  `REQ-SB-57` Scenario 1/AC-01 requires). **Resolution: all three are
  explicitly, directly re-composed as plain calls in the new orchestrating
  function** (the retargeted `email_capture_pipeline.run_email_capture_
  pipeline`, same name/module/zero-arg call shape — `skill_tools.py`
  itself needs NO change), never re-implemented, mirroring `librarian_
  housekeeping.run_housekeeping_pass`'s own already-`Accepted` "one
  orchestrator, direct sequential calls to existing plain Jobs" precedent
  (`ADR-049` Decision 7). Full mechanism, including the additive
  `conversation_ids_touched` return-key extension `capture_raw_thread_
  messages` needs to make this composition possible: `ADR-051` and
  `architecture.md`'s "`process_staged_email` Retargeted onto Stage 1/
  Stage 2 Composition" section.
- `process_staged_email`'s own capability/Skill registration
  (`skill_registry.py`, `skill_tools.process_staged_email`'s own
  signature/call site) does NOT change — only `run_email_capture_
  pipeline`'s own function body and return shape (now one row per
  synthesized Thread, not one row per email — a disclosed behavior
  change, `skill_tools.py`'s own `"error"`-key convention stays
  compatible).
- `email_capture_pipeline.py`'s `StateGraph`/`get_job_tree()` and
  `thread_match_merge`'s own function body/definition are DEPRECATED, not
  deleted this pass (per this story's own Non-Goals, deferring that call
  to `/plan-tasks`) — kept because `get_job_tree()` (`REQ-SB-65-US-01`,
  Pipeline Job Tree visualization) is a real, separate, shipped capability
  reading the SAME compiled `_GRAPH`; deleting it would be an
  uncontrolled side effect outside this story's own scope. Its resulting
  staleness (the Job Tree view no longer reflects what actually executes)
  is disclosed, not fixed, as a recommended future follow-up — see
  `ADR-051` Consequences.

**Why `gate: flagged` (trigger-3):** this pass created `ADR-051` (a
genuine, material architectural decision — retargeting a live, scheduled
Agent capability's underlying implementation off a LangGraph-executed
pipeline onto direct function composition, and deciding the fate of
`email_capture_pipeline.py`'s `StateGraph`) and updated `ADR-043`'s own
`Status` line to `Superseded by ADR-051` (points 1 and 3, live-execution
halves only — its module-layout home, Job function signatures, the
flat-JSON Pending-Approval deferred-write shape, approval gating, and the
single Agent-tier identity all stay `Accepted`, unreopened; `ADR-043`'s
own Decision/Context/Consequences body text is untouched, only its Status
line changed, mirroring this project's own established `ADR-007`/
`ADR-013`/`ADR-018`/`ADR-030` partial-supersession precedent). Per
`Implementation/Pipeline.md`, touching an ADR is MUST-FLAG trigger 3
regardless of whether the underlying decision was itself contested — a
`REVIEW-QUEUE.md` pointer is written; the decomposer still runs (the human
reviews the ADR and the resulting locked ACs/tasks together in one pass,
per the pipeline's own "does not halt the stage" contract).

**Architecture scope:** §"`process_staged_email` Retargeted onto Stage 1/
Stage 2 Composition" (`architecture.md`, new section this pass, all three
subsections), §"Email Capture Redesign — Thread Raw/Distilled Split,
Stage 1/Stage 2" (`REQ-SB-71-US-02`, the Stage 1/Stage 2 functions this
composition calls, unmodified in their own core logic except Stage 1's
additive `conversation_ids_touched` return key), §"Files/OKF Companion
Convention" (`REQ-SB-71-US-02`, unchanged, composed via `synthesize_
thread`'s own existing call). The decomposer/coder are bounded to these
sections plus `ADR-051`/`ADR-043` (Status line only) in `ADR.md` — no
other architecture section is in scope for this story's tasks.

---

**Decomposer pass (`/plan-tasks` step 2, 2026-08-19) — `AC-01` split off
and marked non-locked; `ESC-055` opened; story stays `Draft`,
`gate: flagged`.**

Read `Implementation/Pipeline.md`, `MEMORY.md`, and
`Implementation/Learnings.md` first, per this role's own standing
instruction. Locked the analyst's single Gherkin scenario (two
Given/When/Then facets under one heading) as two ACs, tightened wording
only (`"via process_staged_email"` added to both `When`s; `AC-02`'s
trailing `And` reworded so the working-mode flip's own real precondition —
BOTH facets verified, not just this one — is explicit).

**`AC-02` (orphaning facet): locked.** Direct reading confirms
`resolve_thread_note_path` correctly finds an already-directory-shaped
Thread (via `list_thread_notes()`'s own `Work/Threads/*/*.md` glob, which
DOES match a 2-level directory-shaped Thread), and `synthesize_thread`
never computes or calls any rename — no orphaning is structurally
possible on the new composed path. `T01`'s rewire closes this by
construction.

**`AC-01` (duplication facet): marked `locked: false`, exceptionally, per
this role's own sole authority to do so.** Before locking tasks against
`ADR-051`'s own claim that the composed path already correctly handles
this case, this pass independently re-verified it against the real,
current code AND the real, live configured vault (`VAULT_PATH`) — not
trusted from `ADR-051`'s own text alone, mirroring this project's own
established "gap-1's true cause must be re-confirmed by direct
investigation before it is fixed" precedent (`BUGFIX-03-US-01`). Found:
`vault_writer.list_thread_notes()` globs `Work/Threads/*/*.md` only — a
flat, top-level `Work/Threads/<name>.md` note (zero intermediate
directory segments) can never match this pattern, so `resolve_thread_
directory()`/`resolve_thread_note_path()` are blind to it regardless of
which composing function calls them. This is CONFIRMED already firing for
real in the live vault: `conversation_id ED0954959F6F4A4C88F9E2ACA3D7113A`
has both a real flat note (`RE- Azure-Net New Revenue Forecast for H2 for
AM Updates-2026-07-27-8cd2025b.md`) AND a real directory-shaped duplicate
(`2026-08-17 Azure-Net New Revenue Forecast for H2 for AM Updates/`)
holding 4 of that SAME conversation's later messages (2026-07-28, 07-29,
08-10, 08-17) — `BUG-026`'s own duplication failure mode, already live,
independent of `ADR-051`'s own rewire (which does not touch
`vault_writer.py` at all, so it structurally cannot close this). Full
finding, evidence, and the genuinely multiple, non-decided fix options:
`ESCALATIONS.md` → `ESC-055`. `REVIEW-QUEUE.md` entry added, recommending
the architect re-open/amend `ADR-051` (or write a superseding ADR) to
decide how the shared `resolve_thread_directory()`/`list_thread_notes()`
primitive should recognize a flat, pre-redesign Thread note, after which
the decomposer re-locks `AC-01` and re-runs.

**Tasks created — 2, both `status: Draft`, NOT `Ready`** (the story does
not advance to `Ready` this pass, since not every AC is locked — see
below): `BUGFIX-05-US-01-T01` (the `ADR-051` rewire itself — real, needed,
unblocked work regardless of `ESC-055`, since `AC-02` alone already
requires it, and whatever eventually closes `AC-01` will sit on top of
this SAME composed function, not replace it) and `BUGFIX-05-US-01-T02`
(live verification of `AC-02` ONLY, against a real directory-shaped Thread
with real `messages/`/`files/` content — explicitly does NOT attempt
`AC-01`'s own old-shape verification and does NOT flip `email-capture-
pipeline`'s working mode to `autonomous`, since that flip's own locked
precondition, "once this fix is verified live" in `AC-02`'s own wording,
means BOTH facets, and `AC-01` is not yet even locked). `depends_on`:
`T01: []`, `T02: [BUGFIX-05-US-01-T01]` — a strict two-node chain,
acyclic by inspection.

**AC → verification mapping:** `AC-02` is tagged in `T02`'s own `## Tests`
(the only locked AC this pass). `AC-01` carries no tagged step — it is not
locked, so `Implementation/Pipeline.md`'s "every locked AC needs a tagged
step" rule does not apply to it; it is not silently dropped, it is
explicitly disclosed as non-locked with the reason above and in
`ESC-055`.

**Working-mode flip and DoD:** the story's own Constraint ("`email-
capture-pipeline`'s working mode must stay `supervised` until this fix is
verified live and Done") is read literally — since `AC-01` is not locked,
the story cannot reach `Done` this pass, so the flip does not happen yet.
This is, if anything, a STRONGER reason to keep `supervised`: the
duplication risk `ESC-048` originally protected against is now CONFIRMED
still fully live (not merely theoretical), and would remain live even
after `T01` ships, until `AC-01`'s own underlying primitive gap is fixed.

**`ESC-048`/`ESC-050` (confirmed, not redone):** both remain `Resolved` in
`ESCALATIONS.md`, naming this story as the resolving artefact, per the
analyst's own already-completed `/triage` pass — this pass did not touch
either entry (append-only, resolved entries are never edited). Note for
the human, recorded in `ESC-055` rather than by editing either entry:
`ESC-048`'s own duplication finding is not yet FULLY closed by this
story's current, `ADR-051`-scoped plan alone — a new, separate entry
(`ESC-055`) carries that nuance forward without reopening or editing
`ESC-048` itself.

**Gate checks:** not every AC is locked (`AC-01` is `locked: false`) — per
`Implementation/Pipeline.md`, the story stays `Draft`, not `Ready`; both
tasks stay `status: Draft`, not `Ready`, per the "task status moves in
lockstep with the story" rule. `depends_on` is acyclic (`T01 → T02`,
confirmed by inspection) — condition (c) alone does not advance status
without conditions (a)/(b) also holding.

`gate: flagged 2026-08-19` — trigger 6 fired (a locked-AC candidate,
`AC-01`, could not be verified as passable under `ADR-051`'s own current
scope — no observable positive outcome is possible for it as currently
designed); trigger 7 also fired (contradictory inputs: `ADR-051`'s own
claim vs. the real code's own confirmed behavior, corroborated by a real,
live vault finding, not just a structural-reading disagreement); trigger 1
does NOT apply (no material assumption was made to fill a gap — the
opposite: an assumption implicit in `ADR-051`'s own text was actively
re-verified and found wanting, not silently trusted); trigger 3 does NOT
re-fire (no ADR created or changed by this pass — recommending the
architect reopen `ADR-051` is not the same as this pass touching it);
trigger 4 fired (a new `ESCALATIONS.md` entry, `ESC-055`, was written).
Full write-up: `ESCALATIONS.md` → `ESC-055`; `REVIEW-QUEUE.md` entries
(one closing the operator's own prior `ADR-051`-creation review, one new,
standalone entry for this finding, per this project's own established
"give a genuinely separate risk its own line item" Learnings antipattern,
`SPRINT-048`).

---

**Architect pass, re-opened (`/plan-tasks` step 1, 2026-08-19) — resolves
`ESC-055`'s own open "what still needs a human/architect decision"
question with a concrete technical decision, `ADR-052`.**

Read `Implementation/Pipeline.md`, `MEMORY.md`, and this story's own already
-written `## Notes` (above) first. Re-read `ESC-055` in full, then re-read
the real, current code independently (`vault_writer.list_thread_notes`,
`resolve_thread_directory`, `resolve_thread_note_path`, `thread_directory_
paths`, and — the load-bearing check the decomposer's own write-up flagged
as still needed — `email_classification.synthesize_thread`'s own update
branch) before deciding, rather than trusting either the decomposer's or
`ADR-051`'s own prior text alone.

**Task 1 (the code-level fix):** confirmed, by direct reading of
`synthesize_thread`, that `ESC-055`'s own option (a) — "just widen the
glob and return a found flat note's own path unmigrated" — is NOT actually
minimal-necessary; it is broken. `synthesize_thread`'s update branch derives
`messages_dir = existing_path.parent / "messages"` and calls `write_file_
companion(..., thread_directory=path.parent)`; for a flat note, `existing_
path.parent` is `Work/Threads/` itself — the SHARED root every flat note
lives directly under, not a private per-Thread directory. Naively returning
it would silently point every currently-unmigrated flat Thread's own new
raw messages/Files companions at ONE shared folder — a worse defect than
`BUG-026` itself, one layer deeper into the exact same duplication/
orphaning failure family this story exists to close. Decision: `resolve_
thread_directory()` gains a second scan tier (tried only on a miss from the
existing directory-shaped scan) that also matches a flat `Work/Threads/
<name>.md` note by its own `conversation_id` frontmatter and, on a match,
migrates it — lazily, on this first touch only, never a proactive bulk pass
— to the standard `thread_directory_paths(conversation_id)` shape via a new
`migrate_flat_thread_to_directory` primitive, before returning it. `list_
thread_notes()` itself, and every one of ITS OWN callers, is unchanged.
Full Decision/Alternatives/Consequences: `ADR-052`
(`Implementation/Architecture/ADR.md`); architecture write-up: `architecture
.md` → "Legacy flat-shape Thread recognition — self-healing migration on
first touch" (new subsection, appended directly after "Thread lookup —
frontmatter-based, again"). `ADR-049`'s own `Status` line was updated to
disclose this narrowing (Decision 1's "purely read-only" framing only —
nothing else in that ADR is reopened).

This does unblock `AC-01` — the decomposer may now re-lock it against this
concrete design. Recommended live-verification target for `T02`/a new task:
one of the 7 real flat Threads confirmed live with NO known directory-
shaped duplicate yet (NOT `conversation_id ED0954959F6F4A4C88F9E2ACA3D7113A`
— see Task 2 below for why that specific one would not actually exercise
the new migration path).

**Task 2 (the already-live duplicate, a separate data-remediation
question):** judgement, not silently defaulted — this is explicitly out of
`BUGFIX-05-US-01`'s own scope, deferred to a future Librarian-housekeeping
backlog item, NOT done as part of this story. Reasoning: (1) `ADR-052`'s
own migration mechanism deliberately does NOT retroactively fix this case
— the directory-shaped scan finds the already-existing 2026-08-17 duplicate
first and returns it, by design (ordering is load-bearing, see `ADR-052`
Consequences) — so the flat 2026-07-27 note stays un-migrated/un-merged
regardless of `AC-01`'s own fix; (2) a genuine MERGE of two already-
diverged Thread notes (reconciling `## Summary`/`## Personal Notes`/
`## Actions`/`messages/`/`files/` content across both) is a capability this
codebase does not have at all yet — a fundamentally different, harder
operation than the shape-migration `ADR-052` already builds; (3) this
story's own existing Non-Goals already scope this exact class of repair out
("Backfilling/repairing any already-orphaned Thread from a PAST live
`thread_match_merge` run... out of scope unless a human explicitly asks for
a retrofit/repair pass") — doing it here anyway would be scope creep past
what was already, deliberately scoped out; (4) there may be OTHER, not-yet-
surfaced instances of the same root cause beyond this one confirmed case —
a systematic Librarian "detect and merge duplicate/split Threads sharing a
`conversation_id`" Job is a more complete answer than a manual one-off fix,
and mirrors `CLAUDE.md`'s own "Archive, never delete" value more safely
than a hasty in-place merge. Recorded as a new, not-silently-dropped
recommendation: `ESCALATIONS.md` → `ESC-055` (marked `Resolved`, naming
`ADR-052` as the resolving artefact for the code-fix half, with this
deferral decision recorded in the same resolution note) and a dedicated
`REVIEW-QUEUE.md` entry asking the human to accept the deferral (a new
`REQ-SB-72`-extension backlog item, naming `ED0954959F6F4A4C88F9E2ACA3D7113A`
as its first concrete case) or explicitly request a one-off reconciliation
instead. `BUGFIX-05-US-01` itself does not block on this choice — `AC-01`/
`AC-02` are both fully verifiable without touching this specific
conversation.

**Why `gate: flagged` (trigger-3, again):** this pass created `ADR-052` — a
genuine, material architectural decision (a shared, several-caller lookup
primitive gains a real, disclosed WRITE side effect it did not have before,
narrowing `ADR-049` Decision 1's own "purely read-only" characterization)
— and updated `ADR-049`'s own `Status` line to disclose the narrowing. Per
`Implementation/Pipeline.md`, touching an ADR is MUST-FLAG trigger 3
regardless of whether the underlying finding was itself contested — a
`REVIEW-QUEUE.md` pointer is written; the decomposer still runs (the human
reviews `ADR-052` and the resulting re-locked `AC-01`/tasks together in one
pass, per the pipeline's own "does not halt the stage" contract). Trigger 4
does NOT re-fire for a NEW entry this pass (this pass appends a resolution
to the ALREADY-existing `ESC-055`, per this project's own established
status-update convention — `ESC-048`'s own precedent — rather than opening
a new escalation).

**Architecture scope (supersedes this story's own prior "Architecture
scope" line, above — additive, not a narrowing):** §"`process_staged_email`
Retargeted onto Stage 1/Stage 2 Composition" (`architecture.md`, unchanged
from the prior pass), §"Thread lookup — frontmatter-based, again" AND its
new sibling §"Legacy flat-shape Thread recognition — self-healing migration
on first touch" (`architecture.md`, both under "The Librarian Section —
First Housekeeping Pipeline"), §"Files/OKF Companion Convention"
(`REQ-SB-71-US-02`, unchanged). The decomposer/coder are bounded to these
sections plus `ADR-051`, `ADR-052`, and `ADR-043`/`ADR-049` (Status lines
only) in `ADR.md` — no other architecture section is in scope for this
story's tasks.

---

**Product-owner pass (`/plan-sprints`, 2026-08-19) — grouped into
`SPRINT-065` (single-story bugfix sprint).**

Confirmed this is the only `Ready`, `sprint: ""` story this pass (the
other two `Ready` stories, `REQ-SB-59-US-01`/`REQ-SB-42-US-01`, already
carry `sprint: SPRINT-059`/`SPRINT-039`). Grouping is unambiguous — one
story, its own small dependency graph (`T01: [] → T02: [T01]`, `T03: []`,
`T04: [T01, T02, T03]`), no cross-sprint edge needed, no phase-mixing
question (bugfix exception). `depends_on_sprints: []`.

`gate: clear 2026-08-19` — no MUST-FLAG trigger fired: no material
assumption, no PRD requirement involved (bugfix story, `BUG-026`-anchored),
no ADR touched by this role, no `ESCALATIONS.md` entry written, not
oversized/blocked, no contradictory inputs, exactly one valid partition.
Sprint advanced `Draft → Ready`. See `Implementation/Sprints/SPRINT-065-
process-staged-email-retires-legacy-thread-match-merge.md`.

---

**Decomposer pass (re-lock), `/plan-tasks` step 2, 2026-08-19 —
`AC-01` re-locked against `ADR-052`; two new tasks created; story
advances `Draft → Ready`.**

Read `Implementation/Pipeline.md`, `MEMORY.md`, and
`Implementation/Learnings.md` first, per this role's own standing
instruction; re-read this story's own full `## Notes` history (both prior
passes) and `ESC-055` (now `Resolved`) before acting. Read `ADR-052` in
full and the new "Legacy flat-shape Thread recognition — self-healing
migration on first touch" `architecture.md` subsection before re-locking.

**`AC-01` (duplication facet): re-locked.** Tightened wording against
`ADR-052`'s own concrete design — added an explicit `Given` naming
`resolve_thread_directory()`'s new second scan tier/migration mechanism,
narrowed the precondition `Given` to "no directory-shaped duplicate
already existing for that SAME `conversation_id`" (the real, verifiable
precondition `ADR-052`'s own ordering rule requires — a `conversation_id`
with BOTH shapes already, i.e. `ED0954959F6F4A4C88F9E2ACA3D7113A`, is a
deliberate, disclosed non-goal of this mechanism, not this AC's own
target case), and split the single `Then` into two explicit `Then`/`And`
clauses (migration to standard shape; new message threaded into that same
migrated history) so both the shape-migration outcome and the
threading-continuity outcome are each independently observable/
verifiable, not folded into one vague assertion. The trailing "no second
duplicate" `And` is unchanged in substance.

**Task placement decision: `AC-01`'s fix does NOT belong in `T01`.**
`ADR-052`'s own mechanism (`migrate_flat_thread_to_directory`, the new
`resolve_thread_directory()` scan tier) lives entirely in
`vault_writer.py` — a file that does not appear anywhere in `T01`'s own
`## Files to Modify` (`raw_message_capture.py`,
`email_capture_pipeline.py`, `skill_tools.py`). `T01` is the
composing-function rewire layer; `ADR-052`'s fix is the shared-primitive
lookup layer one level below it, used by several OTHER real callers too
(`meeting_classification.py`, `_trigger_project_resynthesis`, every
Librarian Job) — not something specific to `T01`'s own composition.
Folding it into `T01` would conflate two genuinely separate concerns and
blow `T01`'s own already-precise, already-detailed scope (hard rule 5,
coder is scope-bounded to `## Files to Modify`). A NEW task,
`BUGFIX-05-US-01-T03`, is created instead — `vault_writer.py` only, no
`depends_on` edge onto `T01` (the two are genuinely independent changes
to different files; nothing in `T03` requires `T01` to exist first, and
vice versa).

**A second new task, `BUGFIX-05-US-01-T04`, verifies `AC-01` live** —
depends on `T01` (`AC-01`'s own `Given` requires `process_staged_email`
to already compose `capture_raw_thread_messages`/`synthesize_thread`) AND
`T03` (the migration primitive itself) AND, additionally, `T02` (so that
`AC-02` is already confirmed `Done`/PASS before `T04` performs the
working-mode flip — see below). `depends_on`: `T01: []`, `T02: [T01]`,
`T03: []`, `T04: [T01, T02, T03]` — acyclic by inspection (a DAG with
`T01`/`T03` as roots, `T02` depending only on `T01`, `T04` depending on
all three).

**The working-mode flip moves from being permanently out-of-scope (as
`T02` originally, correctly, disclosed) to `T04`.** `AC-02`'s own locked
wording ties the flip to "once this scenario AND Scenario 1 are both
verified live" — since `T02` alone can only ever verify Scenario 2
(`AC-02`), and `T02`'s own `depends_on` does not include `T03`, `T02`
correctly still does not perform the flip. `T04` is the first task in
this story's own dependency graph where both preconditions are jointly
satisfiable, so it performs the flip once its own `AC-01` verification
passes and `T02`'s own already-recorded `AC-02` PASS is confirmed. `T04`
also carries a SECOND tagged `[BUGFIX-05-US-01-AC-02]` verification step
(the flip-clause itself) — `AC-02`'s own Gherkin has three `Then`/`And`
clauses, and `T02` deliberately only ever covered the first two; this is
not a re-verification of what `T02` already proved, it is the one
remaining clause of the SAME locked AC that had no tagged step anywhere
until now. This does not violate "one AC, one ID" — Pipeline.md's own
rule is "at least one tagged step per locked AC," not exactly one, and
multiple steps for the same AC across different tasks is not a new
pattern this story invents.

**AC → verification mapping (both locked ACs, confirmed complete):**
`AC-01` is tagged in `T04`'s own `## Tests` (steps 1 and 4). `AC-02` is
tagged in `T02`'s own `## Tests` (steps 1 and 4, the threading/
subfolders-unchanged clauses) AND `T04`'s own `## Tests` (step 5, the
flip clause) — every clause of both locked ACs now has at least one
tagged verification step somewhere in this story's task set. No locked
AC is left unverified.

**Existing tasks `T01`/`T02` updated, not rewritten:** `T01`'s own "Out of
Scope"/Constraints text correcting stale "AC-01 not locked" language to
point at `T03` instead; `T02`'s own Objective/Out of Scope text similarly
corrected — `AC-01` is no longer "not locked," it is locked and verified
in `T04`; the working-mode flip is no longer permanently out of scope for
this story, it is `T04`'s own job. Neither task's own `## Files to
Modify`, `## Constraints` (substantive rules), or `## Tests` steps
otherwise changed — both remain otherwise exactly as the prior pass left
them.

**Gate checks:** every AC is now locked (`AC-01` and `AC-02`); every
locked AC has at least one tagged step (confirmed above); `depends_on` is
acyclic (confirmed above). All three conditions
`Implementation/Pipeline.md` names for `Draft → Ready` now hold — the
story advances to `Ready`. Per "task status moves in lockstep with the
story," all four tasks (`T01`, `T02`, `T03`, `T04`) are set `status:
Ready` in this same pass (`T01`/`T02` flipped from `Draft`; `T03`/`T04`
created directly at `Ready`, per this project's own "new task files are
written at Draft; when the story advances to Ready, tasks move too"
sequencing, applied within one pass since both events happen together
here).

**Working-mode Constraint, re-confirmed:** the story's own Constraint
("`email-capture-pipeline`'s working mode must stay `supervised` until
this fix is verified live and Done") is still read literally — the flip
is `T04`'s own live-verification action, not something this decomposer
pass performs; the mode remains `supervised` in the real, live system
until a human/coder actually runs `T04`.

**`REVIEW-QUEUE.md`:** the still-open `ADR-052` review entry is checked
off this pass, citing the story's own frontmatter `gate_reason` (the
operator resolved it directly, in full autopilot, on the same basis
`ADR-047`–`ADR-051` were) — mirroring this project's own established
"operator resolves directly, decomposer/architect records it" convention
already used earlier in this same story's own history. The SEPARATE,
still-open entry recommending a future Librarian-housekeeping backlog
item for the already-diverged `ED0954959F6F4A4C88F9E2ACA3D7113A` case is
left untouched — that is a distinct, still-pending human decision
(accept the deferral vs. request a one-off reconciliation now), explicitly
disclosed as not blocking this story's own advancement to `Ready`.

**`ESC-048`/`ESC-050`/`ESC-055` (confirmed, not redone):** all three
remain `Resolved` in `ESCALATIONS.md`; this pass did not touch any of
them (append-only, resolved entries are never edited).

`gate: clear 2026-08-19 — no NEW trigger fired this pass`: trigger 1
(material assumption) does not apply — `AC-01`'s re-locked wording and
the `T03`/`T04` task placement both follow directly from `ADR-052`'s own
already-`Accepted` Decision text, not a gap-filling assumption; trigger 3
(ADR touched) does not apply — this pass did not create or change any ADR
(the architect already did, in the immediately prior pass); trigger 4
(new `ESCALATIONS.md` entry) does not apply — no new entry written, all
three existing entries stay `Resolved`, untouched; trigger 6 (locked AC
cannot be verified) does not apply — `AC-01` now has a concrete,
observable, tagged verification path (`T04`); trigger 7 (contradictory
inputs) does not apply — `ADR-052`'s own design is corroborated, not
contradicted, by direct reading of `vault_writer.py`'s real current
primitives (`thread_directory_paths`, `rename_thread_directory`) this
pass independently re-checked before writing `T03`'s own code; trigger 8
(multiple equally-valid breakdowns / genuinely unclear) does not apply —
the task-placement question (fold into `T01` vs. new task) has one clear
answer given `T01`'s own already-fixed `## Files to Modify` boundary, not
a genuine toss-up.

---

**Coder pass (`/implement-sprint SPRINT-065`, 2026-08-19) — `T01`, `T02`,
`T03` built and verified `Done`; `T04` found a genuine, live `AC-01`
failure and is `Blocked`; story stays `In Progress`.**

`T01` (rewire) and `T03` (migration primitive) built exactly to spec,
smoke-tested clean against the real, live vault. `T02` live-verified
`AC-02` (orphaning facet) genuinely PASS — after a self-detected,
self-repaired incident where its FIRST attempt ran against a stale,
pre-`T01` backend process (see `T02`'s own Implementation Log for the full
timeline; real vault fully repaired, confirmed byte-identical, before the
clean, passing re-attempt).

`T04` live-verified `AC-01` (duplication facet) and found it genuinely
FAILS as currently designed: `T03`'s own migration primitive works
correctly in isolation (confirmed again here), but the SAME composed
pipeline tick immediately calls `synthesize_thread` next, which
regenerates `## Summary` purely from the Thread's own `messages/`
directory — which the migration deliberately leaves EMPTY (`ADR-052`
Decision 1's own "touches only filesystem SHAPE" design). The real,
substantive pre-migration `## Summary` content is silently overwritten and
lost, not preserved — directly contradicting `AC-01`'s own locked wording.
This is a genuine, previously-undiscovered interaction gap between two
already-`Accepted` ADRs (`ADR-051`, `ADR-052`) when chained together in
the SAME real pipeline tick, not a `T01`/`T03` coding defect — neither
task's own smoke tests happened to chain "migrate" directly into
"synthesize," the one sequence `T04`'s own live, end-to-end test exposes.
Real vault fully repaired (byte-identical restore from a pre-test backup,
confirmed via `diff`) before any further action — the story's own
standing "no-data-loss is load-bearing" Constraint took precedence over
`T04`'s own narrower "keep the migration" instruction, which assumed a
successful, content-preserving migration. Full write-up: `ESCALATIONS.md`
→ `ESC-056`; `REVIEW-QUEUE.md` entry written (blocking, needs an architect
decision).

**Working-mode flip: NOT performed.** `AC-02`'s own locked wording
requires BOTH facets verified passing before the flip; `AC-01` is not.
`email-capture-pipeline` stays `supervised`.

**Story stays `In Progress`, not `Done`.** `BUG-026` stays `In Sprint`, not
`Closed` (`BUGS.md`/`BACKLOG.md` mirror). `AC-01` is not re-locked or
re-scoped by this pass — it stays locked, `FAIL`, pending the architect's
own decision on how the migration+synthesis flow should preserve a
freshly-migrated Thread's real prior content (three non-decided candidate
approaches laid out in `ESC-056`). Once decided, the decomposer re-locks
`AC-01` against the new design and a replacement/amended `T04` performs
the live re-verification and (once both facets genuinely pass) the
working-mode flip.

`gate: flagged 2026-08-19` — trigger 6 fired (`AC-01` verified live and
found FAILING, not merely unverifiable); trigger 7 fired (contradictory
inputs — `ADR-052`'s own "preserving its own prior content" framing vs.
the real, observed behavior of the composed flow); trigger 4 fired (new
`ESCALATIONS.md` entry, `ESC-056`). Trigger 3 does NOT apply — no ADR was
created or changed by this coder pass (recommending the architect revisit
`ADR-052`'s own interaction with `ADR-051` is not the same as this pass
touching either). Full detail: `ESC-056`; `REVIEW-QUEUE.md`.

---

**Architect pass (`/plan-tasks` step 1, re-opened, 2026-08-19) — resolves
`ESC-056`'s own open "what still needs a human/architect decision"
question with a concrete technical decision, `ADR-053`.**

Read `Implementation/Pipeline.md`, `MEMORY.md`, and this story's own full
`## Notes` history (all three prior passes) first. Re-read `ESC-056` in
full, then re-read the real, current code independently — `vault_writer.
migrate_flat_thread_to_directory`, `email_classification.synthesize_
thread`, `read_body_section`/`replace_body_section`, and `section_
ownership.py`'s `_CALLER_ALLOW_LISTS` — before deciding, rather than
trusting `ESC-056`'s own three candidate options at face value.

**The gap, confirmed by direct reading (not restated from `ESC-056`'s own
text alone):** `## Summary` is the ONLY section any live code path
overwrites post-migration — `## Related` ownership already transferred to
the Librarian (`ADR-049` Decision 4), `## Personal Notes`/`## Actions` are
human-owned and never agent-written, and the legacy `## Transcript`
section is dead and untouched by `synthesize_thread` either way.
`synthesize_thread`'s own `## Summary` regeneration is, by `ADR-048`'s own
deliberate design, a FULL reconstruction from `messages/` alone (never a
rolling/incremental delta) — a just-migrated flat Thread's `messages/`
holds at most the one new message that triggered the migration, so the
flat note's own real, substantive pre-migration Summary is silently lost.

**Each of `ESC-056`'s own three candidate options was evaluated directly
against the real code and rejected, not adopted as-is:** option (a)
(backfill a synthetic raw message into `messages/`) would silently
corrupt `first_message`/classification (which reads the chronologically
first message under `messages/`) and inflate `message_count` permanently
— a real, deeper risk this pass found independently, beyond the
"stretches `create_raw_message_note`'s verbatim-real-email contract"
concern `ESC-056` itself already flagged. Option (b) (a Thread-state-aware
`synthesize_thread` merge variant) either doubles Compass cost (a second
call) or produces disjointed, un-synthesized prose (a plain concatenation)
depending on how "merge" is implemented. Option (c) (copy `## Summary`
directly into the concept file during migration, then make `synthesize_
thread` append-not-replace) would make `vault_writer.py` a SECOND,
uncoordinated writer of a header `section_ownership.py`'s allow-list
already scopes to one registered caller id — exactly the pattern `ADR-042`
point 2 / `ADR-048` Decision 2 exist to prevent.

**Decision — a fourth design, adopted instead:** a one-time,
self-consuming `pre_migration_summary.md` sidecar file. `migrate_flat_
thread_to_directory` reads the flat note's own pre-migration `## Summary`
(via the existing `read_body_section`, no new reader) BEFORE the file
move and, if non-empty, writes it verbatim to `<new-thread-directory>/
pre_migration_summary.md` — plain text, no frontmatter (the same
"reserved, non-frontmatter sidecar" shape `index.md`/`log.md`/
`captures.md` already established for OKF directories, `ADR-042` point 1,
here for a Thread directory instead), living OUTSIDE `messages/` so it is
structurally invisible to `list_thread_notes()` and to `synthesize_
thread`'s own `messages_dir.glob("*.md")` loop — it can never enter the
`messages` list, so it has zero effect on classification, participant
accumulation, or `message_count`. `synthesize_thread` gains one small,
additive read immediately before composing `full_content` for its
existing Compass call: if `path.parent / "pre_migration_summary.md"`
exists, its text is prepended as an explicitly-labeled prior-history
block — the SAME Compass call, never a second one. On a SUCCESSFUL
synthesis, the sidecar is renamed in place to `pre_migration_summary.
consumed.md` (never deleted — archive-not-delete, mirroring `ADR-047`
Decision 2's own soft-delete convention at the smallest possible scope) so
it is fed exactly once; on a FAILED synthesis it is left untouched,
exactly like the Thread's own existing `## Summary`, and retried on the
next successful run. `list_all_note_paths()` gains an exclusion for both
`pre_migration_summary.md` and `pre_migration_summary.consumed.md` by
filename, mirroring the existing `index.md`/`log.md`/`captures.md`
exclusion. No `section_ownership.py` change — the sidecar carries no `## `
header and is never written via `replace_body_section`; `## Summary`'s own
allow-list stays exactly `{"email_classification.synthesize_thread"}`,
unchanged. Full Decision/Alternatives/Consequences: `ADR-053`
(`Implementation/Architecture/ADR.md`); architecture write-up:
`architecture.md` → "Migration content-preservation — the
`pre_migration_summary.md` sidecar" (new subsection, appended directly
after "Legacy flat-shape Thread recognition — self-healing migration on
first touch").

**This does NOT reopen `ADR-048`'s "full reconstruction, never a
rolling/incremental delta" Stage 2 design** — the sidecar mechanism is a
narrow, one-time exception scoped exclusively to a freshly-migrated flat
Thread's own pre-migration history (real content otherwise represented
nowhere under `messages/`), never a standing "read your own prior AI
output as rolling context" mechanism for ordinary, steady-state Thread
updates. `ADR-051` (the composed-function rewire itself) is not reopened
either.

**Task placement for the decomposer:** the fix spans two files —
`app/data_access/vault_writer.py` (the sidecar write inside `migrate_
flat_thread_to_directory`, plus the `list_all_note_paths()` exclusion) AND
`app/business/email_classification.py` (`synthesize_thread`'s own new
sidecar read/consume step). This is a deliberate, disclosed departure from
`BUGFIX-05-US-01-T01`'s own task-level Constraint ("must NOT modify
`email_classification.py`") — that constraint was scoped to `T01`'s own
narrower rewire concern, not a standing architectural prohibition; this
`ADR-053` decision supersedes it for this one, narrow, additive change
only. Whether the decomposer amends `T03` (the existing `vault_writer.py`
migration-primitive task) and `T04` (the existing live-verification task,
currently `Blocked`) in place, or creates new tasks, is a decomposer-level
judgement call — either way, `AC-01` must be re-locked against this
concrete design (a freshly-migrated Thread's `## Summary` afterward
reflects BOTH the real pre-migration history AND the new message's own
content, not one or the other) and the tagged verification step must
additionally confirm the sidecar is correctly renamed to `.consumed.md`
afterward, never deleted. Recommended live-verification target: the SAME
`Compass Alert- Failed API Calls` conversation `ESC-056` found and already
fully repaired (byte-identical), or any other of the 6 remaining real flat
Threads confirmed live with no known directory-shaped duplicate.

**Architecture scope (supersedes this story's own prior "Architecture
scope" lines, above — additive, not a narrowing):** §"`process_staged_
email` Retargeted onto Stage 1/Stage 2 Composition" (unchanged), §"Thread
lookup — frontmatter-based, again", §"Legacy flat-shape Thread recognition
— self-healing migration on first touch", AND its new sibling §"Migration
content-preservation — the `pre_migration_summary.md` sidecar"
(`architecture.md`, all under "The Librarian Section — First Housekeeping
Pipeline"), §"Email Capture Redesign — Thread Raw/Distilled Split, Stage
1/Stage 2" (`REQ-SB-71-US-02`, unchanged — `synthesize_thread`'s own core
full-reconstruction design), §"Files/OKF Companion Convention"
(unchanged). The decomposer/coder are bounded to these sections plus
`ADR-051`, `ADR-052`, `ADR-053`, and `ADR-043`/`ADR-049` (Status lines
only) in `ADR.md` — no other architecture section is in scope for this
story's tasks.

**Why `gate: flagged` (trigger-3, again):** this pass created `ADR-053` —
a genuine, material architectural decision (a shared migration primitive
gains a second, narrow, disclosed content-preservation write; a shared
Stage 2 synthesis function gains a new, additive, self-consuming read).
Per `Implementation/Pipeline.md`, touching an ADR is MUST-FLAG trigger 3
regardless of whether the underlying finding was itself contested — a
`REVIEW-QUEUE.md` pointer is written; the decomposer still runs (the human
reviews `ADR-053` and the resulting re-locked `AC-01`/tasks together in
one pass, per the pipeline's own "does not halt the stage" contract).
Trigger 4 does NOT re-fire for a NEW entry this pass (this pass appends a
resolution to the ALREADY-existing `ESC-056`, per this project's own
established status-update convention, rather than opening a new
escalation).

`ESC-056` marked `Resolved` in `ESCALATIONS.md`, naming `ADR-053` as the
resolving artefact, per this project's own established status-update
convention (append-only — the entry's own original text is untouched, a
resolution note and updated `Status:` line are appended).

---

**Decomposer pass (re-lock #2), `/plan-tasks` step 2, 2026-08-19 —
`AC-01` re-locked against `ADR-053`; one new task created (`T05`); `T04`
amended in place and unblocked; story stays `In Progress` (already past
the `Draft → Ready` transition point — see "Story status" below).**

Read `Implementation/Pipeline.md`, `MEMORY.md`, and
`Implementation/Learnings.md` first, per this role's own standing
instruction; re-read this story's own full `## Notes` history (all prior
passes), `ESC-055`/`ESC-056` (both `Resolved`), `T01`–`T04`'s own current
files in full, `ADR-053` in full, and the new "Migration
content-preservation — the `pre_migration_summary.md` sidecar"
`architecture.md` subsection before acting — including direct reading of
the real, current `migrate_flat_thread_to_directory` and `synthesize_
thread` bodies (`vault_writer.py`/`email_classification.py`) rather than
trusting `ADR-053`'s own docstring-shaped code sketches at face value.

**`AC-01` (duplication + content-preservation facet): re-locked.**
Tightened wording against `ADR-053`'s own concrete sidecar design — the
`Given` now names the sidecar mechanism explicitly (written by `migrate_
flat_thread_to_directory`, folded in and archived by `synthesize_thread`);
the precondition `Given` now requires a real, NON-EMPTY pre-migration
`## Summary` (the case the sidecar mechanism actually protects — a flat
note with an already-empty Summary needs no protection, `ADR-053`
Decision 1's own "true no-op" branch); the single "preserving its own
prior content" `Then` clause is split into two explicit, independently
observable clauses (the regenerated `## Summary` genuinely reflects BOTH
the real pre-migration history and the new message; the sidecar is
archived to `pre_migration_summary.consumed.md`) so neither the "fold-in
happened" outcome nor the "archived, not silently lost" outcome is folded
into one vague assertion. The migration-shape and no-duplicate clauses are
unchanged in substance from the prior re-lock.

**Task placement: `T05`, a NEW single task spanning BOTH files, not a
split across two tasks, not folded into `T01`/`T03` (both `Done`,
frozen).** Three real constraints shaped this decision:
1. **`T01` and `T03` are `Done`.** Per `Implementation/Pipeline.md` hard
   rule 1 ("specs are append-only... completed tasks... are frozen"), a
   `Done` task may not be edited — this alone rules out folding `ADR-053`'s
   write half into `T03` or its read half into `T01`, regardless of which
   file each half touches. `ADR-053`'s own note ("a disclosed departure
   from `T01`'s own narrower task-level constraint") describes a
   constraint SUPERSESSION for the new work, not permission to reopen a
   completed task.
2. **The write half (`vault_writer.py`, inside `migrate_flat_thread_to_
   directory`) and the read half (`email_classification.py`, inside
   `synthesize_thread`) are genuinely inseparable for verification
   purposes** — one sidecar file, written by one function and consumed by
   the other in the SAME real pipeline tick. A task shipping only the
   write half would have no way to observe whether the fold-in/archive
   half actually works (the sidecar would just sit there, unconsumed); a
   task shipping only the read half would have nothing real to read (no
   sidecar ever gets created). This directly matches the risk this pass
   was asked to weigh: splitting them across two tasks would force each to
   be built/verified in isolation against a not-yet-real counterpart —
   rejected for that reason. One task, `T05`, ships and smoke-tests both
   halves together.
3. **This is additive implementation work, not a second architecture
   decision** — `ADR-053` already fully specifies both halves; `T05`
   implements it, `T04` (unchanged in kind, amended in place) still owns
   the live, end-to-end capability-level proof.

**A genuine, additional finding this pass made by direct investigation
(not previously disclosed anywhere): `T03`'s own smoke test already
permanently migrated one real flat Thread (`conversation_id
CF7FD118DD45F740ACAD6B93AB83BEB5`, "Requested Item RITM0108464 has been
updated") to the directory shape BEFORE `ADR-053`'s sidecar mechanism
existed.** Direct reading of `T03`'s own Implementation Log confirms its
own `## Summary` is still intact (byte-identical, `synthesize_thread` has
not run on it since) — no data has been lost yet — but it now has NO
sidecar, so it carries the EXACT SAME latent content-loss risk `ESC-056`
found, live, for this one specific real Thread, the next time a genuinely
new message naturally arrives for it. This is not ambiguous and not a new
architectural question — it is a direct, bounded application of `ADR-053`'s
own already-decided sidecar shape to one already-known real case — so this
pass resolves it directly (mirroring this story's own established
"resolve directly when the fix only adds safety, never removes it"
pattern) rather than flagging: `T05` gains an explicit, bounded, one-time
manual backfill step for this ONE Thread (not a general retroactive
mechanism), gated on re-confirming at execution time that its `## Summary`
and empty `messages/` state are still exactly as `T03` left them before
writing the sidecar — if not, the task is instructed to escalate rather
than fabricate. Disclosed via a non-blocking `REVIEW-QUEUE.md` FYI entry
below, not a new `ESCALATIONS.md` entry (a concrete, already-bounded fix
is already in hand, not an open question needing a human decision).

**`T04` amended in place, not rewritten:** `depends_on` gains `T05`
(`[BUGFIX-05-US-01-T01, BUGFIX-05-US-01-T02, BUGFIX-05-US-01-T03,
BUGFIX-05-US-01-T05]`); `status`/`gate` move `Blocked`/`flagged` →
`Ready`/`clear`; `## Objective`, `## Starting State → End State`
(including the recommended verification target), and `## Tests` steps
1/4 are updated to verify the sidecar fold-in/archive alongside the
already-existing migration/threading/no-duplicate checks. Its own prior
FAIL attempt (this task's real, live finding that led to `ESC-056`) is
left completely untouched in its own `## Implementation Log` — an
append-only historical record, not something this pass edits or removes,
mirroring `T02`'s own already-established "self-detected incident stays
in the log, doesn't get erased" precedent.

**Re-verification target confirmed:** re-read `T04`'s own Implementation
Log directly (not assumed) before deciding. Its own FAIL attempt records
an explicit, `diff`-confirmed byte-identical restoration of `conversation_
id 041969487D51E942B77F5CD4A13A6CC2` ("Compass Alert- Failed API Calls")
— "The real vault is confirmed back in its exact pre-`T04` state." This is
strong enough evidence to recommend REUSING it (not a fresh, unknown
candidate) — it is safe, genuinely restored, and its own real pre-migration
`## Summary` text is already known and recorded, making "does the
regenerated Summary genuinely reflect both the old and new content" a
directly checkable comparison rather than a fresh unknown. `T04`'s own
`## Starting State` above names this as the recommended target with an
explicit fallback if it is found altered by unrelated activity at
verification time.

**`depends_on` (full graph, acyclic by inspection):** `T01: []`, `T02:
[T01]`, `T03: []`, `T04: [T01, T02, T03, T05]`, `T05: [T03]` — a DAG with
`T01`/`T03` as roots, `T02` depending on `T01`, `T05` depending on `T03`
(amends the function `T03` created), `T04` depending on all of `T01`,
`T02`, `T03`, `T05`. No cycle.

**AC → verification mapping (both locked ACs, confirmed complete):**
`AC-01` is tagged in `T04`'s own `## Tests` (steps 1 and 4, both updated
this pass to also cover the sidecar fold-in/archive). `AC-02` remains
tagged in `T02`'s own `## Tests` (steps 1/4) and `T04`'s own `## Tests`
(step 5, the flip clause) — unchanged from the prior pass. No locked AC is
left unverified; `T05` carries its own real, non-AC-tagged smoke/
regression checks (mirroring `T01`/`T03`'s own established pattern),
since live AC verification stays `T04`'s own job.

**Story status:** left `In Progress`, NOT moved to `Ready`. Per
`Implementation/Pipeline.md`'s own status vocabulary
(`Draft | Ready | In Progress | Blocked | Done`), `Ready` precedes work
starting; this story is already well past that point — three of its five
tasks (`T01`/`T02`/`T03`) are already `Done`, real work has already
shipped. Moving `status:` backward to `Ready` would be a lifecycle
regression, not a forward advance, and is not what "every AC is locked"
gates in the first place (that `Draft → Ready` rule governs the FIRST
time a story's tasks become buildable, not every subsequent re-lock after
work has already begun). The correct, and only accurate, status update
this pass makes is unblocking `T04` (`Blocked` → `Ready`) and creating
`T05` (`Ready`) — the story's own `status: In Progress` already,
correctly, reflects "tasks exist, some are `Done`, the rest are eligible
to build," with no separate story-level `Blocked` to clear (only `T04`
itself carried that sub-status, now resolved). The story reaches `Done`
only once `T04`/`T05` are also `Done` and the working-mode flip has
actually happened — unchanged from the standing Definition of Done above.

**`REVIEW-QUEUE.md`:** the still-open `ADR-053` review entry is checked
off this pass, citing the story's own frontmatter `gate_reason` (the
operator resolved it directly, in full autopilot, on the same basis
`ADR-047`–`ADR-052` were) — mirroring this project's own established
"operator resolves directly, decomposer/architect records it" convention
already used earlier in this same story's own history. A new, non-blocking
FYI entry is added for the `RITM0108464` sidecar-backfill finding above
(resolved directly via `T05`, not requiring a human decision, but
disclosed per this project's own "give a genuinely separate risk its own
line item" `Learnings.md` antipattern-avoidance, `SPRINT-048`). The
SEPARATE, still-open entry recommending a future Librarian-housekeeping
backlog item for the already-diverged `ED0954959F6F4A4C88F9E2ACA3D7113A`
case is left untouched — still a distinct, still-pending human decision,
unrelated to this pass.

**`ESC-055`/`ESC-056` (confirmed, not redone):** both remain `Resolved` in
`ESCALATIONS.md`; this pass did not touch either (append-only, resolved
entries are never edited).

`gate: clear 2026-08-19 — no NEW trigger fired this pass`: trigger 1
(material assumption) does not apply — `AC-01`'s re-locked wording and
`T05`'s own task placement/content both follow directly from `ADR-053`'s
own already-`Accepted` Decision text, independently re-verified against
the real, current code (not assumed from the ADR's own docstring sketches
alone); the `RITM0108464` backfill finding is a direct observation from
`T03`'s own already-written Implementation Log, not a gap-filling guess.
Trigger 3 (ADR touched) does not apply — this pass did not create or
change any ADR (the architect already did, in the immediately prior
pass). Trigger 4 (new `ESCALATIONS.md` entry) does not apply — no new
entry written; `ESC-055`/`ESC-056` stay `Resolved`, untouched. Trigger 6
(locked AC cannot be verified) does not apply — `AC-01` now has a
concrete, observable, tagged verification path (`T04`, amended). Trigger 7
(contradictory inputs) does not apply — `ADR-053`'s own design is
corroborated, not contradicted, by this pass's own direct reading of the
real, current `migrate_flat_thread_to_directory`/`synthesize_thread`
bodies before writing `T05`'s own code. Trigger 8 (multiple equally-valid
breakdowns / genuinely unclear) does not apply — the task-placement
question (one combined task vs. a split) has one clear answer given the
write/read halves' own genuine verification coupling and `T01`/`T03`'s own
frozen `Done` status, not a genuine toss-up.

---

**Coder pass (`/implement-sprint SPRINT-065`, 2026-08-19, session close) —
`T05` and `T04` built and verified `Done`; both locked ACs genuinely PASS
live; working mode flipped `autonomous`; story advances to `Done`.**

`T05` implemented `ADR-053`'s sidecar mechanism exactly to spec against
the real, live vault: `migrate_flat_thread_to_directory` writes `pre_
migration_summary.md` verbatim before the rename; `synthesize_thread`
folds it into its existing Compass call, archives it to `.consumed.md` on
success, exactly once (confirmed via a second synthesis run); `list_all_
note_paths()` excludes both filenames; the one-time `RITM0108464` backfill
was performed after re-confirming its preconditions still held. Full
evidence: `T05`'s own Implementation Log.

`T04` re-ran its own live verification against the now-`Done` `T05`.
**Two real, self-caught incidents occurred and were fully repaired before
the tracked verification run** (both disclosed in full in `T04`'s own
Implementation Log, second entry): a diagnostic call inadvertently
triggered `resolve_thread_directory`'s own documented side-effecting scan
outside the real capability endpoint; and, separately, the first tracked
attempt ran against a stale `uvicorn` process still running pre-`ADR-053`
code (no content lost either time — confirmed via direct byte comparison
before each repair; the real Thread was restored, byte-for-byte, twice).
Once repaired and re-attempted against a freshly-restarted, confirmed-
correct server: `[BUGFIX-05-US-01-AC-01]` verified PASS — the migration
happens, the sidecar is written and folded in (the regenerated `##
Summary` genuinely reflects both the real pre-migration alert content and
the new message), the sidecar is archived to `.consumed.md`, and no
duplicate Thread exists. `[BUGFIX-05-US-01-AC-02]`'s own flip clause
verified PASS — `email-capture-pipeline`'s working mode flipped
`supervised → autonomous` via the real `PATCH` endpoint, confirmed
permanent via a fresh, separate `GET`. The already-diverged `ED0954959F6F4A4C88F9E2ACA3D7113A`
case confirmed untouched throughout.

**All five tasks (`T01`–`T05`) now `Done`. Both locked ACs (`AC-01`,
`AC-02`) genuinely verified PASS live, with real evidence recorded in each
task's own Implementation Log. The Definition of Done is satisfied —
story advances to `Done`.** `BUG-026` flips `In Sprint → Closed` in both
`BUGS.md` and `BACKLOG.md`'s `## Bugs` mirror, as part of this same pass.

`gate: flagged` (not blocking) — carrying `T04`'s own disclosed real-vault
incidents forward for human awareness, per this project's established
"disclosed, not silently buried" convention (mirrors `T02`'s own identical
precedent from earlier in this same story). Nothing remains open or
unresolved; this is a visibility flag, not a block.
