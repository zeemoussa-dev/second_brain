---
id: REQ-SB-95-US-05
title: Entity resolution instead of search — one tag-keyed index, synthesis first then evidence
requirement_ids: [REQ-SB-95]
requirement_section: "REQ-SB-95: An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution"
phase: P2
status: Ready
gate: flagged
gate_reason: "trigger-3 (ADR-037 created) — the tag-keyed index is a projection rebound inside VaultManager.rebuild_index() rather than a new Index artifact with its own cron job, a plugin registers a namespace as a callable, and the FRAMEWORK_API bump is taken once for all of REQ-SB-95; plus trigger-7 (decomposer, 2026-10-16) — the sibling US-02 task files carry no FRAMEWORK_API instruction, so the single bump is owed by whichever story lands last and only this story's T02 currently knows it"
sprint: SPRINT-090
created: 2026-10-16
updated: 2026-10-16  # product-owner: grouped into SPRINT-090 (alone — depends_on_sprints: [SPRINT-087, SPRINT-088]; that ordering also takes the FRAMEWORK_API bump via T02's conditional read)
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

<!-- Locked by the decomposer, 2026-10-16. Each scenario carries its AC-ID on
the line after its closing fence. Scenario 8 is decomposer-authored (see Notes →
Decomposer pass): it makes `ADR-037`'s registration seam and its single
`FRAMEWORK_API` bump verifiable rather than implicit. The framework names no
plugin anywhere below — "the registry" always means whatever namespace a plugin
registered through `plugin_api.register_tag_namespace`. -->

### Scenario 1: A named entity resolves to a kind, a tag and a hub

```gherkin
Given a plugin has registered a tag namespace whose entries know an entity by
    its name
When that name is resolved
Then the resolution returns that entity's kind, its `<namespace>/<slug>` tag and
    its hub note
  And it is answered by asking the registered `entries()` callable at that
    moment — never by a fuzzy search over note titles, and never from a list
    captured when the namespace was registered
  And `kind` is carried through exactly as the plugin supplied it; the framework
    never enumerates or interprets the value
```
<!-- AC-ID: REQ-SB-95-US-05-AC-01 -->

### Scenario 2: The updates about an entity are read scoped, synthesis first

```gherkin
Given a resolved entity with a hub note and tagged evidence notes in the vault
When the scoped read for that entity is performed
Then the result is composed from the entity's own hub synthesis FIRST, then its
    tagged evidence — Threads and Meetings — newest first, by each note kind's
    own real recency field
  And every note in the result carries that entity's tag; nothing outside the
    tag scope is read or returned
  And no whole-vault search is run as part of answering — the read reaches the
    vault only through the tag-keyed index, and the search entry point is never
    called
```
<!-- AC-ID: REQ-SB-95-US-05-AC-02 -->

### Scenario 3: An alias or a domain resolves to the same entity

```gherkin
Given a registered entry carrying aliases and known email domains
When it is named by an alias, or by one of its domains, in any letter case
Then it resolves to the same kind, tag and hub as its primary name
  And when two registered entries match the same name, alias or domain, the
    result is reported as ambiguous, naming both candidates, and is never
    silently resolved to one of them
```
<!-- AC-ID: REQ-SB-95-US-05-AC-03 -->

### Scenario 4: One tag-keyed index serves every entity, including a brand-new one

```gherkin
Given a new entity exists in the vault, with notes already carrying its tag
When the vault index is rebuilt
Then that entity is served by the one tag-keyed index with no per-entity
    provisioning step — no new `Index` artifact is created, no new cron job is
    registered, and no second refresh trigger exists
  And the tag-keyed index is rebound in the same pass as `_vault_entries`, so it
    can never be newer or older than the notes it groups
  And the three existing per-entity Indexes and their hourly jobs are untouched
```
<!-- AC-ID: REQ-SB-95-US-05-AC-04 -->

### Scenario 5: A name that does not resolve is answered honestly

```gherkin
Given a name that no registered namespace knows — including the case where no
    namespace is registered at all
When resolution is asked for it
Then the answer states plainly that the name did not resolve, repeating the name
    as it was given
  And no scoped read is performed and no unscoped search result is returned in
    its place
  And a registered `entries()` callable that raises is skipped and logged, and
    still produces "did not resolve" rather than a wrong answer
```
<!-- AC-ID: REQ-SB-95-US-05-AC-05 -->

### Scenario 6: The agent reaches the scoped read through the catalogue

```gherkin
Given the scoped entity read is published as a catalogued Action with an `http`
    implementation naming its own route
When an agent calls it
Then the call goes through the Action call gate and is validated like any other
    action call — unknown id, missing required input and unresolved
    implementation are refused the same way
  And a caller not in that Action's `allowed_callers` is refused, with the
    refusal recorded in the Action-call ledger
```
<!-- AC-ID: REQ-SB-95-US-05-AC-06 -->

### Scenario 7: The one tag-keyed index covers every entity tag in the vault

```gherkin
Given the vault holds notes carrying many different `<namespace>/<slug>` tags
When the tag-keyed index is built
Then every such tag present in the vault is a key in that one index, whether or
    not its namespace is registered — so this holds on an install with no
    plugins at all, and no namespace prefix is filtered in or out by a list
    written into the framework
  And a tag key with no registered entry is reported as unknown, naming the tag,
    rather than silently dropped
```
<!-- AC-ID: REQ-SB-95-US-05-AC-07 -->

### Scenario 8: A namespace is registered as a callable, and the contract bumps once

```gherkin
Given a plugin registers a tag namespace through
    `plugin_api.register_tag_namespace(namespace, entries)`
When the plugin is loaded, and later a resolution is asked for
Then `entries` is stored as a callable and invoked at resolution time, never
    called at registration time
  And a second registration of the same namespace prefix is refused, naming both
    plugins
  And `FRAMEWORK_API` stays 7 while this capability lands, and becomes 8 exactly
    once — in whichever of `register_tag_namespace` and `register_action`
    (`REQ-SB-95-US-02`) lands last, never twice
```
<!-- AC-ID: REQ-SB-95-US-05-AC-08 -->

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

Final split, decomposer, 2026-10-16. The boundary question is settled
(`ADR-035` Decision 1): every task below lands in **this** repository as generic
mechanism, naming no plugin. Dependency order is
`(T01, T02) → T03 → T04 → T05`.

| ID | Type | Task | ACs | Depends on | Task File |
|---|---|---|---|---|---|
| REQ-SB-95-US-05-T01 | backend | The tag-keyed index as a projection, computed and rebound inside `VaultManager.rebuild_index()` | AC-04, AC-07 | — | `../Tasks/REQ-SB-95-US-05-T01-tag-keyed-index-projection.md` |
| REQ-SB-95-US-05-T02 | backend | `plugin_api.register_tag_namespace(namespace, entries)` — the callable seam, and the one `FRAMEWORK_API` bump | AC-08 | — | `../Tasks/REQ-SB-95-US-05-T02-register-tag-namespace-plugin-api.md` |
| REQ-SB-95-US-05-T03 | backend | The generic tag resolver — name/alias/domain → `(kind, tag, hub)`, ambiguity and non-resolution reported | AC-01, AC-03, AC-05, AC-07 | T01, T02 | `../Tasks/REQ-SB-95-US-05-T03-generic-tag-resolver.md` |
| REQ-SB-95-US-05-T04 | backend | The scoped read — hub synthesis first, then tagged evidence newest first, nothing outside the tag | AC-02 | T01, T03 | `../Tasks/REQ-SB-95-US-05-T04-scoped-entity-read.md` |
| REQ-SB-95-US-05-T05 | backend | The scoped read as a shipped, catalogued Action reached through the call gate | AC-06 | T04, REQ-SB-95-US-02-T02, REQ-SB-95-US-03-T02, REQ-SB-95-US-03-T03 | `../Tasks/REQ-SB-95-US-05-T05-scoped-read-as-catalogued-action.md` |

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

**Architecture scope (architect, 2026-10-16) — the sections that bound the coder:**

`Implementation/Architecture/architecture.md` → §An Agent Acts From a Published
Catalogue (`REQ-SB-95`) → **§Entity Resolution — a Generic Tag Resolver, No
Plugin Named**, **§The One Tag-Keyed Index — a Projection, Not an Artifact**,
**§Registering a Tag Namespace** and **§One Contract Bump for All of
`REQ-SB-95`**. Read-only context: §The Action Call Gate (Scenario 6 reaches the
scoped read through it). ADRs: `ADR-032`, `ADR-035` (Decision 1), `ADR-022`
(unamended), **`ADR-037`** (new).

What `ADR-037` settles, so the build does not have to choose:

- **The tag-keyed index is a projection, computed inside
  `VaultManager.rebuild_index()` and rebound alongside `_vault_entries`** — no
  new `Index` artifact, no new cron job, no second refresh trigger. `BUG-082` is
  the reason: a stored projection with its own trigger is how the backend's own
  index sat at boot-state for three days. `ADR-032`'s "a single artifact" is read
  as "one index, dict lookup, no per-entity provisioning", not as an `Index` kind
  instance.
- **Keys are every `<namespace>/<slug>` tag present in the vault**, registered or
  not (Scenario 7 holds with zero plugins installed); an unregistered tag key is
  reported, never dropped.
- **`plugin_api.register_tag_namespace(namespace, entries)` where `entries` is a
  CALLABLE**, asked at resolution time — same shape as
  `register_subject_enricher`/`register_agent_matcher`, plain dicts out, `kind`
  an opaque pass-through string. Duplicate prefix refused; a raising callable
  skipped; ambiguity reported, never silently resolved.
- **The `FRAMEWORK_API` bump is taken once for all of `REQ-SB-95`** —
  `register_action` (`US-02`) and `register_tag_namespace` (this story) land
  additively at 7, and the constant moves to 8 exactly once, in whichever of the
  two lands last. This is a cross-story edge on `plugin_api.py` the decomposer
  and product-owner must honour.

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

**Decomposer RE-pass, 2026-10-16 — 8 ACs locked, 5 tasks, `Draft → Ready`.**
The previous pass's task files were deleted before they could be used; these
five are written fresh, not patched.

- **AC-01 … AC-08 are all locked, and coverage was checked AC by AC** — the
  previous pass marked this story `Ready` while **AC-02 and AC-06 had no
  verification step in any task**, a hard-rule-4 failure. The map now, each
  entry a real numbered `[AC-ID]`-tagged step in that task's `## Tests`:
  AC-01 → `T03` (steps 1–4); **AC-02 → `T04` (steps 1–5, plus its manual
  step)**; AC-03 → `T03` (5–6); AC-04 → `T01` (1–4); AC-05 → `T03` (7–9);
  **AC-06 → `T05` (steps 1–5, plus its manual step)**; AC-07 → `T01` (5–6) and
  `T03` (10); AC-08 → `T02` (1–5). No locked AC is unverified.
  `depends_on` is acyclic (`T01/T02 → T03 → T04 → T05`). Tasks move to `Ready`
  with the story.
- **Two ACs were tightened for verifiability**, wording only, no scope change:
  AC-02 now names *each note kind's own real recency field* and makes "no
  whole-vault search" observable (the search entry point is never called),
  because `capture_freshness.py` already fixes the real fields —
  `Thread.last_message_at`, `Meeting.start`, `RawMessage.received` — and a
  decomposer-invented date field would have been a material assumption. AC-07
  now says explicitly that no namespace prefix may be filtered by a list
  written into the framework, which is `ADR-022`'s CFO test stated as a
  checkable property rather than an intention.
- **Scenario 8 is decomposer-authored.** `ADR-037` calls the single contract
  bump "a planning constraint, not just a coding one" and tells the decomposer
  to place it rather than let it be discovered. A planning constraint with no
  locked AC is a sentence in an ADR; as AC-08 it is a test.
- **The cross-story `plugin_api.py` edge, stated plainly.** `register_action`
  (`REQ-SB-95-US-02-T05`) and `register_tag_namespace` (`T02` here) are the only
  two additions `REQ-SB-95` makes to that file, and the constant moves 7 → 8
  **once, in whichever lands last**. `T02` is therefore written to *read the real
  current `plugin_api.py` first*: if `register_action` is already present, this
  is the later landing and the bump is taken here; if it is not, `FRAMEWORK_API`
  stays 7 and the bump is owed by `US-02`.
  **This is the trigger-7 half of the gate:** the already-written
  `REQ-SB-95-US-02-T05` task file carries no `FRAMEWORK_API` instruction at all
  (confirmed by direct reading — it was authored by a concurrent decomposer run
  that this pass may not edit). If `US-02` lands last as things stand, nobody
  bumps the constant and no plugin can ever depend on either capability.
  `REVIEW-QUEUE.md` carries the two-line fix.
- **No cross-story `depends_on` was invented for that edge.** Making `T02`
  depend on `REQ-SB-95-US-02-T05` would force this story behind the whole spine
  for a one-line constant, contradicting the story's own "Scenarios 1–5 and 7
  stand alone". The conditional read above gets the same guarantee without the
  ordering cost. The genuine cross-story dependency is `T05` only (AC-06), which
  needs the Action kind and the call gate and says so in `depends_on`.
- **No `ESCALATIONS.md` entry written by this pass.** `ESC-063` stays Resolved.
  No oversized task; `T03` and `T04` are the two with real logic and each is one
  module plus its tests.
- **`T05` now also depends on `REQ-SB-95-US-03-T02`** (the gate and the
  ledger), not only on `US-03-T03`'s dispatch: AC-06's second clause requires
  the refusal to be *recorded in the ledger*, which `T02` of that story builds.

**Architect pass, 2026-10-16 — re-flagged under trigger 3.** The analyst's
trigger-4/7 flags are cleared (the operator decided it; `ADR-035`, and `ESC-063`
is Resolved). This pass fires **trigger 3 only**: `ADR-037` was created. No new
`ESCALATIONS.md` entry. One reading is worth the human's eye and is stated
openly in `ADR-037`: `ADR-032`'s phrase "a single artifact" is taken to mean one
index with a dict lookup and no per-entity provisioning, **not** an `Index`
artifact-kind instance with its own cron job — so this is read as specifying what
`ADR-032` left open, not as contradicting it. If the operator reads it the other
way, `ADR-037` is the thing to reject. The decomposer still runs.
