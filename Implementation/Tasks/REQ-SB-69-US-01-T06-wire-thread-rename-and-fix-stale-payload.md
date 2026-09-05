---
id: REQ-SB-69-US-01-T06
title: Wire thread_match_merge to the human-readable filename/lookup/rename mechanism; fix route_to_project's stale Pending-Approval-payload path
parent_story: REQ-SB-69-US-01
requirement_id: REQ-SB-69
type: backend
status: Done
gate: flagged
gate_reason: "trigger-4 (ESCALATIONS.md entry written, ESC-044 — resolved same pass, BUG-019)"
phase: P1
depends_on: [REQ-SB-69-US-01-T05]
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-69-US-01-T06 — Wire Thread rename mechanism; fix stale payload

## Parent Story

- Story: [[REQ-SB-69-US-01]] — `../UserStories/REQ-SB-69-US-01-decoupled-email-pull-and-human-readable-thread-notes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-69 *Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes*

---

## Objective

Wire `thread_match_merge` to `T05`'s new filename/lookup/rename
primitives — a Thread note's filename becomes human-readable and
collision-safe, tracks its own `last_message_at` on every later message,
and never loses content across a rename. Fix the real, previously-latent
stale-path bug this rename mechanism newly exposes in `route_to_project`'s
Pending-Approval payload (`ADR-046` Decision 8).

---

## Starting State → End State

**Before / Inputs:**
- `thread_match_merge` (`email_classification.py`, lines 151-284):
  `created = not vault_writer.thread_note_exists(conversation_id)`;
  `path = vault_writer.thread_note_path(conversation_id)`; on create,
  `vault_writer.create_thread_note_baseline(conversation_id,
  tags=message_tags)`. Every later primitive call in the function
  (`upsert_frontmatter_key`, `read_body_section`,
  `append_body_section_line`, `replace_body_opening_line`,
  `replace_body_section`) composes against this SAME `path` for the
  whole function body.
- `route_to_project` (lines 374-447): reads `thread_path =
  thread_result["thread_path"]`, includes it (a plain string) in the
  Pending Approval's `payload`. `finalize_thread_project_routing` (lines
  450-476): `thread_path = Path(payload["thread_path"])`, writes
  `project` frontmatter directly to that path — trusting it unchanged
  since proposal time.

**After / Outputs:**
- `thread_match_merge`'s create-vs-update branch changes: `existing_path
  = vault_writer.resolve_thread_note_path(conversation_id)`; `created =
  existing_path is None`. On create: `path = vault_writer.
  thread_note_path_for(email["subject"], email["received"][:10],
  conversation_id)` (the FIRST message's own subject becomes
  `thread_name`, captured once, never recomputed on a later message —
  `ADR-046` Decision 6); `vault_writer.create_thread_note_baseline(
  conversation_id, thread_name=email["subject"], tags=message_tags)` is
  written directly AT `path` (i.e. `write_note` must be called with the
  filename stem this new `path` implies — reconcile
  `create_thread_note_baseline`'s own internal `write_note` call, which
  currently hardcodes `filename_stem=conversation_id`, to use the new
  stem instead; see `## Files to Modify` for the exact composition). On
  update: `path = existing_path` initially (every existing read/write in
  the function body continues to compose against this real, CURRENT
  path, unchanged from today's shape) — then, AFTER every other
  frontmatter/body write for this call has completed (mirrors `ADR-046`
  Decision 7's own "rename never races an in-flight write" ordering),
  compute `new_path = vault_writer.thread_note_path_for(<the Thread's own
  thread_name frontmatter value, read once near the top of the
  function>, email["received"][:10], conversation_id)`; if `new_path !=
  path`, call `vault_writer.rename_thread_note(path, new_path)` and use
  `new_path` as the `thread_path` value in this function's own returned
  result dict.
- `route_to_project`'s Pending-Approval `payload` gains
  `"conversation_id": thread_result["conversation_id"]` (already
  available on `thread_result`, no new plumbing needed to obtain it).
- `finalize_thread_project_routing` re-resolves the Thread's CURRENT real
  path via `vault_writer.resolve_thread_note_path(payload.get(
  "conversation_id"))` when `conversation_id` is present in `payload`,
  falling back to the legacy `Path(payload["thread_path"])` string ONLY
  when `conversation_id` is absent (a real, disclosed migration-window
  case — any Pending Approval created BEFORE this task ships lacks it).
  The write itself (`upsert_frontmatter_key(thread_path, "project",
  project)`) targets whichever path was resolved.

---

## Files to Modify

- `src/backend/app/business/email_classification.py`:
  - `thread_match_merge`: replace the `created`/`path` computation at the
    top of the function with the `resolve_thread_note_path`-based logic
    above. Read the Thread's own `thread_name` (from frontmatter, once
    resolved, for the update branch — on create it's simply
    `email["subject"]`) so the rename-check computation has the right
    input. Move the rename call (if any) to the END of the function body,
    after every other write, before constructing the returned `result`
    dict — use the FINAL resolved path (post-rename, if renamed) as
    `result["thread_path"]`.
  - `route_to_project`: add `"conversation_id": thread_result[
    "conversation_id"]` to the `payload` dict passed to
    `create_pending_approval`.
  - `finalize_thread_project_routing`: change `thread_path = Path(
    payload["thread_path"])` to resolve via `vault_writer.
    resolve_thread_note_path(payload["conversation_id"])` when
    `"conversation_id" in payload`, falling back to the legacy
    `Path(payload["thread_path"])` string otherwise. If the resolved
    lookup returns `None` (a genuinely deleted/moved Thread — an edge
    case, not expected in ordinary operation), fall back to the legacy
    `payload["thread_path"]` string too rather than raising, mirroring
    this codebase's own "honest degradation over a hard crash" posture.

- `src/backend/app/data_access/vault_writer.py`:
  - `create_thread_note_baseline`: reconcile its own internal `write_note`
    call's `filename_stem` argument with the new `thread_note_filename_
    stem`-derived stem, rather than the old `conversation_id`-only stem —
    this is the one small additional change beyond `T05`'s own already-
    built primitive functions, needed so a BRAND-NEW Thread is created
    directly at its own correct, human-readable filename from the start
    (never created under the old scheme and then immediately renamed).

---

## Constraints

- Inherits from parent story.
- **The rename call happens strictly AFTER every other frontmatter/body
  write for that call has completed** — never before, and never
  interleaved. This is what `ADR-046` Decision 7 names as the concrete
  mechanism preventing a rename from racing an in-flight write to the
  OLD path.
- **`thread_name` is captured ONCE, at creation, from the first message's
  own subject, and never recomputed on a later message** — a later
  message's own (possibly different, e.g. "Re: X") subject must NOT
  change an already-existing Thread's `thread_name` frontmatter value.
- **Every existing Thread behavior this task doesn't name stays
  unchanged**: tag accumulation/union, `participants` accumulation,
  `## Transcript` growth, `## Summary`/opening-line regeneration via
  Compass, `customer_hub_linking.ensure_customer_hub_note` — none of
  this function's own already-shipped logic changes shape, only its
  create-vs-update path resolution and its post-write rename step.
- **`route_to_project`'s existing "no-op immediately when `created` is
  False" guard is unchanged** — this task only adds one new payload key.
- **The legacy `payload["thread_path"]`-string fallback in
  `finalize_thread_project_routing` must keep working for any Pending
  Approval created before this task ships** — a real, disclosed
  migration-window consequence (`ADR-046`), not an edge case to skip.
- No change to `T07`/`T08`'s own scope (dates, wikilinks) in this task.

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-69-US-01-AC-05]` Stage and process a brand-new email whose
   `conversation_id` has never been seen before (via `email_staging.
   stage_email` + `run_email_capture_pipeline()`, or a direct
   `thread_match_merge(email, classification, [])` call). Confirm the
   resulting Thread note's filename is `<slug-of-subject>-<date>-
   <8-hex-hash>.md`, that its frontmatter's `thread_name` equals the
   email's own subject, and that the filename is NEVER the raw
   `conversation_id` GUID.
2. `[REQ-SB-69-US-01-AC-06]` Construct two distinct synthetic
   `conversation_id` values that produce the SAME `thread_name`+`date`
   (e.g. two emails with an identical subject received on the same
   date, but genuinely different `conversation_id`s). Run
   `thread_match_merge` for both. Confirm two DISTINCT files are written
   (different hash suffixes), and confirm neither note's own content
   (frontmatter, `## Summary`, `## Transcript`) was overwritten by the
   other's — read both files back and confirm each still reflects only
   its own originating email.
3. `[REQ-SB-69-US-01-AC-07]` Using the Thread note created in step 1,
   record its current `## Summary`/`## Transcript`/`## Attachments`
   content and its current filename. Run `thread_match_merge` again for
   the SAME `conversation_id` with a message whose `received` date is a
   LATER calendar date. Confirm: (a) the file at the OLD filename no
   longer exists; (b) a file exists at a NEW filename reflecting the new
   date, still human-readable, still collision-safe; (c) the note's
   frontmatter (`conversation_id`, `tags`, `participants`, `thread_name`)
   and its `## Summary`/`## Transcript`/`## Attachments` content from
   BEFORE this call are all still present in the renamed file, with the
   new message's own contribution added on top — nothing lost or reset.
4. Non-AC regression check (the stale-payload fix): create a real
   `route_thread_to_project` Pending Approval for a brand-new Thread
   (`route_to_project`). Confirm its `payload` now includes
   `conversation_id`. THEN, before approving it, trigger a later message
   on the SAME conversation that causes a real rename (per step 3's own
   technique) — confirm the Thread's filename has genuinely changed.
   THEN approve the Pending Approval (`finalize_thread_project_
   routing`). Confirm the `project` frontmatter key is written to the
   Thread's CURRENT (renamed) file, not the stale path captured at
   proposal time.
5. Non-AC regression check: construct a synthetic legacy-shaped Pending
   Approval payload (a `route_thread_to_project` record with
   `payload["thread_path"]` set but NO `conversation_id` key — simulating
   one created before this task shipped). Call
   `finalize_thread_project_routing` against it directly. Confirm it
   still resolves and writes correctly via the legacy string-path
   fallback, without raising.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-69-US-01-AC-05` — a brand-new Thread's filename is
      human-readable, never the raw `conversation_id` GUID
- [x] `REQ-SB-69-US-01-AC-06` — two colliding date+name Threads are
      safely disambiguated, neither overwrites the other
- [x] `REQ-SB-69-US-01-AC-07` — an existing Thread's filename tracks a
      new last-message date; all prior content preserved intact
- [x] The stale Pending-Approval-payload bug is fixed, with a working
      legacy-payload fallback (Test steps 4, 5)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — updated (`## Patterns`): grep the whole business layer for every
      real caller of a "deterministic path" helper before superseding it,
      not just the story's own named call site.
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Human-readable date rendering (`last_message_at_display`, `##
  Transcript` timestamps) — `T07`.
- `## Related` wikilinks — `T08`.
- Deleting/retiring `thread_note_path`/`thread_note_exists` — a future
  cleanup task.

---

## Context / Notes

`ADR-046` Decisions 6-8 (`Implementation/Architecture/ADR.md`) are the
full architectural reasoning, including Context point 5/6's own direct-
reading grounding for why the stale-payload bug is real and reachable
now (not before this story). `T05`'s own primitives (`thread_note_
filename_stem`, `thread_note_path_for`, `resolve_thread_note_path`,
`rename_thread_note`) are composed here, not rebuilt — read `T05`'s own
task file/Implementation Log for their exact signatures before wiring.

---

## Implementation Log

**What was changed:**

- `src/backend/app/business/email_classification.py`:
  - `thread_match_merge`: create-vs-update now resolved via
    `vault_writer.resolve_thread_note_path(conversation_id)`
    (`existing_path is None` ⇒ `created`), replacing the retired
    `thread_note_exists`/`thread_note_path` pair for this call site. On
    create: `thread_name = email["subject"]` (captured once), `path =
    thread_note_path_for(thread_name, email["received"][:10],
    conversation_id)`, `create_thread_note_baseline(conversation_id,
    thread_name, email["received"][:10], tags=message_tags)`. On update:
    `path = existing_path`; `thread_name` read from the Thread's own
    already-resolved frontmatter (never recomputed from the later
    message's own subject). Every existing read/write in the function
    body is otherwise untouched, still composing against `path`. At the
    very end of the function — strictly after every frontmatter/body
    write (including the opening-line/`## Summary` regeneration or its
    `summary_error` skip) — on the UPDATE path only, recomputes
    `new_path` via `thread_note_path_for` against the now-current
    `last_message_at`; renames via `vault_writer.rename_thread_note` iff
    it differs, and uses the final (possibly renamed) path as
    `result["thread_path"]`.
  - `route_to_project`: payload gains `"conversation_id":
    thread_result["conversation_id"]`.
  - `finalize_thread_project_routing`: `thread_path` now resolved via
    `vault_writer.resolve_thread_note_path(payload["conversation_id"])`
    when `"conversation_id" in payload`, falling back to the legacy
    `Path(payload["thread_path"])` string when the key is absent OR the
    resolved lookup returns `None`. The write itself
    (`upsert_frontmatter_key(thread_path, "project", project)`) targets
    whichever path was resolved; the returned dict's own `"path"` display
    value is unchanged (`payload["thread_path"]`, the human-readable
    string captured at proposal time), per the task's own spec.
- `src/backend/app/data_access/vault_writer.py`:
  - `create_thread_note_baseline`: gained a required `date: str`
    parameter (positional, after `thread_name`, before the existing
    `tags` keyword) — needed so its own internal `write_note` call could
    use `thread_note_filename_stem(thread_name, date, conversation_id)`
    as `filename_stem` instead of the old `conversation_id`-only stem, so
    a brand-new Thread is created directly at its own correct,
    human-readable filename from the start. This exact parameter was not
    spelled out verbatim in the task's own `## Starting State → End
    State` text (which only said "reconcile ... filename_stem argument
    with the new thread_note_filename_stem-derived stem") — logged below
    as a scope-internal judgement call, not an escalation (the function
    itself is explicitly named in this task's own `## Files to Modify`).
    Docstring updated to describe the new behavior (a Thread is now
    created directly at its correct filename, never created under the
    old scheme and immediately renamed — T05's own docstring note to that
    effect is now stale and was corrected here).

**Scope-internal judgement calls (for human spot-check, not escalations):**

1. **`create_thread_note_baseline` gained a `date: str` parameter**
   (positional, `conversation_id, thread_name, date, tags=None`), not
   spelled out as an exact signature in the task's own End-State text.
   Required because `thread_note_filename_stem`/`thread_note_path_for`
   need a `date` component this function otherwise has no way to obtain,
   and the task's own text is explicit that this function's internal
   `write_note` call must use the NEW stem, not the old
   `conversation_id`-only one. `thread_match_merge` passes
   `email["received"][:10]` — the SAME date value it independently uses
   to compute `path` via `thread_note_path_for` just before this call, so
   the two stay in lock-step by construction (verified live, `AC-05`).
2. **`finalize_thread_project_routing`'s returned `"path"` value stays
   `payload["thread_path"]`** (the string captured at proposal time),
   never the freshly-resolved path — per the task's own explicit text
   ("`thread_path` stays in the payload too, for the Pending Approvals
   UI's own human-readable display — only the WRITE path... changes").
   Only the actual `upsert_frontmatter_key` WRITE target changed; the
   display value returned to the approval-resolution caller is
   unchanged, matching the task's own literal instruction.

**Real, previously-undisclosed finding, escalated and resolved same
pass (`ESC-044`, `BUG-019` — see `ESCALATIONS.md`/`BUGS.md` for full
write-ups):** before treating `thread_note_exists`/`thread_note_path` as
untouched-but-effectively-superseded (per this task's own Constraint,
"any other real caller must be confirmed first"), grepped
`src/backend` for both names. Found a real, live second caller —
`meeting_classification.py::_link_to_thread_by_conversation_id`
(`REQ-SB-56-US-01`'s Link-to-Thread PRIMARY strategy) — outside this
task's own `## Files to Modify`, whose existence check
(`thread_note_exists(conversation_id)`) silently starts returning
`False` for every genuinely-new Thread once this task ships (confirmed
live). Per `Implementation/Pipeline.md` hard rule 5 ("any out-of-scope
event → immediate escalation, no improvisation"), this was escalated
(`ESC-044`) rather than silently worked around — and, mirroring this
same story-adjacent sprint's own already-established `ESC-043`/`BUG-018`
"found live during this task's own verification, small, causally
inseparable from the change that exposed it → fix directly, same pass"
precedent, resolved immediately as `BUG-019` (`meeting_classification.py`
one-line existence-check swap to `resolve_thread_note_path(...) is not
None`), verified live, and logged. `gate: flagged` (trigger-4) reflects
this — not a blocker on `T06`'s own locked ACs, which are unaffected.

**Verification — manual mode, run live against the real, configured
vault (`VAULT_PATH = <OPERATOR_VAULT_OLD>`), via two
disposable, self-cleaning Python scripts (`verify_t06.py`,
`verify_bug019.py`) using only `T06VerifyCustomer`/`T06VERIFY-CONV-*`
prefixed disposable data, all cleaned up (Thread notes deleted, the
disposable Customer/Project directory tree `rmtree`'d, disposable
Pending-Approval records purged) and confirmed zero residue afterward.
Real Compass calls were made (live LLM synthesis for `## Summary`/
opening-line regeneration and `guess_project_for_thread`), not mocked.**

- **`[REQ-SB-69-US-01-AC-05]`** — a brand-new conversation
  (`T06VERIFY-CONV-0001`, subject "T06 Verify Kickoff Sync") processed
  via `thread_match_merge`. Resulting filename:
  `T06 Verify Kickoff Sync-2026-08-10-81148565.md` — never the raw
  `conversation_id`; frontmatter `thread_name` == the email's own
  subject exactly. **PASS (4/4 assertions).**
- **`[REQ-SB-69-US-01-AC-06]`** — two distinct real `conversation_id`s
  (`...-0002A`/`...-0002B`) sharing an identical subject ("Weekly
  Status") and identical date (`2026-08-11`) both processed. Two
  genuinely distinct files written (`...-feece4e2.md` /
  `...-0b117eac.md`, distinct hash suffixes), each note's own
  `conversation_id` frontmatter confirmed to match only its own
  originating email — neither overwrote the other. **PASS (3/3
  assertions).**
- **`[REQ-SB-69-US-01-AC-07]`** — the `AC-05` Thread's pre-update
  filename/frontmatter/`## Transcript` recorded, then `thread_match_merge`
  called again for the SAME `conversation_id` with a message dated
  `2026-08-15` (5 days later) and a different subject ("RE: T06 Verify
  Kickoff Sync"). Confirmed: (a) the OLD filename
  (`...-2026-08-10-81148565.md`) no longer exists on disk; (b) a NEW file
  exists (`...-2026-08-15-81148565.md`) — same hash suffix (confirms
  `conversation_id`-alone hashing held), new date, still human-readable;
  (c) `conversation_id`/`tags`/`thread_name` frontmatter preserved
  (`thread_name` still the ORIGINAL subject, confirming it was never
  recomputed from the later "RE:" subject); `## Transcript` contains
  BOTH the original and the new dated entry (nothing lost); `## Summary`
  present and regenerated (expected, unrelated pre-existing behavior).
  **PASS (8/8 assertions).**
- **Stale-payload regression (test step 4)** — a real
  `route_thread_to_project` Pending Approval created via `route_to_project`
  for a brand-new Thread (`...-0004`, "Contract Renewal Discussion");
  confirmed `payload["conversation_id"]` present and correct. A LATER
  message on the SAME `conversation_id`, dated 10 days later, triggered a
  real rename (`...-2026-08-12-...` → `...-2026-08-22-...`, confirmed the
  stale proposal-time path no longer exists on disk). Approved via
  `finalize_thread_project_routing(approval["payload"])` — confirmed the
  `project` frontmatter key was written to the CURRENT, renamed file, not
  the stale path. **PASS (4/4 assertions).**
- **Legacy-payload fallback regression (test step 5)** — a synthetic
  `route_thread_to_project`-shaped payload with `thread_path` set but NO
  `conversation_id` key (simulating a pre-`T06` record), passed directly
  to `finalize_thread_project_routing`. Confirmed it resolved and wrote
  the `project` frontmatter key correctly via the legacy string-path
  fallback, no exception raised. **PASS (1/1 assertion).**
- **`BUG-019` fix (non-AC regression, `meeting_classification.py`)** — a
  fresh disposable post-fix Thread + a disposable Meeting note confirmed
  `_link_to_thread_by_conversation_id` now returns `True` and writes the
  Meeting's own `thread` frontmatter field correctly. **PASS.**

All 21 T06-own assertions (across `AC-05`/`AC-06`/`AC-07`/stale-payload/
legacy-fallback) plus the separate `BUG-019` regression check passed.
Cleanup confirmed: 0 residual `T06VERIFY*` Thread notes, disposable
Customer directory removed, disposable Pending-Approval record purged.

**A pre-existing, unrelated environment quirk found and worked around
(not a code defect, not escalated):** a direct, isolated
`from app.business import email_classification` as a throwaway script's
OWN first import can intermittently raise `ImportError` on this
codebase's own pre-existing `email_classification` ↔
`pipelines.email_capture_pipeline` circular import (routed through
`vault_filing_expert` → `agent_orchestration` → `skill_registry` →
`skill_tools`), depending on which side of the cycle a script happens to
enter from first. Confirmed this is NOT a real production concern:
`import app.main` (the actual running app's own entry point) imports
cleanly every time — the real app's own router-registration import order
already avoids the trap. Every verification script here does
`import app.main` first, exactly mirroring the real app's own resolution
order, before importing the specific business modules under test.

**MUST-FLAG check:** trigger 4 fired (an `ESCALATIONS.md` entry,
`ESC-044`, was written) — `gate: flagged`, resolved same pass, does not
block `Done` (mirrors `ESC-043`/`BUG-018`'s own identical precedent: the
finding is real but does not touch this task's own locked ACs). No
material assumption filled a genuine spec gap beyond the one documented
scope-internal judgement call above (the `date` parameter, directly
implied by the task's own explicit "reconcile... with the new
thread_note_filename_stem-derived stem" instruction, not invented); no
new ADR created or changed; no locked AC failed verification; no new
dependency, unrelated shared-interface change, or unanticipated file
beyond the one found-and-immediately-resolved above.

gate: flagged 2026-08-17 — trigger-4 (`ESC-044`/`BUG-019`, written and
resolved same pass; does not block this task's own `Done` status, per
`ESC-043`/`BUG-018`'s own established precedent).
