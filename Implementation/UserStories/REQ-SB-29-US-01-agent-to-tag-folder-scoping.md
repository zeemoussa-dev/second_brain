---
id: REQ-SB-29-US-01
title: Agent-to-tag/folder vault scoping — assignment on the Agent Settings surface, and scope-bounded retrieval on request
requirement_ids: [REQ-SB-29]
requirement_section: "REQ-SB-29: Agent-to-Tag/Folder Scoping"
phase: P1
status: Draft
gate: clear
gate_reason: "Resolved 2026-08-12 — operator decided the retrieval mechanism: a narrower, story-scoped ad hoc primitive now, matching existing precedent, not a wait on REQ-SB-01/02 (see Notes). Still net-new-design-needed — run /design REQ-SB-29 before /plan-tasks."
sprint: ""
created: 2026-08-11
updated: 2026-08-11
---

# REQ-SB-29-US-01 — Agent-to-tag/folder vault scoping — assignment on the Agent Settings surface, and scope-bounded retrieval on request

## Story

**As a** Second Brain user
**I want** to link an agent to a specific vault tag (e.g. `customer/masdar`)
or folder, and have that agent retrieve notes matching its assigned scope
when I ask it to
**So that** an agent bounded to a customer or area can answer requests like
"get me the pipeline for Masdar" using that customer's actual notes,
without me having to locate them in the vault myself

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-29: Agent-to-Tag/Folder Scoping* —
  "An agent can be linked to a specific vault tag (e.g. `customer/masdar`)
  or folder, giving it bounded, relevant query access to that slice of the
  vault — for example, an agent assigned to a customer tag can retrieve
  that customer's Pipeline/Agreements/Consumption notes on request, without
  searching the whole vault." Acceptance: "An agent can be assigned one or
  more vault tags/folders as its scope; when asked, the agent can retrieve
  and use notes matching its assigned scope (e.g. 'get me the pipeline for
  Masdar' returns that customer's actual Pipeline notes) rather than
  requiring the user to locate them manually."
- **PRD breadcrumb (2026-08-11, operator-authored, cited verbatim, NOT
  re-decided here):** "Directly activates the Customer/Pipeline/Agreements/
  Consumption schema resolved 2026-08-10 (`MEMORY.md`) that has had
  'structure only — no ingestion/agent code' ever since. Genuinely open,
  not decided here: how an agent's tag/folder scope is assigned (a new
  field on the Agent Settings surface, alongside Section/Provider/
  Keywords/Working-mode?), whether an agent can have multiple scopes or
  exactly one, how this interacts with REQ-SB-01/02 (Vault Indexing &
  Browse/Search, neither built yet) as the underlying query mechanism, and
  how it relates to REQ-SB-20's keyword-based routing (a different,
  complementary dimension — keywords describe *what an agent knows*,
  tag/folder scope describes *what an agent can reach*). Left to `/spec`."
- **Resolved here, by safe precedent (not a guess):** scope is assigned per
  agent on the Agent Settings surface (`AgentDetailPanel.tsx`'s `kv-list`,
  built by the already-`Done` `REQ-SB-13-US-01`) — the exact same surface
  that already carries `REQ-SB-18`'s Section picker, `REQ-SB-19`'s Provider
  picker, `REQ-SB-20`'s Keywords field, and `REQ-SB-21`'s Working-mode
  picker (all `Draft`/`Ready`, not yet all `Done`, but all sharing this one
  surface's established row pattern). A "Vault scope" row follows the
  identical pattern — this does not need any of those four stories to be
  `Done` first, since the panel itself already exists.
- **Resolved directly from the PRD's own Acceptance text (not a guess):**
  **"one or more" scopes per agent** — the Acceptance text says "assigned
  one or more vault tags/folders," settling the single-vs-multiple question
  the breadcrumb raised. This story specs multi-scope assignment.
- **Resolved directly from the PRD's own breadcrumb (not a guess):**
  tag/folder scope (*what an agent can reach*) and REQ-SB-20's keywords
  (*what an agent knows*) are explicitly complementary, non-overlapping
  dimensions — this story does not touch or duplicate `REQ-SB-20`'s
  Keywords field or its Hub-routing mechanism.
- **Genuinely NOT resolved — the retrieval mechanism itself (see
  `ESCALATIONS.md` → `ESC-008`).** The PRD's Acceptance text is not only an
  assignment mechanism; it commits to real retrieval behaviour — "when
  asked, the agent can retrieve and use notes matching its assigned scope."
  `BACKLOG.md` confirms `REQ-SB-01` (Vault Indexing) and `REQ-SB-02`
  (Browse & Search) both have **no story at all**, not even `Draft` — the
  general query mechanism the breadcrumb itself names as the obvious
  foundation does not exist. However, this codebase already has real,
  shipped precedent for *narrower*, ad hoc, non-general vault-query
  primitives with no general indexer behind them: `vault_writer.
  list_notes_in_kind_folder(kind)` (folder-scoped, powers `my_day.py`),
  `list_known_customers()`/`list_known_partners()` (tag-scoped,
  vault-derived), and the migration-scan pattern (`ADR-009`/`ADR-012`,
  frontmatter+tag+wikilink-scoped). A tag/folder-scoped retrieval primitive
  for exactly this story's need could plausibly be built the same narrow
  way, without waiting for REQ-SB-01/02's full general indexing/search
  feature to exist. **Whether that narrower substitute satisfies the PRD's
  intent, or whether REQ-SB-01/02 must ship first, is a genuine product/
  architecture judgement call — not guessed here.** See `ESCALATIONS.md` →
  `ESC-008` and the flag below.
- **No `html-prototype/` screen covers a scope field.** `html-prototype/
  agents-map.html`'s agent detail side panel `kv-list` (approved for
  `REQ-SB-13-US-01`, since extended by the `REQ-SB-18/19/20/21` design
  pass with Section/Provider/Keywords/Working-mode rows) has no Vault
  scope row anywhere — confirmed by direct inspection. See the flag below.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. Scenarios 3-5 (retrieval) describe only what the PRD's own
Acceptance text commits to; they deliberately do not assert a specific
retrieval mechanism (general indexer vs. narrower scoped primitive) — see
ESC-008, left open. -->

### Scenario 1: Assigning a vault tag as an agent's scope

```gherkin
Given the user is viewing an agent's Agent Settings surface
When the user assigns a vault tag (e.g. "customer/masdar") to that agent as
    its scope
Then the agent's assigned scope is shown on its Agent Settings surface
```

### Scenario 2: An agent can be assigned more than one scope

```gherkin
Given the user is viewing an agent's Agent Settings surface, and that agent
    already has one vault tag or folder assigned as its scope
When the user assigns a second, different vault tag or folder to that agent
Then both scopes are shown as assigned to that agent
  And neither the first nor the second assignment is lost
```

### Scenario 3: Retrieving notes matching an agent's assigned scope on request

```gherkin
Given an agent is assigned the "customer/masdar" tag as its scope
  And the vault has Pipeline notes tagged "customer/masdar"
When the user asks that agent to retrieve Masdar's pipeline
Then the agent returns the actual Masdar Pipeline notes from the vault
  And the returned notes are limited to ones matching the agent's assigned
    scope
```

### Scenario 4: A request outside an agent's assigned scope does not return unrelated vault content

```gherkin
Given an agent is assigned only the "customer/masdar" tag as its scope
When the user asks that agent for notes belonging to a different customer,
    not covered by its assigned scope
Then the agent does not return notes outside its assigned scope
  And the agent honestly reports that the request is outside its scope,
    rather than fabricating a response or silently searching the whole
    vault
```

### Scenario 5: A request within an agent's scope with no matching notes returns an honest empty result

```gherkin
Given an agent is assigned a vault tag or folder as its scope
  And no notes in the vault currently match that scope
When the user asks that agent to retrieve notes from its assigned scope
Then the agent honestly reports that nothing matching was found, rather
    than fabricating a response
```

### Scenario 6: An agent with no assigned scope has no bounded vault query access

```gherkin
Given an agent has no vault tag or folder currently assigned to it
When the user asks that agent to retrieve notes from a scope
Then the agent has no bounded vault query access to use
  And the agent does not silently search the whole vault in place of a
    scope
```

## Affected Screens

- `html-prototype/agents-map.html` — the agent detail side panel's Settings
  `kv-list` needs a new "Vault scope" field/row (tags/folders, supporting
  more than one value). **Not present in the approved prototype** — no
  design authority exists for its visual shape (a free-text tag list? a
  multi-select against `list_known_customers()`-style vault-derived
  values? a folder picker?). See the flag below.

## Dependencies

- **Blocked by:** `REQ-SB-01` (Vault Indexing) and `REQ-SB-02` (Browse &
  Search) — **neither has a story yet, not even `Draft`** — as the
  breadcrumb's own named "underlying query mechanism," OR an
  architect-approved narrower scoped-query primitive built directly
  against the vault (matching existing precedent: `list_notes_in_kind_
  folder`, `list_known_customers`/`list_known_partners`, the migration-scan
  pattern). **Which path applies is genuinely open — see `ESCALATIONS.md`
  → `ESC-008`, not resolved here.** Scenarios 1-2 (assignment) do not
  depend on either path; Scenarios 3-6 (retrieval) do.
- **Related to:** `REQ-SB-18-US-01`/`REQ-SB-19-US-01`/`REQ-SB-20-US-01`/
  `REQ-SB-21-US-01` — share the same Agent Settings surface `kv-list`
  pattern this story's scope field follows (not a build dependency; the
  panel itself already exists via the already-`Done` `REQ-SB-13-US-01`).
- **Related to, not overlapping:** `REQ-SB-20` (Section Hub Intelligence &
  Cross-Section Routing) — keywords describe *what an agent knows*,
  tag/folder scope (this story) describes *what an agent can reach*;
  explicitly complementary per the PRD breadcrumb, not the same mechanism.
- **Related to:** `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`
  → "Customer structured data" — the Pipeline/Agreements/Consumption
  schema this requirement directly activates for real retrieval (structure
  only until now, per `MEMORY.md`'s 2026-08-10 decision).
- **External:** none new.

## Constraints

- **Multiple scopes per agent are allowed** (resolved directly from the
  PRD's own Acceptance text — "one or more") — do not build a
  single-scope-only model.
- Scope is assigned per agent on the Agent Settings surface, following the
  same `kv-list` row pattern as Section/Provider/Keywords/Working-mode.
- **The retrieval mechanism (decided 2026-08-12, see Notes): a narrower,
  story-scoped ad hoc primitive, NOT a wait on REQ-SB-01/02.** Build a new
  `vault_writer` primitive (e.g. `list_notes_matching_scope(tags_or_folders)`)
  directly against the vault, mirroring the exact shape of
  `list_notes_in_kind_folder`/`list_known_customers`/`list_known_partners`
  and the migration-scan pattern (`ADR-009`/`ADR-012`) — frontmatter/tag/
  folder-matched, no general indexer, no embeddings/ranking. Do not build
  against REQ-SB-01/02 as a dependency; they remain unbuilt and unrelated
  to this story.
- A request outside an agent's assigned scope, or with no matching notes,
  must be answered honestly (Scenarios 4-5) — never fabricated, and never
  silently widened to search the whole vault.
- An agent with no assigned scope has no bounded vault query access
  (Scenario 6) — this story does not give every agent implicit whole-vault
  access as a fallback.

## Implementation Tasks

<!-- Left for the architect/decomposer at /plan-tasks, once the flagged
retrieval-mechanism question (ESC-008) is resolved. -->

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **General-purpose free-text vault search** (`REQ-SB-02`) — this story is
  bounded, tag/folder-scoped retrieval for one agent's assigned scope, not
  a general search feature.
- **Search-quality mechanisms** (chunking, embeddings, reranking —
  `REQ-SB-06`) — out of scope; that requirement is explicitly gated on
  REQ-SB-02 existing first.
- **Automatic inference of an agent's scope** from its Section, keywords,
  or past activity — scope is explicitly user-assigned, per the Agent
  Settings surface, not derived.
- **Any change to `REQ-SB-20`'s keyword-based routing mechanism or its
  Keywords field** — genuinely complementary, not touched here.
- **Boolean/compound scope queries** (AND/OR/NOT across multiple assigned
  tags or folders) — this story's retrieval is a straightforward
  match-against-assigned-scope, not a query language.
- **Writing to the vault within an agent's scope** — this requirement's
  acceptance text is read/retrieval only ("retrieve and use notes matching
  its assigned scope"); scoped write access is not asked for here.

## Notes

**Prototype parity (agents-map.html):**

- `agents-map.html`'s side panel Settings block (`kv-list`) — needs a new
  Vault scope field/row — **not covered by the approved prototype.**
- `agents-map.html`'s side panel Chat block — a request like "get me the
  pipeline for Masdar" and its scoped/honest-empty/out-of-scope replies
  have no prototype coverage — **not covered by the approved prototype.**
- `agents-map.html`'s side panel Available Actions/Communication History
  blocks — **N/A**, not touched by this story.
- No screen anywhere in `html-prototype/` visualizes scope-bounded
  retrieval results or an out-of-scope/no-match honest response — **not
  covered by the approved prototype.**

**Why this stays ONE story (assignment + retrieval), not split:** applying
this project's standing "no independent value alone" test (already used
for `REQ-SB-18-US-01`, `REQ-SB-19-US-01`, `REQ-SB-20-US-01`) — a scope
field with no retrieval mechanism ever consuming it has no value, and a
retrieval mechanism with no assigned scope to bound it is meaningless. The
PRD's own single-requirement framing agrees.

**Why this is NOT scoped down to "assignment only," despite REQ-SB-01/02
not existing:** unlike simply omitting the retrieval scenarios, the PRD's
Acceptance text is explicit and concrete about retrieval ("when asked, the
agent can retrieve and use notes matching its assigned scope... returns
that customer's actual Pipeline notes") — silently dropping that half of
the requirement would mean shipping a story that satisfies only the
weaker, PRD-unstated half of REQ-SB-29 and calling it complete. Per the
analyst's mandate to flag rather than guess when genuinely unclear, the
retrieval scenarios are written as the PRD actually describes them, and
the open question is flagged for a human decision (build via REQ-SB-01/02,
or an architect-approved narrower primitive) rather than silently resolved
by omission.

gate: flagged 2026-08-11, gate_reason: unclear-requirement (`ESC-008`) +
net-new-design-needed. REQ-SB-29 itself is finalised PRD text (no
`<!-- Draft -->` marker) — the flag is about the retrieval mechanism's
missing foundation and the unbuilt Agent Settings scope field, not about
the requirement's own finalization state. `ESCALATIONS.md` → `ESC-008`
records the unclear-requirement trigger. A `REVIEW-QUEUE.md` entry has been
added recommending an operator decision on the retrieval-mechanism
question, followed by `/design REQ-SB-29` for the scope field, before
`/plan-tasks` runs on this story.

**Update, 2026-08-12 — Resolved.** Operator decided the retrieval
mechanism: build the narrower, story-scoped ad hoc primitive now (see
Constraints), matching this project's own already-shipped precedent for
non-general vault queries — not a wait on `REQ-SB-01`/`REQ-SB-02`, which
remain the least-started requirements in the PRD with no realistic
near-term timeline. `gate:` reset to `clear`. `ESCALATIONS.md` → `ESC-008`
flipped to `Resolved`, naming this update as the resolving artefact.
**Next step: this story is still net-new-design-needed** (no Vault-scope
row exists on the Agent Settings surface in any `html-prototype/` screen)
— run `/design REQ-SB-29` before `/plan-tasks`.
