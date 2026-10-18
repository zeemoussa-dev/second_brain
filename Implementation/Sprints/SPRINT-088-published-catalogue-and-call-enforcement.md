---
id: SPRINT-088
title: The catalogue published into agent context and enforced at the call — "I cannot do that" becomes a real answer
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint closed 2026-10-18 — every task Done, nothing blocked, all eight locked ACs verified. Flagged for the standard close: the coder drafted the ## Retrospective below and the human harvests its patterns/antipatterns into Implementation/Learnings.md. Three open follow-ups are named there and none of them blocks anything."
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-087]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~5 tasks, L"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-10-16
started: 2026-10-18                        # YYYY-MM-DD when status → In Progress
completed: 2026-10-18              # YYYY-MM-DD when status → Done
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
| [REQ-SB-95-US-03](../UserStories/REQ-SB-95-US-03-published-catalogue-and-call-enforcement.md) | The catalogue is published into agent context and enforced at the call — "I cannot do that" becomes a real answer | P2 | Done |

Build order inside the sprint, read from the task files' own `depends_on`:
`T01` (needs `US-02-T01`), `T02` (needs `US-02-T03`) `→ T03`, `T02 → T04`,
`(T01, T03, T04) → T05`.

---

## Dependencies / External Blockers

- **UNBLOCKED AND `Done`, 2026-10-18 — `T05` (`ESC-074` Resolved). Nothing is
  blocked; the sprint is closed.** `app/main.py` was authorised into `T05`'s
  `## Files to Modify` for the seed call and nothing else, and `dcfa14b` adds
  it — 15 lines, beside the Master Template seed it mirrors, 0 removed. The
  shipped `report-unmet-request` starter now really installs itself on a real
  install. Proved on a **disposable install on `127.0.0.1:8016`** (its own
  vault, data path and a Hermes home pointed at a directory that does not
  exist; the operator's `:8001` was never called and was still listening
  afterwards): the first boot printed
  `[startup] seeded starter Actions: report-unmet-request`, `GET /actions`
  returned it, and the **shipped runner script, copied into a profile in the
  deployed flat shape and run as a real subprocess over a real socket**, called
  it and got `RECORDED, NOT PERFORMED` with the operator's own words in the
  ledger at `pointed_at` — on an install whose only contact with the starter
  was starting up. The never-overwrite rule was proved rather than asserted: a
  hand edit to the seeded Action's description survived a restart, and the
  second boot printed no seed line at all. Suite **538 → 548 passed, 0
  failed**, the +10 being the concurrent `SPRINT-091` session's `e373391`, not
  this change; **no test enters `app.main`'s lifespan**, so the suite's
  side-effect profile is unchanged — re-measured behind the write/outbound
  interceptor at 9 protected-root touches (all pre-existing `mkdir` on the
  data-path root), 0 connects to `:8001`/`:8088`/`:8090`/`:5173`, 1 real httpx
  request (the pre-existing unreachable-port test), 0 `urlopen`.
  *(What follows is the original blocked note, kept for the record.)*
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

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — §The Action Call Gate and §Confirmation and the Action-Call Ledger were updated by the tasks that changed them
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — `ADR-032`/`ADR-033` pre-date this sprint and are Accepted; this sprint created none
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes

**gate: flagged 2026-10-18 (coder) — the sprint is `Done` and the flag is the
standard close, not a block.** `T05`'s one authorised line landed (`dcfa14b`,
`ESC-074` Resolved), the starter really installs on boot, and all five tasks and
all eight locked ACs are verified. The flag asks for one thing only: skim the
`## Retrospective` below and harvest its *Patterns to carry forward* and
*Antipatterns to avoid* into `Implementation/Learnings.md` — the coder drafts,
the human harvests. Three open follow-ups are named at the end of the retro;
none of them blocks `SPRINT-089` or `SPRINT-090`, both of which this sprint
closing unblocks. *(The blocked note below is kept for the record.)*

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

- **Estimated:** `~5 tasks, L` — **Actual:** 5 tasks, 10 commits, `L` and
  honestly so — **Takeaway:** the task count was exactly right and the `L` was
  right for the wrong reason. The sizing note predicted the cost would be
  verification rather than code volume, and that held: every task needed a real
  running backend, and four of the five were verified against a **disposable
  install on its own port** (`:8013`, `:8014`, `:8015`, `:8016`) because the
  thing under test writes to a vault, a data path and Hermes profiles. What the
  estimate did **not** price is the cost this sprint actually paid: **three of
  five tasks stopped mid-flight on the same scope defect** (`ESC-072`,
  `ESC-073`, `ESC-074`), each needing a human round-trip before a task that was
  otherwise finished could be marked `Done`. That is not effort an `L` absorbs —
  it is wall-clock latency the estimate has no unit for. Worth noting for the
  next sprint sized on "verification cost, not code volume": add "how many human
  round-trips does this plan imply?" as a second axis.

### What worked

- **Building the gate before anything could be dispatched.** The decomposer
  split `T02` (validate, record, refuse) from `T03` (dispatch) deliberately, and
  it paid off twice. `T02` shipped a seam that reported `not_dispatched` **in
  words** instead of claiming an operation ran, so the install was never in a
  state where a call looked successful and wasn't; and when `T03` was blocked
  mid-flight, the honest placeholder was still the shipped behaviour, so nothing
  regressed while a human decided. "Nothing is half-performed" was a property of
  the build order, not just of the code.
- **One mechanism, reused rather than reinvented.** `T03` built
  `consume_single_use_grant()` over the ledger's exclusive-create
  `claim_call_once()`; `T04` spent the confirmation grant through that same
  function instead of writing a second single-use mechanism beside it. The
  structural finding fell straight out of the reuse: a confirmed operation
  leaves **two** ledger rows joined by `granted_by_call_id`, because the claim
  is taken against the call id, so one id can never carry two grants. Two
  parallel implementations would have disagreed about that silently.
- **A separate `accepted` field, distinct from `outcome`.** `T02` made them
  separate on purpose and `T05`'s runner branches on `accepted` **and nothing
  else**. That one decision means a future outcome word cannot be read as
  success by a client that has never heard of it — the shipped runner's refusal
  path is safe against vocabulary it does not know, which is the exact failure
  mode "no silent fallback" is about.
- **The suite-wide Hermes sandbox, written once in `conftest.py` rather than
  four times.** `ESC-072` surfaced because wiring one trigger would have made
  four existing test files attempt **123 real `SOUL.md` writes across 41 live
  profiles** — measured behind an interceptor, never run for real. Fixing it in
  `conftest.py` protected every test written afterwards for free, including all
  twelve of `T05`'s, and it needed a second seam nobody had spotted
  (`HermesCLI._hermes_exe()` falling back to the real `hermes` on PATH, whose
  home comes from the environment and not from our config). A sandbox that
  covers one seam is not a sandbox.
- **Measure the blast radius before running the suite, every time.** Every task
  in this sprint ran the whole suite behind a plugin intercepting writes,
  subprocesses, sockets, `httpx` and `urlopen`, classifying each target against
  the real vault, data path and Hermes home. It caught `ESC-072` before any
  damage, caught `ESC-073`'s "this test re-reads your entire vault on every run"
  (1.09s → 8.60s) before it shipped, and in this last pass it is what turned
  "the seed probably doesn't affect tests" into the checkable fact that **no
  test enters `app.main`'s lifespan at all**.
- **Verify on a disposable install on its own port, never the operator's.** Four
  ports, four throwaway installs, each with its own vault, data path and Hermes
  home — and `:8001` demonstrably never called in any of them. It made real
  verification (a real browser over CDP in `T04`, a real subprocess over a real
  socket in `T05`) something that could be done freely instead of something to
  be nervous about.
- **Driving the shipped payload script by path, through its real `main()`.**
  `T05`'s tests load the actual deployed file over a real command line and
  replace only `urlopen`, handing the very `Request` the runner built to an
  in-process `TestClient`. The gate, the dispatch and the ledger are all real;
  no socket opens. That is as close to "test the thing that ships" as a payload
  script can get without a network.

### What didn't work

- **Three tasks out of five stopped on the same defect: `## Files to Modify`
  names where new code *lives* and not the one line that makes it *run*.**
  `ESC-072` (the trigger was unwired), `ESC-073` (the `http` dispatch branch was
  built and switched off), `ESC-074` (the starter was built and never seeded).
  In every case the feature was finished, tested and committed, and the product
  did not have it. The root cause is a decomposition habit, not three unlucky
  tasks: a task file that lists the new module but not its call site produces a
  coder who correctly refuses to touch the call site.
  **This has been acted on, not left as an observation.** The generator is
  fixed rather than the instance: `.claude/agents/decomposer.md` now carries a
  standing rule to name the switch-on site in `## Files to Modify`, with all
  five escalations of this shape (`ESC-069`, `ESC-071`, `ESC-072`, `ESC-073`,
  `ESC-074`) cited as its evidence, and framework `MEMORY.md` records it
  (`fe4b0c1`). The loop is closed; the next reader should see a fixed generator,
  not a complaint repeated a sixth time.
- **A hand-maintained mirror of another build's route table drifts by
  construction.** `ESC-071` — `/settings/actions` was missing from
  `UI_FEATURE_KEYS`, so the one Action this sprint ships could not name the one
  screen it points at. The key was added in `af54a4c`, which fixes the instance
  and not the mechanism: the backend keeps a hand-copied list of the frontend's
  routes, while a `skill` implementation resolves against the **live** deployed
  catalogue. The two kinds of implementation are held to different standards of
  truth, and the weaker one will drift again. Carried as an open follow-up below.
- **The live-agent clause in `AC-01` and `AC-05` is the one thing this project
  cannot cheaply verify.** `T01` managed it (one of 41 real profiles, restored
  byte-for-byte afterwards). `T05` could not: deploying the runner Skill into a
  live profile is the exact accident `conftest.py` exists to prevent, and a
  disposable install has no Hermes gateway or model keys. What was run instead —
  the shipped script over a real socket — is literally the text the agent would
  relay, and it is recorded as an **assumption for human spot-check rather than
  as a pass**. That is the honest answer, but the gap is real and will recur in
  `SPRINT-089`, which has live-agent clauses of its own.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Name the switch-on site, not just the new module** — when a task adds code
  that something else must call, `## Files to Modify` names the call site too,
  or the task ships a feature the product does not have. Now a standing rule in
  `.claude/agents/decomposer.md`; five escalations in two sprints are its
  evidence.
- **Measure the blast radius before you trust a test suite** — run the suite
  once behind an interceptor over writes, subprocesses, sockets, `httpx` and
  `urlopen`, classifying every target against the real vault, data path and
  Hermes home. Apply whenever a change makes a test path able to write somewhere
  it previously only read. It has now caught three distinct accidents before
  they happened.
- **Sandbox the whole suite in `conftest.py`, not the files you happen to be
  editing** — and sandbox *every* seam that can reach the live install, not the
  obvious one. A suite that can corrupt the machine running it must fail safe by
  default, not by convention.
- **Verify on a disposable install on its own port** — own vault, own data path,
  own (non-existent) Hermes home, and state in the log which port and that the
  operator's was never called. It converts "we could test this for real" from a
  risk into a routine.
- **Branch on an explicit `accepted` field, never on the outcome vocabulary** —
  keep the "did this happen?" boolean separate from the "what happened?" word,
  so a client that has never heard of a new outcome refuses it instead of
  reading it as success.
- **Build the gate before anything can be dispatched** — split "validate,
  record, refuse" from "perform" into separate tasks, and make the unbuilt half
  report its absence in words. The install is never in a state where a call
  looks successful and isn't, and a mid-flight block costs nothing.
- **Drive a shipped payload script by path, through its real entry point** —
  load the actual file, pass a real command line, and replace only the outermost
  transport. Anything else tests a copy of the logic rather than the artefact
  that gets deployed.
- **Re-measure the baseline, never assume it** — on a checkout with more than
  one session live, HEAD moves mid-task. This sprint's tasks reported
  511 → 525 → 538 → 548 and every step was a measured number with the
  concurrent commit named. A remembered baseline would have read as a
  regression.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Composing an entity on read to avoid a boot-time seed** — it looks like it
  saves a call site and it quietly bypasses the store, so every test that
  isolates the store is silently wrong about what exists. Three in-scope
  alternatives to `ESC-074` were rejected for exactly this; two of them broke a
  `Done` task's test and the third would have put an Action in the gate that no
  agent is told about and no screen lists.
- **Hand-copying another build's route table into this one** — a mirror with no
  mechanism behind it drifts by construction, and the drift surfaces as a
  refusal the operator reads as a bug in their own data (`ESC-071`).
- **Pointing a test at a real, expensive production route** — `T03` found a test
  Action aimed at the real `POST /vault-index/refresh`; the moment dispatch went
  live that became a full re-read of the operator's vault on every suite run
  anybody did. Test Actions point at harmless test-only targets.
- **Marking a live-agent AC "passed" on the strength of the mechanism** — if the
  model-side half was not performed, say which half was not performed and record
  it as an assumption. "The mechanism works, therefore the agent will say the
  right thing" is the shape of claim this whole sprint exists to stop agents
  making.

### Open follow-ups

- **`UI_FEATURE_KEYS` drift (`ESC-071`, instance fixed, mechanism untouched).**
  The backend keeps a hand-maintained mirror of the frontend's route table so a
  `ui` Action can name a screen; `/settings/actions` was missing from it and was
  added by hand in `af54a4c`. A `skill` implementation, by contrast, resolves
  against the **live** deployed catalogue. Until `ui` resolves against something
  real too — generated from the frontend's own route table, or checked by a test
  that fails when the two disagree — this will drift again and will present as
  an Action the operator cannot save. **Filed as:** this follow-up and
  `ESC-071`'s own entry in `ESCALATIONS.md`; no story yet.
- **No route exposes `consume_single_use_grant(reported_outcome=…)`, so a
  performed grant's ledger row still reads `authorised`.** `T03` built the
  parameter for exactly this and nothing calls it with an outcome: when the
  runner performs a granted Skill it has no way to tell the app the Skill
  finished, or whether it succeeded. The operator learns the real result from
  the agent's words, and the ledger — the thing meant to be the record — stops
  one step short. Both files that would close it (`actions_router.py`,
  `action_invocation.py`) were outside `T05`'s scope, so it was recorded rather
  than improvised. **Filed as:** judgement call 6 in `T05`'s
  `## Implementation Log` and this follow-up; it wants a small story of its own,
  and `SPRINT-089`'s workflow runs will want the same reporting channel.
- **`MEMORY.md` is ~80 KB against its own 40 KB budget.** It is read at the
  start of every task in this pipeline, so the overrun is paid repeatedly by
  every agent, and the practical effect is that the file stops being read
  carefully — which is how a rule already written down gets broken anyway.
  Splitting or pruning it is a human call about what is still true, not
  something a coder should do inside a task. **Filed as:** this follow-up.
- **The live-agent half of `AC-05` was not performed** (no Hermes gateway or
  model keys on a disposable install, and deploying into one of the operator's
  41 live profiles is the accident the sandbox exists to prevent). Recorded as
  an assumption in `T05`'s `## Implementation Log`, not as a pass. **Filed as:**
  that assumption plus the `REVIEW-QUEUE.md` entry for `T05`; it needs a human
  spot-check in a real chat, and the same gap will recur in `SPRINT-089`.
