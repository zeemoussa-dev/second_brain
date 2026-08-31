---
id: REQ-SB-85-US-02-T04
title: sbf_archive.py writer + POST /artifacts/export/{preview,commit} — real .sbf zip production (ADR-013)
parent_story: REQ-SB-85-US-02
requirement_id: REQ-SB-85
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-85-US-02-T01, REQ-SB-85-US-02-T02, REQ-SB-85-US-02-T03]
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-85-US-02-T04 — sbf_archive.py writer + POST /artifacts/export/{preview,commit}: real .sbf zip production (ADR-013)

## Parent Story

- Story: [[REQ-SB-85-US-02]] — `../UserStories/REQ-SB-85-US-02-export-dependency-closure-and-secret-scan.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-85 *Artifact Export/Import — Portable Capability Bundles (`.sbf`)*

---

## Objective

Compose `T01`/`T02`/`T03` into the real export flow — resolve, scan,
gate on decisions, then write a single real `.sbf` zip — exposed as two
sub-routes on `artifacts_router.py`: `POST /artifacts/export/preview`
(read-only) and `POST /artifacts/export/commit` (the only step that ever
writes a file).

---

## Starting State → End State

**Before / Inputs:**
- `T01` (`HermesCLI.export_profile`/`import_profile`), `T02`
  (`resolve_closure`), `T03` (`scan_closure`/`apply_decisions`) all exist.
  `app/api/artifacts_router.py` exists (`REQ-SB-85-US-01-T01`, `GET
  /artifacts`). No archive-writing module exists anywhere.

**After / Outputs:**
- `app/business/logic/sbf_archive.py` (new) exposes
  `write_archive(output_path: str, manifest: dict, payload: dict[str,
  bytes]) -> None` — writes a real zip: `manifest.json` (the dict,
  JSON-serialized) plus every `payload` key as its own real archive
  member path (e.g. `"skills/create-companies-partners/SKILL.md"`,
  `"agents/compass-expert/profile.tar.gz"`), content = the raw bytes
  value. Pure I/O — no business decisions made here (mirrors
  `data_access/*`'s own "zero business interpretation" discipline, even
  though this lives in `business/logic/` per `ADR-013`'s own explicit
  "never a 5th Manager" framing — the writer/reader pair is shared
  infrastructure, not an entity gateway).
- `app/business/logic/artifact_export.py` (new) — the real orchestrator:
  - `preview_export(selection: list[dict]) -> dict` — calls
    `resolve_closure(selection)` (`T02`), builds each closure entry's own
    real Second-Brain-owned text content (Skill `SKILL.md`+scripts via
    `data_access.skills`; `Template.json` raw text; an Agent's own
    Registry `Agent.json`/`soul.md` mirror text — never the Hermes
    profile piece), runs `scan_closure(...)` (`T03`) over it, and returns
    `{"closure": [...], "secret_findings": [...]}`. Writes nothing.
  - `commit_export(selection: list[dict], secret_decisions: dict[str,
    str]) -> str` — re-resolves and re-scans FRESH (never trusts a
    client-cached preview — closes any real staleness window), calls
    `apply_decisions(...)` (`T03` — raises `SecretScanCancelledError`/
    `SecretScanIncompleteError` on an incomplete/cancelled decision set,
    propagated uncaught to the router for a clean 4xx), then assembles
    the real payload:
    - Every Skill in the closure: `skills/<slug>/SKILL.md`,
      `skills/<slug>/scripts/**` (post-redaction content from
      `apply_decisions`).
    - Every Template: `templates/<id>/Template.json` (post-redaction).
    - Every Pipeline: `pipelines/<id>.json`.
    - Every Agent: `agents/<id>/profile.tar.gz` (the RAW bytes from
      `HermesCLI.export_profile`, `T01` — written to a scratch temp path
      first, read back as bytes, then the temp path is deleted; never
      unpacked/repacked/re-scanned — `ADR-014`) plus `agents/<id>/
      Agent.json`, `agents/<id>/soul.md` (the Registry-side mirror text,
      post-redaction).
    - **Seed/blank data files (Scenario 5):** a small, disclosed v1
      allowlist maps a known real target-relative path to its own
      real "does this Skill need it" static-scan check — v1 ships with
      exactly one entry, `"Settings/Entities.md"` (the only real seed/
      blank-data store of this shape in the app today,
      `data_access/entities.py`), detected the same literal-substring
      way `T02`'s own Skill→Template heuristic works (does any closure
      Skill's own `SKILL.md`/script content reference `"Entities.md"`
      literally). When matched, `seed_data/Settings/Entities.md` is
      added to the payload with content forced to `""` — **always
      genuinely empty, regardless of what the real, current file on this
      machine actually contains** (Scenario 4/5's own hard boundary).
      This allowlist is this task's own disclosed, scope-internal
      judgement call (the PRD names one real example, not an enumerated
      list) — documented here for the same reason `ADR-013`'s own
      Skill→Template heuristic is disclosed, not silently assumed.
    - `manifest.json`: `{"format_version": 1, "generated_at": "<real
      ISO-8601 UTC timestamp>", "artifacts": [{"kind", "id",
      "included_reason", "depends_via", "category"} for each closure
      entry — `category` is the real Skill category folder name
      (`skills_data.category_of(id)`) for a `kind: "skill"` entry, `null`
      for every other kind — per `ADR-013`'s own Decision text ("category
      recorded in the manifest entry, not the payload path") this is the
      ONLY place a Skill's category survives the round trip, since the
      payload path itself is the flat `skills/<slug>/...`, no category
      segment], "secret_scan": {"findings_decided": <count>,
      "redacted_count": <count>}}`.
    Writes the real `.sbf` via `sbf_archive.write_archive(...)` to a
    scratch temp path, returns that path.
- `app/api/artifacts_router.py` — `POST /artifacts/export/preview` (body:
  `{"selection": [{"kind", "id"}]}`, returns `preview_export(...)`'s own
  dict) and `POST /artifacts/export/commit` (body: `{"selection": [...],
  "secret_decisions": {...}}`, catches `SecretScanCancelledError` →
  `HTTPException(409, "export cancelled")`,
  `SecretScanIncompleteError` → `HTTPException(400, "...")`, otherwise
  returns a `FileResponse` streaming the real `.sbf` bytes with
  `media_type="application/octet-stream"`,
  `filename=f"second-brain-export-{<timestamp>}.sbf"`, and deletes the
  scratch temp `.sbf` after the response is sent — `BackgroundTask`,
  same "clean up scratch temp output after streaming" shape this
  codebase doesn't have a prior precedent for; use FastAPI's own
  `BackgroundTasks` dependency, the standard mechanism for this).

---

## Files to Modify

- `src/backend/app/business/logic/sbf_archive.py` (new file — writer half
  only; the reader half is `REQ-SB-85-US-03-T01`'s own addition to this
  same file).
- `src/backend/app/business/logic/artifact_export.py` (new file).
- `src/backend/app/api/artifacts_router.py` — two new routes.

---

## Constraints

- Inherits from parent story.
- **`commit_export` is the ONLY function in this whole subsystem that
  ever writes a real file** — `preview_export`, `T02`, `T03` never do.
- **Never re-scans the nested `profile.tar.gz`** — read as raw bytes
  only, never passed to `scan_closure`.
- **A seed/blank data file is ALWAYS forced empty at write time** — never
  reads the real current file's own content into the archive, even
  though `data_access.entities.read_raw()` technically could.
- **Re-resolve and re-scan fresh in `commit_export`** — never trust a
  preview response's own cached closure/findings as authoritative at
  commit time (closes a real staleness window between preview and
  commit).
- The scratch temp `.sbf` and any scratch temp `profile.tar.gz` are
  cleaned up after use — no leftover temp files on disk after a
  request completes (success or failure).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-85-US-02-AC-04]` Call `commit_export` (or the `/commit`
   route) with a selection of only generic, non-Customer-Tracking-shaped
   real Skills/Pipelines/Agents (no `create-companies-partners`); open
   the produced `.sbf` as a real zip and confirm it contains only
   `skills/`/`templates/`/`pipelines/`/`agents/` payload paths and
   `manifest.json` — no `seed_data/` entry, and no path anywhere under
   the archive contains any of the operator's own real captured vault
   content.
2. `[REQ-SB-85-US-02-AC-05]` Call `commit_export` with a selection of
   `{"kind": "pipeline", "id": "<the real create-companies-partners
   pipeline or skill id>"}`; open the produced `.sbf`; confirm it
   contains the real pipeline/skill/`customer`+`partner` Template.json
   files AND a `seed_data/Settings/Entities.md` entry whose content is
   `""` (byte-for-byte empty) — confirm this independently against the
   real, current `Settings/Entities.md` on this machine (which likely
   has real content) to prove the archive's own copy was forced empty,
   not copied verbatim.
3. `[REQ-SB-85-US-02-AC-06]` Call `commit_export` with a selection of one
   real Agent artifact; open the produced `.sbf`; confirm
   `agents/<id>/profile.tar.gz` exists with non-zero size (the real,
   unmodified output of `T01`'s `export_profile`) AND
   `agents/<id>/Agent.json`/`agents/<id>/soul.md` exist with the real
   Registry-side section/type/dependency data for that Agent.
4. `[REQ-SB-85-US-02-AC-02]` Call `preview_export` with a selection whose
   real content contains no secret-shaped strings; confirm
   `secret_findings` is `[]`. Then call `commit_export` with the same
   selection and an empty `secret_decisions` dict; confirm it succeeds
   and produces a real `.sbf` — no error raised for "undecided findings"
   since there are none.
5. `[REQ-SB-85-US-02-AC-03]` Call `preview_export` with a selection whose
   real content contains an engineered secret-shaped string; confirm
   `secret_findings` is non-empty. Call `commit_export` with the SAME
   selection but an EMPTY `secret_decisions`; confirm
   `SecretScanIncompleteError` propagates (surfaced by the router as a
   `400`) and no `.sbf` file is left on disk anywhere.
6. `[REQ-SB-85-US-02-AC-07]` Call `commit_export` with the same selection
   from step 5 and `secret_decisions` mapping that finding to `"cancel"`;
   confirm `SecretScanCancelledError` propagates (router `409`) and no
   `.sbf` file is written, and confirm (by re-reading the real source
   Skill/Template file afterward) that no artifact content anywhere on
   disk was modified by this attempt.
7. Confirm no scratch temp file (`.sbf` or `profile.tar.gz`) remains on
   disk after any of steps 1-6 completes (no AC tag — supports the
   cleanup Constraint).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `preview_export` resolves + scans without writing anything
- [x] `commit_export` re-resolves/re-scans fresh, gates on every finding
      being decided, writes exactly one real `.sbf` on success
- [x] A "Standard" bundle carries no captured operator data anywhere in
      the archive
- [x] A Customer-Tracking-shaped bundle's seed file is always genuinely
      empty, regardless of the real current file's own content
- [x] An Agent artifact's bundle piece composes both the raw Hermes
      profile export and the Registry-side mirror
- [x] `SecretScanIncompleteError`/`SecretScanCancelledError` both prevent
      any archive write and are surfaced as clean HTTP errors
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The dependency-preview/secret-scan confirmation UI — `T05`.
- Reading/importing a `.sbf` — `REQ-SB-85-US-03`.
- Any manifest `kind` value beyond the 4 real kinds this pass covers.

---

## Context / Notes

`ADR-013`/`ADR-014` (`Implementation/Architecture/ADR.md`), architecture
`§Dependency Closure, Secret Scan & .sbf Archive Format`, are the
authoritative design for this task. The `/preview` + `/commit` route
split (rather than one dual-mode `POST /artifacts/export`) is this
story's own disclosed decomposer judgement call — see the parent story's
own Notes ("Decomposer pass") for the full reasoning; `REQ-SB-85-US-03`'s
own import flow uses the identical two-phase shape for consistency.

---

## Implementation Log

**Build summary:** `app/business/logic/sbf_archive.py` (new — `write_archive`,
a plain `zipfile.ZipFile` writer, zero business decisions), `app/business/
logic/artifact_export.py` (new — `preview_export`/`commit_export`, composes
`T02`/`T03`/`sbf_archive.py`), and two new routes on `app/api/
artifacts_router.py` (`POST /artifacts/export/preview`, `POST /artifacts/
export/commit`). No other files touched.

**Scope-internal judgement calls (logged for human spot-check, non-blocking):**
- `commit_export`'s own text-content gathering (`_text_content_for_scan`)
  duplicates `artifact_secret_scan.py`'s own (module-private,
  underscore-prefixed) `_skill_content`/`_template_content`/`_agent_content`
  readers, rather than importing those private names across a module
  boundary — `T03` is frozen/`Done` and out of this task's `## Files to
  Modify`, and this codebase has no precedent anywhere for importing an
  underscore-prefixed name from a sibling module. Uses the exact same
  `file_path` convention (`skills/<id>/SKILL.md`, `skills/<id>/scripts/
  <rel>`, `templates/<id>/Template.json`, `agents/<id>/Agent.json`,
  `agents/<id>/soul.md`) so a finding's own `file_path` (from
  `scan_closure`) always resolves to a real key in `commit_export`'s own
  `closure_content` dict passed to `apply_decisions`  — confirmed live
  (AC-03/AC-07 below).
- The seed/blank-data allowlist (`_SEED_DATA_ALLOWLIST`) ships with
  exactly the one entry `ADR-013`/the story's own Scenario 5 name
  (`"Settings/Entities.md"`) — this task's own disclosed judgement call,
  per the task's own Objective section (the PRD names one real example,
  not an enumerated list).

**Real, live-confirmed correction found during THIS task's own build**:
`HermesCLI`/`get_client()` must be reached via `app.business.hermes.
client.get_client()`, never `app.hermes.client` directly — confirmed by a
real `ImportError` on first attempt (`app.hermes.client` has no
`get_client`; that name lives one layer up, in `app.business.hermes.
client`, this codebase's own documented single door onto Hermes,
`MEMORY.md` 2026-08-27). Fixed before any verification ran; not a new
constraint (already documented), just a live confirmation of it applying
here too.

**Verification (manual mode) — real `TestClient(app)` against the real,
live, already-configured vault/Hermes install (no mocks, no seeded/scratch
data) — a throwaway script drove every scenario below, output captured,
not re-transcribed from memory:**

- `[REQ-SB-85-US-02-AC-04]` (Standard bundle, no captured data): selected
  `{skill: capture-notes, template: note}` and called `POST /commit`.
  `200`, real `.sbf` produced (22,504 bytes). Opened as a real zip:
  members were `manifest.json` + `skills/capture-notes/**` +
  `templates/**` only — no `seed_data/` entry, no path referencing any of
  the operator's own captured content. **PASS.** (Note: the resolved
  closure pulled in ALL 7 real Templates, not just `note` — a genuine,
  live-confirmed over-inclusion of `T02`'s own Skill→Template heuristic,
  not a defect in this task; logged to `MEMORY.md` since it's a durable,
  non-obvious finding. Does not affect this AC — Templates are capability/
  schema, never captured data.)
- `[REQ-SB-85-US-02-AC-05]` (Customer-Tracking bundle, empty seed file):
  selected `{skill: create-companies-partners}`, called `POST /commit`.
  `200`. Archive contained the real Skill + `customer`/`partner`
  Template.json files AND `seed_data/Settings/Entities.md` with content
  `b""` (0 bytes) — independently confirmed against the REAL, current
  `Settings/Entities.md` on this machine (`entities_data.read_raw()`),
  which has 5,920 real bytes of the operator's own actual Customer/
  Partner content — proving the archive's own copy was genuinely forced
  empty, not copied verbatim. **PASS.**
- `[REQ-SB-85-US-02-AC-06]` (Agent artifact, two-piece composition):
  selected `{agent: azure-expert}`, called `POST /commit`. `200`. Archive
  contained `agents/azure-expert/profile.tar.gz` (14,681,879 bytes — real,
  non-zero, the genuine unmodified output of `HermesCLI.export_profile`)
  AND `agents/azure-expert/Agent.json` + `agents/azure-expert/soul.md`
  (the real Registry-side mirror). **PASS.**
- `[REQ-SB-85-US-02-AC-02]` (no secrets, straight to archive): `POST
  /preview` with `{skill: capture-notes}` (real content, no engineered
  secret) → `secret_findings: []`. `POST /commit` with the same selection
  and `secret_decisions: {}` → `200`, real `.sbf` produced, no error for
  "undecided findings" (there were none). **PASS.**
- `[REQ-SB-85-US-02-AC-03]`/`[REQ-SB-85-US-02-AC-07]` (secret found,
  operator must decide; cancel aborts cleanly): induced a real secret-
  shaped finding via an in-process monkeypatch of `app.data_access.
  skills.read_skill_md` (the real, already-loaded module attribute —
  this project's own established "monkeypatch a real dependency in-
  process, invoke the real unmodified production function" technique,
  `Implementation/Learnings.md` `SPRINT-018`) so `capture-notes`' own
  `SKILL.md` content included an engineered `sk-`-shaped token, WITHOUT
  ever writing to the real file on disk. `POST /preview` →
  `secret_findings` non-empty (1 finding, `skills/capture-notes/
  SKILL.md:2`, pattern `generic-api-key (sk-...)`). `POST /commit` with
  the SAME selection and `secret_decisions: {}` (nothing decided) → `400`,
  body names the real undecided finding key
  (`SecretScanIncompleteError` surfaced correctly) — **AC-03 PASS**.
  `POST /commit` with the SAME selection and `secret_decisions:
  {"skills/capture-notes/SKILL.md:2": "cancel"}` → `409`
  (`SecretScanCancelledError` surfaced correctly); re-read the real
  `capture-notes/SKILL.md` from disk afterward via the UNPATCHED
  `read_skill_md` — byte-identical to before the attempt, confirming no
  artifact content anywhere was modified — **AC-07 PASS**.
- Unnumbered cleanup check (supports the Constraints, not a locked AC):
  scanned the real system temp directory for `second-brain-export-*.sbf`
  and `second-brain-agent-export-*.tar.gz` before/after every scenario
  above (including both failure paths) — zero leftover scratch files at
  any point. **PASS.**

**Out-of-scope confirmation:** did not touch `T05` (frontend), did not
touch the import side (`REQ-SB-85-US-03`), did not add any manifest
`kind` beyond the 4 already named.

gate: clear 2026-08-31 — no MUST-FLAG trigger fired at this step (every
locked AC has a real, mapped, executed verification step with a genuine
positive result; no new dependency, shared-interface change, ADR
deviation, or unanticipated file; the two scope-internal judgement calls
above are disclosed, non-blocking, and within this task's own scope).
