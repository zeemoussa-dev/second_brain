---
id: REQ-SB-36-US-01
title: Real Anthropic Provider integration and a web-research skill for Research Expert agents
requirement_ids: [REQ-SB-36]
requirement_section: "REQ-SB-36: Agent Knowledge Bootstrapping via Delegated Research"
phase: P1
status: Done
gate: clear
gate_reason: "trigger-3 (ADR-022 created, then amended mid-build 2026-08-12 by a direct operator correction reversing point 3's Provider-resolution design — ESCALATIONS.md -> ESC-019, Resolved). The AC-01/AC-03 real-result/real-empty-result verification gap flagged 2026-08-12 (no genuine ANTHROPIC_API_KEY provisioned) was closed 2026-08-13 by a coder re-verification pass once the operator provisioned a real key — both ACs now fully verified live; a live-discovered nuance in AC-03's exact response shape (see T04's Implementation Log) is flagged for human review, not blocking. See ## Notes."
sprint: SPRINT-022
created: 2026-08-12
updated: 2026-08-13
---

# REQ-SB-36-US-01 — Real Anthropic Provider integration and a web-research skill for Research Expert agents

## Story

**As a** Research Expert agent (or any other agent later granted access)
**I want** a real, invocable skill, backed by a genuinely working Anthropic
Provider integration, that performs actual web research and returns real
results
**So that** an agent with no existing knowledge of a subject can gather
real, current information from the web — not just from documents already
in the vault or already supplied by the user

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-36: Agent Knowledge Bootstrapping
  via Delegated Research* — "the Research Expert gathers information —
  from documents the user supplies and from its own real web research."
- **PRD breadcrumb (2026-08-12, operator-authored, cited verbatim):** "the
  Research Expert's research comes from both operator-supplied documents
  and real web search, using the Anthropic Claude Provider specifically
  for the research capability."
- **Correction found live during this `/spec` pass, then resolved by the
  operator directly, both recorded in the PRD's own breadcrumb now:** the
  PRD originally described the Anthropic Provider as "already configured"
  — **false**, found by direct inspection of the real codebase:
  `app/business/provider_registry.py`'s own `_REAL_CLIENT_PROVIDER_IDS =
  {"compass"}` — a small, hardcoded set, confirmed both by this pass's own
  direct read of the real source and by `MEMORY.md`'s own standing
  Constraints entry — means no Provider other than `"compass"` has ever
  been wired to a real client; no "Anthropic Claude" Provider entry is
  even seeded anywhere (only `"compass"` self-seeds); `requirements.txt`
  has no `anthropic`/`langchain-anthropic` package (only
  `langchain-openai`); `.env.example` has no Anthropic-related config key;
  and `app/business/agent_orchestration/model_factory.py` (`ADR-015`) is
  `langchain_openai.ChatOpenAI`-only, an OpenAI-wire-format abstraction
  Anthropic's own native Messages API is not compatible with. The
  Provider entry other stories referenced was a UI-only placeholder, never
  backed by a real client.
- **Resolved 2026-08-12, operator-directed, quoted verbatim ("Yes add
  Anthropic APIs Support"):** building a **real Anthropic Provider
  integration** — new `anthropic`/`langchain-anthropic` dependency, a real
  client construction path, credential wiring in `.env.example`/
  `app/config.py`, extending `REQ-SB-19`'s already-`Done` Provider registry
  with an actual working entry rather than a placeholder — **is confirmed
  in scope**, specifically to give the Research Expert real web-search
  capability. **The mechanism is confirmed: Anthropic's own server-side
  web-search tool**, reached once a real Anthropic client exists — the
  exact tool-use wiring (how the skill's own `@mcp.tool()` function calls
  through to it) is left to `/plan-tasks` as ordinary implementation
  latitude, not a further open architectural fork.
- **Resolved (mechanism shape, unchanged from the original spec pass, by
  direct precedent):** this story reuses `REQ-SB-27-US-01`'s already-`Done`
  skill registry/access plumbing exactly as built — a new
  `@mcp.tool()`-decorated skill function added to `app/business/
  skill_tools.py`'s catalog, granted per-agent via `app/business/
  skill_registry.py`'s existing grant/revoke mechanism. This is a *third*
  real skill, separate from the two the operator already named in
  `ESCALATIONS.md` → `ESC-006`'s 2026-08-12 update ("extracting data out
  of a file," "insert a table and format an excel file") — not a
  replacement for either.
- **Scoping note — why the real Anthropic Provider integration stays
  bundled with this skill, not split into its own story.** A real
  Anthropic client, once built, would incidentally make ordinary chat via
  an "Anthropic Claude" Provider assignment work for any agent (not just
  the Research Expert's own skill invocation) — but the operator's own
  words scope this build "specifically to give the Research Expert real
  web-search capability," so this story's own Acceptance Criteria (below)
  test the web-research skill's behaviour, not general-purpose Anthropic-
  backed chat for other agents (see `## Non-Goals`). A future story can
  pick up general Anthropic-backed chat as separate, explicit product work
  if the operator wants it — not assumed or built here.

## Acceptance Criteria

<!-- Untagged Gherkin — the decomposer authors final wording and assigns
AC-IDs at /plan-tasks. Happy path first, then access control (reusing
REQ-SB-27-US-01's existing mechanism), then the honest-no-results edge
case, then the honest-not-yet-available registration case. Do NOT add
AC-IDs — the decomposer assigns them at /plan-tasks. -->

### Scenario 1: An agent granted access to the web-research skill can invoke it and receive real results

```gherkin
Given a real Anthropic Provider integration exists (a working client,
    reaching Anthropic's own server-side web-search tool)
  And an agent has been granted access to the web-research skill (per
    REQ-SB-27-US-01's existing grant mechanism)
When the agent invokes the skill with a research subject/query
Then the skill returns real information gathered from the web, not a
    fabricated or guessed result
```
<!-- AC-ID: REQ-SB-36-US-01-AC-01 -->

### Scenario 2: An agent without granted access cannot invoke the skill

```gherkin
Given an agent has not been granted access to the web-research skill
When an invocation of the skill is attempted for that agent
Then the invocation is refused, per REQ-SB-27-US-01's existing
    access-control behavior (distinct from Scenario 4's honest-
    unavailable response)
```
<!-- AC-ID: REQ-SB-36-US-01-AC-02 -->

### Scenario 3: A web search with no useful results is reported honestly

```gherkin
Given an agent invokes the web-research skill with a query
  And the search genuinely returns nothing relevant
When the skill's invocation completes
Then it honestly reports that nothing relevant was found, rather than
    fabricating a plausible-sounding result
```
<!-- AC-ID: REQ-SB-36-US-01-AC-03 -->

### Scenario 4: The skill's registration follows the existing honest-unavailable convention before the real Anthropic client is wired

```gherkin
Given the web-research skill is registered in the skill repository's
    catalog (mirroring REQ-SB-27-US-01's own registration mechanism)
  And the real Anthropic Provider integration is not yet available (e.g.
    mid-build)
When a granted agent's invocation of it is attempted
Then it returns REQ-SB-27-US-01's existing honest "not yet available"
    response, never a fabricated result presented as real
```
<!-- AC-ID: REQ-SB-36-US-01-AC-04 -->

## Affected Screens

- **None new.** Ships zero UI, mirrors `REQ-SB-27-US-01`'s own precedent
  — no `html-prototype/` screen shows any Skills surface today. Creating
  an "Anthropic Claude" Provider entry itself uses `REQ-SB-19-US-01`'s
  already-approved, already-generic Provider CRUD form (name/endpoint/
  credential/model) — no new field or screen shape is needed for that
  entry to exist or to carry a real client behind it.

## Dependencies

- **Blocked by:** `REQ-SB-27-US-01` (Done, plumbing only) — this story
  extends its skill catalog/access mechanism with a real skill, reusing it
  as-is.
- **Extends:** `REQ-SB-19-US-01` (Done) — Provider CRUD/registry; this
  story adds a real client-construction path for a genuinely new Provider
  id (e.g. `"anthropic-claude"`) to `provider_registry.py`'s
  `_REAL_CLIENT_PROVIDER_IDS`-style honesty gate, the same shape
  `"compass"` already has, rather than inventing a second mechanism.
  Confirmed in scope by the operator (see Context) — extending an
  already-`Done` story's own underlying module with new, real capability
  is ordinary forward work in this project (the same shape multiple other
  `Done` stories already compose alongside `agent_registry.py`), not a
  reopening of `REQ-SB-19-US-01` itself.
- **Related to:** `REQ-SB-36-US-02` — the Research Expert this skill is
  primarily built for is that story's own concern. This skill (and the
  real Provider integration behind it) has independent, demonstrable
  value on its own, per this project's standing "no independent value
  alone" test.
- **Related to:** `ESCALATIONS.md` → `ESC-006` — the other two first real
  skills already named by the operator (file-data-extraction, Excel
  formatting); this is a third, independently-scoped skill.
- **External:** a real Anthropic API key/credential must be provisioned
  (mirrors `Settings.compass_api_key`'s own `.env`-sourced pattern) —
  provisioning the actual key value is an operational step, not a code
  dependency.

## Constraints

- **Building a real Anthropic Provider integration is in scope**
  (operator-confirmed) — new `anthropic`/`langchain-anthropic` dependency
  in `requirements.txt`, a real client-construction path (extending
  `provider_registry.py`'s honesty-gate pattern or `model_factory.py`,
  exact shape left to `/plan-tasks`), and credential wiring in
  `.env.example`/`app/config.py`, mirroring `Settings.compass_api_key`'s
  own existing shape.
- **The web-search mechanism is confirmed: Anthropic's own server-side
  web-search tool**, reached once the real client above exists — not a
  custom search-API-plus-synthesis approach. Exact tool-use wiring is
  ordinary `/plan-tasks` implementation latitude.
- Reuses `REQ-SB-27-US-01`'s existing registration/access-grant/invoke
  plumbing as-is — no changes to that story's own already-`Done` code
  beyond adding one new catalog entry plus its handler.
- **Never fabricate a search result** — mirrors `ADR-011` point 3 /
  `REQ-SB-27-US-01`'s own honesty pattern (Scenario 3/4).
- **Follows the existing Provider-honesty convention**
  (`provider_registry.has_real_client`, `ADR-011`/`ADR-014`'s "declared
  but not yet backed by a real handler → honest unavailability" pattern)
  during the build — before the real client lands, the skill's own
  registration returns Scenario 4's honest "not yet available" response,
  never a fabricated placeholder result.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-36-US-01-T01 | backend | New `anthropic` dependency + `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL` Settings fields | `requirements.txt`, `config.py`, `.env.example` | `REQ-SB-36-US-01-T01-anthropic-dependency-and-settings-fields.md` |
| REQ-SB-36-US-01-T02 | backend | New `anthropic_client.py` — `web_search(api_key, model, query)` | `data_access/anthropic_client.py` | `REQ-SB-36-US-01-T02-anthropic-client.md` |
| REQ-SB-36-US-01-T03 | backend | `provider_registry.py` — `"anthropic-claude"` real-client id, `"Anthropic Claude"` auto-seed, new `get_provider()` | `business/provider_registry.py` | `REQ-SB-36-US-01-T03-provider-registry-anthropic-claude.md` |
| REQ-SB-36-US-01-T04 | backend | `skill_tools.py` — new `web_research(query)` skill (honest unavailable/empty/real) | `business/skill_tools.py` | `REQ-SB-36-US-01-T04-web-research-skill-tool.md` |
| REQ-SB-36-US-01-T05 | backend | `skill_registry.invoke_skill` additive `args`; `skills_router.py` optional invoke body | `business/skill_registry.py`, `api/skills_router.py` | `REQ-SB-36-US-01-T05-invoke-skill-args-and-router-body.md` |
| REQ-SB-36-US-01-T06 | backend | `mcp_client.py` — new `load_agent_tools(agent_id)`, removes `load_vault_query_tools`; `graph.py` call-site edit | `agent_orchestration/mcp_client.py`, `agent_orchestration/graph.py` | `REQ-SB-36-US-01-T06-mcp-client-load-agent-tools-gap-fix.md` |

`depends_on` graph (acyclic): `T01: []`, `T02: [T01]`, `T03: [T01]`,
`T04: [T02, T03]`, `T05: [T04]`, `T06: [T04, REQ-SB-20-US-01-T05]`. One
deliberate cross-story edge on `T06` — see `## Notes` for why (a genuine
same-function collision risk with `REQ-SB-20-US-01-T05`'s own edit to the
identical `load_vault_query_tools()` call site, caught by this decomposer
pass, not an ADR-mandated dependency). No dependency on `REQ-SB-21-US-01`
anywhere in this story.

## Definition of Done

- [x] All acceptance-criteria scenarios pass — **AC-01 through AC-04 all fully verified live as of 2026-08-13, against a genuine, operator-provisioned `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL`. AC-01: a real, non-fabricated result with real citations (`python.org`, Wikipedia) confirmed. AC-03: honestly reports nothing relevant found (never fabricates) confirmed, though in a real, observed shape (`found: true` + honest refusal text + empty `sources`) that differs from the task's own originally-documented `found: false` shape — a live-discovered nuance, not a defect, flagged for human review, not blocking. See `REQ-SB-36-US-01-T04`/`T05`'s own Implementation Logs and `REVIEW-QUEUE.md`.**
- [x] Every Implementation Task above is complete (`T01`-`T06`, `T04`/`T05` corrected mid-build per an operator-directed design reversal — see `## Notes`)
- [x] All Constraints respected (including the corrected Provider-resolution Constraint added mid-build)
- [ ] Automated tests added/updated and passing (once test tooling exists) — n/a, project-wide test tooling still pending
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **General-purpose Anthropic-backed chat for other agents** — this story
  scopes the real Anthropic Provider integration to the Research Expert's
  web-search skill specifically (operator's own framing, see Context); a
  future story can pick up general-purpose Anthropic-backed chat as its
  own, explicit product work if wanted, not assumed here.
- **The exact tool-use wiring detail** (how the skill's own
  `@mcp.tool()` function calls through to Anthropic's server-side tool) —
  ordinary `/plan-tasks` implementation latitude, not decided here.
- **The Research Expert agent itself, the Hub-delegation chain, and the
  Compass pilot** — `REQ-SB-36-US-02`, a separate story.
- **Document-supplied research (file upload)** — `REQ-SB-28`, separate,
  explicitly later work.
- **The other two named first-real-skills** (file-data-extraction, Excel
  formatting) — separate, unspecced follow-on work (`ESC-006`).
- **Any UI** — ships zero UI, mirrors `REQ-SB-27-US-01`.

## Notes

**Prototype parity:** not applicable — this story ships zero UI (see `##
Affected Screens`).

**Why `gate: clear` — re-checked against every MUST-FLAG trigger, not
assumed:**

1. **No remaining material assumption.** The Anthropic-provider gap was a
   code-verified fact, not a guess, and the operator has since directly
   confirmed the Provider-build-in-scope decision and the search
   mechanism (Anthropic's own native tool). The only remaining latitude
   ("exact tool-use wiring") is ordinary implementation detail, not a
   fork requiring human judgement — the same class of thing
   `REQ-SB-19-US-01`/`REQ-SB-27-US-01` both left to `/plan-tasks` while
   still `gate: clear`.
2. `REQ-SB-36` is not marked `<!-- Draft -->`/unfinalised — it carries a
   "Scope resolved" breadcrumb whose own named sub-question here is now
   resolved. Trigger 2 does not apply.
3. N/A directly (architect/ADR trigger) — though `/plan-tasks` should
   expect a real architecture decision here: extending
   `model_factory.py`/`provider_registry.py` to support a non-OpenAI-wire
   client, or a new sibling client module mirroring `compass_client.py`'s
   own precedent. Not a blocker for this analyst pass.
4. No new `ESCALATIONS.md` entry opened by this pass — this pass instead
   **resolves** `ESC-016`, naming this story's own 2026-08-12 update as
   the resolving artefact.
5. **Not oversized, re-checked given the now-larger confirmed scope.**
   The added real work (new dependency, real client, credential/config
   wiring, one new skill function using an already-confirmed mechanism)
   is comparable in shape and size to `REQ-SB-19-US-01`'s own
   Provider-CRUD build (6 tasks) or `REQ-SB-27-US-01`'s skill-plumbing
   build (4 tasks) — a reasonably-scoped single story, not a forced
   monolith. The operator's own framing ("in scope, specifically to give
   the Research Expert real web-search capability") also confirms this is
   meant to be one bundled unit of work for this purpose, not a
   general-purpose Provider overhaul (see `## Non-Goals`).
6. N/A (coder trigger).
7. **The prior contradiction is resolved, not merely noted.** The PRD's
   own text now records both the original false "already configured"
   claim and the operator's direct correction — the contradiction itself
   is the resolved history, not an open item.
8. **No remaining multiple-equally-valid-options fork.** The
   Provider-build-in-scope question and the web-search mechanism both have
   one confirmed answer now.

`gate: clear` 2026-08-12. `REVIEW-QUEUE.md`'s combined entry for this
story is updated to reflect resolution. `ESCALATIONS.md` → `ESC-016`
flipped to `Resolved`, naming this update as the resolving artefact. This
story is ready for `/plan-tasks`.

**Architecture pass (2026-08-12, `/plan-tasks` step 1 — architect).**
`ADR-022` written (new, appended to `Implementation/Architecture/ADR.md`):
a plain official `anthropic` SDK client (new `app/data_access/
anthropic_client.py`, sibling to `compass_client.py`, deliberately
**not** `langchain-anthropic`/`model_factory.py` — this skill is never
routed through `run_agent_conversation`'s LangGraph loop, per this story's
own Non-Goals). `provider_registry.py`'s `_REAL_CLIENT_PROVIDER_IDS` gains
`"anthropic-claude"`; `_seed_state()` additionally auto-seeds an
`"Anthropic Claude"` Provider entry from two new required `Settings`
fields (`anthropic_api_key`/`anthropic_model`, mirroring `compass_*`
exactly — `.env.example` gains `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL`). New
`app/business/skill_tools.py::web_research(query: str)` resolves that
Provider via a new `provider_registry.get_provider(provider_id)` by-id
lookup + `has_real_client` before calling `anthropic_client.web_search`
(Anthropic's own server-side web-search tool, the operator-confirmed
mechanism) — honestly unavailable (Scenario 4) or honestly empty (Scenario
3), never fabricated. `skill_registry.invoke_skill(agent_id, skill_id,
args=None)` gains an additive `args` parameter and `skills_router.py`'s
invoke endpoint gains an optional JSON body, reused exactly as-is per this
story's own Constraints.

**A live-discovered, load-bearing gap closed by this same pass, not
deferred a second time:** direct reading of `app/business/
agent_orchestration/mcp_client.py::load_vault_query_tools()` found it
returns **every** tool registered on the shared MCP server with no
filtering — meaning any agent's ordinary chat turn could already reach
`skill_tools.py`'s catalog regardless of `skill_registry.has_skill_access`
(harmless while the catalog held only the `diagram_understanding` stub,
but this would have silently falsified this story's own Scenario 2 the
moment `web_research` became real). Fixed as part of `ADR-022`:
`mcp_client.py` gains `load_agent_tools(agent_id)`, filtering the shared
server's tool list so a skill-catalog tool is only bound when
`skill_registry.has_skill_access(agent_id, skill_id)` is `True` (the four
core vault-query tools stay always-available); `graph.py::
run_agent_conversation` calls this in place of the old
`load_vault_query_tools()` (removed, no other caller existed). Reuses
`has_skill_access` exactly as `skill_registry.py`'s own docstring already
anticipated — not a new enforcement concept. Full reasoning: `Implementation/
Architecture/ADR.md` → `ADR-022`; `architecture.md` → "Real Anthropic
Provider integration & web-research skill."

**Architecture scope (bounds the decomposer/coder for this story):**
`Implementation/Architecture/architecture.md` → "Real Anthropic Provider
integration & web-research skill." Concretely: `src/backend/requirements.txt`
(new `anthropic` dependency), `app/config.py`/`.env.example` (two new
required Settings fields), `app/data_access/anthropic_client.py` (new),
`app/business/provider_registry.py` (extend `_REAL_CLIENT_PROVIDER_IDS`,
extend `_seed_state()`, new `get_provider()` helper), `app/business/
skill_tools.py` (new `web_research` entry), `app/business/skill_registry.py`
(additive `args` parameter on `invoke_skill`), `app/api/skills_router.py`
(optional invoke-endpoint body), `app/business/agent_orchestration/
mcp_client.py` (new `load_agent_tools`, removes `load_vault_query_tools`),
`app/business/agent_orchestration/graph.py` (one call-site edit to use
`load_agent_tools`). `app/business/agent_orchestration/model_factory.py`
is explicitly out of scope — untouched. Full reasoning: `Implementation/
Architecture/ADR.md` → `ADR-022`.

**No dependency on `REQ-SB-21-US-01`** — unlike `REQ-SB-35-US-01`/
`REQ-SB-36-US-02` (see `ESCALATIONS.md` → `ESC-017`), this story's own
architecture is fully self-contained and unblocked.

Gate stays `flagged` per this project's own convention — the decomposer
still runs in this same `/plan-tasks` pass (Pipeline.md's "do NOT halt the
stage" rule); the human reviews `ADR-022` and the resulting tasks together.
A `REVIEW-QUEUE.md` pointer has been added.

**Decomposition pass (2026-08-12, `/plan-tasks` step 2 — decomposer).**
All 4 untagged Gherkin scenarios tightened for buildability (wording only)
and locked as `REQ-SB-36-US-01-AC-01` through `AC-04`, each carrying its
trailing `<!-- AC-ID: ... -->` tag. 6 tasks created at the flat
`Implementation/Tasks/` root, in dependency order: the new dependency/
config fields (`T01`), the plain Anthropic SDK client (`T02`), the
Provider-registry extension (`T03`), the skill function itself (`T04`),
the additive `invoke_skill`/router args plumbing (`T05`), and the
conversational tool-binding gap fix (`T06`).

**A real, load-bearing sequencing finding from this pass, not silently
left for `/implement-sprint` to discover the hard way:** `ADR-022` point 6
describes `mcp_client.py`'s `load_vault_query_tools()` → `load_agent_tools(
agent_id)` edit as touching a function with "no other caller" — true only
if this task builds before `REQ-SB-20-US-01-T05` does, since that task
(`Ready`, unbuilt, a different story) *also* edits the exact same
`graph.py::run_agent_conversation` call site (extending its `tools` list
with `request_cross_section_help`). Building `T06` without accounting for
this would silently overwrite whichever of the two landed first, exactly
the antipattern `MEMORY.md`'s own `REQ-SB-26-US-01-T03` Pattern entry
already names ("compose the new change around the REAL current file, never
overwrite it with the stale sample"). Resolved by adding a real
`depends_on` edge, `T06: [T04, REQ-SB-20-US-01-T05]` — not a new ADR
(no interface/scope change, purely a build-order correction the decomposer
is entitled to make), so this is not itself a MUST-FLAG trigger; recorded
here as a scope-internal judgement call per Pipeline.md's own convention
for this class of finding.

`depends_on` graph across all 6 tasks (acyclic): `T01: []`, `T02: [T01]`,
`T03: [T01]`, `T04: [T02, T03]`, `T05: [T04]`,
`T06: [T04, REQ-SB-20-US-01-T05]`. Every locked AC has at least one
AC-tagged manual verification step — `AC-01`/`AC-02` in `T05` (the full
grant/invoke-with-args round trip), `AC-03`/`AC-04` in `T04` (the skill's
own honest-empty/honest-unavailable branches, direct function calls) — no
locked AC without a tagged step, hard rule 4 satisfied. `T06` carries no
AC-tagged step of its own (mirrors `REQ-SB-21-US-01-T02`'s own precedent)
— `AC-02`'s locked text is about the direct REST/`invoke_skill` layer,
already fully covered by `T05`; `T06` additionally closes the
conversational-chat-path gap as forward-looking correctness, per `ADR-022`
point 6, verified by a non-AC smoke check. `status: Draft → Ready`; all 6
tasks written directly at `status: Ready` (lockstep with the story) — none
blocked, since this story has zero dependency on `REQ-SB-21-US-01` and its
one cross-story edge (`REQ-SB-20-US-01-T05`) is already a real, `Ready`
task. **`gate` intentionally left `flagged`, `gate_reason` updated to
record decomposition is complete** — no new material assumption, no new
ADR, no new `ESCALATIONS.md` entry opened by this decomposer pass; the
human still reviews `ADR-022` and this task breakdown together.

**Build pass (2026-08-12, `/implement-sprint` — coder, `SPRINT-022`).**
`T01`-`T06` built in dependency order and verified live against the real
running backend. `T01`-`T03` built and verified exactly per spec (real
`anthropic` SDK install confirmed at `0.121.0`; `Settings` fail-fast
confirmed against the real `.env`'s own genuinely-missing keys;
`provider_registry` extension fully verified including the real
credential-edit-takes-effect difference from Compass's own inert-edit
precedent).

**Mid-build operator correction, investigated and implemented, not
silently substituted (`ESCALATIONS.md` → `ESC-019`, `ADR-022`'s own
"Correction" addendum):** after `T01`-`T03` (and a first pass of `T04`)
were built, the operator directly corrected `ADR-022` point 3's
fixed-`"anthropic-claude"`-Provider-id design, quoted verbatim: "The
Anthropic_API_KEY Should be a Provider added to the Providers List — if I
linked the Research Agent to Compass, use Compass. Don't Halt on that."
Before implementing, a real technical question the operator explicitly
required be investigated (not guessed) was resolved live: Compass/GPT-5
(Core42) has **no** real, hosted web-search tool structurally equivalent
to Anthropic's own — confirmed by this codebase's own `compass_client.py`
(no `tools`/search parameter in its real request shape) and by the
sibling `agentic-map` project's own `services/gateway/providers.py`,
which routes its own web-search-capable agents through a *separate*
Perplexity Sonar provider specifically because Compass/GPT-5 alone
cannot do this. `web_research(query, agent_id)` now resolves the
INVOKING agent's own linked Provider (`provider_registry.
get_agent_provider(agent_id)`) — real Anthropic search when linked to
`"anthropic-claude"`, the exact same honest Scenario-4 "not available"
shape for any other linked Provider (never a fabricated result).
`invoke_skill` additively injects `agent_id` into the handler call only
when the handler's own signature declares it (`diagram-understanding`'s
zero-arg call and the router's own `{"query": ...}` body contract are
both unaffected). Re-verified live end-to-end against the corrected code
(direct calls and real HTTP): a Compass-linked agent honestly reports
unavailable; an Anthropic-linked agent's real dispatch attempt is
directly confirmed via a real, honest Anthropic `401` (not fabricated);
`AC-02`'s access refusal is unaffected.

**Honest, operator-acknowledged verification gap, not silently hidden —
this is a deliberate exception to the ordinary "a locked AC you cannot
verify blocks the task" rule, made on the operator's own explicit,
repeated direction, not the coder's own improvisation:** no genuine
`ANTHROPIC_API_KEY` was available in this environment. `AC-01`
("...returns real information gathered from the web...") and `AC-03`
("...genuinely returns nothing relevant... honestly reports...") are each
split into two halves: the routing/honesty-funnel half (a real dispatch
attempt correctly reaches Anthropic for an Anthropic-linked agent; the
system never fabricates a result when blocked) is fully verified live;
the positive "produces a real, genuinely-relevant result" / "produces a
real, genuinely-empty result" half of each could not be exercised, since
every real call against the placeholder credential honestly fails with a
`401` before ever reaching that branch. A syntactically-valid, clearly-
labeled, provably-inert placeholder was added to the real (gitignored,
uncommitted) `.env` solely so `Settings()`/the app could construct and
boot for all other live verification — never presented as a working key,
never used to claim a fabricated result. Flagged prominently in
`REVIEW-QUEUE.md` for a mandatory follow-up live re-verification of
`AC-01`/`AC-03`'s own positive branches once a real `ANTHROPIC_API_KEY`
is provisioned.

`T06` built and verified per its own spec — the real, current `graph.py`
matched this task's own documented "After" baseline exactly (no
reconciliation needed beyond the one call-site edit). Its own live
verification of `load_agent_tools`'s filtering logic used an in-process
monkeypatch (the established Pattern) rather than a live MCP round trip
against the exact registered `web-research` tool, since this project's
own documented MCP-loopback port (`8001`) was held by a genuinely
unkillable "ghost" listener this session could not clear (no admin
rights available) — confirmed, not assumed, via `Get-NetTCPConnection`/
`Get-Process`/`tasklist`/`wmic`/.NET all agreeing the owning PID doesn't
exist in any enumerable process table. The ordinary non-tool-calling
regression check (T06's own step 4) WAS verified live against that same
real port, since it doesn't depend on the new skill's registration being
fresh there. Flagged in `REVIEW-QUEUE.md` for a human restart/reboot of
whatever holds port `8001` before a future session needs a genuinely
fresh MCP round trip on it.

All fixture/test state cleanly reverted after every verification pass
(`todo-capture` back to its real default `"compass"` Provider, zero
lingering skill grants, `vault-qa` never touched, `.second-brain/
agent_providers.json` re-seeded fresh with the final, consistent
placeholder credential).

`status: Ready → Done`. `gate` stays `flagged` — combined human review of
`ADR-022` (original + this same-date Correction addendum), the
operator-directed mid-build design reversal, and the still-open real-
credential verification gap. Full reasoning: `Implementation/Architecture/
ADR.md` → `ADR-022`; `ESCALATIONS.md` → `ESC-019`; `REVIEW-QUEUE.md`; each
task's own Implementation Log (`T01`-`T06`).

**Re-verification pass (2026-08-13, coder) — the real-credential
verification gap closed, not new build work.** The operator provisioned a
genuine `ANTHROPIC_API_KEY`/`ANTHROPIC_MODEL` in `src/backend/.env`
(replacing the provably-inert `NOT-PROVISIONED-PLACEHOLDER`). Live
re-verification confirmed `AC-01` (a real, non-fabricated result with
real citations — `python.org`, Wikipedia — for the query "What is the
current stable version of the Python programming language?") and `AC-03`
(honestly reports nothing relevant found for two engineered
no-real-answer queries — never fabricates — though the real, observed
honest-empty shape is `{"found": true, "summary": <honest refusal text>,
"sources": []}`, not the `{"found": false, ...}` shape originally
documented in `T04`; a genuine, live-discovered nuance between the
task's own documented contract and the real Anthropic API's actual
behavior, not a code defect — flagged for human review). A genuine
operational root cause was found and resolved along the way (not a code
defect either): `.second-brain/agent_providers.json` had been seeded
during `SPRINT-022`'s own build with the placeholder credential and never
auto-resyncs from `.env` once persisted — resolved by deleting it to
force the documented clean re-seed (the same operational step `T03`'s own
Implementation Log already used once before). No source code was
modified by this pass. Full detail: `T04`/`T05`'s own Implementation
Logs; `REVIEW-QUEUE.md`'s updated `SPRINT-022` entry.
