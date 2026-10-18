---
id: REQ-SB-95-US-03
title: The catalogue is published into agent context and enforced at the call — "I cannot do that" becomes a real answer
requirement_ids: [REQ-SB-95]
requirement_section: "REQ-SB-95: An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution"
phase: P2
status: In Progress
gate: clear
gate_reason: "RESOLVED operator confirmed ADR-033's call path, 2026-10-17 — was: trigger-3 (ADR-033 created — the call lands on one loopback route on this app's own API, reached by a shipped runner Skill; confirmation is an app-owned single-use grant)"
sprint: SPRINT-088
created: 2026-10-16
updated: 2026-10-18  # coder: T01 Done -- ESC-072 resolved by a suite-wide Hermes sandbox (tests/conftest.py); the ActionManager trigger is wired and publishes in the background, AC-01 and AC-08 both verified including the two manual steps on a real profile. T02 Done earlier the same day (AC-02/AC-03/AC-04/AC-07). T03 Done 2026-10-18 -- ESC-073 Resolved by an authorised scope extension (tests/test_action_invocation_gate.py joined T03's files for three named changes); all three dispatch paths are wired and AC-02 is verified end to end through POST /actions/{action_id}/call plus a manual loopback step on a disposable install, suite 502 passed / 0 failed. T04 Done 2026-10-18 (AC-06) -- confirmation, the single-use grant reusing T03's own consume_single_use_grant(), and the operator confirm/decline surface; suite 502 -> 511 passed, verified in a real browser against a disposable install on :8014. T05 Blocked 2026-10-18 on ESC-074 -- the shipped runner Skill (catalog/actions/call-action) and the report-unmet-request starter are built, committed and verified (AC-02/AC-03/AC-04/AC-05, 12 AC-tagged tests, suite 525 -> 538 passed, plus a live run of the shipped script over a real socket against a disposable install on :8015), but the starter is never seeded on a real install: the boot call lives in app/main.py, which is in no task's Files to Modify, and three in-scope alternatives were rejected with reasons. ESC-071 Resolved on the way past (/settings/actions is now a registered ui feature key). The story stays In Progress until that one line is authorised.
---

# REQ-SB-95-US-03 — The catalogue is published into agent context and enforced at the call — "I cannot do that" becomes a real answer

## Story

**As a** Second Brain operator
**I want** every agent to be told exactly what this app can do, and every action
call to be validated against that same catalogue before it runs
**So that** an agent stops recommending operations that do not exist, and says
"I cannot do that" when nothing in the catalogue matches — which is how a
missing capability gets discovered instead of fabricated

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-95* — the **Enforcement, not
  instruction** bullet: "An action call is validated against the catalogue: an
  unknown id is refused, a missing required input means ask rather than guess.
  Publishing the catalogue makes the agent likely to be right; validating the
  call is what makes it true. 'I cannot do that' must be a first-class answer —
  that is how a missing capability gets discovered instead of fabricated." The
  requirement's own **Acceptance** paragraph names the same two halves: "an agent
  asked for something with no matching action says so instead of inventing one,
  and a call naming an action that does not exist is refused by the framework
  rather than by the prompt".
- **Architecture is already settled — `ADR-032`** (Accepted 2026-10-16, pending a
  human look): "Enforcement lives at the call. Publishing the catalogue into
  agent context — **by the same mechanism that already publishes the
  section-access map** — makes the agent likely to be right. Validating the call
  is what makes it true." `ADR-032` also records *why* a prompt-only grounding
  was rejected: "Everything that broke on this install this autumn broke
  silently... an agent inventing an action is the same failure wearing a
  different coat. A gate is what we have learned to trust."
- **Sibling stories.** Third of `REQ-SB-95`'s five. It is the behavioural half of
  the Action spine: `US-02` makes Actions real, stored and portable but changes
  no agent behaviour; this story is where an agent's answers actually change. It
  is split out because publication plus a validating gate across the agent call
  path is its own body of work, and because `US-02` is independently valuable
  (the UI renders from the catalogue either way).
- **Grounded against the real code, not guessed.** Agent context is composed in
  `AgentManager._soul_text()` from `prompt` + `guardrails` + `scope`
  (`app/business/core/agents/agent_manager.py`, confirmed by direct reading) —
  that is the one real place anything reaches an agent's context today, and it is
  the same seam `REQ-SB-95-US-01` uses for operator facts.
- **One honest complication for the architect.** `app/config.py`'s own comment
  records that the **inbound MCP direction (Hermes calling IN to this app) was
  removed**; `hermes_mcp_shared_secret` survives as config. So "the call" is not
  one obvious existing chokepoint today — the in-app agent chat path
  (`business/logic/agent_chat_stream.py`) and a Hermes-side invocation are not
  the same surface. Every AC below is written as observable behaviour so the
  architect can choose the surface at `/plan-tasks` without this story having
  pre-decided it.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: An agent can enumerate what it can actually do

```gherkin
Given this install has a real Actions catalogue
When an agent's context is composed
Then that agent's SOUL.md carries an auto-generated, marker-delimited catalogue
    block listing exactly the Actions whose allowed_callers include that agent
    (or are ["*"]), each with its inputs and required flags, and the one way to
    call them
  And an agent permitted to call nothing carries no such block at all
  And asking that agent what it can do names only operations from that block,
    and no operation that is not a catalogued Action
```
<!-- AC-ID: REQ-SB-95-US-03-AC-01 -->

### Scenario 2: A catalogued action runs when called correctly

```gherkin
Given a catalogued Action the calling agent is permitted to run, that needs no
    confirmation
When POST /actions/<action_id>/call is made with the caller's agent id and every
    required input supplied
Then the call is accepted and dispatched by implementation kind — an http
    implementation is performed by the app, a skill implementation returns a
    single-use grant naming the deployed Skill and the validated inputs, and a
    ui implementation returns where the operator performs it and is never
    performed by the app
  And the Action-call ledger records the call with its performed, authorised or
    pointed-at outcome, and an honest failure outcome if dispatch fails
  And the operator sees the result of the real operation, not a description of it
```
<!-- AC-ID: REQ-SB-95-US-03-AC-02 -->

### Scenario 3: An unknown action id is refused by the framework, not by the prompt

```gherkin
Given an action id that is not in the live catalogue
When a call naming it reaches POST /actions/<action_id>/call
Then the framework refuses the call before any dispatch and nothing is performed
  And the refusal names the unknown id
  And the refusal is recorded in the Action-call ledger
  And the agent reports to the operator that it cannot do that, rather than
    describing an outcome that never happened
```
<!-- AC-ID: REQ-SB-95-US-03-AC-03 -->

### Scenario 4: A missing required input means ask, not guess

```gherkin
Given a catalogued Action with a required input
When a call omits that input
Then the call is refused before anything is performed and the refusal names the
    missing input
  And no default, inferred or guessed value is substituted for it anywhere
  And the agent asks the operator for that input by name
```
<!-- AC-ID: REQ-SB-95-US-03-AC-04 -->

### Scenario 5: "I cannot do that" is a first-class answer

```gherkin
Given the operator asks an agent for something no catalogued Action covers
When the agent answers
Then it states plainly that this app has no action for that request
  And it does not invent an action, promise to do it later, or claim it was done
  And the unmet request is recorded in the Action-call ledger so a genuinely
    missing capability can be discovered rather than fabricated
  And an app that cannot be reached surfaces as a connection failure, never as a
    claimed success
```
<!-- AC-ID: REQ-SB-95-US-03-AC-05 -->

### Scenario 6: A confirmation-required action is confirmed before it runs

```gherkin
Given a catalogued Action whose needs_confirmation flag is set
When an agent calls it
Then nothing is performed and the call returns awaiting_confirmation with a
    call_id recorded in the ledger
  And confirming that call_id turns the record into a single-use grant which the
    re-call consumes exactly once, performing the operation
  And declining records declined, performs nothing, and the agent says so
  And a consumed grant cannot be consumed a second time
```
<!-- AC-ID: REQ-SB-95-US-03-AC-06 -->

### Scenario 7: An agent not permitted to run an action is refused

```gherkin
Given a catalogued Action whose allowed_callers does not include a particular
    agent id
When that agent id calls it
Then the call is refused before dispatch and nothing is performed
  And the refusal states that this caller may not run that action, and is
    recorded in the ledger
  And the same caller is accepted when allowed_callers is ["*"]
```
<!-- AC-ID: REQ-SB-95-US-03-AC-07 -->

### Scenario 8: Editing the catalogue is enough — no prompt is hand-edited

```gherkin
Given an agent's published context already lists the current catalogue
When the operator adds, edits, or removes an Action
Then that agent's block is regenerated in place between its own markers, with no
    hand edit to any prompt, guardrails or scope text, no duplicate block, and
    the surrounding hand-authored text unchanged
  And an Action removed from the catalogue is no longer listed in the block and
    is refused by the gate if called
```
<!-- AC-ID: REQ-SB-95-US-03-AC-08 -->

## Affected Screens

- None new. The agent-facing surfaces that already exist show the change: the
  embedded agent chat panel and the Cockpit chat render the agent's honest
  refusals and its confirmation prompts.
- Whether the confirmation in Scenario 6 reuses the existing Pending Approvals
  surface (`REQ-SB-21`/`REQ-SB-78`, `html-prototype/my-day-approvals.html`) is an
  architecture decision left to `/plan-tasks`; if it does, that screen is reused
  as-is with no new visual pattern.

## Dependencies

- **Blocked by:** `REQ-SB-95-US-02` — there is nothing to publish or validate
  against until the Action catalogue exists.
- **Related to:** `REQ-SB-95-US-01` — shares the agent-context publication seam
  (`AgentManager._soul_text()`); whichever lands first builds it.
  `REQ-SB-95-US-04` — Workflows are published through this same mechanism.
  `REQ-SB-33-US-01` (agent grounding & honest-uncertainty guardrail) — this story
  is the enforced version of that instruction-only guardrail.
- **External:** the live Hermes install, if the architect's chosen call surface
  involves Hermes-side agents rather than only the in-app agent path.

## Constraints

- **Enforcement is a gate, not an instruction** (`ADR-032`). A prompt that merely
  tells an agent to stay within the catalogue does not satisfy any scenario here
  — the refusal must come from the framework.
- **Publication is derived, never hand-copied.** The catalogue reaches agent
  context through the same mechanism that already publishes the section-access
  map; no agent's stored prompt text may be mutated to carry a copy of it.
- **Nothing is half-performed.** A refused call performs no part of the
  operation.
- **No silent fallback.** An agent may not substitute a different action, a
  search, or a plausible narrative for an action it could not call.
- **Existing agent behaviour is otherwise unchanged** — ordinary conversation,
  memory, routing and Skills keep working exactly as they do.

## Implementation Tasks

Final split, owned by the decomposer (2026-10-16). `depends_on` holds task ids;
cross-story edges point at `REQ-SB-95-US-02` tasks.

| ID | Type | Task | ACs covered | depends_on | Task File |
|---|---|---|---|---|---|
| REQ-SB-95-US-03-T01 | backend | Publish the catalogue as a third auto-generated marker block in SOUL.md, republished by `ActionManager` — **Done 2026-10-18**, in two passes. First (`4af306a`): the block, the per-agent `allowed_callers` filtering and the idempotent roster-wide pass; `AC-01` verified, trigger left unwired on `ESC-072`. Second: `ESC-072` Resolved by a suite-wide Hermes sandbox (`tests/conftest.py` — proved at 0 Hermes seam entries and 0 writes inside the real install across the whole suite) and the three `ActionManager` call sites wired, publishing **in the background** so a save never waits (~2.7s/agent). `AC-08` verified in full, including both manual steps against a real profile: one of 41 profiles gained the block, the agent named only its own catalogued Action, an edit was reflected in a new conversation with no hand edit, and the profile was restored byte-for-byte | AC-01, AC-08 | US-02-T01 | `../Tasks/REQ-SB-95-US-03-T01-publish-catalogue-block-into-agent-context.md` |
| REQ-SB-95-US-03-T02 | backend | The validating gate (`action_invocation.py`), `POST /actions/{action_id}/call`, and the Action-call ledger — **Done 2026-10-18** (`63af8e5`): all four failure classes refuse by name, every outcome is recorded in `<DATA_PATH>/data/ActionCalls/`, validation completes before the dispatch seam is entered once, and `AC-02`/`AC-03`/`AC-04`/`AC-07` are verified by 6 AC-tagged tests plus the live-backend manual refusal. Dispatch stays `T03`'s — the seam reports `not_dispatched` in words rather than claiming an operation ran | AC-02, AC-03, AC-04, AC-07 | US-02-T03 | `../Tasks/REQ-SB-95-US-03-T02-action-call-gate-and-ledger.md` |
| REQ-SB-95-US-03-T03 | backend | Dispatch by implementation kind — `http` performed, `ui` pointed at, `skill` authorised via single-use grant — **Done 2026-10-18** (`e16013c`, `ab0ed44`, `66902a7`; `ESC-073` Resolved by an authorised scope extension that added `tests/test_action_invocation_gate.py` to this task for three named changes — the `http` wiring line, the two transitional `not_dispatched` assertions, and repointing a test Action off the real `POST /vault-index/refresh`). All three paths are wired and `AC-02` is verified end to end through `POST /actions/{action_id}/call`, plus the manual loopback step against a disposable install on `127.0.0.1:8013` where the real side effect was read back through a different route (vault overview 0 → 2 notes). Suite 502 passed, 0 failed. What shipped, in detail: `ui` is pointed at and never performed, `skill` is authorised by a single-use grant naming the deployed Skill and the validated inputs, and the one grant mechanism `T04` must reuse (`consume_single_use_grant()` over the ledger's `claim_call_once()` exclusive-create primitive) is built and proved — consumable exactly once, refused twice. `_perform_http_implementation()` is complete and proved end to end through the call route, with the two cases that must not reach a route at all (the self-referential Action, the failing operation) driving it directly (in process over `httpx.ASGITransport`, only 2xx is `performed`, honest failure otherwise, self-reference refused) **and wired into the seam**, so an `http` Action called through the gate really runs this app's own route and the verdict and the ledger carry its real result | AC-02 | T02 | `../Tasks/REQ-SB-95-US-03-T03-dispatch-by-implementation-kind.md` |
| REQ-SB-95-US-03-T04 | backend | Confirmation — `awaiting_confirmation`, the single-use grant, and the operator confirm/decline surface — **Done 2026-10-18** (`afa2b6b`, `1d9c68d`). `needs_confirmation` is honoured at the marker `T02` left, between a complete validation and the dispatch seam: the first call performs no part of the operation, opens its ledger record at `awaiting_confirmation` and refuses with that `call_id`; `GET /actions/calls/pending` + `POST /actions/calls/{call_id}/confirm|decline` are the operator's side, with a Pending confirmations region on the Actions page; a confirmed record is a single-use grant the re-call names as `confirmed_call_id` and spends through **`T03`'s own `consume_single_use_grant()`** — one mechanism, not two. Three ledger states (`awaiting_confirmation`, `confirmed`, `declined`), all named by `ADR-033`; the **refusal vocabulary is not widened** (`awaiting_confirmation` is the same single 409 carrying the whole verdict). A confirmed operation leaves **two rows joined by `granted_by_call_id`** — one id cannot carry two grants, since the claim is taken against the call id. `AC-06` verified by 9 AC-tagged tests (suite 502 → 511, 0 failed) plus the full manual step on a disposable install at `127.0.0.1:8014` with its own dev server on `:5199`, including a real headless-browser Confirm and Decline over CDP. `Agent.working_mode` and the archived approvals subsystem untouched | AC-06 | T02 | `../Tasks/REQ-SB-95-US-03-T04-confirmation-single-use-grant-and-operator-surface.md` |
| REQ-SB-95-US-03-T05 | backend | The shipped loopback runner Skill, honest refusal end-to-end, and the recorded unmet request — **Blocked 2026-10-18** (`af54a4c`, `ce38963`, `199d2dc`; `ESC-074` Open). What shipped and is verified: the runner Skill `catalog/actions/call-action/` (`SKILL.md` + `scripts/call_action.py`, stdlib-only payload the app never imports), which relays every refusal verbatim with its cause, reports `awaiting_confirmation` and **stops**, reports a `ui` Action as recorded-not-performed, performs a `skill` grant in its own profile and reports that Skill's real exit status and words, surfaces an unreachable backend as a connection failure, and refuses to call at all rather than guess its own agent id; plus the shipped starter `report-unmet-request` and `ActionManager.seed_shipped_starters()`, mirroring `seed_shipped_masters()` (never overwrites). `AC-02`/`AC-03`/`AC-04`/`AC-05` verified by 12 AC-tagged tests driving the shipped script by path through an in-process loopback transport (suite 525 → 538, 0 failed), plus the live manual run of that script over a real socket against a disposable install on `127.0.0.1:8015` — unknown id, missing input, unmet request (its words still readable in the ledger afterwards) and a stopped backend, all four honest. **What blocks it:** the seed is never called, because the boot call belongs in `app/main.py`, beside the Master Template seed it mirrors, and that file is in no task's `## Files to Modify`. `ESC-071` Resolved on the way past | AC-02, AC-03, AC-04, AC-05 | T01, T03, T04 | `../Tasks/REQ-SB-95-US-03-T05-runner-skill-and-unmet-request-record.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Authoring or storing Actions** — `REQ-SB-95-US-02`.
- **Workflows** — `REQ-SB-95-US-04` (it reuses this story's publication path).
- **Entity resolution** — `REQ-SB-95-US-05`.
- **A capability-request backlog UI.** Scenario 5 asks that an unmet request be
  recorded; turning that record into a reviewable surface is later work.
- **Rewriting every agent's prompt or guardrails.** Publication is additive.
- **Re-introducing a general inbound Hermes→app API surface** beyond whatever the
  chosen call path genuinely needs.

## Notes

**Prototype parity:**

- Agent chat / Cockpit reply rendering (where refusals and confirmations appear)
  — **Specced** (Scenarios 3, 4, 5, 6, 7) with no new region: these are ordinary
  agent messages in surfaces already approved and shipped
  (`html-prototype/inbox-cockpit.html`, `html-prototype/meeting-cockpit.html`,
  and the live Cockpit, which `REQ-SB-82-US-06` already established supersedes
  the prototype).
- Pending Approvals (`html-prototype/my-day-approvals.html`) — **Specced if
  reused** (Scenario 6), as-is, no new region; the architect decides at
  `/plan-tasks` whether confirmation routes through it.
- No net-new screen region is introduced by this story, so no `/design` pass is
  requested.

**Architect pointers for `/plan-tasks` (context, not decisions):**

- "The same mechanism that already publishes the section-access map" is
  `AgentManager._soul_text()`'s composition of `prompt`+`guardrails`+`scope`.
- The inbound MCP direction (Hermes calling into this app) was removed — see
  `app/config.py`'s own comment — so the call surface is a real decision, not a
  lookup. The in-app path is `business/logic/agent_chat_stream.py`.
- `REQ-SB-33-US-01` already ships a global honest-uncertainty instruction on the
  real reply path; this story should strengthen that into a gate rather than add
  a parallel instruction beside it.

**Architecture scope (bounds the decomposer/coder):**
`Implementation/Architecture/architecture.md` → §An Agent Acts From a Published
Catalogue (`REQ-SB-95`) → **§Catalogue Publication Into Agent Context**,
**§The Action Call Gate**, **§Confirmation and the Action-Call Ledger**.
Read-only context: §Action Catalogue — the Sixth Artifact Kind (`US-02` builds
it; this story consumes it). ADRs in force: `ADR-032`, **`ADR-033`** (this
story's spine), `ADR-019` (the app never executes `skills/catalog/` payload).

**Architect pass 2026-10-16 — the three open questions, answered:**

- **Which surface "the call" lands on — decided: `POST /actions/{action_id}/call`
  on this app's own API, reached from the Hermes side over loopback by ONE
  shipped runner Skill** (`ADR-033`). Grounded, not invented: a Hermes-side
  script already calls this app that way today
  (`vault-search/scripts/search_vault.py` → `GET /vault-search/...` at
  `SECOND_BRAIN_API_URL`, default `http://127.0.0.1:8001`;
  `build_vault_index.py` → `POST /vault-index/refresh`). This is NOT the deleted
  inbound MCP surface. The in-app chat path was ruled out as *impossible*, not
  merely undesirable: `agent_chat_stream.py` relays a Hermes session and sees
  `tool.start`/`tool.complete` after the fact. The gate itself is
  `business/logic/action_invocation.py`; the same route backs the UI.
- **`skill` implementations are authorised, not performed, by the app** — the
  response carries a single-use grant and the runner performs the Skill in the
  profile where Skills already run. `http` is performed in-app; `ui` is never
  performed, only pointed at.
- **Confirmation — decided: app-owned and per call**, in a new ledger at
  `<DATA_PATH>/data/ActionCalls/<call_id>.json`
  (`awaiting_confirmation` → confirmed single-use grant → consumed once, or
  `declined`). The Pending Approvals reuse this story's Affected Screens left
  open is **not available**: `pending_approvals_router.py` is archived and absent
  from the repo, `GET /agents/{id}/history` returns `[]` with a comment naming
  it, and `Agent.working_mode`'s own comment records that Hermes'
  `approval.request`/`respond` path was never wired (the chat stream ends the
  turn on one). So Scenario 6 uses a new, small operator surface over the ledger,
  not `html-prototype/my-day-approvals.html`.
- **Publication — decided: a third auto-generated, marker-delimited block in the
  agent's own SOUL.md**, the exact idempotent shape `_SPECIALISTS_BEGIN/END` and
  `_INDEX_GUIDANCE_BEGIN/END` already use in `AgentManager`, regenerated by
  `ActionManager` on every catalogue change the way `SkillManager` calls
  `publish_section_access_map()` on every deploy/undeploy. `ADR-033` records
  explicitly that this reads `ADR-032`'s "same mechanism that already publishes
  the section-access map" as the derived-republish *pattern*, not as a literal
  second JSON file — nothing in agent context ever reads `section_access.json`.
  **The gate reads the live catalogue, never the published text**, so stale
  publication can mislead but can never let a call through.
- **Stated honestly, for the human reviewer:** the trust boundary is loopback.
  The runner names its own profile id and the app believes it, exactly as
  `/vault-search` believes any local caller today, and an agent with a terminal
  can still run a deployed Skill directly. This makes the Action surface
  truthful; it does not sandbox Hermes.
- Scenario 5's "recorded" unmet request is a row in the same ledger; the
  framework may ship a starter `report-unmet-request` Action (`ADR-032` allows
  shipped starters). The reviewable surface over it stays out of scope.

**Decomposer pass 2026-10-16 — AC locking and the task split:**

- Eight ACs locked, `REQ-SB-95-US-03-AC-01` … `AC-08`, one per analyst scenario.
  Each now names the surface `ADR-033` decided (`POST /actions/{action_id}/call`,
  the marker block, the ledger, the single-use grant) so "refused by the
  framework" is checkable rather than interpretive.
- **AC-01 and AC-05 keep a live-agent clause** ("names only operations from that
  block"; "does not invent an action"). They remain locked rather than
  non-locked because each has a real observable outcome on top of the model's
  words — the published block's content, and a ledger row for the unmet request
  — and both tasks carry a manual step requiring the real reply to be recorded
  verbatim. This matches how this project already verifies real-agent behaviour.
- Five tasks, `T01`–`T05`. Chain: `US-02-T01 → T01`, `US-02-T03 → T02 →
  {T03, T04}`, and `T05` converging on `T01`+`T03`+`T04`. `T02` is split from
  `T03` deliberately: the gate must be provably complete *before* anything can
  be dispatched, which is the whole point of "nothing is half-performed".
- **The Pending Approvals surface is not planned against at all** — the
  architect's evidence that `pending_approvals_router.py` is absent is restated
  as a hard constraint in `T04`, which builds a small new surface over the
  ledger instead.
- Backend ACs get AC-tagged automated tests (`pytest tests/<file>.py` from
  `src/backend`) against the real backend stack; the one frontend touch in `T04`
  is a structural DOM check.
- Gate left as the architect set it (trigger 3, `ADR-033`) — no additional
  trigger fired in this pass. No `ESCALATIONS.md` entry; no new
  `REVIEW-QUEUE.md` item (the open `REQ-SB-95-US-03` entry already asks for the
  `ADR-033` call-path review these tasks are built on).

**Audit breadcrumb:**

gate: flagged 2026-10-16 (architect) — trigger 3: `ADR-033` created, and it is
this story's whole spine. No `ESCALATIONS.md` entry: nothing here contradicts
`ADR-032`, the PRD or `MEMORY.md` — the one interpretation taken (what "the same
mechanism" means) is recorded in `ADR-033` itself so a human can correct it
cheaply. The prior analyst breadcrumb below remains accurate.

gate: clear 2026-10-16 — no triggers fired. No material assumption: every
scenario asserts only what the PRD's Enforcement bullet and its own Acceptance
paragraph already state, and the one genuinely open question (which surface "the
call" lands on) is architecture, left open by writing behavioural ACs rather than
guessed at. `REQ-SB-95` is finalised in the PRD and carries no `<!-- Draft -->`
marker. No ADR created or changed by this pass (`ADR-032` is pre-existing). No
`ESCALATIONS.md` entry. Not oversized (~4 tasks, M). No contradictory inputs. No
second equally-valid scoping — the two halves (publish, validate) are named
explicitly by both the PRD and `ADR-032`.
