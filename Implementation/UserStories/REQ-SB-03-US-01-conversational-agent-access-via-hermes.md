---
id: REQ-SB-03-US-01
title: Conversational Agent Access via Hermes — a Hermes-connected agent answers questions grounded in the indexed vault
requirement_ids: [REQ-SB-03]
requirement_section: "REQ-SB-03: Conversational Agent Access via Hermes"
phase: P1
status: Draft
gate: clear
gate_reason: ""
sprint: ""
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-03-US-01 — Conversational Agent Access via Hermes — a Hermes-connected agent answers questions grounded in the indexed vault

## Story

**As a** Second Brain user
**I want** to ask my Second Brain a question from a Hermes-connected channel
and receive an answer grounded in my indexed vault content
**So that** I can query my own knowledge base conversationally, from
wherever Hermes already reaches me, without opening the notes browser
directly

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-03: Conversational Agent Access via
  Hermes* — "The user can query and converse with their Second Brain through
  Hermes-connected channels. The agent reasons over the indexed vault (per
  REQ-SB-01/REQ-SB-02) to answer, rather than requiring the user to open the
  notes browser directly." Acceptance: "From at least one Hermes-connected
  channel, the user can ask a question and receive an answer grounded in the
  indexed vault content, with no separate 'sync to KB' or promotion step
  required first."
- **Ported from `agentic-map` REQ-015 (OpenClaw-based multi-channel
  messaging) + REQ-016 (`kb_read` tool)** — tool swap only (Hermes instead of
  OpenClaw, the vault index instead of a Postgres/Qdrant-backed KB). See
  `Implementation/Plans/2026-08-10-agentic-map-requirement-port.md`.
- **This is the single most architecturally consequential unbuilt
  requirement in the PRD** — it is the first requirement that asks Second
  Brain to actually be reached by the real, external Hermes system, rather
  than assume it as a name in documentation. Confirmed by direct grep across
  `src/backend` and `Implementation/Architecture/` (2026-08-13): every
  existing mention of "Hermes" is either (a) a docstring/comment naming
  Hermes as a *future* consumer of infrastructure built for a different,
  in-app purpose, or (b) `MEMORY.md`'s own standing constraint — "Hermes
  (external MCP-based multi-channel communication tool) is an integration
  point, not something this project builds — treat it as a dependency with
  its own interface, not code to implement here." **No real Hermes
  connection, credential, endpoint configuration, or live round-trip exists
  anywhere in this codebase.** `Implementation/Architecture/architecture.md`
  → *External Services* still reads "Hermes ... — planned integration, not
  yet built" as of this pass.
- **What already exists, and is directly reusable — not a guess:**
  `ADR-015` (`Accepted`, written 2026-08-11 for `REQ-SB-20`/`25`/`26`/`27` —
  Second Brain's own **in-app** LangGraph agent orchestration) adopted a
  **shared MCP server** design specifically so a future external MCP client
  could reuse the same tool surface: `app/api/mcp_server.py` builds a real,
  live `mcp.server.fastmcp.FastMCP` instance, registers four
  `@mcp.tool()`s (`list_known_customers`, `list_known_kinds`,
  `list_known_partners`, `list_notes_in_kind_folder` —
  `app/business/vault_query_tools.py`'s thin wrappers over already-existing
  `vault_writer` primitives), and is mounted at `app.mount("/mcp", ...)` in
  `app/main.py` over Streamable HTTP transport. Both the module's own
  docstring and `architecture.md` state the intent directly: *"exposes
  vault-query tools to both Second Brain's own in-app LangGraph agents ...
  and Hermes's own external orchestration, over the same mounted
  endpoint"*; *"Hermes reaches this MCP server over the same host:port as
  every other Second Brain HTTP surface."* **This settles the
  client/server direction question the operator anticipated might be
  open: Second Brain is architecturally the MCP SERVER; a Hermes-side agent
  would be an MCP CLIENT reaching `/mcp`, structurally identical to Second
  Brain's own `app/business/agent_orchestration/mcp_client.py`'s loopback
  client** (confirmed by direct reading of both files, 2026-08-13). This
  mechanism has never been exercised by anything other than that same
  in-app, same-machine loopback client — no external MCP client, Hermes or
  otherwise, has ever connected to it.
- **What is genuinely NOT settled, and is not this analyst's call to guess
  (see `## Notes` / `ESCALATIONS.md` → `ESC-023`):**
  1. **Whether a real, reachable Hermes deployment exists at all** to point
     at this endpoint — where it runs, who administers it, and how Second
     Brain (on this single laptop, no admin rights, per `MEMORY.md`) would
     be discoverable to it, is an external-system fact this repo has no
     record of. **Operator decision, 2026-08-13: this specifically does
     NOT block `/spec` finalization or `/plan-tasks` — only real, live
     end-to-end verification at `/implement-sprint` time** (the MCP
     server-side auth/tools this story adds can be built and verified
     without a live Hermes peer; a genuine Hermes-to-Second-Brain round
     trip cannot). See `## Notes`.
  2. ~~The `/mcp` endpoint has zero authentication or authorization
     today~~ — **resolved, operator decision 2026-08-13: yes, add real
     authentication before any non-loopback caller reaches `/mcp`, in scope
     for this story** (see `## Constraints`/Scenario 4 below). Confirmed by
     direct reading of `app/main.py`: `CORSMiddleware` is scoped only to the
     Vite dev-server's browser origins (irrelevant to a server-to-server MCP
     client, which is not subject to CORS at all), and
     `app.mount("/mcp", mcp_server.streamable_http_app())` carries no auth
     dependency, API key, or bearer-token check of any kind today.
  3. **The four tools currently registered are not a substitute for "the
     agent reasons over the indexed vault to answer."** They are narrow
     folder/tag-enumeration helpers built for `REQ-SB-35`'s Vault Filing
     Expert (which notes/customers/kinds/partners exist), not a
     search/retrieval tool over arbitrary note content. REQ-SB-03's own PRD
     text names its mechanism explicitly — "per REQ-SB-01/REQ-SB-02." Both
     are confirmed `Draft`/`gate: flagged`, unbuilt (`REQ-SB-01-US-01`,
     `REQ-SB-02-US-01` — "the least-started requirements in the whole PRD,"
     per `ESCALATIONS.md` → `ESC-008`). **This is a hard, literal blocking
     dependency, not a stylistic one** — there is no real index or search
     tool to register on the MCP server for a Hermes-side agent to call
     until REQ-SB-01/REQ-SB-02 exist. Per the operator's own 2026-08-13
     framing, this is a **sequencing fact, not a spec-level ambiguity** —
     this story's own scenarios are fully and confidently specced; they
     simply cannot be built/verified until REQ-SB-01/REQ-SB-02 ship (an
     ordinary cross-story `depends_on` sequencing concern for `/plan-tasks`/
     `/plan-sprints`, ordinary precedent already established by e.g.
     `REQ-SB-20-US-01`'s own wait on `REQ-SB-18-US-01`).

## Acceptance Criteria

<!-- Untagged Gherkin — the decomposer authors final wording and assigns
AC-IDs at /plan-tasks. Written directly against the PRD's own Acceptance
text; the Constraints/Notes sections are explicit that none of these can be
built until REQ-SB-01/REQ-SB-02 ship and the human decisions named in Notes
are made. -->

### Scenario 1: A question asked through a Hermes-connected channel is answered from the indexed vault

```gherkin
Given the user has a Hermes-connected channel available
  And the vault has already been indexed (REQ-SB-01) with content relevant
    to the user's question
When the user asks a question through that channel
Then the user receives an answer grounded in the indexed vault content
  And no separate "sync to KB" or promotion step was required first
```

### Scenario 2: A question with no relevant indexed content is answered honestly, not fabricated

```gherkin
Given the user has a Hermes-connected channel available
  And the vault's indexed content has nothing relevant to the user's
    question
When the user asks that question through the channel
Then the user receives an honest "no relevant vault content found" response
  And no fabricated or hallucinated answer is presented as if grounded in
    the vault
```

### Scenario 3: The vault-query tool surface is unreachable or the vault is unindexed

```gherkin
Given the user asks a question through a Hermes-connected channel
  And the vault-query tool surface the agent depends on is unavailable
    (e.g. the vault has never been indexed, or the tool endpoint cannot be
    reached)
When the agent attempts to answer
Then the user receives a clear, honest unavailability message
  And no fabricated answer is presented in its place
```

### Scenario 4: A non-loopback caller reaching `/mcp` without a valid shared secret is rejected

```gherkin
Given the `/mcp` endpoint now requires authentication for any non-loopback
    caller (operator decision, 2026-08-13 — minimum-viable shared-secret
    shape, mirroring this project's existing COMPASS_API_KEY/
    ANTHROPIC_API_KEY Settings-based credential pattern)
When a caller other than Second Brain's own in-app loopback MCP client
    (e.g. a would-be Hermes-side client) reaches `/mcp` without presenting a
    valid shared secret
Then the request is rejected
  And no vault-query tool call is executed as a result
  And the in-app LangGraph agent's own existing loopback access (already
    live, REQ-SB-25-US-01) is unaffected by this change
```

## Affected Screens

None — backend/integration only. The Hermes-connected channel's own UI is
external to Second Brain, per `MEMORY.md`'s standing "Hermes is an
integration point, not something this project builds" constraint. Nothing
in `html-prototype/` covers or should cover this requirement.

## Dependencies

- **Blocked by:** `REQ-SB-01` (Vault Indexing) — `REQ-SB-01-US-01`, `Draft`/
  `gate: flagged`, unbuilt. This story's Scenario 1 has no real indexed
  content to reason over until this ships.
- **Blocked by:** `REQ-SB-02` (Browse & Search) — `REQ-SB-02-US-01`, `Draft`/
  `gate: flagged`, unbuilt. The PRD's own text names this as the search
  mechanism the agent reasons over; no relevance-ranked query tool exists to
  register on the MCP server without it.
- **Related to:** `ADR-015` / `REQ-SB-25-US-01` (Real Conversational Agent
  Chat, `Done`) — the shared MCP server (`app/api/mcp_server.py`) this
  story's read-access mechanism is architecturally designed to extend was
  built there, for a different (in-app) purpose. This story reuses, not
  duplicates, that infrastructure once REQ-SB-01/02 exist to back it with
  real tools.
- **External:** a real, reachable Hermes deployment to connect to — does not
  exist in this repo or is knowable from it, and per the operator's own
  2026-08-13 decision, is explicitly **not required to be resolved before
  `/spec`/`/plan-tasks`** — only before `/implement-sprint` can perform real,
  live end-to-end verification. See `## Notes`.

## Constraints

- **Do not build a second, parallel tool-registration mechanism.** Per
  `ADR-015`'s own "grow by registering new `@mcp.tool()` entries on the same
  server, never a new server per capability" extensibility rule, any new
  vault-search tool this story eventually needs (once REQ-SB-01/02 exist)
  registers on the existing `app/api/mcp_server.py` `FastMCP` instance, not
  a second server.
- **No fabricated/hallucinated answers.** Matches this project's standing
  honesty posture already established for actions and Providers (`ADR-011`,
  `ADR-014`) and reused for search-quality guardrails (`REQ-SB-33`, Agent
  Grounding & Honest-Uncertainty Guardrail, `Done`) — an unanswerable
  question gets an honest "not found," never a confident-sounding guess.
- **`/mcp` must require real authentication for any non-loopback caller
  before this story's Hermes-reachable behavior ships (operator decision,
  2026-08-13).** Minimum-viable shape: a shared secret/API key check,
  mirroring this project's own existing `COMPASS_API_KEY`/
  `ANTHROPIC_API_KEY` Settings-based credential pattern (a new
  `HERMES_MCP_SHARED_SECRET`-shaped config value). The exact scheme (header-
  based bearer token vs. another mechanism) is ordinary design latitude for
  `/plan-tasks`'s architect step — the requirement-level decision ("yes,
  real auth, in scope, minimum-viable shared-secret shape") is settled, not
  open. Second Brain's own existing in-app loopback MCP client
  (`agent_orchestration/mcp_client.py`, `REQ-SB-25-US-01`, already live)
  must remain unaffected by this change.
- **The real Hermes connection details (endpoint, credentials, discovery)
  are genuinely unknown and cannot be resolved by this analyst** — an
  external-system fact, confirmed by the operator 2026-08-13 as *not*
  blocking `/spec`/`/plan-tasks`, but blocking real live verification at
  `/implement-sprint`. See `## Notes`.

## Implementation Tasks

<!-- Left for the architect/decomposer at /plan-tasks — blocked on
REQ-SB-01/REQ-SB-02 shipping (ordinary cross-story sequencing, not a spec-
level flag). NOT blocked on confirming a real Hermes deployment exists —
that only gates /implement-sprint's own live end-to-end verification step,
per the operator's 2026-08-13 decision (see ## Notes). -->

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Building or operating Hermes itself** — per `MEMORY.md`'s standing
  constraint, Hermes is an external dependency with its own interface, not
  code this project implements.
- **Write access** — this story is read/query-only; `REQ-SB-04` covers
  writes, under its own, separately-scoped trust rule.
- **Content ingestion (attachments/uploads via a Hermes channel)** —
  `REQ-SB-05`.
- **Any new vault-search/relevance-ranking implementation** — that is
  `REQ-SB-02`'s own scope; this story only consumes it once it exists.
- **Second Brain's own in-app chat (`REQ-SB-13`/`REQ-SB-25`)** — a
  different, already-`Done` mechanism, in-app only, not an external Hermes
  channel. Not extended, duplicated, or reconciled with here.

## Notes

**Prototype parity:** N/A — no `html-prototype/` screen covers or should
cover an external Hermes channel; this requirement's UI, if any, belongs to
Hermes, not Second Brain.

**Update, 2026-08-13 — Operator decision, gate reset to `clear`.** Of this
story's two originally-flagged open questions (`/mcp` authentication; real
Hermes deployment reachability), the operator resolved the one they could:
**yes, add real authentication to `/mcp` before any non-loopback caller
reaches it — minimum-viable shared-secret shape (a new
`HERMES_MCP_SHARED_SECRET`-style config value, mirroring
`COMPASS_API_KEY`/`ANTHROPIC_API_KEY`), in scope for this story, not
deferred.** This is now Scenario 4 and a `## Constraints` entry above, not
an open question. The exact scheme (bearer token vs. another header-based
mechanism) is ordinary `/plan-tasks` architect latitude, not a remaining
ambiguity.

The second question — **whether a real, reachable Hermes deployment
actually exists to connect to and test against** — was explicitly **not**
resolved: "genuinely cannot be decided by me, needs the operator's own
real-world knowledge" (coordinator relay, 2026-08-13). This stays open,
tracked in `ESCALATIONS.md` → `ESC-023` (status remains `Open`, not
`Resolved`), but the operator was explicit that **this does not block
`/spec` finalization or `/plan-tasks` architecture/task creation** — it
only blocks real, live end-to-end verification at `/implement-sprint` time
(a coder can build and unit-test the `/mcp` server-side auth and, once
REQ-SB-01/02 exist, the vault-query tools themselves, entirely without a
live Hermes peer; what cannot be verified without one is an actual
Hermes-to-Second-Brain round trip). This is recorded as a live-verification
constraint on the eventual task/sprint, not a spec-level flag — the same
"design/build vs. live-verified" distinction this codebase already uses
elsewhere (e.g. `ESC-002`/`ADR-013` staying `Open` after design while
`/implement-sprint` verification was still pending).

With both of this story's own flagged questions now either resolved or
explicitly reclassified as a downstream build/verification-time constraint
rather than a spec-level ambiguity, and with the remaining REQ-SB-01/
REQ-SB-02 dependency being an ordinary sequencing fact (not a scope
ambiguity — this story's own scenarios are fully and confidently specced),
`gate:` is reset to `clear`. `REQ-SB-03` still cannot reach `/plan-tasks`
in a meaningfully buildable shape until `REQ-SB-01`/`REQ-SB-02` are at least
`Ready` — that remains a real, load-bearing dependency, just not a gate
flag.

**What to do:** run `/plan-tasks REQ-SB-03` once `REQ-SB-01`/`REQ-SB-02` are
at least `Ready` (architecture/task creation may proceed now per the
operator's own framing; `/implement-sprint`'s final live-verification step
for this story's Hermes-reachable scenarios additionally needs a confirmed,
reachable real Hermes deployment — track that separately at that time, not
here).

gate: clear 2026-08-13 — `/mcp` authentication resolved (operator decision:
yes, minimum-viable shared-secret shape, now Scenario 4/Constraints above);
real-Hermes-deployment-reachability remains genuinely open but explicitly
scoped by the operator as an `/implement-sprint`-time live-verification
concern, not a `/spec`/`/plan-tasks` blocker; the REQ-SB-01/REQ-SB-02
dependency is an ordinary sequencing fact. `ESCALATIONS.md` → `ESC-023`
stays `Open` (partially resolved — see its own 2026-08-13 update) since the
Hermes-reachability question and `REQ-SB-05-US-01`'s own separate open
question remain unanswered. `REVIEW-QUEUE.md` updated accordingly.
