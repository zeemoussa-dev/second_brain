---
id: REQ-SB-27-US-01
title: Skill repository — registration and per-agent access (plumbing only; first real skill deferred)
requirement_ids: [REQ-SB-27]
requirement_section: "REQ-SB-27: Skills Repository"
phase: P1
status: Done
gate: clear
gate_reason: ""
sprint: "SPRINT-015"
created: 2026-08-11
updated: 2026-08-12
---

# REQ-SB-27-US-01 — Skill repository — registration and per-agent access (plumbing only; first real skill deferred)

## Story

**As a** Second Brain user
**I want** a repository where skills can be registered and specific agents
can be granted access to them
**So that** an agent's capabilities can be extended in a structured,
discoverable way as real skills are built over time, instead of every new
capability needing its own bespoke, one-off wiring into a single agent

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-27: Skills Repository* — "A
  repository of skills exists that agents can draw on to perform
  specialized tasks beyond their core built-in function — for example, an
  agent that understands architecture/engineering diagrams can be given a
  photo and identify the components in it." Acceptance: "A skill can be
  registered in the repository; an agent with access to a skill can invoke
  it to perform the specialized task the skill provides (e.g. given an
  uploaded image, identify and describe its components) and use the result
  in its response or filing decision."
- **PRD breadcrumb (2026-08-11, operator-authored) — this requirement's own
  self-assessment:** "this is architecturally the least-precedented
  requirement captured this session and will need real design work, not a
  quick extension of an existing pattern." It names four genuinely open
  questions, none decided in the PRD: (1) what a "skill" actually is
  architecturally; (2) how an agent gets access to a skill (assigned like
  keywords/Section, or available to all agents by default); (3) which
  skill(s) to actually build first — the operator's own worked example
  (image/diagram understanding) implies multimodal input, a real technical
  capability this project has zero precedent for anywhere in its stack;
  (4) the relationship to REQ-SB-28 (File Upload) as the likely input
  mechanism for skills like summarization.
- **Existing registry-pattern precedent read in full before scoping this
  story:** `app/business/agent_registry.py` (`ADR-011` — a fully static,
  hardcoded `AGENTS` dict; agent identity/type/actions are deliberately
  never made mutable) and `app/business/provider_registry.py` (`ADR-014` —
  a *new*, persisted, user-mutable concern composed *alongside*
  `agent_registry.py`, not inside it; a Provider with no real client yet
  returns an honest "not available" response via `has_real_client()`
  rather than a fabricated result, and every known agent self-heals to a
  default assignment). `section_registry.py` (also `ADR-014`) is the same
  shape one concept over (Section instead of Provider). Both are directly
  relevant precedent for "a repository of named things an agent can be
  linked to," but neither settles what a *skill* — a unit of specialized
  **capability**, not configuration — actually is, or how it is invoked.
  That is a materially different kind of decision (an execution-model
  decision, not a configuration-schema decision) and is not assumed here.
- **Scoping decision (why this story is plumbing-only, not the full
  requirement):** the requirement's own Acceptance text requires an agent
  to actually *invoke* a skill and *use a real result* ("given an uploaded
  image, identify and describe its components"). Building that for the
  operator's own worked example would mean this project's first-ever
  multimodal/image-understanding integration, with no existing Provider,
  client, or architecture pattern to extend — a substantial, independent
  technical build in its own right, not a natural corollary of "a
  repository exists." Per this run's own instruction to scope to something
  buildably small if a "no independent value alone" analysis supports it:
  a skill *registry* with per-agent *access* grants has real, demonstrable
  value on its own — mirroring `section_registry.py`'s own precedent, which
  shipped and was useful purely as an organizational/access-control
  concern before any functional payoff was layered on top — **so long as
  invoking a skill with no real handler yet returns an honest "not
  available" response**, the same `has_real_client()`-style honesty
  pattern `ADR-011`/`ADR-014` already established, never a fabricated
  result. This story is scoped to exactly that: registration, per-agent
  access grant/revoke, and an honest not-yet-available invocation
  response. **This story alone does not fully satisfy REQ-SB-27's PRD
  Acceptance text** — the first real skill's actual implementation is
  explicit follow-on work, only after a human resolves the "what is a
  skill" architectural question this story flags rather than guesses (see
  Non-Goals and the flag reasoning in `## Notes`).
- No `html-prototype/` screen shows any Skills surface — confirmed by
  direct inspection of `settings.html` (which has Sections/Providers cards
  but no Skills card) and `agents-map.html`'s agent detail panel (Settings/
  Actions/Chat/History sections, no skill-access picker). This story ships
  zero UI (see `## Non-Goals`), so no `/design` pass is required for *this*
  story to proceed; a future skill-invocation follow-on story that adds a
  Skills card / access picker will need one first.
- **Update, 2026-08-12 — `ADR-015` (LangGraph + shared MCP server,
  `Accepted` 2026-08-11) resolves this story's primary blocking
  ambiguity.** `ADR-015` Decision points 3, 7, and 9 settle what a "skill"
  actually is, architecturally: Second Brain now runs one shared MCP
  server (`app/api/mcp_server.py`, official `mcp` SDK's `FastMCP`, mounted
  at `/mcp`) that both Second Brain's own in-app LangGraph agents and
  Hermes's external orchestration call into as tool-calling clients; per
  Decision point 9, "`REQ-SB-27`'s skills become new `@mcp.tool()` entries
  over time" on that **same** server (not a new server, not a new
  mechanism per skill). This directly resolves the "hardcoded catalog
  (`agent_registry.py`) vs. persisted user-mutable entry
  (`section_registry.py`/`provider_registry.py`, `ADR-014`) vs. something
  else" fork `ESCALATIONS.md` → `ESC-006` posed: it is genuinely **both**,
  at two different layers, exactly mirroring how `agent_registry.py`
  (hardcoded agent identity) and `section_registry.py`/`provider_registry.
  py` (persisted per-agent assignment) already coexist for agents
  themselves — a skill's *capability* (its actual specialized-task logic)
  is necessarily code — an `@mcp.tool()`-decorated Python function, only
  ever created/changed by deploying code, never by a runtime "create
  skill" form — while an agent's *access* to a registered skill remains
  exactly what this story already scoped it as (Scenarios 2/3/5): a new,
  persisted, per-agent grant/revoke concern, composed alongside the tool
  registry the same way `section_registry.py`/`provider_registry.py`
  compose alongside `agent_registry.py`. See `## Constraints` and `##
  Notes` for the full resolution and what remains genuinely open (the
  default-vs-explicit access model for *future* skills, the first real
  skill's implementation, and the `REQ-SB-28` file-upload relationship —
  none of which block *this* story's already-explicit-grant-only scope).

## Acceptance Criteria

<!-- Untagged Gherkin — the decomposer authors final wording and assigns
AC-IDs at /plan-tasks. Happy path first, then access control, then the
honesty-on-no-real-handler edge case, then revocation. Deliberately scoped
to registry/access plumbing only — see Context's scoping decision; no
scenario here asserts a specific skill actually performing a specialized
task. -->

### Scenario 1: A skill can be registered in the repository

```gherkin
Given the skill repository's code-level catalog (`app/business/skill_tools.py`)
    exists
When a skill is registered by adding a new `@mcp.tool()`-decorated skill
    function, with a name and a description of the specialized task it
    provides, to that catalog
Then the skill appears in the repository's list of registered skills,
    returned by `GET /skills`
```
<!-- AC-ID: REQ-SB-27-US-01-AC-01 -->

### Scenario 2: An agent can be granted access to a registered skill

```gherkin
Given a skill is registered in the repository, and an agent exists
When the user grants that agent access to the skill (`POST
    /agents/{agent_id}/skills/{skill_id}`)
Then the skill appears in that agent's list of accessible skills, returned
    by `GET /agents/{agent_id}/skills`
```
<!-- AC-ID: REQ-SB-27-US-01-AC-02 -->

### Scenario 3: An agent without granted access cannot invoke a skill

```gherkin
Given a skill is registered in the repository, but a specific agent has
    not been granted access to it
When an invocation of that skill is attempted for that agent (`POST
    /agents/{agent_id}/skills/{skill_id}/invoke`)
Then the invocation is refused with a response distinct from the "not yet
    available" response Scenario 4 (AC-04) describes for a skill the agent
    DOES have access to
```
<!-- AC-ID: REQ-SB-27-US-01-AC-03 -->

### Scenario 4: Invoking a granted skill that has no real handler yet returns an honest response, not a fabricated result

```gherkin
Given an agent has been granted access to a registered skill, and that
    skill has no real, working implementation behind it yet (its stub
    body)
When the agent's invocation of that skill is attempted (`POST
    /agents/{agent_id}/skills/{skill_id}/invoke`)
Then the response honestly states the skill is not yet available
  And no fabricated or guessed result is returned in its place
```
<!-- AC-ID: REQ-SB-27-US-01-AC-04 -->

### Scenario 5: Skill access can be revoked from an agent

```gherkin
Given an agent currently has access to a registered skill
When the user revokes that agent's access to the skill (`DELETE
    /agents/{agent_id}/skills/{skill_id}`)
Then the skill no longer appears in that agent's list of accessible
    skills, returned by `GET /agents/{agent_id}/skills`
  And Scenario 3's (AC-03) refusal behavior now applies to that agent for
    that skill
```
<!-- AC-ID: REQ-SB-27-US-01-AC-05 -->

## Affected Screens

- **None — this story ships zero UI** (see `## Non-Goals`), so the
  mandatory prototype-reconciliation rule does not trigger for it; no
  `net-new-design-needed` flag applies to *this* story. For reference, a
  future skill-invocation/UI follow-on story would need a Skills card in
  Settings (mirroring the existing Sections/Providers cards' list/edit
  shape, but **read-only for the skill catalog itself** — populated from
  the MCP server's own tool listing, not user-creatable, now that `ADR-015`
  has resolved the catalog to be code-defined) plus a per-agent skill-
  access picker on the Agent Detail Panel (mirroring the existing Section/
  Provider picker rows, which **is** user-mutable CRUD, consistent with
  this story's Scenarios 2/3/5) — that follow-on story would need
  `/design REQ-SB-27` first. See `## Notes`'s Prototype parity note.

## Dependencies

- **Blocked by:** none. The registry/access-grant mechanism this story
  scopes to can reuse `ADR-014`'s already-`Accepted` "new persisted concern
  composed alongside a hardcoded registry" pattern without needing any
  other story to ship first — and, per `ADR-015`, has a settled
  architectural home to compose against too (Second Brain's shared MCP
  server, `app/api/mcp_server.py` / `app/business/agent_orchestration/`).
  **No longer blocked on a human decision** — `ADR-015` (2026-08-11,
  `Accepted`) resolved the "what is a skill, architecturally" question
  this story previously flagged (see `## Context`'s 2026-08-12 update and
  `## Notes`). `ADR-015` itself is a technical dependency in the ordinary
  sense (its new `langgraph`/`mcp`/`langchain-openai`/`langchain-mcp-
  adapters` dependencies and `app/business/agent_orchestration/`/`app/
  business/vault_query_tools.py`/`app/api/mcp_server.py` scaffolding need
  to exist in code) — most plausibly landing as part of `REQ-SB-25-US-01`
  per `ADR-015` point 11's own sequencing note ("most plausibly
  `REQ-SB-25-US-01`, the earliest-ready of the four"), not decided or
  re-litigated here.
- **Related to:** REQ-SB-28 (File Upload for Agents, this session's
  companion requirement) — the operator's own worked example (image/
  diagram understanding) implies file/multimodal input as a skill's likely
  content source. This story's plumbing is deliberately invocation-input-
  agnostic (it does not assume an upload, or any other input shape) so it
  does not block REQ-SB-28's own story; the two are expected to compose
  once both exist, but that composition is not designed here.
- **Related to:** REQ-SB-18 (`REQ-SB-18-US-01`, Done) / REQ-SB-19
  (`REQ-SB-19-US-01`, Done) — same "new, persisted, user-mutable concern
  composed alongside a hardcoded registry" architectural shape, confirmed
  by `ADR-015` (see `## Context`) as the right fit **for skill *access*
  specifically**, not the skill catalog itself — the skill catalog's own
  shape is `agent_registry.py`'s hardcoded pattern instead (a code-level
  `@mcp.tool()` registration, per `ADR-015`), the inverse of what was left
  open here before.
- **External:** none new for the scope this story covers. The eventual
  first real skill (image/diagram understanding) will need a real
  multimodal-capable LLM Provider — none is configured today (Compass is
  this project's only real client, per `ADR-014`, and its multimodal
  capability is unconfirmed) — but that is explicit follow-on work, not a
  dependency of this story's own plumbing-only scope.

## Constraints

- **Never fabricate a skill's result.** An agent's *access* to a skill and
  that skill's *actual working implementation* are two independent facts —
  mirrors `ADR-011` point 3's "declared but not yet backed by a real
  handler" pattern and `ADR-014`'s `provider_registry.has_real_client()`
  honesty check. Invoking a skill with no real handler must always return
  an honest "not available" response (Scenario 4), never a guessed or
  placeholder result presented as real.
- **Does not require or assume REQ-SB-25 (Real Conversational Agent Chat)
  exists.** A skill invocation entry point can reuse whatever mechanism
  already triggers agent actions today (`ADR-011`'s keyword-trigger
  matching / the direct action-button path) without needing real LLM-
  backed chat to exist first; the exact entry point is an implementation
  detail left to `/plan-tasks`, not decided here.
- **Does not assume REQ-SB-28 (File Upload) as a skill's input mechanism.**
  This story's invocation scenarios are deliberately silent on *what* a
  skill receives as input beyond "it can be invoked" — composing with file
  upload is future work.
- No backend endpoint currently exists for registering skills, granting/
  revoking per-agent access, or invoking a skill — a new API surface is
  required; its exact shape is left to `/plan-tasks`, but its architectural
  home is now settled by `ADR-015` (see below).
- **Skill registration is code-level, not a runtime user-facing action.**
  Per `ADR-015` Decision points 3/7/9, a skill's actual specialized-task
  logic is an `@mcp.tool()`-decorated Python function registered on Second
  Brain's shared MCP server (`app/api/mcp_server.py`) — the same server
  Hermes's own external orchestration also calls into. Scenario 1's "a new
  skill is registered... it appears in the repository's list of registered
  skills" is satisfied by the MCP server's own tool-listing capability
  surfacing an already-coded `@mcp.tool()` entry, not by a `POST /skills`
  creation endpoint accepting arbitrary user-supplied logic — mirrors
  `agent_registry.py`'s existing "identity/capability stays hardcoded"
  precedent (`ADR-011` point 2), one layer over.
- **Per-agent skill *access* stays exactly the persisted, user-mutable
  concern this story already scoped it as (Scenarios 2/3/5)** — a new
  concern composed *alongside* the skill/tool catalog, mirroring
  `section_registry.py`/`provider_registry.py`'s `ADR-014` shape, not
  inside the MCP server itself. The MCP server's own tool surface is
  uniform and caller-agnostic (any connected MCP client — Second Brain's
  own LangGraph graph, or Hermes — sees the same registered tools;
  `ADR-015` describes no per-caller ACL layer at the MCP protocol level).
  Per-agent grant/revoke is therefore a Second-Brain-side-only concern,
  enforced within `app/business/agent_orchestration/`'s own graph — most
  plausibly at the tool-binding step, filtering which of the MCP server's
  tools get bound to a given agent's model call, before any MCP call is
  made for that agent — not a new capability the MCP server itself needs
  to understand. The exact enforcement point is ordinary `/plan-tasks`
  implementation latitude, not a further open architectural fork.
- **The honest "not yet available" pattern (Scenario 4) is satisfiable at
  the individual-tool level.** A skill can be registered now (its
  `@mcp.tool()` function exists and is discoverable) with a stub body that
  itself returns the honest "not yet available" message, exactly mirroring
  `ADR-015` point 3's `model_factory.py` precedent ("declared but not yet
  backed by a real handler → honest unavailability, no silent fallback, no
  fabricated response," itself reusing `ADR-011` point 3 / `ADR-014` point
  7) — the real implementation swaps in later without changing the
  registration/access-grant plumbing this story builds.

## Implementation Tasks

<!-- Decomposer pass, 2026-08-12 (original) drafted all 4 tasks at status:
Draft. Follow-up decomposer pass, 2026-08-12 (ESC-011 resolution) wired
T02's real cross-story depends_on and advanced all 4 tasks to status:
Ready in lockstep with the story — see ## Notes. -->

| Task | Title | depends_on | Status |
|---|---|---|---|
| [[REQ-SB-27-US-01-T01]] | Add `agent_skills.json` load/save primitives to `vault_writer.py` | — | Done |
| [[REQ-SB-27-US-01-T02]] | New `app/business/skill_tools.py` — code-level skill catalog + one illustrative `@mcp.tool()` stub skill | `REQ-SB-25-US-01-T05` (cross-story — creates `app/api/mcp_server.py`) | Done |
| [[REQ-SB-27-US-01-T03]] | New `app/business/skill_registry.py` — per-agent grant/revoke CRUD, `has_skill_access`, `invoke_skill` | `T01`, `T02` | Done |
| [[REQ-SB-27-US-01-T04]] | New `app/api/skills_router.py` — full HTTP surface; registered in `app/main.py` | `T03` | Done |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — N/A, manual verification mode still in effect
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **The first real skill's actual implementation** — e.g. the operator's
  own worked example, image/diagram understanding (multimodal input) —
  explicitly deferred to a follow-on story. The "what is a skill"
  architectural question is now resolved (`ADR-015`, see `## Context`);
  the remaining blocker for a real first skill is that no multimodal-
  capable Provider exists yet to back it. This story is plumbing only.
- **Any assumption about REQ-SB-28 (File Upload) as the skill's input
  mechanism** — that composition is left open, not designed or assumed
  here.
- **Any UI** — no `/design` pass has occurred for a Skills card or a
  per-agent skill-access picker; this story's scope is backend plumbing
  only until `/design` runs.
- ~~Whether skill definitions are hardcoded or persisted/user-mutable, or
  something else entirely~~ — **resolved 2026-08-12 by `ADR-015`**: a
  skill's capability is a code-registered `@mcp.tool()` entry on Second
  Brain's shared MCP server (hardcoded, like `agent_registry.py`); its
  per-agent access grant remains the persisted, user-mutable concern this
  story already scoped (like `section_registry.py`/`provider_registry.py`,
  `ADR-014`). See `## Context`'s 2026-08-12 update and `## Constraints`.
  No longer an open question for `/plan-tasks` to re-litigate.
- **Which agent(s) get default access to a newly registered skill** — not
  decided here (opt-in per agent, matching this story's Scenario 2's
  explicit-grant model, is the scenario as written, but whether some
  skills should instead be universally available to all agents by default
  is a real open question the PRD breadcrumb itself names and this story
  does not resolve).

## Notes

**Prototype parity:** not applicable — this story ships **zero UI**
(backend registration/access-grant plumbing only, see `## Non-Goals`), so
the mandatory prototype-reconciliation rule does not trigger for it; no
`html-prototype/` screen shows any Skills surface today (`settings.html`'s
Sections/Providers cards and `agents-map.html`'s agent detail panel were
both checked directly, confirmed empty of any Skills region). A future
skill-invocation/UI follow-on story will need `/design REQ-SB-27` first —
now that `ADR-015` has resolved the underlying architecture (below), the
UI shape question (a user-creatable list like Sections/Providers, vs. a
fixed read-only catalog like the Agents Map's own agent list — mirroring
that the *catalog* is code-defined while *access* is user-mutable) has a
clear answer too: a read-only catalog of registered skills (populated from
the MCP server's tool listing, not user-created) with a per-agent
access-grant picker alongside it, mirroring `AgentDetailPanel.tsx`'s
existing Section/Provider picker rows. Recorded here for whoever runs that
future `/design` pass; not designed now.

**Why `gate: flagged` — this one earns it, per this run's own explicit
instruction not to force a full technical design or guess at what a
"skill" is:**

1. **Material assumption, avoided by scoping down, but the scoping-down
   decision is itself a judgment call a human should confirm** — deferring
   the first real skill and the "what is a skill" architectural shape to
   later work is this analyst's own defensible read of "no independent
   value alone" (mirroring `section_registry.py`'s own precedent), not a
   PRD-directed instruction. A human should confirm this is the right
   slice before `/plan-tasks` commits engineering time to it.
2. REQ-SB-27 is not marked `<!-- Draft -->` in the PRD (it carries a
   "Scope resolved" breadcrumb, not an unfinalised marker) — trigger 2
   does not apply in the literal sense, but the breadcrumb's own text
   ("this is architecturally the least-precedented requirement... will
   need real design work") is functionally the same signal.
3. N/A directly (architect/ADR trigger) — but the architect's very first
   `/plan-tasks` pass on this story should expect to face exactly this
   "what is a skill" decision head-on; flagging it now, before that pass,
   is intended to save a wasted round-trip.
4. `ESCALATIONS.md` → `ESC-006` written (category `unclear-requirement`),
   per the Forbidden section's own instruction: "If the PRD is unclear,
   append an `ESCALATIONS.md` entry... flag the story, and move on." Not
   resolved in this pass — no operator was available to resolve it live,
   unlike `ESC-004`/`ESC-005`'s same-session resolutions for REQ-SB-20/21.
5. Not oversized as currently scoped (comparable to `section_registry.py`'s
   own already-`Done` size) — but the *full* requirement (a real,
   multimodal-capable first skill) would clearly be oversized for one
   story, which is exactly why it's deferred rather than attempted here.
6. N/A (coder trigger).
7. No contradictory PRD inputs.
8. **Multiple equally-valid architectural interpretations exist for what a
   "skill" is** (hardcoded catalog vs. persisted user-mutable entries vs.
   externally-hosted Hermes skill) **and genuinely unclear how an agent
   gets access** (explicit per-agent grant, as scoped here, vs.
   all-agents-by-default) — textbook trigger 8, not guessed past.

`gate: flagged` 2026-08-11, `gate_reason` above. `REVIEW-QUEUE.md` entry
added pointing here. `ESCALATIONS.md` → `ESC-006` added (`Status: Open`).
Not ready for `/plan-tasks` to commit to a task breakdown until a human
has at least glanced at the "what is a skill" question — though per
Pipeline.md's gating contract, a `gate: flagged` story does not block
other eligible work; the architect may still choose to open this story at
`/plan-tasks` and reason about the ADR-level question there, the same
"an ADR-creation flag does not halt `/plan-tasks`" precedent
`REQ-SB-18-US-01`/`REQ-SB-19-US-01` already established.

**Update, 2026-08-12 — first-skill product direction given.** All of the
above is now superseded history (the 2026-08-12 `/spec` re-pass already
resolved "what is a skill" via `ADR-015` and flipped this story's gate to
`clear`, unchanged by this update). Separately, the operator has now
named the actual first two skills: extracting data out of a file, and
inserting/formatting a table in an Excel file — both text/structured-data
skills, not the multimodal image-understanding example originally
discussed, which changes their feasibility (no new multimodal Provider
needed). Full detail: `ESCALATIONS.md` → `ESC-006`'s 2026-08-12 update.
Not built here — this story's own scope stays registry/access plumbing
only; the two named skills are real, but still-unspecced, follow-on
product work.

---

**`gate: clear` 2026-08-12 — `ADR-015` resolves the flag above; re-checked
against every MUST-FLAG trigger before flipping, not assumed clear:**

`ADR-015` (LangGraph + shared MCP server, `Accepted` 2026-08-11) was
written for `REQ-SB-20`/`25`/`26`/`27` collectively and, per its own
Decision points 3/7/9, directly settles what a "skill" is architecturally
— see `## Context`'s 2026-08-12 update and `## Constraints` for the full
reasoning. Re-checking each numbered point above against this new
grounding:

1. **No longer a bare judgment call — grounded in `ADR-015`.** The
   scoping-down decision (plumbing-only, first real skill deferred) was
   already this analyst's own defensible read before `ADR-015`; it is now
   also the shape `ADR-015` itself implies (register the tool now with an
   honest-unavailable stub body, swap in the real implementation later —
   `ADR-015` point 3's `model_factory.py` precedent, one layer over). Not
   a fresh assumption to fill a PRD gap — an architecture-grounded
   reading.
2. Unchanged — `REQ-SB-27` still carries a "Scope resolved" breadcrumb,
   not an unfinalised `<!-- Draft -->` marker. Does not apply.
3. N/A (architect/ADR trigger; this pass created no ADR, only read one).
4. No *new* `ESCALATIONS.md` entry written this pass. `ESC-006` is
   annotated (not silently edited past recognition — its Trigger/original
   Resolution paragraph are untouched) with a 2026-08-12 update recording
   the partial resolution and pointing here; its `Status` stays `Open`
   because two of its four named sub-questions (default-vs-explicit
   access model for *future* skills; the `REQ-SB-28` file-upload
   relationship) remain genuinely undecided at the PRD level — they just
   don't block *this* story's own already-narrower, explicit-grant-only
   scope, which was already designed around them.
5. Unchanged — not oversized as scoped.
6. N/A (coder trigger).
7. No contradictory inputs surfaced by this update.
8. **The "what is a skill" fork is resolved — one grounded interpretation
   remains, not multiple equally-valid ones** (`## Constraints` walks
   through why a single-dispatcher-tool vs. one-tool-per-skill variant
   doesn't reopen this: either way, a skill's real capability is
   necessarily code, never a runtime-user-created arbitrary behaviour).
   The "how does an agent get access" half of the original trigger-8
   citation was, on re-reading, never actually ambiguous for *this
   story's own scope* — Scenario 2 already commits to explicit per-agent
   grant; only the separate question of whether *future* skills should
   default to all-agents access remains open, and that was already
   correctly parked as a `## Non-Goals` item, not a blocker to this
   story's own ACs.

Net: no trigger fires for this story's current scope. `gate: clear`.
`REVIEW-QUEUE.md`'s `REQ-SB-27-US-01` entry is removed (resolved, not
still awaiting a human decision) — `ESCALATIONS.md` → `ESC-006` stays
`Open`, annotated, since it tracks the *whole* four-part question and two
parts remain genuinely open for future skill work, not because this story
is blocked. This story is ready for `/plan-tasks`.

---

**Architect pass, `/plan-tasks` step 1, 2026-08-12 — confirmed `ADR-015`
already covers this story's architectural needs; no new/changed ADR.**

Re-read `ADR-015` in full (`Implementation/Architecture/ADR.md`) against
this story's own plumbing-only scope. `ADR-015` Decision points 3/7/9
already resolve the one genuinely architectural question this story could
have raised ("what is a skill") — a skill's capability is a code-
registered `@mcp.tool()` entry on Second Brain's shared MCP server
(`app/api/mcp_server.py`), and per-agent *access* to it is a new,
persisted, user-mutable concern composed alongside the catalog, mirroring
`section_registry.py`/`provider_registry.py`'s already-`Accepted`
`ADR-014` shape. Everything this pass had to decide beyond that — the
exact catalog-listing mechanism, the new `.second-brain/agent_skills.json`
shape, and the invocation entry point — is ordinary CRUD-pattern
`/plan-tasks` implementation latitude `ADR-015` itself explicitly left
open (its own text: "the exact enforcement point is ordinary `/plan-tasks`
implementation latitude, not a further open architectural fork"), not a
new architectural class of decision. **No ADR created or changed** — trigger
3 does not fire.

Concrete plumbing decided this pass, recorded in full in
`Implementation/Architecture/architecture.md` → "Skills Repository —
registration & per-agent access (REQ-SB-27-US-01, plumbing only — applies
ADR-015, no new ADR)":

- **Catalog:** a new sibling module `app/business/skill_tools.py`
  (parallel to `app/business/vault_query_tools.py`) holds the actual
  `@mcp.tool()`-decorated skill function(s) plus its own small, literal,
  enumerable skill-metadata registry (`id`/`name`/`description`) —
  mirrors `agent_registry.py`'s hardcoded-dict shape one concept over.
  `skill_registry.list_skills()` reads that registry directly rather than
  introspecting the MCP server's full live tool list (which would also
  surface `vault_query_tools.py`'s non-skill tools). This story registers
  exactly one illustrative stub skill with an honest "not yet available"
  body (Scenario 4), demonstrating registration without building the
  first real skill.
- **Per-agent access:** new business module `app/business/
  skill_registry.py` (mirrors `section_registry.py`/`provider_registry.py`
  exactly: `list_skills`, `list_agent_skills`, `grant_skill_access`,
  `revoke_skill_access`, `has_skill_access`, `invoke_skill`) backed by a
  new sibling state file, `.second-brain/agent_skills.json` —
  `{"assignments": {<agent_id>: [<skill_id>, ...]}}`, no top-level catalog
  list (unlike `agent_sections.json`, since the catalog is code, not
  user-created). New `vault_writer.py` primitives `load_skills_state()`/
  `save_skills_state()` mirror `load_sections_state()`/
  `save_sections_state()`. **Deliberately no self-healing default
  assignment** — Scenario 2's explicit-grant-only model; the
  default-vs-explicit-access question stays open per `## Non-Goals`.
- **Invocation entry point:** new `app/api/skills_router.py` — `GET
  /skills`, `GET /agents/{agent_id}/skills`, `POST /agents/{agent_id}/
  skills/{skill_id}` (grant), `DELETE /agents/{agent_id}/skills/{skill_id}`
  (revoke), `POST /agents/{agent_id}/skills/{skill_id}/invoke`
  (Scenarios 3/4 — `has_skill_access` checked first; refusal vs. honest
  "not available" are distinct responses). Chosen over extending
  `agent_registry.py`'s static per-agent action mechanism (`ADR-011`)
  since skills are cross-cutting/dynamically grantable, keeping
  `agent_registry.py`/`agent_chat.py` untouched — this is the
  `/plan-tasks` decision the story's own Constraints left open ("the
  exact entry point is an implementation detail left to `/plan-tasks`").
- **Genuine code dependency, not newly discovered:** `app/business/
  agent_orchestration/` and `app/api/mcp_server.py` do not exist in code
  yet (confirmed by direct inspection this pass) — they are `ADR-015`'s
  own scaffolding, expected to land as part of `REQ-SB-25-US-01`. This
  story's tasks (`skill_tools.py`'s MCP registration, `skills_router.py`)
  depend on that scaffolding existing first — already named in this
  story's own `## Dependencies`; the decomposer should wire the
  task-level `depends_on` edge accordingly, not re-litigate it.

**Architecture scope (bounds the coder's tasks):**
`Implementation/Architecture/architecture.md` → "Skills Repository —
registration & per-agent access (REQ-SB-27-US-01)" (this pass's new
subsection — primary scope) plus, read-only for context/pattern-matching
only (not itself modified by this story): "Agent Sections & LLM
Providers — mutable, persisted agent configuration (REQ-SB-18-US-01,
REQ-SB-19-US-01)" (the `ADR-014` CRUD pattern this story mirrors) and
"In-App Agent Orchestration (LangGraph) & Shared MCP Server (REQ-SB-20,
REQ-SB-25, REQ-SB-26, REQ-SB-27)" (`ADR-015` — the shared MCP server /
`agent_orchestration/` scaffolding this story's tasks depend on but do
not build).

`gate: clear` 2026-08-12 — re-checked against every MUST-FLAG trigger:
(1) no material assumption — every open plumbing question was resolved
against an already-`Accepted` ADR/pattern, not guessed; (2) `REQ-SB-27`
is not `<!-- Draft -->`; (3) **no ADR created or changed**; (4) no new
`ESCALATIONS.md` entry; (5) not oversized, no `Blocked` status, no
cross-sprint dependency introduced (the `REQ-SB-25-US-01` scaffolding
dependency is an ordinary task-level `depends_on`, already named in
`## Dependencies`, not a new escalation); (6) N/A (coder trigger); (7) no
contradictory inputs; (8) no remaining multiple-equally-valid-options —
every plumbing question above had one grounded, ADR-consistent answer.
This story proceeds to the decomposer.

---

**Decomposer pass, `/plan-tasks` step 2, 2026-08-12 — ACs locked, tasks
drafted; story stays `Draft`, `gate: flagged` (a real, un-guessable
blocker, not a triviality).**

**AC authoring + locking:** all 5 of the analyst's untagged Gherkin
scenarios tightened for buildability (each `Given`/`When`/`Then` now names
the concrete HTTP surface it maps to, per the architect's own
`architecture.md` decisions — `GET /skills`, `POST`/`DELETE
/agents/{agent_id}/skills/{skill_id}`, `POST .../invoke`) and locked as
`REQ-SB-27-US-01-AC-01` through `REQ-SB-27-US-01-AC-05`, in scenario
order. No scenario's meaning was weakened, narrowed, or omitted — Scenario
1's tightening reflects the story's own Constraint that registration is
code-level, not a runtime action (`GET /skills` reflecting an
already-coded catalog entry, not a `POST /skills` creation call).

**Tasks drafted — 4 total, flat root, all at `status: Draft`:**
`REQ-SB-27-US-01-T01` (`vault_writer.py` primitives, `depends_on: []`),
`REQ-SB-27-US-01-T02` (`app/business/skill_tools.py` — catalog + one
stub `@mcp.tool()` skill, `depends_on: []`), `REQ-SB-27-US-01-T03`
(`app/business/skill_registry.py` — grant/revoke CRUD, `has_skill_access`,
`invoke_skill`, `depends_on: [T01, T02]`), `REQ-SB-27-US-01-T04`
(`app/api/skills_router.py` + `app/main.py` wiring, `depends_on: [T03]`).
Every locked AC has a matching AC-tagged manual verification step in
`T04`'s `## Tests` (this story ships zero UI, so the router — the
user/API-observable surface — carries the tagged steps, mirroring
`REQ-SB-08-US-01-T05`'s own established placement rule for backend-only
stories; `T01`-`T03` carry non-AC smoke checks only, mirroring
`REQ-SB-19-US-01`'s own provider-registry precedent).

**Why this story stays `Draft`, `gate: flagged`, not advanced to
`Ready` — a real blocker, checked against the Ready-gate's own three
conditions, not skipped:** (a) every AC is locked — true; (b) every
locked AC has a tagged step — true (`T04`); **(c) `depends_on` is
acyclic — cannot be honestly confirmed**, because this story's own real
dependency (named in its own `## Dependencies` and in this pass's
architecture-scope Notes above: `T02`'s `@mcp.tool()` registration needs
`app/api/mcp_server.py`'s shared `FastMCP` instance, which is
`REQ-SB-25-US-01`'s own scaffolding) has **no task ID to point at** —
direct inspection of `Implementation/Tasks/` this pass found **zero**
`REQ-SB-25-US-01-T*.md` files. `REQ-SB-25-US-01`'s own architect pass
completed 2026-08-12 (see that story's own `## Notes`, "Proceeding to the
decomposer"), but its decomposer step has evidently not yet run. Rather
than (i) inventing a task ID that does not exist (would silently break
`/implement-sprint` on a dangling reference) or (ii) guessing which task
in a not-yet-decomposed story will end up owning `mcp_server.py`
(a material assumption about another story's own task breakdown, not
this decomposer's call to make), `T02`'s `depends_on` is left `[]` with
the real blocker recorded directly in its own frontmatter `gate_reason`
and `## Context / Notes`, and this story's own `status:` stays `Draft`
so every task inherits `Draft` too (Pipeline.md's own lockstep rule),
which safely keeps `/implement-sprint` from picking any of them up before
the edge is real. This is trigger 7 (contradictory inputs — the
launching brief assumed `REQ-SB-25-US-01`'s tasks already existed) and
trigger 8 (genuinely blocked, not guessable) both firing; logged as
`ESCALATIONS.md` → `ESC-011` and a `REVIEW-QUEUE.md` entry, both pointing
here.

**What resumes this story:** once `REQ-SB-25-US-01` is run through its
own `/plan-tasks` decomposer step and a real task ID exists for whichever
task creates `app/api/mcp_server.py`'s `FastMCP` instance (and confirms
`app/business/vault_query_tools.py`'s final location), re-run the
decomposer on this story to (1) replace `REQ-SB-27-US-01-T02`'s
`depends_on: []` with that real task ID, (2) flip this story's `status:`
to `Ready` (checks (a)/(b) already pass; (c) will then be honestly
satisfiable), and (3) flip all 4 tasks to `status: Ready` in lockstep.
No AC text, task content, or file scope needs to change at that point —
only the one `depends_on` edge and the two status flips.

**Separately, worth a `/plan-sprints`-time note (not resolved here, per
this pass's own brief):** even once wired, this story's tasks form a real
cross-story dependency chain into `REQ-SB-25-US-01`'s own tasks. Whether
the two stories land in the same sprint or in ordered sprints linked by
`depends_on_sprints` is the product-owner's call at `/plan-sprints`, not
decided here (Pipeline.md hard rule 7) — flagged here only so it isn't
missed as a "these are two unrelated Ready stories" grouping mistake once
both are actually `Ready`.

---

**Follow-up decomposer pass, 2026-08-12 — resolves `ESC-011`; story
advances `Draft → Ready`, `gate: flagged → clear`.**

`REQ-SB-25-US-01`'s own decomposer pass has since completed
(`status: Ready`, `gate: clear`; 8 tasks, `T01`-`T08`).
`REQ-SB-25-US-01-T05` (`Implementation/Tasks/
REQ-SB-25-US-01-T05-mcp-server.md`) is confirmed as the real task that
creates `app/api/mcp_server.py` — a module-level `FastMCP` instance
(named `mcp_server`) registering `vault_query_tools.py`'s four functions,
mounted at `/mcp` in `main.py`.

**Change made:** `REQ-SB-27-US-01-T02`'s `depends_on: []` replaced with
`[REQ-SB-25-US-01-T05]` (cross-story task-ID edge, not a story-ID —
Pipeline.md hard rule). No AC text or task file scope changed otherwise
beyond recording the resolution and confirming the shared instance's real
name (`mcp_server`) in `T02`'s own file, per its own "confirm before
assuming" instruction.

**Ready-gate re-checked, all three conditions now honestly satisfiable:**
(a) every AC is locked — unchanged, true (all 5, `AC-01`-`AC-05`,
original decomposer pass); (b) every locked AC has a tagged verification
step — unchanged, true (`T04`'s `## Tests`); (c) `depends_on` is acyclic
— **now confirmable**: `T01` → `[]`; `T02` → `[REQ-SB-25-US-01-T05]`
(external, and `REQ-SB-25-US-01-T05` itself has no dependency back into
this story — no cycle); `T03` → `[T01, T02]`; `T04` → `[T03]`. A linear
chain, `T01`/`T02` → `T03` → `T04`, with one external leaf edge into a
different story's own already-`Ready` task graph. No cycle anywhere.

Story `status:` moves `Draft → Ready`. All 4 tasks moved `Draft → Ready`
in lockstep (Pipeline.md's task-status-lockstep rule) — see
`## Implementation Tasks` table above and each task's own frontmatter.

**Gate:** no MUST-FLAG trigger fires this pass — the only reason this
story stayed `Draft`/`gate: flagged` after its original decomposer pass
was the un-wireable `depends_on` edge (trigger 7/8, `ESC-011`), now
resolved with a real task ID, not a guess. `gate: flagged → clear`.

**`ESCALATIONS.md` → `ESC-011` flipped to `Resolved`**, naming this task
update (`REQ-SB-27-US-01-T02`'s `depends_on` edge plus this story's
`Draft → Ready` transition) as the resolving artefact.
`REVIEW-QUEUE.md`'s `REQ-SB-27-US-01` entry is removed — fully resolved,
nothing left awaiting a human decision for this story. (`ESC-006` is
untouched by this pass — it separately tracks the still-open
default-vs-explicit future-skill-access and `REQ-SB-28` file-upload
questions, neither of which block this story's own now-`Ready` scope.)

This story and all 4 of its tasks are eligible for `/plan-sprints` —
subject to the cross-story sequencing note immediately above (this
story's `T02` cannot start building before `REQ-SB-25-US-01-T05` is
`Done`; a `/plan-sprints`-time call, not decided here).

---

**Coder pass (`/implement-sprint SPRINT-015`, 2026-08-12).** All 4 tasks
built and `Done`, in dependency order (`T01`→`T02`→`T03`→`T04`). All 5
locked ACs verified live against the real backend (port `8002` — ports
`8000`/`8001` both live-occupied, same established pattern `SPRINT-014`
set), real HTTP calls, `.second-brain/agent_skills.json` deleted before
each verification pass:

- **AC-01**: `GET /skills` returned exactly the one `diagram-understanding`
  skill this story's `T02` registered.
- **AC-02**: granting `email-capture` access (`POST /agents/email-capture
  /skills/diagram-understanding`) was reflected in `GET
  /agents/email-capture/skills`.
- **AC-03**: invoking the skill for an ungranted agent
  (`meeting-capture`) returned `403` with a refusal message.
- **AC-04**: invoking the skill for the granted agent (`email-capture`)
  returned `200` with an honest "not yet available" body, distinct in
  both status code and shape from `AC-03`'s refusal — no fabricated
  diagram-understanding result anywhere in the response.
- **AC-05**: revoking access (`DELETE .../diagram-understanding`) removed
  it from `GET /agents/email-capture/skills`, and a further invoke
  attempt returned `AC-03`'s same `403` refusal shape.

One scope-internal reconciliation was needed (`T02`'s stub-skill
registration turned out to need zero edits to `app/api/mcp_server.py`
itself — the `@mcp.tool()` decorator registers on the already-shared
`FastMCP` instance regardless of which module applies it — and `T03`'s
own dispatch mechanism was reconciled against `T02`'s real one-function-
per-skill shape via a small local handler-lookup table in
`skill_registry.py`, since `T02` did not build a generic `skill_tools.
invoke(skill_id)` dispatcher); both are recorded in each task's own
Implementation Log as ordinary scope-internal judgement calls, not
escalations — no locked AC was weakened, omitted, or changed in meaning,
and no file outside each task's own declared scope was touched.

`status: Ready → Done`. This story remains plumbing-only per its own
Non-Goals — no real skill implementation, no UI, both explicit follow-on
work. Full evidence in each task's own Implementation Log.
