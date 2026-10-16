---
id: REQ-SB-95-US-05
title: Entity resolution instead of search — one tag-keyed index, synthesis first then evidence
requirement_ids: [REQ-SB-95]
requirement_section: "REQ-SB-95: An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution"
phase: P2
status: Draft
gate: clear
gate_reason: ""
sprint: ""
created: 2026-10-16
updated: 2026-10-16
---

# REQ-SB-95-US-05 — Entity resolution instead of search — one tag-keyed index, synthesis first then evidence

## Story

**As a** Second Brain operator
**I want** a named entity in my question to resolve to a real kind, tag and hub
note, and the answer to be read from that entity's own scoped synthesis and
evidence
**So that** "give me the updates about Adobe" returns what is actually known
about Adobe, instead of a whole-vault search done because searching is the only
verb the agent has

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-95* — Finding 3 ("retrieval searches
  everything because searching is the only verb": Adobe is a Customer or a
  Partner, everything about it already carries `customer/adobe`, its synthesis
  lives in a hub note and its evidence in tagged Threads and Meetings; the
  install already proves the mechanism with three hand-made Index artifacts
  scoped by exactly that tag — `customer/adnoc`, `customer/masdar`,
  `customer/taqa`, rebuilt hourly — but there is none for Adobe and nothing tells
  the agent to prefer them) and the fourth **What is wanted** bullet ("Entity
  resolution instead of search. A name resolves against the Entities registry
  (names, aliases, domains) to a kind, a tag and a hub; the tag scopes the read;
  the read goes synthesis-first then evidence, newest first. **One tag-keyed
  index serves every entity rather than one index per entity**").
- **Architecture is already settled on the mechanism — `ADR-032`** (Accepted
  2026-10-16, pending a human look): "Entity scoping is ONE tag-keyed index, not
  one index per entity. A single artifact groups every `customer/*` and
  `partner/*` tag, so resolution is a dict lookup and a new entity needs no
  provisioning. The existing per-entity Indexes stay available for the few
  accounts that deserve a custom scope." `ADR-032` also records the consequence:
  "the answer depends on the registry being current. Discovery was paused for 41
  days before anyone noticed; this makes that staleness matter more, and argues
  for the pipeline freshness surface already proposed under `BUG-085`."
- **Sibling stories.** Fifth of `REQ-SB-95`'s five, and the most independent:
  `US-01` (Operator Profile), `US-02`/`US-04` (the Action and Workflow kinds) and
  `US-03` (publication and enforcement) are one spine; this is the retrieval
  half, and it answers the PRD's third failing request on its own. Its only
  dependency on the spine is Scenario 6 — the agent reaching the scoped read
  through the catalogue rather than only through a route.
- **Grounded against the real code, not guessed.** `Index` is already a real
  artifact kind with its own Manager, its own `folders`/`tags`/`depth`/
  `storage_path` scope and a real Hermes cron job per index
  (`business/core/index/index_manager.py`, confirmed by direct reading) — the
  three per-customer Indexes the PRD names are instances of it. A tag-keyed index
  is therefore an addition in a mechanism that already exists, not a new one.
- **One honest complication, and the reason this story is flagged.**
  `ADR-022` decides that the Customer, Partner and Opportunity concepts,
  `Entities.md`, its Settings page, the company Skills and `company_index` all
  move out of the framework into an Entities plugin (`sb-plugins-entities`), and
  that framework core "never imports, names or knows a plugin" — its own test
  being "*a second brain built for a CFO cares nothing about Partners and
  Customers*". `Settings/Entities.md` is already treated as **plugin** seed data
  by `app/plugin_api.py`'s `register_seed_data_file()`. `ADR-032` specifies a
  resolver over `customer/*` and `partner/*` tags without saying which side of
  that boundary it lands on. See the gate flag, `ESC-063`, and `REVIEW-QUEUE.md`.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A named entity resolves to a kind, a tag and a hub

```gherkin
Given the Entities registry knows an entity by its name
When that name is resolved
Then the resolution returns the entity's kind, its tag, and its hub note
  And the resolution is a lookup against the registry, not a search of the vault
```

### Scenario 2: The updates about an entity are read scoped, synthesis first

```gherkin
Given a resolved entity with a hub note and tagged evidence notes in the vault
When the operator asks an agent for the updates about that entity
Then the answer is built from that entity's own hub synthesis first, then its
    tagged evidence — Threads and Meetings — newest first
  And nothing outside that entity's tag scope is read to answer the question
  And the agent does not fall back to a whole-vault search
```

### Scenario 3: An alias or a domain resolves to the same entity

```gherkin
Given an entity recorded in the registry with aliases and known email domains
When the operator names it by an alias, or by one of its domains
Then it resolves to the same kind, tag and hub as its primary name
  And an alias that collides with another entity's name is reported as ambiguous
    rather than silently resolved to one of them
```

### Scenario 4: One tag-keyed index serves every entity, including a brand-new one

```gherkin
Given a new entity exists in the vault and the registry, with notes already
    carrying its tag
When the operator asks about it
Then it is served by the one tag-keyed index with no per-entity provisioning
    step — no new Index artifact, no new cron job, no hand-made setup
  And the three existing per-entity Indexes keep working untouched, still
    available for accounts that deserve a custom scope
```

### Scenario 5: A name that does not resolve is answered honestly

```gherkin
Given the operator names something the Entities registry does not know
When the agent answers
Then it states plainly that the name did not resolve to a known entity
  And if it does anything else instead, it says what it did
  And it does not present unscoped search results as if they were that entity's
    updates
```

### Scenario 6: The agent reaches the scoped read through the catalogue

```gherkin
Given the scoped entity read exists on this install
When an agent is asked about an entity
Then it reaches the scoped read as a catalogued Action, validated like any other
    action call
  And an agent not permitted to run it is refused like any other action
```

### Scenario 7: The one tag-keyed index covers every entity tag in the vault

```gherkin
Given the vault holds notes tagged for many different entities
When the tag-keyed index is built
Then every entity tag present in the vault is a key in that one index
  And an entity whose tag exists in the vault but which the registry does not
    know is reported, rather than silently dropped
```

## Affected Screens

- **None required — backend and agent behaviour only.** The operator experiences
  this story through agent answers in surfaces that already exist (the embedded
  agent chat panel and the Cockpit).
- If the tag-keyed index is surfaced for inspection, the natural home is the
  existing `src/frontend/src/pages/SettingsVaultIndex*Page.tsx` family, reused
  as-is — explicitly a Non-Goal here.

## Dependencies

- **Blocked by:** `REQ-SB-95-US-02` (Action as an artifact kind) and
  `REQ-SB-95-US-03` (catalogue publication + call validation) — **for Scenario 6
  only**. Scenarios 1–5 and 7 stand alone; if the product-owner needs to, this
  story can precede the spine with Scenario 6 split out.
- **Blocked by (human):** the `ADR-022` / `ADR-032` boundary question — see the
  gate flag and `ESC-063`. This decides which repository the work lands in.
- **Related to:** `REQ-SB-29-US-01` (agent-to-tag/folder scoping),
  `REQ-SB-54-US-01` (the vault knowledge model that put synthesis in hubs and
  evidence in tagged Threads/Meetings), `BUG-085` (pipeline freshness surface —
  the staleness consequence `ADR-032` names).
- **External:** the live install's Entities registry being current; the three
  real per-customer Indexes and their hourly cron jobs.

## Constraints

- **One tag-keyed index, not one per entity** (`ADR-032`). A design that
  provisions an Index artifact per entity does not satisfy this story.
- **Resolution is a registry lookup**, not a fuzzy search over note titles.
- **Scoped reads only.** The read is bounded by the resolved entity's tag;
  widening to the whole vault is the failure this story exists to remove.
- **Synthesis before evidence, newest first** — the read order is part of the
  requirement, not an implementation preference.
- **The existing per-entity Indexes are not deleted or migrated** (`ADR-032`).
- **The repository boundary must be honoured** once the human settles it — core
  must not name a plugin, and a plugin must not reach past `app.plugin_api`
  (`ADR-022`, `ADR-023`).

## Implementation Tasks

<!-- Indicative only — the decomposer owns the final split and the real IDs.
Which repository these land in depends on the flagged ADR-022/ADR-032 boundary
question. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-95-US-05-T01 | backend | Entity resolver — name/alias/domain → kind, tag, hub, over the Entities registry | `src/backend/app/business/` (or the Entities plugin, pending the boundary decision) | — |
| REQ-SB-95-US-05-T02 | backend | The one tag-keyed index — build over every `customer/*`/`partner/*` tag, with its own refresh | `src/backend/app/business/core/index/` | — |
| REQ-SB-95-US-05-T03 | backend | The scoped read — hub synthesis first, then tagged evidence newest first | `src/backend/app/business/logic/` | — |
| REQ-SB-95-US-05-T04 | backend | Expose the scoped read as a catalogued Action | `src/backend/app/business/core/actions/` | — |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **The Operator Profile, the Action and Workflow kinds, and the enforcement
  gate** — `REQ-SB-95-US-01` through `US-04`.
- **Replacing general vault search.** Search stays exactly as it is for questions
  that are not about a resolved entity.
- **Populating or curating the Entities registry.** Discovery and registry
  maintenance are existing, separate work.
- **A freshness/staleness surface for the index.** `ADR-032` explicitly defers
  that to `BUG-085`.
- **Deleting or migrating the three existing per-customer Indexes.**
- **Executing the `ADR-022` Entities extraction.** Whatever the boundary decision
  is, this story implements entity resolution — it does not perform the plugin
  extraction.

## Notes

**Operator decision, 2026-10-16 — flag cleared.** Operator, 2026-10-16: "Resolver is framework, Customer stays the plugin." The framework ships a tag-keyed resolver generic over any `<namespace>/<slug>` tag, naming no plugin; a plugin registers its namespace through the Plugin API, and the entities plugin registers `customer/` and `partner/`. This story builds here as mechanism; the namespace registration is `sb-plugins-entities`' own work. `ADR-022` stands unamended. `ESC-063` is Resolved, resolving artefact `ADR-035`.

**Prototype parity:**

- No screen region is added or changed by this story — the operator sees it
  through agent answers in already-approved, already-shipped chat surfaces
  (`html-prototype/inbox-cockpit.html`, `html-prototype/meeting-cockpit.html`,
  and the live Cockpit that `REQ-SB-82-US-06` established supersedes them).
  **Specced** with no net-new region; no `/design` pass is requested.
- Index inspection screens (`SettingsVaultIndexBuilderPage.tsx`,
  `SettingsVaultIndexFilteringPage.tsx`) — **Deferred**: surfacing the tag-keyed
  index for operator inspection is a Non-Goal here and would reuse those
  approved screens if it is ever wanted.

**Architect pointers for `/plan-tasks` (context, not decisions):**

- `IndexManager` already owns scoped indexes (`folders`/`tags`/`depth`/
  `storage_path`) with a real per-index Hermes cron job created via
  `hermes cron create --script --no-agent`, and its deployed script takes **zero
  argv and zero env** — it reads its own `Index.json` at run time. That is the
  live constraint any tag-keyed index refresh has to live inside.
- `Settings/Entities.md` is reached today through
  `plugin_api.register_seed_data_file()` — concrete evidence that the registry is
  already being treated as plugin-owned seed data, which is what makes the
  boundary question real rather than theoretical.

**Why `gate: flagged`** (MUST-FLAG review, trigger by trigger):

1. **Material assumption** — avoided. The ACs assert resolution, scoping and read
   order, all of which the PRD states literally; nothing here assumes which
   repository owns the code, which is precisely the flagged question.
2. **Unfinalised requirement** — no. `REQ-SB-95` carries no `<!-- Draft -->`
   marker and has a complete Acceptance paragraph.
3. N/A (architect/ADR trigger). No ADR created or changed by this pass. Noted for
   the human: `ADR-032` is itself still awaiting a look and is not in
   `REVIEW-QUEUE.md`.
4. **FIRED** — `ESCALATIONS.md` entry `ESC-063` written (category
   `adr-deviation`).
5. **Oversized** — no (~4 tasks, M), and the five-way split exists to keep it so.
6. N/A (coder trigger).
7. **FIRED — the controlling flag.** `ADR-022` and `ADR-032` give contradictory
   answers about where Customer/Partner entity knowledge lives. See the
   frontmatter `gate_reason`.
8. **Multiple equally-valid options** — a consequence of trigger 7 rather than a
   separate finding: framework-core resolver vs Entities-plugin resolver are both
   defensible readings of the two Accepted ADRs.
