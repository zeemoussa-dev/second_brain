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
