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
assigned scope (e.g. "get me the pipeline for Masdar" returns that
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
7-Day Window, Done — the list this filters). -->

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
