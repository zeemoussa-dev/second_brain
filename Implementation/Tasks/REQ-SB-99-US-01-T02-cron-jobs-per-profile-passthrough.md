---
id: REQ-SB-99-US-01-T02
title: cron_status.list_cron_jobs() gains an optional profile_id pass-through, default behaviour unchanged
parent_story: REQ-SB-99-US-01
requirement_id: REQ-SB-99
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-10-17
updated: 2026-10-17
---

# REQ-SB-99-US-01-T02 — A Named Profile's Cron Jobs Become Readable

## Parent Story

- Story: [[REQ-SB-99-US-01]] — `../UserStories/REQ-SB-99-US-01-hermes-profile-as-it-really-is.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-99 *See a Hermes Profile As It Really Is — Soul, Skills, Config, Jobs*

---

## Objective

Let the app read the cron jobs of a *named* profile, which it has never been
able to do, without changing what `GET /hermes/cron/jobs` returns today.

---

## Starting State → End State

**Before / Inputs:**

- `src/backend/app/business/hermes/cron_status.py::list_cron_jobs()` takes no
  arguments and calls `get_client().cron.list_cron_jobs()` with no
  `profile_id`, so it has only ever listed the root/`default` profile's jobs.
- `app/hermes/cron.py::HermesCron.list_cron_jobs(profile_id=None)` has accepted
  a `profile_id` since 2026-08-28 and resolves
  `<home>/cron/jobs.json` for `None` or `<home>/profiles/<id>/cron/jobs.json`
  otherwise (`_profile_dir`, line ~98).
- **The id mapping matters:** `HermesCron._profile_dir("default")` would resolve
  `<home>/profiles/default`, which exists on no install. The `default` profile
  *is* `<HERMES_HOME>`, so `"default"`/`""`/`None` must all map to `None` before
  reaching the library — the same convention `HermesSkills._profile_dir` and
  `cli._profile_args` already use.
- `CronJob` carries **no** profile/agent attribute. Binding is structural: the
  directory the job's `jobs.json` lives in.

**After / Outputs:**

- `list_cron_jobs(profile_id: str | None = None) -> list[dict]` — additive and
  default-unchanged, mapping `None`/`""`/`"default"` to the root and any other
  id to that profile's own directory.
- Each returned dict gains a truthful binding label the view can use without
  re-deriving it, e.g. `"scope": "install"` for root-level jobs and
  `"scope": "profile"` for a named profile's own — the `asdict(job)` payload
  otherwise unchanged.
- `GET /hermes/cron/jobs` and the Hermes Ops screen call the function exactly as
  before and receive exactly what they receive today.

---

## Files to Modify

- `src/backend/app/business/hermes/cron_status.py` — the optional pass-through
  and the scope label.
- `src/backend/tests/test_cron_profile_scope.py` (new) — the tests below.

---

## Constraints

- Inherits from parent story.
- **Additive only.** No existing caller is edited and no existing default
  changes; `GET /hermes/cron/jobs` stays root-only under this story
  (`ADR-043` Consequences — fixing it install-wide is deliberately not this
  story's work).
- Do not touch `app/hermes/cron.py` — the library parameter already exists.
- Do not extend or reuse `GET /agents/{id}/jobs`: that is the **Pipeline** job
  tree and has nothing to do with Hermes cron.
- Schedule and last-run outcome come off `CronJob` as it already stands
  (`schedule_display`, `last_run_at`, `last_status`, `last_error`). No run
  history, no authoring.
- Read-only: a missing `jobs.json` means `[]`, never an exception and never a
  created file.

---

## Tests

**Automated tests:** `cd src/backend; pytest tests/test_cron_profile_scope.py`

Use a fake client (`monkeypatch.setattr(client_module, "_client", fake_client)`,
the `tests/test_agent_listing_cost.py` technique) whose `cron.list_cron_jobs`
records the `profile_id` it was given and returns a different engineered job
list per directory.

1. `[REQ-SB-99-US-01-AC-04]` With a root `jobs.json` holding job `R1` and
   `profiles/adnoc-expert/cron/jobs.json` holding job `A1`, assert
   `list_cron_jobs("adnoc-expert")` returns exactly `A1`, carrying its
   `schedule_display`, `last_run_at` and `last_status`, and does **not** contain
   `R1`.
2. `[REQ-SB-99-US-01-AC-04]` Assert `list_cron_jobs()` (no argument) and
   `list_cron_jobs("default")` both resolve the root — the recorded
   `profile_id` passed to `HermesCron` is `None` in both cases — and both return
   exactly `R1`, byte-identical to what the function returned before this change
   (pin the no-argument call's output against the pre-change shape plus the new
   `scope` key only).
3. `[REQ-SB-99-US-01-AC-04]` Assert root-level jobs come back labelled
   `scope: "install"` and a named profile's own jobs `scope: "profile"`, so the
   view can show install-level jobs as such without attributing them to a named
   profile.
4. `[REQ-SB-99-US-01-AC-04]` With no `jobs.json` for the named profile, assert
   `list_cron_jobs("adnoc-expert")` returns `[]` and raises nothing, and that
   `list_cron_jobs()` still returns the root's jobs.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] Optional `profile_id` pass-through, with `default`/`""`/`None` mapped to the root
- [ ] Root vs profile binding labelled truthfully on each returned job
- [ ] `GET /hermes/cron/jobs` and the Hermes Ops screen unchanged
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Making `GET /hermes/cron/jobs` install-wide, or any Hermes Ops change.
- Cron job authoring, scheduling, triggering or run history.
- The per-profile view's own response and route — `T05`.

---

## Context / Notes

`architecture.md` → **§Cron Jobs — Binding Is a Directory, Not a Field** and
`ADR-043`. The architect's correction to the story's own pointer: the app's
cron reader has only ever seen the root profile, so Scenario 4 needs this
additive pass-through, not a filter over an already-complete list.

---

## Implementation Log

_(Filled in by the coder.)_
