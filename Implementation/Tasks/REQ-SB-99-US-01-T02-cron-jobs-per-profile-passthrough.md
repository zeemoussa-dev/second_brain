---
id: REQ-SB-99-US-01-T02
title: cron_status.list_cron_jobs() gains an optional profile_id pass-through, default behaviour unchanged
parent_story: REQ-SB-99-US-01
requirement_id: REQ-SB-99
type: backend
status: Done
gate: flagged
gate_reason: "Four scope-internal judgement calls logged for an optional spot-check — chiefly the additive `scope` key on the existing `GET /hermes/cron/jobs` payload; nothing is blocked."
phase: P2
depends_on: []
created: 2026-10-17
updated: 2026-10-18
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

- [x] Optional `profile_id` pass-through, with `default`/`""`/`None` mapped to the root
- [x] Root vs profile binding labelled truthfully on each returned job
- [x] `GET /hermes/cron/jobs` and the Hermes Ops screen unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      (no entry — the `default`-is-the-root convention is already recorded in
      `ADR-043` and in `cli._profile_args`' own docstring; nothing new emerged)
- [x] `CHANGELOG.md` entry appended

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

**2026-10-18 — built and verified.** Commit `c826512` (code + tests).

### What changed

`app/business/hermes/cron_status.py` only. `list_cron_jobs(profile_id=None)`
resolves the id through a module-level `_profile_dir_id()` —
`{None, "", "default"}` all become `None` — and labels each returned dict
`scope: "install"` (root) or `scope: "profile"` (named). Nothing else in the
file changed; `app/hermes/cron.py` was not touched, and neither was the one
existing caller (`api/hermes_router.py:39`, which still calls it with no
argument).

### Verification — automated mode

Suite: `.venv/Scripts/python.exe -m pytest -q` in `src/backend`.
**Baseline 517 passed / 0 failed** at `02cc49e` (measured before any edit).
**After: 538 passed / 0 failed** — the +21 is 9 of mine plus 12 from another
coder committing into this checkout concurrently. No flakes fired in either run.

| AC-ID | Test (`tests/test_cron_profile_scope.py`) | Observed |
|---|---|---|
| `REQ-SB-99-US-01-AC-04` | `test_a_named_profiles_own_jobs_are_readable_at_last` | PASS — `list_cron_jobs("adnoc-expert")` returns exactly `A1` carrying `schedule_display`/`last_run_at`/`last_status`; `R1` absent; `HermesCron` asked for `adnoc-expert` once |
| `REQ-SB-99-US-01-AC-04` | `test_default_and_no_argument_both_mean_the_install_root_itself` | PASS — recorded `profile_id` is `None` for all three of omitted / `"default"` / `""`, and all three return exactly `R1` |
| `REQ-SB-99-US-01-AC-04` | `test_the_existing_callers_payload_is_unchanged_but_for_the_new_label` | PASS — equals `{**asdict(ROOT_JOB), "scope": "install"}`; the key-set difference from the pre-change shape is exactly `{"scope"}` |
| `REQ-SB-99-US-01-AC-04` | `test_the_hermes_ops_endpoint_still_sees_the_install_root_and_only_that` | PASS — `GET /hermes/cron/jobs` through `TestClient` returns the root's jobs only, asking `HermesCron` for `None` |
| `REQ-SB-99-US-01-AC-04` | `test_each_job_says_which_side_of_the_split_it_came_from` | PASS — root jobs `install`, the named profile's own `profile` |
| `REQ-SB-99-US-01-AC-04` | `test_a_profile_with_no_jobs_json_reads_as_empty_and_creates_nothing` | PASS — `[]`, no exception, no `profiles/` directory created, root still lists `R1` |
| `REQ-SB-99-US-01-AC-04` | `test_binding_is_the_directory_the_jobs_json_lives_in` | PASS — against the real `HermesCron` over a `tmp_path` install: two real `jobs.json` files, each read from its own directory; `"default"` reads the root, not `profiles/default` |

Two further tests carry no AC: `test_one_call_costs_one_stat_one_read_and_no_subprocess`
(`[constraint: cost]`) and `test_no_test_here_can_see_the_operators_real_install`.

### Cost, pinned by equality (`BUG-086` is the measured precedent)

Through counting wrappers on `Path.is_file`/`Path.read_text` plus a
`subprocess.run`/`Popen` tripwire, per call:

- existing `jobs.json`: **1 stat, 1 read, 0 subprocesses** — equality on the
  exact path, so a second listing or a stray executions-db open fails;
- missing `jobs.json`: **1 stat, 0 reads** — a file that is not there is never
  opened;
- the fake client additionally raises on `get_cron_job`,
  `list_cron_executions`, `get_execution_detail` and on **any** non-`cron`
  client attribute, so reaching `cli` (the toolsets subprocess) or `profiles`
  would fail loudly.

### Where reads and writes landed

A scratchpad pytest plugin wrapped `Path.is_file/is_dir/exists/read_text/
read_bytes/open/iterdir/glob/rglob/stat` and `write_text/write_bytes/mkdir/
unlink/rmdir/touch/rename/replace`, plus `subprocess.run`/`Popen`, and recorded
every path resolving under the operator's real `<HERMES_HOME>` (captured at
plugin import, before conftest's per-test sandbox applies). Running this file
under it: **0 reads and 0 writes under the real install.** The only
subprocesses in the run were one `git rev-parse HEAD` (counted twice,
`run` → `Popen`) from importing `app.main`'s `/health` commit lookup — nothing
on the cron path. conftest's suite-wide sandbox was neither weakened nor
bypassed; the two filesystem tests follow its documented escape hatch and point
`settings.hermes_home_path` at their own `tmp_path`.

### Judgement calls (logged for spot-check, not escalations)

1. **`GET /hermes/cron/jobs`'s payload gains the `scope` key.** `AC-04` says
   the endpoint returns "exactly what they return today", while the task's End
   State says every returned dict gains the label and test 2 pins "the
   pre-change shape plus the new `scope` key only". Taken as: same jobs, same
   order, every pre-existing field byte-identical, one additive key. The
   alternative — labelling only on a new per-profile call path — would have
   meant two shapes for one function. The Hermes Ops screen types the response
   as `HermesCronJob[]` and renders named fields, so an unknown extra key is
   inert there.
2. **`""` is mapped to the root too**, though only `default`/`None` are named
   in `cli._profile_args`. An empty id cannot name a directory, and
   `<home>/profiles/` would otherwise be resolved as the "profile".
3. **Two tests run against a real `tmp_path` install** rather than only the
   fake client the task suggested. The fake proves the id that is *passed*; it
   cannot prove `profiles/default` is never resolved, which is the one failure
   `ADR-043` singles out.
4. **`scope` is computed from the resolved id, not from the caller's argument**,
   so `list_cron_jobs("default")` and `list_cron_jobs()` agree by construction.

Nothing was written to `REVIEW-QUEUE.md` or `ESCALATIONS.md`; nothing outside
`## Files to Modify` was touched beyond `CHANGELOG.md` and the status
propagation.
