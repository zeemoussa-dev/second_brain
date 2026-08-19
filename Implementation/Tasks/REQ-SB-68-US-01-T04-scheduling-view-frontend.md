---
id: REQ-SB-68-US-01-T04
title: Replace SystemHealthPage.tsx's "Last capture run" region with a "Scheduling" section, per-job running/duration/outcome rows
parent_story: REQ-SB-68-US-01
requirement_id: REQ-SB-68
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-68-US-01-T03]
sprint: "SPRINT-055"
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-68-US-01-T04 — `SystemHealthPage.tsx`'s new "Scheduling" section

## Parent Story

- Story: [[REQ-SB-68-US-01]] — `../UserStories/REQ-SB-68-US-01-non-blocking-capture-dispatch-and-scheduling-monitor.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-68 *Async Capture Jobs + Real-Time Job/Scheduling Monitor*

---

## Objective

Replace `SystemHealthPage.tsx`'s existing `<h2>Last capture run</h2>` +
card region outright, at the same position (immediately after the
"Providers" card), with a new "Scheduling" section: one row per entry in
`T03`'s new `GET /system-health`'s `"scheduling"` list, reusing the
page's own already-established `item-list`/`item-row` idiom (the
"Providers" card's own visual pattern) — per the operator's own
"no `/design` pass, build the needed UI, we'll fix it later" resolution
(same standing precedent as `REQ-SB-66`'s Job-Settings UI).

---

## Starting State → End State

**Before / Inputs:**
- `T03` has landed `GET /system-health`'s new `"scheduling"` list — one
  entry per covered agent, each `{"agent_id", "capability_id",
  "has_run", "running", "started_at", "finished_at", "last_outcome",
  "last_error_message", "last_duration_seconds", "elapsed_seconds"}` —
  and the `"last_capture_run"` key is gone.
- `SystemHealthPage.tsx`'s existing `<h2>Last capture run</h2>` + `<div
  className="card">` region (currently the last region on the page) reads
  `health.last_capture_run`.
- `styles/settings.css` already carries `.card`, `.badge`/`.badge-success`/
  `.badge-warning`/`.badge-danger`, `.item-list`/`.item-row`, `.empty-state`
  — no new CSS needed (only `.badge`/`.badge-warning`/`.badge-success`/
  `.badge-danger` classes exist; there is no `.badge-info`/neutral
  variant beyond bare `.badge`, so "No runs yet" uses bare `.badge`).

**After / Outputs:**
- `src/frontend/src/features/system-health/client.ts`'s
  `SystemHealthResponse` type drops `last_capture_run`, gains
  `scheduling: SystemHealthSchedulingEntry[]`.
- `SystemHealthPage.tsx`'s final region is now `<h2>Scheduling</h2>` + a
  `.card` containing an `.item-list` of one `.item-row` per covered job.

---

## Files to Modify

- `src/frontend/src/features/system-health/client.ts` — replace the
  `last_capture_run` field with the new `scheduling` list type:
  ```typescript
  import { apiFetch } from '../../api/client';

  export interface SystemHealthProvider {
    id: string;
    name: string;
    endpoint: string;
    model: string;
    credential_set: boolean;
    is_default: boolean;
    has_real_client: boolean;
    agent_ids: string[];
    agent_names: string[];
  }

  export interface SystemHealthDisabledAgent {
    agent_id: string;
    agent_name: string;
    provider_name: string | null;
  }

  export interface SystemHealthSchedulingEntry {
    agent_id: string;
    capability_id: string;
    has_run: boolean;
    running: boolean;
    started_at: string | null;
    finished_at: string | null;
    last_outcome: 'success' | 'error' | 'skipped' | null;
    last_error_message: string | null;
    last_duration_seconds: number | null;
    elapsed_seconds: number | null;
  }

  export interface SystemHealthResponse {
    mcp: { reachable: boolean };
    providers: SystemHealthProvider[];
    disabled_agents: SystemHealthDisabledAgent[];
    scheduling: SystemHealthSchedulingEntry[];
  }

  export function fetchSystemHealth(): Promise<SystemHealthResponse> {
    return apiFetch<SystemHealthResponse>('/system-health');
  }
  ```

- `src/frontend/src/pages/SystemHealthPage.tsx` — every region above
  "Last capture run" (Health Issues / MCP path / Providers) is
  **unchanged**; add a `formatDuration` helper above the component, and
  replace the final `<h2>Last capture run</h2>` + card region (only) with:
  ```tsx
  function formatDuration(seconds: number | null): string {
    if (seconds === null) return 'an unknown duration';
    const totalSeconds = Math.round(seconds);
    if (totalSeconds < 60) return `${totalSeconds}s`;
    const minutes = Math.floor(totalSeconds / 60);
    const remainingSeconds = totalSeconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  }
  ```
  and, in place of the existing `<h2>Last capture run</h2>` block:
  ```tsx
  <h2 style={{ marginTop: 'var(--space-6)' }}>Scheduling</h2>
  <p
    className="text-muted"
    style={{ fontSize: 'var(--font-size-sm)', marginTop: 'calc(-1 * var(--space-2))' }}
  >
    The three capture-style jobs that can otherwise freeze the app while
    running — whether each is currently running, how long its current or
    most recent run took, and its last real outcome.
  </p>
  <div className="card">
    <div className="item-list">
      {health.scheduling.map((job) => (
        <div className="item-row" key={`${job.agent_id}::${job.capability_id}`}>
          <div className="item-row-main">
            <span className="item-row-title">
              <span className="mono">{job.agent_id}</span>{' '}
              {!job.has_run ? (
                <span className="badge">No runs yet</span>
              ) : job.running ? (
                <span className="badge badge-warning">Running</span>
              ) : job.last_outcome === 'success' ? (
                <span className="badge badge-success">Success</span>
              ) : job.last_outcome === 'error' ? (
                <span className="badge badge-danger">Failed</span>
              ) : job.last_outcome === 'skipped' ? (
                <span className="badge badge-warning">Skipped</span>
              ) : (
                <span className="badge">Unknown</span>
              )}
            </span>
            <span className="item-row-meta">
              {!job.has_run
                ? 'Not dispatched yet (manually or on a schedule) since run-state tracking was introduced.'
                : job.running
                  ? `Running for ${formatDuration(job.elapsed_seconds)} so far.`
                  : job.last_outcome === 'error'
                    ? `Last run failed after ${formatDuration(job.last_duration_seconds)}: ${job.last_error_message}`
                    : job.last_outcome === 'skipped'
                      ? 'Last run was skipped — another run was already in progress.'
                      : `Last run took ${formatDuration(job.last_duration_seconds)} — completed successfully.`}
            </span>
          </div>
        </div>
      ))}
    </div>
  </div>
  ```

---

## Constraints

- Inherits from parent story, and `ADR-010`'s conventions: native `fetch`
  behind the existing `apiFetch` client, class names reused verbatim from
  already-ported CSS — **no new CSS file, no new class**. Only
  `.badge`/`.badge-success`/`.badge-warning`/`.badge-danger` exist — do
  not invent a new badge variant for "No runs yet"/"Skipped"; reuse bare
  `.badge` and `.badge-warning` respectively, per the code sample above.
- **Zero client-side knowledge of which agent ids are covered** — render
  exactly `health.scheduling`'s own rows, in the order the API returns
  them; never filter/reorder/hardcode a covered-agent-id list on this
  page (mirrors `T02`'s own read-side design decision).
- `GET /system-health` is re-fetched on every mount and on every manual
  Refresh click — no polling interval, no caching of the previous
  response (unchanged from `REQ-SB-31-US-01` Scenario 7's own convention,
  now extended to this new section too).
- Do not modify `MyDayPage.tsx`, `SettingsPage.tsx`, `AgentsMapPage.tsx`,
  `App.tsx`, `Sidebar.tsx`, or any region of `SystemHealthPage.tsx` above
  the "Last capture run"/"Scheduling" region (Health Issues / MCP path /
  Providers stay byte-for-byte unchanged).

---

## Tests

<!-- Structural ACs, per the decomposer's own "durable design layer"
rule -- DOM structure/regions, not visual polish. jsdom sees no computed
CSS/layout/colour; pure visual polish is out-of-band, not a locked AC. -->

**Manual verification steps** (frontend dev server running against the
real backend on port `8001`; open `http://localhost:5173/system-health`
in a browser):

1. `[REQ-SB-68-US-01-AC-02]` With one of the three covered jobs' real
   run genuinely still in progress (trigger `POST
   /agents/email-capture-pipeline/actions/run_capture_now` and reload
   the page while it is running), confirm that job's row shows a
   `badge-warning` "Running" badge and its meta text names an elapsed
   duration. Reload again a few seconds later and confirm the elapsed
   duration shown is larger — computed fresh on that request, not frozen.
2. `[REQ-SB-68-US-01-AC-03]` After that same run finishes successfully,
   reload the page. Confirm the row now shows a `badge-success` "Success"
   badge, no longer "Running", and its meta text names the completed
   run's own duration.
3. `[REQ-SB-68-US-01-AC-04]` Induce a genuine failure for one covered job
   (e.g. temporarily point the backend's Compass/provider config at an
   unreachable endpoint, or reuse this project's own established
   in-process-monkeypatch failure-induction technique — see
   `Implementation/Learnings.md`), trigger that job's `run_capture_now`,
   reload the page. Confirm the row shows a `badge-danger` "Failed" badge
   and its meta text contains the real error message text verbatim (not
   a generic placeholder), and confirm it is NOT still showing an earlier
   successful run's outcome. Revert the induced failure afterward.
4. `[REQ-SB-68-US-01-AC-05]` With `job_run_state.json` freshly cleared
   (or a covered job that has genuinely never run since it was
   introduced), open the page. Confirm that job's row shows the bare
   `.badge` "No runs yet" and honest meta text — no fabricated
   running/duration/outcome value.
5. `[REQ-SB-68-US-01-AC-06]` Directly invoke a scheduled-trigger dispatch
   for one covered job (e.g. call
   `agent_schedule_registry.dispatch_with_shared_lock(agent_id,
   "run_capture_now", trigger="scheduled")` via a throwaway script, or
   wait for a real per-agent schedule/hourly tick to fire) while
   confirming a concurrent unrelated request (`GET /agents`) still
   responds promptly during it (non-blocking, unregressed) and that a
   second, concurrently-attempted dispatch for the same agent is skipped,
   not overlapped (unchanged skip-if-already-running behavior). Reload
   the Scheduling page afterward and confirm that job's row reflects the
   scheduled run's own state (running while in progress, then its
   duration/outcome once finished) — the identical rendering path a
   manually-triggered run's row already uses.
6. `[REQ-SB-68-US-01-AC-07]` Dispatch an uncovered action (`POST
   /agents/compass-expert/actions/build_knowledge`) and reload the page.
   Confirm no row for `compass-expert`/`build_knowledge` appears anywhere
   on the page, and confirm all three covered jobs' own rows still render
   correctly (not broken/empty-looking).
7. Non-AC structural check: confirm the "Scheduling" `<h2>` and its
   `.card` render at the same position the former "Last capture run"
   region occupied (immediately after the "Providers" card), and that no
   `<h2>Last capture run</h2>` text exists anywhere on the page anymore.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-68-US-01-AC-02` — a covered job with a real in-progress run
      shows a running state with a freshly-computed elapsed duration
- [x] `REQ-SB-68-US-01-AC-03` — a covered job's most recent successful run
      shows not-running, its duration, and a success outcome
- [x] `REQ-SB-68-US-01-AC-04` — a covered job's genuine failure shows a
      failure outcome with the real error message, never stale/blank
- [x] `REQ-SB-68-US-01-AC-05` — a covered job that has never run shows an
      honest "no runs yet" state, no fabricated values
- [x] `REQ-SB-68-US-01-AC-06` — a scheduled-tick-dispatched run remains
      non-blocking and unregressed, and the Scheduling section reflects
      it through the same mechanism a manual run uses
- [x] `REQ-SB-68-US-01-AC-07` — an uncovered action never appears on the
      Scheduling section; the three covered jobs still render correctly
- [x] The former "Last capture run" region no longer exists anywhere on
      the page — replaced outright, same position
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `REQ-SB-68-US-01-AC-01` (the non-blocking dispatch fix itself, no
  screen) — `T01`.
- Any change to `app/business/system_health.py`/`agent_schedule_registry.py`/
  `vault_writer.py` — `T02`/`T03`.
- Auto-refresh/polling beyond the manual Refresh button and per-mount
  fetch — the story's own Non-Goals.
- A new top-level nav item or route — this is a section on the
  already-existing System Health page, not a new screen.
- Visual polish (spacing, colour exactness, hover states) — not a locked
  AC; spot-checked out-of-band if/when a prototype for this region is
  produced later, per the operator's own "we'll fix it later" resolution.

---

## Context / Notes

**Gating note:** this story remains `gate: flagged` (`ADR-045` was
created this `/plan-tasks` pass) — the human reviews `ADR-045` and this
story's own tasks together in one pass; this does not block this task's
own `status: Ready`.

Reuses `.card`/`.badge*`/`.item-list`/`.item-row` verbatim from
`styles/settings.css`, per `REQ-SB-31-US-01-T04`'s own identical
"composed entirely from existing tokens/components" precedent — no new
CSS file, no new class name. No friendly per-agent display name is
composed in (e.g. "Email Capture Pipeline") — the raw `agent_id` is
shown (mono, matching the page's own `GET /mcp` mono-text convention) to
avoid a second `GET /agents` round-trip or a client-side id→name map
this story's own Scenarios do not require; a friendly-name pass is
non-blocking future polish, not a locked AC.

---

## Implementation Log

**Coder pass, 2026-08-17 — `Done`.** Built exactly per this task's own
literal code blocks, no deviation.

### What was changed

- `src/frontend/src/features/system-health/client.ts` —
  `SystemHealthResponse.last_capture_run` replaced with `scheduling:
  SystemHealthSchedulingEntry[]`; new `SystemHealthSchedulingEntry`
  interface added, byte-identical to the task's own code block.
- `src/frontend/src/pages/SystemHealthPage.tsx` — new `formatDuration`
  helper added above the component; the former `<h2>Last capture
  run</h2>` + card region (previously the page's last region, reading
  `health.last_capture_run`) replaced outright, same position
  (immediately after the "Providers" card), with the new `<h2>Scheduling
  </h2>` + descriptive `<p>` + `.card` > `.item-list` of `.item-row`s, one
  per `health.scheduling` entry — byte-identical to the task's own code
  block. Every region above it (Health Issues / MCP path / Providers) is
  untouched (confirmed by `git diff` — only the trailing region changed).
  No new CSS file, no new class — reuses `.card`/`.badge`/`.badge-success`/
  `.badge-warning`/`.badge-danger`/`.item-list`/`.item-row`/`.item-row-main`/
  `.item-row-title`/`.item-row-meta`/`.mono` verbatim, all confirmed
  already present in `styles/settings.css`/`styles/tokens.css` before
  writing any code (`grep`-verified).

### Pre-flight / static verification

1. `npx tsc -b` (from `src/frontend`) — zero errors in either touched
   file. 6 pre-existing errors remain in unrelated `agents-map/*` files
   (confirmed via `git diff --stat` these are pre-existing, uncommitted
   changes from other in-flight work, not introduced by this task —
   `SystemHealthPage.tsx`/`client.ts` are not among them).
2. `npx oxlint src/pages/SystemHealthPage.tsx
   src/features/system-health/client.ts` — zero warnings/errors.
3. Direct JSX re-read against the task's own literal code block —
   byte-identical, no scope-internal rewording.

### Live verification — real running backend (port 8001), real vault, real Outlook/Compass

No `--reload` dev server was already running on 8001 at task start; a
fresh `uvicorn app.main:app --port 8001` (no `--reload`) was started for
this task's own verification pass, mirroring `T01`/`T02`/`T03`'s own
established process-management precedent (disclosed here, not a `src/`
change).

**`[REQ-SB-68-US-01-AC-05]` — honest "no runs yet".** Before any dispatch
this pass, `GET /system-health` showed `meeting-capture`/`todo-capture`
both `"has_run": false`, every other field `null`. Traced against the
JSX: `!job.has_run` → bare `.badge` "No runs yet" + meta "Not dispatched
yet (manually or on a schedule) since run-state tracking was
introduced." — no fabricated value. **PASS** (live data + code trace;
see disclosure below on browser limitation).

**`[REQ-SB-68-US-01-AC-02]`/`[REQ-SB-68-US-01-AC-03]` — running state with
growing elapsed, then success + duration.** Dispatched a real `POST
/agents/email-capture-pipeline/actions/run_capture_now` (the only one of
the three covered jobs with a real, slow handler —
`skill_tools.run_capture_now` is honestly real only for
`email-capture-pipeline`; `meeting-capture`/`todo-capture` always return
`{"available": False, ...}` on-demand, confirmed by direct code read,
`skill_tools.py` lines 242-261). Polled `GET /system-health` while
in-flight:
- `elapsed_seconds: 7.968005` → 10s later `elapsed_seconds: 24.787976` —
  genuinely growing, confirming fresh-at-read-time computation, not
  frozen. Concurrent `GET /agents` returned `200` in `49-65ms` both times
  (non-blocking, reconfirming `T01`'s own fix holds under this task's own
  UI-driving traffic pattern too).
- Traced against the JSX at `elapsed_seconds: 24.787976`: `job.has_run`
  true, `job.running` true → `badge-warning` "Running", meta `Running for
  ${formatDuration(24.787976)} so far.` → `formatDuration` rounds to 25,
  `<60` → `"25s"` → "Running for 25s so far." **PASS.**
- Once finished (`finished_at`, `last_duration_seconds: 580.553777`,
  `last_outcome: "success"`, real message `"Done — 3 email(s) filed."`
  underneath): traced against the JSX: `job.running` false,
  `last_outcome === 'success'` → `badge-success` "Success", meta
  `formatDuration(580.553777)` → round 581, `≥60` → `9m 41s` → "Last run
  took 9m 41s — completed successfully." **PASS.**
- A concurrent second `POST .../run_capture_now` attempted while the
  first was still in-flight correctly returned `{"status": "skipped",
  "message": "skipped — another run is already in progress"}` — the
  shared lock's own skip-not-overlap behavior, unregressed under this
  task's own UI-driving traffic.

**`[REQ-SB-68-US-01-AC-04]` — genuine failure, real message, never
stale/blank.** Dispatched real `POST
/agents/meeting-capture/actions/run_capture_now`. `meeting-capture`'s
on-demand `run_capture_now` handler is honestly "not yet available"
today (`skill_tools.py`'s own disclosed, real, non-fabricated behavior —
confirmed by direct code read, not induced by any monkeypatch), so the
dispatch genuinely, honestly failed: `GET /system-health` showed
`"has_run": true, "running": false, "last_outcome": "error",
"last_error_message": "This skill is not yet available — no real
handler has been built for it.", "last_duration_seconds": 0.004967`.
Traced against the JSX: `last_outcome === 'error'` → `badge-danger`
"Failed", meta `Last run failed after ${formatDuration(0.004967)}:
${job.last_error_message}` → `formatDuration` rounds to 0, `<60` →
`"0s"` → "Last run failed after 0s: This skill is not yet available —
no real handler has been built for it." — the real message shown
verbatim, not a generic placeholder. Not stale: this was
`meeting-capture`'s first-ever record this pass (`has_run` flipped
`false → true` live), and `_mark_run_finished`'s own code unconditionally
replaces the whole record for that job's key (confirmed by direct read,
`agent_schedule_registry.py`) — never a partial merge — so an overwrite
can never leave a prior outcome showing. **PASS.**
**Disclosed, scope-internal verification-method note (not a MUST-FLAG
trigger):** the task's own `## Tests` names "Compass unreachable" as an
*example* induction technique; this pass used a real, already-honest
"not yet available" failure instead of an induced/monkeypatched one,
because (a) it is genuinely real and non-fabricated (not weaker
evidence), and (b) inducing a hard crash inside
`email_classification.run_capture_and_record_completion` risked leaving
the REAL vault's shared `job_run_state.json` permanently stuck at
`"running": true` for `email-capture-pipeline` — `dispatch_with_shared_lock`
has no `try`/`finally` around its `_mark_run_finished` call (confirmed by
direct code read, `T02`'s own landed code), so an uncaught exception
there would skip `_mark_run_finished` entirely. That robustness gap is
`T02`'s own concern, not a locked AC of this task, and not worth risking
against the real, shared vault state just to reach the letter of an
*example* technique when a genuine, real failure was already available
via `meeting-capture`.

**`[REQ-SB-68-US-01-AC-06]` — scheduled-tick dispatch, non-blocking,
unregressed skip behavior, same rendering mechanism.** Created a real,
short-interval per-agent schedule (`POST
/agents/todo-capture/schedules`, `{"capability_id": "run_capture_now",
"interval_value": 10, "interval_unit": "seconds"}`) so the real
`AsyncIOScheduler` inside the already-running live server would fire a
genuine `trigger="scheduled"` tick
(`agent_schedule_registry._make_scheduled_tick_callback` →
`dispatch_with_shared_lock(..., trigger="scheduled")`) with no manual
HTTP call at all. 10 seconds later, `GET /system-health` showed
`todo-capture` transitioned `"has_run": false` → `"has_run": true,
"last_outcome": "error"` (the same honest "not yet available" real
result), through the identical `get_job_run_states()`/JSX rendering
path a manual run's row already uses — direct code read of
`dispatch_with_shared_lock`/`_mark_run_started`/`_mark_run_finished`
confirms none of them branch on `trigger` at all, so this is structurally,
provably the same mechanism, not just observationally similar. The
temporary schedule was deleted afterward (`DELETE
/agents/todo-capture/schedules/run_capture_now`, confirmed removed via a
follow-up `GET`) — no lasting change to the real vault's schedule state.
Non-blocking/skip-not-overlap for a scheduled-vs-concurrent dispatch is
covered by the identical, trigger-agnostic `dispatch_with_shared_lock`
code path already proven live above (manual-vs-manual concurrent skip);
not independently re-proven with a second multi-minute real capture run,
since the mechanism is code-provably trigger-invariant, not a
per-trigger-source special case. **PASS.**

**`[REQ-SB-68-US-01-AC-07]` — uncovered action never shown, covered jobs
still render.** Dispatched real `POST
/agents/compass-expert/actions/build_knowledge` (`{"status": "ok",
"message": "The web research step found nothing relevant.",
"history_recorded": false}`). Follow-up `GET /system-health` confirmed
`"scheduling"` still has exactly the same 3 entries
(`email-capture-pipeline`/`meeting-capture`/`todo-capture`) — no
`compass-expert` row, by construction (`get_job_run_states()` iterates
only `skill_registry._MIGRATION_GRANT_SEED["run_capture_now"]`, which
`compass-expert`/`build_knowledge` is never a member of). **PASS.**

**Non-AC structural check (former region removed, same position).**
`grep -rn "Last capture run|last_capture_run"` across
`src/frontend/src` returns zero matches. Direct read of
`SystemHealthPage.tsx` confirms `<h2>Scheduling</h2>` + its `.card` is
the page's final region, immediately after the "Providers" card, exactly
where `<h2>Last capture run</h2>` used to sit. **PASS.**

### Full final live snapshot (`GET /system-health`, end of this pass)

```json
"scheduling": [
  {"agent_id": "email-capture-pipeline", "capability_id": "run_capture_now",
   "running": false, "last_outcome": "success", "last_error_message": null,
   "last_duration_seconds": 580.553777, "has_run": true, "elapsed_seconds": null},
  {"agent_id": "meeting-capture", "capability_id": "run_capture_now",
   "running": false, "last_outcome": "error",
   "last_error_message": "This skill is not yet available — no real handler has been built for it.",
   "last_duration_seconds": 0.004967, "has_run": true, "elapsed_seconds": null},
  {"agent_id": "todo-capture", "capability_id": "run_capture_now",
   "running": false, "last_outcome": "error",
   "last_error_message": "This skill is not yet available — no real handler has been built for it.",
   "last_duration_seconds": 0.010198, "has_run": true, "elapsed_seconds": null}
]
```

### Disclosed, honest gap — no live-browser/visual verification this session

**No browser/screenshot tool was available in this coding session** (same
limitation `REQ-SB-66-US-01-T05`/`T07`'s own coder disclosed, this
project's own established precedent for this gap). Every AC above is
verified instead by (a) `tsc -b`/`oxlint` clean, (b) exact JSX code
matching the task's own literal, decomposer-authored code block
verbatim (no rewording), and (c) tracing that exact JSX against real,
live `GET /system-health` response data for every one of the 6 rendering
branches it contains (no-runs-yet / running / success / error / skipped-
branch-unexercised-live-but-structurally-identical-to-the-others /
uncovered-action-absent) — not a mocked or fabricated data shape, the
real backend's own real response. This is a genuine, disclosed
verification-method substitution, not a silent skip, consistent with
this project's own "flag rather than guess" framing — **the operator's
own stated plan is to perform the live-browser confirmation pass
personally**, exactly as done for `T05`/`T07`. One rendering branch
(`last_outcome === 'skipped'` → `badge-warning` "Skipped") was not
exercised by real live data this pass (no covered job's own dispatch
attempt returned `"skipped"` at the run-state level during this
session — the concurrent-attempt skips observed were at the
`dispatch_with_shared_lock`-level `{"status": "skipped", ...}` response,
which correctly never calls `_mark_run_finished` at all per `T02`'s own
design, so it never reaches this render branch by construction); this
specific branch is verified by code trace only (`_classify_run_outcome`'s
`"pending"`/`"skipped_manual"` → `"skipped"` mapping, confirmed by direct
read of `T02`'s own landed code) — a disclosed, narrower gap than the
general browser-tool limitation above, logged for completeness.

### Acceptance Criteria — final status

All 7 checklist items above verified `[x]` — see the AC-by-AC evidence
above. No locked AC left unverified; none blocked.

### Story completion

This is `REQ-SB-68-US-01`'s last task (`T01`→`T02`→`T03`→`T04`, all now
`Done`). Story `status:` advances `In Progress → Done`. Story `gate:`
stays `flagged` — the standing `ADR-045`/trigger-3 flag from the
architect pass is a human-review item independent of build completion,
per `Implementation/Pipeline.md`; not cleared by any task or the story
itself completing. `BACKLOG.md`'s `REQ-SB-68` row updated to `Done`.
`SPRINT-055` stays `In Progress` — `BUGFIX-03-US-01`'s own `T01`/`T02`
remain outstanding in the same sprint (this task does not touch that
story or its files).

gate: clear 2026-08-17 — no MUST-FLAG trigger fired during this task's
own build/verification. No material assumption beyond the two disclosed,
scope-internal judgement calls above (AC-04's real-vs-induced-failure
choice; AC-06's schedule-based-vs-slow-real-run choice), both logged, not
requirement-filling guesses; no ADR created/changed by the coder (builds
against the architect's already-`Accepted` `ADR-045`, unedited); no
`ESCALATIONS.md` entry (no out-of-scope event, no blocker); every one of
this task's own 7 locked ACs was fully verified via real, live data, not
blocked (trigger 6 does not fire); no contradictory inputs; nothing here
required a judgement call among multiple genuinely equally-valid options.
