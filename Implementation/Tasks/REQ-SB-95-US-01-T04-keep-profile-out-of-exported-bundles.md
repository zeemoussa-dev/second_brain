---
id: REQ-SB-95-US-01-T04
title: Keep the Operator Profile out of an exported bundle, and disclose what a real Agent bundle still carries
parent_story: REQ-SB-95-US-01
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-01-T01, REQ-SB-95-US-01-T02]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-01-T04 — The Profile Does Not Travel

## Parent Story

- Story: [[REQ-SB-95-US-01]] — `../UserStories/REQ-SB-95-US-01-operator-profile.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Make "the Operator Profile is excluded from artifact export" (`ADR-032`) a
proven, guarded property rather than an accident of it not being a kind yet —
**and**, separately and without changing any behaviour, record exactly what a
real exported Agent bundle contains today, so the operator can settle the open
privacy question on facts.

---

## Starting State → End State

**Before / Inputs:**

- `business/logic/artifacts_inventory.py` enumerates the artifact kinds;
  `artifact_dependency_resolver.py` builds a closure; `artifact_export.py`
  writes the payload per kind via `_PAYLOAD_FOLDER`; `artifact_seed_data.py`
  adds allowlisted, **plugin-registered** seed-data paths as empty files.
- The Operator Profile is not an artifact kind and nothing registers it as
  seed data — true today, and nothing currently stops a future change from
  sweeping `data/Operator/` in alongside `data/Actions/` and `data/Workflows/`.
- `ActionCalls/` and `WorkflowRuns/` are excluded for the same reason
  (`ADR-032`) — instance data, not capability.
- **Confirmed by direct reading, and load-bearing for the disclosure below:**
  `artifact_export.py` copies an exported Agent's registry-side `soul.md`
  verbatim (`content[f"agents/{id}/soul.md"] = soul_path.read_text(...)`) *and*
  writes `agents/<id>/profile.tar.gz`, the raw unmodified output of
  `HermesCLI.export_profile` — which `ADR-014` fixes as an **opaque-bytes**
  boundary and which carries the profile's own SOUL.md.

**After / Outputs:**

- A guard that fails loudly if the Operator Profile ever becomes exportable:
  no `operator`/`profile` artifact kind in the inventory, no `Operator/` path
  in any export payload, no closure entry for it, and no seed-data allowlist
  entry naming `Profile.json`.
- A **disclosure**, not a behaviour change: a real export of a real Agent is
  performed and the Implementation Log records, honestly, whether any Profile
  colleague name or address appears (a) in `agents/<id>/soul.md` and (b)
  inside `agents/<id>/profile.tar.gz`.

---

## Files to Modify

- `src/backend/tests/test_operator_profile_not_exported.py` (new — the guard)
- `src/backend/app/business/logic/artifact_export.py` — **only** if the guard
  finds the Profile genuinely reachable today; if it is already excluded by
  construction, change nothing here and say so in the Implementation Log.

---

## Constraints

- Inherits from parent story.
- **Do not implement either answer to the open privacy question.** Stripping
  the `## Who you work for` block from an exported agent's soul, and accepting
  the leak and documenting it, are both forbidden here. AC-08 is `locked:
  false` precisely because the operator has not chosen yet
  (`REVIEW-QUEUE.md`), and a task that picked one would be the choice.
- **Do not reach inside `profile.tar.gz`.** `ADR-014` makes it opaque bytes;
  this task reads it only to *report* what is in it.
- Minimal change. If AC-06 already holds by construction, the deliverable is
  the guard plus the disclosure — not a refactor of the export machinery.
- Nothing else about exporting may change: the kinds that travel today must
  still travel with byte-identical payloads.

---

## Tests

**Automated tests** — `src/backend/tests/test_operator_profile_not_exported.py`,
run with `pytest tests/test_operator_profile_not_exported.py` from
`src/backend`; follow `tests/test_artifact_seed_data.py` and
`tests/test_blueprint_no_instance_data.py` for the existing
"instance data must not travel" technique.

1. `[REQ-SB-95-US-01-AC-06]` With a real Profile saved under a tmp data path,
   assert `artifacts_inventory` reports no artifact kind for it and that it
   cannot be named in an export selection (the resolver refuses or ignores an
   `operator` kind rather than resolving a closure for it).
2. `[REQ-SB-95-US-01-AC-06]` Build an export payload over a selection covering
   every real kind (including an Agent) and assert no payload key begins with
   `operator`/`Operator`, and that no key anywhere in the payload is
   `Profile.json`.
3. `[REQ-SB-95-US-01-AC-06]` Assert `artifact_seed_data.seed_data_files()`
   contains no entry whose name is `Profile.json`, so the empty-seed path
   cannot carry it either.
4. `[REQ-SB-95-US-01-AC-06]` Export the same selection with and without a saved
   Profile and assert the two payloads are byte-identical — the Profile's
   existence changes nothing that travels.

**Manual verification steps:**

1. `[REQ-SB-95-US-01-AC-06]` With the backend running and a real Profile saved
   naming at least one colleague, export a real bundle containing an Agent from
   the Artifacts screen; open the `.sbf` and confirm there is no
   `Operator/Profile.json` entry anywhere in it.
2. `[REQ-SB-95-US-01-AC-08 — DISCLOSURE ONLY, non-blocking, changes nothing]`
   In the same real bundle, search `agents/<id>/soul.md` and the extracted
   `agents/<id>/profile.tar.gz` for each colleague name and address from the
   Profile. Record both results verbatim in the Implementation Log — found or
   not found, per file. **Do not fix either result**; this is evidence for the
   operator's pending strip-vs-accept decision, and the task is not blocked by
   whatever it finds. Export through the running server (`MEMORY.md`:
   `registry_loader.agent_data_dir()` returns `None` until
   `registry_loader.boot()` has run in-process, so a raw script silently loses
   `Agent.json`/`soul.md`).

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] The Profile is provably not an exportable artifact, and a guard keeps it so
- [ ] No `Operator/` payload, no `Profile.json` seed entry, in any bundle
- [ ] Everything that travels today still travels byte-identically
- [ ] The real-bundle disclosure for AC-08 is recorded, with no behaviour changed
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Stripping the `## Who you work for` block on export, or any other
  implementation of AC-08 — blocked on the operator's decision.
- Changing `ADR-014`'s opaque-bytes treatment of `profile.tar.gz`.
- Export/import of Actions and Workflows — `REQ-SB-95-US-02-T04` /
  `REQ-SB-95-US-04-T04`.

---

## Context / Notes

`ADR-032` (the Profile is excluded from artifact export by default) and
`ADR-014` (the agent profile tarball is opaque bytes) are the two authorities
here, and the gap between them is exactly the open question. The story's
`## Notes` → *Decomposer RE-pass* records the finding in full; `REVIEW-QUEUE.md`
carries the decision.

---

## Implementation Log

_(Filled in by the coder.)_
