---
id: REQ-SB-64-US-01
title: Section Hub as KB Traffic Gateway — a Section's own Hub mediates its pipelines'/agents' KB-bound placement requests before they reach REQ-SB-63's Librarian
requirement_ids: [REQ-SB-64]
requirement_section: "REQ-SB-64: Section Hub as KB Traffic Gateway — Every Pipeline/Agent Write Routes Through Its Section's Manager"
phase: P1
status: Draft
gate: flagged
gate_reason: "trigger-8 (genuinely unclear / multiple equally-valid scope interpretations) AND trigger-1 (material scope-narrowing assumption made to keep this story buildable) — two real open questions the PRD's own text explicitly leaves for /spec: (1) whether this retrofits REQ-SB-55's already-shipped Consult-Librarian call site or only applies going forward, and (2) the exact mechanical shape of Hub-mediation (a plain synchronous call vs. a decorator/interceptor). This pass proposes a leaning candidate for both, with reasoning, but does not resolve either — no operator confirmation was available during this /spec pass (contrast REQ-SB-63-US-01, where the retrofit question WAS resolved live, in-session, by the operator). This pass also narrows the PRD's own broad 'every agent/pipeline KB read+write' framing down to the one concrete, operator-named write path (Email Capture Pipeline's existing Librarian-consult call) — a real, disclosed scope-narrowing decision, not something the PRD itself stated this precisely. See ## Notes. A REVIEW-QUEUE.md entry has been added."
sprint: ""
created: 2026-08-16
updated: 2026-08-16
---

# REQ-SB-64-US-01 — Section Hub as KB Traffic Gateway — a Section's own Hub mediates its pipelines'/agents' KB-bound placement requests before they reach REQ-SB-63's Librarian

## Story

**As a** Second Brain user
**I want** each Section's own Hub to sit between its pipelines'/agents' KB-
bound placement requests and REQ-SB-63's Librarian — a real gateway, not
just today's cross-Section HELP router — so a pipeline never reaches the
Librarian (or the vault) directly, bypassing its own Section's manager
**So that** the KB stays organized the way the operator described it: a
Section's own Hub always knows what traffic is moving through its Section,
while the Librarian stays the one shared authority that decides WHERE
content actually belongs

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-64: Section Hub as KB Traffic
  Gateway — Every Pipeline/Agent Write Routes Through Its Section's
  Manager*.
- **Extends `REQ-SB-20`'s already-shipped Hub concept — confirmed by
  direct reading of the real, current code, not assumed:**
  `graph.py::_route_hub_request` (`app/business/agent_orchestration/
  graph.py`) is a LangGraph node bound to `AgentConversationState` — it
  fires only when a chat-originated agent tool-calls
  `request_cross_section_help`, and its job is purely cross-Section
  agent-to-agent HELP routing (own-Hub-then-target-Hub two-hop relay,
  `REQ-SB-20-US-01`, `Done`). It does **not** today mediate any
  pipeline's or agent's own KB reads/writes — every one of the 29
  business-layer modules that import `vault_writer` (confirmed by direct
  grep this pass) calls it, or `vault_filing_expert.
  determine_placement_and_file`, directly. `ADR-041` point 2 already
  defines Hub as "both a MANAGER... AND a DATABASE" — this requirement is
  the first time that DATABASE/gateway half is actually built, not a new
  architectural concept (operator's own framing, PRD `<!-- -->`).
- **The Librarian half is separately real and Done.** `REQ-SB-63-US-01`
  (`Done`, `SPRINT-050`) generalized `vault_filing_expert.
  determine_placement_and_file` into the one shared placement authority
  every KB-shaping decision consults. Confirmed live today: `email_
  classification.py::consult_librarian` (the `Consult-Librarian` branch
  Job wired into `REQ-SB-55`'s already-shipped Thread pipeline) calls
  `determine_placement_and_file` **directly** — Job → Librarian, with no
  Hub in between. This is the exact gap this requirement closes: Hub =
  per-Section traffic gateway; Librarian = the shared placement brain a
  Hub calls into — not competing designs (PRD's own framing).
- **Concrete worked example, confirmed directly by the operator, and the
  reference call chain the PRD itself says `/spec` should design
  against:** "The [Email Capture] Pipeline in Data Gathering [Section] is
  connected to the Data Gathering Hub, which sends it to the Librarian
  for filing." `REQ-SB-55` (Email Capture & Threading Pipeline, `Done`,
  `SPRINT-049`) is assigned to a real, operator-created `data-gathering`
  Section (created directly by the operator this session, alongside
  `Customers`/`Sales`/`Productivity`/`Technology`) — `email-capture-
  pipeline` and `meeting-capture` are both assigned to it via `section_
  registry.list_sections()`'s real, persisted runtime state (not visible
  in this repo's own code-level `_STARTING_SECTION_NAMES` seed list or
  any committed JSON, since `.second-brain/` state is runtime/user data,
  not checked into git — consistent with `ADR-014`'s own "parallel
  persisted store" design). This story takes that operator-confirmed
  runtime fact as given, not something to re-derive from the repo.
- **Two open scope questions the PRD's own text explicitly leaves for
  `/spec`, not assumed here (see `## Notes` for full reasoning and
  candidate answers):**
  1. **Retrofit scope** — does this route `REQ-SB-55`'s already-shipped
     `consult_librarian` call site through the Hub retroactively, or does
     it only apply going forward to whatever pipeline comes after? This
     codebase has an established "no retrofit, replace with pipeline"
     precedent (`REQ-SB-63-US-01`'s own resolved retrofit question,
     `REQ-SB-55-US-01`'s own Scenario 6 regression guard protecting
     `REQ-SB-08`/`09`/`10`'s OLD, pre-redesign pipelines) — but `REQ-SB-55`
     is itself a NEW pipeline built under this same KB redesign, not one
     of those old ones, so that precedent's applicability here is a
     genuinely different, real question, not a foregone conclusion.
  2. **Mechanical shape** — a real synchronous call every write passes
     through? A decorator/interceptor pattern? Something else? And
     explicitly OUT of scope for this pass: what "extra data" a Hub might
     add to passing traffic — the operator named that as a possible
     FUTURE addition only ("maybe in future it will add some extra
     data"), not a resolved current one.
- **Scope-narrowing decision this pass makes, disclosed, not silently
  assumed:** the PRD's own body text reads broadly — "Every Section gets
  a real Hub that its own agents' and pipelines' KB reads/writes route
  through, rather than each agent calling `vault_writer.py` directly as
  they all do today." Taken completely literally, that is a from-scratch
  migration of all 29 existing `vault_writer`-calling business modules —
  an epic, not one story (mirroring `ADR-041`'s own "Scope is large
  enough to likely need its own multi-story epic" framing for a
  comparably broad taxonomy rollout). This story instead narrows to the
  one concrete, operator-named write path — the Email Capture Pipeline's
  existing `consult_librarian` → Librarian placement/hub-linking/cross-
  cutting-check call — mirroring this project's own repeatedly-applied
  "build/prove one real, concrete thing before generalizing" precedent
  (`ADR-041`'s own Builder-after-real-Pipeline sequencing; `REQ-SB-63-
  US-01`'s own deliberately narrow, concrete Acceptance Criteria despite
  a comparably broad PRD framing). The Thread-Match/Merge Job's own
  separate, direct `vault_writer` write of the Thread note itself (not a
  Librarian-consult call) is explicitly NOT in scope here — see
  `## Non-Goals`.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: The Email Capture Pipeline's Librarian-consult routes through the Data Gathering Hub, not directly to the Librarian

```gherkin
Given the Email Capture Pipeline (agent id "email-capture-pipeline",
    Section "Data Gathering" per section_registry.get_agent_section)
    reaches its existing Consult-Librarian step for an already-filed
    Thread — mirroring the ALREADY-SHIPPED consult_librarian ->
    determine_placement_and_file call
When that step's placement/hub-linking/cross-cutting-check request fires
Then the request is routed through the Data Gathering Section's own Hub
    before it reaches REQ-SB-63's Librarian — Job -> Hub -> Librarian, not
    Job -> Librarian directly
  And the Librarian's returned decision (Tier 1 write/link, Tier 2
    proposal, or a cross-cutting-update proposal) is applied exactly as
    it is today, unchanged by being reached via the Hub
```

### Scenario 2: A Hub forwards a placement request to the Librarian without deciding placement itself

```gherkin
Given any Section's own Hub receives a KB-bound placement request from
    one of its own pipeline Jobs or agents
When the Hub processes that request
Then the Hub itself makes no placement/tag/location decision — it
    forwards the request to REQ-SB-63's Librarian, the one shared
    authority that knows the whole KB (every Section, every tag, every
    storage location)
  And the Hub returns the Librarian's decision back to the requesting Job
    unchanged
```

### Scenario 3: A Job or agent only ever reaches its OWN Section's Hub for a KB-bound write

```gherkin
Given a pipeline Job or agent belongs to a specific Section (per
    section_registry.get_agent_section)
When that Job/agent has a KB-bound placement request ready
Then it routes through its OWN Section's Hub — never a different
    Section's Hub, and never bypassing its own Hub to call the Librarian
    directly for that request
```

### Scenario 4: The already-shipped cross-Section HELP routing is unchanged by this generalization

```gherkin
Given an agent's existing chat-originated cross-Section HELP request
    (graph.py::_route_hub_request, REQ-SB-20-US-01, Done)
When this story ships
Then that already-proven routing behavior is unchanged — this story adds
    a NEW KB-write-mediation responsibility onto each Hub, it does not
    alter, replace, or duplicate the already-shipped cross-Section HELP
    mechanism
```

### Scenario 5: A Librarian Provider-unavailable result is honestly relayed through the Hub, never fabricated or swallowed

```gherkin
Given the Librarian returns its own already-proven honest {"status":
    "unavailable", ...} result (its configured model Provider is
    unavailable)
When that result is returned through the Hub back to the requesting Job
Then the Job receives that SAME honest, unmodified result — the Hub
    relays it verbatim, never fabricating a placement and never silently
    swallowing the unavailable signal
  And the Pipeline's own terminal step for that item still completes to
    a clean, ordinary end, unchanged from today's already-proven behavior
```

### Scenario 6: This story does not extend Hub-mediation to every other direct vault_writer call in the codebase

```gherkin
Given the other existing business-layer modules that call vault_writer.py
    directly today (outside the one concrete Email Capture -> Librarian
    consult call site above) — including the Thread-Match/Merge Job's
    own direct write of the Thread note itself, and REQ-SB-08/09/10's
    already-Done capture pipelines
When this story ships
Then none of those other direct vault_writer or direct Librarian-consult
    call sites are modified, wrapped, or routed through a Hub by this
    story — the PRD's own broader "every agent/pipeline KB read/write"
    framing is narrowed here to the one concrete, operator-named example
    this story proves the mechanism against (see Non-Goals); extending
    Hub-mediation further is future requirement work, not this story's
    scope
```

## Affected Screens

None — backend only. `html-prototype/agents-map.html` already visually
represents each Section's Hub node; this story changes internal routing
behavior only, with no new visual state, no new screen region, and no
change to how a Hub renders. See `## Notes` for the prototype-parity
line.

## Dependencies

- **Blocked by:** none — both preconditions the PRD itself names
  (`REQ-SB-55-US-01`, `Done`, `SPRINT-049`; `REQ-SB-63-US-01`, `Done`,
  `SPRINT-050`) have already shipped, satisfying the PRD's own explicit
  "Do not `/spec` until both `SPRINT-049` and `SPRINT-050` are `Done`"
  gate.
- **Related to:** `REQ-SB-20-US-01` (Section Hub Intelligence &
  Cross-Section Routing, `Done`) — the already-shipped Hub concept/
  `_route_hub_request` this story extends with a new responsibility,
  never replaces.
- **Related to:** `REQ-SB-63-US-01` (The Librarian, `Done`) — the shared
  placement authority a Hub forwards requests to; this story never
  duplicates or bypasses its Tier 1/Tier 2/cross-cutting-update logic.
- **Related to:** `REQ-SB-55-US-01` (Email Capture & Threading Pipeline,
  `Done`) — the one concrete pipeline/call site (`consult_librarian`)
  this story's minimum acceptance bar targets; whether this is a retrofit
  of that already-shipped call site or a forward-only design is the
  open question in `## Notes`.
- **Related to:** `REQ-SB-56-US-01`/`REQ-SB-57-US-01`/`REQ-SB-58-US-01`
  (all `Draft`) — none of these pipelines has its own Librarian-consult
  call site yet (`REQ-SB-63-US-01`'s own Non-Goals already established
  this); wiring THEIR future consult calls through their own Hub is each
  of those stories' own future addition, not this story's scope.
- **External:** none beyond the already-live Hub-routing and Librarian-
  consult mechanisms this story extends.

## Constraints

- **A Hub never itself decides placement/tag/location** — it always
  forwards to the Librarian, the one shared authority (PRD's own explicit
  framing); no parallel, Hub-local placement logic is ever built.
- **The already-shipped cross-Section HELP routing
  (`graph.py::_route_hub_request`) must remain unbroken and unchanged** —
  this story is additive, never a replacement.
- **No "extra data" enrichment is added to traffic passing through a Hub
  by this story** — explicitly future, operator-named-but-unresolved
  scope only (see Non-Goals).
- **This story's scope is bounded to the one concrete `REQ-SB-55`
  Consult-Librarian call site** — no blanket migration of the other
  direct `vault_writer`-calling business modules is attempted here.
- **The exact mechanical shape of Hub-mediation is NOT built until the
  operator confirms it** (see Notes) — do not silently pick sync-call vs.
  decorator/interceptor at `/plan-tasks` without the human review this
  story's `gate: flagged` calls for.
- **Section membership is resolved via `section_registry.py`'s real,
  persisted state** (`get_agent_section`) — never hardcoded per pipeline.
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Analyst-authored starting point, non-authoritative — the decomposer's
own table at /plan-tasks supersedes this. Task count/shape is intentionally
provisional until the architect resolves the mechanical-shape open question
(## Notes) and the operator confirms the retrofit-scope open question. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-64-US-01-T01 | backend | New per-Section Hub gateway function (composed alongside `section_registry.py`, mirroring its "compose alongside, don't reopen" convention) that forwards a placement request to `vault_filing_expert.determine_placement_and_file`, returning its result unchanged | `app/business/section_registry.py` or a new sibling module (architect to decide) | `../Tasks/REQ-SB-64-US-01-T01-section-hub-gateway.md` |
| REQ-SB-64-US-01-T02 | backend | Route the Email Capture Pipeline's `consult_librarian` call through the Data Gathering Hub instead of calling `determine_placement_and_file` directly — retrofit-vs-forward-only scope per operator confirmation (see Notes) | `app/business/email_classification.py` | `../Tasks/REQ-SB-64-US-01-T02-thread-pipeline-hub-routing.md` |

## Definition of Done

- [ ] Both open scope questions (retrofit scope; mechanical shape) have
      been confirmed by the operator and recorded in this story's
      `## Notes`
- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Migrating all 29 existing `vault_writer`-calling business modules onto
  Hub-mediated routing** — the PRD's own broad "every agent/pipeline KB
  read/write" framing, taken completely literally, is an epic-sized
  migration; this story narrows to the one concrete, operator-named
  Email Capture -> Librarian call site and proves the mechanism there
  first, mirroring this project's own repeated "one real thing before
  generalizing" precedent.
- **The Thread-Match/Merge Job's own direct `vault_writer` write of the
  Thread note itself** — a separate write path from the Librarian-consult
  call this story targets; not touched here.
- **Retrofitting or bridging `REQ-SB-08`/`09`/`10`'s current
  classification modules** — already explicitly out of scope per
  `REQ-SB-63-US-01`'s own resolved decision ("no Retrofit... replace it
  with pipeline"); unchanged and unaffected by this story either.
- **Wiring an equivalent Hub-mediated Librarian consult into
  `REQ-SB-56`/`57`/`58`'s own pipeline Jobs** — none of those pipelines
  has a Librarian-consult call site yet; each of those stories' own
  future addition, not this one's.
- **KB-bound READS routed through a Hub** — the PRD's body text mentions
  "reads/writes," but the operator's own concrete worked example and this
  story's minimum acceptance bar are both about a WRITE/filing decision;
  read-path Hub-mediation is not designed or built here.
- **Any "extra data" a Hub might enrich passing traffic with** — the
  operator named this as a possible FUTURE addition only ("maybe in
  future it will add some extra data"), not a resolved current one; not
  designed here.
- **The exact mechanical shape of Hub-mediation** (sync call vs.
  decorator/interceptor) — a candidate is proposed in `## Notes` but
  genuinely open, flagged for operator confirmation before `/plan-tasks`
  locks a design in.
- **The Pipeline Builder / DAG UI** (`ADR-041` points 5–6) — unrelated,
  separately deferred work.

## Notes

**Open scope question #1 (retrofit scope) — genuinely open, NOT resolved
by this pass (part of why `gate: flagged`):**

Both readings are real and buildable:

- **Option A — retrofit, as an additive wrap around the already-shipped
  call site (leaning candidate).** Insert Hub-routing directly into
  `email_classification.py::consult_librarian`'s existing call to `vault_
  filing_expert.determine_placement_and_file`, so the ALREADY-shipped
  `REQ-SB-55` pipeline's real, running behavior becomes Job -> Hub ->
  Librarian without touching Fetch/Classify/Thread-Match-Merge/Route-to-
  Project's own already-verified internals. This is NOT the same class of
  "retrofit" the project's "no retrofit, replace with pipeline" precedent
  was about — that precedent (`REQ-SB-63-US-01`'s own resolved question)
  concerned `REQ-SB-08`/`09`/`10`, PRE-KB-redesign modules on a genuinely
  different, older code path. `REQ-SB-55` is itself a NEW-model pipeline
  built under this same redesign, and `REQ-SB-63-US-01-T02` already
  proved, live, that an ADDITIVE node/edge can be wired into `REQ-SB-55`'s
  compiled `StateGraph` after shipment without reverting or rewriting any
  already-verified work — this would be the same shape again, one call
  site rewrapped, not a rebuild. Also matches the PRD's own present-tense
  worked example ("...is connected to the Data Gathering Hub, which sends
  it to the Librarian...") and the operator's own "builds ON TOP OF the
  pipeline once it exists" framing.
- **Option B — forward-only.** Leave `REQ-SB-55`'s existing `consult_
  librarian` call untouched exactly as shipped; Hub-mediation applies only
  to whatever pipeline Job is built AFTER this story ships. Matches the
  operator's own SPRINT-049-time sequencing decision ("Finish SPRINT-049
  as-is, add Hub-routing after") read literally, and avoids touching
  already-verified, currently-running production behavior at all.

This pass leans toward Option A (reasoning above) but does **not** decide
it — the PRD's own text is explicit that this is a real, unresolved
question for `/spec`, and no operator confirmation was available during
this drafting pass (unlike `REQ-SB-63-US-01`, where the equivalent
question WAS resolved live, in-session, by direct operator answer).
`REQ-SB-64-US-01-T02` above is written to cover EITHER answer generically
("route the Email Capture Pipeline's existing consult_librarian call
through the Hub") — its concrete shape (edit the shipped call site
in-place vs. gate it behind a forward-only branch) is not locked until
this question is confirmed.

**Open scope question #2 (mechanical shape) — genuinely open, NOT
resolved by this pass (part of why `gate: flagged`):**

- **Candidate — a new, plain, composed-alongside business-layer function
  (leaning candidate).** A new Hub-gateway function (e.g. `section_hub.
  route_placement_request(...)`), composed alongside `section_registry.
  py` the same way that module is itself "composed alongside `agent_
  registry.py`, not inside it" (`ADR-014`'s own precedent), called
  directly and synchronously from a pipeline Job — the exact call shape
  `ADR-041` point 3 already establishes for "branch to consult an
  Expert," and the exact shape `consult_librarian` already uses to reach
  the Librarian today (this just inserts one more explicit hop). A
  decorator/interceptor around `vault_writer` was considered and is NOT
  the leaning candidate: today's only existing "Hub" implementation
  (`graph.py::_route_hub_request`) is a LangGraph node bound to chat
  `AgentConversationState` — structurally unusable by a Pipeline Job,
  which is a plain Python function outside that graph — and an implicit
  interceptor would need to solve "which Section is this call scoped to"
  invisibly, a problem an explicit call site (which already knows its own
  `requesting_agent_id`, per `consult_librarian`'s existing signature)
  does not have.
- **What "extra data" a Hub might add to passing traffic is explicitly
  OUT of scope for this pass** — the operator named it as a possible
  FUTURE addition only, not a resolved current one; not designed here.

This is genuinely a design-latitude question this story leaves to the
architect pass at `/plan-tasks`, mirroring `REQ-SB-63-US-01`'s own
two-phase precedent (analyst proposes/flags, architect designs the
concrete shape, decomposer locks ACs against it) — not something this
`/spec` pass commits to.

**Scoping decision — narrowed to the one concrete, operator-named write
path, not the PRD's full literal breadth:** see `## Context`'s own
"Scope-narrowing decision" paragraph and `## Non-Goals` above. Recorded
here as part of why `gate: flagged` — this is a real, disclosed
interpretive choice this pass made to keep the story buildable and sized
for one working context, not something the PRD itself stated this
precisely.

**Prototype parity:** N/A — no new `html-prototype/` screen region.
`agents-map.html` already visually represents each Section's Hub node;
this is a backend routing change with no new UI state.

**No other trigger fired beyond trigger-1/trigger-8 above:** `REQ-SB-64`
carries no `<!-- Draft -->` marker in the PRD (it is explicitly "not a
placeholder," per its own Acceptance text); no `ESCALATIONS.md` entry was
written — both open questions are forward, PRD-acknowledged design
questions awaiting operator confirmation, not backward pipeline steps or
out-of-scope events; not contradictory — the PRD's own text is internally
consistent, it simply leaves two questions open on purpose; sizing is
kept to one generalized gateway mechanism plus one concrete integration
point (mirroring `REQ-SB-63-US-01`'s own comparable two-task shape), not
the full, epic-sized literal reading of "every agent/pipeline KB
read/write" — see the scope-narrowing decision above for why that larger
reading is explicitly deferred rather than attempted in this story.

**What to do next:** this story stays `Draft`/`gate: flagged` — it should
NOT proceed to `/plan-tasks` until a human confirms, in `REVIEW-QUEUE.md`:
(1) the retrofit-scope question (Option A vs. Option B above), and (2)
the mechanical-shape candidate (or an alternative). Once both are
answered, update this story's `## Notes` with the resolution (mirroring
how `REQ-SB-63-US-01`'s own resolved retrofit question was recorded) and
re-run `/plan-tasks REQ-SB-64-US-01`.
