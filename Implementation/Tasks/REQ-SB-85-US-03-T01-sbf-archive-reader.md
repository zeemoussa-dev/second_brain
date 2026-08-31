---
id: REQ-SB-85-US-03-T01
title: sbf_archive.py reader — real .sbf parsing + malformed-archive rejection (ADR-013)
parent_story: REQ-SB-85-US-03
requirement_id: REQ-SB-85
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-85-US-02-T04]
created: 2026-08-31
updated: 2026-09-01
---

# REQ-SB-85-US-03-T01 — sbf_archive.py reader: real .sbf parsing + malformed-archive rejection (ADR-013)

## Parent Story

- Story: [[REQ-SB-85-US-03]] — `../UserStories/REQ-SB-85-US-03-import-conflict-resolution-and-provisioning.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-85 *Artifact Export/Import — Portable Capability Bundles (`.sbf`)*

---

## Objective

Add the reader half of `sbf_archive.py` (the writer half,
`REQ-SB-85-US-02-T04`, already exists in the same file) — parses a real
uploaded `.sbf` into its manifest + real per-payload-path bytes, and
rejects a malformed archive cleanly, never partially.

---

## Starting State → End State

**Before / Inputs:**
- `app/business/logic/sbf_archive.py` exists with `write_archive(...)`
  (`REQ-SB-85-US-02-T04`) — a real zip: `manifest.json` plus per-kind
  payload paths (`skills/`, `templates/`, `pipelines/`, `agents/`,
  `seed_data/`). No reader exists yet.

**After / Outputs:**
- `sbf_archive.py` gains:
  - `class MalformedBundleError(Exception)` — the dedicated error type for
    every real rejection path below.
  - `read_archive(archive_path: str) -> tuple[dict, dict[str, bytes]]` —
    opens the file as a real zip (`zipfile.ZipFile`, `zipfile.BadZipFile`
    caught and re-raised as `MalformedBundleError`), reads `manifest.json`
    (missing → `MalformedBundleError`; present but not valid JSON →
    `MalformedBundleError`, chained `from`), validates the manifest has
    the required top-level keys (`format_version`, `generated_at`,
    `artifacts`, `secret_scan` — any missing → `MalformedBundleError`
    naming which key), then reads every OTHER real member in the zip into
    an in-memory `{member_path: bytes}` dict. Returns
    `(manifest_dict, payload_bytes_dict)` on success — never a partial
    result on any failure path (any raise happens before returning
    anything).
  - `format_version` mismatch (a value other than the one `write_archive`
    currently produces) is NOT treated as fatal for this task — logged/
    surfaced as a field on the returned manifest for a caller to decide
    (forward-compat framing per `ADR-013`'s own "this ADR's own layout is
    the extension point" Consequences note); only a structurally broken
    archive (bad zip, missing/unparsable manifest, missing required keys)
    raises `MalformedBundleError`.

---

## Files to Modify

- `src/backend/app/business/logic/sbf_archive.py` (existing file, adds
  the reader half alongside the already-`Done` writer).

---

## Constraints

- Inherits from parent story.
- **Never partially deploys or partially trusts a malformed archive** —
  every validation happens before any byte is returned to a caller; a
  caller either gets a fully-parsed, structurally-valid result or a
  `MalformedBundleError`, never something in between.
- **Pure parsing — no deployment, no conflict detection, no write of any
  kind.** This function never touches any real Manager or the target
  machine's own current state.
- Reuses the exact same manifest shape `write_archive` already produces —
  no schema drift between the two halves of this one shared module.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-85-US-03-AC-01]` Produce a real `.sbf` via
   `REQ-SB-85-US-02`'s own already-`Done` `commit_export` (a real
   selection covering at least one artifact of each of the 4 kinds, if
   available); call `read_archive(...)` on it; confirm the returned
   manifest's `artifacts` list matches exactly what was exported (same
   kinds/ids/`included_reason`), and that the payload dict contains a
   real, non-empty entry for every real payload path the writer produced
   (`skills/.../SKILL.md`, `templates/.../Template.json`,
   `pipelines/....json`, `agents/.../profile.tar.gz` +
   `agents/.../Agent.json`).
2. `[REQ-SB-85-US-03-AC-08]` Call `read_archive(...)` on a plain, non-zip
   text file; confirm `MalformedBundleError` is raised (not a bare
   `zipfile.BadZipFile`, not a silent empty result).
3. `[REQ-SB-85-US-03-AC-08]` Build a real, well-formed zip that has NO
   `manifest.json` member at all; call `read_archive(...)`; confirm
   `MalformedBundleError` is raised naming the missing manifest.
4. `[REQ-SB-85-US-03-AC-08]` Build a real zip with a `manifest.json`
   member whose content is not valid JSON (e.g. truncated/garbled text);
   confirm `MalformedBundleError` is raised, chained from the real
   underlying JSON-decode error.
5. Build a real zip with a syntactically-valid `manifest.json` that is
   missing one required key (e.g. no `artifacts` key); confirm
   `MalformedBundleError` names the missing key (no AC tag — supports the
   "never partially trusts" Constraint with a case distinct from steps
   2-4).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `read_archive` returns the real, complete manifest + payload bytes
      for a well-formed `.sbf` produced by `REQ-SB-85-US-02`'s own writer
- [x] A non-zip file, a zip with no manifest, a zip with unparsable
      manifest JSON, and a zip with missing required manifest keys all
      raise `MalformedBundleError`, never a partial result
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Conflict detection against the target machine's own current state — `T02`.
- Actually deploying anything — `T05`.
- The upload/preview UI — `T06`.

---

## Context / Notes

`ADR-013` (`Implementation/Architecture/ADR.md`), architecture
`§Dependency Closure, Secret Scan & .sbf Archive Format`, are the
authoritative design for this task — this reader is the "consumer, not
author, of the format" the story's own architect-pass Notes describe.

---

## Implementation Log

**Build summary:** `app/business/logic/sbf_archive.py` gains the reader
half alongside the already-`Done` writer (`REQ-SB-85-US-02-T04`) — new
`MalformedBundleError` exception and `read_archive(archive_path: str) ->
tuple[dict, dict[str, bytes]]`. Opens the file via `zipfile.ZipFile`
(`zipfile.BadZipFile` caught, re-raised as `MalformedBundleError`), reads
`manifest.json` (`KeyError` on a missing member → `MalformedBundleError`),
parses it (`json.JSONDecodeError` → `MalformedBundleError`, chained
`from`), validates all four required top-level keys
(`format_version`/`generated_at`/`artifacts`/`secret_scan` — the exact
same set `write_archive`'s own callers already produce, per `ADR-013`),
then reads every other real, non-directory zip member into an in-memory
`{member_path: bytes}` dict. Every raise happens strictly before any
`return` — no partial result on any failure path. A `format_version`
mismatch alone is deliberately not validated/raised here, matching the
task's own Objective (forward-compat framing, `ADR-013`'s "this ADR's own
layout is the extension point" Consequences note) — left as a field on
the returned manifest for a future caller to interpret. No other file
touched; pure parsing only — no deployment, no conflict detection, no
write of any kind, confirmed by direct reading of the final diff (only
`import json`/`zipfile` used, no Manager/filesystem-write call anywhere in
the new function).

**Scope-internal judgement calls (logged for human spot-check, non-blocking):**
- Skipped zip members where `ZipInfo.is_dir()` is true, in addition to
  skipping `manifest.json` itself, when building the payload dict — the
  real writer (`write_archive`) never creates directory entries (plain
  `archive.writestr(member_path, content)` per member), so this never
  fires against a genuine `write_archive`-produced `.sbf`; added purely as
  defensive robustness against a hand-built or third-party-zip-tool-built
  archive (e.g. one produced by a filesystem-recursive zip write) that
  might include folder entries — never changes behavior for any real
  bundle this system itself produces.
- The malformed-archive error messages name the archive path and, for the
  missing-key case, the specific missing key — not literally prescribed by
  the task text beyond "naming which key," but the most direct way to
  satisfy that wording; no behavior beyond message content is affected.

**Verification (manual mode) — real, live round trip against the real,
already-configured vault/Hermes install (`VAULT_PATH`), no mocks — a
throwaway script (`registry_loader.boot()` awaited first so the real
Agent Registry is populated, matching what the app's own lifespan does at
startup) drove every scenario below, output captured, not re-transcribed
from memory:**

- `[REQ-SB-85-US-03-AC-01]`: called `artifact_export.commit_export(...)`
  (`REQ-SB-85-US-02-T04`'s own already-`Done` writer path) with a real
  selection covering all 4 kinds (`skill: capture-notes`, `template:
  note`, `pipeline: company-discovery`, `agent: azure-expert`) — produced
  a real `.sbf`. Independently re-opened that same file with a raw
  `zipfile.ZipFile` to capture the writer's own ground-truth
  manifest/member list, then called `read_archive(...)` on it. Result:
  `manifest["artifacts"]` byte-for-byte matched the raw zip's own
  `manifest.json` (`kind`/`id`/`included_reason`/`depends_via`/`category`
  all present, all 4 kinds represented); `payload` keys exactly matched
  the raw zip's own non-`manifest.json` member set (49 members); every
  payload entry was non-empty EXCEPT `seed_data/Settings/Entities.md`
  (0 bytes) — correct and expected, since the writer forces every seed/
  blank-data entry empty by design (`ADR-013` Scenario 4/5), not a defect
  in the reader; real non-empty entries confirmed present for every kind
  named in the AC (`skills/capture-notes/SKILL.md`,
  `templates/note/Template.json`, `pipelines/company-discovery.json`,
  `agents/azure-expert/profile.tar.gz` + `agents/azure-expert/Agent.json`).
  **PASS.**
- `[REQ-SB-85-US-03-AC-08]` (non-zip file): called `read_archive(...)` on
  a real plain text file (`.sbf` extension, plain-text content, not a zip
  at all) — raised `MalformedBundleError` naming the file path and "is not
  a valid zip archive"; not a bare `zipfile.BadZipFile`, no partial
  result. **PASS.**
- `[REQ-SB-85-US-03-AC-08]` (well-formed zip, no `manifest.json`): built a
  real zip via `zipfile.ZipFile(..., "w")` containing only
  `skills/foo/SKILL.md`, no `manifest.json` member at all — called
  `read_archive(...)` — raised `MalformedBundleError` explicitly naming
  "has no manifest.json member". **PASS.**
- `[REQ-SB-85-US-03-AC-08]` (unparsable `manifest.json`): built a real zip
  whose `manifest.json` member content was truncated/garbled
  (`"{not valid json,,,"`) — called `read_archive(...)` — raised
  `MalformedBundleError` chained `from` a real `json.JSONDecodeError`
  (`exc.__cause__` confirmed to be a `JSONDecodeError` instance).
  **PASS.**
- (no AC tag — supports the "never partially trusts" Constraint) Built a
  real, syntactically-valid `manifest.json` missing the `artifacts` key
  (`format_version`/`generated_at`/`secret_scan` present) — called
  `read_archive(...)` — raised `MalformedBundleError` explicitly naming
  the missing key (`'artifacts'`). **PASS.**

All 5 real verification scenarios above passed on first run after fixing
two throwaway-script setup issues (not defects in the reader itself, both
below), confirmed by re-running the full script clean afterward.

**Real, live-confirmed findings during THIS task's own verification
(script-setup, not reader defects):**
- The verification script's first selection used `pipeline:
  create-companies-partners` (that id is actually a Skill id, confirmed
  via `data_access.pipelines.list_pipeline_ids()` → `['company-discovery',
  'meeting-builder', 'threads-builder']`) and omitted `registry_loader
  .boot()`, so the closure resolver silently dropped the pipeline
  selection and the Agent's own `Agent.json`/`soul.md` were absent (the
  real Agent Registry is populated asynchronously by the app's own
  `lifespan`, never automatically in a standalone script). Both fixed in
  the verification script itself (real pipeline id `company-discovery`;
  `asyncio.run(registry_loader.boot())` called before any `commit_export`)
  — zero change to `sbf_archive.py`. Logged since it's the kind of
  "compose against the real current file/module" reconciliation this
  project's own `Implementation/Learnings.md` names as a recurring pattern
  worth naming explicitly.

**Out-of-scope confirmation:** touched only
`app/business/logic/sbf_archive.py`; did not touch conflict detection
(`T02`), the Template/Pipeline write paths (`T03`/`T04`, already `Done`
independently), the import orchestrator/endpoint (`T05`), or the
upload/preview UI (`T06`). No new dependency, no shared-interface change,
no ADR deviation, no unanticipated file.

**`MEMORY.md`:** not updated — no new decision/pattern/constraint emerged
beyond what `ADR-013` already documents; the reader is a direct,
same-shape implementation of that ADR's own format contract.

gate: clear 2026-09-01 — no MUST-FLAG trigger fired at this step (both
locked ACs have a real, mapped, executed verification step with a genuine
positive result; no new dependency, shared-interface change, ADR
deviation, or unanticipated file; the two scope-internal judgement calls
above are disclosed, non-blocking, and within this task's own scope). The
story's own `gate: flagged` (trigger-3, `ADR-014`/`ADR-015` pending human
review) is unaffected by this task closing — that review item is not this
task's to clear.
