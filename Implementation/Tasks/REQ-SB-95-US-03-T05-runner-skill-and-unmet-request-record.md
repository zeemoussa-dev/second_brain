---
id: REQ-SB-95-US-03-T05
title: The shipped runner Skill over loopback, honest refusal end-to-end, and the recorded unmet request
parent_story: REQ-SB-95-US-03
requirement_id: REQ-SB-95
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-95-US-03-T01, REQ-SB-95-US-03-T03, REQ-SB-95-US-03-T04]
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-03-T05 — The Runner Skill + "I Cannot Do That" as a Recorded Answer

## Parent Story

- Story: [[REQ-SB-95-US-03]] — `../UserStories/REQ-SB-95-US-03-published-catalogue-and-call-enforcement.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Give the agent its one door — a shipped runner Skill that posts to
`POST /actions/{action_id}/call` over loopback — and make "I cannot do that" a
real, recorded answer rather than a sentence.

---

## Starting State → End State

**Before / Inputs:**

- The gate, dispatch and confirmation are complete but reachable only from the
  UI and from a raw HTTP client.
- `business/core/skills/catalog/vault/vault-search/scripts/search_vault.py`
  already calls this app over loopback at
  `os.environ.get("SECOND_BRAIN_API_URL", "http://127.0.0.1:8001")`, and
  `vault-index/scripts/build_vault_index.py` POSTs `/vault-index/refresh` — the
  proven, shipped pattern this reuses. It is **not** the deleted inbound MCP
  surface.

**After / Outputs:**

- One shipped runner Skill under `business/core/skills/catalog/<tool>/<slug>/`
  (payload, never imported by the app — `ADR-019`) whose script:
  - posts the action id, the caller's own profile id and the inputs to
    `POST {SECOND_BRAIN_API_URL}/actions/{action_id}/call`;
  - relays a refusal verbatim, naming the cause, and never narrates an outcome
    that did not happen;
  - on an `awaiting_confirmation` response, reports the pending confirmation and
    stops;
  - on a `skill` grant, performs the named Skill in its own profile and reports
    the real outcome back.
- A shipped starter `report-unmet-request` Action (`ADR-032` allows shipped
  starters) so an unmet request lands as a row in the Action-call ledger.
- End-to-end honesty: an unknown id, a missing required input and a
  not-permitted caller each reach the operator as the framework's own refusal.

---

## Files to Modify

- `src/backend/app/business/core/skills/catalog/<tool>/<slug>/Skill.json` (new — the runner Skill definition; `<tool>/<slug>` chosen to match the existing catalogue's grouping convention)
- `src/backend/app/business/core/skills/catalog/<tool>/<slug>/scripts/call_action.py` (new — modelled on `search_vault.py`)
- `src/backend/app/business/core/actions/` starter-Action seed for `report-unmet-request` (the shipped-starter mechanism, mirroring how Master Templates ship)
- `src/backend/tests/test_action_runner_skill.py` (new)

---

## Constraints

- Inherits from parent story.
- The runner is **payload**: the app must never import it (`ADR-019`). It is
  deployed into a Hermes profile like any other Skill.
- **No silent fallback.** The runner may not substitute a different action, a
  search, or a plausible narrative for a call it could not make — including
  when the backend is not running, which must surface as a connection failure,
  not a claimed success.
- The trust boundary is loopback and is stated honestly in `ADR-033`: the runner
  names its own profile id and the app believes it. Do not claim this sandboxes
  Hermes.
- `REQ-SB-33-US-01`'s honest-uncertainty instruction stays as it is.

---

## Tests

**Automated tests** — `src/backend/tests/test_action_runner_skill.py`, run with
`pytest tests/test_action_runner_skill.py` from `src/backend`. Import the
runner script by path as a payload script (the existing per-Skill
`scripts/tests/` pattern is the precedent) and point it at the real app through
a loopback-shaped transport.

1. `[REQ-SB-95-US-03-AC-03]` Drive the runner with an action id that is not in
   the catalogue; assert its output is the framework's own refusal naming the
   unknown id, that it reports inability rather than any outcome, and that a
   `refused:` ledger row exists.
2. `[REQ-SB-95-US-03-AC-04]` Drive it with a required input omitted; assert the
   output asks for that input by name and that no value was invented.
3. `[REQ-SB-95-US-03-AC-02]` Drive it with a valid `skill`-implementation call;
   assert it receives the single-use grant and performs the named Skill in its
   own profile, reporting the real outcome.
4. `[REQ-SB-95-US-03-AC-05]` Call the shipped `report-unmet-request` Action with
   an unmet-request text; assert a ledger row records the request text and that
   it is retrievable afterwards.
5. `[REQ-SB-95-US-03-AC-05]` Assert the runner surfaces a connection failure
   honestly when the app is unreachable, rather than reporting success.

**Manual verification steps:**

1. `[REQ-SB-95-US-03-AC-05]` With the backend running and the runner Skill
   deployed to a real Hermes profile, ask that agent in a real chat for
   something no catalogued Action covers. Confirm it states plainly that this
   app has no action for the request, does not invent one, does not promise it
   for later, does not claim it was done, and that a ledger row records the
   unmet request. Record the reply verbatim in the Implementation Log.
2. `[REQ-SB-95-US-03-AC-03]` In the same session, induce a call to a
   non-existent action and confirm the operator sees the honest refusal rather
   than a described outcome.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] One shipped runner Skill, loopback, modelled on `search_vault.py`
- [ ] Refusals relayed verbatim; no invented outcome on any path
- [ ] `awaiting_confirmation` and `skill` grants handled correctly by the runner
- [ ] Shipped `report-unmet-request` starter Action; unmet requests recorded
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- A reviewable capability-request backlog UI (story Non-Goals).
- Any general inbound Hermes→app API surface beyond this one route.
- Workflow runs — `REQ-SB-95-US-04-T05`.

---

## Context / Notes

`architecture.md` → **§The Action Call Gate** ("The agent's only door is one
shipped runner Skill") and **§Confirmation and the Action-Call Ledger** (the
`report-unmet-request` starter). `ADR-033` records the loopback precedent with
the exact two shipped scripts to model this on — read both before writing.

---

## Implementation Log

_(Filled in by the coder.)_
