---
id: REQ-SB-95-US-05-T05
title: The scoped read as a shipped, catalogued Action reached through the call gate
parent_story: REQ-SB-95-US-05
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "`ESC-080` is Resolved and the starter shipped; what remains flagged is NEW and is **not** this task's own scope: `REQ-SB-101`'s default-deny middleware refuses the gate's own in-process dispatch sub-request, so **every** `http`-implementation Action now answers `outcome: failed` on a signed-in install — measured live on a disposable backend, raised as `ESC-081`. Also carries five scope-internal judgement calls and one framework constraint that `MEMORY.md` is too far over budget to accept."
phase: P2
depends_on: [REQ-SB-95-US-05-T04, REQ-SB-95-US-02-T02, REQ-SB-95-US-03-T02, REQ-SB-95-US-03-T03]
created: 2026-10-16
updated: 2026-10-21
---

# REQ-SB-95-US-05-T05 — The Scoped Read, Reached Through the Catalogue

## Parent Story

- Story: [[REQ-SB-95-US-05]] — `../UserStories/REQ-SB-95-US-05-entity-resolution-tag-keyed-index.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Make the scoped entity read something an agent reaches the same way it reaches
anything else — a shipped Action whose `http` implementation names its own
route, validated by the call gate like every other action call.

---

## Starting State → End State

**Before / Inputs:**

- `T04`'s scoped read, as business logic with no HTTP surface of its own.
- `REQ-SB-95-US-02-T02`'s save-time implementation resolution (an `http`
  implementation resolves against the running app's own route table).
- `REQ-SB-95-US-03-T02`'s `POST /actions/{action_id}/call` gate and the
  Action-call ledger; `REQ-SB-95-US-03-T03`'s dispatch by implementation kind.
- `ADR-032` allows the framework to ship starter Actions, the way it ships
  Master Templates.

**After / Outputs:**

- A route exposing the scoped read (on a new or existing router — one choice,
  logged), taking the entity name and returning the resolved entity plus the
  scoped result, including the honest "did not resolve" and "ambiguous"
  results from `T03`.
- A **shipped starter Action** whose single `implementation` is `http` naming
  that route, with its inputs typed and the entity name marked required.
- An agent's call therefore goes through the gate: unknown id, missing
  required input, and an implementation that no longer resolves are refused
  exactly as for any other Action, and a caller outside `allowed_callers` is
  refused with the refusal recorded in the ledger.

---

## Files to Modify

- the route's router file (new, or the closest existing single-purpose router —
  read the real current `app/api/` convention first and log the choice)
- the shipped-starter Action definition, wherever `REQ-SB-95-US-02`'s landed
  code puts shipped starters (**read that real code before writing** — do not
  invent a second mechanism for shipping one)
- `src/backend/tests/test_scoped_read_action.py` (new)

---

## Constraints

- Inherits from parent story.
- **The gate is not re-implemented here.** This task contributes an Action and
  a route; validation, dispatch, refusal and the ledger are `US-03`'s and must
  be used unchanged.
- **No plugin named**, and the Action's description must not name a business
  vocabulary (`Customer`, `Partner`) — it is generic entity resolution.
- The route is the `http` implementation of the Action **and** may back an
  in-app surface later; the agent's door is still the Action call, not a
  private endpoint it is told about.
- If `US-02`/`US-03` have not landed when this task is picked up, it is
  **blocked**, not improvised against an imagined interface — its `depends_on`
  says so.

---

## Tests

**Automated tests** — `src/backend/tests/test_scoped_read_action.py`, run with
`pytest tests/test_scoped_read_action.py` from `src/backend`; drive the real
app with `httpx.ASGITransport(app=app)` the way the existing API tests do.

1. `[REQ-SB-95-US-05-AC-06]` Call the shipped Action through
   `POST /actions/{id}/call` with a valid caller and a resolvable entity name;
   assert the response carries the scoped read's own result (hub first, then
   evidence) and that a ledger record was written for the call.
2. `[REQ-SB-95-US-05-AC-06]` Call it with the required entity-name input
   missing; assert the gate refuses naming the missing input and that the
   scoped read was never executed (spy it).
3. `[REQ-SB-95-US-05-AC-06]` Call an unknown action id; assert the same
   refusal path as any other unknown id.
4. `[REQ-SB-95-US-05-AC-06]` Call as a caller **not** in `allowed_callers`;
   assert it is refused and that the refusal is recorded in the Action-call
   ledger with the caller and the reason.
5. `[REQ-SB-95-US-05-AC-06]` Break the implementation's target route (rename it
   in-process) and assert the Action is reported as no longer resolving, and
   that a call is refused rather than half-performed.

**Manual verification steps:**

1. `[REQ-SB-95-US-05-AC-06]` With the backend running and the Action in the
   catalogue, call it from a real agent through the shipped runner Skill and
   confirm the answer comes back scoped; then call it as an agent outside
   `allowed_callers` and confirm the refusal appears in the ledger. Record both
   outcomes in the Implementation Log.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] The scoped read has a route, and a shipped Action whose `http` implementation names it — `GET /vault-search/entity-read` on `vault_search_router` (`420dd6c`) and `app/business/core/actions/starters/read-entity-updates/Action.json`, which a disposable backend really seeded at boot and served from `GET /actions` with `status: "resolves"`
- [x] Calls go through the existing gate; unknown id / missing input / unresolved implementation refused there
- [x] A caller outside `allowed_callers` is refused and the refusal is in the ledger
- [x] No gate, ledger or dispatch logic duplicated in this task
- [~] `MEMORY.md` updated if this task produced a new decision / pattern / constraint — three constraints emerged and none could be appended (86 KB against the file's own 40 KB budget, whose rule 1 forbids appending while over); all three are written verbatim into `REVIEW-QUEUE.md` for the compaction pass
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The gate, the ledger, confirmation and dispatch — `REQ-SB-95-US-03`.
- The Action artifact kind itself — `REQ-SB-95-US-02`.
- Any screen.

---

## Context / Notes

`architecture.md` → **§The Action Call Gate** (read-only context for this
story) and the scoped-read bullet of **§The One Tag-Keyed Index**. This is the
story's only genuinely cross-story task: Scenarios 1–5 and 7 stand alone, so if
the product-owner needs to sequence this story ahead of the `REQ-SB-95` spine,
this task is the one that waits.

---

## Implementation Log

**Coder, 2026-10-21 — `Blocked → Done`.** Finished the task a previous session
left part-built: the route and the 14 gate tests were already committed in
`420dd6c`, and what landed now is the shipped starter folder itself, the three
assertions `ESC-080` authorised, and the verification below.

### What shipped in this pass

- `app/business/core/actions/starters/read-entity-updates/Action.json` — one new
  folder, no new mechanism. `shipped_starters.list_shipped_starter_ids()` already
  enumerates that directory and `app/main.py` already calls
  `seed_shipped_starters()` at boot (`ESC-074`), so shipping a starter is adding
  a folder and nothing else. Its single `implementation` is
  `{"http": {"method": "GET", "path": "/vault-search/entity-read"}}` — the route
  `420dd6c` added — typed inputs (`name` string **required**, `evidence_limit`
  integer optional), `allowed_callers: ["*"]`, `needs_confirmation: false`.
- `tests/test_action_runner_skill.py` — the three `[REQ-SB-95-US-03-AC-05]`
  assertions that pinned the shipped set as a one-element literal, under the
  scope extension recorded at the end of this file.
- `tests/test_scoped_read_action.py` — `THE_SHIPPED_ACTION_JSON` is now **read
  from the shipped file** instead of restating it as a literal, so the bytes this
  file verifies and the bytes a fresh install seeds cannot drift apart.

### Suite

Measured on this machine before the first edit and again after the last, both
from `src/backend` with `VAULT_PATH`, `SECOND_BRAIN_DATA_PATH` and
`HERMES_HOME_PATH` pointed at a scratch tree and synthetic `COMPASS_*`/
`SELF_EMAIL` values, so the operator's vault, data store and Hermes install were
unreachable throughout:

| | collected | passed | failed |
|---|---|---|---|
| **Baseline** | 780 | 778 | 2 |
| **After** | 780 | 778 | 2 |

The same two ids before and after:
`test_skill_writes_declaration.py::test_every_writer_of_a_restricted_template_is_declared`
and `test_versioning.py::test_drift_report_uses_the_documented_statuses`. Both
read what is **deployed into a real Hermes install**, which the isolation
deliberately removes; neither is touched by this task. (Without seeding the
shipped Master Templates into the scratch data store the same run gives 771/9 —
the extra seven are the same artefact, and seeding the templates is what removes
them.) The two affected files alone: `26 passed`.

One intermediate full run showed `test_health_check.py::test_health_reports_the_
commit_…` and `test_marketplace_source.py::test_update_pulls_the_recorded_
repository_again` failing and both of the above passing; run again, that pair
passed and `test_marketplace.py::test_uninstall_leaves_the_templates_in_place`
failed with a `PermissionError`. That is the known order-dependent family, not
this change.

### `[REQ-SB-95-US-05-AC-06]` — observed outcomes

**Automated** (`pytest tests/test_scoped_read_action.py`, 14 tests, all passing;
the real `app.main.app` over `httpx.ASGITransport`, route table deliberately
unpatched):

1. **Valid caller, resolvable name → PASS.** The verdict carries the scoped
   read's own result, hub synthesis first then evidence newest first, and the
   ledger record for the call is on disk.
2. **Required input missing → PASS.** Refused `409` naming `name`, and the spy
   around `scoped_entity_read.read_entity_named` recorded **zero** calls.
3. **Unknown action id → PASS.** `refused:unknown_action`, the same path as any
   other unknown id.
4. **Caller outside `allowed_callers` → PASS.** Refused, and the refusal is a
   real file in the ledger carrying the caller and the reason.
5. **Target route renamed in-process → PASS.** The Action is reported as no
   longer resolving and the call is refused rather than half-performed.

**Manual** (the task's one manual step), run against a **disposable** backend on
`127.0.0.1:8099` with its own scratch vault, data store and absent Hermes home —
never the operator's `:8001`. Bootstrapped a first Admin on it and sent the
runner's own request shape with that session as a bearer token:

- **The catalogue — PASS.** `GET /actions` returned
  `['read-entity-updates', 'report-unmet-request']`: the starter was seeded at
  boot from the repository folder, by the real mechanism, with
  `implementation_kind: "http"` and `status: "resolves"`. Nothing was patched to
  make that true.
- **The refusals — PASS.** Missing `name` →
  `refused:missing_required_input` ("requires 'name', which this call did not
  supply; ask for it by name — nothing is guessed or defaulted in its place").
  Unknown id → `refused:unknown_action`. Then the stored copy's
  `allowed_callers` was narrowed to `["an-agent"]` through `PUT /actions/{id}`
  (the operator's own edit outranks the shipped copy, which is the documented
  rule) and a call as `an-outsider-agent` → `refused:caller_not_permitted`,
  "agent 'an-outsider-agent' may not run action 'read-entity-updates'". All four
  calls are files in `<DATA>/ActionCalls/`, each naming the caller and the
  outcome. **This is the whole of the AC-06 Gherkin, observed live.**
- **The accepted call's answer — DID NOT COME BACK, for a reason outside this
  task.** `accepted: true`, a ledger row written, and then
  `outcome: "failed"` with `detail: "...dispatched to this app's own GET
  /vault-search/entity-read and it answered HTTP 401, so the operation did NOT
  happen"`, `result: {"reason": "not_authenticated"}`. The gate behaved
  **exactly** as designed — a non-2xx is "it did not happen", never a fabricated
  success. The cause is `REQ-SB-101`, which landed after this task was blocked:
  `_request_this_apps_own_route()` re-enters the app through `ASGITransport`,
  which by its own docstring runs "the real middleware stack", and that stack is
  now default-deny with no credential on the sub-request. **Every** `http`
  implementation is affected, not this one. Raised as **`ESC-081`**, with a
  `REVIEW-QUEUE.md` pointer.
- **Why this does not block the AC.** AC-06's Gherkin is about the gate —
  validation, the four refusals and the ledger — and all of it passed live. The
  scoped answer itself is verified by automated test 1 through the real gate and
  the real dispatch. The step the manual run could not complete is a regression
  in another story's code, owned by `ESC-081`, not a gap in this task's
  deliverable.
- **Not performed, and disclosed:** the "call it from a real agent through the
  shipped runner Skill" half. The runner (`catalog/actions/call-action/scripts/
  call_action.py`) sends **no credential at all**, so post-`REQ-SB-101` it is
  refused `401` before the gate is reached; driving a real agent would also have
  meant writing into the operator's live Hermes install, which the standing
  conditions forbid. Same root cause, same escalation.

### The three assertions (`ESC-080` scope extension)

Each became a membership check over the live set; none lost what it proved.

| Test | Was | Now |
|---|---|---|
| `…_records_an_unmet_request_and_it_is_retrievable` | `seeding["seeded"] == [THE_UNMET_REQUEST_STARTER]` | `THE_UNMET_REQUEST_STARTER in seeding["seeded"]` — still proves the starter really seeded |
| `…_never_overwrites_the_operators_own_copy` | `seeded == [x]`, then `again == {"seeded": [], "kept": [x]}` | `x in first_pass["seeded"]`; then **`again["seeded"] == []` kept exactly as it was** (a second pass installs nothing at all — that is idempotence and it is not weakened) and `x in again["kept"]`, with the operator's edited description still asserted byte-for-byte |
| `…_is_a_real_definition_this_catalogue_can_hold` | `list_shipped_starter_ids() == [x]` | `x in list_shipped_starter_ids()` — the definition is still loaded, parsed and asserted field by field |

Only "and nothing else is shipped" went. Each assertion carries its reason in
its own failure message (`"membership, not equality: the shipped set grows
(ESC-080)"`), because a comment anywhere else in that file would have been
outside the authorisation.

### Scope-internal judgement calls (for human spot-check)

1. **`THE_SHIPPED_ACTION_JSON` reads the repository file** rather than keeping
   the literal that stood in for it while the file was held back. Two copies of
   a definition is the same hand-maintained-duplicate shape this whole
   escalation family is about. It reaches `shipped_starters._SHIPPED_STARTERS_DIR`
   by name because the module exposes the parsed dict and not the text, and
   adding a public accessor would have been a change to a `Done` task's module.
2. **The `shipped` fixture still points the reader at a `tmp_path` directory**
   holding only this starter, rather than at the repository directory. Seeding
   from the real directory would install `report-unmet-request` into these tests
   too, and this file would then fail the day a third starter is added — exactly
   the mistake `ESC-080` exists about.
3. **`starters/README.md` was NOT updated**, though it documents why each
   starter ships and now covers one of two. It belongs to `REQ-SB-95-US-03-T05`
   (`Done`) and the `ESC-080` extension is explicit that only the three
   assertions in `test_action_runner_skill.py` are authorised. The rationale is
   in the Action's own description and here instead. Worth one line from whoever
   next has that file in scope.
4. **The manual step was run against a disposable backend with synthetic data**,
   not the operator's install — standing condition, and the same call the three
   previous tasks in this sprint made.
5. **`allowed_callers` was narrowed on the disposable install to observe the
   refusal.** The shipped Action is `["*"]` by design (an agent not told it
   exists cannot use it), so "a caller outside `allowed_callers`" cannot occur
   live without an edit. The edit used the product's own `PUT /actions/{id}`.

### The Action's description carries no business vocabulary

It says "ONE named thing", "the namespaces registered on this install", "that
name's own scope". It names no `Customer`, no `Partner`, no `Opportunity`, no
plugin, no `Hermes`, no `Obsidian` — asserted mechanically, over the shipped
bytes, by
`test_the_shipped_definition_names_no_business_vocabulary_and_no_plugin`. `T01`
and `T03` went to real trouble to keep `kind` opaque and the Action definition is
the one artefact an agent actually reads, so a single example word in it would
have taught the vocabulary anyway.

### `MEMORY.md` — a third constraint parked, not appended

The file is 86 KB against the 40 KB budget its own rule 1 sets, and that rule
forbids appending while over. Verbatim, in `REVIEW-QUEUE.md` for the compaction
pass: *the app's own in-process dispatch is a real request through the real
middleware stack — anything that makes the app default-deny makes the app unable
to call itself, unless the dispatcher is given an identity. Authentication added
to an app that re-enters itself must name every internal re-entry point in the
same change.*

---

## Scope extension — 2026-10-21 (unblocks `ESC-080`)

**Added to `## Files to Modify`:** `src/backend/tests/test_action_runner_skill.py`,
scoped to **the three assertions that pin the shipped-starter set as a literal
one-element list** and nothing else in the file.

Your diagnosis is right and measured: the folder is additive, the product does not
notice it, and three tests do because they say
`list_shipped_starter_ids() == [THE_UNMET_REQUEST_STARTER]`. Those are
`REQ-SB-95-US-03-T05`'s and that task is `Done`, so you were right to stop.

**Make them assert over the live set rather than re-pinning it.** `ESC-077`
authorised the identical change one sprint ago for `_MANAGER_BY_KIND`, and the
reason holds here: a hand-maintained list has to be edited by every future
starter's author, which is the omission this whole family of escalations is about.
Concretely — assert the unmet-request starter is **present**, and that seeding
reports it among the seeded, rather than that it is the only one. The two
`kept`/`seeded` assertions become membership checks of the same shape.

Do not weaken what the tests mean: each still has to prove that seeding is
idempotent, that a second pass keeps the operator's own edited copy, and that a
shipped definition really loads. Only "and nothing else is shipped" goes.

Then finish `T05`: the starter Action folder, the verification, `Done`, and
**close `SPRINT-090`** — `status: Done`, `completed: 2026-10-21`, a drafted
retrospective. It is the last task of the last open sprint.
