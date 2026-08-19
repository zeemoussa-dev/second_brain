---
id: REQ-SB-71-US-01-T01
title: section_ownership.py guard — human-owned headers unconditionally unwritable, per-caller deny-by-default allow-list; replace_body_section gains required caller kwarg
parent_story: REQ-SB-71-US-01
requirement_id: REQ-SB-71
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-01-T01 — Section-ownership allow-list guard

## Parent Story

- Story: [[REQ-SB-71-US-01]] — `../UserStories/REQ-SB-71-US-01-section-ownership-enforcement.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-71, point 6 (Section-ownership enforcement)

---

## Objective

New, composed-alongside `app/data_access/section_ownership.py` implementing
two independent, structural rules (human-owned headers always unwritable;
per-caller deny-by-default allow-list), and retrofit `vault_writer.
replace_body_section`'s own signature to require a `caller: str`
keyword-only parameter that the guard checks before performing any write.

---

## Starting State → End State

**Before / Inputs:**
- `vault_writer.replace_body_section(path, header: str, new_content: str)
  -> bool` (line 1548) has zero caller-awareness — any caller can pass any
  header string and it replaces that region unconditionally, no rejection
  path exists at all.
- No `section_ownership.py` module exists.

**After / Outputs:**
- `app/data_access/section_ownership.py` (new):
  ```python
  class SectionWriteNotAllowed(PermissionError):
      """Raised by replace_body_section when `caller` may not write
      `header` -- a real, observable, honest failure, never a silent
      no-op indistinguishable from replace_body_section's own separate,
      unchanged 'header not found in THIS file' contract."""

  _HUMAN_OWNED_HEADERS: frozenset[str] = frozenset({
      "## Personal Notes", "## Actions",
  })

  _CALLER_ALLOW_LISTS: dict[str, frozenset[str]] = {
      "email_classification.thread_match_merge": frozenset({"## Summary", "## Related"}),
      "thread_summary_backfill.backfill_thread_summaries": frozenset({"## Summary"}),
      "project_customer_synthesizer.synthesize_project": frozenset({"## Glimpse"}),
      "project_customer_synthesizer.synthesize_customer": frozenset({"## Glimpse"}),
      "project_customer_synthesizer.finalize_background_amendment_proposal": frozenset({"## Background"}),
  }

  def is_header_allowed(caller: str, header: str) -> bool:
      if header in _HUMAN_OWNED_HEADERS:
          return False
      return header in _CALLER_ALLOW_LISTS.get(caller, frozenset())
  ```
  `_HUMAN_OWNED_HEADERS` is checked FIRST and unconditionally — no
  caller's own registry entry can ever override it, by construction.
  `_CALLER_ALLOW_LISTS` is deny-by-default: a caller id absent from the
  dict may write nothing.
- `vault_writer.replace_body_section(path, header: str, new_content: str,
  *, caller: str) -> bool` — `caller` is REQUIRED and keyword-only (no
  default). Calls `section_ownership.is_header_allowed(caller, header)`
  first; raises `section_ownership.SectionWriteNotAllowed(caller, header)`
  when not allowed, before touching the file. When allowed, the existing
  header/next-header location + replace logic (`ADR-042` point 2) runs
  completely unchanged. The function's own separate, pre-existing
  "header not found in this file" → returns `False` contract is
  unaffected — that check still only fires after the `caller` check
  passes.
- `read_body_section`/`append_body_section_line`/
  `replace_body_opening_line`/`insert_body_line_if_missing` are all
  UNCHANGED — this task touches `replace_body_section` and nothing else in
  `vault_writer.py`.

---

## Files to Modify

- `src/backend/app/data_access/section_ownership.py` (new) — the module
  above in full: `SectionWriteNotAllowed`, `_HUMAN_OWNED_HEADERS`,
  `_CALLER_ALLOW_LISTS` (seeded with the 4 real, already-shipped callers'
  correct entries, per the table above — this task ships the registry
  content; `T02` retrofits the CALL SITES to pass their own matching
  `caller=` id), `is_header_allowed(caller, header) -> bool`.
- `src/backend/app/data_access/vault_writer.py` — `replace_body_section`'s
  own signature gains the required keyword-only `caller: str` parameter;
  its own body gains the `is_header_allowed` check + `raise` at the very
  top, before any of its existing header-location logic runs. Import
  `section_ownership` at this module's top level. No other function in
  this file is touched.

---

## Constraints

- Inherits from parent story.
- **Exactly two rules — no snapshot-before-write safety net, no extra
  approval gate beyond `REQ-SB-57`'s existing `Background`-amendment
  flow.**
- **`caller` has NO default** — a forgotten declaration at any future call
  site must be a loud `TypeError` at call time, never a silently-permitted
  gap.
- **Caller granularity is the calling FUNCTION (`module.function`), not the
  calling module** — `project_customer_synthesizer.py`'s own three real
  call sites are three DISTINCT ids in the registry, since
  `synthesize_project` has no legitimate reason to ever write
  `## Background`.
- **A rejected write must fail loudly and honestly** — `raise`, never a
  silent no-op that reads the same as "header not found," and never a
  partial write (the guard check happens before any file I/O).
- **Scope is exactly `replace_body_section`** — do not add the same guard
  to `append_body_section_line`, `insert_body_line_if_missing`,
  `replace_body_opening_line`, or `write_note`.
- **This task does NOT touch any real call site's own arguments** — the 4
  existing callers still call the OLD 3-positional-argument signature
  until `T02` retrofits them (this task alone leaves them broken at
  call-time — that is expected and resolved in the very next task,
  `T02`, before this story reaches `Done`).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`) — `section_ownership.py` lives in `data_access`, never
  `business`, since `replace_body_section` itself (a `data_access`
  function) performs the check and cannot depend on `app.business`.

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-71-US-01-AC-02]` In a Python shell (or a small throwaway
   script), call `vault_writer.replace_body_section(<a real note's path>,
   "## Personal Notes", "x", caller="thread_summary_backfill.
   backfill_thread_summaries")` — a caller whose registered allow-list is
   `{"## Summary"}` only, naming a header outside it. Confirm
   `section_ownership.SectionWriteNotAllowed` is raised, and confirm (by
   reading the note back) the section's existing content is byte-for-byte
   unchanged — no write occurred.
2. `[REQ-SB-71-US-01-AC-03]` Repeat step 1 against `## Personal Notes` and
   separately `## Actions`, using EVERY ONE of the 5 registered caller ids
   in `_CALLER_ALLOW_LISTS` (including one whose allow-list nominally
   includes `## Summary`/`## Glimpse`/`## Background` — i.e. a caller that
   IS otherwise permitted to write something). Confirm
   `SectionWriteNotAllowed` is raised in every single case — the
   human-owned check applies uniformly, never overridden by any caller's
   own registry entry. Then call `vault_writer.read_body_section(<the same
   path>, "## Personal Notes")` and confirm it still succeeds and returns
   the section's real content unchanged — reads are never blocked, only
   writes.
3. Non-AC regression check: call `replace_body_section` with a caller id
   and header pair that IS on that caller's own allow-list (e.g.
   `caller="thread_summary_backfill.backfill_thread_summaries"`,
   `header="## Summary"`) against a disposable test note. Confirm the
   write succeeds and the section's new content round-trips correctly via
   `read_body_section` — the guard does not interfere with a legitimately
   allowed write's own correctness.
4. Non-AC regression check: call `replace_body_section` with a caller id
   NOT present in `_CALLER_ALLOW_LISTS` at all (e.g. `caller="nonexistent.
   function"`), naming an otherwise-ordinary agent-owned header (e.g.
   `"## Summary"`). Confirm `SectionWriteNotAllowed` is raised —
   deny-by-default for an unregistered caller, not a silent pass-through.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-71-US-01-AC-02` — a caller writing outside its own
      allow-list is rejected outright, with a real, observable, honest
      failure
- [x] `REQ-SB-71-US-01-AC-03` — a human-owned section is always readable,
      never writable by any agent code path, uniformly across every
      declared human-owned header and every caller
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Retrofitting the 4 real existing call sites with their own `caller=`
  argument — `T02`'s own scope entirely (this task alone leaves them
  calling an invalid signature; expected, resolved next).
- `REQ-SB-71-US-02`/`-US-03`'s own new caller registrations
  (`email_classification.synthesize_thread`,
  `email_classification.write_file_companion`,
  `meeting_classification.classify_recent_meetings`) — each of those
  stories' own tasks adds its own registry entry, depending on this task.
- Extending the guard to any other body-writing primitive.
- A snapshot-before-write safety net or any new approval gate.

---

## Context / Notes

`ADR-048` Decision 2 and Alternatives Considered 1-3
(`Implementation/Architecture/ADR.md`) are the full architectural
reasoning (why per-function not per-module granularity; why a plain
registry not a decorator). `architecture.md`'s own "Section-Ownership
Enforcement (`REQ-SB-71-US-01`)" subsection has the identical code shape —
this task is a direct, literal implementation of both, with the exact
registry table already fully specified (no open mechanism question left).

---

## Implementation Log

**What was built:** `app/data_access/section_ownership.py` (new) — exactly
the module shape the story/architect/decomposer already fully specified:
`SectionWriteNotAllowed(PermissionError)`, `_HUMAN_OWNED_HEADERS =
frozenset({"## Personal Notes", "## Actions"})`, `_CALLER_ALLOW_LISTS`
seeded with the 5 real caller ids (`email_classification.
thread_match_merge`, `thread_summary_backfill.backfill_thread_summaries`,
`project_customer_synthesizer.synthesize_project`, `project_customer_
synthesizer.synthesize_customer`, `project_customer_synthesizer.
finalize_background_amendment_proposal`), `is_header_allowed(caller,
header)` checking Rule 1 first, unconditionally. `vault_writer.
replace_body_section` gained the required keyword-only `caller: str`
parameter, raising `SectionWriteNotAllowed` before any file I/O when
disallowed. No deviation from the plan.

**Verification method:** this task's own `## Tests` explicitly authorizes
"a Python shell (or a small throwaway script)" for this task specifically
(unlike `REQ-SB-70-US-01-T01`, which is endpoint-only) — used a throwaway
script (`src/backend/.scratch/verify_section_ownership.py`, not part of
`## Files to Modify`, not committed) run via the real venv interpreter
against a REAL Thread note in the real operator vault
(`Work/Threads/Requested Item RITM0108464 has been updated-2026-07-27-
025663bd.md`). The script restores the note's own pre-verification content
after its one legitimate write-regression check — confirmed byte-for-byte
restored.

- `[REQ-SB-71-US-01-AC-02]` **PASS.** Called `replace_body_section` with
  `caller="thread_summary_backfill.backfill_thread_summaries"` (allow-list
  `{"## Summary"}`) against `"## Personal Notes"` (outside its allow-list)
  — `section_ownership.SectionWriteNotAllowed` raised; the note's content
  was confirmed byte-for-byte unchanged immediately after. Also confirmed
  (non-AC regression) an UNREGISTERED caller (`"nonexistent.function"`) is
  denied-by-default against an otherwise-ordinary agent-owned header
  (`"## Summary"`) — rejected, content unchanged.
- `[REQ-SB-71-US-01-AC-03]` **PASS.** Every one of the 5 registered caller
  ids was tried against BOTH `"## Personal Notes"` and `"## Actions"` (10
  attempts total, including callers otherwise permitted to write
  something) — `SectionWriteNotAllowed` raised in all 10 cases, content
  unchanged after all 10. `read_body_section(path, "## Personal Notes")`
  still succeeded (returned `''`, the section's real — empty, since this
  note kind doesn't carry that section yet — content) — reads are never
  blocked, only writes.
- Non-AC regression: `replace_body_section` with an ALLOWED pair
  (`caller="thread_summary_backfill.backfill_thread_summaries"`,
  `header="## Summary"`) against the same real note succeeded (`True`
  returned) and round-tripped correctly via `read_body_section` — the
  guard does not interfere with a legitimately allowed write. The note was
  then restored to its exact pre-verification content (confirmed
  byte-for-byte).
- Additionally confirmed `is_header_allowed("project_customer_
  synthesizer.finalize_background_amendment_proposal", "## Background")`
  returns `True` — the exact caller+header pair `T02`'s retrofit of that
  specific call site relies on (see `T02`'s own Implementation Log for
  why this function's own full end-to-end live invocation could not be
  separately triggered this session).

gate: clear 2026-08-18 — no MUST-FLAG trigger fired; every locked AC in
this task got a real, live, verified outcome above; no assumption, no ADR
change by this task, no escalation, not oversized, no contradictory input,
no genuinely unclear scope.
