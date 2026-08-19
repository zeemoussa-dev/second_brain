---
id: REQ-SB-57-US-01-T03
title: Meeting-link-in trigger wiring
parent_story: REQ-SB-57-US-01
requirement_id: REQ-SB-57
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal judgement calls + a concurrent-session real-vault finding logged for human spot-check — see Implementation Log"
phase: P1
depends_on: [REQ-SB-57-US-01-T01]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-57-US-01-T03 — Meeting-link-in trigger wiring

## Parent Story

- Story: [[REQ-SB-57-US-01]] — `../UserStories/REQ-SB-57-US-01-project-and-customer-status-synthesizer-agents.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-57 *Project & Customer Status Synthesizer Agents*

---

## Objective

Wire the THIRD, and last remaining, real evidence-change trigger point —
a Meeting successfully linking to a Thread
(`meeting_classification.py`'s Link-to-Thread mechanism) — to the same
shared `resync_project_from_thread` helper `T01` built, so a Meeting
link-in resynthesizes its linked Thread's own Project exactly the same
way a Thread update does (`architecture.md` → "Once linked, the Meeting
feeds the same Project Glimpse its linked Thread feeds").

---

## Starting State → End State

**Before / Inputs:**
- `app/business/meeting_classification.py::classify_recent_meetings` —
  confirmed by direct reading — calls `_link_to_thread_by_conversation_
  id(event, note_path)` first; on failure, falls back to `_link_to_
  thread_by_fallback_heuristic(event, attendees)`, which returns a
  `conversation_id` string (or `None`). Either way, `thread_linked`
  (bool) is the real, final signal of whether this Meeting is now linked
  to a Thread — set at lines 259-264 of that function.
- `vault_writer.resolve_thread_note_path(conversation_id) -> Path |
  None` is the real, already-shipped lookup from a `conversation_id` to
  its Thread's own current path.
- `project_customer_synthesizer.resync_project_from_thread(thread_path)`
  (`T01`) already reads the Thread's own current `project` frontmatter
  fresh and no-ops cleanly (`None`) when absent.

**After / Outputs:**
- `classify_recent_meetings`, immediately after `thread_linked` is
  finalized (after both the primary and fallback linking attempts, so
  either path is covered): when `thread_linked` is `True`, resolves the
  linked Thread's own real path — the fallback path already has
  `fallback_conversation_id` in hand; the primary
  (`_link_to_thread_by_conversation_id`) path needs the Meeting's own
  now-current `thread` frontmatter key re-read, or the `conversation_id`
  it already used — then calls `project_customer_synthesizer.resync_
  project_from_thread(<that Thread's own real path>)`. A `thread_
  linked=False` Meeting makes no call at all.

---

## Files to Modify

- `src/backend/app/business/meeting_classification.py` — add the one
  trigger call described above, after `thread_linked` is finalized;
  import `project_customer_synthesizer`.

---

## Constraints

- Inherits from parent story — exactly one owner writes a Project's own
  `## Glimpse`/`log.md`: this task's new call goes through `resync_
  project_from_thread` only, never assembling or writing Glimpse
  content itself, mirroring `T01`'s own pipeline-node discipline
  exactly.
- **No-op, not an error, for a linked Thread with no `project` set
  yet** — inherited directly from `resync_project_from_thread`'s own
  contract; this task adds no additional guard beyond calling it.
- **Must not alter `classify_recent_meetings`'s own existing return
  shape** (`{"subject", "note_path", "created", "customer", "linked",
  "attendees", "thread_linked"}`) — purely additive, no new key
  required by this task (though adding one is acceptable if useful, as
  long as every existing consumer of this return shape is unaffected —
  confirm no existing caller destructures this dict positionally).
- **Never crashes the meeting-processing loop for one meeting** — wrap
  the new call the same way this module's own existing per-meeting
  error handling already does, if any exists at this call site;
  otherwise mirror `consult_librarian`'s own broad, honest
  non-crashing `try/except` posture so one Synthesizer failure never
  aborts the rest of a `classify_recent_meetings` run.

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-57-US-01-AC-06]` Using real vault fixtures: a real Customer,
   a disposable Project with a linked, disposable Thread (`project`
   frontmatter set), and a disposable Meeting whose attendees/date match
   that Thread closely enough for the SAME Link-to-Thread mechanism to
   link it (or directly exercise the primary `conversation_id`-match
   path by setting the Meeting's own known-conversation-id source
   field). First, call `thread_match_merge` for a new message on that
   Thread (a real Thread-update evidence change). Then, separately,
   drive the Meeting through `classify_recent_meetings` (or call the
   Link-to-Thread call site directly) so it links to the SAME Thread (a
   second, independent evidence change for the SAME Project). Confirm
   the Project's own `## Glimpse`, read after BOTH have settled,
   reflects both — no corrupted, partial, or truncated content, and
   confirm again (by direct code inspection) that neither
   `thread_match_merge` nor `meeting_classification.py`'s own code
   calls `replace_body_section` against `## Glimpse` directly — both
   only ever reach it via `resync_project_from_thread` →
   `synthesize_project`.
2. Non-AC regression check: run a Meeting through `classify_recent_
   meetings` where NO real Thread match exists at all (`thread_linked`
   stays `False`). Confirm no exception is raised and no Project/
   Customer file anywhere is touched.
3. Clean up every disposable fixture (Project, Thread, Meeting note)
   created during verification; confirm pre-existing real vault content
   is byte-for-byte/mtime-unchanged afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-57-US-01-AC-06` — a Thread update and a Meeting link-in for
      the same Project, in close succession, both settle correctly into
      one non-corrupted `## Glimpse`, with only the Synthesizer ever
      writing to it
- [x] A Meeting that fails to link to any Thread triggers no Synthesizer
      call and raises no exception
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `_link_to_thread_by_conversation_id`/`_link_to_thread_
  by_fallback_heuristic`'s own matching logic — this task only adds a
  trigger call after linking succeeds.
- Customer-level cascade verification beyond what `resync_project_from_
  thread` → `synthesize_project` → (once `T02` lands) `synthesize_
  customer` already provides — no new Customer-specific code here.

---

## Context / Notes

Depends on `T01` only — this task's own new call needs `project_
customer_synthesizer.resync_project_from_thread` to exist, nothing from
`T02`. Independent of `T02` in the dependency graph; may build before or
after it.

---

## Implementation Log

**Built (2026-08-18):**

- `app/business/meeting_classification.py`:
  - Import list extended to also import `project_customer_synthesizer`
    from `app.business` (multi-line import, no other import changed).
  - New private helper `_trigger_project_resynthesis(conversation_id:
    str) -> None`, placed directly after `_link_to_thread_by_fallback_
    heuristic` and before `classify_recent_meetings` — resolves the
    linked Thread's own current path via `vault_writer.resolve_thread_
    note_path(conversation_id)` and, only if found, calls the SAME
    shared `project_customer_synthesizer.resync_project_from_thread`
    helper `T01` built. Never assembles or writes `## Glimpse`/`log.md`
    content itself. Wrapped in a broad `try/except Exception: pass`,
    mirroring `consult_librarian`'s own non-crashing posture, per this
    task's own Constraint.
  - `classify_recent_meetings`: immediately after `thread_linked` is
    finalized (covers both the primary `_link_to_thread_by_conversation_
    id` path and the fallback-heuristic path), captures the winning
    `conversation_id` into a new local `linked_conversation_id` (the
    primary path's own already-known `event.get("conversation_id")`, the
    fallback path's own already-known `fallback_conversation_id` — no
    re-read of the Meeting note's own `thread` frontmatter needed, per
    the task's own End State's "or" alternative) and calls
    `_trigger_project_resynthesis(linked_conversation_id)` only when
    `thread_linked` is `True`. A `thread_linked=False` Meeting makes no
    call at all. `classify_recent_meetings`'s own existing return shape
    (`{"subject", "note_path", "created", "customer", "linked",
    "attendees", "thread_linked"}`) is completely unchanged — no new key
    added (none was needed).

**Scope-internal judgement calls (logged for human spot-check, gate:
flagged per this session's own protocol):**

1. **Captured the winning `conversation_id` directly at each linking
   call site, rather than re-reading the Meeting note's own `thread`
   frontmatter after the primary-path link** — the task's own End State
   offered this as one of two equally-valid options ("needs the
   Meeting's own now-current `thread` frontmatter key re-read, or the
   `conversation_id` it already used"); capturing it directly avoids an
   extra file read with identical real behavior.
2. **New helper function `_trigger_project_resynthesis`, not an inline
   block inside `classify_recent_meetings`** — keeps the try/except
   non-crashing wrapper self-contained and independently readable,
   mirroring this module's own existing style of small, single-purpose
   private helpers (`_link_to_thread_by_conversation_id`,
   `_link_to_thread_by_fallback_heuristic`).

**Manual verification (real vault, `VAULT_PATH` = `C:\myWorx\Moussa MD\
Moussa Brain`; real, pre-existing Customer `Core42`; a disposable
Project `"REQ-SB-57-T03 Verification Project"`, one disposable Thread,
and two disposable Meeting notes — all fully removed afterward; see
"Concurrent-session finding" below for one real, disclosed side effect
found and corrected):**

- `[REQ-SB-57-US-01-AC-06]` **PASS.** Created the Project directory
  baseline under real `Core42`. Created a disposable Thread via a real
  `thread_match_merge` call (message 1), set the Thread's own `project`
  frontmatter key to the Project's title (mirroring `finalize_thread_
  project_routing`'s own real write — the Route-to-Project trigger
  itself is `T02`'s scope, not re-tested here). Called `thread_match_
  merge` again for a genuinely NEW message on the same `conversation_id`
  (message 2, a real Thread-update evidence change) then fired the SAME
  Thread-update trigger `T01` wired by calling `resync_project_from_
  thread` directly against that result — confirmed the Project's own
  `## Glimpse` was rewritten with a bullet reflecting message 2's real,
  Compass-synthesized content ("the staging rollout... completed
  successfully today, and the customer has asked for a demo next
  week"). Then drove a disposable Meeting through the REAL,
  unmodified `classify_recent_meetings()` function end-to-end, via an
  in-process monkeypatch of `outlook_com.list_calendar_events` (the
  only function replaced; `classify_recent_meetings` itself and every
  function it calls, including this task's own new
  `_trigger_project_resynthesis`, ran unmodified) returning one fake
  calendar event whose `conversation_id` exactly matched the disposable
  Thread's own — a second, independent evidence change for the SAME
  Project via the Meeting link-in mechanism. Observed:
  `classify_recent_meetings()` returned `thread_linked: True` for that
  Meeting (linked via the PRIMARY `_link_to_thread_by_conversation_id`
  strategy); re-read the Project's `## Glimpse` afterward — still
  correctly contained the same real bullet, content byte-identical
  across two consecutive reads, `_No linked Threads yet._` never
  reappeared — no corrupted, partial, or truncated content after both
  evidence changes settled. Confirmed by direct code inspection (`grep
  replace_body_section` across `meeting_classification.py` — zero
  matches) that `meeting_classification.py` never calls `replace_body_
  section` at all, and a codebase-wide grep for `replace_body_section(
  ...## Glimpse...)` found exactly the 2 calls inside `project_customer_
  synthesizer.py` (`synthesize_project`/`synthesize_customer`) and none
  anywhere else — confirming neither `thread_match_merge` nor `meeting_
  classification.py`'s own code writes `## Glimpse` directly, both only
  ever reach it via `resync_project_from_thread` → `synthesize_project`.
- **Non-AC regression check** — **PASS.** Drove a second disposable
  Meeting through the real `classify_recent_meetings()` (same
  monkeypatch technique) with a `conversation_id` guaranteed to match no
  real or disposable Thread. Observed: `thread_linked: False`, no
  exception raised, and the Project's `## Glimpse` was byte-identical
  before and after this call (re-read and compared directly) — no
  Synthesizer call fired, no Project/Customer file touched.
- **Cleanup:** removed the disposable Project directory, the disposable
  Thread note, and both disposable Meeting notes at the end of the
  verification run.

**Concurrent-session finding, found and corrected live (2026-08-18):**
using a disposable Project nested under the REAL, pre-existing Customer
`Core42` (the same real Customer `T01`/`T02` also verified against)
means `synthesize_project`'s own always-on Customer cascade (`T02`'s
own addition, already landed) rewrote the REAL `Core42.md`'s own `##
Glimpse` mid-verification to include the disposable Project as an
active line — expected, correct behavior of the already-`Done`
ownership-cascade design, but it left a real, stale "REQ-SB-57-T03
Verification Project — active" line in the real `Core42.md` once the
disposable Project directory was deleted at cleanup (deleting the
directory does not itself revert an earlier real write to a SIBLING
real file). Self-healed by calling the real, already-`Done`
`synthesize_customer("Core42")` once more after cleanup — this
regenerated `Core42`'s own `## Glimpse` fresh from current real state
("_No active Projects yet._", confirmed correct — no real active
Project exists under `Core42` right now), the same self-correcting
mechanism this codebase already trusts everywhere else, rather than a
manual byte-level revert. Also independently observed, NOT self-caused
and NOT touched: `Core42`'s own real `log.md` and `index.md` showed
real content/mtime drift between this task's own before/after
snapshots, and one real pre-existing Thread note (present at this
task's own start-of-run snapshot) was gone by its end — traced by
direct content inspection to a concurrent sibling coder session's own
`REQ-SB-57-US-01-T02`/`T04`-class live verification against the SAME
real `Core42` customer running in parallel (this task's own code was
independently confirmed to never call `append_person_note_update_line`
against `log.md` in this run, since `concluded` was `False` throughout
— `synthesize_customer`'s own `if concluded_project is not None` branch
was never taken). Reconfirms `SPRINT-025`/`SPRINT-029`'s own "a shared
dev vault can carry real concurrent-session drift" Learnings entry one
level up, at the shared real Customer-concept-file layer specifically —
recorded in `MEMORY.md` for future `REQ-SB-57`-family verification
against real, shared Customer fixtures. Removed the one empty leftover
`Core42/projects/` directory this task's own disposable Project left
behind (same class of leftover `T01`'s own verification hit and
cleaned up).

gate: flagged 2026-08-18 (coder) — trigger 8-class scope-internal
judgement calls (both logged above) plus the concurrent-session real-
vault finding above, both for human spot-check; no MUST-FLAG escalation
trigger fired (no new dependency, no shared-interface change, no ADR
deviation, no unanticipated file, the locked AC and the non-AC
regression check were both verified live with a real positive result).
`REQ-SB-57-US-01-T03` → `status: Done`.
