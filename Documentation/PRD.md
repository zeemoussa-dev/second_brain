# Product Requirements Document

## Second Brain

A personal knowledge base service that indexes and serves the user's Obsidian
vault directly (no staging/promotion gate — it's trusted personal data, not
agent-written scratch data), integrating with Hermes (an MCP-based multi-channel
communication tool) as a planned integration point. Standalone project for now;
future integration with `agentic-map`'s agents is a deliberately separate, later
decision.

---

<!-- Instructions for filling in this file:
- Each requirement gets a unique ID (e.g. REQ-SB-01).
- Group requirements by roadmap phase (MVP, P1, P2).
- Write requirements from the USER's perspective — what the product must do,
  not how to implement it.
- After writing requirements, run /design on UI-facing ones to prototype
  screens before /spec reconciles stories against them.
- Then run /spec to have the analyst draft user stories.
-->

---

## MVP

### REQ-SB-01: Vault Indexing

The user points Second Brain at an Obsidian vault directory, and it parses and
indexes the markdown notes there — frontmatter, wikilinks, and tags — with no
staging or promotion step. The vault is the user's own trusted personal data,
not agent-written scratch data, so an indexed note is immediately usable; there
is no "pending" or "unreviewed" state to pass through first.

**Acceptance:** Pointing Second Brain at a vault directory produces a complete
index of that vault's notes, correctly capturing each note's frontmatter
fields, outgoing/incoming wikilinks, and tags; re-running the index after the
vault changes picks up additions, edits, and deletions without manual
intervention.

---

### REQ-SB-02: Browse & Search

The user can browse and search their indexed notes directly — no
promotion/approval gate between "indexed" and "usable." Search should be
relevant to real queries, not a bare substring match.

<!-- Ported from agentic-map REQ-008 (Hybrid KB search — make retrieval
relevant to real queries); tool swap only — no Postgres/Qdrant hybrid-search
stack implied, just the same quality bar. -->

**Acceptance:** The user can list/browse all indexed notes, filter or navigate
by tag and by wikilink graph, and run a search query that returns relevant
notes ranked by relevance, not just notes containing an exact substring match.

---

## P1

<!-- Hermes MCP integration for multi-channel communication. -->

### REQ-SB-03: Conversational Agent Access via Hermes

The user can query and converse with their Second Brain through
Hermes-connected channels. The agent reasons over the indexed vault (per
REQ-SB-01/REQ-SB-02) to answer, rather than requiring the user to open the
notes browser directly.

<!-- Ported from agentic-map REQ-015 (OpenClaw-based multi-channel messaging
integration, the precursor to today's Hermes) and REQ-016 (kb_read tool) —
tool swap only: Hermes instead of OpenClaw, the vault index instead of a
Postgres/Qdrant-backed KB. -->

**Acceptance:** From at least one Hermes-connected channel, the user can ask a
question and receive an answer grounded in the indexed vault content, with no
separate "sync to KB" or promotion step required first.

---

### REQ-SB-04: Agent Vault Write Access

A Hermes-connected agent may write back into the vault — not read-only.
Because the vault's trusted status rests on nothing but the user's own edits
having touched it until now, this is a materially bigger trust surface than
read access and needs explicit scoping (what an agent may create/modify, and
under what confirmation) at spec time, not assumed permissive-by-default.

<!-- Ported from agentic-map REQ-019 (kb_write tool implementation); tool swap
only, but scope was an open product decision resolved 2026-08-10 — see
Implementation/Plans/2026-08-10-agentic-map-requirement-port.md. -->

**Acceptance:** A Hermes-connected agent can create or modify a note in the
vault under an explicitly defined scope/confirmation rule (defined at `/spec`
time); writes outside that scope are rejected, not silently allowed.

---

### REQ-SB-05: Content Ingestion Path

Content can enter the vault through a path other than directly editing files
in Obsidian — e.g. an attachment or piece of content arriving via a
Hermes-connected channel lands as a new vault note.

<!-- Ported from agentic-map REQ-035 (Upload data directly to an agent); tool
swap only, scope resolved 2026-08-10 alongside REQ-SB-04 — see
Implementation/Plans/2026-08-10-agentic-map-requirement-port.md. -->

**Acceptance:** Content submitted through a defined ingestion path (channel
attachment, or another surface decided at `/spec` time) results in a new note
in the vault, indexed the same way any Obsidian-authored note would be.

---

### REQ-SB-07: Scheduled Recurring Agent Capture

Capture pipelines (starting with email, per the POC — see MEMORY.md) run
automatically in the background via Hermes, not only on manual trigger: on a
recurring hourly schedule, and once immediately whenever the app starts.
Because Second Brain runs on the user's own laptop rather than a persistent
server, a scheduled run missed while the laptop was off or asleep is caught
up at the next opportunity rather than silently skipped until its next
regular slot.

<!-- Precedent: agentic-map REQ-069 (scheduler catches up on any cron/
skill_cron job missed while the laptop was off, firing it once on wake) —
same underlying problem (personal-laptop-hosted scheduler, not a server),
tool swap only. -->

**Acceptance:** A capture run fires automatically on an hourly cadence and
once immediately on app start; a run missed while the laptop was off/asleep
fires once on the next opportunity instead of waiting for the next
scheduled slot.

---

### REQ-SB-08: Meetings Capture Pipeline

Calendar meetings are captured into the vault the same way email is
(REQ-SB-03's pattern): synced via the Hermes-wrapped Outlook skill,
classified by customer, and filed as Meeting-type notes, on the recurring
schedule from REQ-SB-07.

**Acceptance:** Running the scheduled capture produces one Meeting-type note
per calendar event in the sync window, classified by customer the same way
email is, with no duplicate notes on rerun.

---

### REQ-SB-09: To-Do Task Capture Pipeline

Tasks/to-dos are captured into the vault as their own note type, on the same
recurring schedule as email and meetings. The concrete source of tasks
(Outlook tasks, agent-created follow-ups, manually flagged emails) is an
open question for `/spec` time, not decided here.

**Acceptance:** Running the scheduled capture produces one Task-type note
per to-do item, classified and filed consistently with the email/meeting
pattern, with no duplicate notes on rerun.

---

### REQ-SB-10: People Living Documents

Every person the user communicates with gets a Person-type note in the
vault that accumulates over time — not just contact info (email, phone) but
free-form enrichment the user adds (notes, personality observations, a
LinkedIn profile link, etc.). Background agents create and update baseline
entries as people are encountered (email senders, meeting attendees); the
user can add to any person's note beyond what was auto-captured, and that
manual content must survive later automated updates to the same note.

**Acceptance:** A person first encountered via email or meeting capture gets
a Person-type note with at least name and contact info auto-populated; the
user can add free-form content to that note, and a later automated update to
the same person does not overwrite or remove that manually-added content.

---

### REQ-SB-11: Agent Activity & Error Observability

The user can see, from Second Brain's own UI, what background agent runs
have happened (email/meeting/task/people capture and any future recurring
job) — whether each succeeded or failed — and the current status of
communication channels (e.g. whether the Hermes-wrapped Outlook skill is
currently reachable).

<!-- Precedent: agentic-map REQ-026 (run history/trace store, "Activity
tab" in its console) — same underlying need, Second Brain's own frontend
rather than agentic-map's console. -->

**Acceptance:** The UI shows a chronological list of background agent runs
with outcome (success, or error with detail) and a current status indicator
per communication channel.

---

### REQ-SB-12: Primary Application UI Shell — Agents Map & My Day

The user opens Second Brain to a persistent app shell: a collapsible
burger-menu sidebar for navigating between pages, and a default home page
("Agents Map") that visualizes the Knowledge Base at the center with every
background agent that reads from or writes to it arranged around it,
color-coded by agent type (starting with Worker/Producer/Expert; more types
will be added later without requiring a redesign). From this shell the user
can also reach "My Day" — a dashboard surfacing the day's most important
actions (Emails, Calendar, To-Do, Important Reads), each of which is
clickable and navigates to its own dedicated page — and a Settings page.

<!-- New scope, not ported from agentic-map; captured directly from the
operator's UI vision 2026-08-10 (see Implementation/Plans, if a plan doc is
later added). My Day's four sections read from REQ-SB-07/08/09's capture
pipelines and REQ-SB-11's observability data; which agent types exist beyond
Worker/Producer/Expert, and each My Day drill-down page's exact content, are
open questions for /spec time. Note: MEMORY.md separately records Hermes's
own internal agent-type taxonomy (Expert/Worker/Hub) as context only — this
requirement's Worker/Producer/Expert grouping is Second Brain's own UI
taxonomy and is not required to match Hermes's; reconcile at /spec time if
that turns out to matter. -->

**Acceptance:** Launching Second Brain lands the user on the Agents Map,
which shows the Knowledge Base and every configured agent, each visually
distinguished by its type; the burger menu opens/collapses site navigation to
the Agents Map, My Day, and Settings; My Day shows Emails, Calendar, To-Do,
and Important Reads as separate clickable sections, each navigating to its
own page; Settings is reachable from the same navigation.

---

### REQ-SB-13: Embedded Agent Chat & Communication History

From the Agents Map, the user can select an agent to open a right-side panel
showing that agent's configuration/markup settings, available actions, an
embedded chat to converse with the agent directly inside Second Brain's own
UI (not only through an external Hermes channel, per REQ-SB-03), and a log of
that agent's past communications.

<!-- New scope, not ported from agentic-map; goes beyond REQ-SB-03's
external-channel-only conversational access, so — like REQ-SB-04's write
access carve-out — the trust surface (what the in-app chat can do/see, and
what "communication history" retains) is an open product question for
/spec time, not decided here. -->

**Acceptance:** Selecting an agent on the Agents Map opens a panel showing
that agent's settings and available actions, lets the user send it a message
and receive a reply without leaving Second Brain, and lists that agent's past
communications in chronological order.

---

### REQ-SB-14: Vault Graph Connectivity

Notes the user views in Obsidian's graph appear connected to what they're
actually related to, not as isolated dots. Every captured note that belongs
to a customer links to that customer's hub note (REQ-SB-10's pattern,
extended from People to Customers) via a real wikilink, not only a tag —
Obsidian's graph draws edges from `[[wikilinks]]`, and a shared tag alone
does not produce the same connected structure. This applies to
already-captured notes (a one-time retrofit) and to every note captured
from this point forward.

<!-- Root cause found 2026-08-10: existing notes carry `customer:`
frontmatter and a `customer/<slug>` tag (per ADR-004) but no wikilink to an
actual Customer note — because no Customer hub notes existed yet either.
Fixing this requires both: (a) a Customer hub note per customer with
content (REQ-SB-10's schema, extended to Customers per
Implementation/Plans/2026-08-10-vault-taxonomy-draft.md), and (b) a
wikilink from every customer-tagged note to its hub note. -->

**Acceptance:** Opening Obsidian's graph view shows customer-related notes
connected to their customer's hub note; every existing customer-tagged note
gets this link retroactively; every newly captured note gets it
automatically, with no separate manual step required.

---

### REQ-SB-15: Manual-Entry Templates & Guidelines

The user can create Pipeline, Agreement, Consumption-Snapshot, and Customer
notes by hand directly in Obsidian — most of this data does not arrive via
email and must be entered manually — using a template for each note type
that pre-fills the schema (frontmatter fields, the customer wikilink) so
manual entries are structurally consistent with automated ones. A guide
living inside the vault itself (not only in the project repo) explains what
each note type is for and how to use its template, since the user works
primarily in Obsidian, not in this codebase.

<!-- Schema for all four note types already resolved:
Implementation/Plans/2026-08-10-vault-taxonomy-draft.md. Uses Obsidian's
core Templates plugin (not a community plugin) per the durable-over-clever
principle already applied elsewhere in this project (ADR-002). -->

**Acceptance:** A template exists in the vault for each of Customer,
Opportunity, Agreement, and Consumption-Snapshot, matching the resolved
schema field-for-field; inserting a template via Obsidian's own Templates
feature produces a note structurally identical in shape to one the
automated capture pipeline would produce; a guide note in the vault
explains what each type is for and when to use it.

---

### REQ-SB-16: Partner Hub Notes & Graph Connectivity

Companies that are technology/business partners rather than customer
accounts (e.g. Microsoft) get their own hub note and tag namespace,
distinct from Customer — a partner relationship isn't a sales/consumption
relationship, and conflating the two tag namespaces would misrepresent
which is which. Person notes for a partner's employees link to the
partner's hub note the same way they already link to a Customer's, via
`REQ-SB-14`'s existing graph-connectivity mechanism. Companies already
misclassified as a Customer (found live: Microsoft) get migrated, not left
stranded under the wrong tag.

<!-- Scope resolved 2026-08-11 — see
Implementation/Plans/2026-08-10-vault-taxonomy-draft.md's "Partners"
section. Deliberately does NOT replicate Pipeline/Agreements/Consumption
for Partner (operator's explicit scoping — those track a sales/consumption
relationship a partner doesn't have). `partner/<slug>` and `customer/<slug>`
are mutually exclusive (operator's explicit choice) — a company is one or
the other, never both. Real migration data already exists:
`Work/Customers/Microsoft.md` plus 5 Person notes and 2 Email notes already
tagged `customer/microsoft`. -->

**Acceptance:** A Partner hub note exists at `Work/Partners/<Partner>.md`
per known partner, structurally matching the Customer hub note's living-
document pattern; a Person note whose derived company matches a known
partner links to that partner's hub note automatically, the same way it
already does for a matching Customer; a company already tagged as a
Customer that is really a Partner (Microsoft) is migrated to the Partner
tag/hub, with existing wikilinks continuing to resolve.

---

### REQ-SB-17: Research Notes (Books & Reads)

The user can create a Research note by hand for a book summary or an
article/read they want to memorize, using a template that pre-fills the
minimal schema (title, author, tags) so entries are structurally
consistent — the actual summary/takeaways live in the note's free-form
body, not in frontmatter.

<!-- Scope resolved 2026-08-11 — see
Implementation/Plans/2026-08-10-vault-taxonomy-draft.md's "Researches"
section. Manual-entry only (operator's explicit choice) — no AI-assisted
capture pipeline in this requirement; deferred if wanted later. Uses
Obsidian's core Templates plugin, same mechanism as REQ-SB-15. -->

**Acceptance:** A Research template exists in the vault, matching the
resolved schema (`type: Research`, `title`, `author`, `tags: [kind/
research]`); inserting it via Obsidian's Templates feature produces a note
under `Work/Researches/` ready for the user to fill in with their own
summary/takeaways.

---

### REQ-SB-18: Dynamic Agent Sections & Agent-to-Section Assignment

The Agents Map's angular grouping (its "sections" — today Capture/People/
Q&A, one per agent type) becomes a user-editable concept, replacing the
current 1:1 section-equals-type structure: sections are named business-
domain groupings (starting with Technical, Sales, Productivity, Customers,
Products) that the user can create and edit from Settings, independent of
an agent's Worker/Producer/Expert type (which continues to drive the
agent's ring position — the two are now separate axes, not the same
thing). Every agent belongs to exactly one section; the user can move any
agent to a different section from the Agent Settings surface.

<!-- Scope resolved 2026-08-11, operator-directed (explicitly requested as
a formal requirement, not ad hoc work): Section and Type are independent
(an agent keeps its ring-determining Worker/Producer/Expert type and
separately has a Section); a section can contain agents of any type.
Starting section set: Technical, Sales, Productivity, Customers, Products
— editable/extensible via Settings (create/rename/delete a section), not a
fixed enum. Initial agent→section assignment (Email/Meeting/To-Do Capture
→ Productivity, People Notes → Customers, Vault Q&A → Technical) is a
starting default the user picked, immediately rearrangeable — not load-
bearing product meaning. Real architectural consequence, not decided here:
agents and sections currently live in a static hardcoded Python dict
(`app/business/agent_registry.py`, ADR-011) — reasoned at the time as
"app/deployment configuration, not vault content, not something a future
process could organically add to." User-driven CRUD via a Settings UI is a
different kind of mutability than that reasoning was written against
(explicit user action, not automatic growth) — /plan-tasks must decide the
new persistence mechanism (e.g. a mutable `.second-brain/` state file,
extending that existing convention, vs. some other store), left open here
per this project's own architecture-decisions-belong-to-/plan-tasks
discipline. -->

**Acceptance:** Settings has a Sections area where the user can create,
rename, and delete a section; the Agent Settings surface (REQ-SB-13's
detail panel, or a dedicated Settings agent list) lets the user reassign
any agent to a different existing section; the Agents Map reflects the
current section set and agent-to-section assignments, including sections
with zero agents and agents whose section was just changed, without a
code change or restart.

---

### REQ-SB-19: Per-Agent LLM Provider Selection

The user can configure one or more LLM Providers in Global Settings (each
with at minimum a name, endpoint, credential, and model — Compass is
pre-seeded as the default provider using its existing configuration) and,
per agent, choose which configured Provider that agent uses. Compass
remains the default for every agent unless the user explicitly picks a
different one.

<!-- Scope resolved 2026-08-11, operator-directed. This pass adds the
Provider *concept* — Global Settings CRUD for providers, a per-agent
provider picker, Compass functional as today's only real client. Selecting
a non-Compass provider is honestly unavailable until a real client exists
for it — same "declared but not yet backed by a real handler" pattern
`ADR-011` already established for agent actions, deliberately not building
new provider clients (e.g. OpenAI/Anthropic) in this pass. Exact Provider
field schema and where provider selection is persisted (a `.second-brain/`
state file, `Settings`/`.env`-adjacent config, or another mechanism) are
architecture-level decisions left to `/plan-tasks`, not decided here. -->

**Acceptance:** Global Settings has a Providers area where the user can
add, edit, and remove a Provider entry, with Compass present by default;
the Agent Settings surface lets the user pick a Provider for each agent
individually, defaulting to Compass; an agent using Compass continues to
work exactly as today; an agent whose selected Provider has no real client
built yet honestly reports it's not available rather than silently falling
back to Compass or fabricating a response.

---

### REQ-SB-20: Section Hub Intelligence & Cross-Section Routing

Each Section's Hub (REQ-SB-18) acts as a manager for its section: it
understands which of its agents is knowledgeable about what, using a set
of keywords assigned per agent alongside its Section. When an agent needs
help with something outside its own knowledge, the request is routed
through Hubs, not directly agent-to-agent — and this routing is
particularly load-bearing across Sections: an agent in one Section needing
another Section's agent must have that request go through both Sections'
Hubs (its own Hub, then the target Section's Hub), never a direct
agent-to-agent call across Sections.

<!-- Scope resolved 2026-08-11, operator-directed, dictated verbatim
across two messages and combined here as one requirement since Hub
intelligence and cross-section routing are the same mechanism (a Hub that
doesn't know which agent handles what can't route to another Hub either).
Genuinely open, not decided here: the exact keyword-assignment mechanism
(free text per agent? a fixed vocabulary? who assigns them — the user, or
inferred?), what "the Hub understands" and "talk to each other to route
the request" actually means mechanically (a real LLM-backed routing
decision? a keyword-match lookup table, same shape as REQ-SB-19's chat
action-triggering? something else?), and whether within-Section routing
(an agent asking its own Hub for help with another agent in the *same*
Section) is in scope here or a separate concern from cross-Section
routing. All left to `/spec`/`/plan-tasks`, not guessed here. Depends on
REQ-SB-18 (Sections must exist as a real concept before Hubs can manage
them) and, for any LLM-backed routing decision, likely REQ-SB-19
(Provider selection) too. -->

**Acceptance:** Each agent has one or more keywords assigned alongside its
Section; when an agent needs help outside its own knowledge, the request
is routed via Hub(s) rather than directly to another agent; a request
that needs an agent in a different Section is never sent directly
agent-to-agent across Sections — it goes through the requesting agent's
own Hub and the target Section's Hub.

---

### REQ-SB-21: Agent Working Modes

Every agent has one of three working modes, chosen by the user: **Autonomous**
(acts independently, no approval needed), **Supervised** (proposes an
action and waits for the user's approval before taking it — human in the
loop), and **Manual** (stays dormant and only acts when the user explicitly
asks it to do something).

<!-- Scope resolved 2026-08-11, operator-directed — mode names proposed by
Claude ("Autonomous"/"Supervised"/"Manual", mapping directly to the
operator's own "Fully Autonomous"/"Need Approval before Taking an action
(Human in the loop)"/"Doesn't work till I ask it to do a task") and not
objected to. Genuinely open, not decided here: where working mode is set
(per-agent on the Agent Settings surface is the obvious fit, alongside
REQ-SB-18's Section picker and REQ-SB-19's Provider picker, but not
confirmed), what "propose an action and wait for approval" looks like
concretely for a background capture pipeline (REQ-SB-07/08/09) versus a
chat-triggered action (REQ-SB-13) — these may need different UI treatment
— and the default mode for existing and newly-added agents. Left to
`/spec`, not guessed here. -->

**Acceptance:** Every agent has an assigned working mode (Autonomous,
Supervised, or Manual), visible and changeable by the user; an Autonomous
agent takes its actions without asking; a Supervised agent proposes an
action and waits for explicit user approval before taking it; a Manual
agent takes no action of its own until the user explicitly requests one.

---

### REQ-SB-22: My Day Rolling 7-Day Window

My Day's Emails, Calendar, and To-Do views (REQ-SB-12) show a 7-day rolling
window — 3 days in the past, today, and 3 days in the future — instead of
only "today," so the user can see what just happened and what's coming up
without leaving the dashboard.

<!-- Scope resolved 2026-08-11, operator-directed. Genuinely open, not
decided here: exact per-section presentation (a single combined list
spanning all 7 days? grouped by day? a day-by-day navigator?) and how
"today" is anchored (the app's local clock, presumably) — left to `/spec`.
Extends the already-`Done` REQ-SB-12-US-02 (My Day dashboard); likely a
follow-on story against REQ-SB-12, not a rebuild. -->

**Acceptance:** My Day's Emails, Calendar, and To-Do drill-downs show
items spanning 3 days before today through 3 days after today, not only
today; the window advances automatically as days pass, with no manual
step required.

---

### REQ-SB-23: My Day Intake Agent (Conversational)

A dedicated agent, reachable from My Day as a real chat window, lets the
user hand it free-form information throughout the day — a quick note, a
thought, a fact to remember. The agent can ask follow-up/clarifying
questions before filing, refines the user's raw text into a properly
written note, accepts organizational hints from the user (e.g. "this was
yesterday") to place the information correctly, and then files it into the
right place in the vault based on understanding what it's about — the same
way Email Capture classifies an email by customer, but for arbitrary,
conversational user-provided input rather than one fixed source.

<!-- Revised 2026-08-11, operator-directed — supersedes this requirement's
original one-shot/autonomous framing (2026-08-11 original acceptance:
"send free-form text... files it... classified by what it's about").
`REQ-SB-23-US-01` (already drafted, `/design` already run producing a
one-shot Quick Capture card in `html-prototype/my-day.html`) needs
re-speccing and its prototype revising to match: a real chat thread (not a
single input+submit), the agent's own follow-up questions, mid-conversation
refinement of the note text, and explicit handling of user-supplied
temporal/organizational hints that affect where/how the note is filed.
Depends on REQ-SB-26 (real conversational agent chat — this agent needs
genuine multi-turn understanding, not keyword matching) for its
conversational mechanism. Genuinely open, not decided here: which note
types/kinds it can file into (already-resolved schemas only, or can it
propose a new kind?), and how working mode (REQ-SB-21) interacts with a
conversational flow that already involves back-and-forth by design. Left to
`/spec`. -->

**Acceptance:** The user can converse with the My Day Agent in a real chat
thread; the agent may ask follow-up questions before filing; the user can
refine the note's content and supply organizational hints (e.g. a different
date) mid-conversation; the agent files the resulting note into the vault
consistent with the existing schema conventions (tags and wikilinks, per
the standing design rule), classified by what it's about.

---

### REQ-SB-24: Per-Agent Token Consumption & Cost Tracking

Each configured LLM Provider (REQ-SB-19) has pricing information (cost per
token), and the app tracks how many tokens each agent consumes. The UI
shows, per agent, how much it has cost based on its actual token
consumption and its selected Provider's pricing.

<!-- Scope resolved 2026-08-11, operator-directed. Extends REQ-SB-19's
Provider schema with pricing fields (likely input/output token cost,
mirroring how most LLM providers price asymmetrically) — genuinely open,
not decided here: exact pricing field shape, where consumption is tracked
(per-call, aggregated per agent, over what time window — all-time?
rolling?), and where the cost is surfaced (Agent Settings surface,
alongside REQ-SB-11's observability work, or both). Left to `/spec`, not
guessed here. Depends on REQ-SB-19 (Provider concept must exist first). -->

**Acceptance:** Each configured Provider has a cost-per-token field (or
equivalent); the app records token consumption per agent as it performs
LLM-backed work; the UI shows each agent's accumulated cost, computed from
its actual consumption and its selected Provider's pricing.

---

### REQ-SB-25: Real Conversational Agent Chat

Agent chat (REQ-SB-13) becomes genuinely conversational — backed by a real
LLM call via the agent's selected Provider (REQ-SB-19), not the
keyword-substring matching this project built for action-triggering. An
agent can hold an actual back-and-forth conversation, not just recognize a
fixed set of trigger phrases.

<!-- Scope resolved 2026-08-11, operator-directed — this is a deliberate
reversal of two Accepted architecture decisions, not a silent extension:
`ADR-011` chose keyword-substring matching specifically because it judged
real NLU disproportionate to a one-real-action universe, and `ADR-007`
scoped all agent-orchestration/NLU capability out of Second Brain's own
stack, onto Hermes's side of the integration boundary. The operator has
now explicitly asked for real conversational chat — this requirement is
the trigger `ADR-007`'s own Consequences section anticipated ("If a future
requirement genuinely needs Second Brain itself to coordinate multi-step
... work... that is new scope requiring its own requirement and a
superseding ADR"). A superseding ADR is expected at `/plan-tasks`, not
avoided. Genuinely open, not decided here: whether keyword-match
action-triggering (`ADR-011`) is replaced entirely or kept as a fast-path
alongside real chat for the one already-real action; how this interacts
with REQ-SB-20's Hub routing (also currently keyword-match-based) and
REQ-SB-23's conversational intake agent, which depends on this
requirement's mechanism. Left to `/spec`/`/plan-tasks`. -->

**Acceptance:** Sending an agent a chat message that isn't a recognized
trigger phrase still produces a real, relevant conversational reply (via
the agent's selected Provider), not a generic fallback; an agent can
sustain a multi-turn exchange, not just one-shot request/reply.

---

### REQ-SB-26: Agent Memory

Agents retain memory across interactions — not just the flat chronological
communication-history log already built (REQ-SB-13), but working context
an agent can actually draw on in a later conversation (e.g. recalling
something the user told it earlier).

<!-- Scope resolved 2026-08-11, operator-directed. Genuinely open, not
decided here: memory scope (per-conversation/session vs. persistent across
all time), what gets remembered (raw message history fed back as context,
vs. a summarized/extracted memory store), storage mechanism (extends the
existing `.second-brain/agent_communication_history.json` convention, or a
new mechanism), and whether memory is shared across an agent's Section
(ties to REQ-SB-20) or strictly per-agent. Left to `/spec`. Depends on
REQ-SB-25 (real conversational chat) — memory has no purpose without a real
conversation to inform. -->

**Acceptance:** An agent's reply in a later conversation can correctly
reference or use information the user provided in an earlier conversation
with that same agent, without the user having to repeat it.

---

### REQ-SB-27: Skills Repository

A repository of skills exists that agents can draw on to perform
specialized tasks beyond their core built-in function — for example, an
agent that understands architecture/engineering diagrams can be given a
photo and identify the components in it.

<!-- Scope resolved 2026-08-11, operator-directed. Genuinely open, not
decided here: what a "skill" actually is architecturally (a callable
capability registered somewhere, in the spirit of REQ-SB-19's Provider
registry and the existing agent_registry.py pattern?), how an agent gets
access to a skill (assigned like keywords/Section, or available to all
agents?), the first skill(s) to actually build (the operator's own example
— image/diagram understanding — implies multimodal input, a real technical
capability this project has not built any precedent for), and how this
relates to REQ-SB-28 (file upload) as the likely input mechanism for
skills like summarization. Left to `/spec`/`/plan-tasks` — this is
architecturally the least-precedented requirement captured this session and
will need real design work, not a quick extension of an existing pattern. -->

**Acceptance:** A skill can be registered in the repository; an agent with
access to a skill can invoke it to perform the specialized task the skill
provides (e.g. given an uploaded image, identify and describe its
components) and use the result in its response or filing decision.

---

### REQ-SB-28: File Upload for Agents

The user can upload a file to an agent; the agent summarizes it via
Compass and hands the summary to the Vault Filing Expert (REQ-SB-35),
which decides where it belongs and files it with the right tags — the
same mechanism regardless of which agent received the upload.

<!-- Scope resolved 2026-08-11, operator-directed; mechanism resolved
2026-08-13, operator-directed, verbatim: "The Files we got from the
Attachments we need to pass them to Compass to Generate a Summary and
we Store the Summary in the Vault and tags so I can Link and use them
later" — then confirmed, when asked whether this is the same mechanism
as a dedicated file-intake agent handing off to the Vault Filing Expert:
"Same thing." This resolves the original open question ("how does
'summarize and file' map onto a skill invocation vs. a bespoke
capability") concretely: (1) summarization is a Compass-backed
capability (not Anthropic — distinct from REQ-SB-36-US-01's web-research
skill, which specifically needed Anthropic's own tool; a plain Compass
completion is sufficient for summarization) invoked the same way any
other agent capability is (see REQ-SB-39 — this becomes a Skill, not a
bespoke one-off, once that unification lands); (2) the summary is never
filed directly by the receiving agent — it always routes through the
Vault Filing Expert (REQ-SB-35, already Done), the same placement/
tagging authority REQ-SB-36's own delegated-research chain already uses,
so upload-derived content and research-derived content are filed
consistently. Still genuinely open, not decided here: which agents
accept uploads (any agent via its chat, or a dedicated intake surface),
accepted file types/size limits, and whether uploaded originals are
retained in the vault alongside their summary or discarded after
processing. Left to `/spec`. Depends on REQ-SB-25 (real chat, Done),
REQ-SB-35 (Vault Filing Expert, Done), and REQ-SB-39 (Unify Agent
Capabilities Under Skills — summarization should be built as a Skill
from the start, not a bespoke capability this story would otherwise
invent). -->

**Acceptance:** The user can attach a file to a chat message sent to an
agent; the agent summarizes the file's contents via Compass; the summary
is handed to the Vault Filing Expert, which files it into the vault with
appropriate tags, matching existing schema conventions, so the user can
link to and find it later.

---

### REQ-SB-29: Agent-to-Tag/Folder Scoping

An agent can be linked to a specific vault tag (e.g. `customer/masdar`) or
folder, giving it bounded, relevant query access to that slice of the
vault — for example, an agent assigned to a customer tag can retrieve that
customer's Pipeline/Agreements/Consumption notes on request, without
searching the whole vault.

<!-- Scope resolved 2026-08-11, operator-directed. Directly activates the
Customer/Pipeline/Agreements/Consumption schema resolved 2026-08-10
(`MEMORY.md`) that has had "structure only — no ingestion/agent code" ever
since. Genuinely open, not decided here: how an agent's tag/folder scope is
assigned (a new field on the Agent Settings surface, alongside Section/
Provider/Keywords/Working-mode?), whether an agent can have multiple
scopes or exactly one, how this interacts with REQ-SB-01/02 (Vault
Indexing & Browse/Search, neither built yet) as the underlying query
mechanism, and how it relates to REQ-SB-20's keyword-based routing (a
different, complementary dimension — keywords describe *what an agent
knows*, tag/folder scope describes *what an agent can reach*). Left to
`/spec`. -->

**Acceptance:** An agent can be assigned one or more vault tags/folders as
its scope; when asked, the agent can retrieve and use notes matching its
assigned scope (e.g. "get me the pipeline for Acme Corp" returns that
customer's actual Pipeline notes) rather than requiring the user to
locate them manually.

---

### REQ-SB-30: Email Importance Filtering via Compass Reasoning

My Day's Emails list shows only the important captured email, not every
email that was filed — determined by a real Compass (LLM) judgment call,
not a keyword/sender heuristic.

<!-- Scope resolved 2026-08-12, operator-directed ("Don't show me All
Emails Show me Important Email in the list use some Compass Reasoning").
Genuinely open, not decided here: (1) the exact importance signal Compass
should reason over (sender/customer relationship, urgency language,
whether it's a direct ask vs. an FYI/notification, thread position —
or some combination); (2) whether importance is binary (show/hide) or a
score/tier the UI could also surface, not just filter on; (3) WHEN the
judgment happens — at capture time (one Compass call per new email,
mirroring how customer classification already works, cheap going
forward) vs. on-demand per My Day view (would mean re-reasoning about the
same 22-in-window emails on every page load — slower, costlier, and
inconsistent between loads unless cached); (4) the retrofit question for
the 181 already-captured real emails, most already outside today's 7-day
My Day window and therefore not urgent to backfill, but the ~22 currently
inside the window have no importance signal yet either — backfill now,
or let the window naturally roll past them within a week. Left to
`/spec`. Depends on REQ-SB-07 (Scheduled Recurring Agent Capture, Done —
the classification call this extends) and REQ-SB-22 (My Day Rolling
7-Day Window, Done — the list this filters).

**Needs re-spec, not yet done (flagged 2026-08-16):** written against the
old flat, one-note-per-email capture model. `REQ-SB-54`/`REQ-SB-55`
replace that with Threads (one note per conversation, updated in place),
and `REQ-SB-59` wipes `Work/Emails/` entirely — "My Day's Emails list"
and "the 181 already-captured real emails" no longer describe the real
shape once that ships. Do not `/spec` this requirement as originally
written; re-derive it against the Thread model first. -->

**Acceptance:** My Day's Emails list shows only email Compass judges
important, not the full captured set; the judgment is a real reasoning
call (not a keyword/sender allowlist), and the user is not shown a
misleadingly-empty "Nothing captured yet" state when unimportant email
was in fact captured and simply filtered out.

---

### REQ-SB-31: System Health View

A visible surface showing the operational status of Second Brain's own
moving pieces — whether the backend is reachable, whether the in-app MCP
server and LangGraph agent path are actually working (not just that the
process is running), whether each configured Provider is reachable,
whether the scheduler's last capture run succeeded — so a real failure is
visible at a glance instead of discovered by symptom-chasing through
individual features.

<!-- Scope resolved 2026-08-12, operator-directed ("we need to have a
System Health view as we keep on adding Pieces everywhere"), prompted
directly by a real debugging session the same day: a critical, silent
chat failure (an orphaned backend worker process serving stale code,
then a hardcoded stale MCP port, then a nested-event-loop self-connection
bug) took extensive live investigation to even notice, let alone
diagnose — nothing in the app itself surfaced that anything was wrong.
Genuinely open, not decided here: (1) the exact set of checks (backend
reachability is implicit if the page loads at all; candidates include
the MCP server mount, a real Provider round-trip vs. just "has
credentials configured", the scheduler's last-run outcome already
tracked in `.second-brain/last_capture_run.json`, per-agent Provider
availability already exposed via `provider_available` on `GET /agents`);
(2) active probing (the page/an endpoint makes real calls to verify each
piece, costing time/API calls) vs. passive reporting (surfaces the most
recent real outcome already recorded from ordinary use, e.g. the last
chat call's own success/failure, added at zero extra cost but only as
fresh as the last real usage); (3) placement (a new nav item/page vs. a
Settings section vs. a small persistent status indicator in the app
shell); (4) whether this also captures unhandled backend exceptions
going forward (today's `ERROR: Exception in ASGI application` tracebacks
are only visible in the raw server log, never surfaced to the app
itself) or is scoped to synchronous health checks only this pass. Left
to `/spec`. -->

**Acceptance:** The user can see, without digging through server logs or
guessing from a feature silently failing, whether Second Brain's backend,
MCP/agent-orchestration path, configured Providers, and last scheduled
capture run are each genuinely working — not just "the process is up."

---

### REQ-SB-32: Rich Text Rendering in Agent Chat

Agent chat replies render as formatted rich text (bold, bullet/numbered
lists, headings, etc.) instead of literal plain text — today, an agent's
markdown-formatted reply (e.g. a bulleted answer) shows its raw `**`/`-`
syntax verbatim, since `.chat-message` is a plain `white-space: pre-wrap`
text block.

<!-- Raised 2026-08-12, operator-directed ("I need the text to be Rich
text instead of plain Text") — explicitly logged as a discussion topic,
not scoped or built this pass ("mark it as a discussion to avoid going
back to this everytime"). Genuinely open, not decided here: which
markdown subset to support (a full CommonMark render vs. just
bold/italic/lists, the common case for a chat reply), which rendering
approach (a markdown-to-React library vs. a small hand-rolled parser,
matching this project's own general preference for minimal dependencies
where reasonable), and whether user-sent messages also render as rich
text or only agent replies (an agent reply is LLM-authored markdown; a
user's own typed message is not usually written expecting markdown
interpretation). Left to `/spec`, whenever picked up. -->

**Acceptance:** An agent's chat reply containing markdown formatting
(bold, lists, etc.) renders as actual formatted rich text in the chat
thread, not literal markdown syntax characters.

---

### REQ-SB-33: Agent Grounding & Honest-Uncertainty Guardrail

Every agent's real conversational replies (REQ-SB-25) are grounded in
what it actually retrieved via its own tools — never the model's general
training knowledge presented as a vault fact — and an agent honestly
says it doesn't know, rather than guessing or fabricating, whenever its
tools don't return an answer or the question falls outside its assigned
scope (REQ-SB-29).

<!-- Raised 2026-08-12, operator-directed, alongside REQ-SB-29 (Vault
Scope) and REQ-SB-31 (System Health View) as three related facets of
"making an agent trustworthy, not just responsive" — operator's own
framing: "avoid Hallucination as much as possible... if they don't know
I can Get Don't know as an Answer... part of Agents Declaration should
be the scope, Rail Guides." Distinct from REQ-SB-29's own existing
Scenario 4/5 honesty behavior (which covers "the question is outside my
assigned scope") — this requirement covers the harder, separate case:
the question is legitimately within scope, but the agent's own tool
calls didn't actually surface a real answer, and the model must not
paper over that gap with a plausible-sounding guess. Genuinely open, not
decided here: (1) the exact mechanism — a stronger system-prompt
instruction alone (cheap, no guarantee) vs. a verification/citation step
that checks the reply is actually traceable to a real tool result before
returning it (stronger guarantee, real added latency/complexity); (2)
whether this is a global instruction for every agent or configurable
per-agent (some agents may reasonably want to answer general questions
too, not just vault-grounded ones); (3) how this is exposed as part of
"Agent Declaration" alongside Section/Keywords/Working-mode/Provider/
Scope on the Agent Settings surface — a visible toggle/setting, or an
always-on baseline behavior with nothing to configure. Left to `/spec`.
Depends on REQ-SB-25 (Real Conversational Agent Chat, Done — the reply
path this guards) and relates to REQ-SB-29 (Vault Scope, the sibling
"what can this agent reach" boundary) and REQ-SB-31 (System Health View,
where whether this guardrail is active for a given agent is expected to
surface as part of that agent's own health/readiness signal). -->

**Acceptance:** An agent's conversational reply never states a vault
fact that didn't come from a real tool result; when its tools return no
relevant answer (in-scope or not), the agent says so honestly instead of
producing a plausible-sounding guess.

---

### REQ-SB-34: Tech Knowledge Area — WITHDRAWN, merged into REQ-SB-35

<!-- Withdrawn 2026-08-12, operator-directed, one exchange after this
requirement was first drafted: "The Tech Folder is just an Example the
Vault Expert should follow the Guidelines we had in the book in
deciding where to store stuff — may be it's just a research or a new
Category we don't know of yet." The operator's original worked example
("we will need to have a Tech Folder with sub Folders") was illustrative
of the *kind* of decision the Vault Filing Expert must make, not a
prescribed destination to build. Prescribing a new top-level "Tech" area
here would have hardcoded exactly the enum this project's own already-
established pattern warns against (`Implementation/Learnings.md` →
"Design for the extensibility point, not the enum" — `kind`/`customer`
are vault-derived and model-proposed, never a hardcoded list). This
requirement's real intent — a technology subject's information needs
*somewhere* correct to live, whether that's an existing category
(Research, per REQ-SB-17) or a genuinely new one the vault doesn't have
yet — is now folded into REQ-SB-35's own acceptance criteria below,
where the decision actually belongs (it's the Vault Filing Expert's job
to decide, guided by the vault's own design methodology, not a fixed
folder this requirement would have predetermined). REQ-SB-34's ID is
retired, not reused, per this project's own append-only numbering
convention (mirroring how superseded ADRs keep their number). No story
was drafted against this requirement before withdrawal. -->

---

### REQ-SB-35: Vault Filing Expert

A dedicated agent capability that, given new content another agent has
produced (e.g. research output), determines where it belongs in the
vault and with what tags — consistent with the vault's existing design
methodology (`Documentation/References/beyond-the-second-brain-
methodology.md`) and taxonomy conventions (tags for multidimensional
attributes, folders for single-home entities, per `ADR-004`) — and then
writes it. The decision is not limited to already-existing categories:
when the content genuinely doesn't fit anywhere that already exists,
the Vault Filing Expert can propose and create a new category/folder,
following the same "read what's already there, let the model propose
new values" pattern this project already applies to `kind`/`customer`
(`Implementation/Learnings.md`) rather than being limited to a fixed
enum decided in advance. Other agents consult this capability before
filing new content rather than each agent inventing its own
placement/tagging logic.

<!-- Scope resolved 2026-08-12, operator-directed, arising from a worked
example ("Ask my Vault Expert to know where it should Store the info
then store it in the Knowledge Hub with the right tags"), then corrected
one exchange later, same date: "The Tech Folder is just an Example the
Vault Expert should follow the Guidelines we had in the book in
deciding where to store stuff — may be it's just a research or a new
Category we don't know of yet." This second quote is why REQ-SB-34
(originally a prescribed new "Tech" area) was withdrawn and folded in
here instead: the operator's own point is that *this* requirement — the
Vault Filing Expert's own placement judgment, grounded in the book's
methodology — is what decides whether something lands in an existing
category (e.g. Research, REQ-SB-17) or genuinely needs a new one,
never a folder this PRD predetermines. Distinct from REQ-SB-29
(Agent-to-Tag/Folder Scoping) — that requirement bounds what slice of
the vault an agent can *read*; this requirement is about correctly
deciding where *new* content should be *written*, a different concern
the operator named separately and by a different name ("Vault
Expert"). Genuinely open, not decided here: (1) whether this is a
distinct agent in the registry (a literal "Vault Expert" agent other
agents route a request to, via REQ-SB-20's Hub mechanism) or a shared
capability/skill (REQ-SB-27) any agent can invoke directly without a
routed request. **Resolved 2026-08-12, operator-directed ("This is an
Agent"):** the Vault Filing Expert is a distinct agent in the registry,
reached via REQ-SB-20's Hub routing like any other cross-Section
request — not a shared skill. (2) mechanically,
how it applies "the book's guidelines" to a live placement decision — a
system-prompt instruction summarizing the methodology's own principles
(atomic notes, output-orientation, tags-for-multidimensional-attributes,
extensibility-over-enumeration), a set of hardcoded rules mirroring
`ADR-004`, or an LLM reasoning call that inspects the vault's actual
current structure at decision time and reasons from the methodology
document directly — not decided here; (3) what counts as "genuinely
doesn't fit anywhere existing" versus a stretch-fit into something
already there, and what governance (if any) exists over new
top-level-area creation specifically, versus a new tag/subfolder within
an existing area (a materially smaller decision). **Resolved
2026-08-12, operator-directed:** a tag or subfolder within an existing
area proceeds autonomously, same as the rest of REQ-SB-36's chain; but
proposing a wholly new top-level vault area pauses for the operator's
explicit approval first — a scoped exception to REQ-SB-36's own "fully
autonomous end-to-end" resolution, reusing REQ-21's existing
Supervised-mode machinery for just this one action type rather than
inventing a new approval mechanism. (4) what happens when it's
genuinely unsure even after reasoning from the methodology — proposes a
best guess and proceeds, or defers. Left to `/spec` — expect this to be
one of the more genuinely undecided stories from this batch, not a
quick extension of an existing pattern. Depends on REQ-SB-20 (if built
as a routable agent) and relates to REQ-SB-33 (the same honesty
standard should apply to a placement decision, not just a conversational
answer). -->

**Acceptance:** Given new content to file, the Vault Filing Expert
determines a vault location and tags consistent with the vault's
existing design methodology and taxonomy conventions, and writes the
content there; when the content doesn't fit any existing category, the
Vault Filing Expert can identify and use a genuinely new one instead of
forcing a stretch-fit into something that already exists; other agents
that produce new content route it through this capability rather than
deciding placement themselves.

---

### REQ-SB-36: Agent Knowledge Bootstrapping via Delegated Research

A new agent that starts with no knowledge of its assigned subject can
build that knowledge by delegating: it asks its own Section's Hub for
help, which routes (via REQ-SB-20's cross-section mechanism) to find a
Research Expert; the Research Expert gathers information — from
documents the user supplies and from its own real web research — and
hands the result to the Vault Filing Expert (REQ-SB-35), which decides
correct tags/placement per the vault's own design methodology — an
existing category if one genuinely fits, a new one if it doesn't. The
whole chain runs end-to-end without
requiring approval at any step. Once a new agent has been bootstrapped
this way, more source material can be added later (e.g. a pricing
spreadsheet, an unreleased-feature document) via file upload
(REQ-SB-28), following the same Vault Filing Expert step.

<!-- Scope resolved 2026-08-12, operator-directed, as a single concrete
worked business example (verbatim): "I need to build a Compass Expert
who in the beginning will be empty in order to build data — it needs to
talk to the Tech Manager to talk to the Managers to find a Research
Expert. The Research Expert will go and do research for Compass basic
info that can make the agent an expert in Compass, then ask my Vault
Expert to know where it should store the info, then store it in the
Knowledge Hub with the right tags... more info will need to be added
from other systems — an Excel file for pricing, or new features that
are still not public yet." Clarified directly, same date: "Manager" is
the existing Hub (REQ-SB-18/20), not a new agent tier; the Research
Expert's research comes from both operator-supplied documents and real
web search, using the Anthropic Claude Provider specifically for the
research capability. **Correction, 2026-08-12:** this PRD originally
described the Anthropic Provider as "already configured" — false,
found live during `/spec`: `provider_registry.py`'s
`_REAL_CLIENT_PROVIDER_IDS` contains only `{"compass"}`, no `anthropic`/
`langchain-anthropic` dependency exists in `requirements.txt`, and no
credential exists in `.env.example` — the Provider entry other stories
referenced was a UI-only placeholder, never backed by a real client.
**Resolved, operator-directed ("Yes add Anthropic APIs Support"):**
building a real Anthropic Provider integration (new dependency, real
client, credential wiring, extending REQ-SB-19's already-`Done`
Provider registry with an actual working entry rather than a
placeholder) is in scope, specifically to give the Research Expert real
web-search capability — the natural mechanism is Anthropic's own
server-side web-search tool, reached once a real Anthropic client
exists, though the exact tool-use wiring is left to `/plan-tasks`. The
whole chain runs fully autonomously end-to-end except the one new-
top-level-vault-area exception noted in REQ-SB-35 above; the operator
reviews the rest of the resulting vault content after the fact, not
mid-chain (this implies every agent in the chain runs in Autonomous
working mode, REQ-SB-21, for this specific flow — a per-agent setting
already built, not new scope here). The Compass Expert itself is the
first concrete pilot of this pattern, not a one-off: the requirement is
the general capability (an empty Expert can bootstrap itself via
delegated research), Compass is simply the first real subject. Genuinely
open, not decided here: (1) the exact mechanism for the Research
Expert's real web search — a new Skill under REQ-SB-27's already-built
plumbing (the natural fit — REQ-SB-27's own Non-Goals deferred "the
first real skill"; this is a strong candidate to be it) is the most
likely shape but not confirmed; (2) how a brand-new, empty Expert agent
actually gets created and assigned (a manual Agent Settings action the
operator already has via REQ-SB-18/19/20/21/29, or does bootstrapping
itself imply some new agent-creation flow?); (3) what "the agent is now
an expert in Compass" concretely means once built — is there a
completion signal, or does the agent simply now have vault content
under its scope (REQ-SB-29) to draw on. Left to `/spec`. Depends on
REQ-SB-20 (Hub routing, Draft — the delegation mechanism), REQ-SB-27
(Skills Repository, Done/plumbing-only — the likely home for the new
web-research skill), REQ-SB-35 (Vault Filing Expert, new — decides
where this pilot's output lands, per its own withdrawn-REQ-SB-34 note),
REQ-SB-28 (File Upload, Draft — the later Excel/unreleased-feature ingestion
path), REQ-SB-29 (Vault Scope — what the finished Expert can draw on),
and REQ-SB-21 (Working Modes, Done — Autonomous mode is what makes
"runs end-to-end without approval" possible). This is the largest,
most cross-cutting requirement captured this session — expect `/spec`
to consider splitting it into more than one story (e.g. the delegation/
routing mechanism vs. the Research Expert's web-search skill vs. the
Vault Filing Expert vs. the Compass Expert as a concrete pilot
instance) rather than one monolithic story. -->

**Acceptance:** A newly created, empty Expert agent can, without manual
intervention, have its own Section's Hub route a help request across
Sections to find a Research Expert; the Research Expert produces real
information about the Expert's assigned subject (from supplied
documents and/or real web research); the result is filed into the vault
by the Vault Filing Expert with correct tags/placement; the entire
sequence completes without pausing for approval; the resulting vault
content is available for the newly-expert agent to draw on afterward.

---

### REQ-SB-37: Agent Creation Wizard

The user can create a new agent from the app itself, via a wizard whose
steps change based on the agent's Type: a **Worker** is configured with
Skills (its tools), a Vault Scope, and a Section; an **Expert** is
configured with a knowledge domain and starts genuinely empty — honestly
answering "I don't know" until real content exists in its scope (see
REQ-SB-40 for how that gap closes over time); a **Producer** is
configured with a Purpose and an output action (what it does with what
it produces). No place in the UI currently lets the user do this — every
agent that exists today was added by editing
`app/business/agent_registry.py`'s source code directly.

<!-- Raised 2026-08-13, operator-directed, verbatim: "Add the Creation
of Agents As we have no place to create an agent." This is a direct
reversal of a standing architectural decision, not a new extension of
one — `ADR-011` point 2 established "agent identity/type/actions stay
hardcoded... not a persisted/mutable concern," and every subsequent ADR
that touched agents this session (`ADR-014`, `ADR-017`, `ADR-018`,
`ADR-020`, `ADR-021`, `ADR-023`) built on that same assumption without
reopening it. A superseding ADR is expected at `/plan-tasks`, mirroring
how `REQ-SB-25` previously reversed `ADR-007`/`ADR-011`'s own
keyword-matching choice.

**Per-type wizard shape, operator-directed 2026-08-13, verbatim:**
"1. Workers Need tools Mainly a Scope of work and Section they add data
to. 2. Experts they are domain Expert to need to Understand What they
have and what they missing to be called Expert. 3. Producers Need to
have a Purpose and then do something with [it]." Clarified further in
the same exchange: Worker "tools" = Skills, not custom hardcoded
actions — "We have no Custom Action, we need to Convert those Custom
Actions to Skills. Example, Read Mail is a Skill under Outlook COM Tool
we need to have that in our tool set." **This resolves this
requirement's own original biggest open question (custom actions) by
reframing it entirely — see REQ-SB-39, a new, larger requirement this
answer forced into existence**: every existing hardcoded action
(`run_capture_now`, `rebuild_person_note`, `ask_question`, etc.)
becomes a Skill, and REQ-SB-37's own wizard grants Skills the same way
to a newly-created agent that REQ-SB-27's existing grant/revoke
mechanism already does for any other agent — no separate "define a
custom action" UI is needed once REQ-SB-39 lands, because there is no
longer a second, harder-coded capability mechanism to design a UI for.

On Expert readiness ("what they have and what they're missing to be
called Expert"), operator-directed: "I guess we need both the wizard,
and the Agent can say I don't know as a start, and a human input is
needed to fill the gap — by time it will be Expert (the number of I
don't know is how we close this Expert gap in future)." This is
REQ-SB-33's already-shipped honest-uncertainty behavior, now given a
purpose beyond just answering honestly in the moment: a new,
significant requirement (**REQ-SB-40**) to actually track and close
those gaps over time. REQ-SB-37's own wizard for an Expert is therefore
thin by design — define the domain/scope, done — the "becoming an
Expert" part is REQ-SB-40's own job, not this wizard's.

Genuinely still open, not decided here: (1) where creation lives in the
UI (a new "Create Agent" affordance on the Agents Map, on Settings, or
both); (2) the exact Producer "output action" shape — is this also a
Skill (write to a Section, mirroring the already-shipped
Worker/capture-pipeline pattern), or something else; (3) whether
creation is itself gated by anything (e.g. does creating a new
top-level vault area an agent's own scope points at need the same
Tier-2-style approval `REQ-SB-35` already established for a different
actor). Left to `/spec`. Depends on `REQ-SB-18-US-01`/`REQ-SB-19-US-01`/
`REQ-SB-20-US-01`/`REQ-SB-21-US-01` (all `Done`), **REQ-SB-39** (Unify
Agent Capabilities Under Skills — a hard prerequisite: the wizard's own
Worker/Producer flows are Skills-based by the operator's own direction,
so this story cannot be fully built until that unification lands), and
relates to `REQ-SB-29` (Vault Scope, still `Draft`) and `REQ-SB-40`
(Expert readiness, new — the "becoming an Expert" half of this
requirement's own Expert-type flow). -->

**Acceptance:** The user can create a new agent from within the app,
without editing source code, via a wizard whose fields depend on the
chosen Type (Worker: Skills + Vault Scope + Section; Expert: a defined
knowledge domain, starting empty and honestly uncertain; Producer: a
Purpose + an output action); the new agent is immediately visible
alongside existing agents; its already-existing per-agent properties
(Section, Provider, Skills, Working mode, Vault Scope) can be configured
the same way an existing agent's can.

---

### REQ-SB-38: Agents Map Density Clustering

As the number of agents within a Section grows, the Agents Map overview
groups agents that would otherwise crowd/overlap into a single cluster
marker — a circle showing a count and a "+" — instead of rendering every
individual agent node at a fixed position regardless of how many share
the same Section. Clicking a cluster marker shows the agents inside it.

<!-- Raised 2026-08-13, operator-directed, verbatim: "This is a problem
and will always appear as the number of Agents grow, we will have them
on top of each other... We need to be able to cluster some agents
together to limit the overlapping in future — a circle with a number
and '+' so we can click on it to view the agents inside." Prompted
directly by `BUG-009`'s own fix the same day: `layoutAgents.ts`'s fan-out
angle was corrected to stay within a Section's own wedge boundary, but
that fix only prevents cross-Section spillover — it does not prevent
same-Section crowding as agent count grows (more agents fanned across
the same, now correctly-bounded, arc simply render closer together,
eventually overlapping node-to-node). This requirement is the necessary
next layer: a real density/scale problem, not a boundary bug, and
distinct from `layoutSectionDrilldown`'s own full-360° drill-down
spread (which has more angular budget per agent than the overview's
per-Section wedge, but is not immune to the same problem at high enough
counts either). Genuinely open, not decided here: (1) the exact
threshold that triggers clustering — a fixed max-agents-per-wedge count,
or a computed check against actual rendered node size vs. available arc
length (more robust as node size/spacing constants change, but more
work); (2) whether clustering applies only to the overview's per-Section
wedges, or also to `layoutSectionDrilldown`'s own full-circle spread
once a single Section's own agent count grows large; (3) what "clicking
a cluster shows the agents inside" means mechanically — a further
semantic-zoom drill-down (the same click-to-zoom mechanic `BUG-002`'s
Option D fix already established for Section Hubs, applied one level
deeper) is the obvious, precedented fit, but not confirmed; (4) how
clustering interacts with an agent's own Type (Worker/Producer/Expert
ring) — does a cluster ever mix agents of different Types, or is
clustering always scoped within one ring; (5) whether a cluster's own
count needs to update live as agents are added/removed (relates to
`REQ-SB-37`, Agent Creation — a newly-created agent could itself push a
Section over its clustering threshold). Left to `/spec`. Likely needs a
`/design` pass first, mirroring `BUG-002`'s own precedent of exploring
candidate layouts in `agents-map-exploration.html` before committing to
one, since this is new visual/interaction design, not a pure logic fix.
Depends on `REQ-SB-12-US-01` (Agents Map, Done — the overview this
extends) and relates to `REQ-SB-37` (Agent Creation, Draft — the main
way agent count actually grows over time). -->

**Acceptance:** When a Section has more agents than can render without
crowding/overlapping, the Agents Map overview shows a cluster marker (a
count and a "+") in place of the individual agent nodes it represents,
instead of rendering them all at fixed positions regardless of count;
clicking the cluster marker reveals the agents inside it.

---

### REQ-SB-39: Unify Agent Capabilities Under Skills

Every agent capability — including every existing hardcoded Action
(`run_capture_now`, `rebuild_person_note`, `ask_question`,
`view_last_run`, `view_channel_status`, `pause_schedule`,
`build_knowledge`) — becomes a Skill, granted/revoked the same way
`REQ-SB-27`'s existing mechanism already does for `web-research` and
`diagram-understanding`. There is no longer a second, parallel,
hardcoded-in-Python capability system; Skills become the single way any
agent, existing or newly created, gets something to do.

<!-- Raised 2026-08-13, operator-directed, in direct response to
REQ-SB-37's own "can a user-created agent define custom actions?" open
question: "We have no Custom Action, we need to Convert those Custom
Actions to Skills. Example, Read Mail is a Skill under Outlook COM Tool
we need to have that in our tool set." Confirmed, when asked how far
this should go: **"Everything, including existing shipped agents"** —
not just new wizard-created agents; every already-shipped, already-
verified action this session built gets refactored, for one consistent
model going forward.

This is a genuine architecture reversal, not a wizard feature — flagged
explicitly to the operator as such before this requirement was written,
and confirmed as the intended scope. It touches a large surface: `ADR-011`
point 2's own action-definition shape (`app/business/agent_registry.py`'s
static `AGENTS` catalog), `ADR-020`'s entire two-axis working-mode
gate (which keys Supervised's approval requirement off each action's own
`mutates` classification — a concept that has no direct Skills-side
equivalent today, since `REQ-SB-27`'s own Skills were built for
narrower, largely read-only/side-effect-limited capabilities like
web-research and diagram-understanding, not for triggering a real
background capture pipeline or rebuilding a Person note), and every
already-shipped story that added or relied on an Action:
`REQ-SB-07`/`08`/`09` (capture pipelines, `run_capture_now`),
`REQ-SB-10` (`rebuild_person_note`), `REQ-SB-13`/`25` (chat-triggered
actions), `REQ-SB-21` (the working-mode gate itself), `REQ-SB-36`
(`build_knowledge`). Genuinely open, not decided here: (1) whether
`mutates` becomes a per-Skill classification (mirroring `agent_registry`
action's own field exactly) so `ADR-020`'s existing Supervised-mode gate
logic can key off Skills with minimal redesign, or whether Skills need a
materially different approval model; (2) whether Skill invocation for a
mutating capability (e.g. the refactored `run_capture_now`) needs to
gain the same Manual/Supervised/Autonomous gating chat/direct actions
already have, since `REQ-SB-27`'s own skill-invocation endpoint
(`POST /agents/{agent_id}/skills/{skill_id}/invoke`) was never built
with that gate in mind; (3) migration mechanics — does every existing
agent's current action set get auto-converted to equivalent Skill
grants at once, or does this roll out incrementally; (4) whether the
chat-triggered keyword-match funnel (`ADR-011`) itself needs to change
to dispatch to Skills instead of Actions, or whether that funnel stays
Action-shaped and Skills remain a parallel, chat-independent invocation
path (which would only partially satisfy "one consistent model"). Left
to `/spec`/`/plan-tasks` — expect this to need serious architectural
design work and likely more than one superseding ADR, not a quick
extension. This is a hard prerequisite for `REQ-SB-37`'s own
Worker/Producer wizard flows, which are Skills-based by the operator's
own direction. Depends on `REQ-SB-21-US-01` (Working Modes, Done — the
gate being redesigned) and `REQ-SB-27-US-01` (Skills, Done/plumbing —
the mechanism being generalized). -->

**Acceptance:** Every capability any agent has — including every
capability that exists today as a hardcoded Action — is represented and
invoked as a Skill; granting or revoking an agent's capabilities uses
one consistent mechanism regardless of agent type or when the agent was
created; a mutating Skill's invocation still honors the agent's own
working mode (Autonomous/Supervised/Manual) the same way a mutating
Action does today.

---

### REQ-SB-40: Agent Knowledge-Gap Tracking & Expert Readiness

Every time an agent honestly answers "I don't know" (REQ-SB-33), that
gap is recorded, not just spoken. The user can see an agent's
accumulated gaps, close one by providing information directly or by
directing the agent to research it, and watch the count of open gaps
decline over time — the count of remaining "I don't know"s is the
signal of how close an Expert agent is to being genuinely expert in its
domain.

<!-- Raised 2026-08-13, operator-directed, verbatim (answering "what
makes an Expert agent actually ready/complete"): "I guess we need both
the wizard, and the Agent can say I don't know as a start, and a human
input is needed to fill the gap — by time it will be Expert (the number
of I don't know is how we close this Expert gap in future)." This
builds directly on REQ-SB-33 (Agent Grounding & Honest-Uncertainty
Guardrail, Done, SPRINT-018) — that requirement made an agent say "I
don't know" honestly instead of fabricating, but the reply itself is
never captured anywhere beyond the chat transcript; this requirement is
the natural next layer the operator's own recommendation-response text
in that session already anticipated ("part of Agent Health"). Relates
to, without duplicating: REQ-SB-31 (System Health View, Done —
current-snapshot infrastructure status, not per-agent knowledge
completeness); REQ-SB-11 (Activity & Error Observability, Done —
chronological background-run outcomes, not conversational
honest-uncertainty instances, a different kind of event entirely);
REQ-SB-36 (delegated research — one of the two named ways a gap gets
closed, "directing the agent to research it"). Genuinely open, not
decided here: (1) the exact mechanism for detecting/recording an "I
don't know" — a structured signal the model itself emits alongside its
reply (more reliable, requires extending REQ-SB-33's own system-prompt
design), vs. a pattern-match over the reply text (cheaper, less
reliable); (2) what "human input fills the gap" looks like concretely —
a chat reply that gets filed via the Vault Filing Expert the same way
REQ-SB-23's My Day Intake Agent already files conversational input, or
a dedicated gap-resolution UI; (3) where the gap count/readiness signal
is surfaced (the new Agent Overview surface, REQ-SB-41, is the obvious
fit, but not confirmed); (4) whether a closed gap needs any
verification that it was actually answered correctly, or whether any
human-provided or research-derived content unconditionally counts as
closing it. Left to `/spec` — expect real design work, this is a
genuinely new capability, not an extension of an existing pattern.
Depends on REQ-SB-33 (Done — the honest-uncertainty behavior this
captures) and relates to REQ-SB-35 (Vault Filing Expert, Done — likely
where gap-closing content gets filed), REQ-SB-36 (delegated research, a
named gap-closing path), and REQ-SB-41 (Agent Overview, the likely
display surface). -->

**Acceptance:** Every honest "I don't know" an agent gives is recorded
as an open knowledge gap, not just spoken and forgotten; the user can
view an agent's open gaps; a gap can be closed either by the user
directly providing the missing information or by directing the agent to
research it; the count of open gaps for an agent is visible and
decreases as gaps are closed.

---

### REQ-SB-41: Agent Overview Surface

Opening an agent currently lands straight on its Chat tab. Before
chatting, the user can see an overview of what the agent actually is:
its purpose, its Vault Scope, its grounding/guardrail behavior, and
whether it's Autonomous, Supervised, or Manual — a real summary, not
just a chat box.

<!-- Raised 2026-08-13, operator-directed, verbatim: "The Agents Tab now
Opens Straight to Chat I need to have an Overview Of what the Agent do,
Scope, Guardrails and Is It Autonomous Etc before [I] Can Chat with it."
`AgentDetailPanel.tsx` (REQ-SB-13/21, Done) already has a tab structure
(Chat/History/Settings, `SPRINT-021`) — this requirement is most
naturally a new tab (or a new default landing view) added to that same
panel, not a wholly new surface, but two of the four things the
operator wants shown have no existing UI representation to reuse: (1)
**Scope** — REQ-SB-29 (Agent-to-Tag/Folder Scoping) is still `Draft`,
never built; there is nothing to display until it ships. (2)
**Guardrails** — REQ-SB-33 (Done) is a global, always-on system-prompt
instruction with, per its own Notes, "no new Agent Settings UI needed
this pass" — it has never been surfaced anywhere in the UI, for any
agent. Working mode (REQ-SB-21, Done) and purpose/description (already
on every agent's existing Settings tab) are both already real, existing
data this requirement just needs to surface earlier/more prominently.
Genuinely open, not decided here: (1) whether this is a new 4th tab
("Overview") alongside Chat/History/Settings, or replaces Settings'
current landing position, or becomes the panel's new default tab
(currently Chat); (2) exact Guardrails copy/presentation, given the
guardrail itself is global and non-configurable today — likely a
static, informational statement ("this agent only answers from what its
tools actually find") rather than a toggle; (3) whether REQ-SB-40's gap
count (once built) belongs on this same Overview. Left to `/spec` — a
`/design` pass is also needed (no prototype shows this). Depends on
REQ-SB-21-US-01 (Working Modes, Done) and REQ-SB-33-US-01 (Grounding,
Done); blocked on REQ-SB-29-US-01 (Vault Scope, still `Draft`) for the
Scope half specifically — the rest of this requirement (purpose,
guardrails, working mode) does not need to wait for it. -->

**Acceptance:** Opening an agent shows an overview — its purpose, its
Vault Scope (once assigned), a statement of its grounding/guardrail
behavior, and its current working mode — before or instead of landing
directly on the Chat tab.

---

### REQ-SB-42: Real-Time Agent Activity Pulses (Agents Map)

Replace the Agents Map's static agent-to-agent connections with a live,
real-time visualization of what's actually happening right now: which
agents are currently active, and — when one agent's request is actually
being routed to another (Hub-to-Hub cross-section routing) — a traveling
pulse between the two specific agents involved.

<!-- Raised 2026-08-13, operator-directed: "instead of a static Agents
Connection... show real time inter communication between agents like
pulses and showing active Agents at the moment who is currently running
a task (as a Pulse Visual)." Clarified via requirements-gathering
session, verbatim decisions: (1) "active" covers four triggers — running
a capture/Skill, generating a chat reply, an in-flight Hub-routed
cross-section request (REQ-SB-20, Done — `graph.
route_cross_section_request`), and an open pending-approval record
(REQ-SB-21, Done — Supervised-mode gate); (2) both a per-agent glow (for
the first three, general "this agent is working" states) and a traveling
pulse between two specific agents (for the Hub-routed case only, since
that is the one case with two real named endpoints) are wanted,
together; (3) an open pending-approval record renders as a visually
distinct, steady/non-animated highlight — it is a paused/blocked state,
not an actively-working one, and must never be confused with the
animated pulse; (4) surfaces on both the Agents Map overview and a
Section's drill-down Agents Tree; (5) the existing decorative KB↔Hub
spoke pulse (`agents-map.html`'s always-on `kb-pulse-dot` animation,
data-independent) is kept unchanged as ambient texture — this
requirement is a new, additive, data-driven layer on top, not a
replacement; (6) real-time means near-instant push, not a polling
interval — operator explicitly chose push over a 2–5s poll.

Genuinely open, left to `/plan-tasks`: **no live/ephemeral per-agent
activity state exists today** — REQ-SB-11's Agent Activity & Error
Observability (Done) records completed history entries only, after the
fact; this requirement needs a new "is this agent doing something right
now" concept, written at the start of each real dispatch path (capture
run, Skill invocation, chat generation, Hub-routed call, pending-approval
creation) and cleared at completion. **No real-time push transport
exists today** — every existing surface is REST/poll-shaped; introducing
WebSocket or SSE is a genuine new architectural capability, not a small
lift, and the specific choice between them is an architect-level call.
Also open: exact visual treatment (glow radius/color, traveling-pulse
styling relative to the existing `kb-pulse-dot`), and whether the
Section drill-down's Agents Tree needs its own connection-line
geometry for the Hub-routed traveling-pulse case or can reuse the
overview's. Depends on REQ-SB-20-US-01 (Section Hub Intelligence &
Cross-Section Routing, Done), REQ-SB-21-US-01 (Agent Working Modes,
Done). A `/design` pass is needed — no prototype shows live/animated
per-agent activity state today, only the static decorative pulse. -->

**Acceptance:** On both the Agents Map overview and a Section's
drill-down Agents Tree, an agent visually pulses/glows while it is (a)
running a capture or Skill, (b) generating a chat reply, or (c) engaged
in a Hub-routed cross-section request to/from another agent — the
latter rendered as a traveling pulse along the connecting line between
the two specific agents. An agent with an open pending-approval record
renders with a distinct, steady (non-animated) highlight instead, so a
blocked/waiting agent is never visually confused with an actively-working
one. Updates arrive via a real-time push channel (near-instant, not
polling). The existing decorative KB↔Hub spoke animation is unaffected —
this is a new, additive data-driven layer.

---

### REQ-SB-43: Meeting Cockpit — Expert-Assisted Meeting Workspace

Clicking a meeting (from My Day's Calendar) opens a dedicated 3-panel
workspace, usable both to prep before the meeting and to keep open live
during it. The right panel shows the meeting's info, with each attendee
rendered as a clickable chip that links to their existing Person note in
the vault. The middle panel is a chat where the user can bring in Expert
agents as needed — every Expert brought in sits in one shared,
unified conversation thread. The left panel lists the user's available
Agents (to bring into that chat) and this meeting's own quick-research
results. From the chat, the user can trigger on-the-spot research and,
for each result, explicitly choose whether to save it into the vault or
discard it.

<!-- Raised 2026-08-13, operator-directed, verbatim: "Once I click on a
meeting that means I need the Help of the Map, The System Check the info
of the meeting, Allow me to go to the meeting with the Experts that I
need their help in that meeting and allow me to do a quick research on
the spot and I choose either to add that to the Vault or no... it will
be 3 Panels, Info in the right with People in the meeting clickable as
Tags or Chips so I can know about who are they in the Vault the middle
is a Chat Window based on the Agent the left in my Agents and the
Researches I created and I can Bring Experts as needed to the meeting."
Clarified via requirements-gathering session, verbatim decisions: (1)
one workspace serves both pre-meeting prep and live, during-the-meeting
use — no separate mode; (2) the middle panel is a single unified
multi-agent chat thread, not one thread per brought-in Expert; (3) the
left panel's research list is scoped to this one meeting, not a
cross-meeting personal library; (4) saving a quick-research result
creates a new, standalone note wikilinked to the meeting's own Meeting
note (REQ-SB-08's existing note type), matching this project's
established one-note-per-thing pattern (Person/Meeting/Research notes),
rather than being appended into the Meeting note itself.

**Distinct from, not a replacement for, REQ-SB-20's Hub routing:**
REQ-SB-20's cross-section routing is agent-initiated — an agent
autonomously asks its Hub for help outside its own knowledge. This
requirement's "bring Experts as needed" is user-initiated — the person
using Second Brain explicitly chooses which Expert(s) join this
meeting's chat. Both mechanisms can coexist; this requirement does not
change REQ-SB-20's own behavior.

Genuinely open, left to `/spec`/`/plan-tasks`: exact entry-point
mechanics (today's My Day Calendar rows are a flat, non-clickable list —
REQ-SB-08's own capture pipeline gives no signal for "meeting currently
in progress," so whether prep-mode and live-mode need any different
data is unresolved); how a unified multi-agent chat attributes each
reply to the specific Expert that produced it; what an attendee chip
does when no Person note exists yet for that attendee (link to a
create flow, or a plain "no note yet" state); whether working-mode
gating (Autonomous/Supervised/Manual, REQ-SB-21) still applies to an
Expert's actions once brought into this cockpit, or whether being
explicitly user-invited changes that; and the on-the-spot research
mechanism itself (reusing REQ-SB-36's existing web-research skill
directly, or a new capability). Depends on REQ-SB-08-US-01 (Meeting
notes must exist to attach to), REQ-SB-10-US-01 (Person notes, for the
attendee chips), REQ-SB-18/REQ-SB-20 (Sections and Experts must exist to
be "brought in"), REQ-SB-36 (the web-research skill this likely reuses
for on-the-spot research). A `/design` pass is needed — no prototype
shows this 3-panel workspace; `my-day-calendar.html`'s meeting rows are
not currently clickable at all. -->

**Acceptance:** Clicking a meeting item, before or during that meeting,
opens a 3-panel Meeting Cockpit: the right panel shows the meeting's
info with every attendee as a clickable chip linking to their Person
note (when one exists); the middle panel is one unified chat thread in
which every Expert the user has brought in can respond; the left panel
lists the user's available Agents (to bring into the chat) and this
meeting's own quick-research results. From the chat, the user can
trigger on-the-spot research, and each research result offers an
explicit choice to save it as a new note wikilinked to the Meeting note,
or discard it.

---

### REQ-SB-44: Inbox Cockpit — Expert-Assisted Email Workspace

Clicking an email (from My Day's Emails list) opens the same 3-panel
workspace pattern as REQ-SB-43's Meeting Cockpit, adapted for email. The
right panel shows the email's info, with every person on it — sender
plus any CC'd or thread participants — rendered as a clickable chip
linking to their existing Person note, and the email's attachments (if
any) surfaced for review. The middle panel is a unified multi-agent
chat where brought-in Experts can help the user understand the email
and draft a reply as text — this pass never sends anything on the
user's behalf. The left panel lists the user's available Agents (to
bring into the chat) and this email's own quick-research results. From
the chat, the user can trigger on-the-spot research and, for each
result, explicitly choose whether to save it into the vault or discard
it.

<!-- Raised 2026-08-13, operator-directed: "Same Idea for the inbox."
Reuses REQ-SB-43's own already-settled decisions verbatim: one unified
multi-agent chat thread (not one thread per Expert); the research list
is scoped to this one email, not a cross-email personal library; a
saved research result becomes a new, standalone note wikilinked to the
email's own Email note (REQ-SB-07's existing note type), not appended
into it. Clarified via requirements-gathering session, verbatim
decisions on the genuine ways email differs from a meeting: (1) unlike
the Meeting Cockpit (research/prep only, never acts on the real-world
event), this chat CAN draft a reply as reviewable text — but sending is
explicitly out of scope for this pass; drafting a reply is not itself a
vault-mutating or externally-visible action, so it does not need
working-mode/approval gating the way a real send would; a future
send capability, if ever built, is a separate, later decision requiring
its own Supervised/Manual approval gating (mirroring REQ-SB-21), not
assumed or half-built here. (2) people chips cover the sender AND any
CC'd/thread participants, not sender-only, mirroring a meeting's
multi-attendee chip row rather than a single-person case. (3)
attachments are in scope this pass, surfaced for the brought-in Experts
to review — this creates a real, hard dependency on REQ-SB-28 (File
Upload for Agents, `Draft`, not yet built), unlike REQ-SB-43 which has
no attachment concept at all.

Genuinely open, left to `/spec`/`/plan-tasks`: whether a drafted reply
persists anywhere (saved as a draft object the user can return to,
or purely ephemeral within the chat session until copied out); whether
today's Email note frontmatter/`email_classification.py` capture
CC'd-recipient or thread-participant data at all (a quick check of
`architecture.md`'s Data Model during this session found no existing
`cc`/`thread_id`-equivalent field — this may need new capture-side work,
not just a cockpit-side read, and is a real open question, not assumed
resolved); how an attachment surfaced here relates to REQ-SB-28's own
Compass-summarize/attach-and-handoff mechanism (reused directly, or a
separate read-only preview); and the same open questions REQ-SB-43
already named for its own entry-point/multi-agent-attribution/
working-mode-gating mechanics, which apply here identically. Depends on
REQ-SB-07-US-01 (Email notes, Done), REQ-SB-10-US-01 (Person notes, for
the people chips), REQ-SB-18/REQ-SB-20 (Sections and Experts, for
"bring Experts as needed"), REQ-SB-28 (File Upload for Agents, `Draft` —
hard prerequisite for the attachments half specifically, not the rest
of this requirement), REQ-SB-36 (the web-research skill this likely
reuses for on-the-spot research). A `/design` pass is needed — no
prototype shows this workspace; `my-day-emails.html`'s rows are not
currently clickable at all. -->

**Acceptance:** Clicking an email item opens a 3-panel Inbox Cockpit:
the right panel shows the email's info with the sender and every
CC'd/thread participant as a clickable chip linking to their Person
note (when one exists), plus the email's attachments if any; the middle
panel is one unified chat thread in which every Expert the user has
brought in can respond, including drafting a reply as reviewable text
(never sent automatically); the left panel lists the user's available
Agents (to bring into the chat) and this email's own quick-research
results. From the chat, the user can trigger on-the-spot research, and
each research result offers an explicit choice to save it as a new note
wikilinked to the Email note, or discard it.

### REQ-SB-45: Shared Serialization for Scheduled Background Jobs

As more agents gain their own scheduled/app-start triggers (beyond
today's single email-capture job), a shared serialization mechanism
ensures at most one Outlook-COM-touching background job runs at a time
across all of them — not just within one job type, as today's
`_capture_run_lock` does.

<!-- Raised 2026-08-14, operator-directed, during BUG-008's fix session.
Not urgent today: `capture_scheduler.py` currently wires exactly one
scheduled job (`run_capture_if_idle`, email capture only), so there is
nothing yet for a shared lock to serialize against. The concern is real
and forward-looking, not speculative: `SPRINT-030`'s own live
verification session accidentally ran two full capture passes
concurrently (two backend processes racing on the same live Outlook/
Compass calls) after a coder mistakenly started two server instances —
demonstrating that today's lock only protects a job against itself, not
against a sibling job touching the same COM resource. As meeting-
capture, todo-capture, people-producer, or REQ-SB-40's own future
scheduled gap-checks (if any) gain independent app-start/interval
triggers, the same class of collision becomes reachable through normal
operation, not just an operator mistake.

Explicitly NOT a full task-queue/broker — this project has deliberately
stayed JSON-file/in-process throughout (no database, no message broker);
a queue would be disproportionate new infrastructure for a single-user
local app. The right-sized fix is a generalization of the existing
pattern: one shared lock (or equivalent) that every Outlook-COM-touching
scheduled job acquires before running, mirroring `_capture_run_lock`'s
own already-proven shape rather than introducing new machinery.

Deliberately deferred to `/spec` once there is a second real scheduled
job to design the shared lock against — building it now, against only
one caller, risks guessing the wrong shape.

**Update, 2026-08-14 — Activated.** `REQ-SB-47` (Per-Agent Scheduler)
introduces exactly that second real caller — the operator confirmed
building this requirement's shared lock as part of `REQ-SB-47`'s own
work, rather than continuing to defer it. No longer speculative; in
scope now. -->

**Acceptance:** When two or more scheduled/app-start background jobs
that touch Outlook COM would otherwise be eligible to run at the same
time, only one actually runs; the others wait or skip (mirroring
`run_capture_if_idle`'s own existing skip-not-queue behavior) rather than
executing concurrently against the same COM resource.

### REQ-SB-46: Agent Creation Wizard Redesign — Popup Modal with Visual Step Bar

The Agent Creation Wizard (`REQ-SB-37`, shipped) moves from a Settings-page
entry point to a floating action button at the bottom-right of the Agents
Map, opening as a popup modal with a visual step-progress bar (steps 1-4)
across the top. The wizard's step content is reorganized: Step 1 —
Name, Description, Type, Scope (shown only when the selected Type has
one — Worker), and Section. Step 2 — Instructions/Guardrails, and the
agent's output plus what it does with that output. Step 3 — Tools/Skills
the agent has access to (grouped per `REQ-SB-48`). Step 4 — a summary
review, plus a Trigger choice for how the agent gets invoked: User
(direct/chat-triggered, today's default), Agent (Hub-routed/cockpit
`@mention`-invoked, per `REQ-SB-20`/`REQ-SB-43`/`REQ-SB-44`/`REQ-SB-49`),
or Schedule (configures a recurring schedule at creation time via
`REQ-SB-47`).

<!-- Raised 2026-08-14, operator-directed, verbatim: "The Link should be
in the Agentic Map at the Bottom Right. Click on it open a Pop up wizard
with the top is Steps Bar (1,2,3,4) A Visual Appealing one." This
requirement supersedes `REQ-SB-37`'s already-shipped step ORDER/UI shape
(inline on Settings, Expert/Worker/Producer type-first branching) — it
does not change the underlying per-type field set `REQ-SB-37-US-01/02/03`
already built (Purpose/Domain, Skills grant, Scope, Section, single
output Skill), only the entry point, the container (popup vs. inline),
the visual step-progress treatment, and the step-to-field grouping.

Genuinely open, left to `/spec`: (1) since Type is now chosen INSIDE Step
1 alongside Scope/Section (rather than as a separate first screen), Step
1 needs to dynamically show/hide the Scope field the instant Type
changes — the exact interaction (Scope field appears/disappears
in-place, vs. Type change resets the step) is a real UI decision; (2)
the Step 4 "Trigger: User/Agent/Schedule" concept is genuinely new — no
such field exists on any agent today. Whether choosing "Schedule" at
creation time actually opens `REQ-SB-47`'s own schedule-configuration UI
inline (composing that requirement) or just records an intent to
configure one later is left open; (3) whether "Agent" as a trigger choice
records anything structurally different from today's default (every
agent is already Hub-routable/`@mention`-able with no per-agent opt-in)
is also open — it may turn out to be purely informational/no-op at the
data-model level. -->

**Acceptance:** A floating action button at the Agents Map's bottom-right
opens the Agent Creation Wizard as a popup modal with a visual
step-progress bar showing steps 1-4; Step 1 collects Name, Description,
Type, conditionally Scope, and Section; Step 2 collects
Instructions/Guardrails and the agent's output/output-destination; Step 3
collects Tools/Skills access; Step 4 shows a summary and a Trigger choice
(User/Agent/Schedule) before creating the agent — the resulting agent is
functionally identical to one created through today's shipped wizard,
with a redesigned entry point and step flow only.

### REQ-SB-47: Per-Agent Scheduler

A new Schedule tab on the agent detail panel lets the user configure a
recurring schedule that sends a request to the agent to run one of its
assigned tasks/capabilities (e.g. "capture mail" for `email-capture`),
view that agent's own real run history, modify an existing schedule, and
trigger an immediate on-demand run ("run now").

<!-- Raised 2026-08-14, operator-directed, verbatim: "I need a Schedule
Tab, The Schedule Can Send a Request to Agent to Start do one of the
Tasks Assigned to the Agent (Capture mail example)... I need to know the
run History and Option to Modify the Schedule and Ability to run now."

This is the first PER-AGENT, PER-CAPABILITY generalized scheduling
mechanism — today only `email-capture` has any real scheduling at all,
hardcoded as a single `AsyncIOScheduler` job in `capture_scheduler.py`
with no UI. Building this properly requires generalizing that mechanism
to any agent/capability pair, which is exactly the second real caller
`REQ-SB-45`'s shared-lock generalization needs — **operator-confirmed
2026-08-14: build `REQ-SB-45` as part of this requirement's own work**,
not as a separate later pass.

Genuinely open, left to `/spec`: the concrete schedule-definition shape
(interval only, like today's hourly job, or a fuller cron-like
expression); which capabilities are schedulable (any granted Skill/
Action, or only ones explicitly marked schedulable); whether "run
history" reuses `REQ-SB-11`'s existing Agent Activity log directly or
needs its own schedule-run-specific view; and "run now"'s relationship to
the already-existing mutating `run_capture_now` Skill (likely the same
underlying mechanism, generalized). -->

**Acceptance:** An agent's detail panel gains a Schedule tab where the
user can configure a recurring schedule targeting one of that agent's own
assigned tasks/capabilities, see that agent's real run history, edit or
remove an existing schedule, and trigger an immediate on-demand run; when
more than one agent has an active schedule, or a scheduled run and an
on-demand run would otherwise overlap, only one Outlook-COM-touching run
executes at a time (`REQ-SB-45`).

### REQ-SB-48: Skills Grouped by Tool — Collapsible Multi-Select Tree with Icons

The unified Capabilities list (`REQ-SB-39`, shipped) reorganizes from a
flat list into Skills grouped under a parent "Tool" concept (e.g.
"Outlook" as a Tool containing the Skills that operate against it), each
Tool and Skill carrying an icon, presented as a collapsible tree the user
can multi-select within (grant/revoke more than one Skill under a Tool at
once).

<!-- Raised 2026-08-14, operator-directed, verbatim: "Skills should be
Grouped by Tools Outlook as a Tool with the Skills in it. Icons should be
Added and we need to be able to Multiselect those tools in the Agent in a
Collapse tree like Approach."

Genuinely open, left to `/spec`: **the Tool taxonomy itself does not
exist anywhere in this codebase today** (`skill_tools.SKILLS` is a flat
dict with no grouping field) — a real, new grouping decision, not a
lookup. A reasonable starting default (Outlook — `view_last_run`,
`run_capture_now`, `pause_schedule`; Vault — `ask_question`,
`view_channel_status`, `rebuild_person_note`, `write-to-vault-draft`,
`summarize-file`; Web — `web-research`; Compass — `build_knowledge`,
`diagram-understanding`) is a plausible mapping but not decided here —
`/spec` should confirm or adjust it. Icon sourcing (a fixed icon per Tool
vs. per individual Skill) is also open. -->

**Acceptance:** An agent's Capabilities list renders as a collapsible
tree grouped by Tool, each Tool and Skill showing an icon; the user can
multi-select and grant/revoke more than one Skill within an expanded Tool
group in one action; collapsing a Tool group hides its Skills without
losing their grant state.

### REQ-SB-49: Cockpit @Mentions

Inside a Cockpit's (`REQ-SB-43`/`REQ-SB-44`, shipped) chat, typing
`@agent_id` mentions and brings that agent into the shared thread inline
(an alternative to the left panel's bring-in list), and a message can
additionally mention a specific PERSON by name (e.g. `@AhmedMoussa`)
whose Person note the mentioned agent should update based on the
instruction text.

<!-- Raised 2026-08-14, operator-directed, verbatim examples:
"@meeting_Expert Take this file and Extract the info and Store it."
"@people Add The Following to @AhmedMoussa since now he is leaving the
company and going to Core42."

Two genuinely distinct mechanisms bundled under one "@mention" syntax,
not decided here, left to `/spec`: (1) `@agent_id` as an inline
bring-into-thread shortcut — a fairly direct UI affordance composing
`REQ-SB-43`/`44`'s own already-shipped bring-in mechanism. (2) A person
mention (`@AhmedMoussa`) inside an instruction directed at an agent
(here, the People Notes producer) implies that agent should locate the
real Person note matching that name and apply a natural-language-
described update to it — this is a genuinely new, real vault-write
capability (parsing an instruction, resolving a name to a real Person
note, applying an edit) that composes with `REQ-SB-04`'s vault-write
mechanism and very likely needs `REQ-SB-21` working-mode gating (a
person-note edit is a real mutation, unlike the Cockpit's existing
research-save-with-explicit-confirm flow) — left entirely to `/plan-tasks`
to design, not guessed at here. -->

**Acceptance:** Typing `@agent_id` in a Cockpit chat message brings that
agent into the shared thread inline; a message mentioning a specific
person by name, directed at a brought-in agent, results in that agent
locating the real matching Person note and proposing (never silently
applying) an edit reflecting the instruction, subject to that agent's own
working-mode gate.

### REQ-SB-50: Tags and Locations Autocomplete

Tag and folder/location input fields across the app (at minimum the
Vault Scope field, `REQ-SB-29`) suggest real, existing vault tags and
folder paths as the user types, sourced from the vault's own current
content — never a fixed or fabricated list.

<!-- Raised 2026-08-14, operator-directed, verbatim: "Tags and Locations
Should Support Auto Complete." Minimal, contained requirement — this
codebase already has real, vault-derived enumeration primitives to build
on (`list_known_customers`/`list_known_partners`-shaped functions).
Genuinely open, left to `/spec`: the full list of input fields this
applies to beyond the Vault Scope field named by the operator (candidates
include the Wizard's own Section/Scope fields, `REQ-SB-46`). -->

**Acceptance:** A tag or location input field offers real, vault-derived
suggestions as the user types, drawn from the vault's actual current tags
and folder paths — never a hardcoded or fabricated suggestion list.

### REQ-SB-51: Background Agents — Excluded from Inter-Agent Addressing, Displayed Separately

An agent can be marked as a Background Agent — one that runs its own
work (typically on a schedule or app-start trigger) but is never a valid
target for another agent's Hub-routed request or a Cockpit `@mention`
bring-in, and is displayed in a separate area of the Agents Map rather
than among the addressable agents in the main Section/ring layout.

<!-- Raised 2026-08-14, operator-directed, verbatim: "I need to have some
Agents as Background Agents, They don't talk to others for example Email
Capture is An Agent but not to be called by others I guess They should be
Hidden Displayed in a Different Place."

Genuinely open, left to `/spec`: (1) whether this is a new explicit
per-agent boolean flag (default `false`, settable at creation via
`REQ-SB-46`'s own wizard and via existing agent Settings) or an inferred
property of something already real (e.g. every current Worker-type
capture pipeline could plausibly be background-by-default) — the
operator's own "I need to have SOME Agents as Background" phrasing reads
as an explicit, opt-in marking, not an automatic Type inference, but this
is not decided here. (2) Whether the 3 existing capture-pipeline Workers
(`email-capture`, `meeting-capture`, `todo-capture` — the operator's own
named example) should be retrofitted to this flag as part of this
requirement, mirroring this project's own established retrofit pattern
for existing shipped agents (`REQ-SB-39`'s Skills migration,
`REQ-SB-41`'s Purpose backfill). (3) The exact display treatment for
"a different place" — a distinct visual area/list on the Agents Map
(e.g. below or beside the main Section wheel), not decided here. (4)
Whether "not to be called by others" also excludes a Background Agent
from the Agent Creation Wizard's own Step 4 "Agent" trigger option and
from the Cockpit's left-panel bring-in list (both already real,
`REQ-SB-43`/`44`/`46`), or only from Hub-routing specifically — the
operator's own "don't talk to others" phrasing reads broadly (all
inter-agent addressing paths), not narrowly. (5) Whether a Background
Agent can still be manually opened/chatted with directly by the user
(the operator's own concern is about OTHER AGENTS calling it, not the
user) — resolve conservatively toward "yes, the user can still reach it
directly" unless `/spec` finds a reason otherwise. -->

**Acceptance:** An agent marked as a Background Agent never appears as a
selectable target in another agent's Hub-routed cross-Section request or
in a Cockpit `@mention`/bring-in list; it is displayed in a distinct area
of the Agents Map, separate from the addressable agents in the main
Section/ring layout; the user can still open and interact with it
directly.

### REQ-SB-52: Agents Map Visual Redesign — SkillTree-Inspired Theme

The Agents Map overview and agent detail surfaces adopt a new visual
treatment inspired by a reference site (`skilltree.altari.ai`) the
operator liked: a dark, ambient theme with an animated starfield
background, translucent "glass" detail cards, and a polished zoom
toolbar — applied to this app's own existing Section/agent data model,
not a copy of the reference site's own content or department taxonomy.

<!-- Raised 2026-08-14, operator-directed: shared a reference URL,
confirmed (after two attempts — the first failed on tooling limits, the
second succeeded by reaching into the reference site's own iframe) real,
concrete design elements worth adopting:
- Dark charcoal-navy background (`#20242D`), warm cream text (`#E9E4D6`),
  "Plus Jakarta Sans" typeface.
- An animated twinkling starfield background — many small, randomly
  positioned/sized/timed pulsing dots, a cheap real CSS animation, not
  canvas/WebGL.
- Detail panels as translucent near-black "glass" cards
  (`rgba(14,17,24,.85)`, 10px rounded corners, flat — no shadow).
- A standard zoom toolbar (−, %, +, Fit, help) for the map viewport.
- The reference site's own drill-down-with-a-back-button pattern and
  department-carousel browsing already have close analogues in this
  app's shipped Section Hub drill-down and radial Section layout —
  adopting the SkillTree-inspired chrome does not require inventing a
  new navigation model, mostly a new visual skin over what's already
  real and working.

Explicitly NOT in scope: the reference site's own marketing/paywall
elements (email gate, "Founding Cohort" purchase modal), its own
Department/Team/Job/Skill content taxonomy (this app already has its own
real Section/Type/agent model), and its "Dashboard"/"Chart" alternate
view modes (a possible later, separate requirement, not assumed here).

Given this is a genuinely new, distinctive visual direction (not a
well-understood interaction pattern a coder can safely improvise, unlike
several recent smaller enhancements this session deliberately skipped
`/design` for), operator-directed: run `/design` first and get a real,
browser-viewable prototype signed off before this becomes a spec'd story
and a build.

**Deferred follow-on, explicitly NOT in this pass's scope, operator's
own words (2026-08-14): "I believe producers will be closers to the hub
as they produce info for Knowledge Base Workers are the Pipeline kind
and Experts will be my External Layer We will get to that intime."** A
real semantic reordering of `layoutAgents.ts`'s ring-per-Type radius
assignment — Producer innermost (closest to the Knowledge Base, since a
Producer's own output feeds it directly), Worker in the middle (the
pipeline/capture stage), Expert outermost (the externally-reachable
layer). Not a color/theme change — a structural change to which Type
occupies which ring. Deliberately not folded into this reskin pass;
revisit as its own follow-on once the operator returns to it.

**Update, 2026-08-14 — operator escalation: "No No I want to Copy
everything The Layout the Animation the Looks and Colors Forget what we
have."** The first `/design` pass (a light reskin — 2 colors + a
starfield layer + glass panels, keeping the existing bounded canvas and
structure) is NOT sufficient; the reference site's ENTIRE visual system
is now the direct authority, not an accent layered on top of the current
design. Re-extracted the reference site's own real CSS source (not just
computed styles this time — 4 `<style>` tags, ~67KB, read directly from
its own DOM) for a complete, reproducible system:

**Full real color palette** (`:root`, not just the 2 tokens the first
pass used):
```
--bg: #0E1118;            /* map canvas background — darker than the outer chrome */
--ivory: #E9E4D6;         /* primary text */
--ivory-2: #B9B4A6;       /* secondary/muted text */
--ink-2: #8A8DA0;         /* tertiary text/icon */
--ink-3: #565A6E;         /* most-muted, borders */
--copper: #C58B5F;        /* accent — used on the central "hub" chip */
--line: rgba(233,228,214,.1);   /* hairline borders */
--glass: rgba(14,17,24,.85);    /* panel background */
```

**Layout is a true full-viewport canvas, not a bounded box** —
`#viewport { position: fixed; inset: 0; overflow: hidden; }`. The first
pass kept the map inside the existing `.agents-map-stage` bounded
container; the reference's own map fills the entire screen edge-to-edge.

**Real node styling:** 74×74px circles, centered via a negative-margin
trick (`margin: -37px 0 0 -37px` — positioning math is against the
node's CENTER point, standard for radial/polar layouts), `border-radius:
50%`, smooth `.18s` transform/shadow transitions. Nodes pop in
**staggered**, not all at once — `animation: nodepop .45s
cubic-bezier(.2,.9,.3,1.4) forwards; animation-delay: var(--d, 0s)` (a
slight bounce-overshoot easing, per-node delay via a CSS custom
property) — this staggered cascade entrance is a real, adoptable detail.
A subtle background "ring"/orbit track sits behind the nodes at near-zero
opacity (`background: rgba(32,35,43,.02)`, plus a soft outer glow via
`box-shadow: 0 0 0 10px rgba(32,35,43,.025)`).

**Real animation set** (10 relevant `@keyframes`, exact values):
- `twinkle` (stars): opacity `.45 → .1 → .45`, `6s ease-in-out infinite`.
- `nodepop` (node entrance): scale `.3 → 1` + fade in, bounce easing, staggered per-node.
- `treein` (tree/section entrance): fade + `translateY(34px) → 0`.
- `drawline` (connector lines): SVG `stroke-dashoffset` animates to `0` — connector lines literally draw themselves in, not just fade.
- `npulse` (a "live" node): SVG circle radius `5 → 6.5 → 5` with opacity pulse.
- `livepulse` (glow ring around an active node): `box-shadow` pulses using `color-mix(in srgb, var(--c) …%, transparent)` — a per-node color-coded glow ring that expands/contracts.
- `hspin` / `hdrift` (the central hub): a full 360° spin plus a tiny few-px organic drift, both slow/subtle — the hub isn't static, it breathes.
- `chevnudge` (edge-navigation hint): the left/right paging chevron nudges a few px to draw the eye.
- `bpulse` (a badge): opacity pulse `.85 → .2`.

**Detail card ("glass" panel), real values:** `background: var(--glass);
backdrop-filter: blur(16px);` — a REAL frosted-glass blur, not just a
translucent flat color (the first pass's glass had no blur). `border: 1px
solid var(--line); border-radius: 10px;` fixed position `top:104px;
left:28px; width:364px;`, its own internal scroll
(`max-height: calc(100vh - 200px); overflow-y: auto`).

**Zoom toolbar, real values:** fixed `bottom:16px; right:16px;`, same
glass+blur treatment (`blur(12px)`), compact `3px` padding, `10px`
radius.

**Department-paging edge navigation:** `position: fixed` (not absolute —
stays put regardless of pan/zoom), vertically centered
(`top:50%; transform: translateY(-50%)`), `z-index:9`, hidden by default
(`opacity:0; pointer-events:none`) until activated — a real, deliberate
"revealed on hover/interaction" affordance, not always-visible chrome.

**Typography:** `h1 { font-family: 'Plus Jakarta Sans', …; font-size:
27px; letter-spacing: .12em; font-weight: 400; }` — wide letter-spacing,
regular (not bold) weight, for a refined display-heading feel. The
reference also loads a second font, **Marcellus** (a serif), not yet
placed to a specific element in this pass's own extraction — worth the
designer checking where it's used before assuming Plus Jakarta Sans
covers everything.

**Still explicitly NOT in scope** (unchanged from the first pass): the
reference's own marketing/paywall chrome, its own Department/Team/Job/
Skill content (this app's own real Section/Type/agent data replaces it
1:1), and its "Dashboard"/"Chart" alternate view modes. -->

<!-- Update, 2026-08-15 — operator escalation: scope widened from "Agents
Map surfaces" to the WHOLE APP: "Go full Sprint, Colors and fonts need to
follow the prototype." Confirmed explicitly via clarifying question
("Whole app" over "Agents Map only") — `tokens.css`'s own `:root` color
variables and the global font stack are shared by every screen (My Day,
Settings, System Health, Agent Activity, Browse & Search, the Agents Map),
so this is a genuine `tokens.css`-level palette + typography swap, not a
per-screen restyle. **This reverses a previous, deliberate decision** —
`tokens.css`'s own standing comment records the app was switched FROM a
dark theme TO the current light/green theme "per operator browser review"
(2026-08-10); this update supersedes that reversal with a fresh, explicit
operator instruction, not a silent flip-flop — the reasoning for the
2026-08-10 switch was never itself invalidated, the operator has simply
now decided differently in light of the SkillTree-inspired exploration
prototype.

**Scope of this pass, precisely:** replace `tokens.css`'s `--color-*`
variables with the dark palette above (`--bg`/`--ivory`/`--ivory-2`/
`--ink-2`/`--ink-3`/`--copper`/`--line`/`--glass`, mapped onto this app's
own existing token NAMES — `--color-bg`, `--color-surface`, `--color-text`,
`--color-accent`, etc. — not new, differently-named tokens, so every
screen's existing `var(--color-*)` usage picks up the new palette for
free with no per-screen CSS edits); load the real "Plus Jakarta Sans" +
"Marcellus" font files locally (no CDN, matching this project's own
established no-network-font-request convention — see
`html-prototype/fonts/`) and wire them into `--font-sans`/a new
`--font-serif` token. Per-type agent colors (`--agent-color-worker/
-producer/-expert`) stay conceptually distinct from `--color-accent`
(unchanged intent) but their exact hex values may need re-tuning for
contrast against the new dark background — a designer/coder judgement
call, not re-litigated here.

**Explicitly still NOT in this pass's scope** (unchanged): the starfield
background, glass detail cards, zoom toolbar, drill-down animation set,
and every other structural/animation element documented above — those
stay scoped to the Agents Map specifically (already covered by this same
requirement's existing text) and to the html-prototype/ exploration work,
which the operator has explicitly deferred: "Leave the Rest till We
finish the prototype." This update is colors + fonts ONLY, applied
app-wide. -->

**Acceptance:** The Agents Map overview and its agent detail surfaces
fully adopt the reference system's real color palette, typography,
full-viewport canvas layout, node styling (size/positioning/staggered
entrance), glass-blur panel treatment, and the specific named animations
above (starfield twinkle, connector line-drawing, node pop-in, hub
spin/drift, live-pulse glow, edge-navigation reveal) — applied to this
app's own real Section/agent/Type data, not the reference's own content.
Every existing interaction (Section drill-down, cluster markers, agent
detail panel tabs, Cockpit, wizard) continues to work exactly as it does
today; only the visual/animation system changes, not the underlying
behavior or data model.

### REQ-SB-53: Split Capture Pipelines into Staged Pull / Tag / Link / Store Agents — SUPERSEDED

**Superseded 2026-08-16** by the `ADR-041` Agent/Pipeline/Job/Hub model
and its concrete pipelines: `US-01` (Email) by `REQ-SB-55`, `US-02`
(Meetings) by `REQ-SB-56`. `US-03` (To-Do) has no superseding requirement
yet — still parked, needs its own future re-spec under the same model.
Original scope: split each of the 3 monolithic capture Workers
(`email-capture`/`meeting-capture`/`todo-capture`) into 4 separate
Pull/Tag/Link/Store agent identities. Built on the pre-`ADR-041`
Agent-Type model, made obsolete by the Job/Pipeline taxonomy before any
part of it shipped. Full original text: `git log -p` on this file, or
`Implementation/Sprints/`/`Implementation/UserStories/` for whatever
partial work exists.

---

### REQ-SB-54: Vault Knowledge Model Redesign — Threads, Linked Meetings, Living Project & Customer Documents

Replaces the vault's own note-per-email capture shape with a layered
knowledge model: an **evidence layer** (Threads, Meetings, and manual
Captures — raw-but-processed records of what happened) feeding a
**synthesis layer** (Project and Customer documents — living records of
what's true right now). This is the foundational data-model requirement
every other requirement in this batch (`REQ-SB-55` through `REQ-SB-59`)
builds on.

<!-- Raised 2026-08-16, operator-directed, over an extended discussion
(not a single instruction) — the operator explicitly asked to be treated
as a thinking partner, not handed a spec, so this requirement reconstructs
the converged design from that conversation rather than a single ask.
Root pain stated directly: **"The pain is I can't find the current status
of anything."** Every decision below traces back to that one sentence.

**Evidence layer (raw, append-only, never silently rewritten):**
1. **Threads replace Emails.** Today (`email_classification.py`) every
   email becomes its own note; Outlook's real `ConversationID` is already
   captured (`outlook_com.py`) but only used for a loose
   `find_related_note_stems()` lookup, never to merge notes. Under this
   requirement, the FIRST email in a conversation creates one Thread
   note; every later email in that SAME conversation updates that same
   note (running transcript, dated entries) instead of creating a new
   file. Operator, confirming this replaces rather than adds to Emails:
   "Okay thread and Meetings" (in response to being asked whether Emails
   stays as a separate parallel section — it does not).
2. **Meetings stay their own note kind**, not folded into Threads — a
   meeting has its own shape (attendees, agenda, action items) — but
   gains a link back to whichever Thread it relates to (see `REQ-SB-56`).
3. **Manual Captures — a third evidence source, not a protected
   human-only zone.** Operator: "This is not only Agent input, sometimes
   I need to add stuff in Obsidian... The Source of info we have now is
   Emails, WebSearch, Files and Meetings, but sometimes I get info that
   is not in any of those — a word or a mouth, a quick update in an
   elevator, a quick guide from a manager." Resolved: the operator writes
   these directly into the relevant Project/Customer note, in the
   moment, into an append-only "Captures" section — same tier as a
   Thread or Meeting, feeding the exact same synthesis, not a
   personal-commentary carve-out. Routing is free for this source (no
   guess-and-approve needed) since the operator already knows what it's
   about when they write it.

**Synthesis layer (regenerated, agent-owned, machine- and human-facing) —
built on Google Cloud's Open Knowledge Format (OKF v0.2, published June
2026), not an invented schema:**
4. **Project (new note kind) and Customer (restructured, not new) are
   each a small OKF-conformant DIRECTORY, not a single file** — operator,
   choosing to adopt OKF's own reserved-filename convention literally
   rather than keep History/Captures as in-file sections:
   ```
   Work/Customers/<customer-slug>/
     index.md        — OKF reserved: directory listing (bullet links +
                        descriptions to what's inside)
     <customer-slug>.md — the OKF "concept" file itself: frontmatter
                        type: customer (OKF's one required field) +
                        title/description/tags/status/stale_after
                        (staleness signal) + generated/verified (the
                        agent-proposes/operator-approves trail, reusing
                        OKF's own actor convention — generated: {by:
                        <agent-id>, at: <timestamp>}, verified: {by:
                        human:<operator>, at: <timestamp>}) +
                        sources: [...] (provenance — which Threads/
                        Meetings/Captures this Glimpse was built from,
                        citable, not just vaguely linked). Body = Glimpse
                        (regenerated) + Background (slow-changing facts).
     log.md           — OKF reserved: History. Date-headed prose entries,
                        append-only by construction (a separate file
                        nothing ever rewrites wholesale, not just a
                        section inside one).
     captures.md       — NOT an OKF-reserved name, but the SAME "isolate
                        anything append-only/operator-owned into its own
                        file" principle, extended for the reason in
                        point 3: physically separating Captures means an
                        agent's full-file Glimpse regeneration can never
                        touch it, by construction — not just by
                        convention.
   Work/Customers/<customer-slug>/projects/<project-slug>/ — same shape,
     nested one level down, pending point 6 below.
   ```
5. **Threads and Meetings stay FLAT — NOT physically nested under a
   Customer/Project's own directory.** This isn't a new call; it's this
   vault's own already-established rule extended consistently:
   `MEMORY.md`'s standing constraint (from `REQ-SB-14`) is "Customer is
   never a folder level — only frontmatter (`customer:`) and a
   `customer/<slug>` tag... an email's customer relevance is
   multidimensional and shouldn't force one physical location." The same
   reasoning applies to Project. Threads/Meetings live in
   `Work/Threads/`/`Work/Meetings/` as already specced, cross-linked to
   their Customer/Project via frontmatter (`customer:`, `project:`) plus
   an OKF `sources` entry on the Project's own concept file — never moved
   between directories when a routing correction happens, which would
   otherwise turn a cheap frontmatter edit into an error-prone file move.
6. **RESOLVED 2026-08-16 — operator, direct confirmation:** "Yes, Project
   gets the same directory shape as Customer." Project gets the identical
   OKF-conformant four-file shape as Customer (`index.md`/`<slug>.md`/
   `log.md`/`captures.md`) — no longer a working default, a confirmed
   decision. `ESCALATIONS.md` → `ESC-037`, `Resolved`.
7. **Exactly one owner writes each concept file's Glimpse content and
   appends to `log.md`; nothing else ever touches either directly** —
   the directory split (point 4) makes part of this structurally
   enforced rather than just conventional: `log.md`/`captures.md` being
   separate files means a full-file Glimpse regeneration on the concept
   file physically cannot touch them, by construction. The remaining
   convention to enforce (mechanism belongs to `REQ-SB-57`): only one
   synthesizer ever rewrites a given concept file's own Glimpse section.
8. **Regenerate, don't patch**, for anything meant to reflect current
   state (a Thread's own top summary, a concept file's own Glimpse
   section) — read the full current evidence set and rewrite fresh,
   rather than incrementally editing old text, which drifts and
   duplicates. This also sidesteps an already-documented fragility:
   `vault_writer.py`'s `insert_body_line_if_missing` computes a fixed
   byte offset from the frontmatter's closing `---`, which is unsafe for
   a note touched many times over its life (see `MEMORY.md`) — a note
   meant to be rewritten repeatedly should read-reconstruct-overwrite in
   full, not lean on that incremental primitive at all. `log.md` and
   `captures.md` are exempt by construction (point 7) — they're never
   regenerated, only appended to.
9. **Prerequisite risk, must be verified live BEFORE this is built, not
   discovered after:** Outlook's `ConversationID` is the proposed Thread
   key, and it's already-captured data — but this codebase has TWICE
   already trusted an Outlook COM identifier that looked unique and
   wasn't (`EntryID`, then `GlobalAppointmentID` — both collapsed across
   recurring-meeting occurrences; see `MEMORY.md`, `ESC-002`/`ESC-012`).
   Before this requirement's implementation proceeds, confirm live
   (read-only, no vault writes) that `ConversationID` is genuinely stable
   within a real multi-message thread and distinct across unrelated
   threads on this Outlook installation. **Verified 2026-08-16: no false
   merging found across 41 real multi-message threads** (see
   `REQ-SB-54-US-01`'s own `## Notes` for the full result) — but this only
   tested one failure direction.
10. **`ConversationID` alone under-merges — real threads get split
    across it, not just correctly joined by it.** Operator, correcting
    point 9's own verdict directly: "The ConversationID is not the only
    link, sometimes different emails with different ConversationID are
    linked to the same thread." This is the OPPOSITE failure mode from
    point 9's own collision check (which only tested whether ONE
    `ConversationID` incorrectly spans unrelated messages) — point 10 is
    about ONE real conversation legitimately spanning MULTIPLE
    `ConversationID`s that Outlook itself never merges (e.g. a reply with
    an edited subject that trips Outlook's own conversation-split logic,
    a forward into a new recipient set, someone starting a fresh email
    about an already-discussed topic). **Resolved 2026-08-16, by scope
    split rather than by inventing a merge heuristic:** Thread stays
    EXACTLY as originally specced — one Thread note per `ConversationID`,
    nothing more, no cross-ID merge logic attempted here. Operator: "I
    guess we keep threads as is and then we will need to have an entity
    called Conversation where thread is the raw data, then we will handle
    the data in the KB later." **`Conversation` is a NEW, separate note
    kind reserved by this requirement but NOT built by it** — sits above
    Thread (Thread = raw per-`ConversationID` capture; Conversation = the
    eventual real-world grouping of one-or-more related Threads). The
    actual merge logic (what makes two Threads "the same Conversation") is
    explicitly deferred to a FUTURE requirement, to be designed against
    real captured Thread data rather than guessed in the abstract now.
    This un-blocks `REQ-SB-55`'s `Thread-Match/Merge` Job entirely — it
    can be built exactly as originally specced, joining on
    `conversation_id` alone. Until the future Conversation requirement
    ships, `REQ-SB-57`'s Project synthesizer reads evidence directly from
    Threads (per-`ConversationID`), not from any Conversation rollup.
11. **Every KB file's body opens with a one-line summary, visible without
    scrolling.** Operator: "Files now in the KB will contain a OKF
    Standard Front matter and a quick Summary in the beginning as a start
    of the file to know what's inside." OKF's own `description`
    frontmatter field already gives a one-sentence summary at the
    machine-readable level, but frontmatter is often collapsed/less
    visible at a glance in Obsidian — this is a SEPARATE, visible line at
    the top of the BODY, not a replacement for `description`. **Working
    default, not yet operator-confirmed — flag if wrong:** the first body
    line of every concept file (Thread, Meeting, Project, Customer, and
    later Conversation) is a single regenerated sentence stating current
    state at a glance, immediately followed by the rest of that file's
    own structure (transcript, Glimpse, agenda, whatever applies). For
    Project/Customer concept files this can literally BE the Glimpse's
    own opening line, not a duplicate third summary.
-->

**Acceptance:** A real multi-message Outlook conversation, captured
through the pipeline in `REQ-SB-55`, produces exactly ONE Thread note
(not one per message), whose transcript/summary/tags visibly update as
later messages in that same conversation arrive — confirmed via a real,
live capture run, not a mocked one. At least one Customer directory
exists in the OKF-conformant shape from point 4 (`index.md`,
`<slug>.md`, `log.md`, `captures.md`) with the update-ownership
boundaries in point 7 verifiably respected (a manual edit placed in
`captures.md` survives an agent-triggered Glimpse regeneration of
`<slug>.md`, by construction — separate files, not just a respected
convention). Every concept file's frontmatter validates as OKF-conformant
per point 4's field mapping (`type` present at minimum) and its body
opens with the point-11 summary line. `ConversationID` stability
(point 9) is verified live and recorded in the story's `## Notes` before
any code implementing points 1–8 is written. `Conversation` (point 10)
is reserved as a concept only — its own merge logic is explicitly out of
scope for this requirement and does not block `REQ-SB-55`'s
`Thread-Match/Merge` Job, which joins on `conversation_id` alone as
originally specced.

---

### REQ-SB-55: Email Capture & Threading Pipeline

Replaces the monolithic `email-capture` Worker
(`app/business/email_classification.py::classify_recent_emails`) with a
Pipeline of Jobs, under `ADR-041`'s Agent/Pipeline/Job/Hub model, built
on the Thread data shape from `REQ-SB-54`. **Supersedes
`REQ-SB-53-US-01`** (Email Pull/Tag/Link/Store split) — that story was
built on the pre-`ADR-041` Agent-Type model and was already parked
pending "a Pipeline Builder requirement" (`BACKLOG.md`'s own note on
`REQ-SB-53`); this requirement is that trigger.

<!-- Raised 2026-08-16, same extended discussion as `REQ-SB-54`.

**Job chain:** `Fetch` (existing Outlook pull, unchanged) → `Classify`
(existing customer/kind classification, PLUS two new outcomes: does this
belong to an existing Thread or start a new one; does this look like a
recurring/structured artifact that wants its own standing Pipeline) →
`Thread-Match/Merge` (create the Thread note on the first message of a
`conversation_id`, update — full regeneration per `REQ-SB-54` point 8 —
on every later one) → `Route-to-Project` (guess which of the matched
Customer's currently-open Projects this belongs to, or propose a NEW
Project if none fit).

**`Thread-Match/Merge` joins on `conversation_id` alone, by design, not
as an incomplete shortcut.** A real conversation CAN legitimately span
multiple `ConversationID`s (operator, 2026-08-16: "The ConversationID is
not the only link, sometimes different emails with different
ConversationID are linked to the same thread") — but resolved the same
day, by scope split rather than by building a merge heuristic into this
Job: reconciling multiple Threads into one real-world Conversation is a
NEW, separate, future requirement (`REQ-SB-54` point 10's own
`Conversation` entity), not this Job's problem. This Job's own Thread
notes stay exactly what they are — one per `ConversationID` — and a later
pass builds Conversation on top without this Job needing to change.

**Two branch Jobs:**
- `Summarize-Attachment` — each attachment gets its own summarized,
  dated sub-entry appended to the Thread's body, kept separate from the
  regenerated top-level summary so attachment content isn't lossily
  compressed into one paragraph.
- `Detect-Recurring-Pattern` — operator: "sometimes I get an Email that
  contains the pipeline or consumption of a customer, I need to take
  that email and start a pipeline for it... I am trying to build a
  reusable system here, not just a one-time code." When this Job fires,
  it does NOT do the recurring work itself — it proposes a NEW standing
  Pipeline, seeded from the triggering email, pre-filling the EXISTING
  Agent Creation Wizard (`REQ-SB-37`) rather than inventing new
  infrastructure. Detection must be general (structural/pattern-based —
  "does this look like a recurring, structured artifact" — not a
  hardcoded rule for one customer's consumption-report format), so the
  SAME mechanism catches invoices, weekly exports, or anything else
  structured and repeating in the future, per the operator's own
  reusability framing.

**Approval gating — confirmed directly:**
- Thread → Project routing (or new-Project proposal): operator, asked
  whether the agent should decide or ask — "Agent Guess and it Goes to
  my Approve list."
- New-Pipeline proposal from `Detect-Recurring-Pattern`: operator, asked
  the same question at the bigger-stakes level — "Agent detected, but
  let me approve before it builds." Both route through the EXISTING
  Pending Approvals surface (`agent_pending_approvals.json`,
  My Day → Approvals) — no new approval mechanism, reuse what exists.
- Once a Thread's Project placement is approved, later replies in that
  SAME conversation are NOT re-routed or re-approved — they're just an
  update to the already-placed Thread note (per `REQ-SB-54` point 1).
  The approve list scales with new things happening, not with email
  volume.

**Tags:** unioned onto the Thread's frontmatter on every update, never
overwritten or pruned in v1 (per `REQ-SB-54`'s general regenerate-vs-
append split — tags follow the "accumulate" side, same as Customer's
Glimpse follows "regenerate").

**Explicitly out of scope for this requirement:** the actual build of
whatever new Pipeline `Detect-Recurring-Pattern` proposes — that's a
new, separate Pipeline created (with operator approval) through the
existing wizard at RUNTIME, not something this requirement's own
implementation needs to anticipate the shape of.
-->

**Acceptance:** A real live Outlook capture run demonstrates: (a) two
messages in the same real conversation produce ONE Thread note with a
visibly-updated transcript and regenerated summary, not two notes; (b)
an attachment on one of those messages appears as its own dated,
summarized sub-entry; (c) the Thread's Project placement appears as a
Pending Approval item, not an auto-committed write, and a second
message in the same conversation does NOT produce a second approval
item; (d) a deliberately structured/repeating test email trips
`Detect-Recurring-Pattern` and produces a Pending Approval proposing a
new Pipeline, pre-filled into the Agent Creation Wizard, not built
automatically. `email-capture` no longer exists as a separate
`agent_registry` entry once this pipeline ships; `REQ-SB-53-US-01` is
marked superseded, not reworked.

---

### REQ-SB-56: Meeting Capture & Thread Linking

Extends the existing `meeting-capture` Worker with a `Link-to-Thread`
Job, so a meeting that's genuinely part of an email conversation shows
up connected to it, instead of as an unrelated island. **Supersedes
`REQ-SB-53-US-02`** (Meeting Pull/Tag/Link/Store split), same reasoning
as `REQ-SB-55`'s relationship to `REQ-SB-53-US-01`. `REQ-SB-53-US-03`
(To-Do) is NOT covered by this batch — it was not part of this
discussion and stays parked.

<!-- Raised 2026-08-16, same discussion as `REQ-SB-54`/`REQ-SB-55`.

**Linking strategy, in priority order:**
1. **`conversation_id` match, if available.** A meeting invite sent
   inside an email thread may itself carry that thread's
   `ConversationID` as an Outlook item. If so, linking is free — same
   join as everything else in `REQ-SB-54`/`REQ-SB-55`, no separate
   matching logic. **Unconfirmed, flag for the architect:** does this
   codebase's meeting-capture COM read (distinct from the email read in
   `outlook_com.py`) actually expose `ConversationID` on meeting/
   appointment items? Not yet checked — verify live before relying on
   it, same spirit as `REQ-SB-54` point 9's verification requirement.
2. **Attendee-overlap + date-range-proximity heuristic, as fallback** —
   for meetings created directly (not as a reply within a conversation),
   which structurally can't share a `conversation_id` with anything.
   Exact overlap/proximity thresholds left to the architect/decomposer
   to propose; this is a genuine judgement call the operator did not
   pin down numerically during discussion — flag rather than guess a
   specific threshold silently.

Once linked, the meeting shows up as evidence feeding the same Project
Glimpse the linked Thread feeds (see `REQ-SB-57`) — this requirement
only covers the linking itself, not the synthesis that reads it.
-->

**Acceptance:** A real meeting invite sent as a reply within an existing
captured email Thread ends up linked to that Thread's note (verified via
whichever of the two strategies above actually applies once point 1 is
checked live). A meeting with no email-thread origin at all still gets a
best-effort link via the fallback heuristic, or is left explicitly
unlinked rather than mis-linked — false-positive links are worse than no
link, given they'd corrupt a Project's own Glimpse. `meeting-capture`'s
existing fetch behavior is unchanged; only the new Job is added.
`REQ-SB-53-US-02` is marked superseded, not reworked.

---

### REQ-SB-57: Project & Customer Status Synthesizer Agents

Builds the two Producer agents that actually keep `REQ-SB-54`'s Glimpse/
History sections current — the piece that turns "a nicely structured
file" into "a file that's actually trustworthy," per the operator's own
complaint about the existing Customer notes: "no one update this file."

<!-- Raised 2026-08-16, same discussion. UPDATED 2026-08-16 (same day) for
`REQ-SB-54`'s adoption of OKF's own directory shape (point 4) — "Glimpse"
and "History" are no longer sections inside one file; they're the
concept file's own body vs. a separate `log.md`.

**Project Synthesizer** — triggered whenever evidence changes under a
Project (a linked Thread updates, a Meeting links in, the operator adds
a Capture — NOT on a fixed schedule). Rewrites that Project's own
`<project-slug>.md` concept-file Glimpse content in full
(`REQ-SB-54` point 8); appends a dated entry to that Project's own
`log.md` only when something concludes, per whatever bar `REQ-SB-56`/
`REQ-SB-54` point 5 settles on.

**Customer Synthesizer** — same mechanism, one level up: triggered
whenever a Project underneath a Customer changes. Rewrites the
Customer's own concept-file Glimpse as a rollup (one line per active
Project — this is the "by one doc get an idea about what happened"
surface the operator asked for); appends a dated entry to the Customer's
own `log.md` when a Project concludes; separately proposes Background
amendments (still in the concept file's own body, not a reserved OKF
filename) through Pending Approvals when it detects a new durable fact
(distinct trigger from routine Glimpse regeneration — a permanent claim
about the customer is a bigger deal than routine status noise,
operator's own reasoning for gating new-Project proposals extends here
too).

**Ownership enforcement (this is where `REQ-SB-54` point 7 actually gets
built):** `log.md`/`captures.md` being separate files already makes part
of this structurally impossible to violate — a full-file Glimpse
rewrite on the concept file physically cannot touch them. The remaining
convention to enforce: no other Job or Agent in this batch writes to a
concept file's own Glimpse content directly — a Thread update TRIGGERS
Project resynthesis, it doesn't perform it; a Project update TRIGGERS
Customer resynthesis, same rule. This is what prevents two agents racing
to rewrite the same concept file when, e.g., a Thread update and a
Meeting link-in happen close together.

Whether "Project Synthesizer" and "Customer Synthesizer" are two
distinct Agent identities or one generalized synthesizer Job
parameterized by scope (Project vs. Customer) is an implementation
choice for the architect — the operator's own design conversation
treated them as the same mechanism applied at two levels, not two
independently-designed things.
-->

**Acceptance:** A real Thread update (new message captured under
`REQ-SB-55`) triggers a visible Glimpse rewrite on its linked Project
within the same pipeline run, without any other Job having written to
that section directly. When a Project's status is set to concluded (test
hook or manual trigger, however the architect designs the conclusion
signal), a new dated line appears in its Customer's History and the
Customer's Glimpse drops that Project from its active rollup — both in
the same synthesis pass. A deliberately-introduced new durable fact
about a test customer produces a Pending Approval proposing a Background
amendment, not a silent rewrite.

---

### REQ-SB-58: Customer/Project-Aware Expert (Glimpse-First Answers)

Extends the existing `vault-qa` Expert agent so a status question is
answered from the relevant Customer/Project's Glimpse first, rather than
a generic vault search re-synthesizing an answer from scratch every
time — the chat-facing half of "the KB is for me and my Agents to put
data and pull data" (`REQ-SB-54` point 4).

<!-- Raised 2026-08-16, same discussion — smaller in scope than the other
five requirements in this batch, kept separate because it's a distinct
behavioral change to an existing agent, not new data-model or pipeline
work.

When a question resolves to a specific Customer or Project (via existing
name/entity matching this app's search already does), `vault-qa` should
read that note's Glimpse (and Background, for older/durable questions)
FIRST, and only fall back to searching raw Thread/Meeting evidence when
the operator asks for detail a Glimpse wouldn't carry, or for a citation
back to the original source. This is an extension of `vault-qa`'s
existing behavior, not a new Agent.
-->

**Acceptance:** Asking `vault-qa` "what's the status of \<test
customer\>" returns an answer sourced from that Customer's Glimpse
(verified by checking the answer reflects a deliberately-edited Glimpse
value, not a re-derived one), answers in materially less time/tool-calls
than a full vault search over that customer's raw Threads, and a
follow-up "show me the original email" still successfully drills into
the underlying Thread evidence on request.

---

### REQ-SB-59: Full Vault Migration to the New Knowledge Model

One-time backfill: wipe `Work/Emails/` and any stale cross-links it
produced, then fully re-run capture over Outlook history through the
pipelines built in `REQ-SB-55`/`REQ-SB-56`, populating Threads/Meetings/
Projects/Customers under the new model from scratch. Depends on
`REQ-SB-54` through `REQ-SB-58` all being `Done` first — this is
integration work, not something that can run against a partial pipeline.

<!-- Raised 2026-08-16, same discussion. Operator explicitly authorized
data loss/rewrite: "I am okay with rewriting the data." Resolved
directly: wipe-then-recapture, not a parallel run compared/diffed before
cutover — reasoning confirmed with the operator: Outlook remains the
real source of truth (nothing is destroyed at the source), and a
parallel-run/diff approach adds real complexity for a single-user vault
where the cost of "wrong" is cheap (re-run capture again), so the
simpler approach was preferred over the more defensive one.
-->

**Acceptance:** After this requirement ships, `Work/Emails/` (or its
replacement `Work/Threads/`) contains zero notes predating this
migration's own run, every Customer note under `Work/Customers/` has
been regenerated with the new Background/History/Glimpse/Captures shape
(pre-migration content preserved into Background/History where it
represents durable facts or concluded items, not silently discarded),
and a spot-check against 3 real, previously-known multi-message
conversations confirms each now exists as exactly one Thread note with
a correct, complete transcript.

---

### REQ-SB-63: The Librarian — Vault Expert as the Central Placement/Restructuring/Enrichment Authority for the New KB Pipelines

Generalize the already-shipped Vault Filing Expert (`ADR-021`,
`vault_filing_expert.determine_placement_and_file`) from a single-input-channel
placement tool (today: only chat-uploaded attachments) into the consulted
authority every `REQ-SB-55`/`56`/`57`/`58` pipeline Job routes a KB-shaping
decision through, rather than each pipeline growing its own separate,
divergent routing/cross-reference logic. Concretely, this Agent already:
understands the live vault structure (`known_kinds`/`known_customers`/
`known_partners`, read fresh, never hardcoded); decides Tier 1 (fits an
existing category — write immediately) vs. Tier 2 (a genuinely new top-level
area — routes to a real Pending Approval); and mechanically links/creates the
referenced Customer/Partner hub note. This requirement extends that same
Agent (never a second, divergent implementation) to also decide the
genuinely new case the current single-purpose version doesn't handle: content
whose arrival implies a cross-cutting update elsewhere in the KB (e.g. "this
Thread also means Customer X's Glimpse needs regenerating"), triggering
`REQ-SB-57`'s synthesizer rather than only ever producing one new note.

<!-- Raised 2026-08-16, same day as SPRINT-048's close. Operator's own
reasoning, verbatim intent: "If we have a vault expert then a pipeline of
Threads starts, prepares everything, then gives it to the vault — the
[expert] understands the vault structure, decides yes this is a Thread
stored in that structure, maybe this is also customer info I will need to
add there, etc. This will help the vault be always organized under one
master (call him the Librarian), and the vault will be asking for approval
of stuff if it needs my validation." Investigated before writing this
requirement: `vault_filing_expert.py` already IS almost exactly this
today, just scoped to one caller (attachment review) — this requirement is
a genuine generalization of proven, shipped code, not a from-scratch
concept, and its Tier-2 pending-approval mechanism is exactly the
"ask for approval" behavior the operator described, already built.

Two open scope questions deliberately left for `/spec`, not assumed here:
(1) **Retrofit scope** — does "one master" mean the Librarian becomes the
funnel for `REQ-SB-55` onward ONLY (additive, matching this whole KB
redesign's own established non-retrofit pattern — `REQ-SB-54` didn't touch
existing data either), or does it also retrofit the already-`Done`,
already-shipped Email/Meeting/Task/People capture pipelines
(`REQ-SB-08`/`09`/`10`) to route through it too? These currently write
directly via their own classification modules, never through the Filing
Expert — retrofitting them is a materially larger, riskier blast radius
than extending net-new pipelines. (2) **Trigger mechanism for the new
cross-cutting-update case** — does the Librarian call `REQ-SB-57`'s
synthesizer directly (a new Agent-to-Agent call), or does it create a
Pending Approval/proposal the same way Tier 2 already does, letting the
existing approval surface be the one place all "the vault wants to change
something beyond the obvious new note" decisions surface? -->

**Acceptance:** Not yet specced in full Gherkin — this requirement is real
(not deferred) and ready for `/spec`, which must resolve both open scope
questions above rather than assume a default. At minimum: a Job in
`REQ-SB-55`'s Thread pipeline can consult the Librarian mid-flow (mirroring
`ADR-041`'s own "branch to consult an Expert" pattern) and receive a real
placement decision grounded in the live vault structure; a decision that
implies a cross-cutting update elsewhere surfaces as a real, human-visible
event (either a direct trigger or a Pending Approval, per whichever design
`/spec` resolves) rather than being silently dropped or silently applied
with no trace.

---

### REQ-SB-64: Section Hub as KB Traffic Gateway — Every Pipeline/Agent Write Routes Through Its Section's Manager

Extends `REQ-SB-20`'s already-shipped Hub concept (today: a per-Section
manager that knows its own agents/experts and routes cross-Section HELP
requests — `graph.py::_route_hub_request`) to also mediate ALL KB-bound
traffic — not just agent-to-agent help requests — from that Section's own
agents and pipelines. Every Section gets a real Hub that its own agents'
and pipelines' KB reads/writes route through, rather than each agent
calling `vault_writer.py` directly as they all do today. The Hub does not
itself decide WHERE content ultimately belongs in the KB — for the actual
placement/tag/location decision, the Hub consults `REQ-SB-63`'s Librarian,
the one shared authority that knows the whole KB (every Section, every
tag, every storage location). Hub = per-Section traffic gateway; Librarian
= the shared placement brain a Hub calls into. Not competing designs — a
Hub may, in the future, also enrich the traffic passing through it with
extra Section-specific context before or after that Librarian consult.

<!-- Raised 2026-08-16, same day as SPRINT-049's build. Operator, when
asked to clarify how this related to REQ-SB-63: "There is no Agent to
Agent Communication between different Sections, that's why we have Hubs
to know which Agents or Experts are in that Section. All traffic that is
going to the KB from the pipeline and Agents goes through that Manager
(maybe in future it will add some extra data). The Librarian is the one
that knows about the KB, the Sections inside, the tags and where to store
new info." Operator's own framing: "not a new requirement" — `ADR-041`
already defines Hub as "a Section's own manager... AND database," this
requirement is the first time that database/gateway half is actually
built, not a new architectural concept.

**Explicitly deferred, by direct operator decision, until `SPRINT-049`
(`REQ-SB-55`) and `SPRINT-050` (`REQ-SB-63`) both ship:** asked whether
the in-flight Email Capture pipeline (T07/T08 still outstanding at the
time this was raised, `ADR-043`'s direct-vault-write shape) should be
redesigned now to route through the Hub, the operator chose "Finish
SPRINT-049 as-is, add Hub-routing after" — avoiding reverting real,
already-verified work over a mid-build architecture change. This
requirement builds ON TOP of the pipeline once it exists, not underneath
it retroactively at this moment.

Genuinely open, not decided here: whether this retrofits the pipeline
`REQ-SB-55`/`REQ-SB-63` will have already shipped by the time this is
spec'd (routing their already-working direct calls through the Hub after
the fact) versus only applying to whatever comes after — given this
whole KB redesign's own established "no retrofit, replace with pipeline"
precedent (`REQ-SB-63`'s own resolved scope question), retrofitting
`REQ-SB-55`'s pipeline is NOT assumed here and must be resolved at
`/spec` time, not guessed. Also open: the exact mechanical shape of "all
traffic routes through the Hub" (a real synchronous call every write
passes through? a decorator/interceptor pattern? something else), and
what "extra data" a Hub might add to passing traffic, since the operator
named that as a possible future addition, not a resolved current one.

**Concrete worked example, confirmed by the operator the same day:** "The
[Email Capture] Pipeline in Data Gathering [Section] is connected to the
Data Gathering Hub, which sends it to the Librarian for filing." This is
the reference call chain `/spec` should design against: `REQ-SB-55`'s
pipeline (assigned to the `Data Gathering` Section, alongside
`meeting-capture`) → that Section's own Hub → `REQ-SB-63`'s Librarian for
the actual filing/placement decision. Doesn't change the sequencing
decision above (still waits for `SPRINT-049`/`050`) — recorded here so
the eventual `/spec` pass has a real, concrete example to design the
general mechanism against, not just the abstract principle. -->

**Acceptance:** Not yet specced — this requirement is real (not a
placeholder like `REQ-SB-60`/`61`/`62`) but is sequenced to wait for
`REQ-SB-55`/`REQ-SB-63` to ship first. Do not `/spec` until both
`SPRINT-049` and `SPRINT-050` are `Done`.

---

### REQ-SB-65: Pipeline Job Visualization — the Email Capture Pipeline's Real, Running Internals Rendered as a Tree on the Agents Map

Render `REQ-SB-55`'s real, running Email Capture Pipeline as a connected
tree of its own Jobs (`Classify`, `Thread-Match/Merge`, `Route-to-Project`,
`Summarize-Attachment`, `Detect-Recurring-Pattern`) on the Agents Map,
instead of the single opaque `email-capture-pipeline` node it renders as
today. The shape to build toward already exists as sample data —
`GET /demo/agents`/`GET /demo/pipelines` (`app/api/demo_taxonomy_router.py`,
already mounted on the real backend, `ADR-041`'s own taxonomy fixture) —
and the frontend's tree/dependency-edge layout math
(`layoutAgents.ts::assignTreeAngles`/`buildDependencyEdges`) already exists
too, built specifically for this. Neither has ever been connected to real
data: the demo endpoints have zero frontend consumers, and `layoutAgents.ts`
has only ever been fed a flat `Agent` list with an always-empty
`depends_on`.

<!-- Raised 2026-08-16, same day `SPRINT-049`/`SPRINT-050` shipped, once
the operator started visually validating the real pipeline against the
demo taxonomy's own tree rendering. Operator: "In the Demo API we have a
Pipeline where Agents are connected in a Tree. That is what Depends on
was about in Agents" — confirming `AgentSummary.depends_on`/
`branch_target_agent_id` (typed since `REQ-SB-38`'s own 2026-08-15 work,
"Check Langraph Data... so we can start having a tree view") were always
meant for exactly this, not a coincidence.

**This reopens a decision made earlier the same day.** `ADR-043`
deliberately kept Email Capture's 6 Jobs invisible — one Agent-tier
identity only, no per-Job registry entry, no per-Job Map node — reasoning
that mechanical pipeline verbs are Job-tier, never Agent-tier, per
`ADR-041`. This requirement does not necessarily overturn that: showing
Jobs as tree nodes on the map does not require giving each Job a real,
independently-addressable Agent identity (its own chat/history/Working
Mode) — it only requires a real DATA SOURCE describing the compiled
pipeline's own structure (which Job depends on which), which `/spec`'s
own architect pass must design without assuming either (a) a new
`GET /pipelines`-shaped endpoint that inspects the real, compiled
`email_capture_pipeline.py` `StateGraph` and returns its node/edge shape
read-only (Jobs stay non-addressable, `ADR-043` intact), or (b) giving
each Job a genuine lightweight registry entry after all (revisits
`ADR-043` for real). Do not assume either — this is squarely an
architect-level decision, not something to guess at `/spec` time.

Scope-narrowing precedent worth following: this project's own
established "prove one real thing before generalizing" sequencing
(`ADR-041`'s own Pipeline-Builder-after-one-real-Pipeline rule) suggests
scoping this to Email Capture's own pipeline specifically, not a general
"any Pipeline renders as a tree" platform — the demo taxonomy's 150+
generated sample pipelines exist for UI density testing, not as a
requirement that every one of them needs a real backend counterpart. -->

**Acceptance:** Not yet specced — this requirement is real (not
deferred). At minimum: the Agents Map, viewing the `Data Gathering`
Section, shows the Email Capture Pipeline's own real Jobs as connected
tree nodes reflecting the actual compiled graph's structure (fork/merge/
branch shape, per `ADR-043`), not a single opaque node — grounded in the
real, running pipeline, never fabricated or hardcoded to match the demo
sample's own shape.

---

### REQ-SB-66: Real, Editable Per-Agent/Job Prompt + a Guardrails Placeholder in Settings

Two additions to every Agent's/Job's own Settings surface:

1. **A real, stored, editable Prompt.** Today every prompt in this
   codebase is hardcoded in Python (`compass_client.py`'s various
   `classify_*` functions, `vault_filing_methodology.py`'s placement
   prompt, `agent_chat.py`'s Expert system prompt) — there is no place to
   view or edit one anywhere in the app. This requirement makes "the
   prompt that runs this Agent/Job" a real, persisted, per-Agent/Job
   value, visible and editable from Settings, that the real call site
   actually reads at run time (not just a UI field that does nothing).
2. **A Guardrails placeholder.** A real field/section in Settings,
   present now, with NO defined behavior or enforcement yet — reserving
   the interface slot rather than the mechanism. What "guardrails" ends
   up meaning (the honest-uncertainty grounding instruction made
   editable, behavioral/content limits, confidence thresholds, or
   something else) is explicitly undecided; this requirement does not
   pick one.

This also reopens, deliberately, a decision `REQ-SB-65` made the same
week: Jobs (Pipeline-tier, `ADR-041`/`ADR-043`) were kept "fully
non-addressable — no new CSS class, no new visual affordance, no
click-to-open-detail behavior." Jobs still get no Chat, no History, no
Working Mode of their own (that stays the Pipeline's own concern, via
Pending Approvals) — but they DO need a Settings-only view for Prompt and
the Guardrails placeholder, since that's what this requirement asks to
manage. Real Agents (Worker/Producer/Expert) keep their existing
Overview/Chat/History/Settings shape; only the Settings tab's own content
changes here.

<!-- Raised 2026-08-16, same day REQ-SB-65 shipped, once the operator
started thinking through "different views per agent type." Operator's own
framing: "Jobs we don't need to chat with, I need to have the prompt that
runs the agent to be in the Settings so I can manage it later, the
guardrails — I want you to think what do we need to have per Agent Views
and Settings." Asked directly what "guardrails" should cover: "I still
don't know but we are building a placeholder" — confirmed explicitly as
structure-only, not content-defined, mirroring this project's own
established "structure only, no ingestion/agent code yet" precedent
(`MEMORY.md`, 2026-08-10, `Work/Pipeline`/`Agreements`/`Consumption`).

**RESOLVED 2026-08-16, same day, follow-up discussion, all three
operator-confirmed:**
- **Per-type Settings differences:** NOT a separate screen layout per
  Type — the existing model (one Settings tab, fields conditionally shown
  per Type, exactly like today's Domain-for-Expert/Purpose-for-Producer)
  stays as-is. Prompt and Guardrails are added to every Type's own
  Settings, including Jobs. A Job's own Settings ends up genuinely
  minimal — Prompt + Guardrails only, since it has no Vault Scope, no
  independent Working Mode, no Schedule, and no Skills grant of its own.
- **Prompt storage shape:** a new sibling `.second-brain/agent_prompts.json`
  keyed by id, composed alongside `agent_registry.py` (never inside it),
  mirroring this codebase's own repeated established pattern
  (`agent_keywords.json`/`agent_scopes.json`/`agent_schedules.json`,
  `ADR-011`'s "identity stays hardcoded, mutable state lives separately"
  rule). The same id-keyed shape covers both real Agents and Jobs
  uniformly — Jobs have no `agent_registry.py` entry to attach to, but a
  sibling file needs no such entry, just an id string.
- **Default-fallback behavior:** additive layering. An unset Prompt
  override falls back to today's existing hardcoded default, unchanged —
  never a forced, day-one rewrite of every existing prompt. Mirrors the
  self-healing-default pattern already used by `working_mode_registry.py`/
  `background_agent_registry.py`.
-->

**Acceptance:** Not yet specced in full Gherkin, but all three of this
requirement's own open design questions are now resolved above — ready
for `/spec` to write real Acceptance Criteria against them, not guess.
At minimum: every Agent and every Job has a real, persisted Prompt value
(stored in `agent_prompts.json`, additive over the existing hardcoded
default) editable from its own Settings surface, and the real runtime
call site for that Agent/Job reads the stored value; a Guardrails
field/section is present in the same Settings surface for every
Agent/Job with no enforcement behavior required yet; a Job's own detail
view is reachable (reopening `REQ-SB-65`'s "no click-to-open-detail"
default on purpose) but shows only Prompt/Guardrails Settings — never a
Chat or History tab.

---

### REQ-SB-67: Real Per-Thread Summary Synthesis + Existing-Thread Backfill

Extends `REQ-SB-55-US-01`'s `Thread-Match/Merge` Job (`Done`) to replace
its own deliberately-raw `## Summary` region (today: the latest
message's own unprocessed body, pasted in verbatim —
`REQ-SB-55-US-01`'s own T03 Implementation Log/docstring: "this Job
never makes a second Compass call... not an AI-synthesized abstract")
with a real, Compass-generated synthesis of that Thread's own current
state, grounded in its own transcript — plus adds `REQ-SB-54` point 11's
own one-line "current state at a glance" opening sentence to the
Thread's body, never actually built for Threads. Also builds a one-time,
narrowly-scoped backfill: regenerate Summary + opening line for every
Thread note already in the vault, in place — distinct from `REQ-SB-59`'s
much larger full wipe-and-recapture (which stays blocked on `REQ-SB-54`
through `REQ-SB-58` all shipping); this backfill touches only the
Summary/opening-line content of already-existing Thread notes, leaves
frontmatter/transcript/attachments/tags untouched, and does not depend
on `REQ-SB-56`/`57`/`58`.

<!-- Raised 2026-08-17, operator noticed real captured Thread notes show
empty/raw content instead of a real summary or description. Investigated
live against real vault data (`Work/Threads/*.md`) and the real
`thread_match_merge` code: confirmed the raw-dump behavior is
`REQ-SB-55-US-01`'s own deliberate, documented Constraint (deferring
real synthesis to `REQ-SB-57`'s future scope) — but `REQ-SB-57` (Project
& Customer Status Synthesizer) never actually touches a Thread's OWN
Summary section; it only synthesizes Project/Customer Glimpse FROM
Thread evidence one level up. Surfaced this gap directly to the operator
before building anything (two `AskUserQuestion` rounds): operator
confirmed (1) fix Threads' own Summary now, in addition to still
pursuing `REQ-SB-57` later for Project/Customer status, and (2) backfill
already-captured Threads, not just new ones going forward.

This requirement DELIBERATELY REOPENS one Constraint from the already-
`Done` `REQ-SB-55-US-01` story ("this Job never makes a second Compass
call") — a scope decision that made sense when written (avoid an
unbounded per-message API-cost multiplier) but the operator has now
confirmed the real synthesized summary is worth that cost. Superseding a
Done story's own Constraint via a new requirement (rather than silently
reopening/re-editing the Done story) mirrors this project's own
established precedent (`REQ-SB-65`/`REQ-SB-66` both deliberately
reopened `REQ-SB-41`'s "Jobs are non-addressable" decision the same
way).

Two open scope questions deliberately left for `/spec`, not assumed
here: (1) **Regeneration trigger for the backfill** — a one-shot
script/endpoint the operator runs once, vs. a lazy background job that
catches up existing Threads over time; (2) **Cost/rate-limiting** — the
vault currently holds a small number of real Threads (2 as of this
writing, expected to grow once `REQ-SB-59`'s eventual full recapture
runs), so a naive one-Compass-call-per-Thread backfill is cheap today
but the design should not hardcode an assumption that stays true
forever. -->

**Acceptance:** Not yet specced in full Gherkin — ready for `/spec`. At
minimum: a real, live-captured Thread (new message via the real Outlook
pipeline) produces a genuinely synthesized `## Summary` (not the latest
message's raw body) grounded in that Thread's own transcript, plus a
one-line opening sentence at the top of the body; running the backfill
over the vault's existing Thread notes updates each one's Summary/
opening line in place, verified live against the real, already-captured
Threads, with frontmatter/transcript/attachments left untouched.

---

### REQ-SB-68: Async Capture Jobs + Real-Time Job/Scheduling Monitor

Two tightly-coupled fixes to the same underlying gap:

1. **Fix `run_capture_now`'s blocking bug.** The manual "Run Capture Now"
   action (`POST /agents/{agent_id}/actions/{action_id}` →
   `agents_router.py::_execute_action`) calls its handler directly on the
   asyncio event loop, blocking the ENTIRE backend — not just that one
   request — for the full duration of the run. Confirmed live
   2026-08-17: a manually-triggered capture run made `GET /agents` (and
   every other endpoint) unreachable for several minutes.
   `capture_scheduler.py`'s own scheduled ticks already avoid this exact
   bug via `asyncio.to_thread` — a prior, already-documented 2026-08-14
   bugfix applied to the app-start trigger (see `BUGS.md`) — but the
   manual-trigger path never received the same fix. This requirement
   applies it there too.
2. **A real Job/Scheduling monitor.** Today there is no visibility into
   whether a backend capture job is currently running, how long it has
   been running, or whether its last run errored.
   `.second-brain/last_capture_run.json` only records a bare
   `finished_at` timestamp; `GET /agents/{id}/history` only logs simple
   post-hoc text lines ("Capture run completed — N email(s) filed") with
   no duration or error detail, and nothing at all while a run is still
   in flight. This requirement adds real, persisted run-state tracking
   (started-at, still-running flag, duration once finished, success/
   error outcome with the real error message on failure) for backend
   jobs dispatched through the existing shared-lock/action-dispatch
   mechanisms, surfaced as a new "Scheduling" view under the existing
   System Health page (`REQ-SB-31`, `SystemHealthPage.tsx`).

<!-- Raised 2026-08-17, operator-directed, immediately following a live
incident: manually triggering `run_capture_now` to double-check a low
real-Thread count caused the whole backend to become unresponsive for
several minutes, with zero visibility into what was actually happening
(running? stuck? errored?) from either the API or the UI while it
happened. Both halves of this requirement trace directly back to that
one incident.

Two open scope questions deliberately left for `/spec`, not assumed
here: (1) **Which jobs does the new run-state tracking cover?** — every
dispatched agent action generally (any Worker/Producer capability), or
scoped specifically to the jobs `capture_scheduler.py`'s own shared
dispatch lock already covers today (`email-capture-pipeline`,
`meeting-capture`, `todo-capture`) — the ones actually exposed to the
blocking bug and the ones the operator's own complaint was about; (2)
**Static or live-updating duration?** — whether "how long" means a
duration shown only once a run finishes, or a live-updating elapsed-time
display while a run is still in progress (implying either polling or a
push mechanism on the new Scheduling view). -->

**Acceptance:** A real, manually-triggered `run_capture_now` call no
longer blocks any other endpoint — verified live by hitting `GET
/agents` (or any other route) WHILE a real capture run is genuinely in
progress and confirming it responds normally, not only after the
capture finishes. The new Scheduling view shows, for each covered job:
whether it is currently running, how long the current (or most recent)
run has taken/took, and its last outcome (success, or the real error
message if it failed) — verified against a real live run in each state
(idle, running, succeeded, and a deliberately-induced failure).

---

### REQ-SB-69: Decoupled Email Pull + Human-Readable, Graph-Connected Thread Notes

Two problems, one requirement, because the second is only worth doing once the
first stops the pipeline from randomly wedging mid-work:

1. **Decouple pulling mail from Outlook out of the Classify/Thread/Route
   pipeline entirely.** Today, `run_email_capture_pipeline`'s very first line
   makes ONE synchronous call — `outlook_com.list_recent_mail(limit)` — that
   connects to Outlook COM, sorts the inbox, and iterates every candidate item
   resolving sender/attachments/recipients per item, all before the rest of
   the pipeline (Classify → Thread-Match/Merge → Route-to-Project, none of
   which touch Outlook at all) ever runs. This single call holds the shared
   Outlook-COM dispatch lock (`REQ-SB-45`) for its entire duration. If
   anything about that one call stalls — Outlook's own Object Model Guard
   security prompt going unanswered, a slow/large mailbox enumeration, or any
   other COM-level hang — the WHOLE tick wedges: no email gets classified, no
   Thread gets updated, and the shared lock blocks every other job that needs
   it too, for as long as the stall lasts (confirmed live, repeatedly, on
   2026-08-17 — including one 20+ minute hang and a second, separate hang the
   same night after a supposedly-unlimited Outlook access grant, ruling out
   "the 10-minute grant lapsed" as the sole explanation). Going forward, the
   Outlook pull becomes its own independent step that fetches raw email
   content and writes it to a durable vault-local staging area, then is DONE
   with Outlook — nothing downstream of it ever calls into Outlook COM again.
   Classify, Thread-Match/Merge, Route-to-Project, attachment summarization,
   and thread-summary synthesis all read from that staged content instead. A
   stall in the Outlook pull no longer blocks already-staged mail from being
   processed, and a stall in Compass/vault processing no longer blocks the
   next pull from running.
2. **Thread notes read like a human wrote them, not like a database dumped
   them**, once they're being rebuilt around the staged content anyway:
   - **Filename.** A Thread note's filename is today its raw
     `conversation_id` (an opaque GUID, e.g.
     `01D26A7530444A23803A002210620160.md`). It becomes the Thread's last
     message date, human-readable, plus the conversation's own subject/name —
     collision-safe (two Threads landing on the same date+name get
     disambiguated, never silently overwrite each other).
   - **Dates.** Every date a human actually reads on a Thread note (frontmatter
     `last_message_at`, the Transcript's per-message timestamps) renders
     human-readable (e.g. "Aug 16, 2026, 1:02 PM"), not a raw machine
     timestamp (`2026-08-16 13:02:57.246000+00:00`). Any date field other,
     already-shipped code actually parses/sorts/compares programmatically may
     keep a machine-parseable form alongside — this requirement is about what
     a human reads, not about breaking existing sort/dedup logic; the exact
     split is an implementation decision, not a product one.
   - **Obsidian graph connectivity.** Thread notes gain real `[[wikilinks]]`
     to the Customer/Person/Project notes they actually relate to, so the
     vault's existing Obsidian graph view actually shows a Thread connected to
     the entities it's about — using Obsidian's own linking convention this
     vault already relies on elsewhere (`REQ-SB-02`, `REQ-SB-14`), not a new
     mechanism.

<!-- Raised 2026-08-17, operator-directed, immediately following the second
real Outlook-COM hang incident of the night (the first is REQ-SB-68's own
raised-comment; this is a second, separate recurrence after that requirement
had already shipped its non-blocking-dispatch fix — proving REQ-SB-68's fix
was necessary but not sufficient, because the actual stall lives one layer
deeper, inside Fetch's own single monolithic Outlook call, not in how that
call gets dispatched onto the event loop). The operator's own words: "Here is
my Approach, Have one Agent to Hand the pull of All Emails Separately And
then we will have a pipeline to Summarize the Files and Emails from the Vault
instead of outlook." Also folds in 3 real, disclosed content-quality asks
raised in the same breath, since they touch the same Thread-writing code path
this restructuring already has to touch: human-readable filenames (date +
name, not a GUID), human-readable dates, and real Obsidian wikilinks/mentions
so the vault's own graph view actually connects Threads to what they're
about. The operator explicitly granted full autonomy for this requirement
end-to-end ("You are in full control to make the best out of this Sprint and
You will not be able to know what is blocking us") — open implementation
questions (staging-store format/location, exact filename-collision scheme,
which date fields stay machine-parseable, which entities a Thread wikilinks
to) are resolved directly by the pipeline rather than left flagged for a
human answer that will not be available; each such call is disclosed with
its reasoning in the story/architecture artifacts it lands in, per this
project's own established MUST-FLAG discipline. -->

**Acceptance:** A real, live-triggered email pull populates the vault staging
area without the Classify/Thread/Route pipeline ever calling
`outlook_com.*` directly — verified by confirming those code paths no longer
import `outlook_com` at all. A deliberately-slow or stalled pull no longer
prevents already-staged mail from being classified, threaded, and filed in
the same or a later run — verified live. A newly created or updated real
Thread note's filename is its human-readable last-message date plus its
conversation name (never a bare GUID), its human-visible dates render
human-readable, and it carries at least one real `[[wikilink]]` to a
Customer/Person/Project note it actually relates to — all verified against
real, live-captured Threads, not fixtures.

---

### REQ-SB-70: Vault Base Provisioning API — Fresh PARA/OKF Skeleton

A one-time (but safely re-runnable/idempotent), operator-triggered API that
lays down the empty base folder structure for the redesigned vault. Assumes
`Work/` is already empty — the operator archives/clears any prior content
themselves, entirely out of scope here (mirrors this project's own
established archive-not-delete discipline, just performed by the operator
directly rather than by a migration module this time).

Provisions, as empty scaffolding only (no notes, no data):

- `Work/Customers/` — PARA Areas. Individual Customer OKF directories are
  NOT pre-created here; they're created on-demand the first time a real
  Customer is captured (existing `ensure_customer_hub_note`-style behavior).
- `Work/Threads/` — raw+distilled email Capture (see `REQ-SB-71`).
- `Work/Meetings/` — Meeting Capture (see `REQ-SB-71`).
- `Work/Resources/` — PARA Resources. Empty bucket only; the internal shape
  (Playbook/Competitive-Intel/Product-Knowledge subfolders discussed) is
  NOT locked by this requirement — creating the bucket is in scope, deciding
  its internal organization is not.
- `Work/Archive/` — PARA Archive, with `Opportunities/`, `Customers/`, and
  `Resources/` subfolders, formalizing what `REQ-SB-59`'s migration already
  did quietly into `.second-brain/migration_backup/` — this time a
  first-class, Obsidian-browsable location.

**Explicitly NOT provisioned by this requirement** (real, deliberate
exclusions, not oversights):

- `Work/Opportunities/` — the operator's own words: "Keep Opp for later."
  Structure for this PARA bucket has not been designed yet.
- `Work/Websites/`, `Work/Notes/` — two Capture kinds named as future data
  sources, neither has a designed shape yet.
- `Work/Customers/<slug>/People/`, `Work/Customers/<slug>/files/` — these
  are per-Customer subshapes created alongside their owning Customer
  directory (`REQ-SB-71`'s own scope), not part of the empty base skeleton.

<!-- Raised 2026-08-18, same structural-design conversation as REQ-SB-71
below. Operator's own words: "Structure the base we will have a Provison
API for that." Resolved directly, no material assumption: the exact bucket
list above is a direct transcription of what was designed and confirmed,
turn by turn, earlier in the same conversation — Threads/Meetings/Customers/
People/Files shapes were each individually confirmed by the operator before
being written here; Opportunities/Resources-internals/Websites/Notes were
each explicitly deferred by the operator's own words ("Keep Opp for later"),
not silently dropped. -->

**Acceptance:** Calling the provisioning endpoint against an empty `Work/`
creates exactly the folders named above and nothing else — verified by a
real directory listing before/after. A second call is a no-op (idempotent,
mirroring `ADR-047`'s "nothing left to act on" convention) — no error, no
duplicate creation. `Work/Opportunities/`, `Work/Websites/`, `Work/Notes/`
are confirmed absent after provisioning — proving the deferred buckets were
genuinely excluded, not forgotten.

---

### REQ-SB-71: Redesigned Email & Meeting Capture — Raw/Distilled Split, Section-Ownership Enforcement, People Auto-Extraction, File Companion Notes

Replaces `REQ-SB-55`/`REQ-SB-56`/`REQ-SB-69`'s current Thread/Meeting shape
with the design worked out directly with the operator, note kind by note
kind, in a dedicated vault-structure conversation. Five parts, one cohesive
redesign — `/spec` may split these into multiple stories if that's the
cleaner build shape, but the vision below is one coherent whole and should
not be built piecemeal without the others.

**Standing constraint, applies to this requirement AND `REQ-SB-70`:** every
capability this requirement builds — provisioning, Email pipeline, Meeting
pipeline, and any operator-triggered step within them — must be reachable
via a real HTTP API endpoint (matching this project's existing `/poc/*`
convention), and both build-time and every later verification/manual-trigger
must go through that real endpoint, never a raw internal-function script
call bypassing it. The operator's own words: "you don't do anything manually
you do it by calling the APIs." This closes a real gap named directly from
tonight's own `REQ-SB-59` migration work, where verification calls were
sometimes made via a raw `python -c` script instead of the real endpoint —
that pattern is not acceptable going forward for this requirement or any
work that reuses it.

**Out of scope, explicitly — scheduling/autonomous triggering.** This
requirement is the development pieces ONLY: the API endpoints and the
capture/synthesis logic they invoke when called. It does NOT include wiring
either pipeline into `REQ-SB-47`'s scheduler, any cron-style recurring tick,
or any other self-triggering mechanism — unlike `REQ-SB-55`/`REQ-SB-56`
(which do run on a schedule today). Every call into these APIs is operator-
initiated, with the operator's own AI assistant (Claude Code) acting on
their behalf as the caller — "you will be acting as me" (the operator's own
words). `/plan-tasks`/`/implement-sprint` must not add scheduler wiring,
background-agent registration, or any `agent_schedule_registry` entry for
either pipeline as part of this requirement — if recurring/autonomous
capture is wanted later, that is a deliberate, separate, future requirement,
not an assumed default here. The two-stage split named in point 2 below
describes what happens INSIDE one API call's own execution (Stage 1 then
Stage 2, both synchronous to that call or at least both triggered by it),
not two independently-scheduled jobs.

1. **Thread = raw/distilled split, not one file.** Today a Thread note IS
   the transcript. Going forward: every individual email becomes its own
   immutable, verbatim raw note at
   `Work/Threads/<thread-slug>/messages/<date>-<message-id>.md` — never
   edited once written. The Thread note itself,
   `Work/Threads/<thread-slug>/<thread-slug>.md`, becomes a *distilled*
   layer: `## Summary` (agent-owned, regenerated from the raw messages),
   `## Personal Notes` (human-owned), `## Actions` (human-owned — open
   question for `/spec` to resolve: a literal checklist section, or backed
   by this codebase's existing `todo_classification`/todo-capture
   mechanism so an Action surfaces wherever else todos are tracked, not
   only inside this one note).
2. **Two-stage pipeline, matching this project's own decoupled-pull lesson
   (`REQ-SB-69`).** Stage 1 (fast, cheap, must never fail): capture a raw
   email, group it provisionally by Outlook's own `ConversationID` alone —
   zero LLM calls, zero dependency on Compass being up or fast. Stage 2
   (slower, Compass-backed, fully decoupled from Stage 1): a Librarian-owned
   pass does the real judgment — which Customer this belongs to, merge vs.
   new Thread, regenerating `## Summary`. A stall in Stage 2 must never
   block Stage 1 from continuing to capture raw mail (same proof obligation
   `REQ-SB-69` already established for the pull/process split, extended one
   level deeper). A raw email's provisional Thread grouping is correctable
   later by Stage 2 without re-fetching anything from Outlook.
3. **Meeting = one-time vs. recurring, frontmatter-only logistics, raw
   invite dropped entirely.** A one-time meeting is a single note,
   `Work/Meetings/<meeting-slug>.md`. A recurring meeting is ONE ongoing
   note per series, `Work/Meetings/<series-slug>/<series-slug>.md`, with
   `## History` (agent-owned) gaining one dated entry per occurrence —
   never one file per occurrence. For a recurring occurrence, the dated
   entry is synthesized from BOTH the calendar event (logistics only) AND
   its linked follow-up Thread (the real substantive content, per the
   operator's own description of how recurring meetings actually work for
   them). The raw calendar invite itself — Teams-link legal footer, dial-in
   boilerplate — is dropped entirely at capture, never stored anywhere, not
   even archived (it is noise, not data, per the operator's own explicit
   call). Only functionally useful fields survive, in frontmatter:
   `teams_link`, `dial_in`, `organizer`, `attendees` (wikilinks),
   `recurrence`, `calendar_event_id`/`calendar_series_id`. `## Summary`/
   `## History` are agent-owned; `## Personal Notes`/`## Actions` are
   human-owned.
4. **People — nested under their primary Customer, auto-extracted from TWO
   sources.** `Work/Customers/<customer-slug>/People/<person-slug>.md` is a
   Person's primary home (a physical filing choice, not a hard constraint —
   a Person spanning multiple Customers is simply wikilinked from the
   others, never physically duplicated or moved). Auto-creation/linking
   runs off BOTH email participants (existing `people_extraction`) AND
   Meeting `attendees` (new — the same extraction logic extended to a
   second source), directly closing the operator's own named gap: "people I
   meet that I don't have emails for." A Person not surfaced by either
   automated source (someone only ever mentioned in conversation, never a
   participant/attendee) is a genuine, accepted gap — closed by manual/@
   mention creation, not further automation. Body: `## Glimpse` (agent-owned,
   rolled up from every Thread/Meeting mention) + `## Personal Notes`
   (human-owned).
5. **Files — renamed from `attachments/` to `files/`, each file gets its own
   OKF companion.** `files/<file-slug>/<original-filename.ext>` (the raw
   file, untouched) sits beside `files/<file-slug>/<file-slug>.md` (an OKF-
   shaped note: frontmatter + `## Summary`, agent-owned, generated from the
   file's real content, reusing the existing `compass_client.
   summarize_content` primitive + `## Personal Notes`, human-owned). This
   replaces today's behavior, where an attachment's summary is buried as an
   unlinked "dated sub-entry" inside its parent note — every file becomes a
   first-class, backlink-discoverable thing in its own right. Applies
   uniformly to every concept family that can carry files (Customers,
   Threads, Meetings, People, and Opportunities once that bucket exists) —
   one convention, not a special case per kind.
6. **Section-ownership enforcement is a cross-cutting, foundational rule —
   not specific to Threads/Meetings, and not optional.** Every body section
   in the ENTIRE vault, every note kind, is either Agent-owned (freely
   regenerable) or Human-owned (an agent may read it for context, but no
   agent code path may ever write to it) — never a hybrid/negotiated
   section. This must be enforced in code, not left to convention/comments:
   the existing `vault_writer.replace_body_section` primitive (already used
   today, e.g. by attachment-summary jobs that are told via a code comment
   not to touch `## Summary`) gains a real, checked allow-list of section
   names per caller, so a caller attempting to write outside its own
   allow-list is rejected outright, not merely discouraged. This closes a
   real, named risk: "What Challenges me is the Personal Info on the Item
   Being Re Written... It Applies everywhere not just on the Threads" (the
   operator's own words) — solved by ownership-typing every section plus a
   code-level guard, deliberately WITHOUT a snapshot-before-write safety net
   or an extra approval gate beyond what already exists for `Background`
   amendments (`REQ-SB-57`) — the operator explicitly chose the lighter,
   two-rule version over the heavier four-rule version discussed.

<!-- Raised 2026-08-18, dedicated vault-structure conversation, immediately
following the REQ-SB-59 migration being paused mid-run over a reliability
concern ("This is Very Un Reliable and We lose soo many info if we lost the
emails"). Every design decision above was individually proposed, challenged,
and confirmed turn-by-turn with the operator across that conversation — none
are analyst-assumed defaults. Operator's own words grounding the two biggest
structural calls: "Font Matter and OKF Open Knowledge Format... my Idea is to
have Agents Build the Data, then I can Put More info in the data, but doing
so Will make it a mess that's why I am thinking of Having Agents as
Organizers" (the Stage-1/Stage-2 split, point 2); "1 and 2 is enough" (section-
ownership + code-enforced allow-list, explicitly declining the heavier
snapshot/extra-approval options, point 6). `Work/Opportunities/` integration
is explicitly out of scope (operator: "Keep Opp for later") — this
requirement's Thread/Meeting/People/File work must not assume or hardcode an
Opportunity association that doesn't exist yet. This requirement supersedes
`REQ-SB-55`/`REQ-SB-56`/`REQ-SB-69`'s Thread/Meeting shape going forward;
those requirements' own already-`Done` stories are not retroactively edited
(hard rule 1, append-only specs) — this is new, superseding forward work,
exactly like `REQ-SB-53`'s own "SUPERSEDED" precedent. -->

**Acceptance:** A real, live-captured email produces a raw, immutable message
note under its Thread's own `messages/` folder, and a separate Thread note
whose `## Summary` is agent-regenerated while a manually-added `## Personal
Notes`/`## Actions` entry survives byte-for-byte across a re-synthesis —
verified live. A real one-time meeting produces a single note with no raw
calendar-invite boilerplate anywhere in it; a real recurring meeting's second
captured occurrence appends a new dated `## History` entry to the SAME note
(file count does not grow) whose content is drawn from its linked Thread, not
just calendar metadata — verified live. A real meeting attendee who has never
sent an email gets a real Person note auto-created/linked under their
Customer — verified live. A real attachment produces a `files/<slug>/`
directory containing both the original file and a generated OKF companion
note with a real `## Summary` — verified live. An agent function attempting
to call `replace_body_section` on a section outside its own declared
allow-list is rejected (a real, deliberate test of the guard, not just an
absence-of-bugs argument) — verified live.

---

### REQ-SB-72: The Librarian Section — First Housekeeping Pipeline (Thread Rename, Files Backfill, `## Related` Ownership, Company Folder Backfill)

Introduces **the Librarian as a new Section** in the Agents Map (alongside
Sales/Products/Technical) — not a single monolithic agent, a Section that
houses multiple independently-controllable housekeeping pipelines, mirroring
how every other Section already works. This requirement builds the FIRST
such pipeline, targeting the real Thread corpus `REQ-SB-71` just captured:

1. **Rename Thread files to human-readable names.** `<date> <subject-without-
   Re->` (e.g. `2026-08-16 Ewec Discussion`), replacing the current
   deterministic `<conversation-id-slug>` naming. **This requires switching
   Thread existence-lookup from `ADR-048`'s deterministic path-based check
   back to a frontmatter-based match on `conversation_id`** — a disclosed,
   deliberate partial reversal of `ADR-048` Decision 7, justified by real
   operational data: steady-state capture volume is ~10 emails/hour (not the
   400-email bulk-retrofit volume `ADR-048` was optimized for), at which a
   frontmatter scan is cheap enough to be the standing lookup method, making
   renaming safe by construction rather than needing a fragile fast-path/
   fallback hybrid. (Bulk/retrofit operations may still use path-based
   lookup internally if needed — this does not require every code path to
   change, only steady-state capture's own existence check.)
2. **Backfill the `## Files` section and Files/OKF companions across the
   real corpus.** For every real attachment already durably saved at
   `Work/Threads/attachments/<conversation_id>/<message_id>/<filename>`
   (Stage 1's own existing, real persistence — confirmed live, nothing lost)
   that does not yet have a `files/<slug>/` OKF companion under its owning
   Thread, generate one (reusing `REQ-SB-71-US-02-T07`'s own unmodified
   mechanism). Then add a `## Files` section to the Thread's own concept
   file — one entry per attached file: filename, date, a small summary
   (drawn from the companion note's own `## Summary`), and a link to the
   companion note itself. Distinct from `## Summary`'s own narrative — this
   is a structured list, not prose.
3. **Take over `## Related` ownership from Stage 2, entirely.**
   `email_classification.synthesize_thread` (`REQ-SB-71-US-02-T05`)
   currently writes `## Related` as a byproduct of its own regeneration,
   populated with raw participant email addresses
   (`[[naima.bikbi@core42.ai]]`) rather than real Person/Company note links —
   confirmed live against real Thread notes. Going forward: `synthesize_
   thread` MUST stop writing `## Related` at all (a real, disclosed
   retrofit of already-`Done` `SPRINT-061` code, not new-story-only scope);
   the Librarian becomes its sole owner, populating it with real wikilinks
   to existing Person/Company notes for every participant AND every company
   mentioned in the Thread's own content — not just raw addresses.
4. **Create a Customer folder for a mentioned company if none exists.**
   Reuses the existing `REQ-SB-63` Filing-Expert mechanism
   (`ensure_customer_hub_note`-style behavior) unchanged — no new
   placement-decision logic invented for this requirement.

**Explicitly deferred, not this requirement's scope** (raised and
consciously punted in the same conversation, not oversights):
- **Meaningful/topic tags** (e.g. `#stage/proposal`, `#renewal-risk`) — a
  genuinely separate task needing its own taxonomy discussion, per the
  operator's own reasoning: this pipeline's 4 tasks are all mechanical
  (compute a name, list known facts, link an existing entity, ensure a
  folder exists); tagging requires a vocabulary decision first.
- **Cross-Thread linking of recurring file artifacts** (e.g. the same
  "H2 Forecast" report resent repeatedly with evolving content) — explicitly
  deferred to the future Opportunity/Pipeline work, since tracking how a
  recurring artifact evolves is fundamentally a pipeline-tracking concern.
  For now, each attachment instance is captured independently, disambiguated
  by its own capture date — no same-artifact detection is built here.

**Standing constraint, same as `REQ-SB-70`/`REQ-SB-71`:** every capability
must be reachable via a real HTTP endpoint. **Unlike `REQ-SB-70`/`REQ-SB-71`
(explicitly manual/API-only), this pipeline SHOULD be scheduled/autonomous**
— the operator's own explicit call: ongoing vault hygiene benefits from
running itself, unlike capture (which the operator wants full manual control
over). Any finding this pipeline can't resolve deterministically routes
through a real Pending Approval, the same gate `Background` amendments
already use — this is what keeps autonomous operation safe.

<!-- Raised 2026-08-18, same vault-structure design conversation as
REQ-SB-70/71, opened once REQ-SB-71's own capture pipelines were built and
real housekeeping gaps (ESC-046, ESC-048) surfaced as live evidence for why
this Section is needed. Every decision above (the Section-not-single-agent
shape, the 4 concrete tasks, the frontmatter-matching reversal, the
## Related ownership transfer, both deferrals) was individually proposed,
challenged, and confirmed turn-by-turn with the operator — including two
real course-corrections the operator caught directly: (1) the operator
confirmed physical files must always live in-vault, never external
references only; (2) the operator's own "then we have a Section for files
in the Thread" framing is what resolved a race-condition risk this pass
itself raised (a separate Librarian mentions-pass conflicting with Stage
2's own regeneration) — giving `## Related` its own, already-existing,
exclusively-owned section sidesteps that conflict by construction, the same
"one owner per section" rule `REQ-SB-71-US-01` already built. -->

**Acceptance:** A real Thread's file/directory is renamed to a human-
readable date+subject name, and a real new message in that SAME
conversation is correctly matched to the existing Thread afterward (no
duplicate created) — verified live. A real attachment already durably
staged gets a real `files/<slug>/` OKF companion generated, and the owning
Thread's own `## Files` section lists it with a real summary and a working
link — verified live, across more than the 2 already-companioned threads.
A real Thread's `## Related` section contains real Person/Company note
wikilinks (not raw email addresses) after this pipeline runs, and a
subsequent Stage 2 re-synthesis of that same Thread leaves `## Related`
byte-for-byte unchanged — verified live. A real company mentioned in a
Thread with no existing Customer folder gets one created via the existing
Filing-Expert mechanism — verified live.

### REQ-SB-73: Bidirectional Thread ↔ Message Linking (Retrofit + Rename-Safe)

A real Thread note and its own raw `RawMessage` notes currently have NO
Obsidian-visible relationship — the only connection is filesystem nesting
(`Work/Threads/<slug>/messages/`), invisible to the link graph, backlinks
panel, and graph view. Confirmed live against the real vault: a raw message
note's frontmatter carries only `conversation_id`/`message_id`/`sender`/
`subject`/`received` (no back-reference), and a Thread's own `## Related`
section links out to Customer/Partner notes only, never to its own
messages. Closes this gap in both directions:

1. **Thread → Messages.** A new `## Messages` section on the Thread's own
   concept file, Agent-owned, fully regenerated each pass (never
   incrementally patched — mirrors `## Glimpse`'s existing "mechanical
   rollup" contract, `REQ-SB-54` point 8): one `- [[<message-stem>]]` bullet
   per raw message currently under that Thread's `messages/` directory.
   Safe by construction — a raw message's filename (`<date>-<hash>.md`) is
   never renamed by anything in this codebase, so this direction survives
   a Thread rename with no extra handling needed.
2. **Messages → Thread.** A new `thread:` frontmatter field on each
   `RawMessage` note, a wikilink to its owning Thread's CURRENT slug. This
   direction is NOT safe by construction — `librarian_housekeeping.
   rename_threads()` (`REQ-SB-72-US-01-T03`) renames a Thread's whole
   directory (and its concept file) without touching anything inside
   `messages/`, so a name-based backlink written once would silently go
   stale on the very next rename pass — the same class of staleness
   `ADR-052` already had to fix once for a different lookup path. Resolved
   the same way that precedent resolved it: `rename_threads()` itself is
   extended to fan out immediately after each successful move — walking
   the just-renamed Thread's own `messages/` directory and rewriting every
   message's `thread:` field to the new slug, in the same operation as the
   move, zero staleness window. This is a bounded addition to an already-
   shipped, currently-running job, not a new mechanism.
3. **New Librarian Job — the retrofit vehicle.** A new `link_thread_
   messages()` Job under the existing Librarian Section/Agent (no new
   Section, no new Agent — mirrors how `backfill_files` added a Job to the
   same Section without inventing a new one). For every real Thread: (a)
   regenerates `## Messages` from the current `messages/` glob, (b) writes
   or corrects `thread:` on every message currently missing one or
   pointing at a stale slug. Idempotent and safe to re-run — this single
   Job IS the one-time retrofit across the real corpus (137 Threads / 257
   messages, real counts confirmed live 2026-08-19) AND doubles as an
   ongoing self-healing safety net for anything a future capture pass
   misses, mirroring `backfill_files`'s own existing precedent rather than
   a one-off script (`MEMORY.md` — API-first, no script workarounds).

**Explicitly deferred, not this requirement's scope:** Stage 1 capture
(`raw_message_capture.capture_raw_thread_messages`) is NOT modified to
write these links itself at capture time — structured post-capture
enrichment is the Librarian's job in this codebase (same division of labor
`REQ-SB-72` already established for `## Files`/`## Related`), not
capture's. A freshly captured message becomes linked on the Librarian's
next scheduled pass, not synchronously at capture — acceptable since
capture already runs well ahead of the Librarian's schedule and nothing
downstream depends on same-request linkage.

<!-- Raised 2026-08-19, operator: "Emails are not linked to threads" —
confirmed live against the real vault before scoping (message frontmatter
has no back-reference; Thread's own ## Related never lists its messages).
Retrofit-vs-routing priority ("Do the linking retrofit first, keep routing
manual for now") and the rename-safety design (fan-out on rename vs.
one-directional-only) were each proposed with named tradeoffs and
confirmed directly by the operator turn-by-turn, including the operator's
own explicit prompt to think through the Librarian rename interaction
before scoping this ("Just a Reminder we rename Threads Using the
Liberian, How we will Takle that") — the fan-out design is a direct
response to that prompt, not an unprompted addition. -->

**Acceptance:** Every real Thread's `## Messages` section lists a working
`[[wikilink]]` to every raw message currently under its own `messages/`
directory — verified live across the full real corpus. Every real raw
message note carries a `thread:` frontmatter wikilink that correctly
resolves to its owning Thread's CURRENT file — verified live. A real
Thread is renamed via the existing `rename_threads()` Job, and every
message under it has its own `thread:` field updated to the new slug in
that SAME pass — verified live, zero stale links. Re-running `link_thread_
messages()` against an already-fully-linked corpus is a true no-op (no
file content changes) — verified live.

### REQ-SB-74: Customer Backfill — Propose/Approve Thread Routing + Noise Reconciliation

Confirmed live against the real vault (2026-08-19): a `Work/Customers/`
directory already exists with 26 OKF-conformant Customer folders (real
accounts — ADNOC, Aldar, Masdar, G42, Mubadala, EWEC, SimplAI — mixed with
what checking several turned out to be noise — Apple, Google, Instagram,
LinkedIn, Twitter, YouTube, Microsoft, NVIDIA, Razer, each an identical
empty `## Glimpse`/`## Background` shell, `status: "active"`, apparently
from an earlier mechanical company-name-extraction pass with no
correctness check). Meanwhile **zero of the real 137 Threads have ever
been routed** — all still carry `customer: "Unsorted"` — and a real,
repeatedly-mentioned company (TAQA) has no folder at all. This requirement
does the one-time backfill, using the SAME propose-then-approve posture
already established for `Background` amendments (`REQ-SB-57`) and kept
deliberately separate from live/ongoing capture, which stays manual
(`REQ-SB-70`/`71`'s standing constraint, reaffirmed by the operator this
same conversation).

1. **Librarian proposes a Customer match per Thread.** For each of the 137
   real `Unsorted` Threads, reads subject/participants/message content and
   proposes either an existing Customer folder (name match against the
   real 26) or a NEW Customer folder for a clearly-named real company with
   none yet (e.g. TAQA) — never a silent write.
2. **Batched, not 137 individual approvals.** Proposals group by proposed
   Customer (one approval decision covers every Thread proposed for that
   same Customer), the practical scale this needs to actually get
   reviewed — a genuinely new grouping shape for Pending Approvals,
   disclosed here as a design choice for `/plan-tasks` to size, not
   pre-decided by the operator.
3. **On approval:** writes the batch's Threads' `customer` frontmatter to
   the approved name, AND corrects each Thread's `tags` list entry from
   `customer/unsorted` to the real `customer/<slug>` — this is the
   "tag the Customer" the operator asked for, folded into the same write,
   not a second pass or a new tag taxonomy.
4. **Noise reconciliation is evidence-based, not name-guessed.** Rather
   than a human (or Claude) pre-judging which of the 26 existing folders
   are noise from their name alone — unreliable; several ambiguous
   real-sounding names (Columbus, Sindan, AZCON Holding, HR Avatar) were
   deliberately NOT hand-classified here for exactly this reason — any
   existing Customer folder that ends this pass with ZERO real Threads
   ever matched to it is surfaced as an explicit "no evidence found —
   candidate for archival" proposal. The operator confirms per-candidate;
   approved ones move to `Work/Archive/Customers/` (never deleted, per
   this project's standing archive-not-delete value).

**Explicitly deferred, not this requirement's scope** (operator's own
words this same conversation: "we will work more on Threads Later"):
- **Project-level routing** (Thread → Project beneath a Customer) — stays
  untouched; this requirement only reaches Customer, one level up.
- **Pipeline-stage or topic/content tags on Threads** — the deeper Thread
  taxonomy question stays open for a later, separate conversation; this
  requirement's only tag change is correcting the existing
  `customer/<slug>` tag element once a Thread's real Customer is known.
- **Wiring `synthesize_customer`/`resync_project_from_thread`** into the
  live capture pipeline (`#128`, still explicitly parked by the operator:
  "we will need to discuss that more but not now") — this requirement
  writes `customer:` frontmatter directly via the approval handler, it
  does NOT call `synthesize_customer` as a side effect. A routed Thread's
  Customer `## Glimpse` stays exactly as empty as it is today until that
  separate, still-parked decision is made.

<!-- Raised 2026-08-19, operator: "Start as well The Enrichement, Tags and
Customers Back file From the data." Scoped down through 3 direct
clarifying questions (noise cleanup, backfill method, tag scope) —
operator confirmed "Archive noise, then backfill" and "Propose, then you
approve" as given; the operator's own free-text answer on tag scope
("Customer Backfill and Tag the Customer we will work more on Threads
Later") is what bounds this requirement to Customer-tag correction only,
explicitly deferring pipeline-stage/topic tags and any deeper Thread work
to a later conversation — not an assumption, the operator's own words.
The evidence-based (vs. name-guessed) noise-reconciliation sequencing is
a disclosed design choice made in service of the operator's chosen
"Archive noise, then backfill" intent, reordered for correctness (several
of the 26 names are genuinely ambiguous without checking real Thread
evidence) rather than a reversal of the operator's decision. -->

**Acceptance:** Every real Thread with a clear Customer signal in its own
content receives a real, non-`Unsorted` `customer` frontmatter value and a
corrected `customer/<slug>` tag, only after an explicit operator approval
of its batch — verified live. A real company with no existing Customer
folder (TAQA) gets one proposed and, on approval, created via the existing
`ensure_customer_hub_note` mechanism — verified live. At least one real
existing Customer folder that receives zero real Thread matches through
this pass is surfaced as an archival candidate, and on operator approval
is moved to `Work/Archive/Customers/` with its file content byte-for-byte
unchanged — verified live. Declining a proposed batch leaves every one of
its Threads' `customer` frontmatter and tags unchanged — verified live.

### REQ-SB-75: The Vault — Real-Data Knowledge Graph Screen

A new screen, **"The Vault"**, rendering the real vault as an interactive
force-directed graph — Customers, Threads, Meetings, People, and Files as
nodes, wikilinks as edges — with click-through to the actual note. Design
was validated directly against a live, working sketch built and iterated
this same conversation (real interactions: drag/zoom/pan/filter/search/
click-to-inspect, in the app's own real dark/copper theme) rather than
through a separate `/design` prototype pass — the operator's own explicit
call ("No Need for Designer What we have is amazing"), so this requirement
skips straight to `/spec` carrying that sketch as its concrete reference.

1. **Zero new indexing/caching.** Reuses `vault_indexing.get_index()`
   directly — confirmed live this session to already carry every note's
   `stem`, frontmatter (`type`, tags), and both `outgoing_wikilinks`/
   `incoming_wikilinks` (the same index search/backlinks already read from,
   independently strengthened THIS session by `REQ-SB-73`'s architect pass
   to also scan frontmatter-shaped wikilinks, not just body text). A new
   endpoint reshapes this existing index into `{nodes, edges}` — never a
   second, divergent graph-construction mechanism.
2. **Real screen, adapted from the verified sketch.** New route in the real
   frontend, built from the sketch's own proven interaction set (drag,
   zoom/pan, kind filters with live counts, name search, click-to-select
   with connection highlighting, an inspector panel) — reusing the real
   `tokens.css` values and component vocabulary (`.cockpit-layout`'s 3-
   column recipe) already confirmed correct in the sketch itself, not
   re-derived.
3. **Click a node → see the real note.** Navigates to the ALREADY-SHIPPED
   `/browse/:stem` route (`NoteDetailPage`, `REQ-SB-02`) — no new note-
   viewing mechanism invented; the graph is a new way IN to a screen that
   already renders real note content correctly.
4. **Node kind derived from existing frontmatter/tags**, not a new
   classification pass — `type`/`kind/*` tags already distinguish Thread,
   Customer, Meeting, Person, and File notes across the real corpus.

**Explicitly deferred, not this requirement's scope:**
- Any new note-detail rendering, editing, or note-content interaction
  beyond what `/browse/:stem` already does today.
- The "Vault Browser" vs. "The Vault" naming overlap — flagged live to the
  operator, not yet resolved; both names may coexist, or the operator may
  choose to reconcile them later. Not blocking this requirement.
- Large-corpus performance (neighborhood scoping / clustering instead of
  rendering every note at once) — a real, disclosed concern at genuinely
  large note counts, explicitly out of scope at the vault's current real
  scale (~680 notes) per the operator's own conversation this session.

<!-- Raised 2026-08-19, operator: "I want to put this Graph with a Click
on it to let me see the note at some point as the next sprint. We are
Going to Call this the Vault" — then, when asked whether to route through
the standing `/design` precursor first: "No Need for Designer What we have
is amazing." This is a deliberate, explicit operator override of this
project's normal new-screen convention (design sign-off before `/spec`),
not a skipped step — the sign-off already happened, live, against a real
interactive artifact built and refined together this same conversation
(including a real correction: the first version used a stale light/green
theme from html-prototype/styles.css, caught by the operator and fixed
against the REAL current tokens.css dark/copper theme before this
requirement was drafted). -->

**Acceptance:** The Vault renders every real note in the vault as a node,
colored/grouped by its real kind, with a real edge for every real wikilink
between two indexed notes — verified live against the real corpus. Kind
filters and name search behave exactly as the verified sketch's own —
unchecking a kind fully hides its nodes and edges, not merely dims them —
verified live. Clicking a real node navigates to that note's real content
at `/browse/:stem` — verified live for at least one node of each of the 5
kinds. The screen renders in the app's real, current theme with zero
hardcoded colors that don't resolve through `tokens.css` — verified by
inspection.

### REQ-SB-76: Company Review — Extract & Recommend, Customer/Partner/Affiliate Classification, Batch-Apply

Replaces `REQ-SB-74`'s direct "propose routing a Thread to a Customer name"
mechanism with a safer, two-step one: extract a candidate real-world
**company name** from a Thread's own content, and ask the operator a
narrower, easier question first — **"is this a real Customer, a Partner,
an Affiliate of one, or nothing"** — before any routing decision is even
proposed. Confirmed live this session as the actual root cause of the
pre-existing Customer-folder noise (Apple/Google/Instagram/Twitter/
LinkedIn/etc.): `detect_customer_for_thread` is an LLM call grounded in
raw thread content — including real, common email-client signature
boilerplate ("Sent from my iPhone," "Get Outlook for Android" — 53 real
messages in the vault carry one) — and is told to reuse an exact name from
the **existing known-customers list**, which already contains that same
noise, making it self-reinforcing. Splitting "what company is mentioned"
from "should this become a tracked entity" closes that loop at its
cheapest point.

1. **Extract, don't route.** For each real Unsorted Thread, extract the
   real company name(s) genuinely relevant to the thread's own substance
   — explicitly instructed to disregard email-client/device signature
   boilerplate, mailing-list footers, and disclaimer text, not just told
   "don't guess" as today's prompt already says.
2. **Batched per company, not per Thread** — same shape `REQ-SB-74`/
   `ADR-055` already established (one approval decision covers every
   Thread proposing the same company name), reused directly, not
   reinvented.
3. **Five real outcomes per company batch**, resolved through the
   Pending Approval surface:
   - **Customer** — creates the Customer OKF directory (reuses
     `ensure_customer_hub_note`/`create_customer_directory_baseline`,
     `BUG-028`'s header fix already applied) and writes `customer`
     frontmatter + `customer/<slug>` tag to **every Thread in the
     backlog batch at once** — not just the one that triggered the
     proposal. Because future routing (`detect_customer_for_thread`)
     already reads the known-customer list fresh on every call
     (confirmed live, no new mechanism needed), this alone also
     correctly handles every future new Thread from the same company —
     "one approval, backlog AND future both handled" is the operator's
     own explicit framing for this requirement.
   - **Partner** — same batch-apply, but into `Work/Partners/`, reusing
     `ensure_partner_hub_note`/`link_note_to_partner_hub` (`ADR-009`).
   - **Affiliate of an existing Customer or Partner** — the operator
     picks the real parent from the known list; creates a normal
     Customer or Partner entry (operator's own choice of kind) with its
     `affiliate_of` field set to the parent's name, batch-applied the
     same way. **Re-introduces a real, already-designed mechanism**:
     `affiliate_of` (`ADR-009`) already exists in `vault_writer.py`'s
     legacy flat hub-note baseline (`create_customer_hub_note_baseline`)
     but was never carried forward onto the current OKF directory shape
     (`build_customer_concept_frontmatter`, `ADR-042`/`REQ-SB-54`) — this
     requirement restores it on the shape actually in use today. Also
     **revises `ADR-009`'s "Partner has no Affiliate concept" sub-clause**
     (a disclosed, narrow, additive revision, not a reversal of that
     ADR's real point — the operator's own original "Customer or Partner,
     never both" mutual-exclusivity decision is a different axis entirely
     from whether either one can itself have a parent, and is untouched).
   - **Merge into an existing Customer or Partner** — the real answer to
     the same real company already existing under a second, differently-
     spelled name (operator's own real example: "Mudala"/"Mubadala
     Investment Group" vs. an already-tracked "Mubadala"). The operator
     picks the real, already-known canonical entity from the list; every
     Thread in THIS batch (the duplicate name) gets routed to the
     CANONICAL entity's own `customer`/`partner` frontmatter + tag
     directly — no new folder created for the duplicate name at all. If
     the duplicate name already has its own real OKF directory with real
     content (from before this was recognized as a duplicate), that
     content is moved into the canonical entity and the duplicate's own
     now-empty folder is archived — reusing the exact same generic,
     vault-wide retag mechanism `migrate_customer_to_partner` (point 4,
     below) and the archival-candidate mechanism (`REQ-SB-74`) already
     use, never a new, third move/retag primitive.
   - **Decline** — no action; every Thread in the batch stays exactly as
     it is.
4. **Fixes the real, already-known `migrate_customer_to_partner` gap** —
   confirmed live this session: the function only understands the OLD
   flat `Work/Customers/<name>.md` hub-note shape and silently no-ops
   against every real Customer created under the current OKF directory
   shape. This was already logged as its own placeholder,
   `REQ-SB-62` (2026-08-16) — **this requirement absorbs and supersedes
   it**; `REQ-SB-62` itself is marked accordingly below, not built
   separately.
5. **Multi-Customer Threads — lightweight, additive, not a data-model
   rewrite.** The operator's own explicit scoping: real Threads can
   genuinely involve more than one company, but a full `customer:` →
   list-type schema change touches too much already-shipped code
   (`REQ-SB-74`, `project_customer_synthesizer.py`, `REQ-SB-75`'s Vault
   graph) for what this pass needs. Resolution: `customer:` frontmatter
   stays a single value — whichever company is confirmed FIRST for a
   given Thread. Any ADDITIONAL company confirmed for a Thread that
   already has a primary customer instead appends a `customer/<slug>`
   tag (alongside the existing one) and a `## Related` wikilink to that
   company's own concept file — real, visible, graph-connected, but zero
   change to the primary-field data model or anything reading it today.
6. **The only new UI this requirement needs is the approval decision
   itself** — the operator's own explicit framing ("everything need to be
   done by API calls the Approval is the only thing I need to fix the UI
   for"). The Pending Approvals surface gains a real decision control for
   this proposal kind specifically (Customer / Partner / Affiliate-of-
   [picker] / Decline) — no other new screen.

**Explicitly deferred, not this requirement's scope** (operator's own
words: "log the Rest as REQ and we pick them next"):
- **People notes linking to their real Company/Partner note** (currently
  tag-only, `tags: ["company/adnoc"]`, no real wikilink — confirmed live)
  — logged separately, see `REQ-SB-77`.
- **Grouping/color-coding the Pending Approvals list itself** by
  proposal type, to make bulk review easier — logged separately, see
  `REQ-SB-78`.

<!-- Raised 2026-08-19, same conversation as REQ-SB-74's own live data-
quality findings. Operator's own 6-point list ("Sent from Apple iOS...",
"Recommend instead of Routing... Extract Company Name and Ask me",
"Some Threads can be Assigned to multiple Customers", "People should be
linked to a Company...", "If an Email is very complex... Ask me", "Group
the Approval List to Sections and Colors") was triaged into this one
requirement (points 1/2/5/3 partially — the lightweight tag+Related
resolution) plus two deferred placeholders (points 4/6) at the operator's
own explicit direction: "I will clean the current customer folder... once
we confirm that this is a customer... I can Simple Click Approve and you
create a Customer Folder and Customer Tag Assign it to all threads...
this Handles the Backlog and Also in future it Handles the New Threads...
as Part of this I need to be able to move something to Partners... and
Some Companies are Affaliate to a Customer or a Partner... I guess this
can be a one go... Next we log the Rest as REQ and we pick them next...
everything need to done by API calls the Approval is the only thing I
need to fix the UI for." The Multi-Customer resolution (point 5) is the
operator's own direct correction after seeing the first draft of this
entry: "One Gap is the Multi Customer thread its Important and I don't
want to do a full write for that... All Emails will be updated based on
the list... is this a Customer and we can Append Tags and Related to the
email" — the tag+Related shape is a literal transcription of that
instruction, not this session's own invention. The `affiliate_of`/
`ADR-009` prior art and the `migrate_customer_to_partner`/`REQ-SB-62`
gap were both found live by direct code reading during this requirement's
own drafting, not assumed. The Merge outcome (point 3's fifth bullet) is
the operator's own real-time addition, caught while this requirement was
already being `/spec`'d: "sometimes you get the company Twice but with
Different Name? (Mudala, Mubadala Investment Group) I need an option to
move it as well" — folded in before the story moved past Draft, not a
separate follow-on requirement. -->

**Acceptance:** A real company name genuinely present only in email-
signature/device boilerplate (e.g. a thread whose only "iPhone"/"Android"
mention is client-signature text) is never proposed as a Customer/Partner
candidate — verified live against real messages carrying that boilerplate.
Approving a company as Customer or Partner writes real frontmatter/tags to
every real Thread in that batch, not just one — verified live across a
batch of 2+ real Threads. A company approved as an Affiliate of an
existing real Customer/Partner gets a real `affiliate_of` value pointing
at that real parent, for both Customer-kind and Partner-kind affiliates —
verified live. A company approved as a Merge into an existing real
Customer/Partner routes every Thread in its batch to the CANONICAL
entity's own frontmatter/tag, with no new folder created for the
duplicate name — verified live against a real duplicate-name pair.
`migrate_customer_to_partner` correctly moves a real OKF-directory-shaped
Customer (not just the legacy flat shape) — verified live, closing
`REQ-SB-62`. A real Thread confirmed for a second company after already
having a primary `customer` gets a real, additive `customer/<slug>` tag
and `## Related` wikilink, with its own original `customer` frontmatter
value byte-for-byte unchanged — verified live. Declining a batch leaves
every Thread in it completely unchanged —
verified live.

---

## P2

<!-- The integration surface agentic-map's agents will eventually use to query
this KB (separate, later decision — see MEMORY.md). -->

### REQ-SB-06: Search Quality Enhancements

Once basic search (REQ-SB-02) is in place, refine retrieval quality —
chunking note content ahead of embedding at scale, and reranking results —
rather than relying on the MVP's baseline relevance ranking alone.

<!-- Ported from agentic-map REQ-009 (chunk KB content before embedding) and
REQ-042 (KB reranking stage); deferred to P2 since there is nothing yet to
refine until REQ-SB-02 ships. -->

**Acceptance:** Search result relevance measurably improves over the REQ-SB-02
baseline on a representative set of real queries against the user's own vault.

### REQ-SB-60: Conversation — Merging Related Threads into One Real Exchange

A real-world exchange can span multiple Outlook `ConversationID`s that
`REQ-SB-54`'s Thread notes never merge (a subject-line edit that trips
Outlook's own conversation-split logic, a forward into a new recipient
set, a fresh email restarting an already-discussed topic). This
requirement builds `Conversation`, a note kind above Thread that groups
one-or-more related Threads into the single real exchange a human would
recognize them as.

<!-- Raised 2026-08-16, deferred deliberately, not by oversight — operator:
"I guess we keep threads as is and then we will need to have an entity
called Conversation where thread is the raw data, then we will handle the
data in the KB later." Explicitly punted past REQ-SB-54 through REQ-SB-59:
the merge logic (what makes two Threads "the same Conversation" — subject
similarity, participant overlap, some combination, manual linking, or
something else entirely) should be designed against real captured Thread
data once REQ-SB-55 has been running for a while, not guessed in the
abstract before any such data exists. Do not `/spec` this requirement
until REQ-SB-55 has real capture history to design against. -->

**Acceptance:** Not yet specced — this is a placeholder reserving the
concept, not a buildable requirement. Acceptance criteria are written when
this requirement is actually spec'd, informed by real Thread data.

### REQ-SB-61: App-Driven Section Creation — Location, Tags, Agent Wiring, OKF Conformance in One Flow

Today, `section_registry.create_section(name)` creates a Section as a pure
agent-organization concept (`{id, name}` + agent assignments) — it has no
awareness of vault storage at all. Separately, `REQ-SB-54`/`ADR-042` hand-built
one specific OKF-conformant directory family (`index.md`/`<slug>.md`/`log.md`/
`captures.md`) for exactly one KB area, Customer/Project. This requirement asks
the Second Brain app itself to make initiating a **new area of the KB** a single
first-class flow: define its Location (base vault folder) and Tags, wire one or
more Agents to it, and have it conform to the same OKF + frontmatter standards
`ADR-042` established — without hand-writing a new directory-family module in
code every time a new KB area is needed.

<!-- Raised 2026-08-16, deliberately deferred, not by oversight — operator:
"If I want to initiate a new Section in our KB, let's make Second Brain App do
it, so it will have the Location and Tags, and at the same time I can wire
agents on the new Section, and we will follow the Standards (OKF and Front
Matter)." Mirrors ADR-041's own established sequencing rule for the Pipeline
Builder ("build one real Pipeline by hand before generalizing into a builder")
— REQ-SB-54's Customer/Project OKF family is the first hand-built instance;
this requirement is the generalization, and should wait until it's the SECOND
one being hand-built (i.e. once REQ-SB-54 has shipped and at least one more
real KB area is needed) before designing the generic shape, so the abstraction
is drawn from two real cases, not guessed from one.

RESOLVED 2026-08-16, same day, operator: "This is a unified concept from now
on." Today's "Section" (`section_registry.py` — a pure agent-routing/Hub
grouping, e.g. Sales/Products/Technical/Customers/Productivity, no
vault-location concept at all) and a "new area of the KB" (a new
`Work/<Kind>/` family with its own OKF directory shape, e.g. what `ADR-042`
built for Customer/Project) are NOT two related-but-separate concepts —
going forward a Section IS its KB area: one identity, owning both the
agent-routing/Hub grouping AND its own Location/Tags/OKF-conformant
directory shape, created together in one flow. Any future Section (existing
5 starting ones included, once migrated) is expected to own a KB Location;
"a Section with no vault presence" is no longer a modeled case. This
resolves the disambiguation question for whenever this requirement is
actually spec'd — it does not change the deferral itself (still waiting on
a second real hand-built KB area, per `ADR-041`'s builder-after-two-real-
instances sequencing).

Refined 2026-08-16, discussed and confirmed same day, once `SPRINT-048`'s
own tasks landed: what actually got hand-built by `REQ-SB-54-US-01` is not
"one shape, done twice" — it's **two distinct area shapes**: flat, single-
file (Thread/Meeting, `T02`/`T03`) vs. 4-file OKF directory (Customer/
Project, `T04`/`T05`, where Project turned out to be near-pure reuse of
Customer's own generic `okf_directory_*` primitives, not independently
hand-built new logic). This is real, useful design input for REQ-SB-61
whenever it's spec'd — the generic Section-creation flow will need to
support BOTH shapes (or make shape an explicit choice at creation time), not
assume every Section is a directory. It does not, on its own, satisfy the
deferral condition: there still hasn't been a second real, independent
REQUEST to spin up a brand-new named KB area (as opposed to this sprint's
own planned build-out of Thread/Customer/Project) — the deferral stays in
place, now with a sharper design question to answer once it lifts. -->

**Acceptance:** Not yet specced — this is a placeholder reserving the
capability, not a buildable requirement. Acceptance criteria are written when
this requirement is actually spec'd, once a second real, independent request
for a new KB area arises. Section and KB-area are a unified concept (resolved
2026-08-16) — the eventual spec should model one, not two related identities,
and must account for both the flat and OKF-directory area shapes already
proven by REQ-SB-54 (refined 2026-08-16).

### REQ-SB-62: ~~UI-Driven Customer → Partner Reclassification~~ — SUPERSEDED by REQ-SB-76

`partner_hub_linking.migrate_customer_to_partner(customer_name)` — moving a
Customer hub note into the Partner namespace and retagging every note that
references it — exists today only as a function reachable through
`email_poc_router.py` (a POC endpoint, not a real UI surface). This
requirement asks for a real, user-facing way to trigger this reclassification
from the app.

<!-- Raised 2026-08-16, in the same conversation that closed out SPRINT-048
(REQ-SB-54-US-01) — operator: "The Customer to Partner will be a new
Requirement as I want to be able to do so from UI. Just log it for now."
Logged as asked, not analyzed further. Real, related gap surfaced by
SPRINT-048's own retro, worth carrying into this requirement's eventual
`/spec` pass: `migrate_customer_to_partner` is keyed off the OLD flat
`Work/Customers/<name>.md` hub-note shape and silently no-ops for a Customer
created under REQ-SB-54's new OKF directory shape (`Work/Customers/<slug>/`)
— any real UI-driven version of this capability needs to handle both shapes,
not just the pre-REQ-SB-54 one. See REVIEW-QUEUE.md and SPRINT-048's own
retrospective (Open follow-ups) for that disclosure's full detail.

**Superseded 2026-08-19** by `REQ-SB-76` ("Company Review — Extract &
Recommend, Customer/Partner/Affiliate Classification, Batch-Apply"), which
independently re-found this exact same old-shape/new-shape gap during its
own drafting and folds the fix — plus a real UI-driven trigger point, via
the Pending Approvals surface's new Customer/Partner/Affiliate decision —
directly into its own scope. Never built separately; do not `/spec` this
entry on its own. -->

**Acceptance:** Not yet specced — superseded, see above. Not a buildable
requirement on its own.

### REQ-SB-77: People Notes Linked to Their Real Company/Partner Note

A Person note currently carries only a `tags: ["company/<slug>"]` tag
inferred from email domain — confirmed live this session — with no real
wikilink to that Company's own Customer or Partner concept file. Same
"tagged but not graph-connected" gap already closed twice this session
for other note pairs (`REQ-SB-73` Thread↔Message, `BUG-028` Customer↔
log/captures). A Person with no determinable company should remain a
normal, unblocked entry — never held back waiting for a company match.

<!-- Raised 2026-08-19, operator: "People should be linked to a Company or
in the People Seaction if no COmpany is found for them" — deliberately
deferred out of REQ-SB-76's own scope at the operator's explicit
direction ("log the Rest as REQ and we pick them next"), not yet
`/spec`'d. -->

**Acceptance:** Not yet specced — placeholder reserving the capability.

### REQ-SB-78: Pending Approvals — Grouped, Color-Coded Review

The Pending Approvals surface currently renders as a flat list. At real
scale (496 real pending records existed at one point this session before
manual cleanup) this is genuinely hard to bulk-review. This requirement
asks for the list to group by proposal type/agent, with a real visual
(color) treatment per group, so approving every request of one kind is a
fast, single sweep rather than item-by-item triage.

<!-- Raised 2026-08-19, operator: "We can Group the Approval List to
Sections and Colors So it will be Easier to approve all requests for a
certain type" — deliberately deferred out of REQ-SB-76's own scope at the
operator's explicit direction, not yet `/spec`'d. -->

**Acceptance:** Not yet specced — placeholder reserving the capability.

### REQ-SB-79: The Librarian — Two Sub-Pipelines (Threads Cleaning, Company & Partner Building)

The Librarian Section currently shows as a single agent
(`librarian-housekeeping`) in the Agents Map, not as a Section housing
multiple independently-controllable pipelines — confirmed live this
session as a real, disclosed gap from `REQ-SB-72`'s own original framing
("a Section that houses multiple independently-controllable housekeeping
pipelines," never fully realized: `REQ-SB-65`'s Job Tree visualization is
hardcoded to `email-capture-pipeline` only,
`app/api/agents_router.py`: `jobs = email_capture_pipeline.get_job_tree()
if agent_id == "email-capture-pipeline" else []`). The operator's own
concrete resolution — two sub-agents, not one-per-job:

1. **"Threads Cleaning"** — `rename_threads`, `link_thread_messages`,
   `backfill_files`, `populate_thread_related_links`. These four already
   run together, in this fixed order, inside today's single
   `run_housekeeping_pass()` — the rename-must-run-first ordering
   guarantee stays intact by construction, since all four stay bundled
   in the same sub-agent, on the same schedule; splitting to 2 pipelines
   (not 5) sidesteps the ordering-tradeoff question the original 1-job-
   per-agent framing raised.
2. **"Company and Partner Building"** — `backfill_company_folders`
   (`REQ-SB-72`) plus the newer, separately-dispatched (never on the old
   6-hourly schedule) `propose_customer_backfill`/`propose_customer_
   archival_candidates` (`REQ-SB-74`) and `propose_company_review`
   (`REQ-SB-76`, building this same session) — every real Job whose job
   is creating/maintaining a Customer, Partner, or Affiliate entity,
   grouped under its own real Agent identity with its own schedule,
   independent of Threads Cleaning's own cadence.

**Sizing estimate given directly to the operator, recorded here for
continuity (pre-dates the 2-pipeline concretization, still the right
order of magnitude — 2 groups is less registration work than 5):**
smaller than `REQ-SB-72` itself (which built these jobs from scratch, 9
tasks/L) — mostly re-registration/re-wiring of already-working logic, not
new logic. Real work identified: several files currently hardcode
`agent_id="librarian-housekeeping"` as a single shared identity (Pending
Approvals call sites, `section_ownership.py`'s allow-lists,
`skill_registry.py`'s registrations, `main.py`'s seed-agent list) — each
job's own call sites need to move to whichever of the two new agent_ids
now owns it.

<!-- Raised 2026-08-19, operator: "I can see in the Liberian Section in
the UI its a one Agent not a Pipeline" then "How big is the Change to make
it a pipeline so instead of visiting all steps everytime we have one Sub
Agent Per job" — sizing estimate given directly in conversation, then
explicitly deferred: "Log it as a REQ and pick it up later." Concretized
same day, before this requirement reached `/spec`: "Just be Concrete / 2
Pipelines When for Threads Cleaning and one for Cumpany and Partner
Building" — this IS the requirement's own scope now, not a suggestion
layered on top of a more open "one per job" design. -->

**Acceptance:** Not yet specced — placeholder reserving the capability.
