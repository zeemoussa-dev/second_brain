# Architecture Decision Records

Append-only log of architectural decisions. One ADR per decision, numbered
sequentially from ADR-001.

**Never edit an accepted ADR.** A change of mind is a new superseding ADR (linked
both ways). Status enum: `Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-XXX`.

**Alternatives Considered is mandatory** on every ADR.

**2026-08-20:** Numbering restarts at ADR-001 alongside the backend
architecture redesign (`Implementation/Plans/2026-08-20-backend-
architecture-redesign.md`). The prior sequence (ADR-001 through ADR-058)
is archived, not deleted — see `Documentation-Archive-2026-08-20/
Implementation/Architecture/ADR.md`. ADR-001 below is the one entry
carried forward unchanged in substance (originally ADR-059 in the archived
sequence) — it's the founding decision this whole redesign executes, not
legacy history.

<!-- ADR format:
## ADR-001: [Short title]
**Status:** Accepted
**Date:** YYYY-MM-DD
**Context:** Why this decision was needed — the forces at play.
**Decision:** What was decided and why.
**Alternatives Considered:** Other options evaluated (mandatory field).
**Consequences:** Trade-offs, implications, and future considerations.
---
-->

## ADR-001: Hermes becomes the agent/skill/schedule/approval runtime; Second Brain's backend narrows to a data layer of Tools/Skills - first step (router archive + Hermes REST client scaffold) landed, business-layer split deferred

**Status:** Accepted
**Date:** 2026-08-20
**Originally recorded as:** ADR-059 in the archived pre-2026-08-20 sequence
(`Documentation-Archive-2026-08-20/Implementation/Architecture/ADR.md`).

**Context:** A rapid, cascading sequence of real, live-discovered
data-quality incidents (BUG-031/032/033, a Partner-vs-Customer OKF
directory-shape asymmetry the codebase had never disclosed, a full
Customer/Partner tag revert across the real vault) led the operator to call
a full stop on the hand-built Agent/Skill/Schedule machinery and reassess
from first principles. A direct challenge -- "why are you editing code to
put a schedule?" -- surfaced that most of that machinery (default
schedules, per-agent scheduling, Skill grants) had been hand-written where
a declarative or platform-native mechanism would have served, prompting
"we are building a framework, this is not acceptable." Research into this
codebase's own already-present dependencies (`langgraph>=1,<2`, used only
for the in-app chat loop at the time) and into Hermes (previously
described in `CLAUDE.md` only as "an MCP-based multi-channel communication
tool," https://github.com/nousresearch/hermes-agent) found Hermes to be a
full, substantial agent framework: subagent spawning, a self-improvement
loop, a natural-language cron scheduler, Honcho-based memory, 40+ tools,
MCP client/server integration, a 25+-platform multi-channel gateway, and,
critically, a real, documented REST API gateway (`hermes gateway`, default
`127.0.0.1:8642`, bearer-token auth) exposing chat/completions, runs (with
SSE events), jobs (full CRUD, the real schedule-management surface),
sessions, skills, and toolsets.

**Decision:** Hermes replaces Second Brain's own hand-built Agent/Skill/
Schedule/Approval orchestration layer as the agent runtime. LangGraph's
role narrows to an execution engine usable *within* a task (Second Brain's
own remaining use, or something Hermes itself invokes) rather than the
orchestration layer itself -- no change to `langgraph`'s pin, only to what
calls it. Second Brain's own web UI stays the PRIMARY frontend (Hermes is
consumed as a backend, not a UI replacement); extra channels (chat, other
platforms) run through Hermes' own gateway instead. Second Brain's backend
narrows to a "data layer": vault capture/indexing, Outlook, and vault
read/write, organized as discrete Tools (Outlook, Housekeeping, Vault,
Vault Write, Company/Partner, People, Vault Admin) each exposing
individually-callable Skills -- consumed both by Second Brain's own
narrowed LangGraph use and by Hermes' external orchestration, over the
existing shared `/mcp` mount.

First concrete step, taken the same night as this decision (autonomous
session, operator asleep, explicit instruction to proceed): archived the 9
now-dead orchestration-layer HTTP routers (`agents_router`, `agent_
schedules_router`, `agent_activity_router`, `cockpit_router`, `demo_
taxonomy_router`, `pending_approvals_router`, `providers_router`,
`sections_router`, `skills_router` -- moved to `src/backend/app/_archive/
api/`, not deleted) and added a real, structurally sound Hermes REST
client (`data_access/hermes_client.py`) plus a thin status router mounted
at `/hermes/*` (`business/hermes_status.py`, `api/hermes_router.py`) --
honestly "unreachable" until a real Hermes gateway is configured, never a
fabricated response. Verified live: the backend imports and boots cleanly,
answers `/health`/`/system-health`/`/hermes/health`, and the capture
scheduler's own jobs still register exactly as before.

Second concrete step (2026-08-20, same day, collaborative session): began
a full backend architecture redesign with the operator acting as Architect
+ Business Analyst together -- see `Implementation/Plans/2026-08-20-
backend-architecture-redesign.md` for the block-by-block working log
(Data Access layer split into Vault/System, Business layer split into
logic/vault/core/hermes/langgraph, API layer confirmed to need no
restructuring). That document is the live source of truth for this
redesign's progress; this ADR is not updated play-by-play as it proceeds.

**Deliberately NOT done in the first step** -- archiving the underlying
business-layer registries (`agent_registry`, `agent_schedule_registry`,
`skill_registry`, `skill_tools`, `pending_approval_registry`, `working_
mode_registry`, `provider_registry`, `section_registry`, `scope_registry`/
`scope_query_tools`, `agent_prompts`, `agent_orchestration/`, `cockpit/`)
and splitting `librarian_housekeeping.py`/`vault_filing_expert.py` into
the confirmed Tool/Skill grouping. Real, live dependents were found by
tracing actual imports (not the original file-classification list alone):
`capture_scheduler.py`'s hourly Outlook pull and `mcp_server.py`'s own
tool-registration chain both run through `agent_schedule_registry`/`skill_
tools`; `vault_write_tools.py`'s write-approval safety gate (every
Hermes-triggered write proposal is unconditionally gated behind a Pending
Approval) depends on `agent_registry`/`pending_approval_registry`; and
`librarian_housekeeping.py`'s Company Review pipeline has real, unresolved
Pending Approvals awaiting the operator's own review (BUG-032). This split
also depends on an explicitly still-open question this ADR does NOT
resolve: does Hermes' own run-approval mechanism replace `pending_
approval_registry`/`working_mode_registry` outright, or does Second Brain
keep its own write-approval gate regardless of trigger source? Tracked as
an open question in the 2026-08-20 architecture redesign plan doc above,
not resolved here.

**Alternatives Considered:** (1) Delete the whole existing orchestration
layer immediately and rebuild from a clean slate, as the operator's own
first framing floated -- rejected in favor of the narrower "keep the data
layer, archive the orchestration layer" scope the operator settled on
after discussion, since the data layer (vault capture/indexing, real
Outlook integration, Company/Partner/People business logic) represents
most of this codebase's real, hard-won value and has no Hermes equivalent
to replace it with. (2) Archive the full business-layer registry set in
the same first step, accepting the risk -- rejected: several of those
registries are load-bearing for live, currently-running functionality
(Outlook capture, the MCP tool surface, the write-approval gate) with no
tested Hermes-side replacement deployed yet, and breaking any of them
unsupervised while the operator slept was judged an unacceptable risk
relative to the value of finishing the split one night sooner. (3) Leave
the dead routers in place until the full business-layer split is ready,
doing everything in one pass -- rejected: the routers are provably dead
(no other module imports a router file, confirmed by grep) and their own
frontend surface is already gone in practice once Hermes is the intended
runtime, so archiving them was low-risk, real progress that did not need
to wait on the harder, higher-risk decision.

**Consequences:** The frontend (Agents Map, Cockpit, Skills Tree, the
agent-creation wizard, the Pending Approvals UI) now calls 9 dead
endpoints and will 404 until that surface is either rebuilt against Hermes
or retired -- not addressed by this ADR, tracked in the architecture
redesign plan doc. `CLAUDE.md`'s own description of Hermes as "an
MCP-based multi-channel communication tool" is now known to be a
significant understatement and should be corrected once the fuller
integration shape is settled. No Hermes gateway is deployed yet --
`hermes_client.py`'s callers all degrade to an honest "unreachable" result
today, by design, not a defect.

---

## ADR-002: The email-thread-capture pipeline is Hermes-native (standalone scripts in the Skill's own folder) -- no MCP server, no Second Brain backend dependency

**Status:** Accepted
**Date:** 2026-08-21

**Context:** ADR-001 established Second Brain's data layer as Tools/
Categories/Actions exposed to Hermes over MCP -- the `outlook` and `vault`
Tools built for the vault-rebuild pipeline (`ingest_email`, `rename_
thread`, `link_person_to_thread`, `capture_attachments`, `capture_file_
link`, `list_recent_emails`) were the first real instance of this
pattern. Operator, live: "In the skills folder we can add the Python
file, why do we need our MCP Server?", then, after pushback, "I don't
need MCP Server, I think Hermes will pull the dependencies of the Py file
when needed, try that" -- backed by a real observation: "When I sent a
file to WhatsApp, Hermes pulled a library to read the file. I want our
Skills to be the same, fully hosted in Hermes, no use of our venv."

Investigated two real Hermes-agent source files before answering:
`tools/code_execution_tool.py` (the `terminal`/code-execution tool's
child-Python resolution uses whatever `VIRTUAL_ENV` is already active on
Hermes' own process, never auto-discovers a project's own `.venv`) and
`tools/lazy_deps.py` (a closed allowlist -- `LAZY_DEPS` -- of Hermes' own
known built-in features mapped to exact pip specs, auto-installed into
Hermes' own venv the first time that *specific, already-registered*
feature is used; this is what actually fired for the WhatsApp file, e.g.
`tool.doc_extract` -> `firecrawl-anydoc`). Initial conclusion: this
explains the observation but doesn't generalize -- arbitrary packages
like `pywin32` aren't in the allowlist, and Second Brain's own private
`app.business.logic.*` modules were never pip packages at all, so
`lazy_deps.py` alone couldn't make a Hermes-native script self-sufficient.

Operator pushed further: "So apparently you can tell the skill.md to
install the required python libraries before running the py file, check
that." Verified against Hermes' own bundled skill-authoring guide
(`skills/software-development/hermes-agent-skill-authoring/SKILL.md`):
the standard SKILL.md body includes a documented `## Prerequisites`
section ("exact env vars, installs, API key sourcing") and `## How to
Run` ("canonical invocation through the `terminal` tool") -- meaning a
Skill can simply instruct the agent to run `terminal(command="pip
install pywin32")` as an explicit step. This is real, standard, and
unrestricted (no allowlist, unlike `lazy_deps.py`) -- it fully resolves
the third-party-dependency half of the objection. It does nothing for the
second half: Second Brain's own business-logic code still isn't
pip-installable, so "fully hosted in Hermes" still requires either
duplicating that code into the Skill's own files or wiring `sys.path`
into `src/backend` (pulling in FastAPI/pydantic and the rest of that
dependency chain, plus importing code that assumes it's running inside
the app's own context).

Porting the actual dependency chain surfaced a real scope finding:
`link_person_to_thread`'s Person-note creation doesn't just write a bare
note -- it drags in Second Brain's full company/Customer/Partner matching
and hub-linking system (`people_extraction.py` 356 lines, `customer_hub_
linking.py` 98, `partner_hub_linking.py` 184; ~640 lines beyond `vault_
writer.py` itself).

**Decision:** Duplicate, not wire -- Option 1. The 5 vault-rebuild
Actions plus the Outlook fetch are reimplemented as 8 standalone,
stdlib-plus-pywin32-only Python files living directly in the Skill's own
`scripts/` folder (`Hermes-Provisioning/skills/vault-rebuild/email-
thread-capture/scripts/`, mirrored at `<hermes_home>/skills/vault-
rebuild/email-thread-capture/scripts/`): `vault_lib.py`, `outlook_lib.py`,
and one CLI entry point per Action, each invoked through the `terminal`
tool per the SKILL.md's own rewritten Procedure. No MCP server, no
Second Brain backend process involved in running this pipeline at all.

Scope, per two explicit operator decisions during this same session:

1. **Old code removed, not kept in parallel** (not "keep both as a
   fallback") -- the 6 ported source files, the `vault` Tool's entire
   registry.json entry, and `list_recent_emails` from the `outlook` Tool
   were deleted from Second Brain's backend once the ported scripts were
   verified working end-to-end (idempotency, rename fan-out, participant
   links, bare Person-note dedup -- all smoke-tested against a scratch
   vault before deletion). Single source of truth is now the Skill's own
   `scripts/` folder; the old MCP-based code is not preserved anywhere as
   a fallback.
2. **Person-note creation is deliberately trimmed, not fully ported**
   (operator: "one simple task, we didn't start the process of Enriching
   data yet") -- `vault_lib.ensure_bare_person_note` creates/tops-up a
   bare name+email Person note only, with NO company derivation or
   Customer/Partner matching/hub-linking. That ~640-line system stays
   Second Brain-only, run later as a separate whole-vault pass via the
   backend's own already-existing `retrofit_people_from_emails()` job --
   never duplicated into Hermes.

Binary attachment content can't cross a `terminal`-tool subprocess
boundary as an in-memory Python object the way it could inside one
shared MCP-server process -- `outlook_lib.py`'s own `_extract_attachments`
now saves each real attachment to a durable OS temp file and returns its
path (never deletes it immediately, unlike the source it was ported
from); `capture_attachments.py` reads the bytes back from that path and
deletes it once written into the vault. Large payloads (email bodies up
to 50,000 chars, an email's full attachments array) are handed to
`ingest_email.py`/`capture_attachments.py` via `--input-file <path>`
(the agent `write_file`s a scratch JSON file first) rather than as CLI
arguments, to stay well clear of shell command-line length limits; short
scalar fields (conversation_id, sender name/email, a URL) stay plain CLI
flags for readability in the SKILL.md's own Quick Reference.

**Alternatives Considered:** (1) Keep the MCP server (ADR-001's original
shape) -- rejected once the `terminal`-tool pip-install path closed the
dependency-install gap that was the strongest argument for it; an extra
backend process and MCP transport add real operational surface (a port,
a running FastAPI process, MCP session-manager lifespan wiring already
bug-prone once this session, see the architecture redesign plan doc's
own "MCP server session_manager never initialized" entry) for no
remaining benefit specific to this one pipeline. (2) `sys.path`-wire the
Hermes script directly into `src/backend` and import `app.business.
logic.*` unmodified -- rejected: still needs `pywin32` installed via the
same `terminal`-tool step, ADDITIONALLY needs FastAPI/pydantic/the rest
of `app/`'s own dependency chain installed into Hermes' environment for
no benefit (this pipeline needs none of what FastAPI provides), and ties
a Hermes-hosted script to Second Brain's own on-disk repo layout as an
implicit, easily-broken contract. (3) Full-fidelity Person-note porting
(company match + hub-linking, ~640 lines) -- rejected for Capture-phase
scope reasons (operator's own "we didn't start the process of Enriching
data yet"), not a technical blocker; the code could be ported later if
the operator decides Capture-time enrichment is actually wanted.

**Consequences:** The vault-rebuild pipeline has zero runtime dependency
on Second Brain's backend being up at all -- Outlook desktop + Hermes +
`pywin32` is the complete requirement set. Person notes this pipeline
creates carry no company/Customer/Partner linkage until `retrofit_people_
from_emails()` is run afterward as a separate pass -- a real, deliberate
gap during Capture, not a bug. The `outlook` MCP Tool registration
(`mcp-servers/outlook.yaml`) now exposes only `gather_emails`, which
nothing actually calls over MCP (it's Second Brain's own internal
`capture_scheduler.py` pull, a direct Python call) -- flagged to the
operator as possibly ready for `hermes mcp remove outlook`, not removed
unilaterally since removing a live Hermes registration is a different
class of action than editing this repo's own files. `vault_lib.py`/
`outlook_lib.py` are now a second, independent copy of vault-writing/
Outlook-reading logic (the Skill's own, separate from Second Brain's
`app.data_access.vault_writer`/`outlook_com`) -- an accepted, disclosed
duplication per Decision 1 above, not an oversight; a future bugfix to
either copy's shared logic (e.g. `raw_message_note_path`'s collision
handling) must be applied to both by hand, since nothing keeps them in
sync automatically.

---

## ADR-003: A view-only, live-read mirror of Hermes' real Agent/Skill definitions is a scoped exception to ADR-001's "not ours to own" principle -- display only, no data-access layer, no local persistence

**Status:** Accepted
**Date:** 2026-08-22

**Context:** This session's Hermes-side work (built entirely as external
provisioning outside this repo's own pipeline -- profiles `opp-manager`,
`notes-manager`, `files-manager`, each with real SOUL.md/config.yaml/
Skills) produced a real foundation the operator now wants reflected in
Second Brain's own UI: "Time to move those Agents into our Original
Backend... we need to build our Schema in our backend to match what we
did in Hermes and Mark those Agents and Skills with Hermes... We Build the
backend for View Only now." ADR-001 (2026-08-20) explicitly scoped Hermes/
LangGraph data as "not ours to own or build a data-access layer for" --
this request reads as a direct exception to that, so it was surfaced back
to the operator rather than assumed. Operator's own framing, verbatim:
"Our Backend has a Different Definition Pipeline --> Cron Agent --->
Experts etc, we have Sections. For now we are going to copy what we built
in Hermes as Definition only. Later we will need to use the backend to
send Stuff to Hermes."

**Decision:** Add a read-only mirror, scoped narrowly:
- `app/data_access/hermes_definitions.py` -- reads Hermes' own real files
  directly on every call (profile.yaml's `description`, config.yaml's
  `model`/`agent.reasoning_effort`, SOUL.md's first paragraph as Primary's
  own fallback description, every `skills/*/*/SKILL.md`'s frontmatter) --
  never a synced copy, never a database, so it can't drift from what
  Hermes actually has configured. `hermes_home_path` (new `Settings`
  field, defaults to this machine's real install path) points at the
  root; `_disabled-*` archive folders (skills moved off a profile -- see
  MEMORY.md's own entries on this) are siblings of `skills/`, not nested
  inside it, so they're naturally excluded by construction, no special-
  case filtering needed.
- `app/business/hermes/definitions.py` -- thin dataclass-to-dict wrapper,
  first real content in the `business/hermes/` skeleton folder the
  2026-08-20 redesign plan already earmarked for this.
- `app/api/hermes_agents_router.py` -- `GET /hermes/agents`, `GET
  /hermes/agents/{id}` (404 on unknown). Separate file from the existing
  `hermes_router.py` (that one is live session/status data from Hermes'
  own `hermes serve` API; this is definitions read from Hermes' own
  files -- a distinct concern, one router file per concern).
- Naming: `HermesAgent`/`HermesSkill`, explicitly prefixed -- bare
  `Agent`/`Skill` already means two OTHER things in this codebase (the
  deprecated `agent_registry.py`/`skill_registry.py`, and the new Tool/
  Category/Action vocabulary where "Action" specifically replaced "Skill"
  to avoid this exact collision with Hermes' own Skill concept). Every
  record carries `source: "hermes"` (operator's own "Mark those Agents
  and Skills with Hermes") so the UI can visually distinguish these from
  whatever Second Brain's own separate "Pipeline -> Cron -> Agent ->
  Experts" taxonomy eventually becomes -- that taxonomy is explicitly
  future/undefined as of this ADR, not designed here.
- Backend only, per the operator's own explicit "View Only for now" scope
  -- no frontend page built in this pass (the existing `features/agents-
  map/` UI, confirmed during research, currently points at ADR-001's own
  archived routers and 404s; a new view would need its own work, not
  requested yet).
- No create/update/delete -- read-only by construction, matching "for now
  we are doing everything manually." Point 3 of the operator's own
  request ("In future I want our Backend to be the one who Create Agents
  and Pipeline and Cron Jobs") is explicitly deferred, not designed here.

**Alternatives Considered:**
- *Call Hermes' own `hermes serve` API (port 9119, already wired via
  `hermes_client.py`) instead of reading files* -- rejected: verified live
  that API only exposes `/api/status`, `/api/sessions`, `/api/sessions/
  stats`, `/api/config`, `/api/profiles/active` today, none of which
  return a full Agent+Skills listing. Operator's own explicit choice
  anyway ("Read live from Hermes' own files").
- *A locally-synced store (dataclass + JSON, matching the Provider/Tool
  registry pattern already used under `data_access/system/`)* -- rejected
  for this pass: adds a sync step and a real drift risk (the mirror could
  say something Hermes itself no longer has configured) for zero benefit
  over a live read, which is cheap here (a handful of small file reads,
  not a network call). Worth revisiting only if this endpoint's read
  latency or Hermes' own filesystem layout ever becomes a real problem.
- *Treat this as fully superseding ADR-001* -- rejected, per the
  operator's own answer: this is a scoped display exception, not a
  reversal -- Second Brain's backend still doesn't manage Hermes' agent/
  skill state as of this ADR, only displays a live snapshot of it.

**Consequences:** `pyyaml` added as a new backend dependency (already
transitively present via `langchain`, so no real new install cost).
`hermes_home_path` is a real per-machine path with no portability
guarantee -- running this backend on a machine without a local Hermes
install returns an empty agent list (`list_agents()` returns `[]`, never
raises), not an error, matching the "view only, degrade gracefully"
framing. A live-confirmed skill-count discrepancy exists between this
reader (78 skills for Primary) and Hermes' own `hermes profile show`
output (82) -- not yet root-caused (a nonstandard folder depth somewhere
in the bundled skill set is the leading guess); worth investigating before
this becomes a trust problem, but not blocking for a first view-only pass.
The eventual "backend creates Agents/Pipelines/Cron Jobs in Hermes"
direction (operator's own point 3) will need real write access into
Hermes -- likely via its own CLI/API, a materially different, riskier
capability than this read-only pass, and its own future decision.

---

## ADR-004: Retire the old Second-Brain-native orchestration agents for real (not just archive their routers); restore Sections as Second Brain's own concept with a real taxonomy; retrofit `features/agents-map/` over the Hermes mirror via a presentation-layer adapter, not by reviving the old Agent CRUD/chat/action surface

**Status:** Accepted
**Date:** 2026-08-22

**Context:** ADR-001 (2026-08-20) archived 9 old orchestration routers but
deliberately left their underlying registries (`agent_registry.py`,
`section_registry.py`, `skill_registry.py`, etc.) live, because real
dependents still existed -- most concretely, `main.py`'s own startup
lifespan called `ensure_librarian_agents_and_section()` on every app
start, which idempotently recreated two real agents
(`threads-cleaning`, `company-and-partner-building`) plus a
"Librarian" Section, alongside 8 more hardcoded seed agents in
`agent_registry.py` itself. ADR-003 (same day) built a new, separate,
read-only mirror of Hermes' real agents but explicitly did NOT touch any
of this -- until the operator, mid-retrofit of `features/agents-map/`
(the frontend's own existing, richer Agent/Section/Skill UI, built for
this now-superseded model), confirmed directly: "Yes, remove them, we're
fully on Hermes now."

**Decision:**
1. **Old agents genuinely retired, not just archived.** `agent_registry.
   py`'s `_SEED_AGENTS` emptied to `{}`; `.second-brain/agents_registry.
   json`'s `created_agents` cleared; `main.py`'s lifespan no longer calls
   `ensure_librarian_agents_and_section()` (left defined, unused, in
   `librarian_housekeeping.py` -- nothing else calls it, so leaving it in
   place costs nothing and avoids touching a 1300+ line file further).
   `agent_registry.list_agents()` now honestly returns `[]` rather than a
   stale seed list.
2. **Sections restored as Second Brain's own real concept -- genuinely
   independent of Hermes**, per the operator's own explicit framing:
   "Sections Part has Nothing to do with Hermes So You can Restore it."
   `app/_archive/api/sections_router.py` was fully intact and
   self-contained (only depends on `agent_registry`/`section_registry`,
   both safe post-retirement) -- restored verbatim to `app/api/
   sections_router.py`, wired into `main.py`. `section_registry.py`'s own
   `_STARTING_SECTION_NAMES` updated to the operator's real taxonomy,
   verbatim: "Our Sections will be (Customer, Liberian, Industry,
   Technology, Data Gatherer, Sales)" -- all 6 created up front, most
   empty today ("Show all 6 now, most empty... the map shows where things
   will go, not just what exists today"), rather than only the ones with
   a real agent. Section schema extended with `icon`/`color`/`subtitle`
   (previously absent, a real pre-existing gap against what the frontend
   already expected) defaulting to `null` -- not fabricated, real design
   values are a later pass.
3. **`features/agents-map/` retrofitted via a presentation-layer adapter
   (`app/business/hermes/agents_map_adapter.py`), not by reviving the old
   Agent CRUD/chat/action/job/knowledge-gap surface.** Investigated
   reviving `app/_archive/api/agents_router.py`/`skills_router.py`
   directly first -- rejected: they're real, working routers, but their
   mutating endpoints (create, chat, trigger-action, PATCH assignment,
   knowledge-gap resolve/research) have no real Hermes-side counterpart
   to actually call, and using `agent_registry.create_agent()`'s own
   shape to store 4 fabricated pseudo-agent records representing real
   Hermes profiles would be exactly the kind of hand-maintained,
   drift-prone duplicate ADR-003 was written to avoid. Built fresh,
   view-only `app/api/agents_router.py`/`skills_router.py` instead, at
   the SAME URL surface the frontend already calls (`/agents`,
   `/agents/{id}`, `/skills`, `/agents/{id}/skills`) -- no frontend
   rewiring needed for list/detail rendering. The adapter maps
   `HermesAgent`/`HermesSkill` (ADR-003, kept a pure, undecorated mirror)
   onto the frontend's existing `AgentSummary`/`AgentDetail`/
   `SkillSummary` TypeScript contract:
   - `type` (worker/producer/expert) -- operator's own explicit call,
     verbatim: "Core is a pipeline, every step in the core is a worker,
     File Agent and Notes Agents are Producers, no Experts Yet" -> Primary
     and `opp-manager` are `worker`; `notes-manager`/`files-manager` are
     `producer` (real static id->type table in the adapter, not a
     per-agent guess).
   - `section_id` -- all 4 real agents sit under the real "Data Gatherer"
     Section (resolved by name via `section_registry`, never a bare
     string literal, so a future rename can't silently desync it).
   - `working_mode` -- `autonomous` for all 4 (operator: "All the same
     mode" -> autonomous).
   - `provider_id`/`provider_name` -- real, from `HermesAgent.provider`
     (config.yaml's own `model.provider`, e.g. `"custom:compass"`), a new
     honest field added to `hermes_definitions.py` for this.
   - Fields with no honest Hermes equivalent (`settings`, `keywords`,
     `scope`, `guardrails`, `color`, `depends_on`,
     `branch_target_agent_id`) are left empty/`null`, never fabricated.
   - Chat / Job tree / Knowledge-gaps tabs on `AgentDetailPanel.tsx`:
     operator's own choice, "Show but disabled" -- rendered but inert for
     a `source: "hermes"` agent, rather than hidden entirely or backed by
     fake endpoints.

**Alternatives Considered:**
- *Sync Hermes agent data INTO `agents_registry.json`, reusing the old
  `agent_registry.py`/`agents_router.py` machinery as-is* -- rejected
  (see Decision 3): a lossy, hand-maintained duplicate with no real
  write-endpoint backing, re-exposing full CRUD/chat/action surface over
  data that isn't actually live-manageable that way.
- *Leave the old agents in place, only add the new Hermes mirror
  alongside them* -- rejected per the operator's own explicit
  confirmation ("we're fully on Hermes now") -- keeping stale
  Second-Brain-native agents around after their own architecture (ADR-001)
  named them superseded serves no purpose and actively confuses "what's
  real" on the map.
- *Treat Sections as Hermes-scoped too, folding them into
  `hermes_definitions.py`* -- rejected: Sections are a genuine
  Second-Brain-native, user-mutable concept (ADR-014) that predates and
  is independent of the Hermes work; conflating the two would violate
  ADR-003's own "keep the Hermes mirror honest and undecorated" principle
  from the other direction.

**Consequences:** `app/_archive/api/agents_router.py`/`skills_router.py`
remain archived, untouched, dead code -- not deleted (still a real
historical/reference artifact per the archive's own README), just
confirmed NOT the path taken. A real, pre-existing stale-state bug was
found and fixed in the same pass: `.second-brain/agent_sections.json`
had already been created (with the OLD 5-section seed list plus
dangling assignments to now-retired agent ids) by an earlier app run
before this ADR's seed-list change landed -- `section_registry.py`'s
own seed-on-first-read logic only fires when the file doesn't exist at
all, so updating `_STARTING_SECTION_NAMES` alone didn't retroactively
fix an already-seeded install; the file was regenerated by hand to the
real 6-section list with empty assignments. `/skills` today returns a
genuinely large, noisy list (Primary alone carries ~78 bundled generic
Hermes skills, e.g. `apple-notes`, `github-issues`, unrelated to Second
Brain) -- accurate, not a bug, but likely needs real curation/filtering
in a later UI pass before it's a good user-facing list.

---

## ADR-005: Every real Hermes cron job is ported as a Pipeline definition (`app/data_access/system/pipelines/*.json`), rendered as its own real Step tree on the map -- generalized the existing single-pipeline splice mechanism to N pipelines rather than special-casing a second one

**Status:** Accepted
**Date:** 2026-08-22

**Context:** ADR-004 proved the pattern with one Pipeline ("Threads
Builder", covering the real `email-delta-capture` cron job) by reusing
`features/agents-map/pipelineJobTreeAdapter.ts`'s existing splice
mechanism -- but that mechanism was hardcoded to exactly one pipeline id
(`EMAIL_CAPTURE_PIPELINE_AGENT_ID`, originally the old
`email-capture-pipeline` agent, repointed to `threads-builder`). The
operator then asked for the rest: "Port the rest of the Pipelines now."
The real Hermes cron surface (`hermes cron list`, confirmed live) has
exactly 3 jobs total: `email-delta-capture` (already ported),
`meeting-capture-recurring`, `new-company-discovery`.

**Decision:**
1. Two more real Pipeline definitions added, grounded in the actual,
   first-hand-known behavior of the Skills each cron job runs:
   - `meeting-builder.json` (`meeting-capture-recurring` /
     `meeting-capture` Skill) -- Fetch Meetings -> Resolve Meeting Folder
     (series vs. one-time, mirrors email-thread-capture's own
     resolve-then-create pattern) -> Build Attendees -> Link to Thread.
   - `company-discovery.json` (`new-company-discovery` /
     `new-company-discovery` Skill) -- Scan Threads for Domains + Scan
     Meetings for Domains (parallel; both real, independent scans) ->
     Filter Known Domains -> Add to Entities.md. The recurring cron job is
     ONLY the scan-and-queue half -- classification (Customer/Partner/
     Affiliate/Ignore) happens separately, conversationally, on operator
     review, and is deliberately NOT modeled as a step here.
2. **Generalized the splice mechanism to N pipelines instead of adding a
   second hardcoded id.** New `GET /pipelines` (`list_pipeline_refs()` in
   `agents_map_adapter.py`) lets the frontend discover every real Pipeline
   id without guessing from `AgentSummary`'s own fields.
   `pipelineJobTreeAdapter.ts`'s `spliceEmailCapturePipelineJobTree`
   (singular) replaced with `fetchAllPipelineJobTrees` +
   `spliceAllPipelineJobTrees` (plural) -- fetches every Pipeline's own Job
   tree in parallel, splices each independently; one Pipeline's failed
   `/jobs` fetch degrades to "that one Pipeline's summary node stays
   unspliced," never a blank Section (same degrade contract as the
   original single-pipeline version, now per-pipeline instead of global).
   `AgentsMapPage.tsx`'s own `jobs` state (a flat, cross-pipeline array,
   since a Job is looked up by id alone) gained a sibling
   `jobPipelineIds: Map<jobId, pipelineId>` -- `JobSettingsPanel` needs
   the Job's REAL parent Pipeline id, not a hardcoded one, to ever ask the
   right `/agents/{id}/jobs/{jobId}/settings` endpoint (that endpoint
   itself is not yet built -- View Only scope, ADR-003/004 -- so the panel
   still degrades to an error/empty state today, but now against the
   correct id rather than a silently wrong one).

**Alternatives Considered:**
- *Add a second hardcoded pipeline id constant next to the first,
  special-casing 2 (then 3) pipelines inline* -- rejected: the operator's
  own framing ("Every Pipeline (Cron) Should be Added") makes clear this
  is a real, open-ended set, not a fixed pair; hardcoding N pipeline ids
  inline is the exact kind of thing that breaks silently the next time a
  cron job is added and someone forgets to touch this file.
- *Model Company Discovery's classification step too, to keep every
  Pipeline at a uniform "4 real steps"* -- rejected: classification is
  real, but it's NOT part of what the recurring cron job itself does end
  to end (it happens later, conversationally, on a different trigger) --
  forcing it in as a step would misrepresent the actual automated flow
  just to hit a step-count expectation.

**Consequences:** Verified live end-to-end (Browser pane, real running
dev servers) -- "6 sections · 13 agents mapped" (Primary + 4+4+4 real
Steps across the three Pipelines), Company Discovery's own fork/merge
shape (two parallel scan Steps feeding one Filter Step) renders correctly,
confirming the tree layout handles a real multi-dependency Step, not just
the linear chain Threads Builder happened to be. A real backend-hot-reload
gap was hit and fixed along the way (see ADR-004's own similar note) --
`WatchFiles` reloaded once for an early edit in this pass and then
silently stopped detecting further changes to `agents_router.py`, serving
stale code (a real 404 on `/agents/threads-builder/jobs`) until the dev
server was stopped and restarted cleanly; worth remembering as the
reliable fix whenever the map looks stale after a backend edit that
should have taken effect.

---

## ADR-006: A new "Hermes Operations" page reads cron jobs/schedule/run-history/logs by direct file+sqlite access (no gateway dependency), and a genuine two-way chat bridge proxies Hermes' real JSON-RPC-over-WebSocket protocol rather than reimplementing or approximating it

**Status:** Accepted
**Date:** 2026-08-22

**Context:** Operator: "Reading Corn Jobs and Their Schedule, Server
Status, Schedule of the corn jobs and Status of it and Details Log so we
can link and know what happened" (first, scoped-read piece of a larger
"Hermes Library" initiative), followed mid-task by "Add as well how to
chat with Agent Back and Forth Communication when the Gateway is up."
Investigation (read-only, against this machine's real Hermes install)
found: cron jobs live in plain `<HERMES_HOME>/cron/jobs.json`; run history
lives in `<HERMES_HOME>/cron/executions.db` (SQLite); each run's own
report is a markdown file under `cron/output/<job_id>/`, and its own raw
log lines carry a derivable session tag in `logs/agent.log` -- all four
readable directly, no gateway/CLI process required (consistent with
ADR-001/hermes_definitions.py's existing "not ours to own, read the real
files" precedent). Separately, Hermes' own embedded chat turned out NOT to
be a REST endpoint -- confirmed live (hand-driving `/api/ws`'s real
`session.create`/`prompt.submit`/event-stream protocol against the running
gateway, getting a genuine model reply back) before writing any
integration code.

**Decision:**
1. **Cron/schedule/status/log surface, entirely read-only, entirely direct
   file/db access:** new `app/data_access/hermes_cron.py`
   (`list_cron_jobs`/`get_cron_job`/`list_cron_executions`/
   `get_execution_detail`) reads `jobs.json` + `executions.db` +
   timestamp-derived report/log paths directly, same pattern as
   `hermes_definitions.py` -- no local persistence, every call re-reads the
   real source, can never drift. Business wrapper
   `hermes_cron_status.py` (ADR-005 point 5's "router never reaches
   data_access/ directly" shape) turns the dataclasses into plain dicts.
   Server/gateway status reuses the EXISTING `hermes_status.py`/
   `/hermes/status` built earlier this session -- not rebuilt.
2. **Chat is a genuine bidirectional proxy, not a REST wrapper attempt:**
   new `app/data_access/hermes_ws_client.py::HermesChatSession` is a real
   async JSON-RPC-over-WebSocket client (one Hermes `/api/ws` connection +
   one Hermes chat session per instance), reusing `hermes_client.py`'s
   already-cached session token (passed as `?token=` on the WS handshake,
   the one endpoint that takes it as a query param rather than a header).
   `app/api/hermes_router.py::chat_ws` (`WEBSOCKET /hermes/chat/{agent_id}`)
   bridges a browser WebSocket to this session 1:1 -- every real Hermes
   event frame (`message.delta`/`message.complete`/`thinking.delta`/
   `approval.request`/etc.) passed through verbatim as `{"type","payload"}`
   rather than reinterpreted, so the frontend decides what to render and
   nothing real is silently dropped. `session.create`'s own `profile` param
   scopes a chat to a specific non-Primary specialist (`opp-manager`/
   `notes-manager`/`files-manager`); omitted for `"default"` (Primary),
   since that id is the launch identity itself, not a real `profiles/
   default` directory the param could resolve.
3. New page `HermesOpsPage.tsx` (route `/hermes`, nav "Hermes Operations")
   -- Server Status card, expandable Cron Jobs list (click a job for its
   run history, click a run for its linked report + raw log lines), and a
   Chat panel (agent picker limited to the 4 real Hermes agents --
   Pipelines are Second Brain's own synthetic entries with no live Hermes
   profile behind them, deliberately excluded from the chat picker).

**Alternatives Considered:**
- *Shell out to `hermes cron list`/`hermes cron runs <id>` instead of
  reading `jobs.json`/`executions.db` directly* -- rejected for READS
  specifically (the operator's own "shell out to the CLI for writes"
  recommendation from the same investigation was scoped to WRITES, where
  reimplementing Hermes' own file-format/locking logic would be risky;
  reads have no such risk, and direct file/db access matches the existing,
  already-working `hermes_definitions.py` precedent exactly).
- *Approximate chat with a single-shot REST-style "send and poll for
  result" wrapper* -- rejected: Hermes has no such endpoint: the ONLY real
  send-a-message surface is the stateful, streaming `/api/ws` JSON-RPC
  protocol. A polling approximation would mean inventing a protocol Hermes
  doesn't have, silently losing the real streaming/approval/clarify
  signals, and diverging further from Hermes' actual behavior over time.
- *Build only a minimal single-turn chat (no streaming, no approvals)* --
  offered to the operator as the smaller option; operator chose the full
  version (streaming, session reuse, approval/clarify handling) explicitly,
  accepting the larger scope.

**Consequences:** Verified live, end to end, through the real running
dev servers (Browser pane) -- not just unit-level: the WS chat protocol
was hand-driven against the live gateway BEFORE any backend code was
written (confirmed the exact wire shape, avoiding a wrong-shape rebuild
later); Second Brain's own `/hermes/chat/{agent_id}` proxy was then
smoke-tested standalone (real "PONG"-style reply received) before wiring
the frontend; and finally the full page was exercised in the browser
itself -- expanding a real cron job's run history, drilling into a real
run's linked report + matching log lines, and sending a real chat message
through the actual page UI and getting a real streamed reply back from
Primary. Two real frontend bugs were found and fixed in this same pass
(both `useEffect(() => fetchX().then(setY), [])`-style implicit-arrow-
return-of-a-Promise mistakes, not the tool's fault) -- a `useEffect`
callback must never itself return anything other than `undefined` or a
cleanup function; wrap the body in braces whenever the effect exists only
to kick off a `.then()` chain.

---

## ADR-007: Cockpit roster/message persistence is one new per-subject-keyed JSON store (`.second-brain/cockpit_chat.json`), never a revival of `business/cockpit/threads.py`/`ADR-036`

**Status:** Accepted
**Date:** 2026-08-25

**Context:** `REQ-SB-82-US-01` needs the Chat tab's brought-in roster and
message history to survive reload/navigation, scoped per `(subject_kind,
subject_note_stem)`. `cockpit_router.py`'s `GET /cockpit/{subject_kind}/
{subject_note_stem}` today returns a hardcoded, honest empty `thread`
stub; `Cockpit.tsx`'s `broughtInIds` is local-only `useState`. The
frontend's own `CockpitThread` TS contract (`cockpitApiClient.ts`) is
already correctly shaped for this (`messages: [{speaker, agent_id,
agent_name, text}], brought_in_agent_ids: string[]`) — only a real
backend behind it is missing.

The one prior real implementation of this exact surface
(`business/cockpit/threads.py`, originally `ADR-036` in the archived
pre-2026-08-20 sequence, `.second-brain/cockpit_threads.json`) is
confirmed stale, not quietly reusable: it composed `run_agent_
conversation`, a function that no longer exists post-Hermes-pivot (the
whole Second-Brain-native LangGraph orchestration layer it belonged to
was archived, `ADR-001`). `MEMORY.md`'s own 2026-08-25 entry confirms
`business/cockpit/{threads,research,person_note_proposals,attachments}.py`
are all stale for the same reason. This story's own Constraints
explicitly forbid reviving that design as-is and leave the concrete
storage mechanism open for this pass to decide.

**Decision:** One new, genuinely fresh module, `app/business/cockpit/
chat_store.py`, backed by ONE new JSON file, `.second-brain/
cockpit_chat.json` — a flat top-level dict keyed by `"{subject_kind}:
{subject_note_stem}"`, each value exactly matching `CockpitThread`'s
existing shape: `{"brought_in_agent_ids": [...], "messages": [...]}`.
This reuses the naming spirit of the old `cockpit_threads.json`
convention (one file, subject-keyed) without reusing any of its actual
code or the retired `run_agent_conversation` composition.

Load/save follows the SAME established pattern as every other single-key
JSON state store in this app (`vault_writer.load_agent_visuals_state`/
`save_agent_visuals_state` is the direct precedent — read-whole-file,
default-if-missing, write-whole-file, no locking layer) — new sibling
functions in `vault_writer.py`, not a new persistence technology.

New router surface on `cockpit_router.py`: `POST /cockpit/{subject_kind}/
{subject_note_stem}/roster` (bring in) and `DELETE .../roster/{agent_id}`
(remove); the existing `GET` returns the real, persisted `thread` in
place of the stub. `Cockpit.tsx`'s `bringIn`/`remove` call these instead
of mutating local state.

This story's own store is deliberately generic — no `source: "recommended"
| "manual"` distinction on `brought_in_agent_ids` (that's `REQ-SB-82-US-03`'s
own additive extension, `ADR-009`, layered on the SAME entry, not a
second store) — and carries no message-sending logic at all (`REQ-SB-82-
US-04`'s concern).

**Alternatives Considered:**
- *Resurrect `business/cockpit/threads.py`/`ADR-036` verbatim* — rejected:
  it composes `run_agent_conversation`, a function that no longer exists;
  there is nothing left to revive without a full rewrite, at which point
  it is not actually a revival.
- *One file per subject* (`.second-brain/cockpit_chat/<key>.json`) —
  rejected for this pass: this app's own existing single-key JSON stores
  (`agent_visuals.json`, etc.) all use one file regardless of key count;
  a meeting/email-scale key count (hundreds, not millions) doesn't yet
  justify per-subject files. Revisit if per-subject write contention or
  the single file's size ever becomes a real, measured problem (see
  Consequences).
- *Store chat/roster inside the subject note's own frontmatter* —
  rejected: this project's own System-Data-vs-Vault-Data taxonomy
  (`MEMORY.md`/`CLAUDE.md`) draws a firm line between Second Brain's own
  operational state and the user's trusted vault content; a chat
  transcript is the former, and frontmatter is not naturally append-
  friendly for a growing message log either.
- *Persist via a long-lived `HermesChatSession` per subject, letting
  Hermes' own gateway hold history* — rejected: Hermes' session memory is
  scoped to one agent conversation, not a multi-Expert, per-subject
  roster+thread record Second Brain itself needs to read/render across
  reloads; also out of scope, since this story explicitly builds storage
  only, no send/receive (no `HermesChatSession` is even opened here).

**Consequences:** Every Cockpit subject visited creates or updates one
real entry in this one new file; concurrent writes to different subjects
share the same file (a real, accepted read-modify-write race, the same
accepted characteristic every other single-file JSON state store in this
app already has — no locking layer exists anywhere in this codebase
yet). If file size or write contention ever becomes a real, measured
problem, revisit the one-file-per-subject alternative above. Message
attribution stays exactly `CockpitThread`'s already-existing TS
contract — no frontend widening/narrowing needed once this story ships.
`REQ-SB-82-US-03` will ADD a `recommended_agent_ids` field to this same
per-subject entry (an additive schema change, not a redesign) — see
`ADR-009`.

---

## ADR-008: Research Agent is a new, standalone Hermes profile under the Librarian Section with its own `research-kb-writer` Skill writing into a new `Work/Research/` folder — no MCP server, no routing through `REQ-SB-63`'s Vault Filing Expert

**Status:** Accepted
**Date:** 2026-08-25

**Context:** `REQ-SB-82-US-02` needs a Research Agent, under the existing
Librarian Section, that looks something up and writes what it finds as a
brand-new, additive note into its own dedicated vault area, with no
approval gate (its write structurally cannot touch existing content). No
live research/web-lookup mechanism exists anywhere in the current,
post-Hermes-pivot codebase to build against — the pre-pivot `REQ-SB-36`
web-research Skill belonged to the fully-retired Second-Brain-native
agent/LangGraph model and is not reusable. A genuine, unreconciled
tension existed between this requirement's own "own folder, no placement
decision needed" framing and `REQ-SB-63`'s general "every agent routes
new content through the Librarian/Vault Filing Expert" principle — the
story flagged this as unclear rather than guessing.

Operator resolution (2026-08-25): `vault_filing_expert.py`'s only real
callers (`email_classification.py`, `librarian_housekeeping.py`,
`knowledge_bootstrap.py`, `knowledge_gap_tracking.py`,
`project_customer_synthesizer.py`, `skill_tools.py`) are themselves
pre-Hermes-pivot orchestration-layer code `main.py` no longer wires into
the running app — the same fate as `cockpit_router.py`'s own old
Chat/research surface. It is not a live, reachable mechanism today,
regardless of `REQ-SB-63`'s own general framing. The only proven, live
write pattern in this codebase is a dedicated per-Expert writer Skill
(`azure-kb-writer`, `compass-kb-writer`, and the 3 Customer Experts all
write this way) — write directly via a new one, mirroring
`azure-kb-writer`'s own real, working `write_azure_doc.py` contract.
Research mechanism: Hermes' own bundled `web_search`/`terminal` tools,
the same real, proven capability already powering `azure-expert`'s and
`compass-expert`'s own research — no new lookup capability needed.

**Decision:**
1. **New Hermes profile, `research-agent`**, registered under the
   existing Librarian Section the same way `notes-manager`/`files-manager`
   already are (`app/business/hermes/agents_map_adapter.py`'s
   `_AGENT_TYPE`/`_AGENT_SECTION` dicts) — same "one real domain, one
   Hermes profile" pattern this codebase has now used 15+ times
   (`MEMORY.md`). No MCP server, no Second Brain backend process
   dependency at runtime, per `ADR-002`'s own already-settled reasoning
   (a `terminal`-tool `pip install` step covers any real dependency; this
   agent needs none beyond Hermes' own bundled tools anyway).
2. **Research via Hermes' bundled `web_search`/`terminal` tools directly**
   — no new lookup Skill is built.
3. **New writer Skill, `research-kb-writer`**, script `write_research_
   doc.py`, mirroring `azure-kb-writer`'s own `write_azure_doc.py` CLI
   contract exactly (`--vault-path`/`--input-file`, a scratch JSON
   payload, frontmatter + `**Topic:**`-style backlink + `## Summary`/
   `## Details` + optional images) — called as a plain, direct `terminal`
   invocation using its own full absolute path (this codebase's
   established Skill-script-invocation convention). ONE deliberate
   divergence from `azure-kb-writer`'s own contract: `azure-kb-writer`
   overwrites the SAME note on a repeated same-title/area call
   (`updated: true`, its real refresh mechanism); `research-kb-writer`
   NEVER overwrites — a title collision gets a disambiguating suffix
   (date or numeric) and a brand-new file every time. This directly
   serves `REQ-SB-82-US-02`'s own Constraint (no merge/dedup logic for
   v1; repeated similar requests may legitimately produce more than one
   note) and its Scenario 2 (a research write must never edit or
   overwrite any existing note) — `azure-kb-writer`'s own update-in-place
   default would silently violate that AC the moment two requests
   produced the same title.
4. **Destination: `Work/Research/<slug>.md`** — flat, no category
   subfolder split (unlike Azure's `Services/<Category>/`, since this
   agent's scope is narrower and doesn't yet need one). Frontmatter:
   `type: "ResearchDoc"`, `topic`, `tags: ["research"]`, `source_url`
   (real, omitted rather than fabricated when none exists), `created`.
5. **No approval gate** — the write proceeds immediately once research
   is done, since it is structurally confined to `Work/Research/` and can
   never affect any other note.
6. **Does not route through `REQ-SB-63`'s Vault Filing Expert.** This is
   a structural non-routing (nothing live to route through today), not
   an active choice among two working alternatives.
7. **No caller-specific behavior** (Scenario 4) — the agent is reached
   identically whether relayed from a scheduled job (`REQ-SB-82-US-05`)
   or a live Cockpit Chat request, the same one-shot relay/direct-reach
   mechanisms every other Hermes profile in this codebase already uses.

**Alternatives Considered:**
- *Route research writes through `REQ-SB-63`'s Vault Filing Expert for
  consistency with its own stated principle* — rejected: confirmed its
  only real callers are archived/dead pre-Hermes-pivot code; honoring the
  principle literally would mean reviving genuinely retired
  infrastructure for a single write path that structurally needs no
  placement decision anyway (a fixed destination folder).
- *Build a new MCP server / backend-hosted research capability* (`ADR-001`'s
  original pre-`ADR-002` shape) — rejected per `ADR-002`'s own settled
  reasoning: no benefit remains once Hermes' own `terminal`/`web_search`
  tools are directly usable, no dependency-install gap this agent needs
  solved.
- *Give `research-kb-writer` the same update-in-place semantics as
  `azure-kb-writer`* — rejected: directly conflicts with `REQ-SB-82-US-02`'s
  own explicit "no merge/dedup logic, repeated requests may produce more
  than one note" Constraint and Scenario 2's "never edits or overwrites"
  requirement.
- *Fold this capability into an existing agent (`notes-manager`)* instead
  of a new dedicated Hermes profile — rejected: the PRD's own framing
  ("may itself grow into a full Expert... reused directly from mid-meeting
  Chat too") and Scenario 4's caller-agnostic requirement match the
  established one-domain-one-profile pattern better than folding into
  `notes-manager`'s own narrower catch-all-capture mandate; also
  preserves a clean, sole-KB-write-owner boundary consistent with every
  other Expert-family precedent (Compass, Azure).

**Consequences:** A new `research-agent` Hermes profile must be
provisioned outside this repo (Hermes-side work, same as every other
specialist — not part of this repo's own `src/` build). `Work/Research/`
becomes a new top-level vault area with no consumer beyond the Cockpit
Overview's already-existing (currently-stub) "Related documents"/
"Articles" sections — wiring that consumption is explicitly out of scope
here (`REQ-SB-82-US-05`'s or a later story's concern). Because every
write always creates a new file, `Work/Research/` will accumulate
multiple notes for similar or repeated topics over time with no automatic
consolidation — a known, disclosed limitation per this story's own
Constraints, not a defect.

---

## ADR-009: Meeting Moderator roster recommendation runs entirely inside Second Brain's own backend (deterministic tag/keyword matching, no new Hermes profile), computed-on-first-read and cached as an additive field on `ADR-007`'s own persisted roster store

**Status:** Accepted
**Date:** 2026-08-25

**Context:** `REQ-SB-82-US-03` needs the Meeting Cockpit's Chat roster to
show a "Recommended" grouping (customer-match + domain-match, both
tracks, run independently) before the user manually brings anyone in. The
PRD's own claim that the UI "already reserves" a Recommended slot was
confirmed, by direct inspection, to be inaccurate against the real,
current `Cockpit.tsx` (2026-08-25 UI makeover) — a genuinely new region,
though its VISUAL shape was already approved the same day, in the same
live-whiteboarding session that produced this requirement (an interactive
mockup: right rail "Recommended" section with the matched agent + an Add
action, plain Experts list below — operator-confirmed "Good," no fresh
`/design` pass needed). This story is a real, disclosed dependency on
`REQ-SB-82-US-01`'s own persisted roster store (`ADR-007`) — a
recommendation assembled "before you arrive" needs somewhere durable to
live before the user ever opens the Cockpit. The domain-match track's own
underlying data was confirmed, by direct inspection, not to exist for any
real agent — `agents_map_adapter.py`'s own module docstring: "Fields with
no honest Hermes equivalent (settings, keywords, scope, ...) are left
empty/null rather than fabricated." Operator resolution: domain-match =
lightweight keyword overlap between the meeting's own tags/subject and
each Expert's already-exposed `GET /agents` `name`/`description` fields —
no new structured per-agent scope-tagging schema for v1.

**Decision:**
1. **New business module, `app/business/cockpit/moderator.py`** — two
   independent matching functions: `match_customer_expert(subject_note_
   stem)` (the subject's own `customer` tag/folder → a real,
   already-registered `<customer>-expert` agent id, per `REQ-SB-83`'s
   real Masdar/Adnoc/TAQA agents; `None`, never fabricated, if no match)
   and `match_domain_experts(subject_note_stem)` (tokenized keyword
   overlap between the subject's own tags/subject text and every real
   `type: "expert"` agent's `name`/`description`, both tracks run and
   combined, neither suppresses the other).
2. **Both tracks are purely deterministic/mechanical** (a frontmatter
   lookup and a keyword-overlap comparison) — NOT an LLM judgment call —
   so both run entirely inside Second Brain's own backend, synchronously,
   with no new Hermes profile, cron job, or scheduled task needed for
   this story.
3. **Trigger: compute-on-first-real-read, then cache.** The first `GET
   /cockpit/{subject_kind}/{subject_note_stem}` call for a subject with
   no `recommended_agent_ids` entry yet computes both tracks and persists
   the result; every subsequent read (including the read that opens the
   Chat tab itself, per Scenario 5's own "before bringing anyone in
   manually" wording) serves the cached value. This satisfies every
   Scenario without a proactive/eager trigger — computing at read time,
   before any manual bring-in action within that same page load, already
   IS "before you arrive" in the sense the Scenarios actually assert.
4. **Persisted schema: one additive field on `ADR-007`'s own per-subject
   entry** — `recommended_agent_ids: list[str]`, a non-authoritative hint
   list separate from `brought_in_agent_ids`. Bringing a recommended
   agent into the chat uses the exact same `bring_in_agent` mechanism as
   any manual bring-in (Scenario 6 — recommendation never restricts
   manual choice).
5. **Frontend:** a new "Recommended" grouping in `Cockpit.tsx`'s Chat tab
   right rail, above the existing "In this chat"/"Bring in another
   Expert" groups, per the already-approved mockup shape. An agent
   already brought in renders only in "In this chat," never duplicated
   into "Recommended."

**Alternatives Considered:**
- *Compute the recommendation proactively, triggered by the SAME event
  that captures/updates the subject note* (e.g. an additive step on the
  real Meeting Builder Hermes pipeline, `ADR-005`) — considered: gives a
  literal "recommended before ANY read ever happens" guarantee. Rejected
  for this pass in favor of compute-on-first-read: the proactive route
  would require a purely mechanical, deterministic computation to be
  wired into Hermes-side pipeline/Skill machinery for no behavioral gain
  against this story's own Scenarios (all of which are satisfied by
  "recommended before manual bring-in within the same page load"), adding
  real cross-system complexity (a Hermes Skill calling back into Second
  Brain's REST API just to run a keyword match) for zero observable
  benefit. Revisit only if a future requirement genuinely needs the
  recommendation to exist before the very first Cockpit open of a
  brand-new subject.
- *A new, structured per-agent "scope"/"keywords" field* (extending
  `HermesAgent`) instead of reusing `name`/`description` — rejected per
  the operator's own explicit resolution: no new structured schema for
  v1, refine later if keyword overlap proves too coarse.
- *A second, separate JSON store for `recommended_agent_ids`* instead of
  extending `ADR-007`'s existing per-subject entry — rejected:
  recommendation and roster are the same real-world concept (who's
  in/available for this subject's chat) viewed two ways; splitting them
  into two files would require two reads/writes per Cockpit page load and
  risks the two drifting out of sync (e.g. a recommended agent already
  manually brought in needing cross-store consistency).

**Consequences:** `CockpitThread`'s TS contract gains one new field,
`recommended_agent_ids: string[]`, additive and backward-compatible (a
subject with no recommendation computed yet reads back `[]`, the same
honest-empty convention every other field in this store already follows).
The domain-match track's keyword-overlap quality is coarse by design
(operator's own explicit "refine later" framing) — a real, disclosed
limitation, not a defect, likely to need iteration once exercised against
a broader real agent roster. A brand-new subject's very first `GET` pays
the one-time cost of computing both tracks inline — cheap (local
frontmatter read + an in-memory keyword comparison against however many
real agents exist today), not expected to be a real latency concern at
this codebase's current agent-roster scale.

---

## ADR-010: Meeting Preparation Agent is a new Hermes profile + cron job (mirroring `new-company-discovery`'s real cron shape), relays KB lookups to `research-agent`, and persists its learned suppression preference in Hermes' own native per-profile memory file, not a Second-Brain-owned store

**Status:** Accepted
**Date:** 2026-08-25

**Context:** `REQ-SB-82-US-05` needs an agent that scans upcoming
meetings twice daily, delegates unfamiliar-topic KB lookups to the
Research Agent (`ADR-008`), runs a one-time web lookup for any attendee
whose Person note is still empty beyond frontmatter, sends a WhatsApp
summary only when it finds real data worth checking, and learns to
suppress future notifications for a given meeting/type from plain-
language feedback. The PRD's own cited persistence mechanism,
`vault_writer.append_agent_memory_entries`, was confirmed, by direct
reading, to have ZERO live callers today (only `app/_archive/api/
agents_router.py` and the confirmed-stale `business/cockpit/threads.py`
reference it) — not, in fact, "already working elsewhere" in the current
architecture, contrary to the PRD's own text.

Operator resolution (2026-08-25): (a) WhatsApp delivery = a new Hermes
cron job/profile mirroring `daily-briefing`'s intended proactive shape
and, concretely, `new-company-discovery`'s own real, live cron
(`cron/jobs.json`, confirmed directly: `schedule: {"kind": "interval",
"minutes": 1440}`, `deliver: "whatsapp"`, its own SKILL.md's explicit "if
[nothing found], reply with nothing substantive — do not send a no-op
notification"). (b) Suppression persistence = Hermes' own native
per-profile `memories/USER.md` file — confirmed real and already
populated with genuine learned facts on `azure-expert`'s own file
(`§`-delimited plain-language entries, e.g. reply-style preferences),
NOT `vault_writer.append_agent_memory_entries`. (c) "Meetings like this"
resolves to the meeting's own `calendar_series_id`, falling back to its
`customer` tag for a one-off meeting.

**Decision:**
1. **New Hermes profile, `meeting-prep-agent`**, clone-based, same "one
   real domain, one Hermes profile" pattern this codebase has used
   repeatedly (`MEMORY.md`). Owns its own new cron job: `schedule:
   {"kind": "interval", "minutes": 720}` (twice daily — `new-company-
   discovery`'s own real interval is 1440 minutes/once-daily; this
   agent's PRD requirement is 2x/day, so the interval is halved, same
   `"interval"` schedule kind), `deliver: "whatsapp"`, and a cron
   `prompt` following `new-company-discovery`'s own real, live prompt
   shape (a plain-English instruction naming the Skill, with the same
   explicit "reply with nothing substantive if nothing found" clause) —
   satisfies Scenario 5 (no notification when nothing worth checking) and
   Scenario 8 (runs on its own schedule, no manual trigger).
2. **KB-lookup delegation (Scenario 1):** relays to `research-agent`
   (`ADR-008`) via the SAME one-shot cross-profile relay every
   multi-profile chain in this codebase already uses (`hermes -p
   research-agent chat -q "..."`) — per this project's own documented
   Constraint (`MEMORY.md`), this relay has no live back-channel, so
   `meeting-prep-agent` must fully specify its research ask in one shot,
   never expecting Research Agent to ask a clarifying question back
   mid-relay.
3. **Person-note web lookup (Scenarios 2, 3):** a new Skill, own script,
   mirroring `app/business/cockpit/notes.py::add_person_note`'s
   established append-only-to-an-existing-note shape (never creates a new
   Person note — the note already exists, just empty). Eligibility is a
   plain mechanical check: the note's own body (everything after
   frontmatter) is empty/whitespace-only. A real web lookup runs only
   when that check passes; once ANY real content exists in the body
   (written by this agent OR the user), the check fails on every future
   run — no separate "already looked up" tracking field is needed, the
   note's own real content IS the gate.
4. **Suppression persistence: Hermes' own native per-profile `memories/
   USER.md`.** The agent writes/reads its own learned suppression
   preference in plain language via its own memory tool (the SAME
   mechanism already populating real facts on other profiles), keyed by
   the meeting's own `calendar_series_id`, falling back to its `customer`
   tag for a one-off meeting. No new Second-Brain-side schema, store, or
   API — matching a future meeting against a learned plain-language
   preference is left to the agent's own judgment on each scheduled run
   (its memory file is already injected into its context every session,
   per this project's own documented Hermes memory mechanics), not
   structurally enforced by Second Brain's backend.

**Alternatives Considered:**
- *`vault_writer.append_agent_memory_entries`* (the PRD's own cited
  mechanism) — rejected: confirmed zero live callers today; reviving it
  would mean building against dead infrastructure with no proven current
  behavior, when a real, already-working alternative (Hermes' native
  per-profile memory) is directly observable working today.
- *A new Second-Brain-owned structured suppression store* (e.g.
  `.second-brain/meeting_prep_suppressions.json`, same shape as `ADR-007`'s
  `cockpit_chat.json`) — considered and rejected for this story
  specifically: the operator's own resolution names Hermes' native memory
  as the mechanism, and a structured store would additionally require
  Second Brain's backend to somehow parse the agent's own free-language
  interpretation of "suppress meetings like this" back into a rigid
  match — a judgment call an LLM agent handles naturally on each run and
  a rigid JSON matcher would not.
- *Route WhatsApp delivery through a Second-Brain-owned integration*
  instead of a Hermes cron's own `deliver: "whatsapp"` — rejected: Second
  Brain has and needs no direct WhatsApp integration of its own; Hermes'
  gateway is the sole, already-proven real channel (`ADR-001`'s own
  "extra channels run through Hermes' own gateway" decision), and
  `deliver: "whatsapp"` on a cron job is the exact mechanism
  `new-company-discovery` already uses live today.
- *Have Meeting Prep Agent perform the web lookup and write findings
  itself for unfamiliar topics*, instead of delegating to Research Agent
  — rejected per Scenario 1's own explicit "delegates... rather than
  researching it itself" wording, and per the PRD's own framing of the
  Prep Agent as one caller among possibly others of the shared Research
  Agent capability, not a duplicate implementation.

**Consequences:** A new `meeting-prep-agent` Hermes profile and cron job
must be provisioned outside this repo (Hermes-side work, not part of this
repo's own `src/` build). The suppression preference lives entirely
inside Hermes' own per-profile memory file, outside this repo's version
control and outside Second Brain's own data model — Second Brain's
backend has no visibility into, or ability to query/audit, what is
currently suppressed; a future story wanting Second Brain's OWN UI to
show/manage suppressions would need a different, additive mechanism, not
covered here. The relay to `research-agent` inherits the same documented
one-shot, no-live-back-channel constraint as every other cross-profile
relay in this codebase.

---

## ADR-011: A new, dedicated Compass `gpt-oss-120b` HTTP client is the first direct-to-LLM client in the post-2026-08-20 backend — lives in `app/data_access/`, degrades honestly on failure, and is NOT a continuation of the orphaned `ADR-022` reference

**Status:** Accepted
**Date:** 2026-08-31

**Context:** `REQ-SB-82-US-06` needs a real reasoning pass over the
brought-in Experts' own name/description, recent conversation history, and
the new message's own text to route a substantive Cockpit question
(Scenario 2) — this needs an actual model call, not another deterministic
heuristic. No live HTTP client to any LLM provider exists anywhere in the
current `src/backend` tree today: `config.py` already anticipates one
(`compass_base_url`/`compass_api_key`/`compass_model`, `.env.example`
currently blank placeholders) and `provider_manager.py`'s own
`_REAL_CLIENT_PROVIDER_IDS = {"compass", "anthropic-claude"}` already
flags Compass `has_real_client=True` — but that flag has been
aspirational, not literal, since 2026-08-27: `data_access/{compass,
anthropic,outlook_com}_client.py` were deliberately DELETED that day as
part of the "backend now fully agentic" purge (`MEMORY.md`, 2026-08-27 —
"every parallel/competing orchestration mechanism the backend once ran
itself... is deleted, not just disconnected... Hermes now owns all
scheduling/dispatch/agent-orchestration natively"). Confirmed by direct
git history (`git log --all -- '*anthropic_client*'`/`'*compass_client*'`):
both files existed pre-redesign, survived briefly into the post-2026-08-20
tree, then were removed 2026-08-27 — no worktree/branch holds a viable,
current-architecture copy (the only surviving `compass_client.py` copies
live in stale `worktree-agent-*`/`claude/happy-noyce-b3fecb` branches dated
2026-08-11, ~261,000 lines diverged from `master`, not mergeable).

**A real, disclosed ledger discrepancy, investigated directly rather than
assumed:** `provider_manager.py`'s own code comment ("Compass and
Anthropic Claude both have real clients (ADR-022 point 3)") and two task
files under `REQ-SB-36-US-01` (`T01`/`T02`, `anthropic-client.md`) cite
`ADR-022` as an already-`Accepted` decision covering `has_real_client`/
provider plumbing and the Anthropic client. Direct reading of
`Implementation/Architecture/ADR.md` found no `ADR-022` — the real
ledger's highest entry, before this pass, was `ADR-010`. This is
explained, not left a mystery: `ADR.md`'s own 2026-08-20 numbering-restart
note confirms the ENTIRE pre-redesign ADR sequence (originally ADR-001
through ADR-058) was archived to `Documentation-Archive-2026-08-20/
Implementation/Architecture/ADR.md`, and only ADR-001 (the redesign's own
founding decision) was explicitly carried forward under the new
numbering. An old `ADR-022`, if it existed in that archived sequence,
governed the OLD `anthropic_client.py`/`compass_client.py` pair — both
since deleted (2026-08-27) and never rebuilt. No entry in the CURRENT
`ADR.md` ever formally superseded that old decision, because the code it
governed was retired via a plain `MEMORY.md` Decision entry, not an ADR —
a real gap in ADR hygiene, not a fabricated one. **Conclusion: `ADR-022`
is void by orphaning, not extendable.** Every current-codebase comment/
task file citing it should be read as referring to dead, pre-redesign
history; this ADR is the first REAL, current-ledger decision governing a
direct-to-LLM client, and takes a fresh number in the live sequence
rather than attempting to "restore" ADR-022's old number (which would
misleadingly imply continuity with a decision this pass cannot actually
read or verify).

**Decision:**
1. **New module, `app/data_access/compass_client.py`** — raw HTTP I/O
   only: builds and sends a chat-completion request to `settings.
   compass_base_url` using `settings.compass_api_key`/`settings.
   compass_model`, using `httpx` (already a proven, already-used
   dependency for external HTTP calls in this exact architecture —
   `app/hermes/rest.py`'s own Hermes-gateway client is the direct
   precedent for "an HTTP client module living at this layer, using
   httpx directly"). Placed in `data_access/`, not `app/hermes/` —
   `app/hermes` is reserved exclusively for calls to the Hermes gateway
   itself (2026-08-27's own hard rule: "exactly ONE file,
   `app/business/hermes/client.py`, may import from `app/hermes`"); a
   direct-to-Compass call is a categorically different external
   integration (a raw LLM provider API, not Hermes), so it gets its own
   sibling module at the same layer, not a case inside the Hermes
   package. This also matches `ADR-001`'s own "data layer" framing
   (`app/data_access/` is where this backend's real external-data reads
   live) and `ADR-003`'s established `api -> business -> data_access`
   layering discipline (raw I/O has no business interpretation of its
   own).
2. **Raises a clear, dedicated error on any failure** (network error,
   timeout, non-success response) — mirrors `app/hermes/
   client.py::HermesUnavailableError`'s own shape (a real, named
   exception type the business layer catches explicitly), never a bare
   exception or a silently-swallowed `None`. The exact request/response
   JSON contract against Compass's real `gpt-oss-120b` API is left to
   `/plan-tasks`'/the coder's own live verification against the real
   endpoint once credentials are available (Scenario 6's degrade path is
   what makes this safe to build before that verification is complete —
   see `ADR-012`).
3. **No new business/core Provider-entity code needed.** `ProviderManager`/
   `Provider` (`business/core/provider/`) already carry Compass's
   endpoint/credential/model as data and already flag
   `has_real_client=True` for it (`provider_manager.py`,
   `_REAL_CLIENT_PROVIDER_IDS`) — this ADR makes that existing flag
   literally true for the first time, rather than adding a second,
   competing Provider-credential concept. The new client reads
   `app.config.settings` directly for its own request construction (same
   settings `ProviderManager`'s own `data_access/providers.py` already
   sources `seed_defaults()` from) — it does not go through
   `ProviderManager` at call time, since `ProviderManager` is a CRUD/data
   manager for the Provider entity (config-at-rest), not a runtime
   dispatcher for making calls; consuming settings directly for a live
   request is the same category of read `providers.py` itself already
   performs (a "structural PATH/VALUE read," not business
   interpretation).
4. **The business-level consumer (the LLM-based Cockpit moderator,
   `ADR-012`) lives under `app/business/cockpit/`, not `app/business/
   core/provider/`.** Routing a Cockpit question is Cockpit's own
   business concern (parallel to `moderator.py`'s existing deterministic
   tracks); Provider's Manager owns credential/config CRUD only,
   matching this project's own established "Managers own entity CRUD;
   cross-cutting/consuming business logic lives with the consumer, not
   inside the entity Manager" split (`MEMORY.md`, 2026-08-27/28
   SectionManager/AgentManager entries: "cross managers work is the
   business logic," "Managers don't call Routers, Routers call
   Manager").

**Alternatives Considered:**
- *Extend the orphaned `ADR-022` in place, treating it as still-Accepted*
  — rejected: it cannot be read, verified, or safely extended (it exists
  in no reachable file in the current repo state); silently building on
  an unverifiable citation would risk inheriting assumptions this pass
  cannot actually check. A fresh ADR, explicitly naming and voiding the
  orphaned reference, is the honest choice.
- *Renumber this decision as a restored "ADR-022"* — rejected: would
  misleadingly imply this ADR is a continuation of a specific,
  known-content prior decision; it is not — it's a first-principles
  decision made fresh against the current, post-2026-08-20 architecture.
  Using the next real sequential number (`ADR-011`) keeps the ledger's
  own numbering honest.
- *Place the new client under `app/hermes/`, reusing that package's
  existing httpx wiring* — rejected: `app/hermes` is a deliberately
  Second-Brain-agnostic, Hermes-only library (2026-08-27's own hard rule,
  "never imports `app.config`... exactly ONE file may import from
  `app/hermes`"); a Compass HTTP client needs `app.config.settings`
  directly and has nothing to do with the Hermes gateway protocol —
  folding it in would violate that package's own single-purpose boundary
  for no benefit.
- *Route the Compass call through `ProviderManager`* (a
  `provider_manager.call(...)`-shaped method) — rejected:
  `ProviderManager` is this project's established CRUD/data Manager for
  the Provider entity (mirrors Section/Agent/Pipeline/Vault/Template
  Manager's "one real gateway onto entity data" rule) — adding a live
  network-call method to it would conflate "manage Provider records"
  with "make a live LLM request," a different responsibility this
  project's own Manager pattern deliberately keeps separate (see
  Decision 4).
- *Wait for real Compass credentials before building anything* —
  rejected: the story's own Scenario 6 (honest degrade on failure) is
  independently valuable and testable today (a real network/auth failure
  against blank/placeholder credentials IS the degrade path), and blocks
  nothing about routing correctness on the deterministic side;
  `/plan-tasks`/the coder should still confirm the real request/response
  shape live once credentials exist, per Consequences below.

**Consequences:** `app/data_access/compass_client.py` is the first
direct-to-LLM HTTP client to exist in the post-2026-08-20 architecture —
sets the precedent for any FUTURE direct LLM-provider client (e.g. if
Anthropic Claude's own direct client is ever rebuilt) to live at the same
layer, same shape. Until real Compass credentials are provisioned
(`.env.example`'s `COMPASS_BASE_URL`/`COMPASS_API_KEY`/`COMPASS_MODEL` are
still blank placeholders), every real call exercises the failure/degrade
path (`ADR-012`'s Scenario 6), never the happy path — this is expected
and by design, not a defect; the coder must independently verify the real
request/response contract once credentials exist, since this ADR does
not (and cannot yet) confirm Compass's own live API shape. Every future
reader who encounters a stale `ADR-022` citation elsewhere in this
codebase (existing code comments/task files are NOT retroactively edited
by this ADR — specs/task files are append-only/historical) should treat
it as referring to dead, pre-2026-08-20 history, not a live decision —
this ADR is the one to cite going forward for `has_real_client`/
direct-LLM-client questions.

---

## ADR-012: Cockpit routing becomes LLM-primary with the existing deterministic scorer demoted to an explicit degrade path; a short-reply shortcut and a reply-to-message hint are additive fields on `ADR-007`'s own chat_store schema, not new stores or a hard override

**Status:** Accepted
**Date:** 2026-08-31

**Context:** `REQ-SB-82-US-06` resolves a real, reproduced bug (operator:
"When an Agent Respond to something and I say Yes a different Agent
Picked the thread") plus two related capabilities the operator asked for
while designing the fix: an always-on LLM-based routing pass for
substantive questions, and a reply-to-message hint in both Cockpit and
the single-agent Chat panel. `chat_turn.py`/`moderator.py` (`ADR-009`,
`REQ-SB-82-US-04`, both confirmed live and shipped per `ESC-059`'s
resolution) already own a real, working deterministic routing pipeline:
`route_question` (tokenized keyword overlap, scoped to the brought-in
roster), an `@mention` override, a tie-break that falls back to the
Research Agent, an honest "no one here matches, try X" suggestion, and a
Customer-Section fallback. None of this is being discarded — a
low-signal reply like "Yes" defeats keyword-overlap scoring structurally
(no domain vocabulary to match against), which the new Compass-backed
reasoning pass and a new short-reply shortcut both address, each for a
different failure mode.

**Decision:**
1. **The short-reply shortcut is a pre-routing check inside
   `chat_turn.py::send_user_message`, checked BEFORE any moderator call
   (deterministic or LLM) is made** (Scenario 1: "no full moderator
   routing decision... is needed to reach that outcome"). It reads a
   new, additive field on the SAME per-subject entry `ADR-007`'s
   `chat_store.py` already owns — `last_answering_agent_id: str | None`
   (plus `last_answering_agent_name`, mirroring every other
   agent-reference pair already in this schema) — set by
   `_dispatch_reply` whenever a real agent reply is actually dispatched
   (Expert, Research Agent, or Customer-Section fallback alike; whoever
   most recently answered, not just permanently-brought-in Experts).
   When no such field is set yet for a subject (Scenario 7: nobody has
   answered anything in this thread yet), the shortcut structurally
   cannot fire and the message falls through to normal routing — an
   absence-of-data check, not a separate flag. The exact short-reply
   DETECTION rule itself (length threshold vs. fixed vocabulary vs.
   both) is deliberately left to `/plan-tasks`'s decomposer/the coder,
   per the story's own Constraints — this ADR fixes only the
   mechanism's shape and its schema dependency, not the literal rule.
2. **The LLM-based moderator (composing `ADR-011`'s `compass_client`)
   becomes the PRIMARY routing decision for every message the
   short-reply shortcut doesn't catch** — the operator's own explicit
   "always on" choice (never gated to ambiguous-only cases). It lives in
   `app/business/cockpit/moderator.py` (a new function, sibling to the
   existing `route_question`/`match_domain_experts`/etc. — same module,
   not a new file, since it is one more real routing TRACK this module
   already owns the concept of) and reasons over the brought-in Experts'
   own `name`/`description`, the recent conversation history, and the
   new message's own text — real reasoning, not another keyword
   heuristic.
3. **`route_question`'s existing deterministic scoring is retained,
   unmodified in its own logic, and demoted to the explicit degrade
   path** (Scenario 6) — `chat_turn.py` calls the LLM moderator first;
   any Compass client failure (network error, timeout, non-success
   response — `ADR-011`'s own dedicated exception type) is caught
   explicitly and falls through to the existing `route_question`/
   `suggest_expert_for_question`/Customer-fallback chain exactly as it
   already runs today, never a broken chat and never a silently
   fabricated routing decision. This mirrors `_reply_via_agent`'s own
   already-proven try/except-degrade shape for a Hermes-side failure —
   the same honesty posture applied one level up, at the routing
   decision itself rather than the reply-generation step.
4. **Reply-to-message in the Cockpit is a hint fed into the LLM
   moderator's own reasoning context, never a hard override** (Scenario
   3, 5) — implemented as: the outgoing `POST .../message` endpoint
   accepts an optional `reply_to_message_id` from the caller (new,
   `chat_turn.send_user_message` gains the same optional parameter
   `chat_store.append_message` already accepts internally — additive to
   an existing internal mechanism, not a new concept); when present,
   `chat_turn.py` resolves the referenced message's own text from the
   thread and includes it as extra context in the LLM moderator's
   prompt, alongside the brought-in roster and recent history. The
   moderator's own reasoning still decides the answering Expert — a
   reply-to hint pointing at one Expert's prior message can still route
   elsewhere when the new message's own content clearly belongs to a
   different Expert's domain (Scenario 5), by construction: the hint is
   one more input to the SAME reasoning pass, never a separate override
   branch that could short-circuit it.
5. **Reply-to-message in the single-agent Chat panel (Scenario 4) is
   architecturally out of this ADR's scope** — `AgentChatPanel.tsx`'s
   own send path is a stateless streaming call with no message-id/
   persistence concept and no `chat_store`/Cockpit backing at all
   (confirmed directly, story Context); "only one agent exists there, so
   reply-to never changes who answers" needs no chat_store schema change
   and no LLM-moderator involvement — a lighter-weight, client-side
   context-anchoring mechanism (attach the referenced message's own text
   to the outgoing request) is the shape `/plan-tasks` should cut a task
   for, separately from anything this ADR governs. **No backend schema
   change is needed for this surface.**
6. **A stale/unresolvable reply-to reference never breaks the chat**
   (Scenario 8) — both surfaces treat a reply-to reference that can't
   be resolved against the current thread (e.g. stale client state after
   a reload) as absent: the message still sends and routes normally,
   with no error state rendered for the unresolved reference. This is a
   plain defensive-read contract on whichever layer resolves the
   reference (Cockpit: `chat_turn.py` against the real thread; Chat
   panel: the client's own local message list) — not a new mechanism of
   its own.

**Alternatives Considered:**
- *Gate the LLM moderator to ambiguous cases only (fall back to the
  cheap deterministic scorer first, escalate to Compass only on a
  tie/no-match)* — rejected per the operator's own explicit "always on"
  resolution (Constraints): a real reasoning pass over the actual
  roster/history/message is the operator's own stated fix for "a
  coincidental keyword match," not a mechanism reserved for edge cases.
- *Make reply-to-message a hard override* (route directly to whoever
  sent the referenced message, skip the moderator call entirely) —
  rejected: directly contradicts Scenario 5's own explicit requirement
  that a reply-to hint must not override a question that clearly belongs
  to a different Expert's domain; a hard override would also silently
  defeat the "always on" LLM reasoning decision above for any
  reply-tagged message.
- *A second, separate JSON store for `last_answering_agent_id`*
  (mirroring the "why not a second recommended_agent_ids store" question
  `ADR-009` already answered) — rejected for the same reason `ADR-009`
  gave: it's the same real per-subject concept (this conversation's own
  live state) viewed one more way; splitting it into its own file would
  mean two reads/writes per message with no benefit and a real risk of
  drift.
- *Detect the short-reply case with an LLM call too* (ask Compass "is
  this a low-signal acknowledgment?") — considered, rejected for this
  pass: Scenario 1 explicitly requires that NO full moderator routing
  decision is needed to reach the shortcut outcome; using an LLM call to
  decide whether to skip the LLM call is circular and adds latency/cost
  to the exact case (a bare "Yes") that most needs to be instant. A
  plain, cheap, deterministic detection rule (exact shape left open)
  satisfies the Scenario without this cost.
- *Persist reply-to-message resolution server-side for the Chat panel
  too* (build a lightweight `chat_store`-style store for it) —
  rejected for this pass, matching the story's own Context finding that
  this surface has zero persistence today and Scenario 4 needs none
  (context-anchoring for the CURRENT turn only, no cross-reload
  requirement asserted by any Scenario); revisit only if a future
  requirement needs this surface's history to survive reload the way
  Cockpit's already does.

**Consequences:** `CockpitThread`'s per-subject schema (`ADR-007`,
extended by `ADR-009`'s `recommended_agent_ids`) gains a second additive
field, `last_answering_agent_id`/`last_answering_agent_name` — same
honest-empty-until-set convention as every other field in this store,
backward-compatible with every subject entry that predates this story.
`moderator.py` now owns three independent routing tracks (deterministic
`route_question`, the new LLM-based track, plus the pre-existing
recommendation-matching tracks) — worth a documentation pass inside that
module (already underway via this ADR + its own docstring conventions)
so a future reader doesn't mistake it for a single-mechanism file. Every
Cockpit routing decision now has a real, external network dependency
(Compass) in its primary path for the first time — the degrade path
(point 3) is what keeps this safe; `/plan-tasks`/the coder must verify
the degrade path live (a genuine Compass failure/timeout, not just a
code read) before this ADR's honesty guarantee (Scenario 6) can be
trusted in production, matching this project's own standing
"live-verify a disclosed-but-unconfirmed claim" discipline. The
single-agent Chat panel's reply-to mechanism (point 5) diverges in shape
from Cockpit's own — a future reader should not assume the two
"reply-to-message" features share one implementation; they share only
the same user-facing verb.

---
