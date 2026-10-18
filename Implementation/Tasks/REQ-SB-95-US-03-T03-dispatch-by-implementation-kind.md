---
id: REQ-SB-95-US-03-T03
title: Dispatch by implementation kind — http performed, ui pointed at, skill authorised via single-use grant
parent_story: REQ-SB-95-US-03
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "ESC-073 Resolved -- the scope extension was authorised, `http` is wired, and every locked AC verifies (502 passed, 0 failed; `AC-02` test 1 now runs end to end through `POST /actions/{id}/call`, and manual step 1 passed against a disposable install on 127.0.0.1:8013, never the operator's :8001). Nothing is blocked. Still flagged for a human spot-check of the scope-internal judgement calls in the Implementation Log -- the largest being that `http` is performed IN PROCESS over httpx.ASGITransport rather than over a loopback socket to 127.0.0.1:8001, and, new in this pass, that the gate test file now imports `tests/test_action_dispatch.py` to reuse a shared harmless target route rather than registering a second one of its own."
phase: P2
depends_on: [REQ-SB-95-US-03-T02]
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-03-T03 — Dispatch by Implementation Kind

## Parent Story

- Story: [[REQ-SB-95-US-03]] — `../UserStories/REQ-SB-95-US-03-published-catalogue-and-call-enforcement.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Make a validated call actually do the thing — performing what the app owns,
authorising what it does not, and pointing at what only the operator can do.

---

## Starting State → End State

**Before / Inputs:**

- `T02`'s gate validates and hands off to a dispatch seam that performs nothing
  yet.
- `ADR-019` keeps `business/core/skills/catalog/` as payload the app never
  imports — the app is not a second executor of Skill payload.

**After / Outputs:**

- `action_invocation.py` dispatches on the Action's one implementation kind:
  - **`http`** — performed by the app against its own route, with the validated
    inputs; the real result is returned and recorded as `performed`.
  - **`ui`** — **never performed**: the response names where the operator does
    it, and the ledger records that it was pointed at, not done.
  - **`skill`** — **authorised, not performed**: the response carries a
    single-use grant naming the deployed Skill and the validated inputs, which
    the runner performs in the profile where Skills already run; the ledger
    records the authorisation and, when the runner reports back, the outcome.
- No dispatch path imports or executes anything under `skills/catalog/`.

---

## Files to Modify

- `src/backend/app/business/logic/action_invocation.py`
- `src/backend/app/data_access/action_calls.py` (grant fields, if the record shape needs them)
- `src/backend/tests/test_action_dispatch.py` (new)
- `src/backend/tests/test_action_invocation_gate.py` (added 2026-10-18 by the
  scope extension at the end of this file; `ESC-073`, three named changes only)

---

## Constraints

- Inherits from parent story.
- **The app does not perform what it does not own** (`ADR-033`). A `skill`
  implementation is authorised only; a `ui` implementation is never performed.
- `ADR-019` is binding: no import of `skills/catalog/` payload, no subprocess
  execution of a Skill script from the app.
- A grant is **single-use** — the consumption mechanics are shared with `T04`'s
  confirmation grant; build one mechanism, not two.
- Nothing half-performed: a dispatch that fails records an honest failure
  outcome and never reports `performed`.

---

## Tests

**Automated tests** — `src/backend/tests/test_action_dispatch.py`, run with
`pytest tests/test_action_dispatch.py` from `src/backend`.

1. `[REQ-SB-95-US-03-AC-02]` Call an `http`-implementation Action with valid
   inputs through `POST /actions/{id}/call` over
   `httpx.ASGITransport(app=app)`; assert the app really performed the route
   (the target function was entered with the validated inputs), the response
   carries its real result, and the ledger record says `performed`.
2. `[REQ-SB-95-US-03-AC-02]` Call a `skill`-implementation Action; assert the
   response carries a single-use grant naming the deployed Skill and the
   validated inputs, that nothing under `skills/catalog/` was imported or
   executed, and that the ledger records an authorisation rather than a
   performance.
3. `[REQ-SB-95-US-03-AC-02]` Consume that grant once, then attempt to consume it
   a second time; assert the second attempt is refused.
4. `[REQ-SB-95-US-03-AC-02]` Call a `ui`-implementation Action; assert nothing
   was performed, the response names where the operator performs it, and the
   ledger says so.
5. `[REQ-SB-95-US-03-AC-02]` Induce a failure inside an `http` dispatch (scoped
   in-process monkeypatch, this project's established technique); assert the
   outcome recorded is an honest failure, never `performed`.

**Manual verification steps:**

1. `[REQ-SB-95-US-03-AC-02]` With the backend running, call a real
   `http`-implementation Action over loopback and confirm the operator sees the
   real result of the real operation (check the real side effect, not the
   response text alone).

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Three dispatch paths, each behaving exactly as `ADR-033` decides — all three
      wired and verified end to end through `POST /actions/{id}/call`
- [x] Single-use grant minted for `skill`, consumable exactly once
- [x] No `skills/catalog/` payload imported or executed by the app
- [x] Honest failure outcomes; nothing half-performed
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Confirmation-required Actions — `T04`.
- The runner Skill that consumes the grant — `T05`.

---

## Context / Notes

`architecture.md` → **§The Action Call Gate**, "Dispatch by kind". `ADR-033`'s
second decision bullet is the exact contract, including why the app must not
become a second executor of Skill payload.

---

## Implementation Log

**Coder, 2026-10-18 — `Blocked` (`ESC-073`).** Two of the three dispatch paths
and the whole single-use grant mechanism are built, verified and committed. The
third, `http`, is built and proved at the unit it owns but **deliberately not
wired into the seam**, because wiring it requires a file outside this task's
`## Files to Modify`.

### Verification

Baseline measured before the first edit: **490 passed**, 0 failed (`pytest -q`,
`src/backend`, 21.37s, at `77321d7`). Final: **497 passed**, 0 failed (53.36s) —
the seven new tests in `tests/test_action_dispatch.py` and nothing else moved.
Neither known flake (`test_health_check.py`, `test_marketplace_source.py`) fired
in any run. No frontend file was touched.

**Where this task's writes and calls land, proved BEFORE the suite was run with
the new code.** A pytest plugin captured the three real roots at import time and
wrapped `builtins.open`, `Path.open/write_text/write_bytes/mkdir/unlink/rename/
replace/touch/rmdir`, `os.remove/rename/replace/makedirs/mkdir/unlink` and
`shutil.rmtree/copyfile/copy/copy2/copytree/move`, plus — because this task
dispatches `http` — every `socket.socket.connect`, every real
`httpx.HTTPTransport.handle_request`, every `urllib.request.urlopen`, every
`subprocess` entry point, and the four Hermes write seams.

Running **this task's two files** (`test_action_dispatch.py` +
`test_action_invocation_gate.py`) under it:

- 173 write calls intercepted; **0 inside the real data path, 0 inside the real
  vault, 0 inside the real Hermes home.** Every one landed under pytest's own
  `tmp_path`, including the ledger records and the new `ActionCalls/_claims/`
  markers.
- **0 real httpx or urllib requests.** The `http` dispatch opens no socket at
  all: `ASGITransport` hands the request to the application object in process.
- 21 socket connects, all `('127.0.0.1', <ephemeral>)` — `asyncio`'s own
  self-pipe, one pair per event loop `asyncio.run()` creates. **No address
  mentioning 8001**, so no test could have reached the operator's running
  backend.
- 2 subprocesses, both `git rev-parse HEAD` from the health route at import.
  None from dispatch.
- 9 Hermes seam entries, all `AgentManager.publish_action_catalogue` fired in the
  background by the `POST /actions` saves the tests make — contained by `T01`'s
  suite-wide sandbox, which is why they produced 0 writes in the real install.

Across the **whole suite** under the same interceptor: 0 writes in the real
vault, 0 in the real Hermes home, 18 in the real data path (all pre-existing
`mkdir(exist_ok=True)` from other files — this task's two files produce 0), and
`any address mentioning 8001: []`.

| AC-ID | Step | Observed |
|---|---|---|
| `REQ-SB-95-US-03-AC-02` | Automated test 1 — an `http` implementation is really performed | **Partial — built and proved, not wired.** `test_an_http_implementation_is_really_performed_by_the_app_and_reported_performed` drives `_perform_http_implementation()` directly at a test-only route this file registers on the real app. The target function was entered exactly once with `{"folder": "Projects", "note": "kickoff", "urgent": True}` — the input the route declares as a path parameter bound into the path, the other two in the body — and the real result `{"filed": "Projects/kickoff", "urgent": True}` came back, with the outcome `performed`. **What is NOT verified: the same thing through `POST /actions/{action_id}/call`**, because the seam's `http` branch still reports `not_dispatched` (`ESC-073`). This is the one reason the task is not `Done`. |
| `REQ-SB-95-US-03-AC-02` | Automated test 2 — a `skill` implementation is authorised, not performed | **Pass.** `POST /actions/capture-the-thread/call` → 200, `accepted: true`, `outcome: "authorised"` — explicitly asserted `!= "performed"`. The grant is exactly `{"skill_id": "email-thread-capture", "caller_agent_id": "cbo-agent", "inputs": {"thread_id": "AAMk-0042"}, "granted_at": …, "call_id": …, "single_use": true}`. The set of loaded `skills/catalog/` modules was **unchanged across the dispatch**, and the test runs with `subprocess.Popen/run/call/check_call/check_output` and `os.system` all raising, so no Skill could have been executed unnoticed. The ledger record says `authorised`, carries the grant, and its `result` is `null`. |
| `REQ-SB-95-US-03-AC-02` | Automated test 3 — the grant is consumed once, refused twice | **Pass.** The first `consume_single_use_grant(call_id, reported_outcome="performed", …)` returned `consumed: True` and handed back the skill id and the granted inputs. The second, on the same `call_id`, returned `consumed: False` with *"the grant on action call … has already been consumed; a grant is single-use, so nothing was performed this time"* and `grant: None`. The ledger record afterwards carries the runner's reported outcome and a `grant.consumed_at`. A fourth test proves the same mechanism refuses a `call_id` it never granted anything to, rather than inventing an authorisation. |
| `REQ-SB-95-US-03-AC-02` | Automated test 4 — a `ui` implementation is pointed at, never performed | **Pass.** `POST /actions/export-the-artifacts/call` → 200, `outcome: "pointed_at"` (asserted `!= "performed"`), `where_the_operator_does_it: "/settings/artifacts"`, and the same key named in the detail sentence: *"… is something only the operator can do, on this app's '/settings/artifacts' screen. Nothing was performed — tell the operator to go there."* The test-only target route recorded **zero** entries, so nothing ran. The ledger says `pointed_at` with `result: null` and `grant: null`. |
| `REQ-SB-95-US-03-AC-02` | Automated test 5 — an induced failure inside an `http` dispatch | **Pass.** A scoped `monkeypatch` over the business function behind the test-only route made it raise. The route was really reached, the app's own error middleware turned it into a 500, and dispatch reported `outcome: "failed"` (asserted `!= "performed"`) with *"… answered HTTP 500, so the operation did NOT happen"*. The target recorded zero successful entries and no error body was passed off as a result. A sixth test covers the other half of "nothing half-performed": an `http` implementation naming the **call gate's own route** is reported `failed` rather than recursing into the gate without end. |
| `REQ-SB-95-US-03-AC-02` | **Manual step 1** — a real `http` Action over loopback against the running backend | **Not performed — blocked.** The seam does not route to the `http` performer yet, so a real loopback call would observe the withheld `not_dispatched` answer rather than the behaviour the step asks about. It is the first thing to run once `ESC-073` is authorised. |

### The blocker, measured rather than estimated

Wiring the `http` branch was implemented in full and run before being withheld.
With it live, exactly **one** test fails —
`test_action_invocation_gate.py::test_a_valid_call_passes_the_gate_records_it_and_enters_dispatch_exactly_once`,
`assert 'performed' == 'not_dispatched'` — which is the transitional assertion
`T02`'s own log assigns to `T03`. The second problem is the silent one: that
file's wildcard test points its Action at the **real** `POST
/vault-index/refresh`, so live dispatch really re-reads the operator's whole
vault on every run (**1.09s → 8.60s** for that file alone, several sessions
running `pytest` here all day). Both fixes live in
`src/backend/tests/test_action_invocation_gate.py`, which is not in this task's
`## Files to Modify`. Full detail and the exact remedy in `ESC-073`.

Meanwhile the `http` branch reports `not_dispatched` — **precisely what `T02`
already shipped for every kind** — so nothing regressed and nothing claims to
have run.

### Judgement calls inside scope (for human spot-check)

1. **`http` is performed IN PROCESS over `httpx.ASGITransport(app=app)`, not
   over a loopback socket to `127.0.0.1:8001`.** The biggest call here.
   `ADR-033` says "`http` is performed by the app"; in process makes that mean
   *this* app, not whatever is listening on that port — a second install, a
   stale process, or the operator's own backend during a test run. It needs no
   port, so a moved port or a reverse proxy changes nothing, and it is provably
   unreachable from a test (0 real httpx/urllib calls, measured). `app.main` is
   imported inside the function for the cycle reason `app_route_table()` already
   documents, and `asyncio.run()` is driven from the synchronous caller the way
   `AgentManager._reload_registry` already does. This is **not** a replacement
   for the loopback hop a deployed Skill makes from the Hermes side — that stays
   `SECOND_BRAIN_API_URL`.
2. **The wire mapping of validated inputs is a declared convention, because
   nothing in the catalogue says one.** An input whose name appears as a path
   parameter in the route is bound into the path (URL-quoted, since an input is
   operator data); the rest travel as a JSON body on `POST`/`PUT`/`PATCH` and as
   query parameters otherwise. An input consumed by the path is **not** sent
   again, or the route would see the same name twice.
3. **Four outcome words, not one.** `performed`, `pointed_at`, `authorised` and
   `failed` extend `ADR-033`'s four values because the app does three different
   things and collapsing them would let "the operator still has to do this
   themselves" read as "done" — which is the story's whole subject. `accepted`
   stays the only field a caller branches on, exactly as `T02` fixed it, and the
   refusal vocabulary was **not** widened: every gate refusal is still one `409`
   carrying the verdict, and a dispatch failure is a `200` with
   `accepted: true, outcome: "failed"`, because the gate genuinely was passed.
4. **The seam's signature is untouched, and the `call_id` is stamped onto the
   grant by `call_action` rather than passed into the seam.** `T02`'s contract
   was that `T03` changes only `dispatch_validated_action_call`'s body; the gate
   owns the `call_id`, the seam decides only *what* is granted. The
   twice-written ledger is preserved unchanged — `validated` before the seam,
   the real outcome after.
5. **An `http` Action naming the call gate's own route is refused by name**
   rather than dispatched. That route is on the live route table, so such an
   Action saves cleanly today; dispatching it would re-enter the gate without
   end, one fresh event loop and worker thread per level. Narrow, named, and
   covered by a test.
6. **The "nothing under `skills/catalog/` was imported" assertion compares the
   loaded set across the dispatch rather than requiring it to be empty.**
   Another test file legitimately imports a payload script by path to test it
   (`build_vault_index`), and `sys.modules` is shared across the run — measured
   when the absolute form passed alone and failed in the full suite. What
   `ADR-019` forbids is the **app** importing one, which is exactly what the
   difference measures.

### Not done here, deliberately

- **Confirmation is untouched** (`T04`). The single-use mechanism it needs is
  built and shipped: `consume_single_use_grant()` over
  `action_calls.claim_call_once()`. `T04` should spend its confirmation grant
  through that function, not add a second mechanism — and the confirmation check
  still belongs between a complete validation and the dispatch seam, where
  `T02`'s comment marks the spot.
- **No route exposes grant consumption**, because `actions_router.py` is in
  `T04`'s `## Files to Modify` and not in this one's. `T05`'s runner reports back
  through whichever route `T04` adds.
- **Nothing under `skills/catalog/` was created, imported or executed** — the
  runner Skill is `T05`'s.

---

## Scope extension — 2026-10-18 (unblocks `ESC-073`)

**Added to `## Files to Modify`:** `src/backend/tests/test_action_invocation_gate.py`.

Three changes only, all named in `ESC-073`:

1. The two assertions expecting `not_dispatched` become `performed` — `T02`'s own
   Implementation Log calls them transitional and assigns them to this task.
2. **Repoint the wildcard test's Action away from the real `POST /vault-index/refresh`**
   to the harmless test-only route `tests/test_action_dispatch.py` already registers.
   This one is not bookkeeping: with dispatch live, that test re-reads the operator's
   whole vault on every suite run, measured at 1.09s -> 8.60s for that file alone, on a
   machine where several sessions run `pytest` continuously.
3. Route the `http` branch to `_perform_http_implementation()` — the line withheld.

Nothing else in that file is in scope. The twice-written ledger, the single 409 refusal
shape and the seam's signature are `T02`'s contract and stay exactly as they are.

**Then finish the task's own verification:** `AC-02`'s test 1 end to end through
`POST /actions/{id}/call`, and manual step 1 against a real loopback `http` Action. If
the manual step needs a running backend, use a disposable instance on another port as
`REQ-SB-95-US-02-T06` did — never the operator's :8001.

---

## Implementation Log — the scope extension (`Done`)

**Coder, 2026-10-18 — `Blocked` → `Done`.** The three authorised changes landed,
`http` is wired, and every locked AC now verifies. Commit `66902a7`.

### What changed

1. **The seam's `http` branch calls `_perform_http_implementation()`** — the one
   withheld line. The performer itself is untouched; so are the twice-written
   ledger, the single-409 refusal shape, the seam's signature and `T01`'s
   suite-wide Hermes sandbox.
2. **The gate test's two transitional assertions now read `performed`** — the
   verdict's and the ledger record's — plus the `detail` assertion beside them,
   which named the withheld "not implemented yet" sentence. The verdict's
   **real result** is asserted too, so `performed` cannot pass without a route
   having actually answered.
3. **The gate test's Action is off `POST /vault-index/refresh`.** It now names a
   harmless test-only target that `tests/test_action_dispatch.py` registers and
   this task added for the purpose (`POST /__test_action_target_any_inputs`,
   which accepts any inputs and echoes them back); the gate file imports that
   module for the registration side effect. The file's own `A_REAL_ROUTE` was
   renamed `THE_HARMLESS_TARGET_ROUTE`, since a constant that keeps a test
   Action off a real route cannot be called "the real route".
4. **`AC-02` test 1 moved onto the shipped path** — end to end through
   `POST /actions/{action_id}/call` instead of driving the performer directly —
   and now asserts the ledger record as well as the verdict. No test was added
   or removed; one was converted.
5. The stale "built but not wired / `ESC-073`" paragraphs were removed from the
   module and function docstrings, and the one thing wiring really changed was
   recorded in their place: a test Action now really runs what it names.

### Verification

**Baseline measured before the first edit: 502 passed, 0 failed (29.68s).**
Final: **502 passed, 0 failed (34.10s)**. Neither known flake
(`test_health_check.py`, `test_marketplace_source.py`) fired in any of the four
full runs. `test_screen_build_lock.py::test_a_second_build_waits_for_the_first`
— another session's, reported failing when this task was handed over — **passed
in every run here**, including the baseline taken before any edit of mine. No
frontend file was touched.

The two files alone: **13 passed, 0.98s**. The gate file alone: **6 passed,
3.25s**, of which the two dispatching tests cost **0.05s and 0.03s** — the
8.60s vault re-read is gone, and ~3s of that total is importing the app at
collection, not running anything.

**Where writes and outbound calls land, re-measured with `http` dispatch LIVE
and before the suite was run with it.** The same interceptor as the first pass:
`builtins.open`, `Path.open/write_text/write_bytes/mkdir/unlink/rename/replace/
touch/rmdir`, `os.remove/rename/replace/makedirs/mkdir/unlink`,
`shutil.rmtree/copyfile/copy/copy2/copytree/move`, every `socket.socket.connect`,
every real `httpx.HTTPTransport.handle_request`, every `urllib.request.urlopen`,
every `subprocess` entry point, and `HermesProfiles.write_soul/update`.

- **This task's two files** — 1513 write calls intercepted; **0 in the real data
  path, 0 in the real vault, 0 in the real Hermes home**. **0 real httpx
  requests, 0 urlopen** (`ASGITransport` hands the request to the application
  object in process, so performing an `http` Action opens no socket at all). 25
  socket connects, every one an ephemeral `127.0.0.1` `asyncio` self-pipe;
  **`any address mentioning 8001: []`**. 2 subprocesses, both
  `git rev-parse HEAD` from the health route at import. 0 Hermes seam calls.
- **The whole suite** — 12118 write calls; 0 in the real vault, 0 in the real
  Hermes home, and **1** "in the real data path" which is the data path
  directory itself (a pre-existing `mkdir(exist_ok=True)` from another file —
  nothing inside it). 1 real httpx request, `GET http://127.0.0.1:9119/`,
  pre-existing and not from these files. 127 socket connects; the only one whose
  text contains "8001" is `('127.0.0.1', 58001)`, an ephemeral self-pipe port —
  **no connect to port 8001**. 502 passed under the interceptor too.

| AC-ID | Step | Observed |
|---|---|---|
| `REQ-SB-95-US-03-AC-02` | Automated test 1 — an `http` implementation is really performed, **end to end through `POST /actions/{id}/call`** | **Pass.** `POST /actions/file-the-note/call` with `{"folder": "Projects", "note": "kickoff", "urgent": true}` → 200, `accepted: true`, `outcome: "performed"`. The target function was entered **exactly once**, with those three validated inputs — `folder` bound into the path the route declares it in, `note` and `urgent` in the body — and the verdict carried the route's real result `{"filed": "Projects/kickoff", "urgent": true}`, with `grant: null` and `where_the_operator_does_it: null`. The ledger record under the same `call_id` says `performed` and keeps the same inputs and the same real result. |
| `REQ-SB-95-US-03-AC-02` | Automated tests 2–5 (`skill` authorised, grant single-use, `ui` pointed at, induced `http` failure) | **Pass, unchanged** — re-run green in every suite run above. Their observed outcomes are recorded in the first Implementation Log and were not revisited. |
| `REQ-SB-95-US-03-AC-02` | Gate-side `AC-02` — a valid call enters dispatch exactly once and the ledger records what dispatch really reported | **Pass.** `test_a_valid_call_passes_the_gate_records_it_and_enters_dispatch_exactly_once` now asserts `outcome: "performed"`, the route's real result `{"accepted_inputs": {"scope": "Projects", "force": true}}`, and the same word in the ledger record — the transitional `not_dispatched` assertions `T02` assigned here. The seam is still entered exactly once, with exactly the validated inputs. |
| `REQ-SB-95-US-03-AC-02` | **Manual step 1** — a real `http` Action over loopback, checked by its real side effect | **Pass.** Run against a **disposable install on `127.0.0.1:8013`** (its own uvicorn, scratch `VAULT_PATH` / `SECOND_BRAIN_DATA_PATH` / `HERMES_HOME_PATH`), the technique `REQ-SB-95-US-02-T06` established; the operator's `:8001` was never called and was still answering, untouched, afterwards. Two notes were written into the disposable vault behind the backend's back and `GET /vault/overview` still read `total_notes: 0` — the index was genuinely stale. `POST /actions/refresh-my-index/call` (a real `http` Action on `POST /vault-index/refresh`) answered `accepted: true, outcome: "performed"` with the route's own result `{"notes_indexed": 2, "rebuilt_at": "…T06:37:10.238843+00:00", …}`, and the detail *"this app performed action 'refresh-my-index' by running its own POST /vault-index/refresh, which answered HTTP 200"*. **The real side effect, read back through a different route:** `GET /vault/overview` then returned `total_notes: 2`, `folder_counts: {"Notes": 2}`, `last_rebuilt_at` equal to the dispatch's own `rebuilt_at`. The ledger file on the disposable install's disk (`config/data/ActionCalls/b665f7a1….json`) carries `performed` and that same real result. A second Action, `exclude-a-folder` on `PATCH /vault/index-config/{folder_name}`, then proved the wire mapping on a real install: called with `{"folder_name": "Notes", "included": false}` it answered `performed`, the route saw `Notes` as a **path parameter** and `included` in the **body**, and the change was persisted to `config/index_config.json` as `{"folders": {"Notes": {"included": false}}}` and read back by `GET /vault/index-config`. The instance was stopped afterwards. |

### Judgement calls inside scope (for human spot-check)

The six recorded in the first Implementation Log all still stand. One new one:

7. **The gate test file imports `tests/test_action_dispatch.py` for the side
   effect of registering the shared harmless target, rather than registering a
   second one of its own.** `ESC-073` named reuse, and two identical
   test-only routes on the real app would be two things to keep in step. The
   cost is a test module importing another test module: real coupling, but
   explicit, commented at both ends, and it keeps the gate file runnable alone
   (measured: `pytest tests/test_action_invocation_gate.py` → 6 passed). The
   alternative — pointing the gate's Action at the EXISTING
   `/__test_action_target/{folder}` — would have forced that route's required
   `note` body field to become optional and the gate's Action to be rebuilt
   around `folder`/`note`, rippling through every refusal assertion in the file
   (`'scope'`, `'force'`, `'recurse'`): far more than the three authorised
   changes.

### Not done here, deliberately

Unchanged from the first Implementation Log: confirmation is `T04`'s, the runner
Skill is `T05`'s, and no route exposes grant consumption yet because
`actions_router.py` is in `T04`'s scope, not this one's.
