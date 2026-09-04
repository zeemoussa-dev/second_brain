---
id: BUGFIX-07-US-01-T01
title: Write/backfill an identifying `# {name}` header on Customer/Project log.md and captures.md via the shared OKF-directory primitive
parent_story: BUGFIX-07-US-01
requirement_id: BUG-028
type: backend
status: Done
gate: flagged
gate_reason: "Scope-internal judgement call logged for human spot-check (not a MUST-FLAG trigger): chose not to mutate any real, already-existing Customer/Project directory during verification since no real headerless-with-content candidate exists in the live vault and touching a real content-free directory would add no marginal verification signal — see Implementation Log."
phase: MVP
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# BUGFIX-07-US-01-T01 — Write/backfill an identifying `# {name}` header on Customer/Project `log.md`/`captures.md` via the shared OKF-directory primitive

## Parent Story

- Story: [[BUGFIX-07-US-01]] — `../UserStories/BUGFIX-07-US-01-okf-directory-log-captures-identifying-header.md`
- Requirement: `BUGS.md` → `BUG-028` (bugfix story; no PRD requirement anchor)

---

## Objective

Fix `BUG-028`: `create_okf_directory_baseline`/`ensure_okf_directory_baseline`
(`src/backend/app/data_access/vault_writer.py`) gain a new `identifying_name`
parameter and one shared helper that writes `# {identifying_name}\n\n` as the
header of `log.md`/`captures.md` on first creation, and backfills the same
header onto an already-existing headerless file without disturbing any real
content already appended to it — mirroring the bare `# {name}` half of
`index.md`'s own already-`Accepted` header convention. All four Customer/
Project wrapper call sites are updated to pass the display name they already
have in local scope.

---

## Starting State → End State

**Before / Inputs:**
- `create_okf_directory_baseline` (lines ~289-314) writes
  `paths["log"].write_text("", encoding="utf-8")` and
  `paths["captures"].write_text("", encoding="utf-8")` unconditionally the
  first time each file is created (guarded only by `if not
  paths["log"].exists()` / `if not paths["captures"].exists()`) — the first
  write is a bare empty string, no header.
- `ensure_okf_directory_baseline` (lines ~317-341) has the exact same shape —
  creates a missing `log.md`/`captures.md` from scratch (still headerless),
  never retrofits a header onto one that already exists, whether genuinely
  empty or already carrying real appended content.
- Both functions take no name/display-value parameter today — only
  `directory_root`, `slug`, concept frontmatter, and `index_listing_body`
  (which already embeds `# {name}\n\n...` for `index.md`, but is not reused
  here per the architect's own mechanism decision — see Constraints).
- Four wrapper call sites already have the real display name in local scope
  and already pass it into `index_listing_body`:
  `create_customer_directory_baseline`/`ensure_customer_directory_baseline`
  (`customer`, lines ~375-388) and `create_project_directory_baseline`/
  `ensure_project_directory_baseline` (`project`, lines ~436-449).
- `create_okf_directory_baseline`'s own docstring claims "`captures.md` is
  never opened by this function beyond that one existence check" — stale
  once this ships.
- Confirmed live (full-repo grep, this pass): every real caller that ever
  appends content into an already-existing `log.md`/`captures.md` goes
  through `append_person_note_update_line` (3 real call sites:
  `project_customer_synthesizer.py` lines ~124/~264 — date-headed History
  lines, e.g. `"2026-08-19 — Project ... status changed to ..."`;
  `person_note_proposals.py` line 64 and `skill_tools.py` line 545 —
  `"- <instruction>"` bullets). None of these lines begin with `# `.

**After / Outputs:**
- `create_okf_directory_baseline(directory_root, slug, concept_frontmatter,
  identifying_name, index_listing_body="")` and
  `ensure_okf_directory_baseline(directory_root, slug,
  concept_frontmatter_defaults, identifying_name, index_listing_body="")`
  both take a new required `identifying_name: str` parameter (positioned
  before the existing `index_listing_body` default-valued parameter, so
  every call site must be updated — no silent default that could mask a
  missed call site).
- A new shared module-level helper, e.g.
  `_write_or_backfill_identifying_header(path: Path, identifying_name: str) -> None`:
  - If `path` does not exist: writes `f"# {identifying_name}\n\n"` as the
    file's full content (the fresh-creation case).
  - If `path` exists: reads its current text; if the text's first line does
    NOT start with `"# "`, prepends `f"# {identifying_name}\n\n"` to the
    existing text unchanged (the backfill case — every existing byte
    preserved, header inserted at the top). If the first line already
    starts with `"# "`, the file is left completely untouched (idempotent —
    a second `ensure_*` run on an already-fixed file is a no-op).
  - An empty existing file (`text == ""`) has no "first line starting with
    `# `" — correctly treated as headerless and gets the header written.
- Both `create_okf_directory_baseline` and `ensure_okf_directory_baseline`
  call this same helper for both `paths["log"]` and `paths["captures"]`,
  replacing their existing bare `write_text("", ...)` fresh-creation calls
  AND adding the previously-absent backfill call for the already-exists
  case.
- All four wrapper functions
  (`create_customer_directory_baseline`/`ensure_customer_directory_baseline`/
  `create_project_directory_baseline`/`ensure_project_directory_baseline`)
  pass `identifying_name=customer` / `identifying_name=project` respectively
  — the same real display-name value already passed into `index_listing_body`
  today, not a new/differently-derived value.
- `create_okf_directory_baseline`'s docstring sentence about never opening
  `captures.md` beyond an existence check is corrected to reflect that it now
  reads/writes `captures.md`'s header content — worded so it's clear the
  `<slug>.md`-regeneration-isolation guarantee (`ADR-042` Decision point 1)
  is unchanged; only the stale claim itself is corrected.
- `log.md`/`captures.md` remain excluded from `vault_indexing`/
  `list_all_note_paths()` — no change to any indexing/search/backlink
  surface.

---

## Files to Modify

- `src/backend/app/data_access/vault_writer.py`:
  1. Add the new `_write_or_backfill_identifying_header` helper (placed
     near `create_okf_directory_baseline`/`ensure_okf_directory_baseline`).
  2. Update `create_okf_directory_baseline`'s signature (add
     `identifying_name: str` before `index_listing_body: str = ""`) and body
     (replace the two `write_text("", ...)` fresh-creation calls on
     `paths["log"]`/`paths["captures"]` with calls to the new helper).
  3. Update `create_okf_directory_baseline`'s docstring — correct the stale
     "`captures.md` is never opened by this function beyond that one
     existence check" sentence to reflect the new header write, while
     preserving the sentence's original point (isolation from `<slug>.md`
     regeneration is unaffected).
  4. Update `ensure_okf_directory_baseline`'s signature (add
     `identifying_name: str` before `index_listing_body: str = ""`) and body
     (replace the two `write_text("", ...)` fresh-creation-only calls with
     calls to the new helper, so both the fresh-creation and backfill cases
     are covered on the top-up path too).
  5. Update `create_customer_directory_baseline` (pass
     `identifying_name=customer`), `ensure_customer_directory_baseline`
     (pass `identifying_name=customer`), `create_project_directory_baseline`
     (pass `identifying_name=project`), `ensure_project_directory_baseline`
     (pass `identifying_name=project`) — their four call sites into
     `create_okf_directory_baseline`/`ensure_okf_directory_baseline`.

No other file is in scope.

---

## Constraints

- Inherits from parent story — fix lives in the shared primitive only
  (`create_okf_directory_baseline`/`ensure_okf_directory_baseline`), never
  duplicated separately into the Customer/Project wrapper functions; both
  kinds are fixed by the same change, per `ADR-042`'s existing shared shape.
- `identifying_name` is a new explicit parameter, NOT a parse of
  `index_listing_body`'s own first line — do not derive it by string-parsing
  `index_listing_body`.
- Header content is exactly `# {identifying_name}\n\n` — the bare `# {name}`
  half of `index.md`'s own convention only. No trailing wikilink-listing
  line. No `— Log`/`— Captures` differentiating suffix.
- The ONE shared helper must serve both the fresh-creation case (in
  `create_okf_directory_baseline`) and the backfill case (in
  `ensure_okf_directory_baseline`, and also reachable from `create_okf_
  directory_baseline` itself since its own `if not paths["log"].exists()`
  guard means a repeat call after a partial/interrupted prior run could
  still hit an already-existing-but-headerless file) — do not write two
  separate header-writing code paths.
- Headerless-detection rule is exactly: the file's current first line does
  not start with `"# "`. Do not use a different heuristic (e.g. "file is
  empty").
- The retrofit must never disturb already-appended real content — insertion
  (prepend), never replacement, of the file's pre-existing body. An
  already-headered file must be left byte-for-byte untouched (idempotent).
- Must NOT add `log.md`/`captures.md` to `list_all_note_paths()` or any
  indexing/search/backlink surface.
- Must NOT change `index.md`'s own header/listing behaviour, or
  `append_person_note_update_line`'s own append contract.
- Must NOT touch `move_okf_directory`, `okf_directory_paths`, or any other
  OKF-directory primitive not named above.

---

## Tests

**Manual verification steps (direct Python-shell calls against the real
data_access functions, using a throwaway directory under the real,
configured vault's `Work/` tree — created and cleaned up by the
verification itself; no fixture/mock filesystem):**

1. [BUGFIX-07-US-01-AC-01] Call `create_customer_directory_baseline` with a
   new, throwaway Customer name that does not yet exist in the real vault.
   Read the resulting `log.md` and `captures.md` directly — confirm each
   file's content is exactly `# {customer}\n\n` (header present, otherwise
   empty). Repeat with `create_project_directory_baseline` for a throwaway
   Project under that same throwaway Customer — confirm its `log.md`/
   `captures.md` are exactly `# {project}\n\n`.
2. [BUGFIX-07-US-01-AC-02] Using the throwaway Customer directory from step
   1, directly write a real, disclosed line into its `log.md` that mimics
   `append_person_note_update_line`'s own real output shape (e.g. a
   date-headed History line and/or a `"- <instruction>"` bullet), with NO
   header — i.e. simulate the pre-fix, already-existing, headerless-with-
   real-content state. Also leave `captures.md` genuinely empty (no
   header). Then re-run `ensure_customer_directory_baseline` against the
   same Customer. Read both files back — confirm `log.md` now starts with
   `# {customer}\n\n` followed immediately by the exact real line written
   before the run (byte-for-byte preserved, not reordered or duplicated),
   and `captures.md` now reads exactly `# {customer}\n\n`.
3. [BUGFIX-07-US-01-AC-02] Re-run `ensure_customer_directory_baseline` a
   second time against the same now-headered Customer directory — confirm
   `log.md`/`captures.md` are byte-for-byte unchanged from step 2's result
   (idempotent, header not duplicated, no content disturbed).
4. [BUGFIX-07-US-01-AC-02] If at least one real, already-existing Customer
   folder in the live vault has a `log.md` that already carries real
   appended content with no header (pre-fix state), run
   `ensure_customer_directory_baseline` against it directly, and confirm
   the same outcome as step 2 against that real data — the header is
   prepended and every pre-existing real line is preserved byte-for-byte.
   Disclose in the Implementation Log whether a real pre-fix candidate was
   found and used, or whether this facet was covered only by the synthetic
   throwaway directory in steps 2/3.
5. Clean up: remove the throwaway Customer/Project directories created for
   steps 1-3 (or leave them clearly marked as test artefacts if vault
   deletion is out of scope for this task — disclose the choice made).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `create_okf_directory_baseline`/`ensure_okf_directory_baseline` both
      take a new `identifying_name: str` parameter and write/backfill
      `# {identifying_name}\n\n` on `log.md`/`captures.md` via one shared
      helper
- [x] Fresh creation (Scenario 1 / `BUGFIX-07-US-01-AC-01`): a newly-created
      Customer or Project directory's `log.md`/`captures.md` open with the
      identifying header, otherwise empty
- [x] Backfill (Scenario 2 / `BUGFIX-07-US-01-AC-02`): re-running `ensure_*`
      against an already-existing, pre-fix, headerless directory adds the
      header to `log.md`/`captures.md` without disturbing any already-
      appended real content; an already-headered file is left untouched
- [x] All four Customer/Project wrapper call sites pass their own real
      display name as `identifying_name`
- [x] `create_okf_directory_baseline`'s docstring no longer claims it never
      opens `captures.md` beyond an existence check
- [x] `log.md`/`captures.md` remain excluded from `vault_indexing`
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Adding `log.md`/`captures.md` to `vault_indexing`/search/backlinks.
- Any change to `index.md`'s own header/listing behaviour.
- Any change to `append_person_note_update_line`'s own append contract.
- Retrofitting `move_okf_directory`, `okf_directory_paths`, or any other
  OKF-directory primitive not named in `## Files to Modify`.
- Any UI change — confirmed no screen is affected (`BUG-028`'s own
  "Screen \ route: N/A").
- Bulk-backfilling every real existing Customer/Project directory in the
  live vault as part of this task — this task fixes the primitive; a
  vault-wide backfill happens naturally the next time each directory's own
  `ensure_*` path runs (e.g. via `REQ-SB-74`'s backfill pass), not as a
  one-off script here unless step 4 of `## Tests` finds it convenient to
  exercise one real pre-existing directory for verification.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "Vault
Knowledge Model Redesign — Threads, Manual Captures, OKF-Conformant
Customer & Project Directories" → `BUGFIX-07-US-01` correction bullet
(architect's pass, 2026-08-19). No ADR created or changed — this reuses the
already-`Accepted` `# {name}` header convention verbatim and does not touch
the 4-file OKF directory shape, `ADR-004`'s folder/tag boundary, or
`ADR-042`'s captures.md-isolation-from-`<slug>.md`-regeneration guarantee.

---

## Implementation Log

**Coder pass, 2026-08-19.** Implemented exactly as specced in `## Files to
Modify`:

- Added `_write_or_backfill_identifying_header(path: Path, identifying_name:
  str) -> None` (new module-level helper, placed immediately before
  `create_okf_directory_baseline`). Fresh-creation branch (`path` does not
  exist): writes `f"# {identifying_name}\n\n"` as the file's full content.
  Backfill branch (`path` exists): reads current text, checks
  `text.split("\n", 1)[0].startswith("# ")` — if not headerless, prepends the
  header to the existing text unchanged; if already headered, returns without
  writing (idempotent, byte-for-byte untouched).
- `create_okf_directory_baseline` gained `identifying_name: str` (positioned
  before `index_listing_body: str = ""`) and now calls the shared helper for
  both `paths["log"]`/`paths["captures"]`, replacing the two bare
  `write_text("", ...)` calls.
- `ensure_okf_directory_baseline` gained the same new parameter in the same
  position and calls the same shared helper for both files, replacing its own
  two `write_text("", ...)`-on-missing-only calls — this is what adds the
  previously-absent backfill behaviour to the top-up path.
- All four wrapper call sites updated: `create_customer_directory_baseline`/
  `ensure_customer_directory_baseline` now pass `identifying_name=customer`;
  `create_project_directory_baseline`/`ensure_project_directory_baseline` now
  pass `identifying_name=project` — the same display-name value each already
  passes into `index_listing_body`.
- `create_okf_directory_baseline`'s docstring corrected: the stale
  "`captures.md` is never opened by this function beyond that one existence
  check" sentence is replaced with wording describing the new header
  write/backfill via `_write_or_backfill_identifying_header`, while
  preserving the original point that no `<slug>.md`-regeneration code path
  can reach `captures.md`'s body content (`ADR-042` Scenario 2/3 guarantee
  unaffected).
- Confirmed (grep, this pass) `create_okf_directory_baseline`/
  `ensure_okf_directory_baseline` have exactly the four real callers named
  above, all in `vault_writer.py` itself — no other file in the codebase
  calls either function directly, so no out-of-scope call site existed to
  update or break.
- `list_all_note_paths()`/`_OKF_RESERVED_FILENAMES` untouched — confirmed by
  direct reading, unaffected by this change; `log.md`/`captures.md` remain
  excluded from `vault_indexing`.

**Verification — manual mode, direct Python-shell calls against the real
`app.data_access.vault_writer` functions, run via the backend's own `.venv`
(`src/backend/.venv/Scripts/python.exe`) against the real, configured
`VAULT_PATH` (`<OPERATOR_VAULT_OLD>`), using a throwaway
`ZZ-Verify-BUGFIX-07-Throwaway-Customer`/`...-Project` pair under `Work/
Customers/`, created and removed by the verification script itself:**

- **`BUGFIX-07-US-01-AC-01` — PASS.** `create_customer_directory_baseline`
  against the new throwaway Customer name produced `log.md` and `captures.md`
  each reading exactly `'# ZZ-Verify-BUGFIX-07-Throwaway-Customer\n\n'`
  (confirmed via `repr()` equality check against the expected string).
  `create_project_directory_baseline` against a throwaway Project nested
  under that same Customer produced `log.md`/`captures.md` each reading
  exactly `'# ZZ-Verify-BUGFIX-07-Throwaway-Project\n\n'`. Both file pairs
  otherwise empty beneath the header, as required.
- **`BUGFIX-07-US-01-AC-02` — PASS.** Reset the throwaway Customer's
  `log.md` to a headerless state and appended two real-shaped lines via the
  real `append_person_note_update_line` (a date-headed History line
  mirroring `project_customer_synthesizer.py`'s own output, and a
  `"- <instruction>"` bullet mirroring `person_note_proposals.py`'s/
  `skill_tools.py`'s own output) — pre-run content:
  `'\n2026-08-19 — Project ZZ-Verify status changed to active\n- Confirm
  with the customer before next check-in\n'`. Left `captures.md` genuinely
  empty (headerless). Ran `ensure_customer_directory_baseline` — `log.md`
  read back as exactly `header + pre_run_content`, byte-for-byte (verified
  by string equality, not just visual inspection), and `captures.md` read
  back as exactly the bare header. Re-ran `ensure_customer_directory_baseline`
  a second time against the same, now-headered directory — both files
  confirmed byte-for-byte unchanged from the first run's result (idempotent,
  no duplication).
  - **Real pre-existing-directory facet, disclosed:** read (never wrote)
    every one of the 26 real Customer folders' `log.md`/`captures.md` under
    `Work/Customers/` in the live vault, plus the one real Project directory
    found (`Unsorted/projects/Azure Demo Account Request/`) — every single
    one of these real files is confirmed genuinely empty (0 bytes), i.e. no
    real, already-existing Customer or Project folder in the live vault
    currently has any real appended content in `log.md`/`captures.md` to
    exercise the byte-preservation facet against. Per the task's own
    disclosure instruction: **no real pre-fix headerless-with-real-content
    candidate was found; this facet (content preservation specifically) was
    covered only by the synthetic throwaway directory above.** Deliberately
    did not run `ensure_*` against a real, content-free Customer folder just
    to touch production data, since (a) it would add no verification value
    beyond what the synthetic empty-`captures.md` check in the same run
    already covers (an empty file gaining a bare header), and (b) the
    story's own Out-of-Scope note reserves bulk/individual real-directory
    backfilling for `REQ-SB-74`'s own backfill pass, only sanctioning a real
    directory touch here if "convenient" for verification — it was not,
    given zero marginal signal.
- Cleanup (Test step 5): the throwaway Customer directory (which contains
  the throwaway Project as a nested `projects/` subdirectory) was removed
  via `shutil.rmtree` at the end of the verification script; confirmed
  `exists() == False` immediately after, and re-confirmed via a directory
  listing that no `ZZ-Verify-*` directory remains under `Work/Customers/`.
  No real vault data was deleted or altered by this task.

**Assumption logged for spot-check (scope-internal judgement call, not an
escalation):** chose not to mutate any real, already-existing Customer/
Project directory as part of verification, per the reasoning above — flagged
here for human spot-check rather than filed as an `ESCALATIONS.md`/
`REVIEW-QUEUE.md` entry, since it is a verification-approach choice within
this task's own explicitly discretionary "if convenient" allowance, not a
scope, interface, or requirement question.

No deviation from the task's `## Files to Modify`/`## Constraints`. Both
locked ACs verified and passing.
