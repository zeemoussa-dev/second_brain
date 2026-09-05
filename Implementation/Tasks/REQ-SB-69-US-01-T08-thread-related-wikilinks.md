---
id: REQ-SB-69-US-01-T08
title: New, deterministically-regenerated ## Related body section — real Customer/Person/Project wikilinks, honest absence for Unsorted/unresolved entities
parent_story: REQ-SB-69-US-01
requirement_id: REQ-SB-69
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal judgement call logged for human spot-check — _build_thread_related_wikilinks implemented without the task text's own sketched `path` parameter (see ## Implementation Log)"
phase: P1
depends_on: [REQ-SB-69-US-01-T06, REQ-SB-69-US-01-T07]
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-69-US-01-T08 — Thread `## Related` wikilinks

## Parent Story

- Story: [[REQ-SB-69-US-01]] — `../UserStories/REQ-SB-69-US-01-decoupled-email-pull-and-human-readable-thread-notes.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-69 *Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes*

---

## Objective

Add a new, deterministically-regenerated `## Related` body section to
Thread notes (`ADR-046` Decision 9) — real `[[wikilink]]`s to the
Thread's matched Customer, its participants' real Person notes, and its
routed Project (once resolved) — via `replace_body_section`, NOT Email's
existing `insert_body_line_if_missing`-based inline primitives (which
would silently conflict with `replace_body_opening_line`'s own full
ownership of the same pre-first-header region). Honest absence, never a
fabricated/placeholder link, for Unsorted/unresolved entities.

---

## Starting State → End State

**Before / Inputs:**
- `create_thread_note_baseline` writes body `"## Summary\n\n##
  Transcript\n"` — no `## Related` section exists.
- `thread_match_merge` calls `customer_hub_linking.
  ensure_customer_hub_note(customer)` only (never the inline-wikilink
  half, `ensure_hub_note_and_link`/`link_note_to_customer_hub`) — no
  wikilink of any kind is ever written into a Thread note's body today.
- `people_extraction.find_existing_person_note(email: str) -> dict |
  None` (lines 195-206) already resolves a real Person note by email,
  read-only, never creating one.
- `vault_writer.hub_note_path(customer) -> Path` already resolves a
  Customer hub note's own path (its `.stem` is the wikilink target).
- A Thread's `project` frontmatter key is absent by design until
  `route_to_project`'s Pending Approval is approved (`ADR-042` point 7) —
  confirmed real, structural timing fact.

**After / Outputs:**
- `create_thread_note_baseline`'s own body gains a `## Related` section,
  alongside `## Summary`/`## Transcript`: `"## Summary\n\n##
  Transcript\n\n## Related\n"` (initially empty — regenerated on the
  very first `thread_match_merge` call that follows creation, same as
  every other call).
- `thread_match_merge` gains, near its end (after the Thread's own
  `project`/`participants`/`customer` frontmatter values are all
  current for this call), a call to a new helper —
  `_build_thread_related_wikilinks(path, customer, participants,
  project) -> str` or composed inline — that assembles a real, honest
  Markdown bullet list of `[[wikilink]]`s:
  - `[[CustomerHubStem]]` when `customer` is real (not `"Unsorted"`/
    blank) — `vault_writer.hub_note_path(customer).stem`.
  - `[[PersonStem]]` for each of the Thread's own current
    `participants` (read from frontmatter, already-accumulated) that
    has a REAL Person note — `people_extraction.
    find_existing_person_note(participant_email)`; a participant with
    no matching Person note is honestly omitted, never guessed.
  - `[[ProjectStem]]` once the Thread's own `project` frontmatter key is
    populated (read the Thread's CURRENT frontmatter — this key is
    absent on every newly created and not-yet-routed Thread, per
    `ADR-042` point 7; when present, resolve its own stem the same way
    `route_to_project`'s own project-directory convention does).
  This list is written into `## Related` via `vault_writer.
  replace_body_section(path, "## Related", <the assembled content>)` —
  a full, deterministic regeneration on EVERY call, never a patch. A
  Thread with none of the three currently resolvable produces an empty
  (but present) `## Related` section — an honest absence.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py` — add `"## Related\n"`
  to `create_thread_note_baseline`'s own body literal, immediately after
  `"## Transcript\n"`.
- `src/backend/app/business/email_classification.py`:
  - `thread_match_merge`: add the `## Related` regeneration call
    (composing `customer_hub_linking`, `people_extraction`,
    `vault_writer.replace_body_section`, and a read of the Thread's own
    CURRENT `project`/`participants` frontmatter) near the end of the
    function, after every other frontmatter/body write for this call has
    already landed (participants/tags/customer are all current by then).
    Import `people_extraction` if not already imported at this module's
    top level (it already is, per this module's existing `from
    app.business import (... people_extraction ...)` block).

---

## Constraints

- Inherits from parent story.
- **Uses `replace_body_section`, never `insert_body_line_if_missing` or
  any other inline-insert primitive** — `ADR-046` Decision 9's own
  explicit, direct-reading-grounded reasoning (a real primitive
  conflict, not a style preference).
- **Regenerated from scratch on EVERY `thread_match_merge` call** — never
  incrementally patched; a Thread that gains a Project link on a LATER
  call (once routing resolves) must see `## Related` grow to include it
  without any special-casing beyond "recompute from current state."
- **No fabricated or placeholder wikilink, ever** — a participant with no
  real Person note, an Unsorted/blank customer, or a not-yet-routed
  Project are ALL honestly omitted, never guessed or stubbed. This is
  the parent story's own hard Constraint (Scenario 11).
- **`customer_hub_linking.ensure_customer_hub_note(customer)`'s own
  existing call is unaffected** — this task adds a NEW wikilink mechanism
  alongside it, never replaces or removes that call.
- **`## Related`'s own presence in `create_thread_note_baseline`'s
  baseline body must not break `ensure_thread_note_baseline_frontmatter`
  or any other already-shipped Thread-note-reading code** — a plain
  additive body-section change; confirm no other function assumes the
  Thread body has exactly two `## ` headers.
- No change to `T05`/`T06`/`T07`'s own scope (filename/lookup/rename,
  dates) beyond the one additive body-literal line above.

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-69-US-01-AC-10]` Run `thread_match_merge` for a real (or
   realistic synthetic) email matched to a REAL, known Customer, with a
   sender whose email has a real, existing Person note. Open the
   resulting Thread note — confirm `## Related` carries at least one
   real `[[wikilink]]` (the Customer hub stem at minimum; the sender's
   Person stem too if a real Person note exists for that email). Open
   Obsidian (or inspect its own graph-data cache/backlink index) and
   confirm a real edge now connects the Thread note to that Customer hub
   note.
2. Extend step 1: approve a real `route_to_project` Pending Approval for
   this same Thread (so `project` frontmatter becomes populated). Run
   `thread_match_merge` again (a later message on the same conversation,
   or a direct re-invocation). Confirm `## Related` now ALSO includes the
   Project's own `[[wikilink]]`, added without disturbing the Customer/
   Person links already there — confirming the "regenerated from
   CURRENT state on every call" contract, not a one-time snapshot.
3. `[REQ-SB-69-US-01-AC-11]` Run `thread_match_merge` for a message whose
   `customer` classification is `"Unsorted"` and whose sender has NO
   real, existing Person note. Confirm the resulting Thread note's `##
   Related` section is present but contains NO wikilink at all — an
   honest, empty section, never a fabricated or placeholder link (e.g.
   never `[[Unsorted]]` or a guessed name).
4. Non-AC regression check: confirm a brand-new Thread's baseline body
   (immediately after `create_thread_note_baseline`, before any
   `thread_match_merge` regeneration) has `## Related` present alongside
   `## Summary`/`## Transcript`, and confirm `read_body_section`/
   `replace_body_section` against `## Summary`/`## Transcript` still work
   correctly with the new third section present (no header-boundary
   regression from the added section).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-69-US-01-AC-10` — a real wikilink to a matched entity is
      written into `## Related`; a real graph edge appears in Obsidian
- [x] `REQ-SB-69-US-01-AC-11` — no fabricated/placeholder wikilink is
      ever written for an unresolved relationship
- [x] `## Related` regenerates from current state on every call (Test
      step 2)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to `route_to_project`/`finalize_thread_project_routing`
  beyond what `T06` already built.
- Backfilling already-captured Thread notes' `## Related` sections —
  parent story's own Non-Goal, deferred.
- This is the LAST task in this story's own dependency chain — nothing
  else depends on it.

---

## Context / Notes

`ADR-046` Decision 9 and Context point 6 (`Implementation/Architecture/
ADR.md`) are the full architectural reasoning, including the direct-
reading finding that ruled out reusing Email's own inline-wikilink
primitives. `people_extraction.find_existing_person_note` and
`vault_writer.hub_note_path` are pre-existing, already-shipped read
primitives — this task composes them, does not modify them.

---

## Implementation Log

**What was changed:**

- `src/backend/app/data_access/vault_writer.py::create_thread_note_baseline`:
  body literal changed from `"## Summary\n\n## Transcript\n"` to
  `"## Summary\n\n## Transcript\n\n## Related\n"` — the third, initially
  empty body section, alongside its own docstring note explaining it is
  regenerated from scratch on the very first `thread_match_merge` call
  that follows creation, same as every other call. No other change to
  this function.
- `src/backend/app/business/email_classification.py`:
  - new `_build_thread_related_wikilinks(customer, participants, project)
    -> str` helper, placed directly above `thread_match_merge`. Composes
    three already-shipped, read-only resolution primitives — never a new,
    divergent stem-resolution scheme:
    - `vault_writer.hub_note_path(customer).stem` for the Customer hub
      link, when `customer` is real (not `"Unsorted"`/blank) — the SAME
      stem source `customer_hub_linking.link_note_to_customer_hub`
      already uses (confirmed identical to the OKF concept file's own
      stem per that module's own docstring).
    - `people_extraction.find_existing_person_note(participant_email)`
      for each of the Thread's own current `participants` — a
      participant with no real, existing Person note is honestly
      omitted (never guessed); its own `note_path`'s `.stem` is the
      wikilink target.
    - `vault_writer.project_directory_paths(customer, project)["concept"]
      .stem` for the Project link, only when `project` is truthy — the
      SAME project-directory convention `route_to_project`/
      `finalize_thread_project_routing` already use
      (`_project_directory_root` + `okf_directory_paths`).
    Returns a `"- [[Stem]]"`-per-line Markdown bullet list, or `""` when
    none of the three are currently resolvable.
  - `thread_match_merge`: one new call block, placed after the rename
    block (so it targets the FINAL, post-rename path) and before the
    function's own `result` dict is built — `_build_thread_related_
    wikilinks(customer, existing_participants, frontmatter.get(
    "project"))` fed into `vault_writer.replace_body_section(path,
    "## Related", related_content)`. `existing_participants` is the
    already-current, post-union participants list this call already
    computed above (no new read); `frontmatter.get("project")` reuses the
    frontmatter dict already read near the top of this function (before
    any of this call's own writes — `project` itself is never touched by
    `thread_match_merge`, only by `finalize_thread_project_routing`, so
    that earlier read stays accurate for this call).
  - `thread_match_merge`'s own docstring updated (the paragraph
    describing `ensure_customer_hub_note`'s "no inline wikilink" behavior)
    to also describe the new `## Related` regeneration, per this task's
    own Constraint that Email's `insert_body_line_if_missing`-based
    primitives are never reused for this.
  - No new imports needed — `people_extraction`, `customer_hub_linking`,
    and `vault_writer` were all already imported at this module's top
    level; `Path` was already imported too (used for `Path(person
    ["note_path"]).stem`).

No deviation from the task's own `## Starting State → End State`/`##
Files to Modify` text.

**Assumption logged for human spot-check (scope-internal judgement call,
not an escalation):** the task's own docstring text names the helper
signature as `_build_thread_related_wikilinks(path, customer,
participants, project) -> str` (a `path` parameter). Implemented instead
as `_build_thread_related_wikilinks(customer, participants, project) ->
str` — no `path` parameter — with the caller doing the
`vault_writer.replace_body_section(path, "## Related", <result>)` call
itself, exactly mirroring `ADR-046` Decision 9's own literal composition
("assembles ... written into `## Related` via `vault_writer.
replace_body_section(path, ...)`" — the ADR itself never has the assembly
helper take `path`). Keeping the helper pure (no I/O, no path argument)
is a strictly narrower, more testable shape than the task text's own
sketch and changes no observable behavior — the task file's own
Objective/`## Starting State → End State` text explicitly frames this as
"a new helper ... or composed inline," i.e. the exact function boundary
was already disclosed as implementation latitude, not a locked
requirement.

**Verification (manual mode, live against the real, configured vault,
`VAULT_PATH=<OPERATOR_VAULT_OLD>`):**

Ran `thread_match_merge` directly (not through a live Outlook pull —
mirrors `T05`/`T06`/`T07`'s own established direct-call verification
precedent for this story) against real vault fixtures: `customer="Core42"`
(a real, existing Customer — `Work/Customers/Core42/`) with sender
`ahmad.hamzeh@core42.ai`, a REAL, already-existing Person note
(`Work/People/ahmad.hamzeh@core42.ai.md`, `name: "Ahmad Hamzeh"`,
confirmed via `people_extraction.find_existing_person_note` before the
run). A disposable, clearly-synthetic `conversation_id` was used so no
real Thread was touched.

1. `[REQ-SB-69-US-01-AC-10]` First call created a brand-new Thread note.
   `## Related` read back: `"- [[Core42]]\n- [[ahmad.hamzeh@core42.ai]]"`
   — both the real Customer hub stem and the real Person stem present.
   Graph-edge check: Obsidian itself was not opened this session (no
   browser/GUI tool available, same disclosed limitation as prior tasks
   this sprint) — used the AC's own named alternative instead
   ("inspect its own graph-data cache/backlink index"): rebuilt this
   codebase's own already-shipped `vault_indexing.rebuild_index()`
   (the same case-insensitive filename-stem wikilink-matching mechanism
   Obsidian's own graph view uses) and confirmed a REAL bidirectional
   edge — the Thread's own `incoming_wikilinks` list on both the
   `Core42` hub-note index entry AND the `ahmad.hamzeh@core42.ai`
   Person-note index entry included the Thread's own stem. PASS (4/4
   assertions: both wikilinks present in `## Related`; both backlink
   edges confirmed in the real index).
   Non-AC regression: `## Summary`/`## Transcript` (both real,
   Compass-synthesized/appended this same call) read back intact and
   correctly populated — the new `## Related` section did not disturb
   either.
2. Extended step 1: set the Thread's own `project` frontmatter key
   directly to a real project name (`upsert_frontmatter_key`, mirroring
   what `finalize_thread_project_routing` would do at a real Approve),
   then ALSO created the real Project OKF directory
   (`vault_writer.create_project_directory_baseline("Core42", "T08
   Verification Project")`, the same real precondition
   `finalize_thread_project_routing` establishes before setting `project`
   in a genuine approval flow) so the graph-edge check would be faithful,
   not against a dangling target. Ran `thread_match_merge` again (a later
   message, same `conversation_id`). `## Related` read back with the
   Project link now ALSO present, alongside the unchanged Customer/Person
   links: `"- [[Core42]]\n- [[ahmad.hamzeh@core42.ai]]\n- [[T08
   Verification Project]]"`. `vault_indexing.rebuild_index()` confirmed a
   real backlink edge from the Project's own index entry back to the
   Thread too. PASS — confirms "regenerated from CURRENT state on every
   call," not a one-time snapshot.
   **Idempotency check:** re-ran `thread_match_merge` a THIRD time with
   the same later message (same `conversation_id`, same `project`). `##
   Related` re-read: still exactly 3 lines, no duplicates, no corruption
   — full regeneration via `replace_body_section` is safely idempotent
   across repeated calls with unchanged inputs. PASS.
3. `[REQ-SB-69-US-01-AC-11]` Ran `thread_match_merge` for a message with
   `classification["customer"] == "Unsorted"` and a sender email with NO
   real, existing Person note (confirmed via `person_note_exists` before
   the run: `False`). `## Related` read back: `""` — present (the header
   exists in the file, `read_body_section` found it) but genuinely empty,
   no `[[` substring anywhere in the section. PASS — an honest absence,
   never a fabricated/placeholder link (no `[[Unsorted]]`, no guessed
   name).
4. Non-AC regression check: called `create_thread_note_baseline` directly
   for a brand-new, disposable `conversation_id`. Confirmed the written
   file's raw text contains all three headers in order (`## Summary` <
   `## Transcript` < `## Related`). Confirmed `replace_body_section`/
   `read_body_section` against `## Summary` AND `## Transcript` still
   round-trip correctly with the new third section present (wrote then
   read back distinct real content for each, no boundary bleed from the
   new `## Related` section). PASS.

Every disposable Thread note (3), the disposable Project OKF directory
(4 files) and its own now-empty `projects/` parent folder created during
verification were deleted afterward; the vault's 2 pre-existing real
Thread notes (`01D26A7530444A23803A002210620160.md`,
`0C41DC9411479C4BAC82EBDDDCA753E7.md`) and `Work/Customers/Core42/`'s own
pre-existing 4 files were confirmed byte-for-byte/mtime-unchanged
afterward — the vault was fully restored to its pre-verification state.

**Status:** `Done`, `gate: flagged` — no MUST-FLAG trigger fired (no new
dependency; no shared-interface change beyond what `ADR-046` Decision 9
already specified; no deviation from `ADR-046`; no unclear/contradictory
requirement), but the one function-boundary judgement call above is a
real scope-internal assumption, logged here for human spot-check per this
project's own convention that such calls flag the task, not block it.
