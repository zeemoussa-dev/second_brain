---
id: REQ-SB-85-US-02-T03
title: artifact_secret_scan.py — secret-shaped-string scan over Second-Brain-owned bundle bytes (ADR-013)
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

# REQ-SB-85-US-02-T03 — artifact_secret_scan.py: secret-shaped-string scan over Second-Brain-owned bundle bytes (ADR-013)

## Parent Story

- Story: [[REQ-SB-85-US-02]] — `../UserStories/REQ-SB-85-US-02-export-dependency-closure-and-secret-scan.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-85 *Artifact Export/Import — Portable Capability Bundles (`.sbf`)*

---

## Objective

Scan the genuinely-new, Second-Brain-owned text content a resolved export
closure would write (Skill `SKILL.md`/scripts, `Template.json`, seed/
blank data files) for secret-shaped strings, and apply an operator's
per-finding decision (Redact / Keep as-is / Cancel export) in-memory
before anything is written — never the nested Hermes profile piece.

---

## Starting State → End State

**Before / Inputs:**
- No secret-detection mechanism exists in Second Brain today. Hermes' own
  `export_profile` already force-redacts its OWN staged files before
  producing its `tar.gz` (`agent.redact.redact_sensitive_text(...,
  force=True)`, confirmed real and out-of-reach — `T01`'s wrapper never
  parses that archive).

**After / Outputs:**
- `app/business/logic/artifact_secret_scan.py` (new) exposes:
  - `scan_closure(closure: list[dict]) -> list[dict]` — takes `T02`'s own
    resolved closure, reads each entry's real Second-Brain-owned text
    content (Skill `SKILL.md` + `list_scripts()` content via
    `data_access.skills`; `Template.json` raw text via
    `data_access.templates.read_template_json` re-serialized, or the raw
    file text directly; a seed/blank data file's own real, already-empty
    content), and returns one entry per finding:
    `{"artifact_kind": str, "artifact_id": str, "file_path": str,
    "line": int, "matched_pattern": str, "snippet": str}` — never the
    nested `agents/<id>/profile.tar.gz` bytes (explicitly skipped by
    kind — an `"agent"` closure entry's Hermes-profile piece is never fed
    into this scanner at all, only its Registry-side `Agent.json`/
    `soul.md` mirror text, which IS Second-Brain-owned and IS scanned).
  - A real, disclosed pattern set covering common secret shapes (e.g. a
    generic `sk-[A-Za-z0-9]{20,}`-style API-key pattern, a `Bearer
    <token>` header-shaped string, a generic 32+ hex-character token
    pattern, an AWS-access-key-shaped `AKIA[A-Z0-9]{16}` pattern) — a
    disclosed, non-exhaustive v1 heuristic set (same "acceptable v1
    limitation, not a blocking defect" framing `ADR-013` already applies
    to the Skill→Template heuristic), not a claim of catching every
    possible secret shape.
  - `apply_decisions(closure_content: dict[str, str], findings: list[dict],
    decisions: dict[str, str]) -> dict[str, str]` — `decisions` keys a
    finding's own stable identity (e.g. `f"{file_path}:{line}"`) to one
    of `"redact" | "keep" | "cancel"`. Raises a dedicated
    `SecretScanCancelledError` if ANY decision is `"cancel"` (the whole
    export aborts — Scenario 7). Raises a dedicated
    `SecretScanIncompleteError` if any real finding has no decision at
    all (never proceeds on an assumed default). Returns the closure's own
    content dict with every `"redact"`-decided finding's own matched
    substring replaced by a fixed placeholder (e.g.
    `"[REDACTED-BY-SECOND-BRAIN-EXPORT]"`) in that file's text; a
    `"keep"`-decided finding's text is returned byte-for-byte unchanged.

---

## Files to Modify

- `src/backend/app/business/logic/artifact_secret_scan.py` (new file).

---

## Constraints

- Inherits from parent story.
- **Never scans or touches `agents/<id>/profile.tar.gz`** — that piece
  arrives already silently redacted by Hermes' own `export_profile`
  (`ADR-014`); this system's "never silent" promise governs only the
  surface it owns. This exclusion is a hard, structural skip-by-kind, not
  an accidental omission — confirm this with a real induced test (Tests
  block).
- **Never writes anything to disk** — this module only reads real content
  and returns in-memory findings/redacted text; `T04`'s archive writer is
  the only real file-write step, and only runs after every finding is
  decided.
- **`"cancel"` on ANY finding aborts the whole export** — never a partial
  cancel of just that one file.
- A real finding with no decision blocks the write — never a silent
  default of "keep" or "redact."

---

## Tests

**Manual verification steps:**
1. Build a synthetic closure entry pointing at real, scratch Skill
   content (a disposable Skill's own `SKILL.md`, or an in-memory content
   dict standing in for it) containing an engineered secret-shaped string
   (e.g. `sk-aaaaaaaaaaaaaaaaaaaaaaaa`); call `scan_closure(...)`; confirm
   a finding is returned with the correct `file_path`/`line`/`snippet`.
   No AC tag directly (the finding-DETECTION step itself has no named
   Gherkin scenario of its own) — supports `AC-03`, verified end-to-end
   at `T04`/`T05`.
2. Call `scan_closure(...)` on a closure whose real content contains no
   secret-shaped strings; confirm an empty findings list is returned. No
   AC tag — supports `AC-02`, verified end-to-end at `T04`/`T05`.
3. `[REQ-SB-85-US-02-AC-03]` Given the finding from step 1, call
   `apply_decisions(...)` with that finding's own key mapped to
   `"redact"`; confirm the returned content has the matched secret
   substring replaced by the placeholder and the surrounding text
   otherwise unchanged. Call it again with `"keep"`; confirm the content
   is returned byte-for-byte unchanged (an explicit, logged
   acknowledgment, not a silent pass-through — confirm the return value
   or a companion field records that this finding was explicitly kept).
4. `[REQ-SB-85-US-02-AC-07]` Call `apply_decisions(...)` with that
   finding's key mapped to `"cancel"`; confirm `SecretScanCancelledError`
   is raised and the returned closure content (if any state was already
   built) is never used to write anything — the caller (`T04`) never
   proceeds to the archive writer on this path.
5. Call `apply_decisions(...)` with the finding present in `findings` but
   ABSENT from `decisions`; confirm `SecretScanIncompleteError` is raised
   (no AC tag — supports the "never a silent default" Constraint).
6. Feed `scan_closure(...)` a closure entry that includes an `"agent"`
   kind with a real (or engineered, scratch) `profile.tar.gz` path
   containing an engineered secret-shaped byte sequence; confirm NO
   finding is ever reported for that file (no AC tag — confirms the hard,
   structural skip-by-kind exclusion, distinct from "no secrets found").

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `scan_closure` detects an engineered secret-shaped string in real
      Second-Brain-owned content and returns an empty list when none exist
- [x] `scan_closure` never scans the nested Hermes profile sub-archive
- [x] `apply_decisions` redacts on `"redact"`, passes through unchanged
      (with an explicit acknowledgment) on `"keep"`, raises
      `SecretScanCancelledError` on any `"cancel"`
- [x] `apply_decisions` raises `SecretScanIncompleteError` on any
      undecided real finding
- [x] Nothing is ever written to disk by this module
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Resolving the closure itself — `T02`.
- Writing the archive / the export endpoint — `T04`.
- The secret-scan confirmation screen — `T05`.

---

## Context / Notes

`ADR-013` (`Implementation/Architecture/ADR.md`), architecture
`§Dependency Closure, Secret Scan & .sbf Archive Format`, are the
authoritative design for this task. The 3 finding-action verbs (Redact /
Keep as-is / Cancel export) are now LOCKED wording on
`REQ-SB-85-US-02-AC-03` — do not rename them without checking the story's
own locked Gherkin first.

---

## Implementation Log

**Build (2026-08-31):** `src/backend/app/business/logic/artifact_secret_scan.py`
(new file, the only file in `## Files to Modify`) implements `scan_closure`
and `apply_decisions` exactly per `ADR-013`. Content readers per closure
`kind`: `skill` → `data_access.skills.read_skill_md` + `list_scripts`;
`template` → `data_access.templates.read_template_json`, re-serialized via
`json.dumps`; `agent` → `data_access.registry.loader.agent_data_dir()`'s
own `Agent.json`/`soul.md` files ONLY (the same lookup
`agent_visual_registry.py`/`agent_manager.py` already use to find an
agent's real on-disk files) — there is no code path anywhere in this
module that reads a Hermes profile directory or `profile.tar.gz`, a
structural exclusion, not a runtime filter. A `pipeline` closure entry
contributes no scanned content (no `pipelines/<id>.json` reader) — the
story's own Objective names only Skill/Template/Agent-registry/
seed-blank-data as the scanned surface; disclosed as a scope-internal
judgement call, not a silent gap (no locked AC names Pipeline content).

**Verification method:** manual mode per the Pipeline contract — ran the
task's own 6 Tests-block steps as a real Python script
(`verify_secret_scan.py`, scratchpad, not committed) against the real,
running app: booted the real Registry (`registry_loader.boot()`), used
the real, PRD-named `create-companies-partners` Skill, the real `customer`
Template, and the real `macc-expert` Agent (confirmed present under
`Sections/sales/Agents/macc-expert` in the live, configured
`second_brain_data_path`). An engineered secret-shaped string
(`sk-aaaaaaaaaaaaaaaaaaaaaaaa`) was induced via a scoped, reverted
in-process monkeypatch of `skills_data.list_scripts` (this project's own
established real-dependency-monkeypatch technique, `Learnings.md`
`SPRINT-018`) — no permanent file edit, no write to the real Skill repo.

- **Test 1 (supports AC-03, no direct tag):** the monkeypatched skill
  content produced exactly one finding — `file_path:
  "skills/create-companies-partners/scripts/scratch_engineered_secret.py"`,
  `line: 1`, `matched_pattern: "generic-api-key (sk-...)"`, `snippet`
  containing the engineered value. **Observed: PASS.**
- **Test 2 (supports AC-02, no direct tag):** the SAME real Skill's own
  actual, unmodified `SKILL.md`/`scripts/**` content (no monkeypatch)
  produced an empty findings list. **Observed: PASS** (also spot-checked
  the real `customer` Template and an unresolvable Skill/Pipeline id in
  the same closure — zero findings, zero exceptions).
- **`[REQ-SB-85-US-02-AC-03]` (Test 3):** `apply_decisions` with the Test-1
  finding decided `"redact"` returned the file's text with the exact
  matched substring replaced by `[REDACTED-BY-SECOND-BRAIN-EXPORT]` and
  the sibling line (`print('nothing else here')`) byte-for-byte unchanged.
  The same finding decided `"keep"` returned the content byte-for-byte
  unchanged AND emitted a real `logging` INFO line naming the finding's
  own key and pattern (`"Secret-scan finding
  skills/.../scratch_engineered_secret.py:1 (...) kept as-is on explicit
  operator decision."`) — the explicit, logged acknowledgment the AC's
  own wording requires, not a silent pass-through; captured live via a
  `logging.StreamHandler` attached to the module's logger during the
  test. **Observed: PASS.**
- **`[REQ-SB-85-US-02-AC-07]` (Test 4):** the same finding decided
  `"cancel"` raised `SecretScanCancelledError`; the caller (this test
  script) never proceeded past the raise. **Observed: PASS.**
- **Test 5 (supports the "never a silent default" Constraint, no direct
  tag):** calling `apply_decisions` with the finding present in `findings`
  but absent from `decisions` raised `SecretScanIncompleteError`, checked
  BEFORE any cancel/redact/keep evaluation. **Observed: PASS.**
- **Test 6 (confirms the hard, structural skip-by-kind exclusion, no
  direct tag):** an `"agent"` closure entry for the real `macc-expert`
  Agent, carrying an extra, deliberately-irrelevant field pointing at a
  real scratch `profile.tar.gz`-shaped file containing an engineered
  `AKIA`-shaped secret, produced zero findings referencing that file —
  confirmed the module's own `_agent_content` reader never reads that
  field or path at all (it only ever opens `Agent.json`/`soul.md` under
  `registry_loader.agent_data_dir()`). **Observed: PASS.**

**Scope-internal judgement calls (for human spot-check, per
`Learnings.md`):**
1. A secret-scan finding's own `"{file_path}:{line}"` key (the identity
   `apply_decisions`'s `decisions` dict keys by) only stays unique if at
   most ONE pattern is reported per physical line — implemented as
   first-match-wins across `_SECRET_PATTERNS`' own declared order (two of
   the v1 patterns, e.g. the 32+ hex-char generic token and the `sk-...`
   pattern, can both match the identical real substring). Recorded in
   `MEMORY.md` for future pattern additions.
2. Pipeline (`pipelines/<id>.json`) content is not scanned by this module
   — the story's Objective enumerates only Skill/Template/Agent-registry/
   seed-blank-data as the surface; no locked AC names Pipeline content, so
   this is read as intentional scope, not an omission.
3. `apply_decisions`'s "explicit, logged acknowledgment" for a `"keep"`
   decision is implemented as a Python `logging` INFO line (the literal
   "logged" in the Tests block's own wording) plus the structural
   guarantee that `apply_decisions` can never act on a `"keep"` for a
   finding absent from `decisions` (raises `SecretScanIncompleteError`
   first) — no change to the documented `dict[str, str]` return shape.

gate: clear 2026-08-31 — no MUST-FLAG trigger fired at this task: every
locked AC (`AC-03`, `AC-07`) has a real, executed, passing manual
verification step above; no new dependency, shared-interface change, ADR
deviation, or unanticipated file; the 3 scope-internal judgement calls
above are disclosed, non-blocking. The story's own `gate: flagged` (trigger-3,
`ADR-013`/`ADR-014` pending human review) is unaffected by this task
completing — per Pipeline.md, the decomposer/coder proceed regardless.
