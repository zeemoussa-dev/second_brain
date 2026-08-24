# Backend architecture redesign — working draft

**Date:** 2026-08-20
**Status:** In progress — collaborative design session (operator + assistant
acting as Architect/Business Analyst), no sprints/no formal pipeline agents
(per operator direction, same session). Executes `ADR-059` (Hermes becomes
the agent/skill/schedule/approval runtime; Second Brain's backend narrows
to a data layer of Tools/Skills). Sequence being followed: Blocks → Schema
+ Source Areas → Code Empty Files (skeleton) → Fill as needed. Currently at
the Blocks/skeleton stage; nothing has been filled in yet — every folder
below is an empty `__init__.py` skeleton only, no logic moved.

A full, working copy of the pre-redesign backend is preserved at
`Backend-Backup/backend-2026-08-20/` — the migration source once blocks
start filling.

## Data taxonomy (operator-defined, 2026-08-20)

Three data types:
1. **System Data** — Second Brain's own operational state needed to run.
2. **Hermes/LangGraph Data** — needed for their own execution; explicitly
   NOT ours to own or build a data-access layer for.
3. **Vault Data** — the real Obsidian vault: OKF directories/notes with
   frontmatter on top.

Real, current-code evidence for why this split matters: `vault_writer.py`
(2,933 lines) conflates types 1 and 3 today — ~2,300 lines are genuine
Vault operations, but ~600+ lines are `_STATE_DIR = ".second-brain"`
System Data (agent registry, schedules, pending approvals, working modes,
skills, providers, sections, cockpit threads, knowledge gaps, agent
prompts). The data itself is also physically co-located: `.second-brain/`
lives *inside* the vault path (`<vault>/.second-brain/`), not in a
Second-Brain-owned location — `agent_pending_approvals.json` (736KB) and
`agent_communication_history.json` (366KB) sit right next to real OKF
notes.

## Blocks agreed so far

### Data Access Layer

- **`app/data_access/vault/`** — created 2026-08-20. Owns real Vault
  content only.
- **`app/data_access/system/`** — created 2026-08-20. Owns Second Brain's
  own operational state (today's `.second-brain/*.json` stores).
  - **`app/data_access/system/provider/`** — created 2026-08-20. The
    lowest point in the system — depends on nothing else here. See
    "Provider schema" below.

### Business Layer

Business layer talks to 4 things (operator's framing): Hermes, LangGraph,
Second Brain Core, Vault. Five sub-blocks, created 2026-08-20:

- **`app/business/logic/`** — the actual business rules (email/meeting/
  todo classification, Customer/Partner/People linking, Thread synthesis,
  Housekeeping, etc.). Orchestrates across the other four; owns no
  data-access logic itself.
- **`app/business/vault/`** — business-shaped operations over Vault
  content, sits on top of `data_access/vault/`.
- **`app/business/core/`** — Second Brain's own **Business Entities**.
  Distinct from Data Access's `system/` (operational bookkeeping) — this
  is a different concept, not the same thing renamed. **Definition still
  open** (see below).
- **`app/business/hermes/`** — talks OUT to Hermes' own REST API gateway.
  No data-access layer beneath it — Hermes owns its own data. Migration
  source: today's `hermes_status.py` (`get_health`/`get_capabilities`/
  `get_jobs`/`get_sessions`).
- **`app/business/langgraph/`** — invokes/manages LangGraph execution. No
  data-access layer beneath it either, same reason.

### API Layer

**Decided 2026-08-20: no block-folder restructuring needed.** Every
router file is already single-purpose (one file per concern) — the
conflation problem the other two layers had doesn't exist here. Stays a
flat `api/` folder.

One nuance raised, not yet resolved (see Open Questions): `mcp_server.py`/
`mcp_auth.py` are the *reverse-direction* interface (Hermes/LangGraph
calling **into** Second Brain), conceptually different from every other
router in `api/` (Second Brain calling out to its own frontend). Operator
called this "the wrong place" — no destination decided yet.

## Schema decisions

### Provider (`data_access/system/provider/`) — DECIDED 2026-08-20

Operator delegated schema-naming authority directly ("Schema Names is
your job I do Mistakes you know what's needed if you don't know do
Research") — decided, not re-asked. Defined in `data_access/system/
provider/schema.py` as a plain `@dataclass`, matching this codebase's
existing dict/dataclass style (no pydantic model — not used for
`.second-brain/`-shaped state elsewhere in the current code):

`id`, `name`, `description`, `icon`, `url`, `api_format`, `api_key`, `model`.

Resolution of the original "API" ambiguity — split into two fields,
because both are genuinely needed, not because one reading won:

- **`api_format`** — the wire protocol/adapter type
  (`API_FORMAT_OPENAI_CHAT_COMPLETIONS` / `API_FORMAT_ANTHROPIC_MESSAGES`
  today, grows as new providers are added). A real, previously-missing
  gap: Compass speaks an OpenAI-chat-completions-shaped wire format,
  Anthropic uses its own native Messages API SDK — genuinely different
  integration code per provider, hardcoded per-client today with no
  data-driven dispatch at all.
- **`api_key`** — the actual credential, renamed from `provider_
  registry.py`'s current `credential` field to match the naming already
  established in `config.py` (`compass_api_key`, `anthropic_api_key`).
- **`id`** — kept as a stable slug/identifier separate from `name` (name
  is editable; `id` is what assignments/lookups reference).
- **`description`, `icon`** — new, pure display metadata, no current
  equivalent, no open question.
- Noted, not resolved here: today's real stored data
  (`.second-brain/agent_providers.json`) keeps the credential in plain
  JSON, unencrypted — likely an accepted tradeoff for a single-user
  personal app, but a conscious choice to revisit when this block's
  storage (not just its schema) gets built.

## Tools / Categories / Actions (decided 2026-08-20)

Second Brain's own exposed framework, one level below the Business layer's
`logic/` block:

- **Tool** = an MCP server. Each Tool (Outlook, Vault, Housekeeping, etc.)
  is its OWN separate MCP server/mount — not one shared `mcp_server.py`
  exposing everything (the current pattern). Matches the actual common
  MCP-ecosystem convention (one server per tool/service), not a deviation
  from it. Resolves the parked "MCP boundary placement" question: instead
  of one `api/mcp_server.py`, each Tool folder owns its own MCP server
  instance, and the API layer mounts each one at its own path (e.g.
  `/mcp/outlook`, `/mcp/vault`).
- **Category** (renamed from "Entity") = a subfolder inside a Tool, e.g.
  `email/`, `calendar/` inside `outlook/`.
- **Action** (renamed from "Skill" — operator-confirmed, to avoid colliding
  with Hermes' own distinct "Skill" concept at `/v1/skills`) = an
  individual callable function inside a Category, e.g. `send_email`,
  `create_meeting`.
- Tool prefix drops from the registered MCP tool name once Tool = the MCP
  endpoint itself (which Tool you're talking to is already implied by
  which MCP server you connected to) — `send_email`, not
  `outlook_email_send_email`. Category prefix may still be worth keeping
  (`email_send_email`) if the same Action name could recur across
  Categories.
- Folder home: nests inside `business/logic/` (e.g.
  `business/logic/outlook/email/`), since Tools/Categories/Actions
  genuinely ARE the business rules, not a new top-level block.

**Bulk data principle (decided 2026-08-20):** Actions stay atomic and
bounded/paginated, always — never an unbounded internal loop. Real
evidence this is already how the codebase leans: `email_pull.py`'s
current `pull_and_stage_emails(limit: int = 10)` is already bounded, not
a fetch-everything call. A bulk/retrofit operation (e.g. a large
historical email backfill) is never one Action call — it's the same
bounded Action called repeatedly by something else that owns the
looping/progress/resumability (a Hermes Job via `/api/jobs`+`/v1/runs`,
or a LangGraph loop node for a Second-Brain-owned flow). Bulk handling is
an orchestration-layer concern, not baked into the Action itself.

## Capture trigger (decided 2026-08-20, corrected same day)

**First answer (superseded, kept here for the reasoning trail, not
deleted):** a hybrid — routine capture stays a Second-Brain-owned local
`capture_scheduler.py` timer, only bulk/retrofit uses Hermes Jobs.
Operator correction: this quietly reintroduces "2 things doing the same
task" — a local scheduler AND Hermes' own Job scheduler running in
parallel — exactly the duplication this whole pivot exists to eliminate.
The reliability worry behind it (keep working if Hermes is down) wasn't
checked against the actual committed direction before being used to
justify keeping a second mechanism alive.

**Corrected decision: one scheduling engine only — Hermes' Job system —
for both routine and bulk capture.** Second Brain owns no scheduler of
its own. "Schedule" in our own codebase is a thin wrapper/facade (lives in
`business/hermes/`) that creates/manages the underlying Hermes Job
pointing at our bounded Action — never a local timer loop. Routine hourly
capture and bulk/retrofit both go through the same mechanism, just
configured differently (recurring cadence vs. on-demand).
`capture_scheduler.py`'s own APScheduler-driven timer is retired outright
once a Hermes Job replaces it — not decoupled-and-kept as a fallback.
Framed engine-agnostic on purpose: LangGraph Platform (if ever deployed
that way) has its own native Cron concept too, so the wrapper should wrap
whichever of Hermes/LangGraph actually owns scheduling for a given task,
not be hardcoded to one.

**Known, accepted tradeoff:** if no Hermes gateway is running, nothing is
scheduled at all — no local fallback hedging against that. Accepted as
the right cost given the committed direction ("utilize the platform to
the max") — a missing Hermes deployment is an ops gap to close, not a
reason to keep a second scheduler alive "just in case."

## Tools registry mounting mechanics (built 2026-08-20, corrected same day)

`data_access/system/tools/schema.py` (Tool/Category/Action dataclasses),
`registry.json` (the declarative data), `registry.py` (load/resolve/
mount/reload) — built and verified live (real `FastMCP.tool()` signature
checked, not assumed; mount/re-mount/NotImplementedError-stub behavior
tested end-to-end).

**Two errors caught by the operator, corrected same day:**

1. **Outlook is not a business object.** First attempt created `business/
   logic/outlook/email.py`/`calendar.py`, mirroring the Tool/Category
   structure 1:1 into `business/logic/`'s own folder layout. Wrong —
   "outlook is a Tool inside an MCP Server," a pure registry/exposure
   concept; the actual business logic underneath is purpose-named (e.g.
   "get outlook emails"), not organized to mirror Tool/Category folders.
   Reverted: `business/logic/` is empty again (skeleton only), `registry.
   json`'s example Tool entries removed (back to `{"tools": []}`) since
   their `handler` paths pointed at the now-deleted, wrong location. The
   mounting mechanics themselves (`schema.py`/`registry.py`) are
   unaffected — they never assumed anything about `business/logic/`'s own
   internal organization, only that `handler` is a valid dotted path once
   one exists.
2. **Icons are Google Fonts (Material Symbols) icon names**, e.g.
   `"mail"`, `"send"`, `"calendar_month"` — never an image/SVG asset, and
   (confirmed separately, live) never MCP's own protocol-level `Icon`
   type either (that needs a real resource `src`, a different concept).
   Applies to every `icon` field in the system, not just Tools/Actions —
   updated in both `tools/schema.py` and `provider/schema.py`.

**Still open, raised by this correction:** what `business/logic/`'s own
internal organization actually looks like, now that it's confirmed NOT to
mirror Tool/Category/Action folders. Not yet decided.

## Ideas noted for later (not blocking, not decided, just tracked)

- **ripgrep for Vault Search.** Real evidence, not just a hunch:
  `vault_search.py` today does plain Python `re` regex scanning over the
  vault, nothing built for fast search at scale. As the vault grows
  (thousands of Thread/message notes), ripgrep is exactly the kind of
  tool built for this — a single, no-install binary, same portable/
  no-admin pattern as the Node.js (`ADR-002`) and portable-Python-3.11
  precedents. Noticed 2026-08-20 while watching Hermes' own installer
  fetch ripgrep for its OWN toolchain — that copy stays Hermes' own
  (outside the Second Brain repo, per the earlier "where to install
  Hermes" decision); if Second Brain wants ripgrep, it's a separate,
  Second-Brain-owned dependency. Revisit when actually building out the
  Vault Tool's search Action, not before.

## Hermes REST client rebuilt against the real, verified protocol (2026-08-20)

The original `hermes_client.py` (built from research before a real Hermes
instance existed) was wrong: wrong port (8642, not 9119), wrong auth shape
(bearer API key, not a page-embedded session token), wrong endpoint paths
(`/health`, `/v1/chat/completions`, `/api/jobs` -- none of these are real).

Real protocol, found by actually installing Hermes and inspecting a live
browser session's own network traffic (monkey-patched `window.fetch` to
capture headers, confirmed by independently replaying the captured header
via a plain `curl` outside the browser):

- Base URL: `http://127.0.0.1:9119` (`hermes serve`'s own real default).
- Auth: `GET /`'s own HTML embeds `window.__HERMES_SESSION_TOKEN__ = "..."`
  -- a per-install access token (not a login credential; `auth_required:
  false`), fetched once and cached, sent as `x-hermes-session-token` on
  every subsequent call.
- Real endpoints: `/api/status` (public, no token needed), `/api/sessions`
  (real Agent/session data -- model, message count, token/cost
  accounting), `/api/sessions/stats`, `/api/config`, `/api/profiles/active`.

`hermes_client.py`/`hermes_status.py`/`hermes_router.py` rebuilt around
this and verified end-to-end THREE layers deep against the actual running
Hermes instance: raw client function → business wrapper → a real booted
FastAPI app's own `/hermes/status`/`/hermes/sessions` routes, all
returning real data (version `0.20.4`, 1 real session, real stats). This
directly answers the original "can we see Agents" open question from
earlier -- yes, `/api/sessions` gives real, rich visibility.

**Also directly answers the deferred `core`/Business Entities framing**
(operator, same day): Hermes has real execution power but zero
understanding of Second Brain's own business concepts. Second Brain's
role is "Builder Orchestrator" -- it OWNS the business understanding
(`core`) and uses it to actively build/infuse what Hermes needs (Tools,
schedules, memory), not just passively expose raw data. Three concrete
infuse mechanisms named, not yet built: registering our own Tool MCP
servers into Hermes automatically, creating Hermes cron jobs from our own
business-driven schedule decisions (matches the earlier "one scheduling
engine" decision), and pushing relevant vault knowledge into Hermes' own
persistent memory store. All three should be driven by `core`'s own
business logic, not flat/mechanical syncing.

## First real Action built: Outlook -> Email -> gather_emails (2026-08-20)

`business/logic/gather_emails.py` -- purpose-named, NOT nested under an
`outlook/` folder (matches the earlier Business-Object correction). Thin
wrapper over `pipelines/email_pull.py`'s own real, unmodified
`pull_and_stage_emails` -- no reimplementation. Registered in
`data_access/system/tools/registry.json` (Outlook Tool -> Email Category
-> `gather_emails` Action). Verified live: `load_tools_registry`/
`resolve_handler`/`_build_mcp_server_for_tool`/`mount_all_tools` all work
correctly against this real entry -- WITHOUT invoking `gather_emails()`
itself (that would trigger a real Outlook COM call + real email staging;
deliberately not run during this verification).

Built as the first concrete step toward "How to build the Email Gathering
Pipeline in Hermes": `hermes mcp add outlook --url <endpoint>` registers
this as a Hermes-reachable MCP server once mounted on the live app; a
`hermes cron create "every 2h" --no-agent --script ...` (or a plain
prompt, for judgment-requiring cases) is the actual schedule/trigger,
matching the earlier "one scheduling engine, Hermes owns it" decision.
**Now wired into `main.py` and fully verified live (2026-08-20).** Two
real bugs found and fixed along the way, neither guessed -- both
confirmed via a real booted app and real HTTP probes:

1. **A mounted Tool's own MCP server never initializes its Streamable
   HTTP transport unless its `session_manager.run()` lifespan is entered
   explicitly** -- the exact same gap `api/mcp_server.py`'s own mount
   already had to work around in `main.py`'s lifespan; `mount_all_tools()`
   alone (called at module level, mirroring `mcp_server`'s own mount) was
   not enough. Fixed: `registry.py` now tracks the built `FastMCP`
   instances (`_mounted_servers`, not just ids) and exposes
   `enter_tool_server_lifespans(stack)`, called from inside `main.py`'s
   lifespan alongside `mcp_server.session_manager.run()`.
2. **`/mcp/outlook` silently 404'd even after fix 1** -- Starlette matches
   mounts in registration order; the pre-existing `/mcp` mount (registered
   first) swallows ANY path starting with `/mcp/`, including
   `/mcp/outlook/*`, before a later, more-specific mount ever gets a
   chance. Fixed by giving Tool mounts their own non-colliding prefix:
   `mount_path` changed from `/mcp/outlook` to `/tools/outlook` in
   `registry.json` (and `schema.py`'s own docstring now documents why).

Verified: a real booted app now answers `/tools/outlook/` with the exact
same real MCP protocol response (`406 Not Acceptable: Client must accept
text/event-stream`) as the long-working `/mcp/` mount -- genuine proof,
not assumed.

**Still not done:** actually registering this endpoint with Hermes
(`hermes mcp add outlook --url http://127.0.0.1:<port>/tools/outlook`)
and creating the cron job -- both real, verified CLI commands (see the
"Email Gathering Pipeline in Hermes" exchange), not yet executed.

## Output-specific Actions vs. write Actions (decided 2026-08-20)

Operator: "I need the MCP Server to Be output Specific, Writing to the
Vault should be Hermes Agent job." A fetch/read Action must return real
data for the agent to reason about and have NO side effects of its own
(no staging, no vault write) -- deciding whether/how to persist anything
is a separate, explicit tool call the AGENT makes, never bundled into the
read Action itself.

This is why `gather_emails` (fetch + stage, bundled) and the new
`list_recent_emails` (fetch only, real content, zero side effects) exist
as two SEPARATE Actions, not one. `gather_emails` still wraps the
existing `pull_and_stage_emails`, kept as-is deliberately -- its bundled
fetch+stage shape is a genuine, documented reliability property (stages
incrementally inside the Outlook COM loop so a mid-loop stall never loses
already-fetched items), still needed by `capture_scheduler.py`'s own
routine local pull, not yet migrated. `list_recent_emails` is the new,
agent-facing, output-only Action -- calls `outlook_com.list_recent_mail`
directly, never through `email_pull.py`.

Along the way, `outlook_com.list_recent_mail` gained an additive `since`
parameter (ISO 8601 datetime string) -- filters via `items.Restrict()`,
matching this same file's own existing `list_upcoming_meetings` date-range
convention (server/COM-side filtering, never a Python-side loop-break that
would still walk every older item just to discard it). Zero behavior
change for existing callers that don't pass it.

## MCP server vs. Hermes-native Skill scripts -- settled, MCP server stays (decided 2026-08-21)

Operator challenge, in two steps: "In the skills folder we can add the
Python file, why do we need our MCP Server?" then, after pushback, "I
don't need MCP Server, I think Hermes will pull the dependencies of the
Py file when needed, try that" -- backed by a real, live observation:
"When I sent a file to WhatsApp, Hermes pulled a library to read the file.
I want our Skills to be the same, fully hosted in Hermes, no use of our
venv."

Investigated two real Hermes source files before answering, not guessing:

- `tools/code_execution_tool.py` -- `_resolve_child_python(mode="project")`
  (the default) uses whatever `VIRTUAL_ENV`/`CONDA_PREFIX` is already set
  on Hermes' OWN process; it does not auto-discover a project's `.venv`
  from cwd/workdir. Falls back to Hermes' own `sys.executable` otherwise.
- `tools/lazy_deps.py` (read in full, ~1243 lines) -- confirmed the real
  mechanism behind the WhatsApp observation: `LAZY_DEPS` is a static,
  curated allowlist (`{"tool.doc_extract": ("firecrawl-anydoc==0.1.6",),
  ...}`) mapping Hermes' OWN known built-in features to exact pip specs.
  `ensure(feature)` installs the mapped spec into Hermes' own active venv
  (uv -> pip -> ensurepip ladder) the first time that specific, already-
  registered feature is used -- e.g. `read_file` against a doc-type file
  triggers `tool.doc_extract`. Unknown/arbitrary feature keys are
  rejected (`FeatureUnavailable`). A more permissive `install_specs()`
  exists for data-driven package lists (e.g. plugin manifests) but still
  validates every spec (`_spec_is_safe()` -- no URLs/paths/shell
  metacharacters) and still installs into Hermes' own environment.

**Decision:** confirmed real and correctly explains the WhatsApp
behavior, but it does not change the MCP-server decision, for two
independent reasons:

1. It is a closed allowlist keyed to Hermes' own registered features --
   nothing about a brand-new Skill script would make Hermes "know" to
   lazy-install anything for it. `pywin32` (needed for the Outlook COM
   layer) is not, and could not become, a `LAZY_DEPS` entry without
   Hermes' own maintainers registering it as a Hermes feature.
2. Even granting arbitrary third-party pip installs, the real dependency
   was never a pip package -- it's Second Brain's own source tree
   (`app.business.logic.*`, `app.data_access.vault_writer`, etc., the
   whole tested business layer built this session). Lazy-installing pip
   packages into Hermes' venv cannot make Hermes import Second Brain's
   own private modules; the only way to run that logic Hermes-natively
   would be to duplicate/copy it into the Skill's own files, recreating
   the exact "two places holding the same logic, one silently drifts"
   problem already rejected earlier for the old scheduling machinery
   (see ADR-001's own context).

Operator, presented with this evidence: "Okay so no way except the MCP
Server" -- confirms the MCP server approach stands. No further action
needed on this thread; the `vault` Tool/MCP server built this session
(`ingest_email`, `rename_thread`, `link_person_to_thread`,
`capture_attachments`, `capture_file_link`) is the real, final shape.

**Alternatives considered (for the record):** Hermes-native Skill script
using `lazy_deps.ensure()`/`install_specs()` for its own dependencies,
with Second Brain's business-layer source either duplicated into the
Skill folder or reached via explicit `PYTHONPATH`/`sys.path` wiring from
within the script. Rejected: duplication reintroduces drift risk;
`PYTHONPATH` wiring still leaves `pywin32` unresolved (not in
`LAZY_DEPS`) and ties a Hermes-hosted script to Second Brain's own
on-disk layout and separately-managed dependencies -- strictly more
fragile than the already-working MCP mount, for no real gain.

Verified live: both Actions resolve and mount correctly through the Tools
registry -- WITHOUT actually invoking either (both would trigger real
Outlook COM calls; deliberately not run during verification, same
discipline as `gather_emails`'s own verification earlier).

## Hermes Skills, real shape (researched 2026-08-20)

From https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills/:
a Hermes **Skill** is a markdown instruction file (`skills/<category>/<skill-
name>/SKILL.md`, YAML frontmatter -- `name`, `description`, `requires_tools`/
`requires_toolsets`, etc.), not callable code. It's a documented PROCEDURE
telling the agent how to accomplish something using tools it already has
(`terminal`, `web_extract`, or MCP-provided tools) -- the agent reads the
instructions and decides which tool calls to make; a Skill never gets
executed directly the way a function does.

This confirms the earlier Skill->Action rename was correct, and sharpens
the layering: our Tools/Actions (`gather_emails`, `list_recent_emails`,
etc.) are the actual callable capabilities; a Hermes Skill is the RECIPE
that tells an agent how to use them for a specific business procedure --
the real, concrete mechanism for both "Hermes to Enrich" and "Hermes
Agents as Section Experts" (the 3-part framework, operator, 2026-08-20):
a Skill per business domain (email processing, company review,
housekeeping) encodes Second Brain's own business expertise as
instructions, using our MCP Tools as the hands. Not yet built -- next
real step once Layer 1 (data in) is fully proven end-to-end.

Real CLI commands: `hermes chat --toolsets skills -q "..."` to test one,
`hermes skills install`/`publish` to install/share.

## Hermes-Provisioning/ folder (created 2026-08-20)

Repo-root folder (same pattern as `Backend-Backup/`/`Documentation-
Archive-2026-08-20/` -- not Second Brain's own application code, so not
under `src/`) capturing Hermes' own configuration as version-controlled
files: `config/` (config.yaml snippets), `mcp-servers/` (registrations),
`cron/` (scheduled job declarations), `skills/` (SKILL.md files). Purpose
(operator): redeploy Hermes in seconds instead of manually rediscovering
tonight's setup steps and bugs again. Already captures the two real,
hard-won fixes from tonight: the corrected Compass `custom_providers`
entry (the base_url double-append bug) and the `outlook` MCP server
registration. See its own README.md for the full workflow.

## Hermes deep-dive (2026-08-20) — real API/CLI/config ground truth

Read Hermes' own real source (`hermes_cli/web_server.py`,
`web_routers/*.py`, `agent_runtime_helpers.py`, `auth_commands.py`) end to
end for the parts relevant to integration, per the operator's own
"be expert in Hermes... avoid surprises" instruction. Full findings saved
to durable cross-session memory (not just this doc, since this is
reusable knowledge beyond this one project) -- see the assistant's own
memory file `reference_hermes_agent_internals.md`.

Highest-value single finding: **`/api/model/*` (info, options, set, moa,
auxiliary) is the real, intended way to change model/provider config** --
using it instead of manual `config.yaml` editing would very likely have
caught the base_url double-append bug immediately (a `GET /api/model/
info` after setting it would show the resolved base_url actually in use),
rather than the multi-round manual-edit-and-retry cycle it actually took.
Worth using the API over raw config edits from now on for anything
model/provider-related.

Also confirmed: Hermes' own `request_dump_*.json` files (written
automatically to `logs_dir` on every API 4xx) are the fastest real
debugging tool for any future Hermes provider/API failure -- check there
before guessing, same as how the base_url bug was actually root-caused.

## Vault rebuild pipeline (2026-08-20) -- one-time, full-history Outlook -> Thread rebuild

**Context:** operator deliberately cleared the vault (confirmed, not
accidental) to rebuild it properly through Hermes, one time, with a
separate incremental pipeline to follow later. Not a data-loss incident.

Built so far, real and verified (load/resolve/mount tested, no actual
Outlook/vault I/O triggered):
- `outlook_com.list_recent_mail` gained `before` (symmetric to `since`) --
  makes a full historical walk possible: an agent pages backward through
  time via repeated calls, each time setting `before` to the oldest
  `received` seen in the previous page. Still one bounded page per call
  (Bulk data principle) -- the walking/pagination decision belongs to the
  agent/cron job, never a loop inside this function.
- New **Vault Tool** (`/tools/vault`, separate from Outlook Tool) --
  Write Category -> **`ingest_email`** Action: given one real email,
  creates its Thread note on first sight of the conversation_id
  (`thread_name` = that email's own subject) and writes the message if
  not already present. Idempotent, safe to call more than once. Built
  directly on `vault_writer.py`'s own already-proven OKF primitives
  (`create_thread_note_baseline`, `create_raw_message_note`,
  `thread_note_exists`, `raw_message_note_exists`) -- zero new
  OKF-writing logic invented, per "minimal code."

**Decided, real architectural point (operator asked directly, 2026-08-20):
should Hermes just write the vault files itself via a prompt + its own
generic filesystem tools, skipping our own write Action entirely? No** --
OKF structure is precise and code-depended-upon (exact frontmatter
fields, slug algorithm, message filename hashing, idempotency rules);
letting an LLM freehand-write files risks exactly the kind of
under-specified-logic data-quality bug that caused BUG-031/032/033
earlier tonight, and risks the schema being encoded in two places (our
Python AND Skill prompts) that drift apart when it changes. The agent's
real job is deciding WHETHER/WHEN to write (call the Action); the Action
enforces HOW it's written correctly.

**Single-email test run (2026-08-21), real, verified:** `list_recent_emails`
+ `ingest_email` produce correctly-structured Thread and Message notes,
matching the proven OKF conventions exactly (inspected the real file
content, not assumed).

**Readability fixes (2026-08-21, both operator-flagged, both fixed and
verified):**
1. Thread directory names were the raw, unreadable `conversation_id` hex
   string. New **`rename_thread`** Action (Vault Tool -> Write), reusing
   `vault_writer.rename_thread_directory` (already-proven primitive, no
   new rename mechanics) -- relabels to `<date> <subject>`, matching the
   old system's own proven 2-stage pattern (create at a stable ID-based
   path first, rename to something readable second -- avoids collision
   risk during bulk capture). Fans the new name out to every message's
   own `thread:` frontmatter. A real bug was caught by testing idempotency
   BEFORE it could hit real data: the first version recomputed the Thread's
   path deterministically from `conversation_id` instead of resolving its
   CURRENT (possibly already-renamed) location via `vault_writer.
   resolve_thread_directory` -- fixed, then verified genuinely idempotent
   (second call on an already-renamed Thread correctly no-ops).
2. Message filenames were `<date>-<hash8>.md` -- also unreadable. Added an
   additive, optional `readable_name` parameter to `vault_writer.py`'s
   `raw_message_note_path`/`raw_message_note_exists`/
   `create_raw_message_note` (same "purely additive, zero behavior change
   for existing callers" discipline as `since`/`before` earlier --
   `raw_message_capture.py`'s own Stage 1 pipeline, a separate still-live
   module using the same primitive, is completely unaffected). When given
   (the sender's name, from `ingest_email`), filename becomes `<date>
   <sender name>.md`, falling back to the hash suffix only on a genuine
   same-day-same-sender collision.

Both verified against two real, different emails (a system alert and a
real business email), inspecting the actual files written each time.

**People-linking Action added (2026-08-21, operator: "add the people
section as well, wiki links to Email and People in the thread"):**
new **`link_person_to_thread`** Action (Vault Tool -> Write) -- ensures a
Person note exists for a message's sender (reuses `people_extraction.
ensure_person_note_for_captured_email`, the SAME real, proven per-write
hook `meeting_classification.py`'s own attendee loop already uses -- no
new Person-note logic invented) and adds a wikilink to it in the Thread's
own `## Related` section, accumulating across multiple senders rather
than overwriting. Required registering a new caller id in `section_
ownership.py`'s deny-by-default allow-list (`link_person_to_thread.
link_person_to_thread` -> `## Related`) -- a genuinely separate pipeline
from `librarian_housekeeping`'s own, never both writing `## Related` for
the same Thread. Kept as its own separate, composable Action (not folded
into `ingest_email`) -- matches the multi-step design; a Skill/prompt
orchestrates the sequence (ingest -> rename -> link_person), same as the
old system's own Job-sequence pattern.

**Real mistake made and caught during testing, disclosed:** first test
call used a fabricated placeholder email instead of the real sender's
actual address, creating one incorrect Person note in the real vault
(`shadi.shaat@example-domain.test.md`) and one stale wikilink pointing at
it. Caught immediately, both cleaned up (note deleted -- a same-session
artifact of my own mistake, not real user data; `## Related` cleared and
re-populated), then re-verified with the real sender_email
(`shadi.shaat@core42.ai`) -- correct Person note created, correctly
tagged `company/core42` (derived from the email domain, existing proven
logic), correctly wikilinked.

**Resolved 2026-08-21: yes, clean the frontmatter too.** `rename_thread`
now also upserts the cleaned subject into the Thread's own `thread_name`
frontmatter field, in the same pass as the directory rename -- no second,
separate step. Verified live with a fresh email.

**Message-level People linking (2026-08-21, operator: "like the People
to Emails as well not only thread" then "not only Sender everyone in the
email"):** `create_raw_message_note` gained an additive
`participant_links: list[str] | None` frontmatter field; `ingest_email`
now ensures a Person note for the sender AND every recipient (the
`recipients` shape `list_recent_emails` already returns per email,
`[{"name","email"}, ...]`), deduplicated by lowercased email, and embeds
all their wikilinks in the SAME write-once pass the message is created
in -- there is no later "patch the links in" step for a message note the
way `link_person_to_thread` has for a Thread's own `## Related`. Verified
live against a real 8-recipient thread: all 9 participants (sender +
8 recipients) got real Person notes and correctly deduplicated wikilinks.

**Attachment capture Action added (2026-08-21, operator: "in the Capture
Phase we will get the file and Add it to the thread under files folder
... file.md next to it with the Source Thread ... Later we will have the
Enrich pipeline for Summarizing").** New **`capture_attachments`** Action
(Vault Tool -> Write) -- deliberately capture-only: saves the real
attachment bytes under the Thread's own `files/` folder and a bare
companion note (empty `## Summary`, a `source_thread` backlink), zero
Compass calls, zero summarization -- that's the explicitly separate,
later Enrich pipeline's own job. Reuses `vault_writer.write_file_
companion` (the SAME real primitive `email_classification.write_file_
companion` already calls one layer up, WITH summarization) -- no new
attachment-writing mechanism invented. Added an additive `source_thread`
parameter to that primitive (only one real caller existed,
`email_classification.py`, unaffected since it's optional).

Also closed a real correctness gap found while building this: `rename_
thread` fanned its new name out to messages' own `thread:` field but not
to file companions' own `source_thread` field, which would have gone
stale after a rename (the files themselves move correctly -- `rename_
thread_directory` already moves the whole tree atomically -- only the
frontmatter TEXT inside each companion note would have kept the old
name). Fixed and verified: renamed a real Thread with a real captured
PDF attachment, confirmed `source_thread` updated to match.

Verified end-to-end against a real email with a real PDF attachment.

**Further refinements (2026-08-21, operator: "Link the file to the email
it came from as well, and include the date in front of the file since we
will have in some threads one file comes multiple times"):**
- `write_file_companion` gained an additive `source_email` frontmatter
  field (a wikilink to the specific message, not just its Thread).
  `ingest_email` now also returns `message_path` so `capture_attachments`
  can build this link without re-deriving it independently.
- `file_slug` now leads with the date (`"<received[:10]> <hash8>-
  <filename>"`) so the same filename attached on different dates is
  visually distinct, not just hash-disambiguated.

**Two real bugs found and fixed while verifying the above, both serious
enough to note in full:**

1. **`raw_message_note_path`'s readable-name collision check couldn't
   tell "this message already lives here" from "a genuine different
   collision.**" Re-resolving an already-written message's own path
   (needed to build the new `message_path`/`source_email` link) wrongly
   treated the existing file as a collision and silently shifted to the
   hash-suffixed form -- fixed by comparing the existing candidate's own
   `message_id` frontmatter before assuming a collision.
2. **`ingest_email` used the wrong, deterministic-from-conversation_id-
   alone existence check (`thread_note_exists`/`thread_directory_paths`)
   instead of `resolve_thread_directory`** -- blind to an already-renamed
   Thread. Calling `ingest_email` again for a message on an
   ALREADY-RENAMED Thread incorrectly reported `thread_created: True`
   and spawned a full second, stray, raw-slug-named duplicate Thread
   directory (its own note, its own copy of the message, its own copy of
   the attachment) alongside the real, renamed one -- exactly the kind of
   data fragmentation this whole rebuild exists to avoid. Fixed to use
   `resolve_thread_directory` consistently (same fix already applied in
   `rename_thread.py`/`link_person_to_thread.py`); the stray duplicate
   (my own test artifact) was found and removed, then the full sequence
   (ingest -> capture) was re-verified clean: correctly reports
   `thread_created: False`/`message_created: False` on a second call,
   both paths resolve to the real, renamed directory, attachment lands
   in the right place with both links correct.

This is exactly the class of bug that would have silently multiplied
across a full bulk pull if it had gone uncaught -- worth being direct
about: real end-to-end testing against real data, not just unit-level
checks, is what surfaced both of these.

**File-link capture Action added (2026-08-21, operator: "files that are
not in the email as attachment but a link to the file somewhere ...
create an MD for this file that will contain the link to it and summary
I will provide later").** New **`capture_file_link`** Action (Vault Tool
-> Write) -- for a file referenced only by URL (e.g. a SharePoint/
OneDrive "shared with you" link), not a real attachment. New sibling
primitive `write_file_link_companion` in `vault_writer.py` (parallel to
`write_file_companion`, no bytes to save since there are none) writes
just the companion note, same date-prefixed `file_slug`/`source_thread`/
`source_email` shape as real captured attachments, with an EMPTY
`## Summary` -- deliberate, per "summary I will provide later," not an
oversight. Deliberately dumb by design: this Action does not detect
whether a URL in an email body is worth capturing -- that judgment call
belongs in a Skill's own prompt, reading the message body; the Action
just persists what the agent has already decided to capture. Verified
live (caught and corrected my own test-input escaping bug along the way
-- a corrupted path string, not an actual code bug -- before confirming
the real, correct output).

**Skill + cron job built (2026-08-21).** `Hermes-Provisioning/skills/
vault-rebuild/email-thread-capture/SKILL.md` -- real YAML frontmatter
(`requires_toolsets: [outlook, vault]`), a full loop spec (paginate via
`before`, ingest -> link person -> rename -> capture attachments/file-
links, per email; stop on an empty page), and explicit rules (never
skip, never summarize, always pass `recipients`, report progress).
Already copied into the real Hermes install
(`<hermes_home>/skills/vault-rebuild/email-thread-capture/`, confirmed
real local path). `mcp-servers/vault.yaml` added for the new Vault Tool
registration (not yet applied -- only `outlook` was registered earlier).

**Not yet done, deliberately left to the operator:** registering the
`vault` MCP server with Hermes and actually running the cron job --
both real commands in `Hermes-Provisioning/README.md`'s own "Running the
one-time vault rebuild" section. This is a genuinely long-running, real
side-effect action (full email history, real vault writes, real LLM
calls) -- not triggered automatically, same discipline as every other
Hermes action tonight with real consequences.

**Not yet built:** the Enrich pipeline (attachment/thread summarization)
-- explicitly a separate, later pipeline per the operator's own scoping.

## Open / parked questions

Track here as they come up; resolve in place (move to "decided" above)
rather than deleting the entry, so the reasoning stays visible.

1. **Approval/Safety gate** — does Hermes' own run-approval mechanism
   replace `pending_approval_registry`/`working_mode_registry` outright,
   or does Second Brain keep its own write-approval gate regardless of
   caller? Operator: "This is a Business Process," revisit when we reach
   that block.
2. **`core` block's real definition, AND `business/logic/`'s own internal
   organization — same discussion, not two separate ones (operator-
   clarified 2026-08-20).** `business/logic/` is organized around Business
   Entities (Customer, Partner, Person, Thread, etc. — whatever the app
   UI actually shows the user), which reflects the app's own conceptual
   model. This is a completely different axis from the backend's own
   technical structure (Tools/MCP servers/Data Access) — the two do NOT
   mirror each other. Confirmed NOT to mirror Tool/Category/Action
   folders (see the Tools-registry correction above). Working definition
   of Business Entities themselves still TBD — revisit when we get there.

## Standing working rules for this redesign (operator-stated, 2026-08-20)

- Challenge the operator directly if something looks architecturally
  wrong — don't just validate.
- Don't create anything until agreement is actually reached, not just
  discussed.
- Purpose right now is skeleton + documentation, not filling in logic —
  that's a later, explicit step.
