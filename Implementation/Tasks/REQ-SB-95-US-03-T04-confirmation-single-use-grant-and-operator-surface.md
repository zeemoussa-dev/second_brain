---
id: REQ-SB-95-US-03-T04
title: Confirmation-required Actions — awaiting_confirmation, the single-use grant, and the operator confirm/decline surface
parent_story: REQ-SB-95-US-03
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "trigger-1: two scope-internal judgement calls logged for spot-check -- a confirmed operation is recorded as TWO ledger rows joined by granted_by_call_id (one id could not carry two grants), and a re-call naming different inputs/action/caller is refused without spending the confirmation"
phase: P2
depends_on: [REQ-SB-95-US-03-T02]
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-03-T04 — Confirmation and the Single-Use Grant

## Parent Story

- Story: [[REQ-SB-95-US-03]] — `../UserStories/REQ-SB-95-US-03-published-catalogue-and-call-enforcement.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Honour the `needs_confirmation` flag `REQ-SB-95-US-02` stores: the first call
performs nothing and opens an `awaiting_confirmation` ledger record; the
operator confirms or declines; a confirmed record is a single-use grant the
re-call consumes exactly once.

---

## Starting State → End State

**Before / Inputs:**

- The Action-call ledger exists (`T02`) and dispatch works (`T03`); the
  confirmation flag is stored but honoured nowhere.
- **The Pending Approvals surface is not live and must not be planned against:**
  `pending_approvals_router.py` is absent from the repo,
  `GET /agents/{id}/history` returns `[]` with a comment naming it, and
  `Agent.working_mode`'s own comment records that the Hermes
  `approval.request`/`respond` path was never wired.

**After / Outputs:**

- First call of a confirmation-required Action: nothing performed, a ledger
  record at `awaiting_confirmation`, and a refusal carrying the `call_id`.
- Confirm / decline routes on `actions_router.py` over the ledger; confirming
  turns the record into a single-use grant, declining records `declined`.
- A re-call consumes the grant exactly once and then dispatches through `T03`;
  a second re-call finds nothing to consume and is refused.
- A small operator surface over the ledger — the pending confirmations list and
  a confirm/decline control per entry, on the existing approved
  `.item-list`/`.item-row` + `.btn` families. It is **not**
  `html-prototype/my-day-approvals.html` and does not revive that subsystem.
- `Agent.working_mode` is untouched — an Action's confirmation flag is a
  per-operation operator decision, orthogonal to it.

---

## Files to Modify

- `src/backend/app/business/logic/action_invocation.py`
- `src/backend/app/data_access/action_calls.py`
- `src/backend/app/api/actions_router.py` (list-pending, confirm, decline)
- `src/frontend/src/pages/SettingsActionsPage.tsx` (a pending-confirmations region on the existing Actions page)
- `src/frontend/src/features/settings/actionsApiClient.ts`
- `src/backend/tests/test_action_confirmation.py` (new)

---

## Constraints

- Inherits from parent story.
- **Nothing is half-performed.** The first call of a confirmation-required
  Action performs no part of the operation.
- The grant is **single-use**; reuse the mechanism `T03` built rather than
  adding a second one.
- Do not revive `pending_approvals_router.py` / `agent_pending_approvals.json`
  and do not touch `load_pending_approvals_state` /
  `save_pending_approvals_state` in `data_access/vault_writer.py`.
- `Agent.working_mode` and the Hermes approval path stay exactly as they are.
- A confirmed-but-never-re-called Action stays visible in the ledger rather
  than silently performing nothing.
- Frontend assertions are on DOM structure only.

---

## Tests

**Automated tests** — `src/backend/tests/test_action_confirmation.py`, run with
`pytest tests/test_action_confirmation.py` from `src/backend`, over
`httpx.ASGITransport(app=app)` with the stores monkeypatched to a tmp dir.

1. `[REQ-SB-95-US-03-AC-06]` Call an Action with `needs_confirmation: true`;
   assert nothing was dispatched, the response carries `awaiting_confirmation`
   and a `call_id`, and the ledger record exists at that state.
2. `[REQ-SB-95-US-03-AC-06]` Confirm that `call_id`, then re-call; assert the
   grant is consumed exactly once and the operation is really performed
   (dispatch seam entered once, ledger `performed`).
3. `[REQ-SB-95-US-03-AC-06]` Re-call a second time with the same `call_id`;
   assert it is refused — a grant cannot be consumed twice.
4. `[REQ-SB-95-US-03-AC-06]` Decline a `call_id`; assert the ledger records
   `declined`, nothing is performed, and a re-call is refused with `declined`.
5. `[REQ-SB-95-US-03-AC-06]` Assert a confirmation-required Action never
   dispatches on the first call regardless of implementation kind (http / ui /
   skill all return `awaiting_confirmation`).

**Manual verification steps:**

1. `[REQ-SB-95-US-03-AC-06]` With the backend and frontend running, call a real
   confirmation-required Action over loopback; confirm the pending entry renders
   on the Actions page as an `.item-row` with confirm and decline controls;
   click confirm, re-call, confirm the real operation happened. Repeat with
   decline and confirm nothing happened and the agent is told so.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] First call performs nothing and opens `awaiting_confirmation`
- [x] Confirm → single-use grant, consumed exactly once on the re-call
- [x] Decline → `declined`, nothing performed, honestly reported
- [x] A small operator surface over the ledger, not the archived approvals one
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- A reviewable surface over the whole ledger / unmet-request backlog (story
  Non-Goals).
- Per-step workflow confirmation — `REQ-SB-95-US-04-T05` reuses this mechanism
  unchanged.
- Reviving or extending the archived Pending Approvals subsystem.

---

## Context / Notes

`architecture.md` → **§Confirmation and the Action-Call Ledger** is
authoritative, including the evidence for why the existing approvals machinery
is unavailable. `ADR-033`'s fourth decision bullet fixes the state machine
(`awaiting_confirmation` → single-use grant → consumed once, or `declined`).

---

## Implementation Log

**2026-10-18 — built and verified. Suite 502 (baseline, measured at
`e6a738f`) → 511 passed, 0 failed.** Commits: `afa2b6b` (backend gate,
routes, 9 AC-tagged tests), `1d9c68d` (the screen region).

### What shipped

- **The confirmation check sits exactly where `T02` left the marker** —
  after validation completes in full, before the dispatch seam is
  entered once. A confirmation-required Action therefore stops at a
  point where the call is known to be runnable and where being asked
  costs nothing.
- **Three ledger states, not one overloaded word:**
  `awaiting_confirmation`, `confirmed`, `declined`. All three are named
  by `ADR-033` and by `architecture.md` → §Confirmation and the
  Action-Call Ledger, so none is invented here. `confirmed` is its own
  state because the Constraints require a confirmed-but-never-re-called
  Action to stay visible rather than silently perform nothing —
  confirming performs nothing, and a word shared with `validated` or
  `performed` could not say that.
- **The refusal vocabulary is NOT widened.** `awaiting_confirmation`
  reaches the caller as the same single 409 carrying the whole verdict
  as a dict `detail`; 2xx still means the gate was passed; a dispatch
  failure is still 200 + `accepted: true, outcome: "failed"`. A client
  branches on `accepted` alone, exactly as before.
- **One grant mechanism.** The confirmation grant is spent through
  `T03`'s `consume_single_use_grant()` over `claim_call_once()` — no
  second mechanism, and no `claim_call_once()` call of this task's own.
- **The ledger is still written twice** for an accepted call. On a
  re-call the first write is the `confirmed` record (grant marked
  spent) plus the new call's own `validated` row, both before the seam;
  the real outcome is written after. A crash mid-dispatch still leaves
  no record claiming the operation ran.
- **Operator surface:** `GET /actions/calls/pending`,
  `POST /actions/calls/{call_id}/confirm`, `POST .../decline`, and a
  *Pending confirmations* region above the Catalogue card on
  `/settings/actions`, on the approved `.item-list`/`.item-row` +
  `.btn` families. `pending_approvals_router.py`,
  `agent_pending_approvals.json`, `load/save_pending_approvals_state`
  and `Agent.working_mode` are all untouched — grep-checked, not
  assumed.

### The route shape, for `T05`

`T05`'s runner Skill talks to exactly this:

```
POST /actions/{action_id}/call
  {"caller_agent_id": "<profile id>",
   "inputs": {...},
   "confirmed_call_id": null}        # third field, OPTIONAL, new here
```

- **First call** (omit `confirmed_call_id`, or send `null`) → **409**,
  `detail` = the whole verdict, `accepted: false`,
  `outcome: "awaiting_confirmation"`, `call_id: "<id>"`, and `refusal`
  is a sentence that already tells the agent what to do next, naming
  the id verbatim. Nothing is performed.
- **Re-call**: send the same `inputs` plus
  `confirmed_call_id: "<that id>"` → **200**, `accepted: true`, the
  normal dispatch outcome, plus a new field `granted_by_call_id`
  naming the confirmation it spent.
- **Any other re-call** (not confirmed yet, declined, already spent,
  different action/caller/inputs, unminted id) → **409**,
  `outcome: "refused:confirmation_not_granted"`, with a `refusal`
  sentence naming which of those it was. `declined` and "already been
  consumed" appear in the sentence verbatim, so the agent can relay the
  truth without parsing a token.
- An Action with `needs_confirmation: false` ignores
  `confirmed_call_id` entirely — the Action's own flag decides, never
  the caller.
- **`T05` note:** the published SOUL block (`T01`) documents the
  two-field body, and `agent_manager.py` is not in this task's file
  list, so it was not edited. The refusal sentence carries the whole
  instruction instead. If `T05` wants the agent told about
  `confirmed_call_id` up front, that is a `T01`-owned file and needs
  its own scope decision.

### Verification — AC-ID → observed outcome

All six automated tests are in `tests/test_action_confirmation.py`
(9 test cases; the kind-independence one is parametrised ×3).
`"Nothing was performed"` is measured three ways, never asserted once:
the dispatch seam is spied *around* and counted, the `http` Action's
real target function records every entry, and every `subprocess` entry
point plus `os.system` raises.

- **`[REQ-SB-95-US-03-AC-06]` Tests block step 1 — first call performs
  nothing** → **PASS**
  (`test_the_first_call_performs_nothing_and_opens_an_awaiting_confirmation_record`).
  Observed: 409; `outcome: "awaiting_confirmation"`; a `call_id` that
  appears in the refusal sentence; dispatch seam entries `[]`; target
  function entries `[]`; exactly one ledger file, at
  `awaiting_confirmation`, carrying the validated inputs and
  `grant: null`; and the record on `GET /actions/calls/pending`.
- **`[REQ-SB-95-US-03-AC-06]` step 2 — confirm, then re-call** →
  **PASS** (`test_confirming_grants_once_and_the_re_call_really_performs_the_operation`).
  Observed: confirm → 200, `outcome: "confirmed"`,
  `grant.single_use: true`, grant inputs = the confirmed inputs, and
  *still* nothing dispatched or performed, still on the pending list.
  Re-call → 200, `performed`, dispatch entered **exactly once**, the
  real target function entered once with
  `{"folder": "Projects", "note": "kickoff", "urgent": false}`, the
  route's real result on the verdict, `granted_by_call_id` = the
  confirmation id, the confirmation record carrying
  `grant.consumed_at` and a detail naming the call that spent it, and
  the pending list now empty.
- **`[REQ-SB-95-US-03-AC-06]` step 3 — a grant cannot be spent twice**
  → **PASS** (`test_a_consumed_confirmation_cannot_be_consumed_a_second_time`).
  Observed: second re-call → 409,
  `outcome: "refused:confirmation_not_granted"`, refusal contains
  "already been consumed", dispatch count still 1, target entered
  still once.
- **`[REQ-SB-95-US-03-AC-06]` step 4 — decline** → **PASS**
  (`test_declining_performs_nothing_and_every_later_re_call_is_told_it_was_declined`).
  Observed: decline → 200, record `declined`, `grant: null`, nothing
  dispatched or performed, off the pending list; re-call → 409 with
  "declined" in the sentence; a later `confirm` of the same id → 409
  and the record still `declined`.
- **`[REQ-SB-95-US-03-AC-06]` step 5 — no kind dispatches on the first
  call** → **PASS** ×3
  (`test_no_implementation_kind_dispatches_on_the_first_call`,
  parametrised over `http` / `ui` / `skill`). Observed for each:
  `awaiting_confirmation`, `grant: null`,
  `where_the_operator_does_it: null`, `result: null`, dispatch entries
  `[]`, target entries `[]`, no subprocess (every entry point raises),
  one ledger record at `awaiting_confirmation`.
- Two further AC-06-tagged tests cover the judgement calls below:
  `test_a_confirmation_is_not_transferable_to_a_different_operation`
  and `test_an_unminted_or_unconfirmed_id_grants_nothing`.

- **`[REQ-SB-95-US-03-AC-06]` Manual step 1 — real backend + frontend,
  loopback call, confirm/decline in the browser** → **PASS**, against a
  **disposable install on `127.0.0.1:8014`** (own vault, data path and
  a non-existent Hermes home) with its own dev server on `:5199`
  (`VITE_API_BASE_URL` overridden inline; `.env.local` not touched).
  The operator's `:8001` was never called and answered 200 afterwards,
  untouched. The Action under test had `POST /actions` as its `http`
  implementation, so "it really ran" is read back through a *different*
  route — `GET /actions` lists the Action it created — rather than
  inferred from a status code. Observed, in order: first call → 409
  `awaiting_confirmation`, and the Action it would create **absent**
  from the catalogue; the entry on `GET /actions/calls/pending`;
  confirm → 200 `confirmed`, catalogue **still** unchanged, entry still
  listed; re-call → 200 `performed` and the new Action **now present**;
  second re-call → 409, nothing created, pending list empty; a fresh
  call → declined → re-call → 409 naming `declined`, nothing created.
  **Browser half** driven against real headless Edge over CDP (the
  minimal-driver technique `SPRINT-033`/`SPRINT-036` established here —
  no Playwright): the entry renders as an `.item-row` with
  `.item-row-title`, `.item-row-meta` and `.item-row-actions` holding
  real `btn btn-primary` **Confirm** and `btn btn-danger` **Decline**
  controls; clicking Confirm turned the badge to "Confirmed — not run
  yet", set the ledger to `confirmed` and created **nothing**; clicking
  Decline removed that row; the agent's subsequent re-calls returned
  `performed` (and the Action appeared) and a 409 naming `declined`
  (and nothing appeared) respectively. Screenshots were reviewed, not
  just captured — the region renders inside the standard card above the
  Catalogue card and matches the approved families.

### Where writes and outbound calls landed (measured, not assumed)

A pytest plugin wrapped `builtins.open` (write modes), `Path.write_text/
write_bytes/mkdir/touch/unlink/rmdir/rename/replace`, the `os` and
`shutil` file primitives, `socket.socket.connect`/`connect_ex`,
`httpx.HTTPTransport.handle_request`,
`httpx.AsyncHTTPTransport.handle_async_request`,
`urllib.request.urlopen`, every `subprocess` entry point and
`os.system`, comparing every path against the **real** vault, data path
and Hermes home captured before any fixture ran.

- `tests/test_action_confirmation.py` alone: **0 writes** inside any
  real root, **0 real outbound http**, **0 subprocesses**, **0 connects
  to port 8001** (41 loopback connects, all ephemeral ports — anyio's
  `TestClient` portal socketpair).
- Whole suite with this file: 18 real-root touches, 1 outbound, 152
  subprocesses. Whole suite **with this file excluded**: 18, 1, 152 —
  **identical**, so none of it is this task's. For the record, the 18
  are two `mkdir` calls on the already-existing DATA_PATH root itself
  (no file created), the 1 is a pre-existing `GET
  http://127.0.0.1:9119/` (Hermes' own port, not 8001), and the
  subprocesses are the pre-existing `git rev-parse HEAD` commit lookup.
- `tests/conftest.py`'s suite-wide Hermes sandbox was neither weakened,
  bypassed nor special-cased.

### Scope-internal judgement calls (for human spot-check — not escalations)

1. **A confirmed operation is recorded as TWO ledger rows, joined by a
   new `granted_by_call_id` field** — the operator's decision, and the
   re-call that acted on it. `T02`'s `_record_call()` docstring
   anticipated one row ("confirmation turns a record into a grant
   rather than opening a second row"); that is impossible for a
   confirmation-required **`skill`** Action, and the reason is
   structural: `claim_call_once()` takes its claim *against the call
   id*, so the dispatch grant minted onto the already-claimed
   confirmation id could never be spent by the runner. One id cannot
   carry two single-use grants. The alternative — a second claim
   namespace — is the "second mechanism" the Constraints forbid. The
   stale docstring was corrected in place (same file, in scope).
2. **A re-call naming a different Action, caller or inputs is refused
   *without* spending the confirmation.** The operator confirms one
   concrete operation, not a licence; confirming "file this in
   Archive" and re-calling with "Inbox" would perform something nobody
   approved — `ADR-032`'s forbidden substitution, one step later.
   Refusing without consuming is deliberate: the operation that *was*
   approved must still be possible.
3. **A `confirmed` record leaves the pending list the moment its grant
   is spent**, keyed off `grant.consumed_at` rather than a fourth
   outcome word. "It was confirmed" and "it was used" are two
   different facts about one decision and the ledger keeps both; the
   screen only needs the second. Found by a failing test, fixed in the
   business rule rather than in the assertion.
4. **Only an `awaiting_confirmation` record can be confirmed or
   declined.** Re-deciding a decided call (including revoking a
   confirmed-but-unspent one) is refused with a sentence naming its
   current state. Revocation is a real question but nothing in the ACs
   asks for it, and inventing it would have been scope creep.
5. **The confirm/decline routes refuse with a plain-sentence 409**, the
   shape the other operator-facing write routes on this router already
   use (`_refusal`, which the screen's `extractErrorDetail` already
   reads), rather than the call route's verdict-dict 409 — those two
   routes answer an operator at a screen, not a runner relaying words.
   The *gate's* refusal shape is untouched.
6. **`ActionCallBody` gained an optional third field.** Additive: an
   existing two-field caller behaves exactly as before. The published
   SOUL block still documents two fields (see the `T05` note above).

### Not done, deliberately

- No Layer-1 visual harness was run because this repo has none —
  `src/frontend/package.json` declares `dev`/`build`/`lint`/`preview`
  only, and there is no `npm run visual`. The real-browser CDP pass
  above plus the reviewed screenshots are the substitute, and they are
  what this project's own `Learnings.md` already records as adequate.
- `MEMORY.md` gained **no new bullet**: the file is 79.7 KB against its
  own stated 40 KB budget, whose rule 1 forbids appending while over.
  The one genuinely new constraint — a call id can carry only one grant
  ever, so a confirmed operation is two rows — was **folded into the
  single-use-grant rule it is a corollary of** (rule 1's "replace a
  rule this one supersedes"). It is install-independent framework
  knowledge and the exact trap the next reuser of this mechanism
  (`REQ-SB-95-US-04-T05`) would fall into.

**Audit breadcrumb:**

gate: flagged 2026-10-18 — trigger 1 only (material judgement calls
listed above). Every locked AC verified; nothing blocked; no
`ESCALATIONS.md` entry written (nothing out of scope was needed — every
file touched is in `## Files to Modify`); no ADR created or changed; no
new dependency; no shared interface broken (the one interface change is
additive and optional). `T05` is unblocked and may start.
