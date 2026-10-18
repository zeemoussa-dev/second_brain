---
id: REQ-SB-95-US-03-T03
title: Dispatch by implementation kind — http performed, ui pointed at, skill authorised via single-use grant
parent_story: REQ-SB-95-US-03
requirement_id: REQ-SB-95
type: backend
status: Blocked
gate: flagged
gate_reason: "ESC-073 Open -- wiring the `http` dispatch branch needs two assertions changed in `src/backend/tests/test_action_invocation_gate.py`, a file outside this task's `## Files to Modify`: one pins `T02`'s transitional `not_dispatched` outcome, and the other points a test Action at the REAL `POST /vault-index/refresh`, which live dispatch turns into a full re-read of the operator's vault on every suite run (measured 1.09s -> 8.60s for that file). The `ui` and `skill` paths, the single-use grant and its ledger claim primitive are built, tested and committed (e16013c, ab0ed44; 490 -> 497 tests, 0 failed), and `_perform_http_implementation()` is complete and proved by three tests driving it directly -- only the one line that reaches it from the seam is withheld, so `AC-02`'s http half is unverified end to end. Also flagged for a spot-check of four scope-internal judgement calls in the Implementation Log, the largest being that `http` is performed IN PROCESS over httpx.ASGITransport rather than over a loopback socket to 127.0.0.1:8001."
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

- [ ] Three dispatch paths, each behaving exactly as `ADR-033` decides — `ui` and
      `skill` done and wired; `http` built and proved but not wired (`ESC-073`)
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
