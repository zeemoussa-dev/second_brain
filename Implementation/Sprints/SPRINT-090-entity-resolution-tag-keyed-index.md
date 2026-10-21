---
id: SPRINT-090
title: Entity resolution instead of search — one tag-keyed index, synthesis first then evidence
status: Done                       # Draft | Ready | In Progress | Blocked | Done
gate: flagged                      # clear | flagged — flagged ⇒ parked in REVIEW-QUEUE.md
gate_reason: "Sprint closed: the retrospective below is DRAFTED and awaits the human harvest into Implementation/Learnings.md. Carried with it, not blocking the close: ESC-081 (new, Open) — REQ-SB-101's default-deny middleware refuses the Action gate's own in-process dispatch, so every `http`-implementation Action answers `outcome: failed` on a signed-in install; it is a REQ-SB-101 x REQ-SB-95 boundary and belongs to neither story alone."
phase: P2                          # single phase only — a sprint never mixes phases
depends_on_sprints: [SPRINT-087, SPRINT-088]   # SPRINT-NNN IDs that must be Done before this can start
sizing_estimate: "~5 tasks, M"     # effort estimate (e.g. "~6 tasks, M"); checked vs actual in retro
created: 2026-10-16
started: 2026-10-18                # YYYY-MM-DD when status → In Progress
completed: 2026-10-21              # YYYY-MM-DD when status → Done
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

# SPRINT-090 — Entity Resolution Instead of Search — One Tag-Keyed Index

## Sprint Goal

Make a named entity in a question resolve to a real kind, tag and hub note, and
have the answer read from that entity's own scoped synthesis and then its
evidence — one tag-keyed index serving every entity, reachable by an agent as a
catalogued Action rather than only as a route.

---

## Grouping Rationale & Sizing

- **Why grouped (and why alone):** `REQ-SB-95-US-05` is the retrieval half of
  the requirement and is almost entirely self-contained — `T01` and `T02` are
  independent roots, `T03` joins them, `T04` follows. Its **only** reach into
  the Action spine is its last task: `US-05-T05`
  `depends_on: [US-05-T04, US-02-T02, US-03-T02, US-03-T03]` — the scenario where
  the scoped read becomes reachable *through the catalogue*. That single edge is
  what puts this sprint behind `SPRINT-087` and `SPRINT-088`; the story's own
  text says the same ("its only dependency on the spine is Scenario 6").
- **Why not merged with `SPRINT-088` or `SPRINT-089`.** With `US-03`: 5 + 5 = 10
  tasks, past the confirmed 8–9-task `L` ceiling. With `US-04`: 5 + 7 = 12 —
  further past it, even though the two share identical upstream sprints and have
  **zero edges between them**. Being mutually independent, `SPRINT-089` and
  `SPRINT-090` may be built in either order once their two upstream sprints are
  `Done`; the numbering carries no ordering claim between them.
- **Sizing:** 5 tasks, sized `M`, matching this project's 5-task precedents
  (`SPRINT-081` at `M`; `SPRINT-032`/`034`/`038` at `S`). Sized `M` rather than
  `S` because `T01` rebinds a projection inside `VaultManager.rebuild_index()`
  against a real, large vault, and `T05` is a four-way integration task whose
  verification needs the real catalogue and the real call gate from two earlier
  sprints.
- **This ordering closes an open plan gap, by design.** `ADR-037` takes the
  `FRAMEWORK_API` 7 → 8 bump **once**, in whichever plugin-contract story lands
  last. `US-05-T02` reads the real `app/plugin_api.py` first and bumps only if
  `register_action` is already present; the sibling `US-02-T05` carries **no**
  equivalent instruction, so if `US-02` landed last nobody would move the
  constant and no plugin could ever use either capability. The
  `depends_on_sprints: [SPRINT-087, …]` edge makes `US-02` land first with
  certainty (hard rule 9), so `US-05-T02`'s conditional read takes the bump.
  This is the second of the two resolution options the `REVIEW-QUEUE.md` item
  itself offered ("tell the product-owner to sequence `US-05` after `US-02`"),
  and it required **no edit to any task file**.

---

## Stories in Scope

<!-- Every story listed here MUST have sprint: SPRINT-090 in its frontmatter —
bidirectional link, written at sprint creation. Order by implementation dependency
(dependency-first). Status column mirrors the live story status; update on change. -->

| Story | Title | Phase | Status |
|---|---|---|---|
| [REQ-SB-95-US-05](../UserStories/REQ-SB-95-US-05-entity-resolution-tag-keyed-index.md) | Entity resolution instead of search — one tag-keyed index, synthesis first then evidence | P2 | **Done 2026-10-21** (`T01`, `T02`, `T03` Done 2026-10-18 — `T02` unblocked the same day by `ESC-079` Resolved; `T04` Done 2026-10-19; `T05` Done 2026-10-21 by `ESC-080` Resolved) |

Build order inside the sprint, read from the task files' own `depends_on`:
`(T01, T02) → T03 → T04 → T05` (`T05` also needs `US-02-T02`, `US-03-T02`,
`US-03-T03`, all delivered by `SPRINT-087`/`SPRINT-088`).

---

## Dependencies / External Blockers

- **Depends on sprints:** `SPRINT-087` (`US-02-T02`'s save-time resolution) and
  `SPRINT-088` (`US-03-T02`'s call gate and `US-03-T03`'s dispatch) — all three
  required by `T05` alone. `/implement-sprint` refuses this sprint until **both**
  are `Done` (hard rule 9).
- **`T01`–`T04` carry no cross-story dependency at all.** If the upstream
  sprints slip and the human wants value sooner, the honest option is to re-cut
  this story — not to start the sprint early; `T05` is the only task that needs
  them. Raise it as a re-plan rather than building out of order.
- **No dependency either way with `SPRINT-089`.**
- **Story-level gate carried forward (`gate: flagged`, not resolved by this
  sprint):** `REQ-SB-95-US-05` is flagged under trigger 3 (`ADR-037` — the
  tag-keyed index as a projection rebound inside `VaultManager.rebuild_index()`
  rather than a new Index artifact with its own cron job, a plugin registering a
  namespace as a callable, and the single `FRAMEWORK_API` bump) and under
  trigger 7 (the bump gap above — **structurally closed by this sprint's
  ordering**, see Grouping Rationale). `ESC-063` (who owns Customer/Partner
  entity knowledge across the `ADR-022` boundary) is **Resolved**: the resolver
  is framework, Customer stays the plugin (`ADR-035`). See `REVIEW-QUEUE.md`.
- **`ADR-032`'s own recorded consequence applies:** the answer depends on the
  Entities registry being current, and discovery was once paused for 41 days
  before anyone noticed. The freshness surface proposed under `BUG-085` is
  related, separate work and is not in this sprint.

---

## Out of Scope

- The Action catalogue (`SPRINT-087`), enforcement at the call (`SPRINT-088`),
  Workflows (`SPRINT-089`), the Operator Profile (`SPRINT-086`).
- Replacing the existing per-entity Index artifacts — `ADR-032` keeps them
  available for accounts that deserve a custom scope.
- The pipeline-freshness surface (`BUG-085`).

---

## Definition of Done

- [x] Every story in scope has status `Done`
- [x] All story-level Definitions of Done satisfied
- [x] `BACKLOG.md` updated — every affected row reflects current status
- [x] `architecture.md` updated if the sprint changed an architectural fact — no change owed: the sprint built exactly what **§The One Tag-Keyed Index** and **§The Action Call Gate** already describe, and `ADR-032`/`ADR-037` already carry the decisions
- [x] Any new ADRs recorded in `ADR.md` with status `Accepted` — none created; `ADR-037` was accepted before the sprint began
- [~] `MEMORY.md` updated with any new decisions / patterns / constraints — **not appended by any of the five tasks**: 86 KB against the 40 KB budget its own rule 1 sets, which forbids appending while over. All of them are verbatim in `REVIEW-QUEUE.md`. See the retro — this is the fourth consecutive sprint to record it
- [x] `CHANGELOG.md` entry appended
- [x] Retrospective section below filled in
- [ ] **Human:** patterns and learnings from the retrospective propagated to `Implementation/Learnings.md` (the coder drafts the retro and gates it; the human harvests it)

---

## Notes

**Started 2026-10-18 (`Ready → In Progress`).** Both `depends_on_sprints` edges
were confirmed `Done` first (`SPRINT-087`, `SPRINT-088`), so hard rule 9 is
satisfied. **`T01` is Done 2026-10-18** — the one tag-keyed index, as a
projection: a module-level `_vault_tag_index` in
`app/business/core/vault/vault_manager.py`, built from the same `new_entries`
and rebound one statement after `_vault_entries` inside `rebuild_index()`, read
through `get_entries_for_tag()` and `get_tag_index_keys()`. Keys are every
`<namespace>/<slug>` tag the vault actually holds, registered or not; the one
stated tag-shape rule keeps a deeper tag (`a/b/c`) under its own full name and
excludes a tag with no namespace at all, which `list_tags()` still counts.
`AC-04` and `AC-07` both verified on 8 AC-tagged tests plus two assertions read
off the module's own syntax tree — exactly one rebind site, in `rebuild_index`,
immediately beside `_vault_entries`; and **no string literal containing a
separator anywhere in the builder**, so no namespace allow-list or deny-list
exists for it to consult. No `Index` artifact and no cron job: both are spied on
for every test in the file and neither fired. Windows `MAX_PATH` pinned by
measurement rather than assumed — a 308-character note on which plain
`os.path.isfile()` answers **False** with no error is still found by the real
walk and still grouped under its tag. Backend suite 677 → **687 passed**, the
same 9 scratch-install failures before and after, run from a scratch CWD with
scratch `VAULT_PATH`/`SECOND_BRAIN_DATA_PATH` so the operator's vault and store
were unreachable throughout. Task `gate: flagged` for three judgement calls
(chiefly that the manual step ran against a synthetic vault over the real HTTP
surface, not the operator's real vault), nothing blocked, no `ESCALATIONS.md`
entry. **`T02` is the other independent root and is next; `T03` follows both.**

**Coder, 2026-10-18 — `T02` Blocked (`ESC-079`); the sprint stays `In Progress`.**
The registration seam is built, tested and committed: `register_tag_namespace`
stores the plugin's `entries` callable and never asks it at registration,
`PluginManager` keys the registrations by prefix with the owning `plugin_id` and
refuses a second plugin's claim naming both, and `get_tag_namespaces()` is the
accessor `T03` will read. `kind` is byte-identical pass-through; registration is
proved **non-filtering** against `T01`'s `AC-07` (the index builder's module
imports nothing from the plugin host, so it cannot consult a registry at all).
18 AC-tagged tests; suite 595 → 618 passed with the non-passing set identical
before and after (115 ids, all pre-existing against an empty scratch install).

What is blocked is one line: `AC-08`'s `FRAMEWORK_API` clause. The sprint
ordering did what it was designed to do — `register_action` is present, so the
conditional read fired here — but the move is **11 → 12** rather than the 7 → 8
`ADR-037` and both task files state (four versions stale before the sprint
began), `REVIEW-QUEUE.md` still carries choosing the sitting as the operator's
open decision, and the bump is live on save against a running backend while the
republish of every installed plugin lives in `src/marketplace/`, outside any
task's scope and mid-flight in another session. It is owed, noted at the
constant, and pinned by a test that fails if anyone bumps twice. **`T03` is
unblocked in code and is next**; `T04` and `T05` follow.

**Coder, 2026-10-18 — `T03` Done; the sprint stays `In Progress`.** The generic
resolver (`app/business/logic/tag_resolution.py`) turns a name, an alias or an
email domain into `(kind, tag, hub)` by asking `T02`'s registered namespaces at
the moment of the question, and reports ambiguity and non-resolution rather
than guessing. `AC-01`, `AC-03`, `AC-05` and `AC-07` are verified by 18
AC-tagged tests; the suite moved 724 → 742 passed with the same 9 pre-existing
scratch-install failures. The CFO test was observed live against a real backend
on a scratch install: the server returns four search hits for a name the vault
really holds, and the resolver — no plugin installed — still answers "did not
resolve". `T02`'s `ESC-079` did **not** block it: the `FRAMEWORK_API` gate
governs only whether a *plugin* may declare the capability, and no file outside
`T03`'s own two was touched. **`T04` (the scoped read) is next**, then `T05`.

**Coder, 2026-10-19 — `T04` Done; the sprint stays `In Progress`.** The scoped
read (`app/business/logic/scoped_entity_read.py`) answers "what is known about
this entity" from that entity's own tag alone: the hub's synthesis first, then
its tagged evidence newest first by each note kind's own real recency field, and
nothing from anywhere else. It is a **sibling** of `tag_resolution.py` rather
than an extension of it, so that module's file-wide tripwires — it reads no
note, searches nothing, performs no scoped read — stay intact and keep earning
`T03`'s central claim mechanically. `AC-02` is verified by 15 AC-tagged tests;
the suite moved 742 → **757 passed** with the same 9 pre-existing
scratch-install failures, compared id by id. The three things the story exists
to guarantee are each enforced rather than inspected: all three vault search
entry points are counters asserted zero for **every** test in the file including
the entity-with-no-evidence path; `get_entries()` and `get_index()` are both
armed to fail after the index is built and the read still succeeds, so the
tag-keyed projection is provably the only door; and the undated-note fallback is
asserted as a relation over the sort key and re-asserted by re-indexing the same
vault in reverse walk order. Four in-memory mutations were run to confirm the
tests fail when the behaviour is removed. `gate: flagged` for six judgement
calls, nothing blocked, no `ESCALATIONS.md` entry. The manual step's real-vault
half was **not performed and is disclosed as a gap**: `register_tag_namespace`
is called by nothing in this checkout outside `plugin_api.py` and three test
files, so no install has a registered namespace, and creating one would have
meant writing a plugin into the operator's live store and reading their real
notes. **`T05` is the last task in the sprint** — the scoped read as a shipped,
catalogued Action reached through the call gate. The sprint does not close until
it lands, and `T02` remains `Blocked` on `ESC-079` (the single `FRAMEWORK_API`
move), which `T04` neither touched nor needed.

**Coder, 2026-10-21 — `T05` Done, the story Done, the sprint `Done`.** The last
task shipped the scoped read as a catalogued Action: one new folder,
`app/business/core/actions/starters/read-entity-updates/Action.json`, whose
single `http` implementation names `GET /vault-search/entity-read` (the route
committed in `420dd6c`). No new shipping mechanism — the boot already seeds
whatever sits in that directory. `ESC-080`'s authorisation was used exactly as
scoped: the three `[REQ-SB-95-US-03-AC-05]` assertions that pinned the shipped
set as a one-element literal became membership checks, and each still proves
what it did (idempotent seeding, the operator's edited copy kept, a shipped
definition really loading). `AC-06` verified on 14 AC-tagged tests and live
against a disposable backend on `127.0.0.1:8099`: the starter was really seeded
at boot and served from `GET /actions` with `status: "resolves"`, and all three
refusals plus the `allowed_callers` refusal were observed with their ledger
files on disk. Suite **778 passed / 2 failed of 780, unchanged before and
after**; the two read a real Hermes install the isolation deliberately removes.

**One new thing came out of finishing it, and it is not this story's.** The
accepted call did not come back with the scoped answer: it came back
`outcome: failed`, `HTTP 401`, because `REQ-SB-101`'s default-deny middleware
refuses the gate's own in-process dispatch sub-request. **Every** `http`
implementation is affected on any install with an account. Raised as `ESC-081`
with three candidate fixes written out; the task is `Done` because `AC-06`'s
Gherkin is about the gate and all of it passed, and the fix belongs to files in
two other `Done` tasks. The sharp part is in the escalation: the suite's autouse
sign-in fixture authenticates the dispatcher's own sub-request too, so 14 green
tests cover behaviour that cannot happen in production.

**gate: clear 2026-10-16 — no product-owner trigger fired.** No assumption (the
single inbound edge is quoted from `US-05-T05`'s own frontmatter); requirement
finalised; no ADR created or changed by this pass; no `ESCALATIONS.md` entry;
**not oversized** (5 tasks); **no `Blocked` story**. On trigger 5's cross-sprint
clause: the two `depends_on_sprints` edges are the decomposer's own `T05` edges
expressed at sprint level, not dependencies this pass introduced — recording
them is what hard rule 7 prescribes, and the repo precedent for a recorded edge
at `gate: clear` is `SPRINT-080`/`083`/`084`. No contradictory inputs. On
trigger 8: this sprint's own story is unambiguous, and the free
`SPRINT-089`/`SPRINT-090` build order is a non-decision (no edge either way,
both legal, stated in both files). The story's upstream `ADR-037` flag is carried
forward; its trigger-7 half is structurally closed by this sprint's ordering and
the `REVIEW-QUEUE.md` item is marked resolved on that basis.

---

## Retrospective

<!-- Filled in by the CODER when status: Done. The coder drafts this section and
sets gate: flagged. The HUMAN then skims it, approves, and copies anything under
"Patterns to carry forward" and "Antipatterns to avoid" verbatim (or expanded)
into Implementation/Learnings.md — that is the cross-sprint index future sprints
read. The retro here is a sprint-level snapshot; Learnings.md is the permanent
record. The coder does NOT write Learnings.md directly. -->

### Sizing accuracy

- **Estimated:** ~5 tasks, `M` — **Actual:** 5 tasks, none split, dropped or
  merged; `M` on code volume — **Takeaway:** the task count was exact and the
  effort estimate was right about the *code*. It was wrong about the
  **calendar**: 2026-10-18 → 2026-10-21, with two tasks parked `Blocked`
  (`T02` on `ESC-079`, `T05` on `ESC-080`) and two human round trips. Both
  escalations were authorised essentially as written, so neither was wasted —
  but neither was predictable from "5 tasks, M" either. The rationale
  correctly called `T05` "a four-way integration task whose verification needs
  the real catalogue and the real call gate from two earlier sprints"; what it
  did not price is that a task touching two earlier sprints' artefacts is also
  a task likely to need permission to touch those sprints' *tests*. On the
  evidence of `SPRINT-089` (4 of 7 tasks escalated) and this one (2 of 5),
  **a sizing estimate should carry an escalation-likelihood note alongside the
  task count whenever a story extends an existing family.**

### What worked

- **Shipping a starter really was one folder.** `T05` added a directory with an
  `Action.json` in it and nothing else: no registry entry, no import, no line in
  `main.py`. `REQ-SB-95-US-03-T05` built the mechanism as a directory scan plus
  a boot-time seed, and the second starter cost nothing to add because of it.
  That is the shape to copy — the only thing a new member of a shipped family
  should cost is the member.
- **Keeping `kind` opaque end to end held under pressure at the last step.**
  `T01` proved it by syntax tree (no separator-bearing literal anywhere in the
  index builder), `T03` by the module's own source, and `T05` by asserting the
  shipped Action's **whole JSON text** against a list of forbidden words. The
  Action definition is the one artefact an agent reads; it would have been the
  easy place to leak "Customer" as a helpful example and undo all of it. The
  check is mechanical, over the real shipped bytes, and costs four lines.
- **The disposable-backend-on-a-spare-port habit, now used by four of five
  tasks in this sprint.** `T03` found its CFO case on `:8097`, `T05` on
  `:8099`. It is what surfaced `ESC-081`, which no amount of additional unit
  testing would have found — because the suite's own fixture is what hides it.
- **Measuring the blast radius before escalating, both times.** `T02` and `T05`
  each reported an exact number (`3 failed, 9 passed`) with the ids, not a
  prediction. Both authorisations came back within one round trip and matched
  the measurement. An escalation that says "this will probably break things" is
  a question; one that says "these three tests, these three lines" is a
  decision.
- **Reading the predecessor's commit before rebuilding anything.** `T05` was
  finished by a second session. Everything it needed — the route, 14 tests, the
  exact bytes of the held-back file — was already in `420dd6c` and in the
  escalation, and the second session's first act was `git show`. Nothing was
  re-derived and nothing was duplicated.

### What didn't work

- **A session was killed mid-write-up, and the cost was three days of apparent
  blockage on work that was finished.** `T05`'s code, tests and live
  verification were all complete and committed on 2026-10-19. What was missing
  was the `## Implementation Log`, which never got written — so the task read
  `Blocked`, the story read `In Progress`, and the sprint stayed open until a
  second session picked it up on 2026-10-21. The commit message and the
  escalation carried enough to reconstruct it (which is itself the saving
  grace), but the pipeline's own status fields said something different from
  what was true. **Write-up is not the last 5% of a task; it is the part the
  next session reads.** Worth considering whether the log should be appended
  incrementally as each verification step passes, rather than composed at the
  end.
- **Three escalations of one family in four days, spanning two sprints.**
  `ESC-078` (`SPRINT-089`), `ESC-079` and `ESC-080` (this sprint) are each "my
  task adds a member to a family, and something hand-maintained enumerates that
  family": an exhaustive union and its maps, a version constant nobody's scope
  owned, a test asserting the shipped set equals a one-element list. `ESC-077`
  had already recorded the lesson and put a rule in
  `.claude/agents/decomposer.md` — and it did not prevent `ESC-080`, because a
  decomposer rule governs the file lists written *from now on* and does nothing
  about literals already sitting in tests. Each one costs a `Blocked` task and a
  human round trip.
- **`MEMORY.md` is 86 KB against the 40 KB budget its own rule 1 sets, and rule
  1 forbids appending while over — so this sprint filed none of its
  constraints either.** Every one of the five tasks parked a candidate in
  `REVIEW-QUEUE.md` instead; thirteen tasks in six days have now done so. **This
  is blocked delivery work, not housekeeping**, and it is the fourth
  consecutive retro to say it. The failure mode is concrete and already
  happening: an agent reads `MEMORY.md` before changing this codebase and reads
  `REVIEW-QUEUE.md` never, so each diverted rule is a rule that will be
  rediscovered by breaking something. `ESC-081` is a live example of exactly the
  class of constraint being lost.
- **The backend suite is more permissive than production, and it hid a
  product-breaking regression for two days.** `tests/conftest.py`'s autouse
  `every_request_is_signed_in_as_an_admin` patches the single seam both the
  middleware and the dependency read — including for the app's own in-process
  dispatch sub-request. So `http` Action dispatch is authenticated under pytest
  and anonymous on a real install, and 14 AC-tagged tests pass against behaviour
  that cannot happen. The fixture was the right call when it was written (106
  tests turned 401 overnight) and its docstring is honest about what it does;
  what is missing is any test that runs *with the guard on*.
- **Two manual steps in this sprint could not be performed as written**, both
  disclosed rather than quietly skipped: `T04`'s real-vault half (nothing in
  this checkout registers a namespace, so no install has one) and `T05`'s
  real-agent half (the shipped runner Skill sends no credential, so
  post-`REQ-SB-101` it is refused at the door). A manual step that assumes an
  installed plugin or a live agent is a step this repository cannot run alone.

### Patterns to carry forward

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **Ship a new family member as data in a directory, not as a registration** —
  when the framework ships a set (Master Templates, starter Actions), make the
  reader a directory scan and the installer a boot-time seed that never
  overwrites. Adding the second member then costs exactly one folder: no import,
  no registry line, no `main.py` edit, and no task's scope has to reach into
  shared code to switch it on.
- **Assert membership in a live set, never equality with a hand-written list** —
  in any test over a family that will grow (shipped starters, artifact kinds,
  registered managers). `x in live_set()` proves everything `live_set() == [x]`
  proves except "and nothing else exists", which is almost never the thing under
  test and is always the thing that breaks the next author. Put the reason in
  the assertion's own failure message so the next reader does not re-tighten it.
- **One source of text for a shipped definition** — when a test verifies bytes
  that also ship, read them from the shipped file rather than restating them as
  a literal. Two copies of a definition drift and nothing notices. Where the
  test needs isolation from the *rest* of the shipped set, copy the real bytes
  into a `tmp_path` directory and point the reader there — real content,
  controlled set.
- **Verify a shipped artefact by booting it, not by parsing it** — "the file is
  valid JSON" is a weak claim. "A disposable backend on a spare port seeded it
  at boot and `GET /actions` returns it with `status: resolves`" exercises the
  directory scan, the seed, the parser, the save-time resolution and the route
  table in one observation, and it is the only thing that proves the route is
  really mounted.
- **Forbid a vocabulary mechanically, over the whole artefact's text** — for any
  framework artefact an agent reads, assert that its serialised form contains
  none of the business words the framework must not know. Prose discipline in
  review does not survive; a four-line loop over `json.dumps(...).casefold()`
  does.
- **Measure the blast radius before escalating** — run the change, record the
  exact failing ids and counts, revert, then escalate with the measurement. It
  turns a question into a decision and it is why both of this sprint's
  escalations were authorised in one round trip.
- **Read the predecessor's commit before touching anything, on any resumed
  task** — `git show <sha>` first. A killed session usually leaves far more
  finished than its status fields suggest, and the commit message plus the
  escalation entry are where it is.

### Antipatterns to avoid

<!-- Copy these into Implementation/Learnings.md after human review. -->

- **A test fixture that makes the suite more permissive than production** — a
  blanket autouse fixture that authenticates, enables or permits *everything*
  will also cover paths nobody meant it to cover, and every test over those
  paths becomes evidence for a claim that is false on a real install. Here it
  signed in the app's own internal dispatch and hid a total failure of `http`
  Action dispatch behind 14 green tests. If a fixture must relax a global guard,
  leave at least one test running with the guard on.
- **Adding authentication to an app that re-enters itself, without naming every
  internal re-entry point in the same change** — the app's own in-process
  dispatch is a real request through the real middleware stack; making the app
  default-deny makes the app unable to call itself. `ESC-081`.
- **Recording a rule only where the rule was broken** — `ESCALATIONS.md` is a
  log of what happened and nobody opens it while writing code. `ESC-077` wrote
  this family's lesson in full and `ESC-080` happened anyway, one sprint later.
  A rule has to land where it is read: `MEMORY.md`, or the agent prompt that
  governs the act.
- **Treating `MEMORY.md` compaction as housekeeping** — it is a blocked
  dependency of every task that produces a constraint, and thirteen tasks have
  now queued behind it. Diverting a rule to `REVIEW-QUEUE.md` is not recording
  it; it is deferring its rediscovery to whoever next breaks something.
- **Composing the implementation log at the end** — a session that dies between
  "verified" and "written up" leaves finished work looking blocked, and the next
  session pays the reconstruction cost. Record each AC's observed outcome as it
  passes.
- **Writing a manual verification step that needs something this repository
  cannot produce** — an installed plugin, a registered namespace, a live agent.
  Two of this sprint's five manual steps were unperformable as written. Either
  name the synthetic stand-in in the step itself, or accept at decomposition
  time that the step is a disclosure rather than a check.

### Open follow-ups

- **`ESC-081` (Open)** — `REQ-SB-101`'s guard refuses the Action gate's own
  in-process dispatch; every `http` implementation answers "the operation did
  NOT happen" on a signed-in install. Three candidate fixes written out in the
  escalation; it is a `REQ-SB-101` × `REQ-SB-95` boundary and needs a decision
  before it can be specced. Filed in `ESCALATIONS.md` + `REVIEW-QUEUE.md`.
- **The shipped runner Skill sends no credential** — same root cause as
  `ESC-081`, and the reason a real Hermes agent cannot reach the gate at all.
  Must be answered by whatever resolves `ESC-081`.
- **`MEMORY.md` compaction pass** — thirteen parked constraints, four
  consecutive retros. In `REVIEW-QUEUE.md`.
- **`starters/README.md` documents why each starter ships and now covers one of
  two.** `T05` left it alone deliberately (it belongs to a `Done` task and the
  `ESC-080` authorisation was explicit about scope). One line, for whoever next
  has that file in scope.
- **The `FRAMEWORK_API` republish correction from `T02`** — all five plugins
  live in their own `sb-plugins-*` repositories and are republished from there,
  not from `src/marketplace/`, which is a publish target that is never
  hand-edited. Recorded in `T02`'s own file; worth being true in anyone's head
  before the next bump.
