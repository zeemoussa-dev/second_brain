---
id: SPRINT-088
title: The catalogue published into agent context and enforced at the call — "I cannot do that" becomes a real answer
status: In Progress                      # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "One task blocked: REQ-SB-95-US-03-T05 on ESC-074 — the shipped report-unmet-request starter is built, tested and committed but never seeded, because the boot call belongs in app/main.py and that file is in no task's Files to Modify. Everything else in T05 is verified (AC-02/03/04/05, suite 538 passed). T01-T04 are Done. The sprint cannot close and no retrospective is drafted until that one line is authorised."
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-087]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~5 tasks, L"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-10-16
started: 2026-10-18                        # YYYY-MM-DD when status → In Progress
completed: ""                      # YYYY-MM-DD when status → Done
---

<!-- STATUS LIFECYCLE — who drives each transition:
     Draft       → product-owner assembles the sprint. Bidirectional link is written
                   at creation: every story listed here already has sprint: SPRINT-NNN.
     Ready       → product-owner advances Draft→Ready when grouping is CLEAR (gate: clear).
                   Ambiguous, oversized, or blocked grouping stays Draft + gate: flagged.
                   Adding a story to a Ready sprint AUTO-REVERTS it to Draft.
     In Progress → /implement-sprint has started. Coder sets this + records started:.
     Blocked     → external dependency is unmet. Record it under Dependencies.
     Done        → every story is Done and every DoD box is checked. Coder sets this,
                   records completed:, DRAFTS the retrospective, and sets gate: flagged
                   for the human to skim and harvest Learnings.md.
-->

# SPRINT-088 — Published Catalogue and Call Enforcement

## Sprint Goal

Tell every agent exactly what this app can do, from the live catalogue, and
validate every action call against that same catalogue before it runs — so an
unknown id is refused by the framework rather than by the prompt, and "I cannot
do that" becomes a real answer with a recorded unmet-request.

---

## Grouping Rationale & Sizing

- **Why grouped (and why alone):** `REQ-SB-95-US-03` is the behavioural half of
  the Action spine and sits one wave behind `US-02`. Its two inbound edges are
  recorded in the task files: `US-03-T01 → US-02-T01` (the catalogue entity it
  publishes from) and `US-03-T02 → US-02-T03` (the CRUD API the call gate
  validates against). Everything else is internal: `T02 → T03`, `T02 → T04`,
  `(T01, T03, T04) → T05`.
- **Why it is not merged back into `SPRINT-087`.** 6 + 5 = 11 tasks, past the
  confirmed 8–9-task `L` ceiling — and this project has a repeatedly-confirmed
  precedent (`SPRINT-011`→`012`, `025`→`026`, `049`→`050`) that a downstream
  story whose own Tests need the **real, running** output of the upstream one is
  better sequenced behind it than improvised against an imagined interface.
  That is exactly this case: the call gate's ACs need a real, stored, resolvable
  Action to refuse and to accept.
- **Why `US-04` and `US-05` are not folded in here.** Both depend on *this*
  story as well as on `US-02` (`US-04-T05 → US-03-T04`, `US-04-T06 → US-03-T01`,
  `US-05-T05 → US-03-T02`/`US-03-T03`), so neither can be built alongside it;
  they go one wave later.
- **Sizing:** 5 tasks, sized `L` — deliberately a notch above this project's
  5-task norm (`SPRINT-032`/`034`/`038` at `S`, `SPRINT-081` at `M`). Code volume
  is not the driver: this is the sprint where agent answers actually change, so
  every locked AC needs real, live agent-call verification across a loopback call
  path, a single-use confirmation grant and a ledger. This project's Learnings
  name that cost explicitly and repeatedly ("verification cost, not code volume,
  drove the real effort" — `SPRINT-031`, `SPRINT-036`).

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-088 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-95-US-03](../UserStories/REQ-SB-95-US-03-published-catalogue-and-call-enforcement.md) | The catalogue is published into agent context and enforced at the call — "I cannot do that" becomes a real answer | P2 | Ready |

Build order inside the sprint, read from the task files' own `depends_on`:
`T01` (needs `US-02-T01`), `T02` (needs `US-02-T03`) `→ T03`, `T02 → T04`,
`(T01, T03, T04) → T05`.

---

## Dependencies / External Blockers

- **`Done`, 2026-10-18 — `T04`. Nothing is blocked; only `T05` remains, and it
  is unblocked.** Confirmation is honoured at the marker `T02` left, between a
  complete validation and the dispatch seam: the first call of a
  `needs_confirmation` Action performs no part of the operation, opens its
  ledger record at `awaiting_confirmation` and is refused with that `call_id`.
  The operator decides on `GET /actions/calls/pending` +
  `POST /actions/calls/{call_id}/confirm|decline` and a Pending confirmations
  region on the existing Actions page; the archived Pending Approvals
  subsystem is not revived and `Agent.working_mode` is untouched. A confirmed
  record is a single-use grant the re-call names as `confirmed_call_id` and
  spends through **`T03`'s own `consume_single_use_grant()`** — the one
  mechanism, reused rather than duplicated. Three ledger states
  (`awaiting_confirmation`, `confirmed`, `declined`), all named by `ADR-033`;
  the **refusal vocabulary is not widened** — `awaiting_confirmation` is the
  same single 409 carrying the whole verdict, and a client still branches on
  `accepted` alone. One structural finding worth carrying: a confirmed
  operation leaves **two ledger rows** joined by a new `granted_by_call_id`,
  because the claim that makes a grant single-use is taken *against the call
  id*, so one id can never carry two grants. `AC-06` verified by 9 AC-tagged
  tests — suite **511 passed, 0 failed** against a measured 502 baseline at
  `e6a738f` — plus the full manual step against a **disposable install on
  `127.0.0.1:8014`** with its own dev server on `:5199`, where the screen half
  was driven in a **real headless browser over CDP**: Confirm turned the badge
  to "Confirmed — not run yet" and created nothing, Decline removed the row,
  and the agent's re-calls afterwards returned `performed` and a refusal naming
  `declined`. Re-measured behind the write/outbound interceptor: 0 writes in
  the real vault, data path or Hermes home, 0 outbound requests, no connect to
  port 8001 — identical with the new file excluded. Commits `afa2b6b`,
  `1d9c68d`.
- **UNBLOCKED AND `Done`, 2026-10-18 — `T03` (`ESC-073` Resolved).** The
  orchestrator authorised the scope extension, so
  `src/backend/tests/test_action_invocation_gate.py` joined `T03`'s files for
  the three changes `ESC-073` named. The seam's `http` branch now calls
  `_perform_http_implementation()`, the two transitional `not_dispatched`
  assertions assert `performed` **and the route's real result**, and that
  file's test Action is off the real `POST /vault-index/refresh` and onto a
  harmless test-only target (its two dispatching tests now cost 0.05s and
  0.03s). `AC-02`'s `http` test runs end to end through
  `POST /actions/{action_id}/call`, and its manual loopback step passed against
  a **disposable install on `127.0.0.1:8013`** — two notes written behind the
  backend's back stayed invisible until the Action call returned `performed`
  with the route's own `{"notes_indexed": 2}`, after which the vault overview
  read 2. The operator's `:8001` was never called. Suite **502 passed, 0
  failed**, identical to the baseline taken before the first edit, and
  re-measured behind the write/outbound interceptor with dispatch live: 0
  writes in the real vault or the real Hermes home, no outbound request, no
  connect to port 8001. Commit `66902a7`. Only `T04` and `T05` remain.
  *(What follows is the original blocked note, kept for the record.)*
- **BLOCKED IN FLIGHT, 2026-10-18 — `T03` (`ESC-073`).** Two of the three
  dispatch paths and the whole single-use grant mechanism are built, tested and
  committed (`e16013c`, `ab0ed44`; suite 490 → 497, 0 failed): `ui` is pointed
  at and never performed, `skill` is authorised by a single-use grant, and
  `consume_single_use_grant()` over the ledger's exclusive-create
  `claim_call_once()` is the one mechanism `T04` is meant to reuse rather than
  reinvent. `_perform_http_implementation()` is complete and proved by three
  tests driving it directly, but **the one line wiring it into the seam is
  withheld**: it needs two assertions changed in
  `src/backend/tests/test_action_invocation_gate.py`, outside `T03`'s
  `## Files to Modify` — one pins `T02`'s transitional `not_dispatched`, and the
  other points a test Action at the real `POST /vault-index/refresh`, which live
  dispatch turns into a full re-read of the operator's vault on every suite run
  (measured 1.09s → 8.60s). A human decision is parked in `REVIEW-QUEUE.md`.
  **The sprint is not stalled:** `T04` is independent of `T03` and buildable
  now; only `T05` converges on it. Meanwhile the `http` branch reports
  `not_dispatched`, which is exactly what `T02` already shipped, so nothing
  regressed on the live install.
- **UNBLOCKED AND `Done`, 2026-10-18 — `T01` (`ESC-072` Resolved).** The
  orchestrator added `src/backend/tests/conftest.py` to `T01`'s files and the
  operator decided the cost question (publish in the background, return
  immediately). Both halves shipped: a suite-wide autouse Hermes sandbox
  (`hermes_home_path` at a non-existent tmp directory + `HermesCLI._hermes_exe`
  stubbed, proved by interception at **0 Hermes seam entries and 0 writes inside
  the real install** across the whole suite) and the three wired
  `ActionManager.create/update/delete` call sites. Backend suite 487 → 490. Both
  locked ACs verified, including the two manual steps against a real profile. The
  blocked note below is kept for the record.
- **BLOCKED IN FLIGHT, 2026-10-18 — `T01` (`ESC-072`).** The SOUL.md catalogue
  block, its per-agent `allowed_callers` filtering and the roster-wide
  republication pass are built, tested and committed (`4af306a`); `AC-01` is
  verified. The `ActionManager.create/update/delete` trigger is **unwired**: the
  backend suite has no Hermes sandbox, and with it wired the four existing Action
  test files attempted 123 real `SOUL.md` writes across all 41 live profiles
  (measured behind an interceptor, never run for real). Isolating those files is
  outside `T01`'s `## Files to Modify`. A human decision is parked in
  `REVIEW-QUEUE.md`. **The sprint is not stalled:** `T02` is buildable now,
  `T03`/`T04` follow it, and only `T05` converges on `T01`.
- **Depends on sprints:** `SPRINT-087` (`REQ-SB-95-US-02` — the Action entity,
  its Manager and its CRUD API). `/implement-sprint` refuses this sprint until
  `SPRINT-087` is `Done` (hard rule 9).
- **Two sprints depend on this one:** `SPRINT-089` (`US-04`) and `SPRINT-090`
  (`US-05`).
- **Shared file with `SPRINT-086`, with no dependency edge between them.**
  `US-03-T01` (here) and `US-01-T02` (`SPRINT-086`) each add their own
  independent auto-generated marker pair to
  `src/backend/app/business/core/agents/agent_manager.py`. No edge was recorded
  between them and neither reads the other's block, but their titles disagree
  about who lands first (`US-03-T01` calls its pair "the third", `US-01-T02`
  calls its own "the fourth"; both describe the same **two** existing pairs).
  The ordinal is cosmetic — no AC depends on it. Under this plan `SPRINT-086`
  lands first, so this story's pair is in fact the fourth. Compose around the
  **real current file**, not the task's remembered version of it.
- **Story-level gate carried forward (`gate: flagged`, not resolved by this
  sprint):** `REQ-SB-95-US-03` is flagged under trigger 3 — `ADR-033` decides
  how an agent actually invokes an action (one loopback route on this app's own
  API, reached by a shipped runner Skill; confirmation as an app-owned
  single-use grant) and awaits the operator's look. That call path is what this
  whole sprint builds, so it is worth reading before the build starts. See
  `REVIEW-QUEUE.md`.

---

## Out of Scope

- The Action catalogue itself — `SPRINT-087`.
- Workflows (`SPRINT-089`) and entity resolution (`SPRINT-090`).
- The Operator Profile's own marker block (`SPRINT-086`).

---

## Definition of Done

- [ ] Every story in scope has status `Done`
- [ ] All story-level Definitions of Done satisfied
- [ ] `BACKLOG.md` updated — every affected row reflects current status
- [ ] `architecture.md` updated if the sprint changed an architectural fact
- [ ] Any new ADRs recorded in `ADR.md` with status `Accepted`
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended
- [ ] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes

**gate: flagged 2026-10-18 (coder) — one task blocked, and the sprint stays open
for it.** `T01`, `T02`, `T03` and `T04` are `Done`; seven of the story's eight
locked ACs are verified (`AC-01`…`AC-08` less nothing — `AC-05` is verified at
the mechanism and on a disposable install, not on a real install, see below).
`T05` is `Blocked` on **`ESC-074`**: its shipped `report-unmet-request` starter
and the `seed_shipped_starters()` that installs it are built, tested and
committed, and nothing calls the seed — the boot call belongs in `app/main.py`,
five lines below the Master Template seed it mirrors, and that file is in no
task's `## Files to Modify`. Three in-scope alternatives were worked through and
rejected (two break a `Done` task's test, the third puts an Action in the gate
that no agent is told about); the escalation quotes the exact addition to
authorise. **No retrospective is drafted while a task is blocked** — it is
written when the sprint closes, which is one authorised line away.

`ESC-071` (the `/settings/actions` key missing from `UI_FEATURE_KEYS`, left Open
by `SPRINT-087`) is **Resolved** inside `T05`, via that escalation's own option
(b): the starter is a `ui` implementation and the Actions page is the only screen
it can honestly name. The drift *mechanism* it exposed is untouched and is the
first entry under the retro's open follow-ups when this sprint closes.

**gate: clear 2026-10-16 — no product-owner trigger fired.** No assumption (both
inbound edges are quoted from the task files); requirement finalised; no ADR
created or changed by this pass; no `ESCALATIONS.md` entry; **not oversized**
(5 tasks); **no `Blocked` story**. On trigger 5's cross-sprint clause: the
`depends_on_sprints: [SPRINT-087]` edge is **not a dependency this pass
introduced** — it is the decomposer's own `US-03-T01 → US-02-T01` /
`US-03-T02 → US-02-T03` edges expressed at sprint level, forced by the fact that
28 tasks cannot be one sprint. Recording it, rather than inventing a merge that
breaks the sizing ceiling, is what hard rule 7 asks for, and it matches this
repo's own precedent for the same situation (`SPRINT-080` ← `079`,
`SPRINT-083` ← `082`, `SPRINT-084` ← `083`, all `gate: clear`). No contradictory
inputs (the marker-block ordinal mismatch above is cosmetic and recorded), and no
ambiguity about the partition.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** _(from `sizing_estimate:`)_ — **Actual:** _(tasks / effort)_ — **Takeaway:** _(over/under, why)_

### What worked

- _(specific behaviour, decision, or technique that paid off)_

### What didn't work

- _(specific friction, dead end, or mistake — name the root cause if known)_

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- _(pattern — short title — when to apply)_

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- _(antipattern — short title — why to avoid)_

### Open follow-ups

- _(follow-up — filed as what and where?)_
