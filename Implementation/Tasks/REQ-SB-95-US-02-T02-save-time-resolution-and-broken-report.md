---
id: REQ-SB-95-US-02-T02
title: Save-time implementation resolution for skill / http / ui, plus the broken-entry read status
parent_story: REQ-SB-95-US-02
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-02-T01]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-02-T02 — Save-Time Implementation Resolution + Broken-Entry Status

## Parent Story

- Story: [[REQ-SB-95-US-02]] — `../UserStories/REQ-SB-95-US-02-action-sixth-artifact-kind.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Refuse to save an Action whose one implementation does not resolve on this
install, naming what did not resolve — and report, on every read, which
catalogued Actions have since become broken.

---

## Starting State → End State

**Before / Inputs:**

- `T01`'s `ActionManager` saves any cardinality-valid Action without checking
  that the thing it names exists.
- `SkillManager.deploy()` is the in-repo precedent for refusing rather than
  shipping something that only fails when it runs; `SkillManager`'s deployment
  report (`current` / `stale` / `missing` / `modified` per skill+profile) is the
  shape to mirror for the read-side status.

**After / Outputs:**

- `ActionManager.create()` / `update()` resolve the named implementation before
  anything is written:
  - `skill` → resolves against `SkillManager` as **deployed**, not merely
    catalogued;
  - `http` → resolves against the running app's own route table (which already
    includes plugin routes mounted under `/plugins/<plugin_id>/`);
  - `ui` → resolves against the registered front-end feature key.
- A non-resolving implementation is refused with a message naming exactly what
  did not resolve, and **nothing is written or changed on disk**.
- `ActionManager` exposes a read-side resolution status per Action
  (`resolves` | `broken`, with what no longer resolves), computed on read, never
  cached — `business/logic/`'s own no-caching convention.

---

## Files to Modify

- `src/backend/app/business/core/actions/action_manager.py`
- `src/backend/app/business/core/actions/action.py` (the resolution-status shape, if it needs a type)
- `src/backend/tests/test_action_resolution.py` (new)

---

## Constraints

- Inherits from parent story.
- **Resolution happens at save, not at call** (`ADR-032`). A call-time-only
  check does not satisfy `AC-02`. (`US-03`'s gate re-checks at call time as
  well, but that is a second line, not this one.)
- The resolution status is **computed on read, never cached** and never written
  into `Action.json`.
- No change to `SkillManager` — this task reads it, it does not extend it.
- The route-table lookup must read the live app's routes, not a hand-maintained
  list of paths.

---

## Tests

**Automated tests** — `src/backend/tests/test_action_resolution.py`, run with
`pytest tests/test_action_resolution.py` from `src/backend`. Monkeypatch the
data-access writes as in `T01`, and monkeypatch `SkillManager`'s deployed-skill
lookup to control what resolves.

1. `[REQ-SB-95-US-02-AC-02]` Save an Action naming a `skill` implementation that
   is catalogued but **not deployed**; assert the refusal message names that
   skill id and that `write_action_json` was never called.
2. `[REQ-SB-95-US-02-AC-02]` Save an Action naming an `http` implementation
   whose path is not in the app's route table; assert the refusal names the
   path and nothing is written.
3. `[REQ-SB-95-US-02-AC-02]` Save an Action naming a `ui` feature key that is not
   registered; assert the refusal names the key and nothing is written.
4. `[REQ-SB-95-US-02-AC-02]` Re-save the same Action with a resolvable
   implementation; assert it is written and `get_by_id()` returns it.
5. `[REQ-SB-95-US-02-AC-07]` Save an Action against a deployed Skill, then
   monkeypatch that Skill out of the deployed set; assert the read-side status
   reports that Action as `broken` naming the missing skill, that every other
   Action still reports `resolves`, and that nothing had to call the Action to
   discover it.

**Manual verification steps:**

1. `[REQ-SB-95-US-02-AC-07]` With the backend running, save an Action against a
   really-deployed Skill, undeploy that Skill, then re-read the catalogue
   through `ActionManager` in a Python shell against the real data path; confirm
   the broken status and the named cause appear without any call being made.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] All three implementation kinds resolve at save time, against real sources
- [ ] A non-resolving save is refused naming the cause, with zero disk effect
- [ ] Read-side `resolves` | `broken` status per Action, computed fresh
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The API surface that exposes the refusal and the status — `T03`.
- Showing broken state on a screen — `T06`.
- Call-time validation — `REQ-SB-95-US-03-T02`.

---

## Context / Notes

`architecture.md` → **§Action Catalogue — the Sixth Artifact Kind** names all
three resolution sources and the `SkillManager`-report shape for the read-side
status. `ADR-032` fixes save-time resolution as the decision ("so a broken
action cannot sit in the catalogue waiting to fail in front of the operator").

---

## Implementation Log

_(Filled in by the coder.)_
