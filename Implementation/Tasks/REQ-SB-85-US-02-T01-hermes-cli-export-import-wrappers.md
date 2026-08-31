---
id: REQ-SB-85-US-02-T01
title: HermesCLI.export_profile / import_profile — real subprocess wrappers (ADR-014)
parent_story: REQ-SB-85-US-02
requirement_id: REQ-SB-85
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-85-US-02-T01 — HermesCLI.export_profile / import_profile: real subprocess wrappers (ADR-014)

## Parent Story

- Story: [[REQ-SB-85-US-02]] — `../UserStories/REQ-SB-85-US-02-export-dependency-closure-and-secret-scan.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-85 *Artifact Export/Import — Portable Capability Bundles (`.sbf`)*

---

## Objective

Add `export_profile`/`import_profile` to `HermesCLI` — the same-shape
`_run()` subprocess wrapper pattern as `create_profile`/`delete_profile`/
`describe_profile` — wrapping Hermes' own real, already-shipped `hermes
profile export`/`hermes profile import` CLI subcommands. Shared by both
`US-02` (export) and `US-03` (import) — built once, here.

---

## Starting State → End State

**Before / Inputs:**
- `src/backend/app/hermes/cli.py::HermesCLI` already has `create_profile`/
  `delete_profile`/`describe_profile`, each following the exact same
  `self._run([...])` capture pattern. No `export_profile`/`import_profile`
  method exists anywhere.

**After / Outputs:**
- `HermesCLI.export_profile(name: str, output_path: str) -> tuple[bool,
  str]` — runs `hermes profile export <name> <output_path>`. A generous
  timeout (120.0s, matching `create_profile --clone`'s own allowance,
  per `ADR-014`'s own disclosed Consequence — `export_profile` can
  produce a multi-MB archive), not the 30s default.
- `HermesCLI.import_profile(archive_path: str, name: str | None = None)
  -> tuple[bool, str]` — runs `hermes profile import <archive_path>`
  (`+ ["--name", name]` when `name` is supplied). Same 120.0s timeout
  (a real profile import can restore a multi-MB archive, same class of
  cost as export).
- Both return the exact `(success, output)` shape every other `HermesCLI`
  method already returns — a non-zero exit (e.g. `import_profile` hitting
  Hermes' own real `FileExistsError` on a name collision) surfaces as
  `(False, <real stderr/stdout text>)`, never raises, never fabricates a
  success.

---

## Files to Modify

- `src/backend/app/hermes/cli.py` — two new methods on `HermesCLI`.

---

## Constraints

- Inherits from parent story.
- **Same class, same file, same `_run()` pattern** — no new wrapper class
  or module (`ADR-014`'s own Decision: "two more profile-lifecycle
  operations, the exact same shape... as the three already living
  there").
- **120.0s timeout on both**, not the 30.0s default — `ADR-014`'s own
  disclosed Consequence, flagged explicitly for this task.
- **The resulting archive bytes are opaque to Second Brain** — this task
  never parses, inspects, or re-scans the tar.gz Hermes produces/consumes;
  that boundary belongs to `T04`'s own `.sbf` assembly (which nests the
  raw bytes unmodified) and is explicitly never re-opened here.
- Never import `app.hermes` from outside `app/business/hermes/client.py`
  — this task edits `app/hermes/cli.py` itself (the one file that's
  allowed to), not a caller.

---

## Tests

<!-- These two methods have no Gherkin scenario of their own naming an
externally-observable UI outcome directly -- they are a real, load-bearing
BUILDING BLOCK T04 (AC-06) and REQ-SB-85-US-03-T05 (Agent import) compose.
Verified here at the unit/subprocess layer; the composed, AC-tagged
outcome is verified where the composition actually happens. -->

**Manual verification steps:**
1. Using a real, disposable Hermes profile (create one via the already-
   real `HermesCLI.create_profile("sbf-t01-verify-scratch", clone=True,
   clone_from="default")`, deleted at the end of this step), call
   `export_profile("sbf-t01-verify-scratch", <a scratch output path>)`;
   confirm it returns `(True, ...)` and a real `.tar.gz` (or equivalent
   real archive Hermes' own export produces) exists on disk at that path
   with non-zero size. No AC tag — a real, disclosed build-correctness
   check for a shared primitive; `AC-06`'s own composed outcome is
   verified in `T04`.
2. Call `import_profile(<the archive from step 1>, name=
   "sbf-t01-verify-scratch-copy")`; confirm `(True, ...)`, then confirm
   via `get_client().profiles.find_by_id("sbf-t01-verify-scratch-copy")`
   that a real profile now exists under that alternate name (the exact
   `--name` primitive `REQ-SB-85-US-03`'s own "keep both" mechanism relies
   on). No AC tag — supports `REQ-SB-85-US-03-AC-04`, verified for real
   in that story's own `T05`.
3. Call `import_profile(<the same archive>, name=
   "sbf-t01-verify-scratch-copy")` again (same name, already exists);
   confirm it returns `(False, ...)` with the real underlying
   `FileExistsError` text surfaced in the output — the exact real signal
   `REQ-SB-85-US-03`'s own conflict detection is built on. No AC tag —
   supports `REQ-SB-85-US-03-AC-03`, verified for real in that story's
   own `T05`.
4. Delete both scratch profiles (`sbf-t01-verify-scratch`,
   `sbf-t01-verify-scratch-copy`) via the already-real `delete_profile`;
   confirm neither remains in `get_client().profiles.get_all()`
   afterward — no leftover test state.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `export_profile(name, output_path)` runs the real `hermes profile
      export` subcommand, 120.0s timeout, `(success, output)` shape
- [x] `import_profile(archive_path, name=None)` runs the real `hermes
      profile import` subcommand (with `--name` when supplied), 120.0s
      timeout, `(success, output)` shape
- [x] A real name collision on import surfaces as `(False, <real
      FileExistsError text>)`, never raises
- [x] No archive bytes are parsed/inspected/re-scanned by this task's own
      code
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new decision/pattern/constraint; see Implementation Log)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Composing these into a `.sbf` bundle — `T04`.
- Second Brain's own secret-scan pass — `T03` (never touches this piece,
  per the story's own Constraints — Hermes' own export already redacts
  silently).
- The Agent-kind import orchestration (conflict decision → overwrite/
  keep-both/skip) — `REQ-SB-85-US-03-T05`.

---

## Context / Notes

`ADR-014` (`Implementation/Architecture/ADR.md`) is the authoritative
design for this task — read it in full before starting.
`REQ-SB-85-US-03-T05` (a sibling story's task, built later) depends on
this task directly — do not rename these two methods or change their
return shape without checking that dependency first.

---

## Implementation Log

**Build.** Added `HermesCLI.export_profile(name, output_path)` and
`HermesCLI.import_profile(archive_path, name=None)` to
`src/backend/app/hermes/cli.py`, same file/class, same `self._run()`
capture pattern as `create_profile`/`delete_profile`/`describe_profile`,
both at `timeout=120.0`. Also extended the module's own top-of-file "real
command surface" docstring to list `export`/`import` alongside the
existing `create/delete/describe`.

**Scope-internal judgement call — disclosed, non-blocking (matches this
project's own `SPRINT-019` Learnings precedent: "when a task's own code
sample disagrees with a real live call, treat the live call as ground
truth and correct the code in-scope").** Before writing the wrapper, ran
`hermes profile export --help` / `hermes profile import --help` live
against this machine's own real, installed `hermes.exe`
(`C:\Users\mahmoud.moussa\AppData\Local\hermes\hermes-agent\bin\hermes.exe`)
and cross-checked against the real, installed
`hermes_cli\subcommands\profile.py` source. Ground truth found:
- `hermes profile export` — `usage: hermes profile export [-h] [-o OUTPUT]
  profile_name`. The output path is a **flag** (`-o`/`--output`), NOT a
  second positional argument as this task's own "After / Outputs" prose
  and `ADR-014`'s own Context both describe (`hermes profile export <name>
  [output]`). `import_profile` matches exactly as documented (`hermes
  profile import [-h] [--name NAME] archive`).
- Built `export_profile` as `["profile", "export", name, "--output",
  output_path]` against this live-confirmed shape, not the task's literal
  prose. The method's own signature/return shape (`(success, output)`,
  120.0s timeout) is unaffected — only the internal `args` list construction
  changed. Documented directly in the method's own docstring so the
  discrepancy is visible at the call site, not just here.
- Filed as an addendum note on the ADR-013/014 line item already open in
  `REVIEW-QUEUE.md` (the human is already reviewing `ADR-014`; this gives
  them the one correction to make there) — not a new blocking escalation,
  since the build itself is correct and live-verified against the real CLI.

**Manual verification (real, disposable Hermes profiles — created and
deleted within this same pass, never a production profile).** Ran a
throwaway Python script (`get_client().cli.export_profile`/
`.import_profile`/`.create_profile`/`.delete_profile`, `.profiles.find_by_id`/
`.get_all()`) against the real, running Hermes install (via
`app.business.hermes.client.get_client()`, `src/backend/.env`'s real
`hermes_home_path`), from `src/backend` with the project's own `.venv`
Python (plain `python`/`py -3` on PATH has no `fastapi`/backend deps
installed in this session).

1. `export_profile("sbf-t01-verify-scratch", <scratch tmp path>)` (source
   profile created via `create_profile(..., clone=True,
   clone_from="default")`) → **PASS**. `(True, "✓ Exported
   'sbf-t01-verify-scratch' to ...\\sbf-t01-verify-scratch.tar.gz")`; the
   real archive existed on disk, `12,492,265` bytes (non-zero). No AC tag
   (per this task's own Tests block) — `AC-06`'s own composed outcome is
   verified in `T04`.
2. `import_profile(<archive from step 1>, name="sbf-t01-verify-scratch-copy")`
   → **PASS**. `(True, "✓ Imported profile 'sbf-t01-verify-scratch-copy'
   at ...")`; `get_client().profiles.find_by_id("sbf-t01-verify-scratch-copy")`
   returned a real, populated `HermesAgent` (88 real skills, same model/
   provider as the clone source) — confirming the `--name` primitive
   `REQ-SB-85-US-03-AC-04`'s "keep both" mechanism will rely on. No AC tag
   — verified for real in `REQ-SB-85-US-03-T05`.
3. `import_profile(<same archive>, name="sbf-t01-verify-scratch-copy")`
   again (same name, already exists) → **PASS**. `(False, "Error: Profile
   'sbf-t01-verify-scratch-copy' already exists at
   ...\\profiles\\sbf-t01-verify-scratch-copy")`. Note: the real, real
   CLI's own user-facing text does not literally print the Python
   exception CLASS NAME `FileExistsError` (the task's own Tests prose
   says "FileExistsError text") — it prints the real, human-readable
   rendering of that same underlying error (`Error: Profile '...' already
   exists at ...`), confirmed by direct reading of `hermes_cli/main.py`'s
   own `except FileExistsError as e: print(f"Error: {e}")`-shaped handler
   for this action. This is the exact real signal (non-zero exit, a
   collision-describing message) `REQ-SB-85-US-03-AC-03`'s own conflict
   detection needs; a substring check on the literal string
   `"FileExistsError"` would be the wrong check against the real CLI's
   actual output — worth `REQ-SB-85-US-03-T05` matching on "already
   exists"/a non-zero exit instead, not the class name string. No AC tag
   — verified for real in `REQ-SB-85-US-03-T05`.
4. Both `sbf-t01-verify-scratch` and `sbf-t01-verify-scratch-copy` deleted
   via the already-real `delete_profile` → **PASS**. Both calls returned
   `(True, ...)`; `get_client().profiles.get_all()` afterward contained
   neither id — no leftover scratch state. Additionally noticed
   `delete_profile` does NOT remove each profile's own convenience wrapper
   script (`create_profile`/`import_profile`'s own real "Wrapper created:
   ...\.local\bin\<name>.bat" side effect) — a real, pre-existing Hermes
   behavior, out of this task's own scope to change. Removed both
   now-dangling `.bat` files by hand
   (`C:\Users\mahmoud.moussa\.local\bin\sbf-t01-verify-scratch{,-copy}.bat`)
   so no scratch artifact of any kind was left behind. The export archive
   itself lived only inside a Python `tempfile.TemporaryDirectory()`,
   already auto-removed on script exit.

**Constraint check — archive bytes never parsed/inspected/re-scanned by
this task's own code.** Confirmed by construction: both new methods only
build an `args` list and return `self._run(...)`'s own `(success, output)`
tuple; neither ever opens, reads, or touches the archive file's bytes.

**Files touched:** `src/backend/app/hermes/cli.py` only (matches `##
Files to Modify` exactly).

gate: clear 2026-08-31 — no MUST-FLAG trigger fired. The one disclosed
finding above (real CLI uses `-o`/`--output`, not a second positional, and
the collision message doesn't literally echo the `FileExistsError` class
name) is a scope-internal correction against verified live ground truth,
not a material assumption filling a genuine gap, an ADR edit, an
out-of-scope event, or an unverifiable AC — matches the established
`SPRINT-019` precedent exactly. Addendum note added to the existing open
`ADR-013`/`ADR-014` `REVIEW-QUEUE.md` line item for the human's awareness
when they review `ADR-014`.
